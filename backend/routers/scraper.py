from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import Opportunity, AlertConfig, SourceType
from ..schemas import ScrapeResult
from ..scrapers import bpp, tenderboard, ungm, email_parser, samgov, worldbank, afdb, google_news
from ..scrapers.base import ScrapedOpportunity
from ..scrapers.ai_scorer import score_batch
from ..notifications import send_daily_alerts
from ..integrations.salespilot import push_high_relevance
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scrape", tags=["scraper"])

ALL_SCRAPERS = [
    (bpp.scrape,          SourceType.scraped, "BPP Nigeria"),
    (tenderboard.scrape,  SourceType.rss,     "Tenderboard.ng"),
    (ungm.scrape,         SourceType.rss,     "UNGM"),
    (samgov.scrape,       SourceType.rss,     "SAM.gov"),
    (worldbank.scrape,    SourceType.rss,     "World Bank"),
    (afdb.scrape,         SourceType.rss,     "AfDB"),
    (google_news.scrape,  SourceType.scraped, "Google News"),
    (email_parser.scrape, SourceType.email,   "Email"),
]


async def _upsert_opportunity(db: AsyncSession, item: ScrapedOpportunity, source_type: SourceType) -> Opportunity | None:
    existing = await db.execute(
        select(Opportunity).where(Opportunity.external_id == item.external_id)
    )
    if existing.scalar_one_or_none():
        return None
    opp = Opportunity(
        title=item.title,
        organization=item.organization,
        source_type=source_type,
        source_url=item.source_url,
        source_name=item.source_name,
        external_id=item.external_id,
        description=item.description,
        deadline=item.deadline,
        published_at=item.published_at,
        sector=item.sector,
        is_travel_related=True,
    )
    db.add(opp)
    return opp


async def _run_scraper(scraper_fn, source_type: SourceType, source_label: str, db: AsyncSession) -> tuple[ScrapeResult, list[Opportunity]]:
    new_opps = []
    try:
        items: list[ScrapedOpportunity] = await scraper_fn()
        skipped = 0
        for item in items:
            opp = await _upsert_opportunity(db, item, source_type)
            if opp:
                new_opps.append(opp)
            else:
                skipped += 1
        await db.commit()
        for opp in new_opps:
            await db.refresh(opp)

        # AI relevance scoring for new opportunities
        if new_opps:
            scores = await score_batch(new_opps)
            for opp, (score, _) in zip(new_opps, scores):
                opp.relevance_score = score
            await db.commit()

        return ScrapeResult(source=source_label, new_count=len(new_opps), skipped_count=skipped), new_opps
    except Exception as exc:
        logger.error(f"Scraper {source_label} failed: {exc}")
        return ScrapeResult(source=source_label, new_count=0, skipped_count=0, error=str(exc)), []


@router.post("/all", response_model=list[ScrapeResult])
async def scrape_all(db: AsyncSession = Depends(get_db)):
    """Trigger all scrapers, AI-score results, then send alert emails."""
    results = []
    all_new: list[Opportunity] = []
    for fn, stype, label in ALL_SCRAPERS:
        result, new_opps = await _run_scraper(fn, stype, label, db)
        results.append(result)
        all_new.extend(new_opps)

    if all_new:
        alert_configs_result = await db.execute(select(AlertConfig).where(AlertConfig.active == True))
        alert_configs = alert_configs_result.scalars().all()
        alert_summary = await send_daily_alerts(all_new, alert_configs)
        logger.info(f"Alerts: {alert_summary['sent']} sent, {alert_summary['skipped']} skipped")

        # Push high-relevance opportunities to SalesPilot CRM
        sp_summary = await push_high_relevance(all_new)
        logger.info(f"SalesPilot bridge: {sp_summary['pushed']} pushed, {sp_summary['failed']} failed, {sp_summary['skipped']} below threshold")

    return results


@router.post("/rescore", response_model=dict)
async def rescore_all(db: AsyncSession = Depends(get_db)):
    """Re-score all opportunities that have relevance_score == 0 using Gemini."""
    result = await db.execute(
        select(Opportunity).where(Opportunity.relevance_score == 0)
    )
    opps = result.scalars().all()
    if not opps:
        return {"rescored": 0, "message": "No zero-score opportunities found"}
    scores = await score_batch(opps)
    updated = 0
    for opp, (score, reason) in zip(opps, scores):
        if score > 0:
            opp.relevance_score = score
            updated += 1
    await db.commit()
    sp_summary = await push_high_relevance([o for o in opps if (o.relevance_score or 0) >= 70])
    logger.info(f"Rescore: {updated}/{len(opps)} updated. SalesPilot: {sp_summary}")
    return {"rescored": len(opps), "updated": updated, "salespilot": sp_summary}


@router.post("/bpp",         response_model=ScrapeResult)
async def scrape_bpp(db: AsyncSession = Depends(get_db)):
    result, _ = await _run_scraper(bpp.scrape, SourceType.scraped, "BPP Nigeria", db)
    return result

@router.post("/tenderboard",  response_model=ScrapeResult)
async def scrape_tenderboard(db: AsyncSession = Depends(get_db)):
    result, _ = await _run_scraper(tenderboard.scrape, SourceType.rss, "Tenderboard.ng", db)
    return result

@router.post("/ungm",         response_model=ScrapeResult)
async def scrape_ungm(db: AsyncSession = Depends(get_db)):
    result, _ = await _run_scraper(ungm.scrape, SourceType.rss, "UNGM", db)
    return result

@router.post("/samgov",       response_model=ScrapeResult)
async def scrape_samgov(db: AsyncSession = Depends(get_db)):
    result, _ = await _run_scraper(samgov.scrape, SourceType.rss, "SAM.gov", db)
    return result

@router.post("/worldbank",    response_model=ScrapeResult)
async def scrape_worldbank(db: AsyncSession = Depends(get_db)):
    result, _ = await _run_scraper(worldbank.scrape, SourceType.rss, "World Bank", db)
    return result

@router.post("/afdb",         response_model=ScrapeResult)
async def scrape_afdb(db: AsyncSession = Depends(get_db)):
    result, _ = await _run_scraper(afdb.scrape, SourceType.rss, "AfDB", db)
    return result

@router.post("/google",       response_model=ScrapeResult)
async def scrape_google(db: AsyncSession = Depends(get_db)):
    result, _ = await _run_scraper(google_news.scrape, SourceType.scraped, "Google News", db)
    return result

@router.post("/email",        response_model=ScrapeResult)
async def scrape_email(db: AsyncSession = Depends(get_db)):
    result, _ = await _run_scraper(email_parser.scrape, SourceType.email, "Email", db)
    return result
