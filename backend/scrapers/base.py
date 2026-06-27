from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ScrapedOpportunity:
    title: str
    organization: str
    source_name: str
    source_url: str
    external_id: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    published_at: Optional[datetime] = None
    sector: Optional[str] = None
