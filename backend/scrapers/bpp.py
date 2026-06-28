"""
Scraper for Bureau of Public Procurement (BPP) Nigeria.
BPP is a regulatory body and does not host a public tender listing.
We pull their WordPress posts (circulars/notices) as a signal feed instead.
Actual Nigerian government tenders come via tendersnigeria.com.
"""
import hashlib
import httpx
import logging
from datetime import datetime
from .base import ScrapedOpportunity

logger = logging.getLogger(__name__)

POSTS_API = "https://bpp.gov.ng/wp-json/wp/v2/posts?per_page=20&_fields=id,title,link,date,excerpt"

TRAVEL_KEYWORDS = [
    "travel", "airline", "hotel", "accommodation", "ticketing",
    "logistics", "visa", "flight", "hospitality", "car hire", "tmc",
    "transport service", "protocol", "conference",
]


def _is_travel_related(text: str) -> bool:
    return any(kw in text.lower() for kw in TRAVEL_KEYWORDS)


async def scrape() -> list[ScrapedOpportunity]:
    results = []
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True, verify=False) as client:
            resp = await client.get(POSTS_API)
            resp.raise_for_status()
            posts = resp.json()

        for post in posts:
            title = post.get("title", {}).get("rendered", "")
            excerpt = post.get("excerpt", {}).get("rendered", "")
            if not _is_travel_related(f"{title} {excerpt}"):
                continue

            link = post.get("link", "https://bpp.gov.ng")
            ext_id = f"bpp_{hashlib.md5(link.encode()).hexdigest()}"
            published = None
            raw_date = post.get("date", "")
            if raw_date:
                try:
                    published = datetime.fromisoformat(raw_date)
                except ValueError:
                    pass

            results.append(ScrapedOpportunity(
                title=title,
                organization="Bureau of Public Procurement",
                source_name="BPP Nigeria",
                source_url=link,
                external_id=ext_id,
                description=excerpt[:500] if excerpt else None,
                published_at=published,
                sector="Government",
            ))

    except Exception as exc:
        logger.warning(f"BPP scraper error: {exc}")

    return results
