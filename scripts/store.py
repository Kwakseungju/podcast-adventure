import json
from pathlib import Path


def load_episodes(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_episodes(path: Path, episodes: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Sort newest first before saving
    episodes_sorted = sorted(episodes, key=lambda e: e.get("published", ""), reverse=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(episodes_sorted, f, indent=2, ensure_ascii=False)
