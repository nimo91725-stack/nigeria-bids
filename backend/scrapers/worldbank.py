"""
World Bank / IFC Procurement API — Nigeria-funded project tenders.
Free, no auth required.
Docs: https://search.worldbank.org/api/v2/procurement
"""
import httpx
import hashlib
from datetime import datetime
from .base import ScrapedOpportunity

API_URL = "https://search.worldbank.org/api/v2/procurement"

TRAVEL_KEYWORDS = [
    "travel", "tmc", "airline", "hotel", "accommodation", "tour",
    "ticketing", "logistics", "visa", "flight", "hospitality",
    "car hire", "transport", "protocol", "conference",
]


def _is_travel_related(text: str) -> bool:
    return any(kw in text.lower() for kw in TRAVEL_KEYWORDS)


def _parse_date(val: str | None) -> datetime | None:
    if not val:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d", "%d-%b-%Y"):
        try:
            return datetime.strptime(val[:len(fmt)], fmt)
        except ValueError:
            continue
    return None


async def _fetch_page(client: httpx.AsyncClient, params: dict) -> dict:
    resp = await client.get(API_URL, params=params)
    resp.raise_for_status()
    return resp.json()


async def scrape() -> list[ScrapedOpportunity]:
    results = []
    base_params = {
        "format": "json",
        "rows": 50,
        "os": 0,
        "countrycode": "NG",         # Nigeria ISO code
        "lang_exact": "English",
        "fct": "procurement_type_exact:Goods,Services",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        # Page through results
        for offset in range(0, 200, 50):
            try:
                params = {**base_params, "os": offset}
                data = await _fetch_page(client, params)
                docs = data.get("documents", {})

                if not docs:
                    break

                for key, doc in docs.items():
                    if not isinstance(doc, dict):
                        continue

                    title = doc.get("project_name") or doc.get("notice_title") or ""
                    description = doc.get("notice_text") or doc.get("procurement_description") or ""

                    if not _is_travel_related(f"{title} {description}"):
                        continue

                    notice_id = doc.get("id") or doc.get("noticd") or ""
                    ext_id = f"wb_{notice_id or hashlib.md5(title.encode()).hexdigest()}"
                    url = doc.get("url") or doc.get("source_url") or "https://projects.worldbank.org"

                    deadline = _parse_date(doc.get("submission_date") or doc.get("deadline"))
                    published = _parse_date(doc.get("notice_date") or doc.get("publication_date"))
                    org = doc.get("borrower") or doc.get("org_name") or "World Bank / Nigeria"

                    results.append(ScrapedOpportunity(
                        title=title,
                        organization=org,
                        source_name="World Bank",
                        source_url=url,
                        external_id=ext_id,
                        description=description[:1000],
                        deadline=deadline,
                        published_at=published,
                        sector="International/NGO",
                    ))

                # Stop if fewer results than page size — last page
                if len(docs) < 50:
                    break

            except Exception as exc:
                raise RuntimeError(f"World Bank scraper error (offset {offset}): {exc}") from exc

    return results
