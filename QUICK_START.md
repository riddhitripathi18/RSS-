# 🚀 QUICK START GUIDE

## Your System is Ready! 

You now have a fully functional **AI-Powered Daily News Digest System**. Here's how to use it:

---

## 🔧 Step 1: Configure (Optional but Recommended)

Edit `.env` file in the project root with your credentials:

```env
# For AI Summaries (Optional)
OPENAI_API_KEY=sk-your-key-here

# For Telegram Delivery (Optional)
TELEGRAM_BOT_TOKEN=your-token
TELEGRAM_CHAT_ID=your-chat-id

# For Email Delivery (Optional)
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

**Without these, the system still works but uses basic summaries!**

---

## ▶️ Step 2: Run the System

### Option A: Quick Test (Recommended for First Run)
```bash
python scheduler.py
# Select option 1 to run immediately
```

This will:
1. ✅ Fetch news from RSS feeds
2. ✅ Deduplicate and rank articles
3. ✅ Generate summaries
4. ✅ Attempt to send digest (may fail if not configured)

### Option B: Schedule for Daily Delivery
```bash
python scheduler.py
# Select option 2 for 8:00 AM daily
# Or option 3 for custom time
```

The system will run automatically every day at your chosen time.

---

## 📊 What Gets Created

After first run, you'll have:
- **rss_news.db** - SQLite database with all articles
- **Digest** - Daily news summary saved to database

---

## 📨 Optional: Enable Delivery

### Telegram Setup (2 minutes)
1. Chat with [@BotFather](https://t.me/botfather) on Telegram
2. Create a bot, copy the token
3. Send a message to your new bot
4. Run this to get your chat ID:
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
5. Add to `.env`:
   ```env
   TELEGRAM_BOT_TOKEN=your-token
   TELEGRAM_CHAT_ID=your-chat-id
   ```

### Gmail Setup (2 minutes)
1. Go to Google Account → Security
2. Enable 2-Factor Authentication
3. Create an [App Password](https://support.google.com/accounts/answer/185833)
4. Add to `.env`:
   ```env
   EMAIL_USERNAME=your-email@gmail.com
   EMAIL_PASSWORD=your-app-password
   ```

### OpenAI Setup (Optional for Better Summaries)
1. Get API key from [OpenAI](https://platform.openai.com/api-keys)
2. Add to `.env`:
   ```env
   OPENAI_API_KEY=sk-your-key
   ```

---

## 🎯 Typical Workflow

```
Day 1: Run and Configure
├─ Run: python scheduler.py → Option 1
├─ Configure: Edit .env with credentials
└─ Test: Verify digest was generated

Day 2+: Automated Delivery
├─ Run: python scheduler.py → Option 2 or 3
├─ System runs daily at scheduled time
└─ Digest delivered to Telegram/Email
```

---

## 📋 File Overview

| File | Purpose |
|------|---------|
| `main.py` | Entry point (run individual agents) |
| `scheduler.py` | Run pipeline now or schedule daily |
| `config.py` | RSS feeds, settings, API keys |
| `fetcher.py` | Collects news from RSS |
| `analyzer.py` | Deduplicates and ranks articles |
| `summarizer.py` | Generates summaries with LLM |
| `delivery.py` | Sends via Telegram/Email |
| `database.py` | Database setup & models |
| `.env` | Your credentials (don't share!) |
| `rss_news.db` | News database (auto-created) |

---

## ✅ Verification Checklist

After first run, verify:

- [x] News fetched from RSS feeds
- [x] Duplicates removed
- [x] Articles ranked by importance
- [x] Summaries generated (with or without LLM)
- [x] Database created (rss_news.db)
- [ ] Telegram delivery working (if configured)
- [ ] Email delivery working (if configured)

---

## ❓ Common Questions

**Q: Do I need an OpenAI account?**  
A: No! System uses mock summaries by default. LLM is optional for better quality.

**Q: Can I use different email providers?**  
A: Yes! Update `EMAIL_SMTP_SERVER` and `EMAIL_SMTP_PORT` in `config.py`.

**Q: How often should I run this?**  
A: Daily is recommended (8 AM is typical). Adjust in scheduler.

**Q: Will it work without internet?**  
A: No, needs internet to fetch RSS feeds.

**Q: Can I add more RSS feeds?**  
A: Yes! Edit the `RSS_FEEDS` list in `config.py`.

---

## 🚨 Troubleshooting

**"No module named 'feedparser'"**
```bash
pip install feedparser requests openai
```

**"Database connection error"**
- Ensure you're in the correct directory
- Check file permissions

**"Telegram/Email not working"**
- Verify credentials in `.env`
- Check internet connection
- Review error message in logs

**"No articles fetched"**
- Check RSS feed URLs are accessible
- Verify internet connection
- Add more feeds in `config.py`

---

## 📚 Next: Full Documentation

Read [README.md](README.md) for comprehensive documentation including:
- Architecture details
- All configuration options  
- Troubleshooting guide
- Database schema
- Enhancement ideas

---

## 🎉 You're All Set!

Your AI-Powered News Digest System is ready to use:

```bash
# Run immediately
python scheduler.py
```

**Enjoy your daily news digest! 📰✨**

---

*Questions? Check README.md for detailed documentation.*
