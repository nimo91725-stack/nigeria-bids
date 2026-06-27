"""
African Development Bank (AfDB) procurement notices — Nigeria projects.
Free public RSS/JSON feed.
"""
import feedparser
import hashlib
from datetime import datetime
from email.utils import parsedate_to_datetime
from .base import ScrapedOpportunity

# AfDB public procurement RSS filtered for Nigeria
RSS_URL = "https://www.afdb.org/en/rss/projects-and-operations/procurement?country=Nigeria"

TRAVEL_KEYWORDS = [
    "travel", "tmc", "airline", "hotel", "accommodation", "tour",
    "ticketing", "logistics", "visa", "flight", "hospitality",
    "car hire", "transport", "protocol", "conference",
]


def _is_travel_related(text: str) -> bool:
    return any(kw in text.lower() for kw in TRAVEL_KEYWORDS)


async def scrape() -> list[ScrapedOpportunity]:
    results = []
    feed = feedparser.parse(RSS_URL)

    for entry in feed.entries:
        title = entry.get("title", "")
        summary = entry.get("summary", "")

        if not _is_travel_related(f"{title} {summary}"):
            continue

        link = entry.get("link", "https://www.afdb.org")
        ext_id = f"afdb_{hashlib.md5(link.encode()).hexdigest()}"

        published = None
        if entry.get("published"):
            try:
                published = parsedate_to_datetime(entry.published)
            except Exception:
                pass

        results.append(ScrapedOpportunity(
            title=title,
            organization=entry.get("author", "African Development Bank"),
            source_name="AfDB",
            source_url=link,
            external_id=ext_id,
            description=summary[:1000] if summary else None,
            published_at=published,
            sector="International/NGO",
        ))

    return results
