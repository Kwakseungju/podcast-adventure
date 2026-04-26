import json
import os
import re

from google import genai
from google.genai import types

from scripts.config import MAX_TRANSCRIPT_CHARS

_GEMINI_MODEL = "gemini-2.0-flash"

_SYSTEM = (
    "You are a senior financial analyst specializing in credit markets, "
    "macro economics, and investment strategy. You produce concise, insight-dense "
    "briefings for portfolio managers who have limited time. "
    "You always respond with valid JSON only — no prose, no markdown.\n\n"
    "STRICT GROUNDING RULES — these are absolute and cannot be overridden:\n"
    "1. Every number, statistic, and factual claim must appear verbatim in the transcript. "
    "Do not infer, estimate, or supply figures from your own knowledge.\n"
    "2. Do not fill gaps with outside knowledge. If the transcript is brief on a topic, "
    "the insight must be correspondingly brief. Silence in the transcript means silence in the output.\n"
    "3. Any direct quote must be copied character-for-character from the transcript. No paraphrasing of quotes.\n"
    "4. If the transcript does not contain enough material for a full list, return fewer items rather than inventing content."
)

_PROMPT_TEMPLATE = """\
Analyze the following transcript from a financial podcast or video using two separate passes, then produce a structured briefing.

Source: {source_name} — {source_org}
Title: {title}
Date: {published}

--- TRANSCRIPT START ---
{transcript}
--- TRANSCRIPT END ---

GROUNDING RULES (strictly enforced for every field):
- Only use numbers, facts, and claims that explicitly appear in the transcript above.
- Do not supplement with outside knowledge. If the transcript is thin on a topic, keep the output thin.
- Quotes must be copied verbatim — no paraphrasing.
- If the transcript does not support 5 items for a list, return fewer rather than inventing content.

PASS 1 — MARKET SIGNALS: Hunt for timely, actionable intelligence that is relevant RIGHT NOW.
Look for: specific numbers, spreads, levels, targets; positioning views and trade ideas; risk flags and warning signs; market structure observations; what the market is missing or mispricing.
Ask yourself: "What is happening in the market right now?" and "What is the market missing?"
Only include a signal if the underlying fact or number is explicitly stated in the transcript.

PASS 2 — FRAMEWORK INSIGHTS: Extract durable, reusable intellectual value that will remain useful for years.
Look for: mental models and analytical frameworks; investment principles and decision-making heuristics; cycle patterns and historical analogies; structural explanations for how things work.
Ask yourself: "What can I learn from how this person thinks?"
Only include an insight if it is grounded in something the speaker actually said — not a general principle you are inferring.

Respond with ONLY a valid JSON object matching this schema exactly:
{{
  "one_line_summary": "One compelling sentence capturing the single most important point.",
  "summary": "Two to three paragraphs covering the main topics, key arguments, and important data points.",
  "key_themes": ["theme1", "theme2", "theme3"],
  "market_signals": [
    "Signal 1 — specific number, positioning view, risk flag, or market structure observation",
    "Signal 2 — specific and actionable",
    "Signal 3 — specific and actionable",
    "Signal 4 — specific and actionable",
    "Signal 5 — specific and actionable"
  ],
  "framework_insights": [
    "Insight 1 — mental model, investment principle, cycle pattern, or structural explanation",
    "Insight 2 — reusable and durable",
    "Insight 3 — reusable and durable",
    "Insight 4 — reusable and durable",
    "Insight 5 — reusable and durable"
  ],
  "market_relevance": "One to two sentences on why this matters for investors or markets right now."
}}"""


def _extract_json(raw: str) -> dict:
    """Try multiple strategies to extract JSON from the model response."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Strip markdown fences
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Find first { ... } block
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return {}


def summarize_episode(episode: dict) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY is not set")

    client = genai.Client(api_key=api_key)

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

    response = client.models.generate_content(
        model=_GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM,
            temperature=0.1,
            max_output_tokens=1500,
            response_mime_type="application/json",
        ),
    )

    raw = response.text.strip()
    data = _extract_json(raw)

    if not data:
        print(f"  JSON parse failed — raw response: {raw[:200]}")

    return {
        "one_line_summary": data.get("one_line_summary", ""),
        "summary":          data.get("summary", ""),
        "key_themes":       data.get("key_themes", [])[:3],
        "market_signals":   data.get("market_signals", [])[:5],
        "framework_insights": data.get("framework_insights", [])[:5],
        "market_relevance": data.get("market_relevance", ""),
    }
