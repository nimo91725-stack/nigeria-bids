from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import Opportunity, AlertConfig, SourceType
from ..schemas import ScrapeResult
from ..scrapers import bpp, tenderboard, ungm, email_parser
from ..scrapers.base import ScrapedOpportunity
from ..notifications import send_daily_alerts
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scrape", tags=["scraper"])


async def _upsert_opportunity(db: AsyncSession, item: ScrapedOpportunity, source_type: SourceType) -> Opportunity | None:
    """Insert opportunity if not already known. Returns the new Opportunity or None if duplicate."""
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
        # Refresh so IDs and timestamps are populated
        for opp in new_opps:
            await db.refresh(opp)
        return ScrapeResult(source=source_label, new_count=len(new_opps), skipped_count=skipped), new_opps
    except Exception as exc:
        logger.error(f"Scraper {source_label} failed: {exc}")
        return ScrapeResult(source=source_label, new_count=0, skipped_count=0, error=str(exc)), []


@router.post("/all", response_model=list[ScrapeResult])
async def scrape_all(db: AsyncSession = Depends(get_db)):
    """Trigger all scrapers, save new opportunities, then send alert emails."""
    scrapers = [
        (bpp.scrape, SourceType.scraped, "BPP Nigeria"),
        (tenderboard.scrape, SourceType.rss, "Tenderboard.ng"),
        (ungm.scrape, SourceType.rss, "UNGM"),
        (email_parser.scrape, SourceType.email, "Email"),
    ]

    results = []
    all_new: list[Opportunity] = []
    for fn, stype, label in scrapers:
        result, new_opps = await _run_scraper(fn, stype, label, db)
        results.append(result)
        all_new.extend(new_opps)

    # Send email alerts for all newly found opportunities
    if all_new:
        alert_configs_result = await db.execute(select(AlertConfig).where(AlertConfig.active == True))
        alert_configs = alert_configs_result.scalars().all()
        alert_summary = await send_daily_alerts(all_new, alert_configs)
        logger.info(f"Alerts: {alert_summary['sent']} sent, {alert_summary['skipped']} skipped")

    return results


@router.post("/bpp", response_model=ScrapeResult)
async def scrape_bpp(db: AsyncSession = Depends(get_db)):
    result, _ = await _run_scraper(bpp.scrape, SourceType.scraped, "BPP Nigeria", db)
    return result


@router.post("/tenderboard", response_model=ScrapeResult)
async def scrape_tenderboard(db: AsyncSession = Depends(get_db)):
    result, _ = await _run_scraper(tenderboard.scrape, SourceType.rss, "Tenderboard.ng", db)
    return result


@router.post("/ungm", response_model=ScrapeResult)
async def scrape_ungm(db: AsyncSession = Depends(get_db)):
    result, _ = await _run_scraper(ungm.scrape, SourceType.rss, "UNGM", db)
    return result


@router.post("/email", response_model=ScrapeResult)
async def scrape_email(db: AsyncSession = Depends(get_db)):
    result, _ = await _run_scraper(email_parser.scrape, SourceType.email, "Email", db)
    return result
