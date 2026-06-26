# pyrefly: ignore [missing-import]
import streamlit as st
# pyrefly: ignore [missing-import]
import pandas as pd
# pyrefly: ignore [missing-import]
import plotly.express as px
# pyrefly: ignore [missing-import]
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import sys
import logging
import io
import re

# Ensure the project root is in the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core.database import init_db, get_session, Article, Digest
from core.config import RSS_FEEDS, DATABASE_URL, NEWS_HOURS_LOOKBACK, MAX_ARTICLES_PER_DIGEST
from core.search import search_articles_by_topic, get_recent_articles
from core.chatbot import ask_chatbot, generate_150_word_summary, generate_trending_overview
from scripts.scheduler import run_daily_pipeline
from frontend import ui

# ───────────────────────────────────────────────────────────────────────────────
# Page Configuration & Styling
# ───────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI-Powered RSS Digest Hub",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

ui.load_custom_css()

# ───────────────────────────────────────────────────────────────────────────────
# Logging Interception
# ───────────────────────────────────────────────────────────────────────────────
class StreamlitLogHandler(logging.Handler):
    def __init__(self, placeholder):
        super().__init__()
        self.placeholder = placeholder
        self.log_stream = io.StringIO()
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.setFormatter(self.formatter)
        
    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_stream.write(msg + '\n')
            self.placeholder.code(self.log_stream.getvalue())
        except Exception:
            self.handleError(record)

# ───────────────────────────────────────────────────────────────────────────────
# Session State Init
# ───────────────────────────────────────────────────────────────────────────────
if "searched_topic" not in st.session_state:
    st.session_state.searched_topic = ""
if "topic_articles" not in st.session_state:
    st.session_state.topic_articles = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_page" not in st.session_state:
    st.session_state.current_page = "categories"
if "selected_categories" not in st.session_state:
    st.session_state.selected_categories = ["Updated", "Technology"]
if "active_article" not in st.session_state:
    st.session_state.active_article = None
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "All"
if "summary_format" not in st.session_state:
    st.session_state.summary_format = "TL;DR"
if "feed_limit" not in st.session_state:
    st.session_state.feed_limit = 20

# ───────────────────────────────────────────────────────────────────────────────
# Data Fetchers
# ───────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_db_engine():
    return init_db()

engine = get_db_engine()

# Intercept click tracking query parameters
query_params = st.query_params
if "read" in query_params:
    try:
        art_id_str = query_params["read"]
        session = get_session(engine)
        target_url = "/"
        try:
            db_art = None
            if art_id_str.isdigit():
                db_art = session.query(Article).filter_by(id=int(art_id_str)).first()
            
            if not db_art:
                for art in session.query(Article).all():
                    if str(abs(art.id)) == art_id_str or str(abs(hash(art.url))) == art_id_str:
                        db_art = art
                        break
            
            if db_art:
                db_art.click_count = (db_art.click_count or 0) + 1
                session.commit()
                target_url = db_art.url
        finally:
            session.close()
            
        # Redirect to external target
        st.markdown(f'<meta http-equiv="refresh" content="0; url={target_url}">', unsafe_allow_html=True)
        st.markdown(f'<script>window.location.replace("{target_url}");</script>', unsafe_allow_html=True)
        st.write(f"🔗 Redirecting to [article]({target_url})...")
        st.stop()
    except Exception as e:
        logging.getLogger(__name__).error(f"Error tracking click: {e}")

def load_metrics():
    session = get_session(engine)
    try:
        total_articles = session.query(Article).count()
        duplicates = session.query(Article).filter_by(is_duplicate=True).count()
        unprocessed = session.query(Article).filter_by(is_processed=False, is_duplicate=False).count()
        total_digests = session.query(Digest).count()
        return total_articles, duplicates, unprocessed, total_digests
    finally:
        session.close()

def load_digests():
    session = get_session(engine)
    try:
        digests = session.query(Digest).order_by(Digest.digest_date.desc()).all()
        data = []
        for d in digests:
            data.append({
                "ID": d.id,
                "Digest Date": d.digest_date,
                "Content": d.content,
                "Article Count": d.article_count,
                "Is Sent": d.is_sent,
                "Sent Date": d.sent_date
            })
        return data
    finally:
        session.close()

def load_articles_for_analytics(limit=1000):
    session = get_session(engine)
    try:
        articles = session.query(Article).order_by(Article.published_date.desc()).limit(limit).all()
        data = []
        for a in articles:
            data.append({
                "ID": a.id,
                "Title": a.title,
                "Source": a.source,
                "URL": a.url,
                "Published Date": a.published_date,
                "Fetched Date": a.fetched_date,
                "Is Duplicate": a.is_duplicate,
                "Is Processed": a.is_processed,
                "Description": a.description or ""
            })
        return pd.DataFrame(data)
    finally:
        session.close()

def ensure_article_summaries(engine, articles: list[dict]) -> list[dict]:
    if not articles:
        return []
    missing_idx = []
    for idx, a in enumerate(articles):
        content_word_count = len((a.get("content") or "").split())
        if content_word_count < 50:
            missing_idx.append(idx)
    if not missing_idx:
        return articles

    new_summaries = {}
    for idx in missing_idx:
        art = articles[idx]
        try:
            summary = generate_150_word_summary(art["title"], art["description"])
            new_summaries[idx] = summary
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed generating summary for article {art.get('id')}: {e}")
            new_summaries[idx] = art["description"]

    session = get_session(engine)
    try:
        for idx, summary in new_summaries.items():
            art = articles[idx]
            art["content"] = summary
            db_art = session.query(Article).filter_by(id=art["id"]).first()
            if db_art:
                db_art.content = summary
        session.commit()
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to save generated summaries to DB: {e}")
        session.rollback()
    finally:
        session.close()
    return articles

def ensure_article_bullets(engine, articles: list[dict]) -> list[dict]:
    if not articles:
        return []
    missing_idx = []
    for idx, a in enumerate(articles):
        bullets_word_count = len((a.get("bullets_content") or "").split())
        if bullets_word_count < 10:
            missing_idx.append(idx)
    if not missing_idx:
        return articles

    from core.chatbot import generate_key_takeaways
    new_summaries = {}
    for idx in missing_idx:
        art = articles[idx]
        try:
            summary = generate_key_takeaways(art["title"], art["description"])
            new_summaries[idx] = summary
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed generating bullets for article {art.get('id')}: {e}")
            new_summaries[idx] = f"- {art['description'] or art['title']}"

    session = get_session(engine)
    try:
        for idx, summary in new_summaries.items():
            art = articles[idx]
            art["bullets_content"] = summary
            db_art = session.query(Article).filter_by(id=art["id"]).first()
            if db_art:
                db_art.bullets_content = summary
        session.commit()
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to save generated bullets to DB: {e}")
        session.rollback()
    finally:
        session.close()
    return articles

def ensure_article_five_ws(engine, articles: list[dict]) -> list[dict]:
    if not articles:
        return []
    missing_idx = []
    for idx, a in enumerate(articles):
        five_ws_word_count = len((a.get("five_ws_content") or "").split())
        if five_ws_word_count < 10:
            missing_idx.append(idx)
    if not missing_idx:
        return articles

    from core.chatbot import generate_5ws_summary
    new_summaries = {}
    for idx in missing_idx:
        art = articles[idx]
        try:
            summary = generate_5ws_summary(art["title"], art["description"])
            new_summaries[idx] = summary
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed generating 5Ws for article {art.get('id')}: {e}")
            new_summaries[idx] = f"- **What**: {art['title']}"

    session = get_session(engine)
    try:
        for idx, summary in new_summaries.items():
            art = articles[idx]
            art["five_ws_content"] = summary
            db_art = session.query(Article).filter_by(id=art["id"]).first()
            if db_art:
                db_art.five_ws_content = summary
        session.commit()
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to save generated 5Ws to DB: {e}")
        session.rollback()
    finally:
        session.close()
    return articles

def prepare_summaries(engine, articles: list[dict], fmt: str) -> list[dict]:
    if fmt == "Bullets":
        return ensure_article_bullets(engine, articles)
    elif fmt == "5 Ws":
        return ensure_article_five_ws(engine, articles)
    else:
        return ensure_article_summaries(engine, articles)

def get_top_clicked_articles(engine, limit=10, hours=24) -> list[dict]:
    session = get_session(engine)
    try:
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
        return [
            {
                "id": a.id,
                "title": a.title,
                "source": a.source,
                "url": a.url,
                "description": a.description or "",
                "content": a.content or "",
                "bullets_content": a.bullets_content or "",
                "five_ws_content": a.five_ws_content or "",
                "published_date": a.published_date,
                "click_count": a.click_count or 0,
            }
            for a in articles
        ]
    finally:
        session.close()

def get_trending_overview_cached(engine, articles: list[dict]) -> str:
    if not articles:
        return "No trending articles are currently available."
    hashable_articles = tuple(tuple(sorted((k, v) for k, v in a.items() if k != 'click_count')) for a in articles)
    @st.cache_data(ttl=300, show_spinner=False)
    def _generate_cached(articles_data):
        reconstructed = [dict(item) for item in articles_data]
        return generate_trending_overview(reconstructed)
    return _generate_cached(hashable_articles)

# ───────────────────────────────────────────────────────────────────────────────
# Sidebar Section
# ───────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    ui.render_sidebar_logo()
    st.markdown("### ⚙️ Pipeline Controls")
    run_btn = st.button("⚡ Run Daily Pipeline Now", use_container_width=True, type="primary")
    if run_btn:
        st.info("Starting Daily News Pipeline...")
        log_expander = st.expander("Pipeline Output Logs", expanded=True)
        log_placeholder = log_expander.empty()
        root_logger = logging.getLogger()
        handler = StreamlitLogHandler(log_placeholder)
        root_logger.addHandler(handler)
        st.cache_resource.clear()
        try:
            run_daily_pipeline()
            st.success("✓ News Digest pipeline completed successfully!")
        except Exception as e:
            st.error(f"Error executing pipeline: {e}")
        finally:
            root_logger.removeHandler(handler)
            
    st.markdown("---")
    st.markdown("### 📋 Configuration Status")
    openai_key_configured = bool(os.getenv("OPENAI_API_KEY"))
    nvidia_key_configured = bool(os.getenv("NVIDIA_API_KEY"))
    telegram_configured = bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"))
    email_configured = bool(os.getenv("EMAIL_USERNAME") and os.getenv("EMAIL_PASSWORD"))

    if nvidia_key_configured:
        chat_status = "🟢 NVIDIA Llama (primary)"
    elif openai_key_configured:
        chat_status = "🟡 OpenAI (fallback)"
    else:
        chat_status = "🟠 Local Mode (no API)"

    st.markdown(f"**AI Chatbot**: {chat_status}")
    st.markdown(f"**OpenAI Summarizer**: {'🟢 Configured' if openai_key_configured else '🟡 Using Mock Summary'}")
    st.markdown(f"**Telegram Dispatcher**: {'🟢 Enabled' if telegram_configured else '🔴 Disabled'}")
    st.markdown(f"**Email Dispatcher**: {'🟢 Enabled' if email_configured else '🔴 Disabled'}")

    st.markdown("---")
    st.markdown("### 🔑 Debug: API Key Preview")
    def mask_key(key: str) -> str:
        if not key:
            return "❌ NOT LOADED"
        return f"✅ {key[:8]}...{key[-4:]}"
    _raw_openai = os.getenv("OPENAI_API_KEY", "")
    _raw_nvidia  = os.getenv("NVIDIA_API_KEY", "")
    st.code(f"OPENAI : {mask_key(_raw_openai)}", language="text")
    st.code(f"NVIDIA : {mask_key(_raw_nvidia)}",  language="text")

    st.markdown("---")
    st.markdown(f"**Feeds Configured**: `{len(RSS_FEEDS)} feeds`")
    st.markdown(f"**Lookback Window**: `{NEWS_HOURS_LOOKBACK} hours`")
    st.markdown(f"**Articles/Digest**: `{MAX_ARTICLES_PER_DIGEST} articles`")

    if st.session_state.searched_topic:
        st.markdown("---")
        st.markdown("### 🎯 Active Topic")
        st.markdown(f"`{st.session_state.searched_topic}`")
        st.caption(f"{len(st.session_state.topic_articles)} articles in context")
        if st.button("🗑️ Clear Topic", use_container_width=True):
            st.session_state.searched_topic = ""
            st.session_state.topic_articles = []
            st.session_state.chat_history = []
            st.rerun()

# ───────────────────────────────────────────────────────────────────────────────
# Auto-Update Check
# ───────────────────────────────────────────────────────────────────────────────
def check_and_run_pipeline_if_needed():
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
            st.info("Auto-triggering Daily News Pipeline...")
            log_expander = st.expander("Pipeline Output Logs", expanded=True)
            log_placeholder = log_expander.empty()
            root_logger = logging.getLogger()
            handler = StreamlitLogHandler(log_placeholder)
            root_logger.addHandler(handler)
            try:
                with st.spinner("Running Daily Pipeline... (See logs below)"):
                    run_daily_pipeline()
                    st.cache_resource.clear()
                    st.rerun()
            finally:
                root_logger.removeHandler(handler)
    except Exception as e:
        st.error(f"Error checking updates: {e}")
    finally:
        session.close()

check_and_run_pipeline_if_needed()

# Helper to filter articles by category
def filter_articles_by_category(articles, category):
    if not category or category == "All" or category == "Updated":
        return articles
    filtered = []
    category_lower = category.lower()
    for a in articles:
        title = (a.get("title") or "").lower()
        source = (a.get("source") or "").lower()
        
        # Split title into distinct alphanumeric words
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

# ───────────────────────────────────────────────────────────────────────────────
# Main Layout Render depending on page state
# ───────────────────────────────────────────────────────────────────────────────

# Top Navigation Bar
new_page = ui.render_app_navigation(st.session_state.current_page)
if new_page != st.session_state.current_page:
    st.session_state.current_page = new_page
    st.rerun()

st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

# Page 1: Categories Onboarding Selection Screen
if st.session_state.current_page == "categories":
    st.markdown('<div style="text-align: center; margin-bottom: 24px; margin-top: 20px;">', unsafe_allow_html=True)
    st.markdown('<h1 style="font-family: \'Playfair Display\', serif; font-size: 3rem; margin-bottom: 5px;">The News</h1>', unsafe_allow_html=True)
    st.markdown('<h2 style="font-family: \'Plus Jakarta Sans\', sans-serif; font-size: 1.4rem; font-weight: 600; color: #b55e2a; margin-top: 0;">Choose Categories</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color: rgba(255, 255, 255, 0.7); font-size: 0.95rem;">Choose your favorite topics and personalize your news feed</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    categories = [
        {"badge": "Always Updated", "title": "Updated", "desc": "Latest news highlights", "icon": ""},
        {"badge": "Political Updates", "title": "Politics", "desc": "Latest political news", "icon": ""},
        {"badge": "Tech Trends", "title": "Technology", "desc": "Innovations and trends", "icon": ""},
        {"badge": "Game Highlights", "title": "Sports", "desc": "Latest sports news", "icon": ""},
        {"badge": "World Updates", "title": "International", "desc": "Global news updates", "icon": ""},
        {"badge": "Top Stories", "title": "Media", "desc": "Trending media stories", "icon": ""},
        {"badge": "Financial Insights", "title": "Stock Market", "desc": "Market trends and finance", "icon": ""}
    ]
    
    for i in range(0, len(categories), 2):
        col_left, col_right = st.columns(2)
        c_left = categories[i]
        with col_left:
            is_sel_left = c_left["title"] in st.session_state.selected_categories
            if ui.render_category_card(c_left["badge"], c_left["title"], c_left["desc"], c_left["icon"], is_sel_left, f"cat_btn_{c_left['title']}"):
                if is_sel_left:
                    st.session_state.selected_categories.remove(c_left["title"])
                else:
                    st.session_state.selected_categories.append(c_left["title"])
                st.rerun()
                
        if i + 1 < len(categories):
            c_right = categories[i + 1]
            with col_right:
                is_sel_right = c_right["title"] in st.session_state.selected_categories
                if ui.render_category_card(c_right["badge"], c_right["title"], c_right["desc"], c_right["icon"], is_sel_right, f"cat_btn_{c_right['title']}"):
                    if is_sel_right:
                        st.session_state.selected_categories.remove(c_right["title"])
                    else:
                        st.session_state.selected_categories.append(c_right["title"])
                    st.rerun()
                    
    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
    if st.button("Continue", type="primary", use_container_width=True, key="continue_to_feed"):
        st.session_state.current_page = "feed"
        st.rerun()

# Page 2: News Feed Screen
elif st.session_state.current_page == "feed":
    search_col, profile_col = st.columns([5, 1])
    with search_col:
        topic_input = st.text_input(
            "Search",
            value=st.session_state.searched_topic,
            placeholder="🔍 Search articles by topic...",
            label_visibility="collapsed",
            key="feed_search_input"
        )
    with profile_col:
        st.markdown("""
        <div style="display: flex; justify-content: flex-end; align-items: center; height: 100%;">
            <div style="width: 42px; height: 42px; border-radius: 50%; background: #b55e2a; color: white; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.1rem; border: 2px solid white; box-shadow: 0 4px 10px rgba(0,0,0,0.15);">
                U
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    if topic_input.strip() != st.session_state.searched_topic:
        st.session_state.searched_topic = topic_input.strip()
        if topic_input.strip():
            with st.spinner("Searching topic..."):
                st.session_state.topic_articles = search_articles_by_topic(engine, topic_input.strip(), limit=30, days=7)
        else:
            st.session_state.topic_articles = []
        st.session_state.feed_limit = 20
        st.rerun()



    # Hero Banner
    ui.render_hero_headlines_card()

    # Trending Section
    top_10 = get_top_clicked_articles(engine, limit=10, hours=24)
    if top_10:
        with st.spinner("Generating trending updates..."):
            top_10 = prepare_summaries(engine, top_10, st.session_state.summary_format)
            overview_text = get_trending_overview_cached(engine, top_10)
        
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.06);
                    border: 1px solid rgba(255,255,255,0.1);
                    border-radius: 20px;
                    padding: 22px;
                    margin-top: 15px;
                    margin-bottom: 20px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
                    font-size: 0.95rem;
                    color: rgba(255,255,255,0.9);
                    line-height: 1.6;">
            <h4 style="margin: 0 0 10px 0; color: #b55e2a; font-size: 1.25rem; display: flex; align-items: center; gap: 8px; font-family: 'Playfair Display', serif;">
                Trending: Last 24 Hours Overview
            </h4>
            {ui.format_to_html(overview_text)}
        </div>
        """, unsafe_allow_html=True)

    # Perspective Format Selection
    st.markdown("""
    <div style='margin-bottom: 8px; font-size: 0.75rem; color: rgba(255,255,255,0.6); text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700;'>
        📄 Perspective Mode
    </div>
    """, unsafe_allow_html=True)
    
    perspective_cols = st.columns(3)
    perspectives = [("TL;DR", "📄 TL;DR Summary"), ("Bullets", "⚡ Key Takeaways"), ("5 Ws", "❓ 5 Ws Analysis")]
    for idx, (p_id, label) in enumerate(perspectives):
        with perspective_cols[idx]:
            is_active = st.session_state.summary_format == p_id
            if st.button(label, key=f"perspective_btn_{p_id}", use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state.summary_format = p_id
                st.rerun()

    # Category Pill Selection
    st.markdown("""
    <div style='margin-top: 15px; margin-bottom: 8px; font-size: 0.75rem; color: rgba(255,255,255,0.6); text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700;'>
        📁 Personal Feed Filters
    </div>
    """, unsafe_allow_html=True)
    
    active_cats = ["All"] + st.session_state.selected_categories
    pill_cols = st.columns(len(active_cats))
    for idx, cat in enumerate(active_cats):
        with pill_cols[idx]:
            is_active = st.session_state.active_tab == cat
            if st.button(cat, key=f"pill_cat_{cat}", use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state.active_tab = cat
                st.session_state.feed_limit = 20
                st.rerun()

    # Fetch and filter feed articles
    if st.session_state.searched_topic:
        feed_articles = st.session_state.topic_articles
        
        # Clear Search Header
        title_col, btn_col = st.columns([4, 1])
        with title_col:
            st.markdown(f"### Results for \"{st.session_state.searched_topic}\" ({len(feed_articles)})")
        with btn_col:
            if st.button("Clear Search ❌", use_container_width=True, key="clear_search_header_btn"):
                st.session_state.searched_topic = ""
                st.session_state.topic_articles = []
                st.session_state.feed_limit = 20
                st.rerun()
    else:
        feed_articles = get_recent_articles(engine, limit=1000, days=2)
        
    filtered_articles = filter_articles_by_category(feed_articles, st.session_state.active_tab)
    
    if not filtered_articles:
        if st.session_state.searched_topic:
            st.info("No matching articles found for this topic and category. Try clearing your search or using a different query!")
        else:
            st.info("No articles found in this category. Try running the pipeline or choosing other filters!")
    else:
        # Optimisation: Do not prepare summaries for the entire list (it hits APIs / takes time).
        # We only prepare summaries for the paginated subset of articles currently displayed.
        display_articles = filtered_articles[:st.session_state.feed_limit]
        
        with st.spinner("Preparing AI summaries..."):
            display_articles = prepare_summaries(engine, display_articles, st.session_state.summary_format)
            
        for idx, a in enumerate(display_articles):
            play_clicked, chat_clicked = ui.render_feed_article_card(a, idx, st.session_state.summary_format)
            if play_clicked:
                st.session_state.active_article = a
                st.session_state.current_page = "detail"
                st.rerun()
            if chat_clicked:
                st.session_state.active_article = a
                st.session_state.current_page = "chat"
                st.rerun()
                
        if len(filtered_articles) > st.session_state.feed_limit:
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            if st.button("Load More Articles", use_container_width=True, key="load_more_btn"):
                st.session_state.feed_limit += 20
                st.rerun()

# Page 3: Audio Detail View Screen
elif st.session_state.current_page == "detail":
    if not st.session_state.active_article:
        st.info("No article selected. Return to feed to choose an article.")
        if st.button("Back to Feed", key="back_to_feed_err"):
            st.session_state.current_page = "feed"
            st.rerun()
    else:
        a = st.session_state.active_article
        safe_id = abs(int(a.get("id") or hash(a["url"])))
        
        if st.button("Back to Feed", key="back_to_feed_ok"):
            st.session_state.current_page = "feed"
            st.rerun()
        
        # Generate summary first
        with st.spinner("Generating summary..."):
            a_list = prepare_summaries(engine, [a], st.session_state.summary_format)
            a = a_list[0]
            st.session_state.active_article = a
            
        if st.session_state.summary_format == "Bullets":
            text_to_display = a.get("bullets_content") or a.get("description") or ""
        elif st.session_state.summary_format == "5 Ws":
            text_to_display = a.get("five_ws_content") or a.get("description") or ""
        else:
            text_to_display = a.get("content") or a.get("description") or ""
            
        pub_date_str = a["published_date"].strftime("%B %d, %Y %H:%M") if a.get("published_date") else "N/A"
        
        # Audio Player layout (with generated summary text content for voice generation)
        ui.render_audio_player(a["title"], a["source"], pub_date_str, text_content=text_to_display)
        
        # Summary Formats Switcher
        st.markdown("### AI Analysis Options")
        format_cols = st.columns(3)
        formats = [("TL;DR", "TL;DR Summary"), ("Bullets", "Key Takeaways"), ("5 Ws", "5 Ws Analysis")]
        for idx, (f_id, label) in enumerate(formats):
            with format_cols[idx]:
                is_active = st.session_state.summary_format == f_id
                if st.button(label, key=f"detail_fmt_{f_id}", use_container_width=True, type="primary" if is_active else "secondary"):
                    st.session_state.summary_format = f_id
                    st.rerun()
                    
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.06); border-radius: 20px; padding: 24px; border: 1px solid rgba(255,255,255,0.1); line-height: 1.6;">
            <h4 style="margin-top:0; color:#b55e2a !important;">AI Generated Content ({st.session_state.summary_format})</h4>
            <div style="color: rgba(255,255,255,0.9); font-size: 0.95rem;">{ui.format_to_html(text_to_display)}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Discuss Chat widget specifically for this article inside detail player view
        st.markdown("---")
        st.markdown("### Chat About This Article")
        chat_key = f"art_chat_{safe_id}"
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []
            
        for msg in st.session_state[chat_key]:
            ui.render_chat_message(msg["role"], msg["content"])
            
        with st.form(key=f"detail_chat_form_{safe_id}", clear_on_submit=True):
            user_q = st.text_input(
                "Ask a question about this article:",
                placeholder="e.g. What is the impact? / Summarize key points...",
                label_visibility="collapsed"
            )
            chat_send = st.form_submit_button("Ask Assistant", type="primary")
            
        if chat_send and user_q.strip():
            with st.spinner("AI is thinking..."):
                answer = ask_chatbot(
                    messages=st.session_state[chat_key],
                    question=user_q.strip(),
                    articles=[a],
                    topic=a["title"]
                )
            st.session_state[chat_key].append({"role": "user", "content": user_q.strip()})
            st.session_state[chat_key].append({"role": "assistant", "content": answer})
            st.rerun()

# Page 4: AI Chatbot Screen
elif st.session_state.current_page == "chat":
    ui.render_section_header("DigestBot Chat Assistant")
    
    if st.session_state.active_article:
        chat_articles = [st.session_state.active_article]
        chat_topic = st.session_state.active_article["title"]
        st.info(f"Active Chat Context: **{chat_topic}**")
        if st.button("Reset Chat Context (use all articles)", key="reset_chat_context"):
            st.session_state.active_article = None
            st.rerun()
    else:
        chat_articles = get_recent_articles(engine, limit=15, days=2)
        chat_topic = "Recent Articles"
        st.caption("Context: 15 recent articles (default context)")
        
    if st.session_state.chat_history:
        if st.button("Clear Chat History", key="clear_chat_hist"):
            st.session_state.chat_history = []
            st.rerun()
            
    if not st.session_state.chat_history:
        ui.render_chat_empty_state(bool(chat_articles))
    else:
        for msg in st.session_state.chat_history:
            ui.render_chat_message(msg["role"], msg["content"])
            
    if chat_articles:
        st.markdown("---")
        with st.form(key="global_chat_form", clear_on_submit=True):
            user_input = st.text_input(
                "Ask a question",
                placeholder=f"Ask a question about {chat_topic}...",
                label_visibility="collapsed",
                key="global_chat_input"
            )
            submitted = st.form_submit_button("Send", type="primary")
            
        if submitted and user_input.strip():
            question = user_input.strip()
            st.session_state.chat_history.append({"role": "user", "content": question})
            history_for_llm = st.session_state.chat_history[:-1]
            with st.spinner("DigestBot is thinking..."):
                answer = ask_chatbot(
                    messages=history_for_llm,
                    question=question,
                    articles=chat_articles,
                    topic=chat_topic
                )
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.rerun()

# Page 5: Workspace Analytics & Feeds
elif st.session_state.current_page == "analytics":
    ui.render_section_header("System Workspace & Analytics")
    
    total_articles, duplicates, unprocessed, total_digests = load_metrics()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ui.render_metric_card("Articles in DB", total_articles)
    with col2:
        ui.render_metric_card("Duplicates Filtered", duplicates)
    with col3:
        ui.render_metric_card("Unprocessed Unique", unprocessed)
    with col4:
        ui.render_metric_card("Digests Generated", total_digests)
        
    st.markdown("### Generated Daily Digests")
    digests = load_digests()
    if not digests:
        st.info("No digests generated yet. Run the pipeline in the sidebar!")
    else:
        digest_options = {
            f"Digest #{d['ID']} ({d['Digest Date'].strftime('%Y-%m-%d %H:%M')}) - {d['Article Count']} articles": d 
            for d in digests
        }
        selected_key = st.selectbox("Select Digest to view", list(digest_options.keys()))
        selected_digest = digest_options[selected_key]
        
        meta_col1, meta_col2 = st.columns(2)
        with meta_col1:
            st.markdown(f"**Date Generated**: {selected_digest['Digest Date'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
        with meta_col2:
            ui.render_delivery_status(selected_digest['Is Sent'])
            if selected_digest['Sent Date']:
                st.caption(f"Sent at: {selected_digest['Sent Date'].strftime('%Y-%m-%d %H:%M:%S')}")
        st.code(selected_digest['Content'], language='text')

    st.markdown("---")
    st.markdown("### 📈 Source Deduplication Analytics")
    df_articles = load_articles_for_analytics()
    if df_articles.empty:
        st.info("Insufficient data to generate charts.")
    else:
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.subheader("Articles Volume by Feed Source")
            source_counts = df_articles["Source"].value_counts().reset_index()
            source_counts.columns = ["Source", "Articles"]
            fig = px.pie(
                source_counts, 
                names="Source", 
                values="Articles",
                color_discrete_sequence=px.colors.sequential.Tealgrn,
                hole=0.4
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color="#ffffff",
                legend=dict(orientation="h", y=-0.1)
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with chart_col2:
            st.subheader("Deduplication Breakdown by Feed")
            dup_by_source = df_articles.groupby(["Source", "Is Duplicate"]).size().unstack(fill_value=0).reset_index()
            if True not in dup_by_source.columns:
                dup_by_source[True] = 0
            if False not in dup_by_source.columns:
                dup_by_source[False] = 0
            dup_by_source.columns = ["Source", "Unique", "Duplicate"]
            
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                name='Unique Articles',
                x=dup_by_source['Source'],
                y=dup_by_source['Unique'],
                marker_color='#b55e2a'
            ))
            fig_bar.add_trace(go.Bar(
                name='Duplicate Articles',
                x=dup_by_source['Source'],
                y=dup_by_source['Duplicate'],
                marker_color='rgba(255,255,255,0.2)'
            ))
            fig_bar.update_layout(
                barmode='stack',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color="#ffffff",
                legend=dict(orientation="h", y=-0.1),
                xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")
    st.markdown("### ⚙️ Active RSS Subscriptions")
    feeds_data = []
    for f in RSS_FEEDS:
        domain = f.split('//')[1].split('/')[0] if '//' in f else f
        feeds_data.append({
            "Feed Domain": domain,
            "Full RSS URL": f
        })
    st.table(pd.DataFrame(feeds_data))


