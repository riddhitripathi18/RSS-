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
from core.chatbot import ask_chatbot
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
    st.session_state.chat_history = []  # list of {"role": ..., "content": ...}

# ───────────────────────────────────────────────────────────────────────────────
# Data Fetchers
# ───────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_db_engine():
    return init_db()

engine = get_db_engine()

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
    """Load articles only for the analytics tab — not exposed directly to users."""
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
    gemini_key_configured = bool(os.getenv("GEMINI_API_KEY"))
    telegram_configured = bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"))
    email_configured = bool(os.getenv("EMAIL_USERNAME") and os.getenv("EMAIL_PASSWORD"))

    if gemini_key_configured:
        chat_status = "🟢 Gemini (free)"
    elif openai_key_configured:
        chat_status = "🟡 OpenAI (paid)"
    else:
        chat_status = "🟠 Local Mode (no API)"

    st.markdown(f"**AI Chatbot**: {chat_status}")
    st.markdown(
        f"**OpenAI Summarizer**: {'🟢 Configured' if openai_key_configured else '🟡 Using Mock Summary'}"
    )
    st.markdown(
        f"**Telegram Dispatcher**: {'🟢 Enabled' if telegram_configured else '🔴 Disabled'}"
    )
    st.markdown(
        f"**Email Dispatcher**: {'🟢 Enabled' if email_configured else '🔴 Disabled'}"
    )
    
    st.markdown("---")
    st.markdown(f"**Feeds Configured**: `{len(RSS_FEEDS)} feeds`")
    st.markdown(f"**Lookback Window**: `{NEWS_HOURS_LOOKBACK} hours`")
    st.markdown(f"**Articles/Digest**: `{MAX_ARTICLES_PER_DIGEST} articles`")

    # Show current topic context in sidebar
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

# ───────────────────────────────────────────────────────────────────────────────
# Top-level Metrics
# ───────────────────────────────────────────────────────────────────────────────
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

# ───────────────────────────────────────────────────────────────────────────────
# Topic Search Bar (Always Visible)
# ───────────────────────────────────────────────────────────────────────────────
ui.render_search_bar()

QUICK_TOPICS = ["Apple", "AI", "Climate", "Economy", "Ukraine", "Technology", "Health"]

search_col, btn_col = st.columns([5, 1])
with search_col:
    topic_input = st.text_input(
        "Topic",
        value=st.session_state.searched_topic,
        placeholder="e.g. Apple, AI, Climate change, Ukraine...",
        label_visibility="collapsed",
        key="topic_input_field"
    )
with btn_col:
    search_btn = st.button("Search", type="primary", use_container_width=True, key="search_btn")

# Quick topic pills
st.markdown(
    " ".join([f"<span class='topic-pill'>{t}</span>" for t in QUICK_TOPICS]),
    unsafe_allow_html=True
)
st.caption("💡 Tip: Click Search to filter articles — the AI chatbot will answer questions about your results only.")

# Handle search
if search_btn and topic_input.strip():
    new_topic = topic_input.strip()
    if new_topic != st.session_state.searched_topic:
        # New topic → reset chat history
        st.session_state.chat_history = []
    st.session_state.searched_topic = new_topic
    with st.spinner(f"Searching articles about **{new_topic}**..."):
        st.session_state.topic_articles = search_articles_by_topic(engine, new_topic, limit=30, days=7)
    if not st.session_state.topic_articles:
        st.warning(f"No articles found for **{new_topic}** in the last 7 days. Try running the pipeline or a different keyword.")
    else:
        st.success(f"✅ Found **{len(st.session_state.topic_articles)}** articles about **{new_topic}**. Switch to the AI Chat tab to ask questions!")

st.markdown("---")

# ───────────────────────────────────────────────────────────────────────────────
# Tabs
# ───────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📰 Daily Digests",
    "🔍 Topic Articles",
    "🤖 AI Chat",
    "📊 System Analytics",
    "⚙️ Active RSS Feeds"
])

# ───────────────────────────────────────────────────────────────────────────────
# Tab 1: Daily Digests
# ───────────────────────────────────────────────────────────────────────────────
with tab1:
    ui.render_section_header('Generated News Digests')
    digests = load_digests()
    
    if not digests:
        st.info("No digests generated yet. Trigger a pipeline run from the sidebar!")
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

        st.markdown("### Content")
        st.code(selected_digest['Content'], language='text')

# ───────────────────────────────────────────────────────────────────────────────
# Tab 2: Topic Articles Explorer
# ───────────────────────────────────────────────────────────────────────────────
with tab2:
    if not st.session_state.searched_topic:
        st.info("👆 Use the **Search** bar above to find articles on a specific topic (e.g., 'Apple', 'AI', 'climate').")
        st.markdown("#### 🕐 Recent Headlines (last 48 hours)")
        recent = get_recent_articles(engine, limit=15, days=2)
        if recent:
            ui.render_topic_articles(recent)
        else:
            st.warning("No recent articles found. Run the pipeline to fetch today's news.")
    else:
        ui.render_section_header(f'📌 Results for: "{st.session_state.searched_topic}"')
        if st.session_state.topic_articles:
            st.caption(f"Showing {len(st.session_state.topic_articles)} articles · Max 30 per search · Last 7 days")
            ui.render_topic_articles(st.session_state.topic_articles)
        else:
            st.warning(f"No articles found for **{st.session_state.searched_topic}**. Try running the pipeline or a different keyword.")

# ───────────────────────────────────────────────────────────────────────────────
# Tab 3: AI Chatbot
# ───────────────────────────────────────────────────────────────────────────────
with tab3:
    has_topic = bool(st.session_state.searched_topic and st.session_state.topic_articles)
    
    # Header
    chat_header_col1, chat_header_col2 = st.columns([4, 1])
    with chat_header_col1:
        ui.render_section_header("🤖 DigestBot — Ask About Your Topic")
        if has_topic:
            gemini_key_configured = bool(os.getenv("GEMINI_API_KEY"))
            openai_key_configured = bool(os.getenv("OPENAI_API_KEY"))
            if gemini_key_configured:
                provider_label = "Gemini 2.0 Flash"
            elif openai_key_configured:
                provider_label = "gpt-4o-mini"
            else:
                provider_label = "Local Keyword Search (no API key)"
            st.caption(
                f"Context: **{len(st.session_state.topic_articles)} articles** about "
                f"**{st.session_state.searched_topic}** · Powered by {provider_label}"
            )
    with chat_header_col2:
        if st.session_state.chat_history:
            if st.button("🗑️ Clear Chat", key="clear_chat"):
                st.session_state.chat_history = []
                st.rerun()

    # Render chat messages
    if not st.session_state.chat_history:
        ui.render_chat_empty_state(has_topic)
    else:
        for msg in st.session_state.chat_history:
            ui.render_chat_message(msg["role"], msg["content"])

    # Chat input
    if has_topic:
        st.markdown("---")
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_input(
                "Ask a question",
                placeholder=f"e.g. What happened with {st.session_state.searched_topic}? Summarize the key developments.",
                label_visibility="collapsed",
                key="chat_input"
            )
            submitted = st.form_submit_button("Send ➤", type="primary", use_container_width=True)

        if submitted and user_input.strip():
            question = user_input.strip()

            # Append user message to history
            st.session_state.chat_history.append({"role": "user", "content": question})

            # Get answer from chatbot (pass history without the new question)
            history_for_llm = st.session_state.chat_history[:-1]  # exclude the just-added user msg
            with st.spinner("DigestBot is thinking..."):
                answer = ask_chatbot(
                    messages=history_for_llm,
                    question=question,
                    articles=st.session_state.topic_articles,
                    topic=st.session_state.searched_topic
                )

            # Append assistant response
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.rerun()
    else:
        st.markdown("---")
        st.info("🔍 Search a topic above first, then come back here to chat about the articles!")

# ───────────────────────────────────────────────────────────────────────────────
# Tab 4: System Analytics
# ───────────────────────────────────────────────────────────────────────────────
with tab4:
    ui.render_section_header('Deduplication & Feed Analytics')
    df_articles = load_articles_for_analytics()
    
    if df_articles.empty:
        st.info("Insufficient data to generate analytics.")
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
                font_color="#8892b0",
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
                marker_color='#007bff'
            ))
            fig_bar.add_trace(go.Bar(
                name='Duplicate Articles',
                x=dup_by_source['Source'],
                y=dup_by_source['Duplicate'],
                marker_color='#ffc107'
            ))
            
            fig_bar.update_layout(
                barmode='stack',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color="#8892b0",
                legend=dict(orientation="h", y=-0.1),
                xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
        dup_rate = (duplicates / total_articles * 100) if total_articles > 0 else 0
        st.markdown("---")
        st.markdown(f"#### 💡 Duplication Rate: **{dup_rate:.1f}%** of all fetched articles were identified as duplicates and filtered out.")

# ───────────────────────────────────────────────────────────────────────────────
# Tab 5: Active RSS Feeds
# ───────────────────────────────────────────────────────────────────────────────
with tab5:
    ui.render_section_header('Active RSS Subscriptions')
    st.write("These feeds are currently monitored by the aggregator agent during each pipeline run:")
    
    feeds_data = []
    for f in RSS_FEEDS:
        domain = f.split('//')[1].split('/')[0] if '//' in f else f
        feeds_data.append({
            "Feed Domain": domain,
            "Full RSS URL": f
        })
        
    st.table(pd.DataFrame(feeds_data))
