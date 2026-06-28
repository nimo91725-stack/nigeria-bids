"""
Google Gemini AI relevance scorer — judges whether an opportunity
is relevant for a travel management company in Nigeria.

Set in .env:
  GEMINI_API_KEY=your-key
"""
import httpx
import json
import logging
from ..models import Opportunity
from ..config import settings

logger = logging.getLogger(__name__)


SYSTEM_INSTRUCTION = """You are an expert procurement analyst for a Nigerian travel management company (TMC).
Score each tender from 0-100 for relevance. High scores (70+) mean the tender is directly for:
- Travel management services
- Airline ticketing / flight booking
- Hotel accommodation / booking
- Car hire / ground transport
- Visa processing
- Event / conference logistics
- Protocol / VVIP travel services

Medium scores (30-69): indirectly relevant (large projects needing travel services, logistics).
Low scores (0-29): unrelated.

Respond ONLY with a JSON object: {"score": <0-100>, "reason": "<one sentence>"}"""


async def score_opportunity(opp: Opportunity) -> tuple[int, str]:
    """Returns (score 0-100, reason string). Falls back to keyword score on error."""
    api_key = getattr(settings, "gemini_api_key", "")
    if not api_key:
        logger.warning("GEMINI_API_KEY not set — skipping AI scoring")
        return opp.relevance_score or 0, "No API key"

    text = f"Title: {opp.title}\nOrganization: {opp.organization}\nDescription: {(opp.description or '')[:500]}"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {"maxOutputTokens": 100, "temperature": 0},
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            content = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            # Strip markdown code fences if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            result = json.loads(content.strip())
            return int(result["score"]), result.get("reason", "")
    except Exception as e:
        logger.error(f"Gemini scoring failed for '{opp.title[:50]}': {e}")
        return opp.relevance_score or 0, "Scoring error"


async def score_batch(opps: list[Opportunity]) -> list[tuple[int, str]]:
    """Score multiple opportunities concurrently (up to 5 at a time)."""
    import asyncio
    semaphore = asyncio.Semaphore(5)

    async def _score(opp):
        async with semaphore:
            return await score_opportunity(opp)

    return await asyncio.gather(*[_score(o) for o in opps])
