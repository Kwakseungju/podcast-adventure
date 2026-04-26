import json
import os
import re

from groq import Groq

from scripts.config import MAX_TRANSCRIPT_CHARS

_GROQ_MODEL = "llama-3.3-70b-versatile"

_SYSTEM = (
    "You are a senior financial analyst specializing in credit markets, "
    "macro economics, and investment strategy. You produce concise, insight-dense "
    "briefings for portfolio managers who have limited time. "
    "You always respond with valid JSON only — no prose, no markdown."
)

_PROMPT_TEMPLATE = """\
Analyze the following transcript from a financial podcast or video and produce a structured briefing.

Source: {source_name} — {source_org}
Title: {title}
Date: {published}

--- TRANSCRIPT START ---
{transcript}
--- TRANSCRIPT END ---

Respond with ONLY a valid JSON object matching this schema exactly:
{{
  "one_line_summary": "One compelling sentence capturing the single most important point.",
  "summary": "Two to three paragraphs covering the main topics, key arguments, and important data points.",
  "key_themes": ["theme1", "theme2", "theme3", "theme4", "theme5"],
  "key_takeaways": [
    "Takeaway 1 — specific and actionable",
    "Takeaway 2 — specific and actionable",
    "Takeaway 3 — specific and actionable",
    "Takeaway 4 — specific and actionable",
    "Takeaway 5 — specific and actionable"
  ],
  "market_relevance": "One to two sentences on why this matters for investors or markets right now."
}}"""


def _extract_json(raw: str) -> dict:
    """Try multiple strategies to extract JSON from the model response."""
    # Strategy 1: direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Strategy 2: strip markdown fences
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Strategy 3: find first { ... } block
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return {}


def summarize_episode(episode: dict) -> dict:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY is not set")

    client = Groq(api_key=api_key)

    transcript = episode.get("transcript", "")
    if len(transcript) > MAX_TRANSCRIPT_CHARS:
        transcript = transcript[:MAX_TRANSCRIPT_CHARS] + "\n\n[Transcript truncated for length]"

    prompt = _PROMPT_TEMPLATE.format(
        source_name=episode.get("source_name", ""),
        source_org=episode.get("source_org", ""),
        title=episode.get("title", ""),
        published=episode.get("published", ""),
        transcript=transcript,
    )

    response = client.chat.completions.create(
        model=_GROQ_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.3,
        max_tokens=1500,
        response_format={"type": "json_object"},  # force JSON output
    )

    raw = response.choices[0].message.content.strip()
    data = _extract_json(raw)

    if not data:
        print(f"  JSON parse failed — raw response: {raw[:200]}")

    return {
        "one_line_summary": data.get("one_line_summary", ""),
        "summary": data.get("summary", ""),
        "key_themes": data.get("key_themes", [])[:5],
        "key_takeaways": data.get("key_takeaways", [])[:5],
        "market_relevance": data.get("market_relevance", ""),
    }
