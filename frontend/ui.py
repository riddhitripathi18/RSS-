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
</style>
""", unsafe_allow_html=True)

def render_sidebar_logo():
    st.markdown("""
    <div class="sidebar-logo">
        <h1 style="font-size: 1.8rem; margin: 0; color: #64ffda;">📰 DigestHub</h1>
        <p style="font-size: 0.85rem; color: #8892b0; margin: 5px 0 0 0;">RSS AI Summarizer & Dispatcher</p>
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

def render_article_card_header(row):
    if row["Is Duplicate"]:
        badge_html = "<span class='status-badge badge-duplicate'>Duplicate</span>"
    else:
        badge_html = "<span class='status-badge badge-unique'>Unique</span>"
        
    proc_badge = "✅ Processed" if row["Is Processed"] else "⏳ Pending"
    pub_date = row['Published Date'].strftime('%Y-%m-%d %H:%M') if pd.notnull(row['Published Date']) else 'N/A'
    
    st.markdown(f"""
    <h4 style="margin: 0 0 5px 0;">{row['Title']}</h4>
    <div style="font-size: 0.85rem; color: #8892b0; margin-bottom: 8px;">
        Source: <strong>{row['Source']}</strong> | 
        Published: {pub_date} | 
        {badge_html} | <span style="font-weight:600;">{proc_badge}</span>
    </div>
    """, unsafe_allow_html=True)

def render_divider():
    st.markdown("<hr style='margin: 10px 0; border: 0; border-top: 1px solid rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
