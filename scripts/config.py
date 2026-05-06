PODCAST_SOURCES = [
    {
        "id": "credit_edge",
        "name": "The Credit Edge",
        "org": "Bloomberg Intelligence",
        "type": "rss",
        "feed_url": "https://www.omnycontent.com/d/playlist/e73c998e-6e60-432f-8610-ae210140c5b1/e74a35e9-c028-4e5f-a3f7-afb10164a717/8792a2e9-d66c-4038-a1fe-afb101654894/podcast.rss",
        "color": "#f97316",  # orange
        "episode_url_base": "https://open.spotify.com/show/0WrBZujO7cbhbaqsNCEbTu",
    },
    {
        "id": "view_from_apollo",
        "name": "The View from Apollo",
        "org": "Apollo Global Management",
        "type": "rss",
        "feed_url": "https://feeds.blubrry.com/feeds/theviewfromapollo.xml",
        "color": "#a855f7",  # purple
        "episode_url_base": "https://www.apolloacademy.com/the-view-from-apollo/",
    },
    {
        "id": "odd_lots",
        "name": "Odd Lots",
        "org": "Bloomberg",
        "type": "rss",
        "feed_url": "https://omnycontent.com/d/playlist/e73c998e-6e60-432f-8610-ae210140c5b1/8A94442E-5A74-4FA2-8B8D-AE27003A8D6B/982F5071-765C-403D-969D-AE27003A8D83/podcast.rss",
        "color": "#06b6d4",  # cyan
        "episode_url_base": "https://open.spotify.com/show/1te7oSFyRVekxMBJUSethH",
    },
    {
        "id": "oaktree_insight",
        "name": "The Insight",
        "org": "Oaktree Capital",
        "type": "rss",
        "feed_url": "https://rss.art19.com/the-insight",
        "color": "#10b981",  # green
        "episode_url_base": "https://open.spotify.com/show/6UllvbuIsyPESs38EWPanH",
    },
]

YOUTUBE_SOURCES = [
    {
        "id": "goldman_sachs",
        "name": "Goldman Sachs",
        "org": "Goldman Sachs",
        "type": "youtube",
        "channel_id": "UCyz6-taovlaOkPsPtK4KNEg",  # youtube.com/@GoldmanSachs
        "color": "#3b82f6",  # blue
    },
    {
        "id": "capital_allocators",
        "name": "Capital Allocators",
        "org": "Ted Seides",
        "type": "youtube",
        "channel_id": "UCbzQ_YWf9RsBP9ATbmv5kxQ",  # youtube.com/c/CapitalAllocators
        "color": "#f43f5e",  # red
    },
]

ALL_SOURCES = PODCAST_SOURCES + YOUTUBE_SOURCES

# How many recent episodes to fetch per source on each run.
# Set high enough to catch any backlog within the DAYS_LOOKBACK window.
MAX_EPISODES_PER_SOURCE = 20

# Look back this many days when checking for new episodes
DAYS_LOOKBACK = 30

# Max transcript length to send to Groq — keep under 9000 tokens (~36000 chars)
MAX_TRANSCRIPT_CHARS = 12_000
