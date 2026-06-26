from fastapi import FastAPI, Depends, Query, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import sys
import os
import re
import logging

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core.database import init_db, get_session, Article
from core.search import search_articles_by_topic, get_recent_articles
from core.chatbot import ask_chatbot, generate_150_word_summary, generate_key_takeaways, generate_5ws_summary, generate_trending_overview
from scripts.scheduler import run_daily_pipeline
from gtts import gTTS
import io

app = FastAPI(title="RSS News API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = init_db()
logger = logging.getLogger(__name__)

# --- Models ---
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    topic: str
    question: str
    history: List[ChatMessage]
    article_id: Optional[int] = None

class SummarizeRequest(BaseModel):
    article_id: int
    format: str

# --- Helper Functions (migrated from Streamlit app.py) ---
def prepare_summaries_db(session, article, fmt: str):
    updated = False
    try:
        if fmt == "Bullets" and (not article.bullets_content or len(article.bullets_content.split()) < 10):
            summary = generate_key_takeaways(article.title, article.description)
            article.bullets_content = summary
            updated = True
        elif fmt == "5 Ws" and (not article.five_ws_content or len(article.five_ws_content.split()) < 10):
            summary = generate_5ws_summary(article.title, article.description)
            article.five_ws_content = summary
            updated = True
        elif fmt == "TL;DR" and (not article.content or len(article.content.split()) < 50):
            summary = generate_150_word_summary(article.title, article.description)
            article.content = summary
            updated = True
        
        if updated:
            session.commit()
    except Exception as e:
        logger.error(f"Failed generating format {fmt} for article {article.id}: {e}")
        session.rollback()
    
    return article

def get_top_clicked_articles(session, limit=10, hours=24):
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    articles = (
        session.query(Article)
        .filter(
            Article.is_duplicate == False,
            Article.published_date >= cutoff
        )
        .order_by(Article.click_count.desc(), Article.published_date.desc())
        .limit(limit)
        .all()
    )
    return articles

def article_to_dict(article):
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
        "click_count": article.click_count or 0,
    }

def filter_articles_by_category(articles_dicts, category):
    if not category or category == "All" or category == "Updated":
        return articles_dicts
    filtered = []
    category_lower = category.lower()
    for a in articles_dicts:
        title = (a.get("title") or "").lower()
        title_words = set(re.findall(r'\b[a-z0-9]+\b', title))
        
        if category_lower == "politics":
            politics_keywords = {
                "politics", "government", "biden", "zelensky", "minister", "election", "senate", 
                "congress", "parliament", "political", "governor", "president", "putin", "kremlin", 
                "democracy", "republican", "democrat", "elections", "cabinet", "pm", "modi", "bjp", 
                "mp", "mla", "opposition", "ruling", "sanctions", "ambassador", "gandhi", "trump",
                "court", "defamation"
            }
            if politics_keywords.intersection(title_words):
                filtered.append(a)
                
        elif category_lower == "technology":
            tech_keywords = {
                "technology", "tech", "ai", "software", "nvidia", "apple", "google", "microsoft", 
                "intel", "amd", "semiconductor", "semiconductors", "microchips", "chips", "hacker", 
                "cybersecurity", "cyberattack", "robot", "robotics", "quantum", "openai", "telecom", 
                "iphone", "smartphones", "cryptocurrency", "blockchain", "metaverse", "data", "digital", 
                "devices", "device", "science", "scientific", "innovation", "innovations", "telecommunication"
            }
            if tech_keywords.intersection(title_words):
                filtered.append(a)
                
        elif category_lower == "sports":
            sports_keywords = {
                "sports", "cricket", "football", "match", "game", "olympic", "olympics", "cup", 
                "tennis", "championship", "tournament", "soccer", "basketball", "baseball", "golf", 
                "wimbledon", "f1", "racing", "athletics", "ipl", "fifa", "stadium", "league", "wicket",
                "player", "coach", "batsman"
            }
            if sports_keywords.intersection(title_words):
                filtered.append(a)
                
        elif category_lower == "international":
            intl_keywords = {
                "world", "global", "ukraine", "china", "russia", "israel", "gaza", "international", 
                "nato", "un", "syria", "taiwan", "brexit", "nuclear", "war", "pope", "embassy", 
                "refugees", "migration", "bilateral", "summit", "diplomatic", "treaty", "foreign",
                "us", "usa", "uk", "london", "paris", "tokyo", "beijing", "moscow", "washington", "iran", 
                "korea", "german", "germany", "france", "french", "europe", "european", "asia", "asian", 
                "africa", "african", "american", "america", "switzerland", "swiss", "dutch", "netherlands", 
                "spain", "spanish", "italy", "italian", "canada", "canadian", "mexico", "brazil", "australia", 
                "australian", "philippines", "seoul", "kyiv", "chornobyl", "turkey", "turkish", "egypt", 
                "pakistan", "afghanistan", "iraq", "saudi", "yemen", "singapore", "malaysia", "indonesia", 
                "thailand", "vietnam", "sweden", "norway", "norwegian", "denmark", "finland", "poland", 
                "ukrainian", "russian", "chinese", "british", "melbourne", "vancouver", "toronto"
            }
            if intl_keywords.intersection(title_words):
                filtered.append(a)
                
        elif category_lower == "stock market":
            market_keywords = {
                "stock", "stocks", "shares", "share", "nasdaq", "dow", "sp", "nifty", "sensex", "bse", 
                "nse", "ipo", "earnings", "dividend", "dividends", "yield", "yields", "securities", 
                "equities", "equity", "valuation", "investing", "investment", "investments", "investor", 
                "investors", "wallstreet", "ticker", "tickers", "trading", "broker", "brokerage", "index", 
                "bull", "bear", "portfolio", "portfolios", "marketwatch", "moneycontrol", "bloomberg"
            }
            if market_keywords.intersection(title_words):
                filtered.append(a)
                
        elif category_lower == "media":
            media_keywords = {
                "media", "news", "press", "journalism", "journalist", "journalists", "broadcast", 
                "broadcasting", "television", "tv", "radio", "newspaper", "newspapers", "reporting", 
                "reporter", "reporters", "social", "facebook", "twitter", "instagram", "tiktok", "youtube", 
                "streaming", "netflix", "disney", "warnermedia", "studios", "studio", "reuters", "nbc", 
                "bbc", "cnn", "nytimes"
            }
            if media_keywords.intersection(title_words):
                filtered.append(a)
    return filtered

# --- Endpoints ---

@app.get("/api/articles/recent")
def recent_articles(limit: int = 30, days: int = 7):
    return get_recent_articles(engine, limit=limit, days=days)

def check_and_run_pipeline():
    session = get_session(engine)
    try:
        today = datetime.utcnow().date()
        latest_article = session.query(Article).order_by(Article.fetched_date.desc()).first()
        needs_update = False
        if not latest_article:
            needs_update = True
        elif latest_article.fetched_date.date() < today:
            needs_update = True
            
        if needs_update:
            logger.info("Auto-triggering Daily News Pipeline...")
            try:
                run_daily_pipeline()
                logger.info("Pipeline completed successfully.")
            except Exception as e:
                logger.error(f"Error running pipeline: {e}")
    finally:
        session.close()

@app.post("/api/pipeline/check")
def trigger_pipeline_check(background_tasks: BackgroundTasks):
    background_tasks.add_task(check_and_run_pipeline)
    return {"message": "Pipeline check initiated in background"}

@app.get("/api/articles/search")
def search_articles(keyword: str, limit: int = 30, days: int = 7):
    return search_articles_by_topic(engine, keyword=keyword, limit=limit, days=days)

@app.get("/api/articles/category/{category}")
def category_articles(category: str, limit: int = 100, days: int = 7):
    recent = get_recent_articles(engine, limit=1000, days=days)
    filtered = filter_articles_by_category(recent, category)
    return filtered[:limit]

@app.get("/api/articles/{article_id}")
def get_article(article_id: int):
    session = get_session(engine)
    try:
        article = session.query(Article).filter(Article.id == article_id).first()
        if article:
            article.click_count = (article.click_count or 0) + 1
            session.commit()
            return article_to_dict(article)
        return {"error": "Article not found"}
    finally:
        session.close()

@app.post("/api/articles/summarize")
def summarize_article(req: SummarizeRequest):
    session = get_session(engine)
    try:
        article = session.query(Article).filter(Article.id == req.article_id).first()
        if article:
            article = prepare_summaries_db(session, article, req.format)
            return article_to_dict(article)
        return {"error": "Article not found"}
    finally:
        session.close()

@app.get("/api/trending")
def trending():
    session = get_session(engine)
    try:
        top_10 = get_top_clicked_articles(session, limit=10, hours=24)
        if top_10:
            for art in top_10:
                prepare_summaries_db(session, art, "TL;DR")
            top_10_dicts = [article_to_dict(a) for a in top_10]
            overview = generate_trending_overview(top_10_dicts)
            return {"overview": overview, "articles": top_10_dicts}
        return {"overview": "No trending articles are currently available.", "articles": []}
    finally:
        session.close()

@app.get("/api/audio/{article_id}")
def get_audio(article_id: int, format: str = "TL;DR"):
    session = get_session(engine)
    try:
        article = session.query(Article).filter_by(id=article_id).first()
        if not article:
            return Response(status_code=404)
        
        text_to_display = article.description or article.title
        if format == "Bullets" and article.bullets_content:
            text_to_display = article.bullets_content
        elif format == "5 Ws" and article.five_ws_content:
            text_to_display = article.five_ws_content
        elif article.content:
            text_to_display = article.content
            
        clean_text = text_to_display or ""
        clean_text = re.sub(r'<[^>]+>', '', clean_text)
        clean_text = re.sub(r'\*+', '', clean_text)
        clean_text = re.sub(r'#+', '', clean_text)
        clean_text = clean_text[:1500].strip()
        
        if not clean_text:
            return Response(status_code=404)

        tts = gTTS(text=clean_text, lang='en')
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        
        return Response(content=audio_fp.getvalue(), media_type="audio/mp3")
    except Exception as e:
        logger.error(f"TTS Error: {e}")
        return Response(status_code=500)
    finally:
        session.close()

@app.post("/api/chat")
def chat(request: ChatRequest):
    session = get_session(engine)
    try:
        articles = []
        if request.article_id:
            article = session.query(Article).filter_by(id=request.article_id).first()
            if article:
                articles = [article_to_dict(article)]
        else:
            articles = get_recent_articles(engine, limit=15, days=2)
            
        messages = [{"role": m.role, "content": m.content} for m in request.history]
        
        answer = ask_chatbot(
            messages=messages,
            question=request.question,
            articles=articles,
            topic=request.topic
        )
        return {"answer": answer}
    finally:
        session.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
