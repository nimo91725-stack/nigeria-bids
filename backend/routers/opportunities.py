from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, desc
from typing import Optional
from ..database import get_db
from ..models import Opportunity, Status
from ..schemas import OpportunityCreate, OpportunityUpdate, OpportunityOut

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.get("/", response_model=list[OpportunityOut])
async def list_opportunities(
    status: Optional[Status] = None,
    sector: Optional[str] = None,
    search: Optional[str] = None,
    min_score: int = Query(0, ge=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = select(Opportunity).order_by(desc(Opportunity.relevance_score), desc(Opportunity.created_at))
    if min_score > 0:
        q = q.where(Opportunity.relevance_score >= min_score)
    if status:
        q = q.where(Opportunity.status == status)
    if sector:
        q = q.where(Opportunity.sector == sector)
    if search:
        term = f"%{search}%"
        q = q.where(
            or_(
                Opportunity.title.ilike(term),
                Opportunity.organization.ilike(term),
                Opportunity.description.ilike(term),
            )
        )
    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/", response_model=OpportunityOut, status_code=201)
async def create_opportunity(data: OpportunityCreate, db: AsyncSession = Depends(get_db)):
    opp = Opportunity(**data.model_dump())
    opp.relevance_score = _score(opp)
    db.add(opp)
    await db.commit()
    await db.refresh(opp)
    return opp


@router.get("/{opp_id}", response_model=OpportunityOut)
async def get_opportunity(opp_id: int, db: AsyncSession = Depends(get_db)):
    opp = await db.get(Opportunity, opp_id)
    if not opp:
        raise HTTPException(404, "Opportunity not found")
    return opp


@router.patch("/{opp_id}", response_model=OpportunityOut)
async def update_opportunity(opp_id: int, data: OpportunityUpdate, db: AsyncSession = Depends(get_db)):
    opp = await db.get(Opportunity, opp_id)
    if not opp:
        raise HTTPException(404, "Opportunity not found")
    for field, val in data.model_dump(exclude_none=True).items():
        setattr(opp, field, val)
    await db.commit()
    await db.refresh(opp)
    return opp


@router.delete("/{opp_id}", status_code=204)
async def delete_opportunity(opp_id: int, db: AsyncSession = Depends(get_db)):
    opp = await db.get(Opportunity, opp_id)
    if not opp:
        raise HTTPException(404, "Opportunity not found")
    await db.delete(opp)
    await db.commit()


TRAVEL_KEYWORDS = [
    "travel", "tmc", "tour", "airline", "hotel", "accommodation",
    "flight", "logistics", "visa", "ticketing", "hospitality", "car hire",
]

def _score(opp: Opportunity) -> int:
    text = f"{opp.title} {opp.description or ''}".lower()
    return sum(10 for kw in TRAVEL_KEYWORDS if kw in text)
