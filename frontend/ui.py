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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }

    /* Glassmorphism theme elements */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 18px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 15px;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #8892b0;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #64ffda;
        margin-top: 5px;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 15px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .badge-sent {
        background-color: rgba(40, 167, 69, 0.2);
        color: #28a745;
        border: 1px solid #28a745;
    }
    .badge-unsent {
        background-color: rgba(220, 53, 69, 0.2);
        color: #dc3545;
        border: 1px solid #dc3545;
    }
    .badge-duplicate {
        background-color: rgba(255, 193, 7, 0.2);
        color: #ffc107;
        border: 1px solid #ffc107;
    }
    .badge-unique {
        background-color: rgba(0, 123, 255, 0.2);
        color: #007bff;
        border: 1px solid #007bff;
    }
    /* Section dividers */
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 15px;
        color: #e2e8f0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding-bottom: 5px;
    }
    /* Logo styling */
    .sidebar-logo {
        text-align: center;
        padding-bottom: 20px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }

    /* ── Topic Search Bar ── */
    .search-container {
        background: linear-gradient(135deg, rgba(100,255,218,0.08) 0%, rgba(0,123,255,0.08) 100%);
        border: 1px solid rgba(100, 255, 218, 0.25);
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 24px;
    }
    .search-label {
        font-size: 1.1rem;
        font-weight: 600;
        color: #64ffda;
        margin-bottom: 4px;
    }
    .search-hint {
        font-size: 0.82rem;
        color: #8892b0;
        margin-bottom: 12px;
    }
    .topic-pill {
        display: inline-block;
        background: rgba(100,255,218,0.12);
        color: #64ffda;
        border: 1px solid rgba(100,255,218,0.35);
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 0.78rem;
        font-weight: 600;
        margin: 3px 4px 3px 0;
        cursor: pointer;
    }

    /* ── Chat Bubbles ── */
    .chat-wrapper {
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding: 4px 0;
    }
    .chat-bubble {
        padding: 12px 16px;
        border-radius: 14px;
        max-width: 85%;
        line-height: 1.55;
        font-size: 0.93rem;
    }
    .chat-bubble-user {
        background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
        color: #ffffff;
        align-self: flex-end;
        margin-left: auto;
        border-bottom-right-radius: 4px;
        box-shadow: 0 2px 8px rgba(0,123,255,0.3);
    }
    .chat-bubble-assistant {
        background: rgba(255, 255, 255, 0.06);
        color: #e2e8f0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        align-self: flex-start;
        border-bottom-left-radius: 4px;
    }
    .chat-role-label {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 4px;
        opacity: 0.75;
    }
    .chat-empty-state {
        text-align: center;
        padding: 48px 24px;
        color: #8892b0;
    }
    .chat-empty-icon {
        font-size: 3rem;
        margin-bottom: 12px;
    }

    /* ── Article card ── */
    .article-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 10px;
        transition: border-color 0.2s;
    }
    .article-card:hover {
        border-color: rgba(100,255,218,0.25);
    }

    /* Style default Streamlit buttons to look like rounded pills */
    div.stButton > button:not([kind="primary"]):not([class*="Primary"]):not([class*="primary"]) {
        border-radius: 20px !important;
        background-color: rgba(100,255,218,0.06) !important;
        color: #64ffda !important;
        border: 1px solid rgba(100,255,218,0.2) !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        padding: 4px 16px !important;
        transition: all 0.2s ease-in-out !important;
    }
    div.stButton > button:not([kind="primary"]):not([class*="Primary"]):not([class*="primary"]):hover {
        background-color: rgba(100,255,218,0.15) !important;
        border-color: #64ffda !important;
        color: #ffffff !important;
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
        # Try to end at a sentence boundary between min and max words
        truncated = " ".join(words[:max_words])
        # Look for last sentence-ending punctuation within the range
        for i in range(len(truncated) - 1, 0, -1):
            if truncated[i] in ".!?" and i > len(" ".join(words[:min_words])):
                return truncated[: i + 1]
        return truncated + "..."

    for a in articles:
        article_id = a.get("id") or abs(hash(a["url"]))
        safe_id = abs(int(article_id))

        # Clean HTML tags from summary content or fallback description
        text_to_display = a.get("content") or a.get("description") or ""
        raw_text = re.sub(r"<[^>]+>", "", text_to_display)
        summary = _truncate_to_words(raw_text) if raw_text.strip() else "No summary available."

        pub = a["published_date"].strftime("%b %d, %Y %H:%M") if a.get("published_date") else "N/A"

        # ── 1. Article Headline ──────────────────────────────────────────────
        st.markdown(f"""
        <div class="article-card" style="margin-bottom:0;padding-bottom:14px;">
            <h4 style="margin:0 0 6px 0;color:#e2e8f0;font-size:1.15rem;">{a['title']}</h4>
            <div style="font-size:0.75rem;color:#8892b0;margin-bottom:10px;">
                {a['source']}&nbsp;·&nbsp;{pub}
            </div>
            <p style="font-size:0.9rem;color:#a8b2d8;line-height:1.6;margin:0 0 12px 0;">{summary}</p>
            <a href="/?read={safe_id}" target="_blank"
               style="font-size:0.85rem;color:#64ffda;text-decoration:none;font-weight:500;">
                🔗 Read full article →
            </a>
        </div>
        """, unsafe_allow_html=True)

        # ── 4. Chat about this article ───────────────────────────────────────
        chat_key = f"art_chat_{safe_id}"
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []

        with st.expander("💬 Chat about this article"):
            # Show existing conversation
            for msg in st.session_state[chat_key]:
                if msg["role"] == "user":
                    st.markdown(
                        f"<div style='background:rgba(0,123,255,0.15);border-radius:8px;"
                        f"padding:8px 12px;margin:4px 0;font-size:0.9rem;'>"
                        f"👤 <b>You:</b> {msg['content']}</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<div style='background:rgba(255,255,255,0.05);border-radius:8px;"
                        f"padding:8px 12px;margin:4px 0;font-size:0.9rem;'>"
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




