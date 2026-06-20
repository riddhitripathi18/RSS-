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

# Premium Custom CSS
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

def load_articles(limit=1000):
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

# ───────────────────────────────────────────────────────────────────────────────
# Sidebar Section
# ───────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    ui.render_sidebar_logo()
    
    st.markdown("### ⚙️ Pipeline Controls")
    
    # Run pipeline manually
    run_btn = st.button("⚡ Run Daily Pipeline Now", use_container_width=True, type="primary")
    
    if run_btn:
        st.info("Starting Daily News Pipeline...")
        log_expander = st.expander("Pipeline Output Logs", expanded=True)
        log_placeholder = log_expander.empty()
        
        # Configure custom logger to capture print statements / logging output
        root_logger = logging.getLogger()
        handler = StreamlitLogHandler(log_placeholder)
        root_logger.addHandler(handler)
        
        # Clear cache after run
        st.cache_resource.clear()
        
        try:
            # Run the scheduler pipeline
            run_daily_pipeline()
            st.success("✓ News Digest pipeline completed successfully!")
        except Exception as e:
            st.error(f"Error executing pipeline: {e}")
        finally:
            # Clean up logging handler
            root_logger.removeHandler(handler)
            
    st.markdown("---")
    st.markdown("### 📋 Configuration Status")
    
    # Check credentials
    openai_key_configured = bool(os.getenv("OPENAI_API_KEY"))
    telegram_configured = bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"))
    email_configured = bool(os.getenv("EMAIL_USERNAME") and os.getenv("EMAIL_PASSWORD"))
    
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

# ───────────────────────────────────────────────────────────────────────────────
# Auto-Update Check
# ───────────────────────────────────────────────────────────────────────────────
def check_and_run_pipeline_if_needed():
    session = get_session(engine)
    try:
        # Check if we have fetched anything today
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
# Main Layout
# ───────────────────────────────────────────────────────────────────────────────
# Load metrics
total_articles, duplicates, unprocessed, total_digests = load_metrics()

# Grid Metrics (Custom CSS Cards)
col1, col2, col3, col4 = st.columns(4)

with col1:
    ui.render_metric_card("Articles Fetched", total_articles)

with col2:
    ui.render_metric_card("Duplicates Filtered", duplicates)

with col3:
    ui.render_metric_card("Unprocessed Unique", unprocessed)

with col4:
    ui.render_metric_card("Digests Generated", total_digests)

# Tabs definitions
tab1, tab2, tab3, tab4 = st.tabs([
    "📰 Daily Digests", 
    "🔍 Articles Explorer", 
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
        # Left-hand selector for digests
        digest_options = {
            f"Digest #{d['ID']} ({d['Digest Date'].strftime('%Y-%m-%d %H:%M')}) - {d['Article_count'] if 'Article_count' in d else d['Article Count']} articles": d 
            for d in digests
        }
        
        selected_key = st.selectbox("Select Digest to view", list(digest_options.keys()))
        selected_digest = digest_options[selected_key]
        
        # Meta info
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
# Tab 2: Articles Explorer
# ───────────────────────────────────────────────────────────────────────────────
with tab2:
    ui.render_section_header('Filter and Explore Articles')
    df_articles = load_articles()
    
    if df_articles.empty:
        st.info("No articles fetched in database yet.")
    else:
        # Filtering controls
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        
        with filter_col1:
            sources = ["All"] + list(df_articles["Source"].unique())
            selected_source = st.selectbox("Filter by Source Feed", sources)
            
        with filter_col2:
            status_opts = ["All Articles", "Unique Only", "Duplicates Only", "Processed Only", "Unprocessed Only"]
            selected_status = st.selectbox("Filter by Status", status_opts)
            
        with filter_col3:
            search_query = st.text_input("Search titles or descriptions", "")
            
        # Apply filters
        df_filtered = df_articles.copy()
        
        if selected_source != "All":
            df_filtered = df_filtered[df_filtered["Source"] == selected_source]
            
        if selected_status == "Unique Only":
            df_filtered = df_filtered[df_filtered["Is Duplicate"] == False]
        elif selected_status == "Duplicates Only":
            df_filtered = df_filtered[df_filtered["Is Duplicate"] == True]
        elif selected_status == "Processed Only":
            df_filtered = df_filtered[df_filtered["Is Processed"] == True]
        elif selected_status == "Unprocessed Only":
            df_filtered = df_filtered[df_filtered["Is Processed"] == False]
            
        if search_query:
            df_filtered = df_filtered[
                df_filtered["Title"].str.contains(search_query, case=False, na=False) |
                df_filtered["Description"].str.contains(search_query, case=False, na=False)
            ]
            
        st.write(f"Showing **{len(df_filtered)}** matching articles")
        
        # Paginate or show inside scrollable container or expanders
        for idx, row in df_filtered.head(100).iterrows():
            badge_html = ""
            with st.container():
                ui.render_article_card_header(row)
                if row["Description"]:
                    # Strip raw HTML tags from the description for clean reading
                    clean_desc = re.sub(r'<[^>]+>', '', row["Description"])
                    st.write(clean_desc)
                st.markdown(f"[Read Original Article]({row['URL']})")
                ui.render_divider()

# ───────────────────────────────────────────────────────────────────────────────
# Tab 3: System Analytics
# ───────────────────────────────────────────────────────────────────────────────
with tab3:
    ui.render_section_header('Deduplication & Feed Analytics')
    df_articles = load_articles()
    
    if df_articles.empty:
        st.info("Insufficient data to generate analytics.")
    else:
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.subheader("Articles volume by Feed Source")
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
            
            # Map columns
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
            
        # Overall Duplication Metrics
        dup_rate = (duplicates / total_articles * 100) if total_articles > 0 else 0
        st.markdown("---")
        st.markdown(f"#### 💡 Duplication Rate: **{dup_rate:.1f}%** of all fetched articles were identified as duplicates and filtered out.")

# ───────────────────────────────────────────────────────────────────────────────
# Tab 4: Active RSS Feeds
# ───────────────────────────────────────────────────────────────────────────────
with tab4:
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
