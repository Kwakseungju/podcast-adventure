import hashlib
from datetime import datetime, timedelta, timezone

import feedparser

from scripts.config import (
    DAYS_LOOKBACK,
    MAX_EPISODES_PER_SOURCE,
    MIN_YOUTUBE_DESC_CHARS,
    PODCAST_SOURCES,
    YOUTUBE_SOURCES,
)


def _episode_id(source_id: str, title: str, published: str) -> str:
    raw = f"{source_id}:{title}:{published}"
    return hashlib.md5(raw.encode()).hexdigest()


def _parse_date(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        val = getattr(entry, attr, None)
        if val:
            try:
                return datetime(*val[:6], tzinfo=timezone.utc)
            except Exception:
                continue
    return None


def _get_audio_url(entry) -> str | None:
    for link in getattr(entry, "links", []):
        if link.get("type", "").startswith("audio/"):
            return link.get("href")
    for enc in getattr(entry, "enclosures", []):
        if "audio" in enc.get("type", ""):
            return enc.get("href") or enc.get("url")
    return None


def _get_transcript_url(entry) -> str | None:
    for link in getattr(entry, "links", []):
        rel = link.get("rel", "")
        mime = link.get("type", "")
        if "transcript" in rel or "transcript" in mime:
            return link.get("href")
    transcript = getattr(entry, "podcast_transcript", None)
    if transcript:
        return transcript.get("url") or transcript.get("href")
    return None


def fetch_rss_episodes(source: dict, cutoff: datetime) -> list[dict]:
    print(f"  Parsing RSS: {source['feed_url']}")
    feed = feedparser.parse(source["feed_url"])

    if feed.bozo and not feed.entries:
        print(f"  Feed parse error: {feed.bozo_exception}")
        return []

    episodes = []
    for entry in feed.entries:
        pub_date = _parse_date(entry)
        if pub_date is None or pub_date < cutoff:
            continue

        title = getattr(entry, "title", "Untitled")
        pub_str = pub_date.strftime("%Y-%m-%d")
        iso = pub_date.isocalendar()

        ep = {
            "id": _episode_id(source["id"], title, pub_str),
            "source_id": source["id"],
            "source_name": source["name"],
            "source_org": source["org"],
            "source_color": source["color"],
            "title": title,
            "description": getattr(entry, "summary", ""),
            "published": pub_str,
            "week": f"{iso[0]}-W{iso[1]:02d}",
            "audio_url": _get_audio_url(entry),
            "transcript_url": _get_transcript_url(entry),
            "episode_url": getattr(entry, "link", source.get("episode_url_base", "")),
            "type": "podcast",
            "duration_secs": None,
        }

        itunes_duration = getattr(entry, "itunes_duration", None)
        if itunes_duration:
            try:
                parts = str(itunes_duration).split(":")
                if len(parts) == 3:
                    ep["duration_secs"] = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                elif len(parts) == 2:
                    ep["duration_secs"] = int(parts[0]) * 60 + int(parts[1])
                else:
                    ep["duration_secs"] = int(parts[0])
            except (ValueError, IndexError):
                pass

        episodes.append(ep)
        if len(episodes) >= MAX_EPISODES_PER_SOURCE:
            break

    return episodes


def fetch_youtube_rss_episodes(source: dict, cutoff: datetime) -> list[dict]:
    """Fetch YouTube videos via the free channel RSS feed — no API key needed."""
    channel_id = source["channel_id"]
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    print(f"  Parsing YouTube RSS: {feed_url}")

    feed = feedparser.parse(feed_url)
    if feed.bozo and not feed.entries:
        print(f"  YouTube RSS parse error: {feed.bozo_exception}")
        return []

    episodes = []
    skipped_shorts = 0
    for entry in feed.entries:
        pub_date = _parse_date(entry)
        if pub_date is None or pub_date < cutoff:
            continue

        description = getattr(entry, "summary", "") or ""
        if len(description.strip()) < MIN_YOUTUBE_DESC_CHARS:
            skipped_shorts += 1
            continue

        title = getattr(entry, "title", "Untitled")
        pub_str = pub_date.strftime("%Y-%m-%d")
        iso = pub_date.isocalendar()

        # YouTube RSS entries have yt_videoid tag
        video_id = getattr(entry, "yt_videoid", None)
        if not video_id:
            # Fallback: extract from entry id e.g. "yt:video:VIDEO_ID"
            eid = getattr(entry, "id", "")
            video_id = eid.split(":")[-1] if ":" in eid else eid

        ep = {
            "id": _episode_id(source["id"], title, pub_str),
            "source_id": source["id"],
            "source_name": source["name"],
            "source_org": source["org"],
            "source_color": source["color"],
            "title": title,
            "description": getattr(entry, "summary", ""),
            "published": pub_str,
            "week": f"{iso[0]}-W{iso[1]:02d}",
            "video_id": video_id,
            "episode_url": f"https://www.youtube.com/watch?v={video_id}",
            "type": "youtube",
            "duration_secs": None,
        }
        episodes.append(ep)
        if len(episodes) >= MAX_EPISODES_PER_SOURCE:
            break

    if skipped_shorts:
        print(f"  Skipped {skipped_shorts} short/clip with no usable description")
    return episodes


def fetch_all_new_episodes(existing_ids: set[str]) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS_LOOKBACK)
    new_episodes = []

    for source in PODCAST_SOURCES:
        print(f"Fetching podcast: {source['name']}")
        eps = fetch_rss_episodes(source, cutoff)
        fresh = [e for e in eps if e["id"] not in existing_ids]
        print(f"  {len(fresh)} new episode(s) out of {len(eps)} fetched")
        new_episodes.extend(fresh)

    for source in YOUTUBE_SOURCES:
        print(f"Fetching YouTube: {source['name']}")
        eps = fetch_youtube_rss_episodes(source, cutoff)
        fresh = [e for e in eps if e["id"] not in existing_ids]
        print(f"  {len(fresh)} new episode(s) out of {len(eps)} fetched")
        new_episodes.extend(fresh)

    return new_episodes
