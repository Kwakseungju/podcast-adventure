"""One-time script to fix episodes where JSON was stored as raw text in summary."""
import json
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_BS = chr(92)  # backslash


def _escape_control_in_strings(s: str) -> str:
    """Escape newlines/tabs only inside JSON string values so json.loads can parse."""
    result = []
    in_str = False
    skip_next = False
    for ch in s:
        if skip_next:
            result.append(ch)
            skip_next = False
        elif ch == _BS and in_str:
            result.append(ch)
            skip_next = True
        elif ch == '"':
            result.append(ch)
            in_str = not in_str
        elif in_str and ch == "\n":
            result.append(_BS + "n")
        elif in_str and ch == "\r":
            result.append(_BS + "r")
        elif in_str and ch == "\t":
            result.append(_BS + "t")
        else:
            result.append(ch)
    return "".join(result)


DATA_FILE = Path("data/episodes.json")

with open(DATA_FILE, encoding="utf-8") as f:
    episodes = json.load(f)

fixed = 0
for ep in episodes:
    if ep.get("key_takeaways"):
        continue  # already fine

    summary = ep.get("summary", "")
    if not summary.startswith("{"):
        continue  # not embedded JSON

    sanitized = _escape_control_in_strings(summary)
    try:
        data = json.loads(sanitized)
    except json.JSONDecodeError as e:
        print(f"Could not parse {ep['title']}: {e}")
        continue

    ep["one_line_summary"] = data.get("one_line_summary", ep.get("one_line_summary", ""))
    ep["summary"]          = data.get("summary", "")
    ep["key_themes"]       = data.get("key_themes", [])[:5]
    ep["key_takeaways"]    = data.get("key_takeaways", [])[:5]
    ep["market_relevance"] = data.get("market_relevance", "")
    fixed += 1
    print(f"Fixed: {ep['title']}")

with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(episodes, f, indent=2, ensure_ascii=False)

print(f"\nDone - fixed {fixed} episode(s)")
