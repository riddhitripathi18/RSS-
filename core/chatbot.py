"""
Chatbot module - RAG-style QnA over topic-filtered news articles.
Provider priority:
  1. NVIDIA (nvidia/llama-3.1-nemotron-ultra-253b-v1) — primary
  2. OpenAI (gpt-4o-mini) — fallback
  3. Local keyword search — always works, no API key needed
"""
import logging
import os
import re
from collections import Counter
from core.config import OPENAI_API_KEY, NVIDIA_API_KEY  # config.py calls load_dotenv()

logger = logging.getLogger(__name__)

OPENAI_CHAT_MODEL = "gpt-4o-mini"
NVIDIA_CHAT_MODEL = "meta/llama-3.1-8b-instruct"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
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

def _ask_nvidia(system_prompt: str, history: list[dict], question: str) -> str:
    """Call NVIDIA NIM API (OpenAI-compatible endpoint)."""
    api_key = NVIDIA_API_KEY or os.getenv("NVIDIA_API_KEY", "")
    if not api_key:
        raise ValueError("NVIDIA_API_KEY not set")

    from openai import OpenAI
    client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=api_key)

    trimmed_history = history[-(MAX_HISTORY_TURNS * 2):]
    nvidia_messages = [
        {"role": "system", "content": system_prompt},
        *trimmed_history,
        {"role": "user", "content": question},
    ]

    response = client.chat.completions.create(
        model=NVIDIA_CHAT_MODEL,
        messages=nvidia_messages,
        max_tokens=600,
        temperature=0.4,
    )
    return response.choices[0].message.content.strip()


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
    lines.append("💡 *To get AI-generated answers, add a valid `NVIDIA_API_KEY` or `OPENAI_API_KEY` to your `.env` file.*")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def ask_chatbot(messages: list[dict], question: str, articles: list[dict], topic: str) -> str:
    """
    Send a question with article context and conversation history.
    Provider priority: NVIDIA → OpenAI → Local keyword search (always works).
    """
    if not articles:
        return "⚠️ No articles loaded for this topic yet. Please search a topic first using the search bar above."

    system_prompt = build_system_prompt(articles, topic)
    history_for_llm = messages[-(MAX_HISTORY_TURNS * 2):]

    nvidia_key = NVIDIA_API_KEY or os.getenv("NVIDIA_API_KEY", "")
    openai_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")

    # ── 1. Try NVIDIA ──
    if nvidia_key:
        try:
            answer = _ask_nvidia(system_prompt, history_for_llm, question)
            logger.info(f"[NVIDIA] answered about '{topic}' ({len(articles)} articles)")
            return answer
        except Exception as e:
            logger.warning(f"[NVIDIA] failed: {e}")
            nvidia_error = str(e)
    else:
        nvidia_error = "Key not found in environment"

    # ── 2. Try OpenAI ──
    if openai_key:
        try:
            answer = _ask_openai(system_prompt, history_for_llm, question)
            logger.info(f"[OpenAI] answered about '{topic}' ({len(articles)} articles)")
            return answer
        except Exception as e:
            logger.warning(f"[OpenAI] failed: {e}")
            openai_error = str(e)
    else:
        openai_error = "Key not found in environment"

    # ── 3. Show errors + local fallback ──
    logger.info(f"[Local] using keyword search fallback for '{topic}'")
    local_result = _local_answer(question, articles, topic)

    error_block = (
        f"\n\n---\n"
        f"⚠️ **Both AI providers failed — showing local keyword results instead.**\n\n"
        f"| Provider | Error |\n"
        f"|----------|-------|\n"
        f"| 🟣 NVIDIA | `{nvidia_error}` |\n"
        f"| 🟡 OpenAI | `{openai_error}` |\n"
    )
    return local_result + error_block


def generate_150_word_summary(title: str, description: str) -> str:
    """Generate a high-quality 100-150 word summary from title and description using LLM."""
    if not title and not description:
        return "No information available."

    prompt = f"""You are an expert news editor and analyst.
Using only the following news headline and short description, write a detailed, professional, cohesive summary of exactly 100 to 150 words.
Do not invent or add any facts that are not present in the input. Focus on expanding the context in a journalistic, professional tone.

Headline: {title}
Description: {description}

Write only the summary. Do not include any intro like "Here is a summary:" or outro text. Ensure the word count is strictly between 100 and 150 words."""

    nvidia_key = NVIDIA_API_KEY or os.getenv("NVIDIA_API_KEY", "")
    openai_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")

    # 1. Try NVIDIA
    if nvidia_key:
        try:
            from openai import OpenAI
            client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=nvidia_key)
            response = client.chat.completions.create(
                model=NVIDIA_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional news editor. You write high-quality summaries of news events based strictly on given information. You never make things up."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3,
            )
            summary = response.choices[0].message.content.strip()
            if len(summary.split()) >= 60:  # Valid length
                return summary
        except Exception as e:
            logger.warning(f"NVIDIA summary generation failed: {e}")

    # 2. Try OpenAI
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model=OPENAI_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional news editor. You write high-quality summaries of news events based strictly on given information. You never make things up."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3,
            )
            summary = response.choices[0].message.content.strip()
            if len(summary.split()) >= 60:  # Valid length
                return summary
        except Exception as e:
            logger.warning(f"OpenAI summary generation failed: {e}")

    # Offline/fallback mode: return description
    return description or title


def generate_key_takeaways(title: str, description: str) -> str:
    """Generate 3-4 bullet points highlighting key takeaways from title and description."""
    if not title and not description:
        return "- No information available."

    prompt = f"""You are an expert news editor.
Based ONLY on the following news headline and short description, write exactly 3 to 4 concise bullet points highlighting key takeaways.
Each bullet point must be 15 to 30 words.
Do not add any intro like "Here are the key takeaways:" or outro text. Output only the bullet points.

Headline: {title}
Description: {description}"""

    nvidia_key = NVIDIA_API_KEY or os.getenv("NVIDIA_API_KEY", "")
    openai_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")

    # 1. Try NVIDIA
    if nvidia_key:
        try:
            from openai import OpenAI
            client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=nvidia_key)
            response = client.chat.completions.create(
                model=NVIDIA_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional news editor. You extract clean, concise bulleted takeaways. You never make things up."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"NVIDIA takeaways generation failed: {e}")

    # 2. Try OpenAI
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model=OPENAI_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional news editor. You extract clean, concise bulleted takeaways. You never make things up."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"OpenAI takeaways generation failed: {e}")

    # Local fallback
    if description:
        sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', description) if s.strip()]
        if len(sentences) >= 2:
            return "\n".join([f"- {s}" for s in sentences[:4]])
        return f"- {title}\n- {description}"
    return f"- {title}"


def generate_5ws_summary(title: str, description: str) -> str:
    """Generate a 5 Ws (Who, What, Where, When, Why) breakdown from title and description."""
    if not title and not description:
        return "- **Who**: N/A\n- **What**: N/A\n- **Where**: N/A\n- **When**: N/A\n- **Why**: N/A"

    prompt = f"""You are an expert news editor.
Based ONLY on the following headline and description, break down the news story into the 5 Ws: Who, What, Where, When, Why.
Format the output exactly as:
- **Who**: [Who is involved]
- **What**: [What happened]
- **Where**: [Where did it occur]
- **When**: [When did it occur]
- **Why**: [Why did it happen]

Keep each explanation concise (under 20 words). Do not add any intro or outro text.

Headline: {title}
Description: {description}"""

    nvidia_key = NVIDIA_API_KEY or os.getenv("NVIDIA_API_KEY", "")
    openai_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")

    # 1. Try NVIDIA
    if nvidia_key:
        try:
            from openai import OpenAI
            client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=nvidia_key)
            response = client.chat.completions.create(
                model=NVIDIA_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional news editor. You analyze stories into the 5 Ws. You never make things up."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"NVIDIA 5Ws generation failed: {e}")

    # 2. Try OpenAI
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model=OPENAI_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional news editor. You analyze stories into the 5 Ws. You never make things up."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"OpenAI 5Ws generation failed: {e}")

    # Local fallback
    who = "Key parties mentioned in headline"
    what = title
    where = "See full article"
    when = "Recent"
    why = description or "Refer to full article for details"
    return f"- **Who**: {who}\n- **What**: {what}\n- **Where**: {where}\n- **When**: {when}\n- **Why**: {why}"


def clean_trending_overview(text: str) -> str:
    """Strip markdown or HTML links from the text, replacing them with bold topic names."""
    if not text:
        return text
    # 1. HTML links like <a href="...">**Topic**</a> or <a href="...">Topic</a>
    text = re.sub(r'<a\s+[^>]*>\s*\*\*([^*]+)\*\*\s*</a>', r'**\1**', text)
    text = re.sub(r'<a\s+[^>]*>([^<]+)</a>', r'**\1**', text)
    
    # 2. Markdown links like **[Topic](link)**, [**Topic**](link), or [Topic](link)
    text = re.sub(r'\*\*\[([^\]]+)\]\([^)]+\)\*\*', r'**\1**', text)
    text = re.sub(r'\[\*\*([^*]+)\*\*\]\([^)]+\)', r'**\1**', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'**\1**', text)
    
    # 3. Clean up any accidental double-nested asterisks like ****Topic****
    text = re.sub(r'\*\*\*\*([^*]+)\*\*\*\*', r'**\1**', text)
    return text


def generate_trending_overview(articles: list[dict]) -> str:
    """Generate a cohesive summary of the major developments in the last 24 hours based on top articles."""
    if not articles:
        return "No articles have been read or fetched in the last 24 hours."

    context_lines = []
    for idx, a in enumerate(articles, 1):
        context_lines.append(f"{idx}. [{a['source']}] {a['title']}")
        context_lines.append(f"   Summary: {a.get('content') or a.get('description') or ''}")

    prompt = f"""You are a professional senior news editor.
Review the following top 10 read news articles from the last 24 hours and identify the main news topics/categories (e.g. Middle East, Sports, Finance, Global Politics, Climate, etc.) they cover.
Synthesize the articles into a clean numbered list of these main topics.
For each topic, write exactly one numbered list item in this format:
[Number]. **[Topic Name]** - [Crisp, concise summary of 30 words or less describing what happened in this topic].

CRITICAL FORMAT REQUIREMENT:
- Output a numbered list (1., 2., 3., etc.).
- Ensure there is a blank line (double newline) between each numbered list item so it renders correctly as a vertical list.
- Format the category/topic name in bold using markdown double asterisks (e.g. `**Middle East**`). Do not make it a clickable link.
- Keep each summary extremely concise (30 words or less).

--- TOP READ ARTICLES ---
{"\n".join(context_lines)}
--- END CONTEXT ---

Format Example:
1. **Middle East** - Qatari and Pakistani mediators report progress in U.S.-Iran peace talks in Switzerland.

2. **Sports** - Gianni Infantino is building ties with the Trump administration, raising concerns about FIFA's future.

Overview Summary:"""

    nvidia_key = NVIDIA_API_KEY or os.getenv("NVIDIA_API_KEY", "")
    openai_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")

    # 1. Try NVIDIA
    if nvidia_key:
        try:
            from openai import OpenAI
            client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=nvidia_key)
            response = client.chat.completions.create(
                model=NVIDIA_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional senior news anchor. You synthesize news into a vertical numbered list of topics, bolding the category titles (e.g. **Middle East** - ...)."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3,
            )
            return clean_trending_overview(response.choices[0].message.content.strip())
        except Exception as e:
            logger.warning(f"NVIDIA trending overview failed: {e}")

    # 2. Try OpenAI
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model=OPENAI_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional senior news anchor. You synthesize news into a vertical numbered list of topics, bolding the category titles (e.g. **Middle East** - ...)."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3,
            )
            return clean_trending_overview(response.choices[0].message.content.strip())
        except Exception as e:
            logger.warning(f"OpenAI trending overview failed: {e}")

    # Local fallback: compile descriptions into a numbered list of topics/sources in bold text
    from collections import defaultdict
    by_source = defaultdict(list)
    for a in articles:
        by_source[a['source']].append(a)
        
    summary_parts = []
    for idx, (source, arts) in enumerate(by_source.items(), 1):
        titles = ", ".join([art['title'] for art in arts[:2]])
        clean_titles = titles[:120] + ("..." if len(titles) > 120 else "")
        summary_parts.append(f"{idx}. **{source}** - Recent coverage includes: {clean_titles}.")
        
    return clean_trending_overview("Offline Mode: Trending updates by source:\n\n" + "\n\n".join(summary_parts))
