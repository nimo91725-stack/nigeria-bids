"""
Scraper for TendersNigeria.com — Nigerian tender aggregator RSS feed.
Replaces the defunct tenderboard.ng.
"""
import feedparser
import hashlib
from email.utils import parsedate_to_datetime
from .base import ScrapedOpportunity

RSS_URL = "https://tendersnigeria.com/feed/"

TRAVEL_KEYWORDS = [
    "travel", "airline", "hotel", "accommodation", "tour", "ticketing",
    "logistics", "visa", "flight", "hospitality", "car hire", "tmc",
    "transport service", "protocol", "conference", "car rental",
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
                source_name="TendersNigeria",
                source_url=link,
                external_id=f"tendersnigeria_{ext_id}",
                description=summary[:1000] if summary else None,
                published_at=published,
                sector="Mixed",
            )
        )
    return results
