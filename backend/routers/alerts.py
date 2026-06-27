from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import AlertConfig
from ..schemas import AlertConfigCreate, AlertConfigOut

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/", response_model=list[AlertConfigOut])
async def list_alerts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AlertConfig))
    return result.scalars().all()


@router.post("/", response_model=AlertConfigOut, status_code=201)
async def create_alert(data: AlertConfigCreate, db: AsyncSession = Depends(get_db)):
    alert = AlertConfig(**data.model_dump())
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    alert = await db.get(AlertConfig, alert_id)
    if alert:
        await db.delete(alert)
        await db.commit()
