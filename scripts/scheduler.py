"""
Scheduler & Orchestrator - Automates the entire news digest pipeline
"""
# pyrefly: ignore [missing-import]
import schedule
import time
import logging
import os
import sys

# Ensure the project root is in the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)
from datetime import datetime
from pipeline.fetcher import run_fetcher
from pipeline.analyzer import run_analyzer
from pipeline.summarizer import run_summarizer
from pipeline.delivery import DigestDelivery

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_daily_pipeline():
    """Run the complete news digest pipeline"""
    logger.info("\n" + "=" * 80)
    logger.info("🚀 STARTING DAILY NEWS DIGEST PIPELINE")
    logger.info("=" * 80)
    
    try:
        # Step 1: Fetch news
        logger.info("\n[STEP 1/4] 📰 FETCHING NEWS FROM RSS FEEDS...")
        run_fetcher()
        
        # Step 2: Analyze news
        logger.info("\n[STEP 2/4] 🔍 ANALYZING AND DEDUPLICATING ARTICLES...")
        run_analyzer()
        
        # Step 3: Summarize with LLM
        logger.info("\n[STEP 3/4] 📝 GENERATING SUMMARIES WITH LLM...")
        run_summarizer()
        
        # Step 4: Deliver
        logger.info("\n[STEP 4/4] 📨 DELIVERING DIGEST...")
        delivery = DigestDelivery()
        digests = delivery.get_unsent_digests()
        
        sent_count = 0
        for digest in digests:
            telegram_sent = delivery.send_via_telegram(digest['content'])
            email_sent = delivery.send_via_email(digest['content'])
            
            if telegram_sent or email_sent:
                delivery.mark_digest_sent(digest['id'])
                sent_count += 1
        
        logger.info(f"\n✓ Delivered {sent_count}/{len(digests)} digests")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ DAILY PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ PIPELINE ERROR: {str(e)}", exc_info=True)


def setup_scheduler(schedule_time="08:00"):
    """Setup daily scheduler"""
    logger.info("=" * 80)
    logger.info("📅 NEWS DIGEST SCHEDULER")
    logger.info("=" * 80)
    logger.info(f"\n⏰ Scheduler configured to run daily at {schedule_time}")
    logger.info(f"   Current time: {datetime.now().strftime('%H:%M:%S')}")
    logger.info(f"   Timezone: System default")
    
    # Schedule the pipeline to run daily at specified time
    schedule.every().day.at(schedule_time).do(run_daily_pipeline)
    
    logger.info("\n✓ Scheduler initialized. Waiting for next scheduled run...")
    logger.info("  (Press Ctrl+C to stop)\n")
    
    # Keep scheduler running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("\n\n⏹️  Scheduler stopped by user")


def run_once():
    """Run the pipeline immediately once"""
    logger.info("\n🔄 Running pipeline immediately (one-time execution)...\n")
    run_daily_pipeline()


def print_menu():
    """Print scheduler menu"""
    print("\n" + "=" * 80)
    print("📰 RSS NEWS DIGEST SYSTEM - SCHEDULER")
    print("=" * 80)
    print("\nOptions:")
    print("  1. Run pipeline immediately (one-time)")
    print("  2. Schedule daily at 8:00 AM")
    print("  3. Schedule daily at custom time")
    print("  4. Exit")
    print("\n" + "=" * 80)


def main():
    """Main scheduler interface"""
    print_menu()
    
    while True:
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == "1":
            run_once()
        
        elif choice == "2":
            setup_scheduler("08:00")
        
        elif choice == "3":
            time_input = input("Enter time (HH:MM, e.g., 09:30): ").strip()
            try:
                # Validate time format
                datetime.strptime(time_input, "%H:%M")
                setup_scheduler(time_input)
            except ValueError:
                print("❌ Invalid time format. Use HH:MM (e.g., 09:30)")
        
        elif choice == "4":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid option. Please enter 1-4.")
        
        print_menu()


if __name__ == "__main__":
    main()
