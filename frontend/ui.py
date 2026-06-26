"""
UI Components module for Streamlit App
Extracts HTML/CSS away from the main application logic
"""
# pyrefly: ignore [missing-import]
import streamlit as st
# pyrefly: ignore [missing-import]
import pandas as pd

def load_custom_css():
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400..900;1,400..900&family=Plus+Jakarta+Sans:ital,wght@0,200..800;1,200..800&display=swap');
    
    /* ─────────────────────────────────────────────────────────────────────────────
       Page background & custom premium font
       ───────────────────────────────────────────────────────────────────────────── */
    html, body,
    [data-testid="stApp"],
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"],
    section.main,
    .main {
        background: radial-gradient(circle at 10% 20%, #0c2b24 0%, #112d27 40%, #a25525 85%, #081a17 100%) !important;
        background-size: cover !important;
        background-attachment: fixed !important;
        color: #f8fafc !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    /* Streamlit block containers should be transparent so the page bg shows */
    [data-testid="stVerticalBlock"],
    [data-testid="stHorizontalBlock"],
    div.block-container {
        background-color: transparent !important;
    }
    
    /* Override Sidebar background to match the dark theme */
    [data-testid="stSidebar"] {
        background-color: rgba(12, 43, 36, 0.95) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    
    /* Clean, modern scrollbars */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(0,0,0,0.1);
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(255,255,255,0.1);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255,255,255,0.25);
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Playfair Display', serif !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        letter-spacing: -0.01em;
    }

    /* Onboarding Category Selection Cards */
    .category-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 16px;
        margin-bottom: 24px;
    }
    
    .category-item {
        background: rgba(255, 255, 255, 0.95) !important;
        border: 2px solid transparent !important;
        border-radius: 20px !important;
        padding: 20px !important;
        color: #1e293b !important;
        transition: all 0.25s ease !important;
        position: relative !important;
        text-align: left !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05) !important;
    }
    
    .category-item:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1) !important;
    }
    
    .category-item.selected {
        border-color: #b55e2a !important;
        background: #ffffff !important;
        box-shadow: 0 8px 25px rgba(181, 94, 42, 0.15) !important;
    }
    
    .category-badge-pill {
        font-size: 0.65rem !important;
        text-transform: uppercase !important;
        font-weight: 700 !important;
        letter-spacing: 1px !important;
        color: #b55e2a !important;
        margin-bottom: 8px !important;
        display: inline-block !important;
    }
    
    .category-icon-container {
        font-size: 1.6rem !important;
        margin-bottom: 8px !important;
    }
    
    .category-card-title {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        color: #0f172a !important;
        margin: 0 0 4px 0 !important;
    }
    
    .category-card-desc {
        font-size: 0.8rem !important;
        color: #64748b !important;
        margin: 0 !important;
        line-height: 1.35 !important;
    }



    /* Headlines Hero Card */
    .hero-headlines-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.94) 0%, rgba(248,250,252,0.96) 100%) !important;
        border-radius: 24px !important;
        padding: 24px !important;
        margin-bottom: 24px !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.08) !important;
        color: #0f172a !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
    }
    
    .hero-content {
        max-width: 70% !important;
    }
    
    .hero-tag {
        font-size: 0.75rem !important;
        font-weight: 700 !important;
        color: #b55e2a !important;
        text-transform: uppercase !important;
        margin-bottom: 6px !important;
        letter-spacing: 0.5px !important;
    }
    
    .hero-title {
        font-family: 'Playfair Display', serif !important;
        font-size: 2rem !important;
        font-weight: 800 !important;
        color: #0f172a !important;
        margin: 0 0 8px 0 !important;
        line-height: 1.15 !important;
    }
    
    .hero-desc {
        font-size: 0.85rem !important;
        color: #475569 !important;
        margin: 0 !important;
        line-height: 1.4 !important;
    }
    
    .hero-graphic {
        width: 60px !important;
        height: 60px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    .heart-3d {
        font-size: 3rem !important;
        animation: float 3s ease-in-out infinite !important;
    }
    
    @keyframes float {
        0% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-8px) rotate(8deg); }
        100% { transform: translateY(0px) rotate(0deg); }
    }

    /* Glassmorphism theme elements */
    .metric-card {
        background: rgba(255, 255, 255, 0.08) !important;
        backdrop-filter: blur(12px) !important;
        border-radius: 20px !important;
        padding: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        text-align: center !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15) !important;
        margin-bottom: 15px !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    }
    .metric-card:hover {
        transform: translateY(-2px) !important;
        border-color: rgba(255,255,255,0.2) !important;
    }
    .metric-label {
        font-size: 0.8rem !important;
        color: rgba(255, 255, 255, 0.6) !important;
        text-transform: uppercase !important;
        letter-spacing: 1.5px !important;
        font-weight: 600 !important;
        margin-bottom: 4px !important;
    }
    .metric-value {
        font-family: 'Playfair Display', serif !important;
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        letter-spacing: -0.01em !important;
    }
    
    .status-badge {
        display: inline-block !important;
        padding: 4px 12px !important;
        border-radius: 20px !important;
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    .badge-sent {
        background-color: rgba(52, 211, 153, 0.12) !important;
        color: #34d399 !important;
        border: 1px solid rgba(52, 211, 153, 0.25) !important;
    }
    .badge-unsent {
        background-color: rgba(248, 113, 113, 0.12) !important;
        color: #f87171 !important;
        border: 1px solid rgba(248, 113, 113, 0.25) !important;
    }

    /* ── Topic Search Bar ── */
    .search-container {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important;
        padding: 24px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1) !important;
    }
    .search-label {
        font-family: 'Playfair Display', serif !important;
        font-size: 1.3rem !important;
        font-weight: 600 !important;
        color: #ffffff !important;
        margin-bottom: 6px !important;
    }
    .search-hint {
        font-size: 0.88rem !important;
        color: rgba(255, 255, 255, 0.7) !important;
        line-height: 1.5 !important;
    }

    /* ── Chat Bubbles ── */
    .chat-wrapper {
        display: flex !important;
        flex-direction: column !important;
        gap: 16px !important;
        padding: 10px 0 !important;
    }
    .chat-bubble {
        padding: 14px 18px !important;
        border-radius: 20px !important;
        max-width: 85% !important;
        line-height: 1.6 !important;
        font-size: 0.95rem !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08) !important;
        margin-bottom: 8px !important;
        color: #ffffff !important;
    }
    .chat-bubble-user {
        background: linear-gradient(135deg, #b55e2a 0%, #8c471d 100%) !important;
        align-self: flex-end !important;
        margin-left: auto !important;
        border-bottom-right-radius: 4px !important;
    }
    .chat-bubble-assistant {
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        backdrop-filter: blur(10px) !important;
        align-self: flex-start !important;
        border-bottom-left-radius: 4px !important;
    }
    .chat-role-label {
        font-size: 0.75rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        margin-bottom: 6px !important;
        color: #ffffff !important;
        opacity: 0.8 !important;
    }
    .chat-empty-state {
        text-align: center !important;
        padding: 60px 24px !important;
        color: rgba(255,255,255,0.7) !important;
    }
    .chat-empty-icon {
        font-size: 3.5rem !important;
        margin-bottom: 16px !important;
        opacity: 0.8 !important;
    }

    /* ── Article Card styling ── */
    .feed-card {
        background: rgba(255, 255, 255, 0.95) !important;
        border-radius: 24px !important;
        border: 1px solid rgba(255,255,255,0.4) !important;
        padding: 22px !important;
        color: #0f172a !important;
        margin-bottom: 16px !important;
        position: relative !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.06) !important;
        transition: all 0.25s ease !important;
    }
    
    .feed-card:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.12) !important;
    }
    
    .feed-card-header {
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        margin-bottom: 10px !important;
    }
    
    .feed-card-badge {
        font-size: 0.65rem !important;
        background: rgba(181, 94, 42, 0.1) !important;
        color: #b55e2a !important;
        padding: 3px 10px !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    .feed-card-time {
        font-size: 0.75rem !important;
        color: #64748b !important;
    }
    
    .feed-card-title {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 1.2rem !important;
        font-weight: 700 !important;
        color: #0f172a !important;
        margin: 0 0 10px 0 !important;
        line-height: 1.35 !important;
    }
    
    .feed-card-desc {
        font-size: 0.85rem !important;
        color: #334155 !important;
        margin: 0 0 14px 0 !important;
        line-height: 1.5 !important;
        white-space: pre-line !important;
    }
    
    .feed-card-footer {
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        border-top: 1px solid rgba(0,0,0,0.05) !important;
        padding-top: 12px !important;
        margin-bottom: 8px !important;
    }

    /* Simulated Audio Player Detail View */
    .audio-player-box {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 24px !important;
        padding: 24px !important;
        backdrop-filter: blur(16px) !important;
        margin-bottom: 20px !important;
    }
    
    .waveform-visualizer {
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        height: 60px !important;
        margin: 20px 0 !important;
        padding: 0 15px !important;
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 16px !important;
    }
    
    .waveform-bar {
        width: 3px !important;
        border-radius: 2px !important;
        background: rgba(255,255,255,0.2) !important;
        transition: height 0.3s ease !important;
    }
    
    .waveform-bar.active {
        background: #b55e2a !important;
    }
    
    .duration-label {
        font-size: 0.75rem !important;
        color: rgba(255,255,255,0.6) !important;
        font-family: monospace !important;
    }

    /* Style default Streamlit buttons to look like rounded pills */
    div.stButton > button {
        border-radius: 24px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        padding: 6px 20px !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    /* Primary buttons (matches orange details) */
    div.stButton > button[kind="primary"], div.stButton > button[class*="primary"] {
        background-color: #b55e2a !important;
        border-color: #b55e2a !important;
        color: #ffffff !important;
    }
    div.stButton > button[kind="primary"]:hover, div.stButton > button[class*="primary"]:hover {
        background-color: #9c4f22 !important;
        border-color: #9c4f22 !important;
        transform: translateY(-1px);
    }
    
    /* Secondary buttons (glassy outline style) */
    div.stButton > button:not([kind="primary"]):not([class*="Primary"]):not([class*="primary"]) {
        background-color: rgba(255, 255, 255, 0.08) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    div.stButton > button:not([kind="primary"]):not([class*="Primary"]):not([class*="primary"]):hover {
        background-color: rgba(255, 255, 255, 0.15) !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
        transform: translateY(-1px);
    }
    
    /* Expanders styling */
    .streamlit-expanderHeader {
        background-color: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
    }
    .streamlit-expanderContent {
        border-left: 1px solid rgba(255,255,255,0.1) !important;
        border-right: 1px solid rgba(255,255,255,0.1) !important;
        border-bottom: 1px solid rgba(255,255,255,0.1) !important;
        background-color: rgba(0,0,0,0.1) !important;
        border-radius: 0 0 12px 12px !important;
    }
</style>
""", unsafe_allow_html=True)

def render_sidebar_logo():
    html_content = (
        '<div style="text-align: center; padding-bottom: 24px; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 24px;">'
        '<h1 style="font-size: 1.8rem; margin: 0; color: #ffffff;">DigestHub</h1>'
        '<p style="font-size: 0.85rem; color: rgba(255,255,255,0.6); margin: 5px 0 0 0;">RSS AI Summarizer &amp; Dispatcher</p>'
        '</div>'
    )
    st.markdown(html_content, unsafe_allow_html=True)

def render_metric_card(label, value):
    html_content = (
        '<div class="metric-card">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div>'
        '</div>'
    )
    st.markdown(html_content, unsafe_allow_html=True)

def render_section_header(title):
    html_content = (
        '<h2 style="font-family: \'Playfair Display\', serif; font-size: 1.8rem; margin-top: 10px; margin-bottom: 20px; color: #ffffff; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px;">'
        f'{title}'
        '</h2>'
    )
    st.markdown(html_content, unsafe_allow_html=True)

def render_delivery_status(is_sent):
    status_text = "SENT" if is_sent else "NOT SENT"
    badge_class = "badge-sent" if is_sent else "badge-unsent"
    html_content = f"**Delivery Status**: <span class='status-badge {badge_class}'>{status_text}</span>"
    st.markdown(html_content, unsafe_allow_html=True)

def render_search_bar():
    html_content = (
        '<div class="search-container">'
        '<div class="search-label">Search News by Topic</div>'
        '<div class="search-hint">'
        'Type a topic to find relevant articles. The AI chatbot will answer questions about these results.'
        '</div>'
        '</div>'
    )
    st.markdown(html_content, unsafe_allow_html=True)

def render_chat_message(role: str, content: str):
    if role == "user":
        label = "You"
        bubble_class = "chat-bubble-user"
    else:
        label = "DigestBot"
        bubble_class = "chat-bubble-assistant"

    formatted_content = format_to_html(content)
    html_content = (
        f'<div class="chat-bubble {bubble_class}">'
        f'<div class="chat-role-label">{label}</div>'
        f'{formatted_content}'
        f'</div>'
    )
    st.markdown(html_content, unsafe_allow_html=True)

def render_chat_empty_state(has_topic: bool):
    if not has_topic:
        html_content = (
            '<div class="chat-empty-state">'
            '<div class="chat-empty-icon"></div>'
            '<h3 style="color: #ffffff; margin-bottom: 8px;">Search a topic first</h3>'
            '<p>Use the search bar above to find articles on a topic.<br>'
            'Then come back here to ask questions about them!</p>'
            '</div>'
        )
    else:
        html_content = (
            '<div class="chat-empty-state">'
            '<div class="chat-empty-icon"></div>'
            '<h3 style="color: #ffffff; margin-bottom: 8px;">Ask me anything!</h3>'
            '<p>I have the topic articles loaded as context.<br>'
            'Ask a question below to get started.</p>'
            '</div>'
        )
    st.markdown(html_content, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# NEW MOCKUP SPECIFIC RENDERERS
# ─────────────────────────────────────────────────────────────────────────────

def render_category_card(badge, title, description, icon, is_selected, key):
    """Render category onboarding selection card styled like Screen 1 of reference image."""
    card_class = "category-item selected" if is_selected else "category-item"
    border_style = "border: 2px solid #b55e2a;" if is_selected else ""
    html_content = (
        f'<div class="{card_class}" style="{border_style}">'
        f'<div class="category-badge-pill">{badge}</div>'
        f'<div class="category-icon-container">{icon}</div>'
        f'<h4 class="category-card-title">{title}</h4>'
        f'<p class="category-card-desc">{description}</p>'
        f'</div>'
    )
    st.markdown(html_content, unsafe_allow_html=True)
    btn_label = "✓ Selected" if is_selected else "Select"
    return st.button(btn_label, key=key, use_container_width=True, type="primary" if is_selected else "secondary")



def render_hero_headlines_card():
    """Render daily breaking headlines hero panel styled like Screen 2 of reference image."""
    html_content = (
        '<div class="hero-headlines-card">'
        '<div class="hero-content">'
        '<div class="hero-tag">Your daily</div>'
        '<h3 class="hero-title">Headlines</h3>'
        '<p class="hero-desc">Stay informed with real-time updates from trusted global news sources</p>'
        '</div>'
        '<div class="hero-graphic">'
        '</div>'
        '</div>'
    )
    st.markdown(html_content, unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def generate_tts_audio_cached(text: str) -> bytes:
    from gtts import gTTS
    import io
    tts = gTTS(text=text, lang='en')
    audio_fp = io.BytesIO()
    tts.write_to_fp(audio_fp)
    return audio_fp.getvalue()

def render_audio_player(title, source, pub_date_str, text_content=None):
    """Render beautiful simulated audio visualizer details styled like Screen 3 of reference image."""
    bar_heights = [15, 30, 45, 20, 10, 25, 40, 50, 35, 20, 15, 30, 45, 60, 55, 40, 30, 25, 10, 20, 35, 50, 45, 30, 15]
    bars_html = "".join([f'<div class="waveform-bar active" style="height: {h}px;"></div>' if idx < 12 else f'<div class="waveform-bar" style="height: {h}px;"></div>' for idx, h in enumerate(bar_heights)])
    
    html_top = (
        '<div style="text-align: center; margin-bottom: 20px;">'
        '<div style="background: linear-gradient(135deg, #153930, #b55e2a); height: 200px; border-radius: 20px; display: flex; align-items: center; justify-content: center; position: relative; box-shadow: 0 8px 25px rgba(0,0,0,0.2);">'
        '<div style="font-size: 4rem; background: rgba(255,255,255,0.2); width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(5px); border: 2px solid white; transition: transform 0.2s;">AI</div>'
        '<div style="position: absolute; bottom: 12px; left: 16px; font-size: 0.8rem; background: rgba(0,0,0,0.5); padding: 4px 10px; border-radius: 12px; color: white;">AI Voice Reader</div>'
        '</div>'
        '</div>'
    )
    st.markdown(html_top, unsafe_allow_html=True)
    
    if text_content:
        import re
        
        # Clean text content from HTML tags and Markdown formatting
        clean_text = text_content or ""
        clean_text = re.sub(r'<[^>]+>', '', clean_text)
        clean_text = re.sub(r'\*+', '', clean_text)
        clean_text = re.sub(r'#+', '', clean_text)
        clean_text = clean_text[:1500].strip()
        
        if clean_text:
            try:
                st.markdown("<p style='text-align: center; font-size: 0.85rem; color: rgba(255,255,255,0.6); margin-bottom: 5px;'>Click play below to listen to the AI Audio Summary</p>", unsafe_allow_html=True)
                audio_bytes = generate_tts_audio_cached(clean_text)
                st.audio(audio_bytes, format="audio/mp3")
                st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Failed to generate voice playback: {e}")
                
    html_player = (
        '<div class="audio-player-box">'
        '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
        f'<span class="feed-card-badge">{source}</span>'
        f'<span style="font-size: 0.75rem; color: rgba(255,255,255,0.6);">{pub_date_str}</span>'
        '</div>'
        f'<h3 style="margin-top: 5px; margin-bottom: 15px; color: white !important; font-family: \'Playfair Display\', serif;">{title}</h3>'
        '<div class="waveform-visualizer">'
        '<span class="duration-label">Active</span>'
        f'<div style="display: flex; gap: 3px; align-items: center; flex-grow: 1; justify-content: center; margin: 0 15px;">{bars_html}</div>'
        '<span class="duration-label">Playing</span>'
        '</div>'
        '</div>'
    )
    st.markdown(html_player, unsafe_allow_html=True)

def format_to_html(text: str) -> str:
    """Convert markdown formatting (**bold**, bullet lists, and numbered lists) into clean HTML."""
    import re
    # Replace markdown bold **text** with <b>text</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    
    lines = text.split('\n')
    
    # Check if there are any list markers (bullets or numbered)
    has_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(('- ', '* ')) or re.match(r'^\d+\.\s', stripped):
            has_list = True
            break
            
    if not has_list:
        return text.replace('\n', '<br>')

    # Convert list items to HTML structures (ul or ol)
    formatted_lines = []
    current_list_type = None  # None, 'ul', or 'ol'
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
            
        # Match bullets
        if stripped.startswith(('- ', '* ')):
            if current_list_type == 'ol':
                formatted_lines.append('</ol>')
                current_list_type = None
            if current_list_type is None:
                formatted_lines.append('<ul style="margin: 4px 0; padding-left: 20px; list-style-type: disc;">')
                current_list_type = 'ul'
            content = stripped[2:].strip()
            formatted_lines.append(f'<li style="margin-bottom: 6px;">{content}</li>')
            
        # Match numbered list (e.g. 1. )
        elif re.match(r'^\d+\.\s', stripped):
            if current_list_type == 'ul':
                formatted_lines.append('</ul>')
                current_list_type = None
            if current_list_type is None:
                formatted_lines.append('<ol style="margin: 4px 0; padding-left: 20px;">')
                current_list_type = 'ol'
            # Strip the leading digits, dot and whitespace
            content = re.sub(r'^\d+\.\s*', '', stripped)
            formatted_lines.append(f'<li style="margin-bottom: 6px;">{content}</li>')
            
        # Normal text
        else:
            if current_list_type == 'ul':
                formatted_lines.append('</ul>')
                current_list_type = None
            elif current_list_type == 'ol':
                formatted_lines.append('</ol>')
                current_list_type = None
            formatted_lines.append(stripped)
            
    if current_list_type == 'ul':
        formatted_lines.append('</ul>')
    elif current_list_type == 'ol':
        formatted_lines.append('</ol>')
        
    return '\n'.join(formatted_lines)

def render_feed_article_card(a, index, current_format="TL;DR"):
    """Render high-end feed article card styled like Screen 2 / 3 of reference image."""
    from datetime import datetime
    pub_date = a.get("published_date")
    time_str = "Recent"
    if pub_date:
        diff = datetime.utcnow() - pub_date
        hours = int(diff.total_seconds() / 3600)
        if hours < 1:
            rel_time = "Just now"
        elif hours == 1:
            rel_time = "1 Hour ago"
        elif hours < 24:
            rel_time = f"{hours} Hours ago"
        else:
            rel_time = pub_date.strftime("%b %d")
        
        exact_time = pub_date.strftime("%b %d, %Y %H:%M")
        time_str = f"{rel_time} ({exact_time})"
            
    if current_format == "Bullets":
        text_content = a.get("bullets_content") or a.get("description") or ""
        if a.get("bullets_content"):
            short_text = text_content
        else:
            words = text_content.split()
            short_text = " ".join(words[:35]) + "..." if len(words) > 35 else text_content
    elif current_format == "5 Ws":
        text_content = a.get("five_ws_content") or a.get("description") or ""
        if a.get("five_ws_content"):
            short_text = text_content
        else:
            words = text_content.split()
            short_text = " ".join(words[:35]) + "..." if len(words) > 35 else text_content
    else:
        text_content = a.get("content") or a.get("description") or ""
        words = text_content.split()
        short_text = " ".join(words[:35]) + "..." if len(words) > 35 else text_content
        
    formatted_desc = format_to_html(short_text)
    safe_id = abs(int(a.get("id") or hash(a["url"])))
    
    html_content = (
        '<div class="feed-card">'
        '<div class="feed-card-header">'
        f'<span class="feed-card-badge">{a["source"]}</span>'
        f'<span class="feed-card-time">{time_str}</span>'
        '</div>'
        f'<h4 class="feed-card-title">{a["title"]}</h4>'
        f'<div class="feed-card-desc">{formatted_desc}</div>'
        '<div class="feed-card-footer">'
        f'<a href="/?read={safe_id}" target="_blank" style="font-size: 0.8rem; color: #b55e2a; text-decoration: none; font-weight: 700;">Original Source Link</a>'
        '</div>'
        '</div>'
    )
    st.markdown(html_content, unsafe_allow_html=True)
    
    col_play, col_chat = st.columns(2)
    with col_play:
        play_clicked = st.button("Listen / Read", key=f"feed_play_{safe_id}_{index}", use_container_width=True)
    with col_chat:
        chat_clicked = st.button("Discuss", key=f"feed_discuss_{safe_id}_{index}", use_container_width=True)
        
    return play_clicked, chat_clicked

def render_topic_articles(articles: list[dict], ask_fn=None):
    """
    Deprecated in favor of render_feed_article_card for custom layouts,
    but kept for backwards compatibility with analytics and search loops.
    """
    summary_format = st.session_state.get("summary_format", "TL;DR")
    for idx, a in enumerate(articles):
        render_feed_article_card(a, idx, summary_format)
        st.markdown("<div style='margin-bottom:18px;'></div>", unsafe_allow_html=True)

def render_app_navigation(active_page):
    """Render beautiful pill button top navigation."""
    cols = st.columns([1, 1, 1, 1])
    pages = [
        ("feed", "Home Feed"),
        ("categories", "Categories"),
        ("chat", "DigestBot"),
        ("analytics", "Analytics")
    ]
    selected_page = active_page
    for idx, (page_id, label) in enumerate(pages):
        with cols[idx]:
            is_active = page_id == active_page
            btn_type = "primary" if is_active else "secondary"
            if st.button(label, key=f"nav_btn_{page_id}", use_container_width=True, type=btn_type):
                selected_page = page_id
    return selected_page
