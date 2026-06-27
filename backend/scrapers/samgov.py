"""
SAM.gov API — US federal procurement opportunities (USAID Nigeria, US Embassy, etc.)
Free, no auth required for public search.
Docs: https://open.gsa.gov/api/opportunities-api/
"""
import httpx
import hashlib
from datetime import datetime
from .base import ScrapedOpportunity
from ..config import settings

API_URL = "https://api.sam.gov/opportunities/v2/search"

PARAMS = {
    "api_key": "",                   # Set via settings.samgov_api_key
    "keyword": "travel management nigeria",
    "limit": 100,
    "offset": 0,
    "postedFrom": "",                 # filled dynamically
    "postedTo": "",
    "status": "active",
    "typeOfSetAsideDescription": "",
}

TRAVEL_KEYWORDS = [
    "travel", "tmc", "airline", "hotel", "accommodation", "tour",
    "ticketing", "logistics", "visa", "flight", "hospitality", "car hire",
    "ground transport", "protocol", "conference", "event management",
]

NIGERIA_KEYWORDS = ["nigeria", "nigerian", "lagos", "abuja", "west africa"]


def _is_relevant(title: str, description: str) -> bool:
    text = f"{title} {description}".lower()
    has_travel = any(kw in text for kw in TRAVEL_KEYWORDS)
    has_nigeria = any(kw in text for kw in NIGERIA_KEYWORDS)
    return has_travel or has_nigeria  # Cast wide — relevance scorer will rank


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(date_str[:19], fmt[:len(date_str[:19])])
        except ValueError:
            continue
    return None


async def scrape() -> list[ScrapedOpportunity]:
    results = []
    # Search multiple relevant keyword sets
    searches = [
        "travel management nigeria",
        "TMC nigeria",
        "airline ticketing usaid nigeria",
        "hotel accommodation nigeria USAID",
        "ground transportation nigeria",
    ]

    seen_ids = set()
    async with httpx.AsyncClient(timeout=30) as client:
        for keyword in searches:
            try:
                resp = await client.get(API_URL, params={**PARAMS, "keyword": keyword, "api_key": settings.samgov_api_key})
                resp.raise_for_status()
                data = resp.json()

                for opp in data.get("opportunitiesData", []):
                    sam_id = opp.get("noticeId", "")
                    if sam_id in seen_ids:
                        continue
                    seen_ids.add(sam_id)

                    title = opp.get("title", "")
                    description = opp.get("description", "")

                    if not _is_relevant(title, description):
                        continue

                    ext_id = f"samgov_{sam_id or hashlib.md5(title.encode()).hexdigest()}"
                    deadline = _parse_date(opp.get("responseDeadLine"))
                    published = _parse_date(opp.get("postedDate"))
                    org = opp.get("departmentName") or opp.get("organizationHierarchy", [{}])[0].get("name", "US Government")
                    url = f"https://sam.gov/opp/{sam_id}/view" if sam_id else "https://sam.gov"

                    results.append(ScrapedOpportunity(
                        title=title,
                        organization=org,
                        source_name="SAM.gov (US Federal)",
                        source_url=url,
                        external_id=ext_id,
                        description=(description or "")[:1000],
                        deadline=deadline,
                        published_at=published,
                        sector="International/NGO",
                    ))
            except Exception as exc:
                raise RuntimeError(f"SAM.gov scraper error ({keyword}): {exc}") from exc

    return results
