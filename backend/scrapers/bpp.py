"""
Scraper for Bureau of Public Procurement (BPP) Nigeria — bpp.gov.ng
Fetches general procurement notices and filters for travel-related ones.
"""
import hashlib
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from .base import ScrapedOpportunity

BASE_URL = "https://www.bpp.gov.ng"
TENDERS_URL = f"{BASE_URL}/tenders"

TRAVEL_KEYWORDS = [
    "travel", "airline", "hotel", "accommodation", "tour", "ticketing",
    "logistics", "visa", "flight", "hospitality", "car hire", "tmc",
]


def _is_travel_related(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in TRAVEL_KEYWORDS)


async def scrape() -> list[ScrapedOpportunity]:
    results = []
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(TENDERS_URL)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # BPP lists tenders in table rows — adapt selector if site changes
            rows = soup.select("table tbody tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 3:
                    continue
                title = cells[0].get_text(strip=True)
                if not _is_travel_related(title):
                    continue
                org = cells[1].get_text(strip=True) if len(cells) > 1 else "BPP Nigeria"
                link_tag = cells[0].find("a")
                url = f"{BASE_URL}{link_tag['href']}" if link_tag and link_tag.get("href") else TENDERS_URL
                ext_id = hashlib.md5(url.encode()).hexdigest()

                deadline = None
                if len(cells) > 3:
                    try:
                        deadline = datetime.strptime(cells[3].get_text(strip=True), "%d/%m/%Y")
                    except ValueError:
                        pass

                results.append(
                    ScrapedOpportunity(
                        title=title,
                        organization=org,
                        source_name="BPP Nigeria",
                        source_url=url,
                        external_id=f"bpp_{ext_id}",
                        deadline=deadline,
                        sector="Government",
                    )
                )
    except Exception as exc:
        # Caller handles logging
        raise RuntimeError(f"BPP scraper error: {exc}") from exc
    return results
