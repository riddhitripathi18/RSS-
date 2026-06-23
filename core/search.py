"""
Search module - Keyword-based article search from the database
Keeps token usage low by only retrieving relevant articles
"""
from core.database import Article, get_session
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def search_articles_by_topic(engine, keyword: str, limit: int = 30, days: int = 7) -> list[dict]:
    """
    Search articles in the DB that match a keyword in title or description.
    Returns at most `limit` articles from the last `days` days.
    
    This is the core function that prevents sending all 700+ articles to LLM.
    """
    session = get_session(engine)
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)

        # Split multi-word queries into individual words and match titles
        # containing ANY of them.  e.g. "stock market" matches titles with
        # "stock" OR "market" (headlines rarely use exact user phrases).
        from sqlalchemy import or_
        words = [w.strip() for w in keyword.split() if w.strip()]
        if not words:
            return []

        title_filters = [Article.title.ilike(f"%{w}%") for w in words]

        articles = (
            session.query(Article)
            .filter(
                Article.is_duplicate == False,
                Article.published_date >= cutoff,
                or_(*title_filters)
            )
            .order_by(Article.published_date.desc())
            .limit(limit)
            .all()
        )

        logger.info(f"Topic search '{keyword}' (words={words}): found {len(articles)} articles (limit={limit}, days={days})")

        return [
            {
                "id": a.id,
                "title": a.title,
                "source": a.source,
                "url": a.url,
                "description": a.description or "",
                "content": a.content or "",
                "published_date": a.published_date,
                "click_count": a.click_count or 0,
            }
            for a in articles
        ]
    finally:
        session.close()


def get_recent_articles(engine, limit: int = 30, days: int = 2) -> list[dict]:
    """
    Fallback: get most recent non-duplicate articles if no keyword supplied.
    """
    session = get_session(engine)
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        articles = (
            session.query(Article)
            .filter(
                Article.is_duplicate == False,
                Article.published_date >= cutoff,
            )
            .order_by(Article.published_date.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": a.id,
                "title": a.title,
                "source": a.source,
                "url": a.url,
                "description": a.description or "",
                "content": a.content or "",
                "published_date": a.published_date,
                "click_count": a.click_count or 0,
            }
            for a in articles
        ]
    finally:
        session.close()
