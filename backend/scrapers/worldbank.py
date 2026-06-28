"""
World Bank Documents & Reports API — Nigeria procurement plans and tender notices.
Uses /api/v2/wds which is the live endpoint (v2/procurement is retired).
Free, no auth required.
"""
import httpx
import hashlib
from datetime import datetime
from .base import ScrapedOpportunity

API_URL = "https://search.worldbank.org/api/v2/wds"

TRAVEL_KEYWORDS = [
    "travel", "tmc", "airline", "hotel", "accommodation", "tour",
    "ticketing", "logistics", "visa", "flight", "hospitality",
    "car hire", "transport", "protocol", "conference",
]

SEARCH_TERMS = [
    "travel management",
    "airline ticketing nigeria",
    "hotel accommodation nigeria",
    "transport services nigeria",
]


def _is_travel_related(text: str) -> bool:
    return any(kw in text.lower() for kw in TRAVEL_KEYWORDS)


def _parse_date(val: str | None) -> datetime | None:
    if not val:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d", "%d-%b-%Y"):
        try:
            return datetime.strptime(val[:19], fmt[:min(19, len(fmt))])
        except ValueError:
            continue
    return None


async def scrape() -> list[ScrapedOpportunity]:
    results = []
    seen = set()

    async with httpx.AsyncClient(timeout=30) as client:
        for term in SEARCH_TERMS:
            try:
                resp = await client.get(API_URL, params={
                    "format": "json",
                    "rows": 50,
                    "os": 0,
                    "countrycode": "NG",
                    "qterm": term,
                    "lang_exact": "English",
                })
                resp.raise_for_status()
                data = resp.json()
                docs = data.get("documents", {})

                for key, doc in docs.items():
                    if not isinstance(doc, dict):
                        continue

                    title = doc.get("display_title") or doc.get("docna", {}).get("0", {}).get("docna", "") or ""
                    if isinstance(title, dict):
                        title = str(title)
                    title = title.strip()

                    if not title or not _is_travel_related(title):
                        continue

                    doc_id = doc.get("id", "")
                    if doc_id in seen:
                        continue
                    seen.add(doc_id)

                    url = doc.get("pdfurl") or doc.get("url_friendly_title") or "https://documents.worldbank.org"
                    ext_id = f"wb_{doc_id or hashlib.md5(title.encode()).hexdigest()}"
                    published = _parse_date(doc.get("docdt") or doc.get("disclosure_date"))
                    org = doc.get("count") or "World Bank / Nigeria"

                    results.append(ScrapedOpportunity(
                        title=title,
                        organization=org,
                        source_name="World Bank",
                        source_url=url,
                        external_id=ext_id,
                        description=doc.get("majdocty", "")[:500],
                        published_at=published,
                        sector="International/NGO",
                    ))

            except Exception as exc:
                raise RuntimeError(f"World Bank scraper error ({term}): {exc}") from exc

    return results
