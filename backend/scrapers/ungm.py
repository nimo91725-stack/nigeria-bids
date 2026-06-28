"""
UNGM (UN Global Marketplace) scraper — Nigeria travel/hospitality tenders.
Uses their JSON search API since the RSS feed is no longer available.
"""
import httpx
import hashlib
import logging
from datetime import datetime
from .base import ScrapedOpportunity

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.ungm.org/Public/Notice/Search"
KEYWORDS = ["travel management", "hotel", "airline", "accommodation", "transport services"]


def _parse_date(val: str | None) -> datetime | None:
    if not val:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(val[:19], fmt[:min(19, len(fmt))])
        except ValueError:
            continue
    return None


async def scrape() -> list[ScrapedOpportunity]:
    results = []
    seen = set()

    async with httpx.AsyncClient(timeout=30, verify=False) as client:
        for kw in KEYWORDS:
            try:
                resp = await client.post(SEARCH_URL, json={
                    "noticeType": 0,
                    "countries": ["NGA"],
                    "keyword": kw,
                    "pageIndex": 0,
                    "pageSize": 20,
                })
                resp.raise_for_status()
                data = resp.json()
                notices = data.get("notices", data) if isinstance(data, dict) else data

                if not isinstance(notices, list):
                    continue

                for n in notices:
                    ref = n.get("Reference", "") or n.get("id", "")
                    if ref in seen:
                        continue
                    seen.add(ref)

                    title = n.get("Title", "") or n.get("title", "")
                    org = n.get("AgencyName", "") or n.get("organization", "UN Agency")
                    url = f"https://www.ungm.org/Public/Notice/{ref}" if ref else "https://www.ungm.org"
                    deadline = _parse_date(n.get("DeadlineDate") or n.get("deadline"))

                    results.append(ScrapedOpportunity(
                        title=title,
                        organization=org,
                        source_name="UNGM",
                        source_url=url,
                        external_id=f"ungm_{hashlib.md5(url.encode()).hexdigest()}",
                        description=n.get("Description", "")[:1000],
                        published_at=_parse_date(n.get("PublishedDate") or n.get("published")),
                        deadline=deadline,
                        sector="International/NGO",
                    ))

            except Exception as exc:
                logger.warning(f"UNGM skipped ({kw}): {exc}")
                continue

    return results
