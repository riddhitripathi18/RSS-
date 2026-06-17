"""
Main entry point for RSS News Digest System
"""
import logging
from pipeline.fetcher import NewsFetcher
from core.config import LOG_LEVEL

# Setup logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function to orchestrate the news digest system"""
    try:
        logger.info("=" * 60)
        logger.info("🚀 RSS News Digest System Starting...")
        logger.info("=" * 60)
        
        # Step 1: Fetch news from all RSS feeds
        logger.info("\n📰 STEP 1: Fetching news from RSS feeds...")
        fetcher = NewsFetcher()
        saved_count = fetcher.fetch_all_feeds()
        logger.info(f"✓ Fetched and saved {saved_count} articles")
        
        # Step 2: Get unprocessed articles
        logger.info("\n📊 STEP 2: Retrieving unprocessed articles...")
        articles = fetcher.get_unprocessed_articles(limit=20)
        logger.info(f"✓ Found {len(articles)} articles to process")
        
        if articles:
            logger.info("\nLatest articles:")
            for idx, article in enumerate(articles[:5], 1):
                logger.info(f"  {idx}. {article.title}")
                logger.info(f"     Source: {article.source} | Published: {article.published_date}")
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ News Fetcher Agent completed successfully!")
        logger.info("=" * 60)
        logger.info("\nNext steps:")
        logger.info("  1. Run analyzer.py to deduplicate and group articles")
        logger.info("  2. Run summarizer.py to generate summaries with LLM")
        logger.info("  3. Run delivery.py to send the digest")
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
