"""
Delivery System - Sends digests via Telegram, Email, and WhatsApp
"""
from core.database import Digest, get_session, init_db
from datetime import datetime
from core.config import (
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT
)
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DigestDelivery:
    """Handles delivery of news digest via multiple channels"""
    
    def __init__(self):
        self.engine = init_db()
        self.telegram_token = TELEGRAM_BOT_TOKEN
        self.telegram_chat_id = TELEGRAM_CHAT_ID
        self.email_username = EMAIL_USERNAME
        self.email_password = EMAIL_PASSWORD
        self.smtp_server = EMAIL_SMTP_SERVER
        self.smtp_port = EMAIL_SMTP_PORT
    
    def get_unsent_digests(self):
        """Get digests that haven't been sent yet (restricted to the last 24 hours to avoid backing up old news)"""
        session = get_session(self.engine)
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(hours=24)
        digests = session.query(Digest).filter(
            Digest.is_sent == False,
            Digest.digest_date >= cutoff
        ).all()
        
        # Convert to dicts
        digests_data = [
            {
                'id': d.id,
                'content': d.content,
                'article_count': d.article_count,
                'digest_date': d.digest_date
            }
            for d in digests
        ]
        
        session.close()
        return digests_data
    
    def send_via_telegram(self, digest_content):
        """Send digest via Telegram"""
        if not self.telegram_token or not self.telegram_chat_id:
            logger.warning("⚠️  Telegram not configured. Skipping Telegram delivery.")
            logger.info("   To enable: set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
            return False
        
        try:
            # pyrefly: ignore [missing-import]
            import requests
            
            # Split digest into chunks (Telegram has message size limits)
            chunks = self._split_message(digest_content, max_length=4000)
            
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            
            for chunk in chunks:
                payload = {
                    "chat_id": self.telegram_chat_id,
                    "text": chunk,
                    "parse_mode": "HTML"
                }
                
                response = requests.post(url, json=payload, timeout=10)
                
                if response.status_code != 200:
                    logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                    return False
            
            logger.info(f"✓ Digest sent via Telegram ({len(chunks)} messages)")
            return True
            
        except Exception as e:
            logger.error(f"Telegram delivery error: {str(e)}")
            return False
    
    def send_via_email(self, digest_content, recipient_email=None):
        """Send digest via Email"""
        if not self.email_username or not self.email_password:
            logger.warning("⚠️  Email not configured. Skipping email delivery.")
            logger.info("   To enable: set EMAIL_USERNAME and EMAIL_PASSWORD in .env")
            return False
        
        if not recipient_email:
            recipient_email = self.email_username
        
        try:
            # Create email
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"📰 Daily News Digest - {datetime.utcnow().strftime('%Y-%m-%d')}"
            msg["From"] = self.email_username
            msg["To"] = recipient_email
            
            # Plain text version
            text_part = MIMEText(digest_content, "plain")
            msg.attach(text_part)
            
            # HTML version (prettier)
            html_content = digest_content.replace('\n', '<br>')
            html_part = MIMEText(f"<pre>{html_content}</pre>", "html")
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=5) as server:
                server.starttls()
                server.login(self.email_username, self.email_password)
                server.sendmail(self.email_username, recipient_email, msg.as_string())
            
            logger.info(f"✓ Digest sent via Email to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Email delivery error: {str(e)}")
            return False
    
    def _split_message(self, text, max_length=4000):
        """Split long messages into chunks"""
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        for line in text.split('\n'):
            if len(current_chunk) + len(line) + 1 > max_length:
                chunks.append(current_chunk)
                current_chunk = line
            else:
                current_chunk += line + '\n'
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def mark_digest_sent(self, digest_id):
        """Mark digest as sent in database"""
        session = get_session(self.engine)
        digest = session.query(Digest).filter_by(id=digest_id).first()
        
        if digest:
            digest.is_sent = True
            digest.sent_date = datetime.utcnow()
            session.commit()
            logger.info(f"✓ Marked digest {digest_id} as sent")
        
        session.close()


def run_delivery():
    """Main function to run the delivery system"""
    delivery = DigestDelivery()
    
    logger.info("=" * 80)
    logger.info("📨 Delivery System Starting...")
    logger.info("=" * 80)
    
    # Get unsent digests
    logger.info("\n1️⃣  Retrieving unsent digests...")
    digests = delivery.get_unsent_digests()
    logger.info(f"✓ Found {len(digests)} unsent digest(es)")
    
    if not digests:
        logger.info("No digests to send.")
        return
    
    # Send each digest
    total_sent = 0
    for digest in digests:
        logger.info(f"\n2️⃣  Sending digest {digest['id']} ({digest['article_count']} articles)...")
        
        # Try Telegram
        telegram_sent = delivery.send_via_telegram(digest['content'])
        
        # Try Email
        email_sent = delivery.send_via_email(digest['content'])
        
        # Mark as sent if at least one channel succeeded
        if telegram_sent or email_sent:
            delivery.mark_digest_sent(digest['id'])
            total_sent += 1
        else:
            logger.warning(f"Could not send digest {digest['id']} via any channel")
    
    logger.info("\n" + "=" * 80)
    logger.info(f"✓ Delivery System completed! Sent {total_sent}/{len(digests)} digests")
    logger.info("=" * 80)
    logger.info("Next: Set up scheduler.py to automate daily digest generation")


if __name__ == "__main__":
    run_delivery()
