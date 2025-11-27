"""SQLAlchemy models for analytics events."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String

from .db import Base


class PageView(Base):
    __tablename__ = "pageviews"

    id: int = Column(Integer, primary_key=True, index=True)
    url: str = Column(String, nullable=False, index=True)
    referrer: Optional[str] = Column(String, nullable=True)
    user_agent: Optional[str] = Column(String, nullable=True)
    timestamp: datetime = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
