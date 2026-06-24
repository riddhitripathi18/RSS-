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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #080A10 !important;
        font-family: 'Inter', sans-serif;
        color: #f1f5f9;
    }
    
    /* Clean, modern scrollbars */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #080A10;
    }
    ::-webkit-scrollbar-thumb {
        background: #1f2937;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #374151;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        color: #ffffff !important;
        letter-spacing: -0.02em;
    }

    /* Glassmorphism theme elements */
    .metric-card {
        background: rgba(20, 26, 40, 0.65) !important;
        backdrop-filter: blur(12px);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.07);
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        margin-bottom: 15px;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(100, 255, 218, 0.25);
        box-shadow: 0 8px 30px rgba(100, 255, 218, 0.05);
    }
    .metric-label {
        font-size: 0.8rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .metric-value {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.4rem;
        font-weight: 700;
        color: #64ffda;
        letter-spacing: -0.03em;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-sent {
        background-color: rgba(52, 211, 153, 0.1);
        color: #34d399;
        border: 1px solid rgba(52, 211, 153, 0.2);
    }
    .badge-unsent {
        background-color: rgba(248, 113, 113, 0.1);
        color: #f87171;
        border: 1px solid rgba(248, 113, 113, 0.2);
    }
    .badge-duplicate {
        background-color: rgba(251, 191, 36, 0.1);
        color: #fbbf24;
        border: 1px solid rgba(251, 191, 36, 0.2);
    }
    .badge-unique {
        background-color: rgba(59, 130, 246, 0.1);
        color: #3b82f6;
        border: 1px solid rgba(59, 130, 246, 0.2);
    }
    
    /* Section dividers */
    .section-header {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.6rem;
        font-weight: 600;
        margin-top: 10px;
        margin-bottom: 20px;
        color: #ffffff;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 8px;
        letter-spacing: -0.01em;
    }
    /* Logo styling */
    .sidebar-logo {
        text-align: center;
        padding-bottom: 24px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.07);
        margin-bottom: 24px;
    }

    /* ── Topic Search Bar ── */
    .search-container {
        background: linear-gradient(135deg, rgba(100, 255, 218, 0.05) 0%, rgba(59, 130, 246, 0.05) 100%);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.15);
    }
    .search-label {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.3rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .search-hint {
        font-size: 0.88rem;
        color: #94a3b8;
        line-height: 1.5;
    }

    /* ── Chat Bubbles ── */
    .chat-wrapper {
        display: flex;
        flex-direction: column;
        gap: 16px;
        padding: 10px 0;
    }
    .chat-bubble {
        padding: 14px 18px;
        border-radius: 16px;
        max-width: 80%;
        line-height: 1.6;
        font-size: 0.95rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 8px;
    }
    .chat-bubble-user {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: #ffffff;
        align-self: flex-end;
        margin-left: auto;
        border-bottom-right-radius: 4px;
        box-shadow: 0 4px 20px rgba(37, 99, 235, 0.25);
    }
    .chat-bubble-assistant {
        background: rgba(20, 26, 40, 0.7);
        color: #f1f5f9;
        border: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(10px);
        align-self: flex-start;
        border-bottom-left-radius: 4px;
    }
    .chat-role-label {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
        color: #64ffda;
    }
    .chat-bubble-user .chat-role-label {
        color: #93c5fd;
    }
    .chat-empty-state {
        text-align: center;
        padding: 60px 24px;
        color: #94a3b8;
    }
    .chat-empty-icon {
        font-size: 3.5rem;
        margin-bottom: 16px;
        opacity: 0.8;
    }

    /* ── Article card ── */
    .article-card {
        background: rgba(20, 26, 40, 0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        backdrop-filter: blur(10px);
        border-radius: 14px;
        padding: 22px;
        margin-bottom: 18px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    }
    .article-card:hover {
        transform: translateY(-2px);
        border-color: rgba(100, 255, 218, 0.25) !important;
        box-shadow: 0 8px 30px rgba(100, 255, 218, 0.06);
    }
    
    /* Source Tags */
    .source-tag {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.72rem;
        font-weight: 600;
        margin-right: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border: 1px solid rgba(255, 255, 255, 0.15);
    }

    /* Style default Streamlit buttons to look like rounded pills */
    div.stButton > button:not([kind="primary"]):not([class*="Primary"]):not([class*="primary"]) {
        border-radius: 24px !important;
        background-color: rgba(100, 255, 218, 0.04) !important;
        color: #64ffda !important;
        border: 1px solid rgba(100, 255, 218, 0.15) !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        padding: 6px 20px !important;
        letter-spacing: 0.5px;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    div.stButton > button:not([kind="primary"]):not([class*="Primary"]):not([class*="primary"]):hover {
        background-color: rgba(100, 255, 218, 0.12) !important;
        border-color: #64ffda !important;
        color: #ffffff !important;
        transform: scale(1.02);
    }
    
    /* Primary buttons */
    div.stButton > button[kind="primary"], div.stButton > button[class*="primary"] {
        border-radius: 24px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
        padding: 6px 20px !important;
        transition: all 0.2s ease-in-out !important;
    }
    
    /* Expanders styling */
    .streamlit-expanderHeader {
        background-color: rgba(20, 26, 40, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 8px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        color: #e2e8f0 !important;
    }
    .streamlit-expanderContent {
        border-left: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
        background-color: rgba(15, 20, 32, 0.3) !important;
    }
</style>
""", unsafe_allow_html=True)

def render_sidebar_logo():
    st.markdown("""
    <div class="sidebar-logo">
        <h1 style="font-size: 1.8rem; margin: 0; color: #64ffda;">📰 DigestHub</h1>
        <p style="font-size: 0.85rem; color: #8892b0; margin: 5px 0 0 0;">RSS AI Summarizer &amp; Dispatcher</p>
    </div>
    """, unsafe_allow_html=True)

def render_metric_card(label, value):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def render_section_header(title):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)

def render_delivery_status(is_sent):
    status_text = "SENT" if is_sent else "NOT SENT"
    badge_class = "badge-sent" if is_sent else "badge-unsent"
    st.markdown(f"**Delivery Status**: <span class='status-badge {badge_class}'>{status_text}</span>", unsafe_allow_html=True)


def render_search_bar():
    """Render the prominent topic search container."""
    st.markdown("""
    <div class="search-container">
        <div class="search-label">🔍 Search News by Topic</div>
        <div class="search-hint">
            Type a topic to find relevant articles. The AI chatbot will answer questions about these results.
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_chat_message(role: str, content: str):
    """Render a single chat message bubble."""
    if role == "user":
        label = "You"
        bubble_class = "chat-bubble-user"
    else:
        label = "🤖 DigestBot"
        bubble_class = "chat-bubble-assistant"

    st.markdown(f"""
    <div class="chat-bubble {bubble_class}">
        <div class="chat-role-label">{label}</div>
        {content}
    </div>
    """, unsafe_allow_html=True)


def render_chat_empty_state(has_topic: bool):
    """Render empty state for the chatbot panel."""
    if not has_topic:
        st.markdown("""
        <div class="chat-empty-state">
            <div class="chat-empty-icon">🔍</div>
            <h3 style="color: #e2e8f0; margin-bottom: 8px;">Search a topic first</h3>
            <p>Use the search bar above to find articles on a topic.<br>
            Then come back here to ask questions about them!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="chat-empty-state">
            <div class="chat-empty-icon">💬</div>
            <h3 style="color: #e2e8f0; margin-bottom: 8px;">Ask me anything!</h3>
            <p>I have the topic articles loaded as context.<br>
            Ask a question below to get started.</p>
        </div>
        """, unsafe_allow_html=True)


def render_topic_articles(articles: list[dict], ask_fn=None):
    """Render article cards in sequence: Headline → Summary → Link → Chat.

    ask_fn: callable(messages, question, articles, topic) -> str
             Pass app.ask_chatbot so ui.py doesn't need to import it.
    """
    import re

    def _truncate_to_words(text: str, min_words: int = 100, max_words: int = 150) -> str:
        """Truncate text to between min_words and max_words, ending at a sentence boundary if possible."""
        words = text.split()
        if len(words) <= max_words:
            return text
        truncated = " ".join(words[:max_words])
        for i in range(len(truncated) - 1, 0, -1):
            if truncated[i] in ".!?" and i > len(" ".join(words[:min_words])):
                return truncated[: i + 1]
        return truncated + "..."

    def _markdown_to_html(text: str) -> str:
        """Convert markdown paragraphs, bullets, and numbered lists to clean HTML for cards."""
        clean = re.sub(r"<[^>]+>", "", text)
        lines = clean.split("\n")
        in_list = False
        list_tag = ""
        html_parts = []
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
                
            # Bullet list detection
            if line_stripped.startswith("- ") or line_stripped.startswith("* "):
                if not in_list:
                    html_parts.append("<ul style='margin: 8px 0 12px 18px; padding: 0; color: #a8b2d8;'>")
                    in_list = True
                    list_tag = "ul"
                elif list_tag == "ol":
                    html_parts.append("</ol><ul style='margin: 8px 0 12px 18px; padding: 0; color: #a8b2d8;'>")
                    list_tag = "ul"
                html_parts.append(f"<li style='margin-bottom: 6px; font-size: 0.9rem; line-height: 1.5;'>{line_stripped[2:]}</li>")
                
            # Numbered list detection
            elif re.match(r"^\d+\.\s+", line_stripped):
                content = re.sub(r"^\d+\.\s+", "", line_stripped)
                if not in_list:
                    html_parts.append("<ol style='margin: 8px 0 12px 18px; padding: 0; color: #a8b2d8;'>")
                    in_list = True
                    list_tag = "ol"
                elif list_tag == "ul":
                    html_parts.append("</ul><ol style='margin: 8px 0 12px 18px; padding: 0; color: #a8b2d8;'>")
                    list_tag = "ol"
                html_parts.append(f"<li style='margin-bottom: 6px; font-size: 0.9rem; line-height: 1.5;'>{content}</li>")
                
            # Plain paragraph
            else:
                if in_list:
                    html_parts.append(f"</{list_tag}>")
                    in_list = False
                html_parts.append(f"<p style='margin: 0 0 12px 0; font-size: 0.92rem; line-height: 1.6; color: #a8b2d8;'>{line_stripped}</p>")
                
        if in_list:
            html_parts.append(f"</{list_tag}>")
            
        return "".join(html_parts)

    def get_source_color(source: str) -> str:
        """Return custom styled CSS border/background color scheme based on feed source."""
        source_lower = source.lower()
        if "reuters" in source_lower:
            return "background-color: rgba(59, 130, 246, 0.1); color: #60a5fa; border-color: rgba(59, 130, 246, 0.25);"
        elif "economic times" in source_lower or "economictimes" in source_lower:
            return "background-color: rgba(16, 185, 129, 0.1); color: #34d399; border-color: rgba(16, 185, 129, 0.25);"
        elif "cnbc" in source_lower:
            return "background-color: rgba(239, 68, 68, 0.1); color: #f87171; border-color: rgba(239, 68, 68, 0.25);"
        elif "bloomberg" in source_lower:
            return "background-color: rgba(245, 158, 11, 0.1); color: #fbbf24; border-color: rgba(245, 158, 11, 0.25);"
        elif "bbc" in source_lower:
            return "background-color: rgba(239, 68, 68, 0.15); color: #f87171; border-color: rgba(239, 68, 68, 0.3);"
        elif "times of india" in source_lower or "toi" in source_lower:
            return "background-color: rgba(139, 92, 246, 0.1); color: #a78bfa; border-color: rgba(139, 92, 246, 0.25);"
        elif "the hindu" in source_lower:
            return "background-color: rgba(14, 165, 233, 0.1); color: #38bdf8; border-color: rgba(14, 165, 233, 0.25);"
        elif "moneycontrol" in source_lower:
            return "background-color: rgba(236, 72, 153, 0.1); color: #f472b6; border-color: rgba(236, 72, 153, 0.25);"
        elif "yahoo" in source_lower:
            return "background-color: rgba(109, 40, 217, 0.1); color: #c084fc; border-color: rgba(109, 40, 217, 0.25);"
        elif "marketwatch" in source_lower:
            return "background-color: rgba(20, 184, 166, 0.1); color: #2dd4bf; border-color: rgba(20, 184, 166, 0.25);"
        elif "hindustan times" in source_lower:
            return "background-color: rgba(244, 63, 94, 0.1); color: #fb7185; border-color: rgba(244, 63, 94, 0.25);"
        elif "ndtv" in source_lower:
            return "background-color: rgba(249, 115, 22, 0.1); color: #ff9d43; border-color: rgba(249, 115, 22, 0.25);"
        elif "guardian" in source_lower:
            return "background-color: rgba(4, 120, 87, 0.1); color: #34d399; border-color: rgba(4, 120, 87, 0.25);"
        else:
            return "background-color: rgba(100, 255, 218, 0.08); color: #64ffda; border-color: rgba(100, 255, 218, 0.2);"

    summary_format = st.session_state.get("summary_format", "TL;DR")

    for a in articles:
        article_id = a.get("id") or abs(hash(a["url"]))
        safe_id = abs(int(article_id))

        # Retrieve text according to current user format preference
        if summary_format == "Bullets":
            text_to_display = a.get("bullets_content") or a.get("description") or ""
        elif summary_format == "5 Ws":
            text_to_display = a.get("five_ws_content") or a.get("description") or ""
        else:
            text_to_display = a.get("content") or a.get("description") or ""
            
        summary_html = _markdown_to_html(text_to_display)
        pub = a["published_date"].strftime("%b %d, %Y %H:%M") if a.get("published_date") else "N/A"

        source_style = get_source_color(a['source'])
        source_badge = f"<span class='source-tag' style='{source_style}'>{a['source']}</span>"

        # ── 1. Article Headline Card ──────────────────────────────────────────
        st.markdown(f"""
        <div class="article-card" style="margin-bottom:0;padding-bottom:18px;">
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
                {source_badge}
                <span style="font-size:0.75rem;color:#8892b0;">{pub}</span>
            </div>
            <h4 style="margin:0 0 10px 0;color:#ffffff;font-size:1.2rem;line-height:1.4;">{a['title']}</h4>
            <div style="margin:0 0 14px 0;">{summary_html}</div>
            <a href="/?read={safe_id}" target="_blank"
               style="font-size:0.85rem;color:#64ffda;text-decoration:none;font-weight:600;display:inline-flex;align-items:center;gap:4px;">
                🔗 Read full article <span style="font-size:0.75rem;">→</span>
            </a>
        </div>
        """, unsafe_allow_html=True)

        # ── 2. Chat about this article ───────────────────────────────────────
        chat_key = f"art_chat_{safe_id}"
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []

        with st.expander("💬 Chat about this article"):
            # Show existing conversation
            for msg in st.session_state[chat_key]:
                if msg["role"] == "user":
                    st.markdown(
                        f"<div style='background:rgba(37,99,235,0.15);border-radius:10px;border:1px solid rgba(37,99,235,0.25);"
                        f"padding:10px 14px;margin:6px 0;font-size:0.9rem;color:#f1f5f9;'>"
                        f"👤 <b>You:</b> {msg['content']}</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<div style='background:rgba(20,26,40,0.5);border-radius:10px;border:1px solid rgba(255,255,255,0.06);"
                        f"padding:10px 14px;margin:6px 0;font-size:0.9rem;color:#f1f5f9;'>"
                        f"🤖 <b>AI:</b> {msg['content']}</div>",
                        unsafe_allow_html=True,
                    )

            if ask_fn is None:
                st.caption("⚠️ Chatbot not connected — ask_fn not supplied.")
            else:
                q_key = f"art_q_{safe_id}"
                user_q = st.text_input(
                    "Ask about this article:",
                    key=q_key,
                    placeholder="e.g. Summarize this / What is the main takeaway?",
                    label_visibility="collapsed",
                )
                if st.button("Ask ➔", key=f"art_btn_{safe_id}", use_container_width=False):
                    if user_q.strip():
                        with st.spinner("Thinking..."):
                            answer = ask_fn(
                                messages=st.session_state[chat_key],
                                question=user_q.strip(),
                                articles=[a],
                                topic=a["title"],
                            )
                        st.session_state[chat_key].append({"role": "user", "content": user_q.strip()})
                        st.session_state[chat_key].append({"role": "assistant", "content": answer})
                        st.rerun()

        st.markdown("<div style='margin-bottom:18px;'></div>", unsafe_allow_html=True)




