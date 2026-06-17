# 📰 AI-Powered Daily News Digest System

An intelligent news aggregation and summarization platform that automatically collects, analyzes, and delivers the day's most important news stories to your inbox or messaging app.

## 🎯 Features

- **📡 RSS Feed Aggregation**: Collect latest news from multiple RSS sources
- **🤖 Intelligent Analysis**: Deduplicate articles, group related stories, and rank by importance
- **✨ AI Summarization**: Generate concise summaries using Large Language Models (LLM)
- **📨 Multi-Channel Delivery**: Send digests via Telegram, Email, and more
- **⏰ Automated Scheduling**: Run daily at your preferred time
- **🗄️ Persistent Storage**: SQLite database for article tracking

## 📋 System Architecture

```
RSS Feeds
   ↓
Fetcher Agent (collects articles from 24hrs)
   ↓
Database (stores articles)
   ↓
Analyzer Agent (deduplicates, groups, ranks)
   ↓
Summarizer Agent (LLM generates summaries)
   ↓
Delivery System (sends via Telegram/Email)
   ↓
Users (receive daily digest)
```

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- Virtual environment (already set up: `myenv/`)

### 2. Install Dependencies

```bash
# Activate virtual environment
.\myenv\Scripts\Activate.ps1

# Install packages (already done)
pip install feedparser requests python-dotenv sqlalchemy openai schedule
```

### 3. Configure .env File

Edit `.env` with your credentials:

```env
# Database (optional - defaults to SQLite)
DATABASE_URL=sqlite:///rss_news.db

# LLM Configuration
OPENAI_API_KEY=sk-your-openai-key-here

# Telegram Configuration (optional)
TELEGRAM_BOT_TOKEN=your-bot-token-here
TELEGRAM_CHAT_ID=your-chat-id-here

# Email Configuration (optional)
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password-here
```

**Note**: For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833), not your regular password.

### 4. Run the System

#### Option A: Run Pipeline Immediately
```bash
python main.py                    # Fetch news
python analyzer.py               # Analyze & rank
python summarizer.py             # Generate summaries
python delivery.py               # Send digest
```

#### Option B: Use Interactive Scheduler
```bash
python scheduler.py
# Select option 1 to run immediately
# Select option 2 to schedule daily at 8:00 AM
# Select option 3 for custom time
```

## 📁 Project Structure

```
RSS_Project/
├── config.py              # Configuration (feeds, settings)
├── database.py            # Database models & setup
├── fetcher.py            # News Fetcher Agent
├── analyzer.py           # News Analysis Agent
├── summarizer.py         # LLM Summarization
├── delivery.py           # Email/Telegram delivery
├── scheduler.py          # Task scheduler & orchestrator
├── main.py              # Entry point
├── .env                 # Environment variables
├── rss_news.db         # SQLite database (auto-created)
└── myenv/              # Virtual environment
```

## 🔧 Configuration Guide

### Adding RSS Feeds

Edit `config.py` and add feeds to the `RSS_FEEDS` list:

```python
RSS_FEEDS = [
    "https://feeds.bbc.co.uk/news/rss.xml",
    "https://feeds.cnbc.com/cnbc/world",
    "https://feeds.reuters.com/reuters/topNews",
    # Add more feeds here
]
```

### Telegram Setup

1. Create a bot on Telegram [@BotFather](https://t.me/botfather)
2. Get your bot token
3. Start a chat with your bot and get chat ID:
   ```bash
   curl https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
4. Add to `.env`:
   ```env
   TELEGRAM_BOT_TOKEN=your-token
   TELEGRAM_CHAT_ID=your-chat-id
   ```

### Email Setup (Gmail)

1. Enable 2-Factor Authentication on your Google account
2. Create an [App Password](https://support.google.com/accounts/answer/185833)
3. Add to `.env`:
   ```env
   EMAIL_USERNAME=your-email@gmail.com
   EMAIL_PASSWORD=your-app-password
   ```

### OpenAI LLM Setup

1. Get API key from [OpenAI](https://platform.openai.com/api-keys)
2. Add to `.env`:
   ```env
   OPENAI_API_KEY=sk-your-key-here
   ```

**Without LLM**: System uses mock summaries (first 150 chars of article)

## 📊 How It Works

### Phase 1: News Fetcher Agent
- Fetches articles from configured RSS feeds
- Filters articles from last 24 hours
- Extracts: title, URL, description, source, publish date
- Stores in SQLite database

### Phase 2: News Analysis Agent
- **Deduplication**: Detects duplicate articles using text similarity (60% threshold)
- **Grouping**: Clusters related articles by keywords
- **Ranking**: Scores articles by:
  - Recency (newer = higher)
  - Source credibility
  - Title length/importance

### Phase 3: LLM Summarization
- Generates 2-3 sentence summaries for each article
- Uses OpenAI GPT-4 (configurable)
- Falls back to excerpt if API unavailable
- Creates formatted daily digest

### Phase 4: Multi-Channel Delivery
- **Telegram**: Sends complete digest to Telegram chat
- **Email**: Sends formatted digest via SMTP
- **Database**: Tracks delivery status

## 📈 Database Schema

### Articles Table
```sql
articles:
- id (primary key)
- title, url, description, content
- source, published_date, fetched_date
- url_hash (for dedup)
- is_duplicate, is_processed
```

### Digests Table
```sql
digests:
- id (primary key)
- digest_date, content
- article_count
- is_sent, sent_date
```

## 🛠️ Troubleshooting

### Network Errors
- Some RSS feeds may be blocked by firewalls
- Add alternative feeds in `config.py`
- Check internet connectivity

### LLM API Errors
- Invalid API key: Check `OPENAI_API_KEY` in `.env`
- Rate limiting: Wait before retrying
- System automatically falls back to mock summaries

### Telegram Delivery
- 404 Error: Check `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`
- Start a message with your bot first

### Email Delivery (Gmail)
- 535 Error: Use App Password, not regular password
- Enable 2FA on Google account first
- Check [Gmail App Passwords](https://support.google.com/accounts/answer/185833)

## 📚 Usage Examples

### Run Once (Immediate)
```bash
python scheduler.py
# Select option 1
```

### Schedule Daily at 8:00 AM
```bash
python scheduler.py
# Select option 2
# Runs automatically every day at 8 AM
```

### Schedule at Custom Time
```bash
python scheduler.py
# Select option 3
# Enter time: 09:30
```

### Run Individual Agents
```bash
# Fetch news only
python -c "from fetcher import run_fetcher; run_fetcher()"

# Analyze articles only
python -c "from analyzer import run_analyzer; run_analyzer()"

# Generate summaries only
python -c "from summarizer import run_summarizer; run_summarizer()"

# Send digest only
python -c "from delivery import run_delivery; run_delivery()"
```

## 📝 Example Output

```
═══════════════════════════════════════════════════════════════════════════════
                    📰 DAILY NEWS DIGEST
═══════════════════════════════════════════════════════════════════════════════

Date: 2026-06-13T14:03:00
Total Articles: 10

───────────────────────────────────────────────────────────────────────────────

1. Afghans Hold Rare Public Protests Against Taliban Rules
   Source: NYT > World News
   Published: 2026-06-12 22:56:10
   
   The United Nations said it was "deeply concerned" about the arrests of dozens 
   of women, and reported that two people were killed in protests organized...
   
   Read more: https://www.nytimes.com/2026/06/12/world/asia/taliban-protests-afghanistan.html

[... more articles ...]

═══════════════════════════════════════════════════════════════════════════════
```

## 🔒 Security Notes

- **Never commit `.env`** with real credentials to Git
- Use [App Passwords](https://support.google.com/accounts/answer/185833) for Gmail
- Keep API keys private
- Consider using environment variables in production

## 📦 Dependencies

- **feedparser**: RSS feed parsing
- **requests**: HTTP client
- **sqlalchemy**: Database ORM
- **python-dotenv**: Environment variable management
- **openai**: LLM integration
- **schedule**: Task scheduling

## 🚀 Next Steps & Enhancements

- [ ] Add support for more delivery channels (Slack, Discord, WhatsApp)
- [ ] Implement custom NLP keyword extraction
- [ ] Add sentiment analysis
- [ ] User preferences (topics, sources, delivery time)
- [ ] Web dashboard for viewing digests
- [ ] Database backup & export
- [ ] Multi-language support
- [ ] Docker containerization
- [ ] Cloud deployment (AWS, GCP, Azure)

## 📖 Documentation

For more details on each component:
- `config.py` - Configuration and settings
- `database.py` - Database schema and operations
- `fetcher.py` - RSS fetching logic
- `analyzer.py` - Article analysis and ranking
- `summarizer.py` - LLM summarization
- `delivery.py` - Multi-channel delivery
- `scheduler.py` - Scheduling and orchestration

## 📞 Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review logs in console output
3. Verify `.env` configuration
4. Check internet connectivity
5. Ensure all dependencies are installed

## 📄 License

This project is open-source and available for personal and commercial use.

---

**Happy News Digesting! 📰✨**

Built with Python, LLMs, and ❤️
