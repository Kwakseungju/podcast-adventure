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
    {
        "id": "masters_in_business",
        "name": "Masters in Business",
        "org": "Bloomberg",
        "type": "rss",
        "feed_url": "https://www.omnycontent.com/d/playlist/e73c998e-6e60-432f-8610-ae210140c5b1/4e4cd910-40a1-4619-a5f3-ae2b0012ffff/5873a3cb-298f-40bc-b71f-ae2b0013000d/podcast.rss",
        "color": "#eab308",  # amber
        "episode_url_base": "https://podcasts.apple.com/us/podcast/masters-in-business/id730188152",
    },
    {
        "id": "in_good_company",
        "name": "In Good Company",
        "org": "Norges Bank Investment Management",
        "type": "rss",
        "feed_url": "https://feeds.acast.com/public/shows/622618c7057f3400120d15db",
        "color": "#14b8a6",  # teal
        "episode_url_base": "https://podcasts.apple.com/us/podcast/in-good-company-with-nicolai-tangen/id1614211565",
    },
    {
        "id": "invest_like_the_best",
        "name": "Invest Like the Best",
        "org": "Colossus",
        "type": "rss",
        "feed_url": "https://feeds.megaphone.fm/CLS2859450455",
        "color": "#6366f1",  # indigo
        "episode_url_base": "https://podcasts.apple.com/us/podcast/invest-like-the-best-with-patrick-oshaughnessy/id1154105909",
    },
    {
        "id": "asia_centric",
        "name": "Asia Centric",
        "org": "Bloomberg Intelligence",
        "type": "rss",
        "feed_url": "https://www.omnycontent.com/d/playlist/e73c998e-6e60-432f-8610-ae210140c5b1/992d604b-06ca-40cb-88b2-af6c016f5aa0/75a9f17c-2ff1-42c9-9a27-af6c016fae89/podcast.rss",
        "color": "#d946ef",  # fuchsia
        "episode_url_base": "https://podcasts.apple.com/us/podcast/asia-centric-by-bloomberg-intelligence/id1567680325",
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

# YouTube Shorts and promo clips publish with an empty description. Since
# YouTube's caption API is blocked from cloud runners, the description is the
# only text this pipeline ever gets for a video — so anything shorter than this
# has nothing summarizable in it and is skipped at fetch time.
MIN_YOUTUBE_DESC_CHARS = 300

# Max transcript length to send to Groq. ~4.5K tokens, which has to leave room
# for the completion budget inside the free tier's 8K tokens/minute ceiling.
# Raising this meaningfully requires a paid Groq tier, not just a bigger number.
MAX_TRANSCRIPT_CHARS = 18_000

# Pause between summarization calls. The free tier allows 8K tokens/minute and
# each call spends ~5.3K, so this keeps a sustained run just under the limit.
SUMMARIZE_SLEEP_SECS = 45
