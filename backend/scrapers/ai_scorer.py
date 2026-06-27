"""
Claude AI relevance scorer — uses claude-haiku to judge whether an opportunity
is genuinely relevant for a travel management company in Nigeria.
Fast and cheap: Haiku processes ~100 opportunities for <$0.05.

Set in .env:
  ANTHROPIC_API_KEY=your-key
"""
import httpx
import json
from ..models import Opportunity
from ..config import settings


SYSTEM_PROMPT = """You are an expert procurement analyst for a Nigerian travel management company (TMC).
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
    api_key = getattr(settings, "anthropic_api_key", "")
    if not api_key:
        return opp.relevance_score, "No API key"

    text = f"Title: {opp.title}\nOrganization: {opp.organization}\nDescription: {(opp.description or '')[:500]}"

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 100,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": text}],
                },
            )
            resp.raise_for_status()
            content = resp.json()["content"][0]["text"].strip()
            result = json.loads(content)
            return int(result["score"]), result.get("reason", "")
    except Exception:
        return opp.relevance_score, "Scoring error"


async def score_batch(opps: list[Opportunity]) -> list[tuple[int, str]]:
    """Score multiple opportunities concurrently (up to 5 at a time)."""
    import asyncio
    semaphore = asyncio.Semaphore(5)

    async def _score(opp):
        async with semaphore:
            return await score_opportunity(opp)

    return await asyncio.gather(*[_score(o) for o in opps])
