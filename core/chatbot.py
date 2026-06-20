"""
Chatbot module - RAG-style QnA over topic-filtered news articles.
Supports two LLM providers:
  1. Google Gemini (gemini-1.5-flash) — free tier, used by default
  2. OpenAI (gpt-4o-mini) — fallback if OPENAI_API_KEY is set and Gemini fails

Set GEMINI_API_KEY in .env to use Gemini (free at https://aistudio.google.com/app/apikey)
"""
import logging
import os
import re
from core.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

OPENAI_CHAT_MODEL = "gpt-4o-mini"
GEMINI_CHAT_MODEL = "gemini-1.5-flash"  # Free tier: 15 req/min, 1M tokens/day
MAX_CONTEXT_CHARS_PER_ARTICLE = 300
MAX_HISTORY_TURNS = 10  # Keep last 10 exchanges in context


def build_context_from_articles(articles: list[dict]) -> str:
    """Build a compact numbered context string from article dicts."""
    if not articles:
        return "No articles available."

    lines = [f"You have access to {len(articles)} news articles on this topic:\n"]
    for i, a in enumerate(articles, 1):
        desc = re.sub(r"<[^>]+>", "", (a.get("description") or "").strip())
        snippet = desc[:MAX_CONTEXT_CHARS_PER_ARTICLE] + ("..." if len(desc) > MAX_CONTEXT_CHARS_PER_ARTICLE else "")
        lines.append(
            f"{i}. [{a['source']}] {a['title']}\n"
            f"   Published: {a['published_date']}\n"
            f"   {snippet}\n"
            f"   URL: {a['url']}\n"
        )
    return "\n".join(lines)


def build_system_prompt(articles: list[dict], topic: str) -> str:
    """Build the system prompt grounding the LLM in the provided articles."""
    context = build_context_from_articles(articles)
    return f"""You are a helpful news assistant for DigestHub.
The user has searched for the topic: "{topic}".
You ONLY answer questions based on the news articles provided below.
If the answer is not in the articles, say so clearly — do not make things up.
Always cite the article source or title when answering.
Keep answers concise and helpful.

--- NEWS CONTEXT ---
{context}
--- END CONTEXT ---"""


def _ask_gemini(system_prompt: str, history: list[dict], question: str) -> str:
    """Call Google Gemini API."""
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if not gemini_key:
        raise ValueError("GEMINI_API_KEY not set")

    import google.generativeai as genai
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel(
        GEMINI_CHAT_MODEL,
        system_instruction=system_prompt
    )

    # Convert history to Gemini format
    gemini_history = []
    for msg in history[-(MAX_HISTORY_TURNS * 2):]:
        role = "user" if msg["role"] == "user" else "model"
        gemini_history.append({"role": role, "parts": [msg["content"]]})

    chat = model.start_chat(history=gemini_history)
    response = chat.send_message(question)
    return response.text.strip()


def _ask_openai(system_prompt: str, history: list[dict], question: str) -> str:
    """Call OpenAI API."""
    api_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")

    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    trimmed_history = history[-(MAX_HISTORY_TURNS * 2):]
    openai_messages = [
        {"role": "system", "content": system_prompt},
        *trimmed_history,
        {"role": "user", "content": question},
    ]

    response = client.chat.completions.create(
        model=OPENAI_CHAT_MODEL,
        messages=openai_messages,
        max_tokens=600,
        temperature=0.4,
    )
    return response.choices[0].message.content.strip()


def ask_chatbot(messages: list[dict], question: str, articles: list[dict], topic: str) -> str:
    """
    Send a question to the LLM with article context and conversation history.
    Tries Gemini first (free), falls back to OpenAI.
    
    Args:
        messages: Previous conversation turns [{"role": ..., "content": ...}]
        question: The user's new question
        articles: Topic-filtered article dicts
        topic: The topic string the user searched

    Returns:
        str: The assistant response
    """
    if not articles:
        return "⚠️ No articles loaded for this topic yet. Please search a topic first using the search bar above."

    system_prompt = build_system_prompt(articles, topic)
    history_for_llm = messages[-(MAX_HISTORY_TURNS * 2):]

    gemini_key = os.getenv("GEMINI_API_KEY", "")
    openai_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")

    # ── Try Gemini first (free tier) ──
    if gemini_key:
        try:
            answer = _ask_gemini(system_prompt, history_for_llm, question)
            logger.info(f"Gemini answered question about '{topic}' ({len(articles)} articles in context)")
            return answer
        except Exception as e:
            logger.warning(f"Gemini failed: {e} — trying OpenAI fallback...")

    # ── Fallback to OpenAI ──
    if openai_key:
        try:
            answer = _ask_openai(system_prompt, history_for_llm, question)
            logger.info(f"OpenAI answered question about '{topic}' ({len(articles)} articles in context)")
            return answer
        except Exception as e:
            logger.error(f"OpenAI also failed: {e}")
            return (
                f"❌ Both AI providers failed.\n\n"
                f"**OpenAI error**: {str(e)}\n\n"
                f"To fix this:\n"
                f"- **Gemini (free)**: Get a key at https://aistudio.google.com/app/apikey and add `GEMINI_API_KEY=...` to your `.env`\n"
                f"- **OpenAI**: Top up credits at https://platform.openai.com/account/billing"
            )

    # ── No keys at all ──
    return (
        "⚠️ No AI provider configured.\n\n"
        "**Option 1 — Gemini (Free)**: Get a key at https://aistudio.google.com/app/apikey\n"
        "Then add to your `.env` file:\n```\nGEMINI_API_KEY=your_key_here\n```\n\n"
        "**Option 2 — OpenAI**: Add credits at https://platform.openai.com/account/billing"
    )
