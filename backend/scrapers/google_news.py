"""
Google Custom Search API — scrapes Nigerian newspaper tender notices.
Requires a free API key from https://developers.google.com/custom-search/v1/overview
and a Custom Search Engine (CSE) scoped to Nigerian news sites.

Set in .env:
  GOOGLE_SEARCH_API_KEY=your-key
  GOOGLE_SEARCH_CX=your-cse-id
"""
import httpx
import hashlib
from datetime import datetime
from .base import ScrapedOpportunity
from ..config import settings

SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

QUERIES = [
    "travel management services tender Nigeria",
    "TMC airline ticketing tender Nigeria",
    "hotel accommodation tender Nigeria government",
    "travel agency RFP Nigeria corporate",
]


async def scrape() -> list[ScrapedOpportunity]:
    if not getattr(settings, "google_search_api_key", "") or not getattr(settings, "google_search_cx", ""):
        return []

    results = []
    seen = set()

    async with httpx.AsyncClient(timeout=30) as client:
        for query in QUERIES:
            try:
                resp = await client.get(SEARCH_URL, params={
                    "key": settings.google_search_api_key,
                    "cx": settings.google_search_cx,
                    "q": query,
                    "num": 10,
                    "dateRestrict": "m1",  # last 1 month
                })
                resp.raise_for_status()
                data = resp.json()

                for item in data.get("items", []):
                    url = item.get("link", "")
                    if url in seen:
                        continue
                    seen.add(url)

                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    ext_id = f"gnews_{hashlib.md5(url.encode()).hexdigest()}"
                    source = item.get("displayLink", "Nigerian News")

                    results.append(ScrapedOpportunity(
                        title=title,
                        organization=source,
                        source_name=f"Google Search — {source}",
                        source_url=url,
                        external_id=ext_id,
                        description=snippet[:1000],
                        sector="Mixed",
                    ))
            except Exception as exc:
                raise RuntimeError(f"Google Search scraper error: {exc}") from exc

    return results
