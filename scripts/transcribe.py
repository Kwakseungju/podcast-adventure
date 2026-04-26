"""
Transcript acquisition pipeline:
  YouTube  → youtube-transcript-api  → yt-dlp + Whisper (fallback)
  Podcast  → podcast:transcript tag  → direct audio download + Whisper (fallback)
  Both     → episode description     (last-resort fallback)
"""

import os
import subprocess
import tempfile
import uuid

import requests

_TMP = tempfile.gettempdir()  # works on both Windows and Linux


# ---------------------------------------------------------------------------
# YouTube
# ---------------------------------------------------------------------------

def _yt_transcript_api(video_id: str) -> str | None:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        ytt = YouTubeTranscriptApi()
        try:
            transcript = ytt.fetch(video_id, languages=["en", "en-US", "en-GB"])
        except Exception:
            transcript = ytt.fetch(video_id)
        return " ".join(s.text for s in transcript)
    except Exception as exc:
        print(f"  youtube-transcript-api: {exc}")
        return None


def _yt_whisper(video_url: str) -> str | None:
    """Download YouTube audio via yt-dlp, compress, transcribe with Whisper."""
    return _whisper_from_url(video_url, is_youtube=True)


# ---------------------------------------------------------------------------
# Podcast
# ---------------------------------------------------------------------------

def _rss_transcript(transcript_url: str) -> str | None:
    try:
        resp = requests.get(transcript_url, timeout=30)
        resp.raise_for_status()
        ctype = resp.headers.get("content-type", "")

        if "json" in ctype:
            data = resp.json()
            segments = data.get("segments", [])
            return " ".join(seg.get("body", "") for seg in segments)

        # VTT / SRT — strip timing lines
        lines = []
        for line in resp.text.splitlines():
            line = line.strip()
            if line and "-->" not in line and not line.startswith("WEBVTT") and not line.isdigit():
                lines.append(line)
        return " ".join(lines) or None
    except Exception as exc:
        print(f"  RSS transcript fetch failed: {exc}")
        return None


def _podcast_whisper(audio_url: str) -> str | None:
    return _whisper_from_url(audio_url, is_youtube=False)


# ---------------------------------------------------------------------------
# Shared Whisper helper
# ---------------------------------------------------------------------------

def _whisper_from_url(url: str, is_youtube: bool) -> str | None:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("  No GROQ_API_KEY — skipping Whisper transcription")
        return None

    tmp = os.path.join(_TMP, f"audio_{uuid.uuid4().hex}.mp3")
    try:
        if is_youtube:
            cmd = [
                "yt-dlp", "-x", "--audio-format", "mp3",
                "--audio-quality", "32K",
                "--no-playlist",
                "-o", tmp, url,
            ]
        else:
            # Direct audio link — download with requests, then compress with ffmpeg
            cmd = None

        if cmd:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0 or not os.path.exists(tmp):
                print(f"  yt-dlp failed: {result.stderr[:200]}")
                return None
        else:
            # Download directly
            raw = os.path.join(_TMP, f"raw_{uuid.uuid4().hex}")
            print("  Downloading podcast audio...")
            with requests.get(url, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(raw, "wb") as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        f.write(chunk)
            # Compress to mono 32kHz mp3 via ffmpeg
            ffmpeg_result = subprocess.run(
                ["ffmpeg", "-y", "-i", raw, "-ac", "1", "-ar", "16000",
                 "-b:a", "32k", tmp],
                capture_output=True, timeout=180,
            )
            os.unlink(raw)
            if ffmpeg_result.returncode != 0 or not os.path.exists(tmp):
                print("  ffmpeg compression failed")
                return None

        size_mb = os.path.getsize(tmp) / 1_048_576
        print(f"  Audio ready ({size_mb:.1f} MB), sending to Whisper...")

        # Whisper API limit is 25 MB
        if size_mb > 24:
            print(f"  File too large ({size_mb:.1f} MB) even after compression — skipping")
            return None

        from groq import Groq
        client = Groq(api_key=api_key)
        with open(tmp, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=f,
                response_format="text",
            )
        transcript = result if isinstance(result, str) else result.text
        print(f"  Whisper transcription done ({len(transcript)} chars)")
        return transcript

    except Exception as exc:
        print(f"  Whisper error: {exc}")
        return None
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def get_transcript(episode: dict) -> str | None:
    ep_type = episode.get("type")
    title = episode.get("title", "?")

    if ep_type == "youtube":
        print(f"  [YouTube] Getting transcript for: {title}")
        t = _yt_transcript_api(episode["video_id"])
        if t:
            return t
        print("  Falling back to yt-dlp + Whisper...")
        t = _yt_whisper(episode["episode_url"])
        if t:
            return t
        # YouTube IPs are often blocked on cloud servers — use description
        print("  YouTube blocked on this server — using description as fallback")

    elif ep_type == "podcast":
        print(f"  [Podcast] Getting transcript for: {title}")
        if episode.get("transcript_url"):
            t = _rss_transcript(episode["transcript_url"])
            if t:
                return t
        if episode.get("audio_url"):
            print("  Transcribing audio with Whisper...")
            t = _podcast_whisper(episode["audio_url"])
            if t:
                return t

    # Last resort — episode description
    desc = episode.get("description", "").strip()
    if desc:
        print("  Using episode description as fallback transcript")
        return desc

    print(f"  No transcript available for: {title}")
    return None
