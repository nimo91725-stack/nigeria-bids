"""
Scraper for Tenderboard.ng — aggregated Nigerian tenders via their RSS feed.
"""
import feedparser
import hashlib
from datetime import datetime
from email.utils import parsedate_to_datetime
from .base import ScrapedOpportunity

RSS_URL = "https://tenderboard.ng/feed/"

TRAVEL_KEYWORDS = [
    "travel", "airline", "hotel", "accommodation", "tour", "ticketing",
    "logistics", "visa", "flight", "hospitality", "car hire", "tmc",
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

        link = entry.get("link", RSS_URL)
        ext_id = hashlib.md5(link.encode()).hexdigest()

        published = None
        if entry.get("published"):
            try:
                published = parsedate_to_datetime(entry.published)
            except Exception:
                pass

        results.append(
            ScrapedOpportunity(
                title=title,
                organization=entry.get("author", "Unknown"),
                source_name="Tenderboard.ng",
                source_url=link,
                external_id=f"tenderboard_{ext_id}",
                description=summary[:1000] if summary else None,
                published_at=published,
                sector="Mixed",
            )
        )
    return results
