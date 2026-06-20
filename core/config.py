"""
Configuration file for RSS News Digest System
"""
import os
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

# RSS Feed sources (add more as needed)
RSS_FEEDS = [
    "https://feeds.bbc.co.uk/news/rss.xml",
    "https://feeds.cnbc.com/cnbc/world",
    "https://feeds.reuters.com/reuters/topNews",
    "https://feeds.theguardian.com/theguardian/international/rss",
    "https://feeds.bloomberg.com/markets/news.rss",
    "https://feeds.nytimes.com/services/xml/rss/nyt/World.xml",
]

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///rss_news.db")

# LLM Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")  # Free tier: aistudio.google.com/app/apikey

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Email Configuration
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", 587))

# News fetch settings
NEWS_HOURS_LOOKBACK = 24  # Fetch news from last 24 hours
MAX_ARTICLES_PER_DIGEST = 10  # Max articles in final digest
SUMMARIZATION_MODEL = "gpt-4-turbo"  # LLM model for summaries

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
