"""Pydantic schemas for request/response payloads."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl, field_validator


class PageViewCreate(BaseModel):
    url: HttpUrl
    referrer: Optional[HttpUrl] = None
    timestamp: Optional[datetime] = None
    user_agent: Optional[str] = None

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_be_timezone_aware(
        cls, value: Optional[datetime]
    ) -> Optional[datetime]:
        if value and value.tzinfo is None:
            raise ValueError(
                "timestamp must include timezone information (ISO8601 with offset)"
            )
        return value


class PageViewOut(BaseModel):
    id: int
    url: HttpUrl
    referrer: Optional[HttpUrl] = None
    timestamp: datetime
    user_agent: Optional[str] = None

    class Config:
        from_attributes = True
