#!/usr/bin/env python3
"""
Podcast & YouTube Intelligence Tracker
Runs daily via GitHub Actions to fetch, transcribe, summarize, and publish.
"""

import sys
from pathlib import Path

# Fix Unicode output on Windows terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from scripts.fetch_sources import fetch_all_new_episodes
from scripts.generate_html import generate_html
from scripts.store import load_episodes, save_episodes
from scripts.summarize import summarize_episode
from scripts.transcribe import get_transcript

DATA_FILE = Path("data/episodes.json")
HTML_FILE = Path("docs/index.html")


def main() -> None:
    print("=== Podcast Intelligence Tracker ===\n")

    episodes = load_episodes(DATA_FILE)
    existing_ids = {ep["id"] for ep in episodes}
    print(f"Loaded {len(episodes)} existing episode(s)\n")

    new_episodes = fetch_all_new_episodes(existing_ids)
    print(f"\nFound {len(new_episodes)} new episode(s) to process")
    for ep in new_episodes:
        print(f"  - [{ep['source_id']}] {ep['title'][:60]} | desc={len(ep.get('description',''))}c")
    print()

    processed = 0
    failed = 0

    for ep in new_episodes:
        print(f"--- Processing: [{ep['source_name']}] {ep['title']} ({ep['published']}) ---")

        transcript = get_transcript(ep)
        if not transcript:
            print("  Skipped — could not obtain transcript\n")
            failed += 1
            continue

        ep["transcript_length"] = len(transcript)
        ep["transcript"] = transcript  # store temporarily for summarize

        print("  Summarizing...")
        try:
            summary_data = summarize_episode(ep)
        except Exception as exc:
            err = str(exc)
            if "429" in err:
                print(f"  API rate limit reached: {exc}\n")
                del ep["transcript"]
                break  # quota exhausted; remaining episodes will be picked up tomorrow
            print(f"  Summarization failed: {exc}\n")
            failed += 1
            del ep["transcript"]
            continue

        # Don't persist the full transcript in episodes.json (too large)
        del ep["transcript"]

        ep.update(summary_data)
        episodes.append(ep)
        existing_ids.add(ep["id"])
        # Save after each episode so progress isn't lost if the run is cut short
        save_episodes(DATA_FILE, episodes)
        processed += 1
        print(f"  Done. Themes: {', '.join(ep.get('key_themes', []))}\n")

    print(f"Processed: {processed}  Failed/Skipped: {failed}\n")

    save_episodes(DATA_FILE, episodes)
    print(f"Saved {len(episodes)} total episode(s) to {DATA_FILE}")

    generate_html(HTML_FILE, episodes)
    print(f"Generated report → {HTML_FILE}")

    # Only fail if we couldn't even generate the HTML
    pass


if __name__ == "__main__":
    main()
