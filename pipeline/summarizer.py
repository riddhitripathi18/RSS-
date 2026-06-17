"""
News Summarizer Agent - Generates summaries using LLM
"""
from core.database import Article, Digest, get_session, init_db
from datetime import datetime
from core.config import OPENAI_API_KEY, SUMMARIZATION_MODEL
import logging
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NewsSummarizer:
    """Summarizes articles using LLM"""
    
    def __init__(self):
        self.engine = init_db()
        self.api_key = OPENAI_API_KEY
        self.model = SUMMARIZATION_MODEL
        
        # Mock mode for testing (no API key required)
        self.use_mock = not bool(self.api_key)
        
        if self.use_mock:
            logger.warning("⚠️  LLM MOCK MODE: No OpenAI API key found.")
            logger.warning("   To use real LLM summaries, set OPENAI_API_KEY in .env file")
            logger.warning("   Get your API key from: https://platform.openai.com/api-keys")
    
    def summarize_article(self, article_dict):
        """Summarize a single article using LLM"""
        title = article_dict['title']
        description = article_dict['description']
        
        if self.use_mock:
            return self._generate_mock_summary(title, description)
        else:
            return self._generate_llm_summary(title, description)
    
    def _generate_mock_summary(self, title, description):
        """Generate a mock summary (for testing without API key)"""
        # Simple mock summary - just take first 100 chars of description
        summary = description[:150] + "..." if description else title
        return summary
    
    def _generate_llm_summary(self, title, description):
        """Generate summary using OpenAI LLM"""
        try:
            # pyrefly: ignore [missing-import]
            from openai import OpenAI
            
            client = OpenAI(api_key=self.api_key)
            
            prompt = f"""You are a news summarizer. Summarize this article in 2-3 sentences.

Title: {title}
Description: {description}

Summary:"""
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except ImportError:
            logger.error("OpenAI library not installed. Run: pip install openai")
            return self._generate_mock_summary(title, description)
        except Exception as e:
            logger.error(f"LLM API error: {str(e)}. Using mock summary.")
            return self._generate_mock_summary(title, description)
    
    def get_processed_articles(self):
        """Get articles that have been processed but not yet included in a digest"""
        session = get_session(self.engine)
        articles = session.query(Article).filter_by(
            is_processed=True,
            is_digested=False  # Only articles not already in a digest
        ).all()
        
        # Mark these articles as digested so they won't be picked up again
        for a in articles:
            a.is_digested = True
        session.commit()
        
        # Convert to dicts
        articles_data = [
            {
                'id': a.id,
                'title': a.title,
                'url': a.url,
                'description': a.description,
                'source': a.source,
                'published_date': a.published_date
            }
            for a in articles
        ]
        
        session.close()
        return articles_data
    
    def generate_daily_digest(self, articles):
        """Generate a daily digest from articles"""
        logger.info(f"Generating daily digest from {len(articles)} articles...")
        
        digest_content = {
            "date": datetime.utcnow().isoformat(),
            "total_articles": len(articles),
            "articles": []
        }
        
        for idx, article in enumerate(articles, 1):
            logger.info(f"  Summarizing article {idx}/{len(articles)}: {article['title'][:50]}...")
            
            summary = self.summarize_article(article)
            
            article_summary = {
                "number": idx,
                "title": article['title'],
                "source": article['source'],
                "url": article['url'],
                "published_date": str(article['published_date']),
                "summary": summary
            }
            
            digest_content["articles"].append(article_summary)
        
        # Create text version of digest
        digest_text = self._format_digest_text(digest_content)
        
        return digest_content, digest_text
    
    def _format_digest_text(self, digest_json):
        """Format digest as readable text"""
        text = f"""
═══════════════════════════════════════════════════════════════════════════════
                    📰 DAILY NEWS DIGEST
═══════════════════════════════════════════════════════════════════════════════

Date: {digest_json['date']}
Total Articles: {digest_json['total_articles']}

───────────────────────────────────────────────────────────────────────────────
"""
        
        for article in digest_json['articles']:
            text += f"""
{article['number']}. {article['title']}
   Source: {article['source']}
   Published: {article['published_date']}
   
   {article['summary']}
   
   Read more: {article['url']}

───────────────────────────────────────────────────────────────────────────────
"""
        
        text += """
═══════════════════════════════════════════════════════════════════════════════
                    End of Daily News Digest
═══════════════════════════════════════════════════════════════════════════════
"""
        
        return text
    
    def save_digest(self, digest_content, digest_text):
        """Save digest to database"""
        session = get_session(self.engine)
        
        digest = Digest(
            digest_date=datetime.utcnow(),
            content=digest_text,
            article_count=digest_content['total_articles'],
            is_sent=False
        )
        
        session.add(digest)
        session.commit()
        logger.info(f"✓ Digest saved to database with ID: {digest.id}")
        session.close()
        
        return digest.id


def run_summarizer():
    """Main function to run the news summarizer"""
    summarizer = NewsSummarizer()
    
    logger.info("=" * 80)
    logger.info("📝 News Summarizer Agent Starting...")
    logger.info("=" * 80)
    
    # Get processed articles
    logger.info("\n1️⃣  Retrieving processed articles...")
    articles = summarizer.get_processed_articles()
    logger.info(f"✓ Found {len(articles)} articles to summarize")
    
    if not articles:
        logger.warning("No articles found to summarize. Run analyzer.py first.")
        return
    
    # Generate digest
    logger.info("\n2️⃣  Generating daily digest with summaries...")
    digest_json, digest_text = summarizer.generate_daily_digest(articles)
    
    # Save digest
    logger.info("\n3️⃣  Saving digest to database...")
    digest_id = summarizer.save_digest(digest_json, digest_text)
    
    # Display digest
    logger.info("\n" + "=" * 80)
    logger.info("✓ Daily News Digest Generated!")
    logger.info("=" * 80)
    logger.info(digest_text)
    
    logger.info("=" * 80)
    logger.info("Next: Run delivery.py to send the digest via Telegram/Email")
    logger.info("=" * 80)


if __name__ == "__main__":
    run_summarizer()
