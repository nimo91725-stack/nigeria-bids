from datetime import datetime
from pydantic import BaseModel, HttpUrl
from typing import Optional
from .models import SourceType, Status


class OpportunityCreate(BaseModel):
    title: str
    organization: str
    sector: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    source_type: SourceType = SourceType.manual
    source_url: Optional[str] = None
    source_name: Optional[str] = None
    deadline: Optional[datetime] = None
    published_at: Optional[datetime] = None
    notes: Optional[str] = None


class OpportunityUpdate(BaseModel):
    title: Optional[str] = None
    organization: Optional[str] = None
    sector: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    deadline: Optional[datetime] = None
    status: Optional[Status] = None
    notes: Optional[str] = None


class OpportunityOut(BaseModel):
    id: int
    title: str
    organization: str
    sector: Optional[str]
    description: Optional[str]
    source_type: SourceType
    source_url: Optional[str]
    source_name: Optional[str]
    deadline: Optional[datetime]
    published_at: Optional[datetime]
    status: Status
    relevance_score: int
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AlertConfigCreate(BaseModel):
    email: str
    keywords: str = "travel,TMC,tour,airline,hotel,logistics"


class AlertConfigOut(AlertConfigCreate):
    id: int
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ScrapeResult(BaseModel):
    source: str
    new_count: int
    skipped_count: int
    error: Optional[str] = None
