from datetime import datetime
from sqlalchemy import String, Text, DateTime, Enum, Boolean, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base
import enum


class SourceType(str, enum.Enum):
    scraped = "scraped"
    rss = "rss"
    email = "email"
    manual = "manual"


class Status(str, enum.Enum):
    new = "new"
    reviewing = "reviewing"
    bidding = "bidding"
    submitted = "submitted"
    won = "won"
    lost = "lost"
    expired = "expired"


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    organization: Mapped[str] = mapped_column(String(300), nullable=False)
    sector: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    requirements: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType), default=SourceType.manual)
    source_url: Mapped[str | None] = mapped_column(String(1000))
    source_name: Mapped[str | None] = mapped_column(String(200))
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[Status] = mapped_column(Enum(Status), default=Status.new)
    is_travel_related: Mapped[bool] = mapped_column(Boolean, default=True)
    relevance_score: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    external_id: Mapped[str | None] = mapped_column(String(300), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AlertConfig(Base):
    __tablename__ = "alert_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(300), nullable=False)
    keywords: Mapped[str] = mapped_column(Text, default="travel,TMC,tour,airline,hotel,logistics")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
