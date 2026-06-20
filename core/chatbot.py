"""
Chatbot module - RAG-style QnA over topic-filtered news articles.
Provider priority:
  1. Google Gemini (gemini-2.0-flash) — free tier
  2. OpenAI (gpt-4o-mini) — fallback
  3. Local keyword search — always works, no API key needed
"""
import logging
import os
import re
from collections import Counter
from core.config import OPENAI_API_KEY, GEMINI_API_KEY  # config.py calls load_dotenv()

logger = logging.getLogger(__name__)

OPENAI_CHAT_MODEL = "gpt-4o-mini"
GEMINI_CHAT_MODEL = "gemini-2.0-flash"
MAX_CONTEXT_CHARS_PER_ARTICLE = 300
MAX_HISTORY_TURNS = 10

# ─────────────────────────────────────────────────────────────────────────────
# Context builder
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# LLM providers
# ─────────────────────────────────────────────────────────────────────────────

def _ask_gemini(system_prompt: str, history: list[dict], question: str) -> str:
    """Call Google Gemini API using the new google-genai SDK."""
    gemini_key = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
    if not gemini_key:
        raise ValueError("GEMINI_API_KEY not set")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=gemini_key)

    contents = []
    for msg in history[-(MAX_HISTORY_TURNS * 2):]:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))
    contents.append(types.Content(role="user", parts=[types.Part(text=question)]))

    response = client.models.generate_content(
        model=GEMINI_CHAT_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=600,
            temperature=0.4,
        ),
    )
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


# ─────────────────────────────────────────────────────────────────────────────
# Local fallback — keyword-based retrieval (zero API calls)
# ─────────────────────────────────────────────────────────────────────────────

_STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "is", "was", "are", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "may", "might",
    "must", "can", "this", "that", "these", "those", "what", "which", "who",
    "how", "when", "where", "why", "with", "from", "by", "about", "into",
    "through", "during", "of", "not", "tell", "me", "give", "show", "list",
    "latest", "recent", "news", "happened", "happening", "any", "some",
    "new", "today", "yesterday", "last", "first", "all", "get", "please",
}


def _score_article(article: dict, keywords: list[str]) -> float:
    """Score an article by how many query keywords appear in title + description."""
    text = (
        (article.get("title") or "") + " " +
        re.sub(r"<[^>]+>", "", article.get("description") or "")
    ).lower()

    score = 0.0
    for kw in keywords:
        count = text.count(kw)
        if count:
            # Title matches worth 3×
            title_count = (article.get("title") or "").lower().count(kw)
            score += title_count * 3 + (count - title_count)
    return score


def _local_answer(question: str, articles: list[dict], topic: str) -> str:
    """
    Keyword-based article retrieval — no API needed.
    Extracts meaningful keywords from the question, scores articles,
    and returns a structured digest of the top matches.
    """
    # Extract meaningful keywords from question
    words = re.findall(r"[a-zA-Z]+", question.lower())
    keywords = [w for w in words if w not in _STOP_WORDS and len(w) > 2]

    # If no keywords, just summarise all articles
    if not keywords:
        keywords = re.findall(r"[a-zA-Z]+", topic.lower())

    # Score and rank articles
    scored = [(a, _score_article(a, keywords)) for a in articles]
    scored.sort(key=lambda x: x[1], reverse=True)

    # Pick top matches (score > 0) or top 5 if none match
    matches = [(a, s) for a, s in scored if s > 0]
    if not matches:
        matches = scored[:5]  # fallback: show top 5 by recency
        note = f"\n\n*No strong keyword matches for your question — showing the {len(matches)} most recent articles instead.*"
    else:
        matches = matches[:6]
        note = ""

    lines = [
        f"📰 **Local Search Results** — {len(matches)} articles matching your question about **{topic}**:",
        f"*(Running in offline mode — no AI API key available. Showing keyword-matched article excerpts.)*",
        "",
    ]

    for i, (a, score) in enumerate(matches, 1):
        pub = a["published_date"].strftime("%b %d, %Y") if a.get("published_date") else "N/A"
        desc = re.sub(r"<[^>]+>", "", a.get("description") or "")
        snippet = desc[:250].strip() + ("..." if len(desc) > 250 else "")

        lines.append(f"**{i}. {a['title']}**")
        lines.append(f"   🗞 *{a['source']}* · {pub}")
        if snippet:
            lines.append(f"   {snippet}")
        lines.append(f"   🔗 [{a['url']}]({a['url']})")
        lines.append("")

    lines.append(note)
    lines.append("---")
    lines.append("💡 *To get AI-generated answers, add a valid `GEMINI_API_KEY` or `OPENAI_API_KEY` to your `.env` file.*")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def ask_chatbot(messages: list[dict], question: str, articles: list[dict], topic: str) -> str:
    """
    Send a question with article context and conversation history.
    Provider priority: Gemini → OpenAI → Local keyword search (always works).
    """
    if not articles:
        return "⚠️ No articles loaded for this topic yet. Please search a topic first using the search bar above."

    system_prompt = build_system_prompt(articles, topic)
    history_for_llm = messages[-(MAX_HISTORY_TURNS * 2):]

    gemini_key = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
    openai_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")

    # ── 1. Try Gemini ──
    if gemini_key:
        try:
            answer = _ask_gemini(system_prompt, history_for_llm, question)
            logger.info(f"[Gemini] answered about '{topic}' ({len(articles)} articles)")
            return answer
        except Exception as e:
            logger.warning(f"[Gemini] failed: {e}")

    # ── 2. Try OpenAI ──
    if openai_key:
        try:
            answer = _ask_openai(system_prompt, history_for_llm, question)
            logger.info(f"[OpenAI] answered about '{topic}' ({len(articles)} articles)")
            return answer
        except Exception as e:
            logger.warning(f"[OpenAI] failed: {e}")

    # ── 3. Local keyword fallback — always works ──
    logger.info(f"[Local] using keyword search fallback for '{topic}'")
    return _local_answer(question, articles, topic)
