"""
Chatbot module - RAG-style QnA over topic-filtered news articles.
Uses OpenAI gpt-4o-mini for cost efficiency.
"""
import logging
import os
from core.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

CHAT_MODEL = "gpt-4o-mini"
MAX_CONTEXT_CHARS_PER_ARTICLE = 300  # title + snippet per article
MAX_HISTORY_TURNS = 10  # Keep last 10 back-and-forth exchanges


def build_context_from_articles(articles: list[dict]) -> str:
    """
    Build a compact, numbered context string from the list of article dicts.
    Each article contributes title + first 300 chars of description.
    """
    if not articles:
        return "No articles available."

    lines = [f"You have access to {len(articles)} news articles on this topic:\n"]
    for i, a in enumerate(articles, 1):
        desc = (a.get("description") or "").strip()
        # Strip any HTML tags from description
        import re
        desc = re.sub(r"<[^>]+>", "", desc)
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


def ask_chatbot(messages: list[dict], question: str, articles: list[dict], topic: str) -> str:
    """
    Send a question to OpenAI along with article context and conversation history.
    Returns the assistant's reply as a string.
    
    Args:
        messages: Previous conversation turns [{"role": ..., "content": ...}]
        question: The user's new question
        articles: Topic-filtered article dicts (from search.py)
        topic: The topic string searched by the user
    
    Returns:
        str: The assistant response
    """
    api_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return "⚠️ OpenAI API key not configured. Please add `OPENAI_API_KEY` to your `.env` file."

    if not articles:
        return "⚠️ No articles loaded for this topic yet. Please search a topic first using the search bar above."

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        system_prompt = build_system_prompt(articles, topic)

        # Build message list: system + trimmed history + new user message
        trimmed_history = messages[-(MAX_HISTORY_TURNS * 2):]  # Keep last N turns
        openai_messages = [
            {"role": "system", "content": system_prompt},
            *trimmed_history,
            {"role": "user", "content": question},
        ]

        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=openai_messages,
            max_tokens=600,
            temperature=0.4,
        )

        answer = response.choices[0].message.content.strip()
        logger.info(f"Chatbot answered question about '{topic}' ({len(articles)} articles in context)")
        return answer

    except ImportError:
        return "⚠️ OpenAI library not installed. Run: `pip install openai`"
    except Exception as e:
        logger.error(f"Chatbot error: {e}")
        return f"❌ Error getting response: {str(e)}"
