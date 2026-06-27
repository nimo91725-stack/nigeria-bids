"""
Feed aggregator for UNGM (United Nations Global Marketplace).
Fetches public procurement notices relevant to Nigeria / travel.
"""
import feedparser
import hashlib
from datetime import datetime
from email.utils import parsedate_to_datetime
from .base import ScrapedOpportunity

# UNGM public RSS for Nigeria-related tenders
UNGM_RSS = "https://www.ungm.org/Public/Notice/SearchResult?noticeType=1&deadline=&countries=NGA&keyword=travel&pageIndex=0&pageSize=50&format=rss"


async def scrape() -> list[ScrapedOpportunity]:
    results = []
    feed = feedparser.parse(UNGM_RSS)
    for entry in feed.entries:
        title = entry.get("title", "")
        link = entry.get("link", "https://www.ungm.org")
        summary = entry.get("summary", "")
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
                organization=entry.get("author", "UN Agency"),
                source_name="UNGM",
                source_url=link,
                external_id=f"ungm_{ext_id}",
                description=summary[:1000] if summary else None,
                published_at=published,
                sector="International/NGO",
            )
        )
    return results
