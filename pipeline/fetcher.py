"""
News Fetcher Agent - Collects articles from RSS feeds
"""
# pyrefly: ignore [missing-import]
import feedparser
# pyrefly: ignore [missing-import]
import requests
from datetime import datetime, timedelta
from core.config import RSS_FEEDS, NEWS_HOURS_LOOKBACK
from core.database import Article, get_session, check_article_exists, init_db
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsFetcher:
    """Fetches news from RSS feeds"""
    
    def __init__(self):
        self.engine = init_db()
        self.articles_fetched = []
        self.hours_lookback = NEWS_HOURS_LOOKBACK
    
    def fetch_from_feed(self, feed_url):
        """Fetch articles from a single RSS feed"""
        try:
            logger.info(f"Fetching from: {feed_url}")
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                logger.warning(f"Feed parse warning for {feed_url}: {feed.bozo_exception}")
            
            articles = []
            cutoff_time = datetime.utcnow() - timedelta(hours=self.hours_lookback)
            
            for entry in feed.entries:
                # Extract publication date
                published_date = datetime.utcnow()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_date = datetime(*entry.published_parsed[:6])
                
                # Skip articles older than cutoff
                if published_date < cutoff_time:
                    continue
                
                # Extract article data
                article = Article(
                    title=entry.get('title', 'No Title'),
                    url=entry.get('link', ''),
                    description=entry.get('summary', ''),
                    source=feed.feed.get('title', 'Unknown Source'),
                    published_date=published_date
                )
                
                if article.url:
                    article.set_url_hash()
                    articles.append(article)
            
            logger.info(f"✓ Fetched {len(articles)} recent articles from {feed.feed.get('title', 'Unknown')}")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching from {feed_url}: {str(e)}")
            return []
    
    def fetch_all_feeds(self):
        """Fetch articles from all configured RSS feeds"""
        logger.info(f"Starting fetch from {len(RSS_FEEDS)} feeds...")
        
        session = get_session(self.engine)
        all_articles = []
        
        for feed_url in RSS_FEEDS:
            articles = self.fetch_from_feed(feed_url)
            all_articles.extend(articles)
        
        logger.info(f"Total articles fetched: {len(all_articles)}")
        
        # Save to database, avoiding duplicates
        saved_count = 0
        for article in all_articles:
            if not check_article_exists(session, article.url):
                session.add(article)
                saved_count += 1
            else:
                logger.info(f"Skipping duplicate: {article.title}")
        
        session.commit()
        logger.info(f"✓ Saved {saved_count} new articles to database")
        session.close()
        
        return saved_count
    
    def get_unprocessed_articles(self, limit=None):
        """Get articles that haven't been processed yet"""
        session = get_session(self.engine)
        query = session.query(Article).filter_by(is_processed=False)
        
        if limit:
            articles = query.limit(limit).all()
        else:
            articles = query.all()
        
        session.close()
        return articles


def run_fetcher():
    """Main function to run the news fetcher"""
    fetcher = NewsFetcher()
    saved_count = fetcher.fetch_all_feeds()
    return saved_count


if __name__ == "__main__":
    run_fetcher()
