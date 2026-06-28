"""
SalesPilot bridge — pushes high-relevance bid opportunities (score >= 70)
into SalesPilot as company + contact leads via its REST API.

Required env vars in Nigeria Bids:
  SALESPILOT_API_URL        = https://salespilot-api-350631615628.africa-south1.run.app
  SALESPILOT_INTEGRATION_KEY = <shared secret set in SalesPilot's INTEGRATION_API_KEY>
  SALESPILOT_MIN_SCORE      = 70  (optional, default 70)
"""
import httpx
import logging
from datetime import datetime, timedelta
from ..models import Opportunity
from ..config import settings

logger = logging.getLogger(__name__)

BASE_URL = getattr(settings, "salespilot_api_url", "").rstrip("/")

# Simple in-memory token cache
_token_cache: dict = {"token": None, "expires_at": None}


async def _get_token(client: httpx.AsyncClient) -> str | None:
    now = datetime.utcnow()
    if _token_cache["token"] and _token_cache["expires_at"] > now:
        return _token_cache["token"]

    api_key = getattr(settings, "salespilot_integration_key", "")
    if not (BASE_URL and api_key):
        return None

    try:
        resp = await client.post(
            f"{BASE_URL}/api/v1/auth/integration-token",
            headers={"X-API-Key": api_key},
        )
        resp.raise_for_status()
        token = resp.json()["access_token"]
        _token_cache["token"] = token
        _token_cache["expires_at"] = now + timedelta(minutes=50)
        return token
    except Exception as e:
        logger.error(f"SalesPilot integration auth failed: {e}")
        return None


async def _find_or_create_company(client: httpx.AsyncClient, headers: dict, name: str) -> int | None:
    try:
        resp = await client.get(
            f"{BASE_URL}/api/v1/companies",
            headers=headers,
            params={"search": name, "limit": 5},
        )
        if resp.status_code == 200:
            data = resp.json()
            items = data if isinstance(data, list) else data.get("items", data.get("data", []))
            for company in items:
                if company.get("name", "").lower() == name.lower():
                    return company["id"]

        resp = await client.post(
            f"{BASE_URL}/api/v1/companies",
            headers=headers,
            json={"name": name, "industry": "Government/Public Sector"},
        )
        resp.raise_for_status()
        return resp.json()["id"]
    except Exception as e:
        logger.error(f"SalesPilot company lookup/create failed for '{name}': {e}")
        return None


def _build_contact_payload(opp: Opportunity, company_id: int) -> dict:
    deadline_str = opp.deadline.strftime("%Y-%m-%d") if opp.deadline else "Not specified"
    notes = (
        f"[Nigeria Bids] Relevance score: {opp.relevance_score}/100\n"
        f"Source: {opp.source_name}\n"
        f"Deadline: {deadline_str}\n"
        f"URL: {opp.source_url or 'N/A'}\n"
        f"Sector: {opp.sector or 'N/A'}\n\n"
        f"{(opp.description or '')[:500]}"
    )
    return {
        "first_name": "Procurement",
        "last_name": "Officer",
        "company_id": company_id,
        "job_title": "Procurement / Tender Contact",
        "notes": notes,
        "tags": ["nigeria-bids", f"score-{opp.relevance_score}", opp.sector or "general"],
        "lead_source": "Nigeria Bids Platform",
    }


async def push_opportunity(opp: Opportunity) -> bool:
    """Push a single opportunity to SalesPilot. Returns True on success."""
    if not BASE_URL:
        return False

    async with httpx.AsyncClient(timeout=30) as client:
        token = await _get_token(client)
        if not token:
            return False

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        org_name = opp.organization or "Unknown Organization"
        company_id = await _find_or_create_company(client, headers, org_name)
        if not company_id:
            return False

        payload = _build_contact_payload(opp, company_id)
        try:
            resp = await client.post(f"{BASE_URL}/api/v1/contacts", headers=headers, json=payload)
            resp.raise_for_status()
            logger.info(f"Pushed to SalesPilot: '{opp.title}' (score {opp.relevance_score})")
            return True
        except Exception as e:
            logger.error(f"SalesPilot contact create failed: {e}")
            return False


async def push_high_relevance(opps: list[Opportunity], min_score: int = 70) -> dict:
    """Push all opportunities with relevance_score >= min_score to SalesPilot."""
    min_score = int(getattr(settings, "salespilot_min_score", min_score))
    candidates = [o for o in opps if (o.relevance_score or 0) >= min_score]

    if not candidates:
        return {"pushed": 0, "failed": 0, "skipped": len(opps)}

    pushed, failed = 0, 0
    for opp in candidates:
        ok = await push_opportunity(opp)
        if ok:
            pushed += 1
        else:
            failed += 1

    return {"pushed": pushed, "failed": failed, "skipped": len(opps) - len(candidates)}
