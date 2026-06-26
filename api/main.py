from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import sys
import os

# Ensure the project root is in the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core.database import init_db, get_session, Article
from core.search import search_articles_by_topic, get_recent_articles

app = FastAPI(title="RSS News API")

# Allow CORS for React frontend (Vite defaults to port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = init_db()

@app.get("/api/articles/recent")
def recent_articles(limit: int = 30, days: int = 7):
    return get_recent_articles(engine, limit=limit, days=days)

@app.get("/api/articles/search")
def search_articles(keyword: str, limit: int = 30, days: int = 7):
    return search_articles_by_topic(engine, keyword=keyword, limit=limit, days=days)

@app.get("/api/articles/{article_id}")
def get_article(article_id: int):
    session = get_session(engine)
    try:
        article = session.query(Article).filter(Article.id == article_id).first()
        if article:
            article.click_count = (article.click_count or 0) + 1
            session.commit()
            return {
                "id": article.id,
                "title": article.title,
                "source": article.source,
                "url": article.url,
                "description": article.description or "",
                "content": article.content or "",
                "bullets_content": article.bullets_content or "",
                "five_ws_content": article.five_ws_content or "",
                "published_date": article.published_date,
                "click_count": article.click_count,
            }
        return {"error": "Article not found"}
    finally:
        session.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
