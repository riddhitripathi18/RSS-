"""
News Analysis Agent - Deduplicates, groups, and ranks articles
"""
from core.database import Article, get_session, init_db
from difflib import SequenceMatcher
import logging
from core.config import MAX_ARTICLES_PER_DIGEST

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NewsAnalyzer:
    """Analyzes and processes news articles"""
    
    def __init__(self):
        self.engine = init_db()
        self.similarity_threshold = 0.6  # 60% similarity = same story
    
    def calculate_similarity(self, text1, text2):
        """Calculate similarity between two texts using SequenceMatcher"""
        if not text1 or not text2:
            return 0
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def find_duplicate_articles(self):
        """Find and mark duplicate articles"""
        session = get_session(self.engine)
        
        # Only check articles that haven't been processed yet
        unprocessed_articles = session.query(Article).filter_by(
            is_duplicate=False, 
            is_processed=False
        ).all()
        
        if not unprocessed_articles:
            session.close()
            return 0
            
        from datetime import datetime, timedelta
        # Get recent articles (last 3 days) to compare against
        cutoff_date = datetime.utcnow() - timedelta(days=3)
        recent_articles = session.query(Article).filter(
            Article.is_duplicate == False,
            Article.published_date >= cutoff_date
        ).all()
        
        logger.info(f"Comparing {len(unprocessed_articles)} new articles against {len(recent_articles)} recent articles for duplicates...")
        duplicates_found = 0
        
        for i, article1 in enumerate(unprocessed_articles):
            if i % 20 == 0:
                logger.info(f"  Progress: {i}/{len(unprocessed_articles)} articles processed...")
            
            for article2 in recent_articles:
                if article1.id == article2.id:
                    continue
                    
                # Skip if we already marked this one
                if article1.is_duplicate:
                    break
                
                # Check title similarity
                title_similarity = self.calculate_similarity(article1.title, article2.title)
                
                # Skip if titles are not similar enough
                if title_similarity < 0.5:
                    continue
                
                # Check description similarity
                desc_similarity = 0
                if article1.description and article2.description:
                    desc_similarity = self.calculate_similarity(
                        article1.description[:200],  # Compare first 200 chars
                        article2.description[:200]
                    )
                
                # Average similarity
                avg_similarity = (title_similarity + desc_similarity) / 2
                
                if avg_similarity >= self.similarity_threshold:
                    # Mark the newer article as duplicate
                    article1.is_duplicate = True
                    duplicates_found += 1
                    if duplicates_found % 5 == 0:
                        logger.debug(
                            f"Duplicate found ({avg_similarity:.2%}): "
                            f"'{article1.title[:50]}...'"
                        )
                    break # No need to check this article1 against others
        
        session.commit()
        logger.info(f"✓ Found and marked {duplicates_found} duplicate articles")
        session.close()
        return duplicates_found
    
    def group_related_articles(self):
        """Group related articles by topic/keywords"""
        session = get_session(self.engine)
        
        # Get non-duplicate articles
        articles = session.query(Article).filter_by(
            is_duplicate=False,
            is_processed=False
        ).all()
        
        articles_by_group = {}
        
        for article in articles:
            # Extract keywords from title (simple approach)
            keywords = self._extract_keywords(article.title)
            
            # Find or create group
            group_key = keywords[0] if keywords else "Other"
            
            if group_key not in articles_by_group:
                articles_by_group[group_key] = []
            
            articles_by_group[group_key].append(article)
        
        logger.info(f"✓ Grouped articles into {len(articles_by_group)} topics")
        session.close()
        return articles_by_group
    
    def _extract_keywords(self, title):
        """Extract important keywords from title (simple method)"""
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'is', 'was', 'are', 'were', 'be', 'been', 'being', 'have', 'has',
            'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }
        
        words = title.lower().split()
        keywords = [w.strip('.,!?;:') for w in words if w.lower() not in stop_words]
        return keywords[:3]  # Return top 3 keywords
    
    def rank_articles(self, articles):
        """Rank articles by importance score"""
        scored_articles = []
        
        for article in articles:
            score = 0
            
            # Score based on recency (newer = higher score)
            if article.published_date:
                from datetime import datetime, timedelta
                age_hours = (datetime.utcnow() - article.published_date).total_seconds() / 3600
                recency_score = max(0, 10 - (age_hours / 2))  # Decreases with age
                score += recency_score * 0.3
            
            # Score based on source popularity
            popular_sources = {
                'The Guardian': 3,
                'Bloomberg Markets': 2.5,
                'NYT > World News': 2.5,
                'Reuters': 2,
                'BBC': 2
            }
            source_score = popular_sources.get(article.source, 1)
            score += source_score * 0.4
            
            # Score based on title relevance (keywords in title)
            if len(article.title.split()) > 5:
                score += 1 * 0.3
            
            scored_articles.append((article, score))
        
        # Sort by score (highest first)
        scored_articles.sort(key=lambda x: x[1], reverse=True)
        logger.info(f"✓ Ranked {len(scored_articles)} articles by importance")
        
        return scored_articles
    
    def get_top_articles(self, limit=MAX_ARTICLES_PER_DIGEST):
        """Get top articles for digest"""
        session = get_session(self.engine)
        
        articles = session.query(Article).filter_by(
            is_duplicate=False,
            is_processed=False,
            is_digested=False  # Skip articles already included in a previous digest
        ).all()
        
        ranked = self.rank_articles(articles)
        top_articles = [article for article, score in ranked[:limit]]
        
        # Mark as processed
        for article in top_articles:
            article.is_processed = True
        
        session.commit()
        
        # Convert to dict to avoid DetachedInstanceError
        articles_data = [
            {
                'id': a.id,
                'title': a.title,
                'url': a.url,
                'description': a.description,
                'source': a.source,
                'published_date': a.published_date
            }
            for a in top_articles
        ]
        
        logger.info(f"✓ Selected top {len(top_articles)} articles for digest")
        session.close()
        
        return articles_data


def run_analyzer():
    """Main function to run the news analyzer"""
    analyzer = NewsAnalyzer()
    
    logger.info("=" * 60)
    logger.info("🔍 News Analysis Agent Starting...")
    logger.info("=" * 60)
    
    # Find duplicates
    logger.info("\n1️⃣  Detecting duplicate articles...")
    analyzer.find_duplicate_articles()
    
    # Group related articles
    logger.info("\n2️⃣  Grouping related articles...")
    grouped = analyzer.group_related_articles()
    
    for group_name, articles in list(grouped.items())[:5]:
        logger.info(f"   {group_name}: {len(articles)} articles")
    
    # Get top articles
    logger.info("\n3️⃣  Ranking and selecting top articles...")
    top_articles = analyzer.get_top_articles()
    
    logger.info("\nTop articles selected:")
    for idx, article in enumerate(top_articles[:5], 1):
        logger.info(f"  {idx}. {article['title'][:60]}...")
        logger.info(f"     {article['source']}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ News Analysis Agent completed!")
    logger.info("=" * 60)
    logger.info("Next: Run summarizer.py to generate LLM summaries")


if __name__ == "__main__":
    run_analyzer()
