"""FastAPI application powering a self-hosted link shortener."""
from __future__ import annotations

from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Path, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl, field_validator

from . import database
from .slugger import generate_slug, validate_custom_slug

app = FastAPI(title="Self-Hosted Link Shortener", version="1.0.0")


def _ensure_db() -> None:
    database.initialize_db()


class LinkCreate(BaseModel):
    url: HttpUrl
    custom_slug: Optional[str] = None

    @field_validator("custom_slug")
    @classmethod
    def validate_slug(cls, slug: Optional[str]) -> Optional[str]:
        if slug is None:
            return slug
        if not validate_custom_slug(slug):
            raise ValueError(
                "Slug must be 4-32 characters of letters, numbers, underscores or hyphens"
            )
        return slug


class LinkResponse(BaseModel):
    slug: str
    original_url: HttpUrl
    created_at: str
    hit_count: int
    last_accessed_at: Optional[str]


class StatsResponse(BaseModel):
    slug: str
    hit_count: int
    created_at: str
    last_accessed_at: Optional[str]


@app.post("/links", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def create_link(payload: LinkCreate, _: None = Depends(_ensure_db)) -> LinkResponse:
    slug = payload.custom_slug
    if slug:
        if database.slug_exists(slug):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already exists")
    else:
        attempt = 0
        slug = generate_slug(payload.url, attempt=attempt)
        while database.slug_exists(slug):
            attempt += 1
            slug = generate_slug(payload.url, attempt=attempt)

    record = database.create_link(slug=slug, url=str(payload.url))
    return LinkResponse(**record, last_accessed_at=None)


@app.get("/links", response_model=List[LinkResponse])
async def list_links(limit: Optional[int] = None, _: None = Depends(_ensure_db)) -> List[LinkResponse]:
    records = database.list_links(limit=limit)
    return [LinkResponse(**record) for record in records]


@app.get("/links/{slug}", response_model=LinkResponse)
async def get_link(slug: str = Path(..., min_length=4, max_length=32), _: None = Depends(_ensure_db)) -> LinkResponse:
    record = database.get_link(slug)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slug not found")
    return LinkResponse(**record)


@app.delete("/links/{slug}")
async def delete_link(slug: str, _: None = Depends(_ensure_db)) -> None:
    removed = database.delete_link(slug)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slug not found")


@app.get("/{slug}")
async def redirect(slug: str, _: None = Depends(_ensure_db)) -> RedirectResponse:
    record = database.get_link(slug)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slug not found")
    database.increment_hit(slug)
    return RedirectResponse(record["original_url"], status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@app.get("/links/{slug}/stats", response_model=StatsResponse)
async def stats(slug: str, _: None = Depends(_ensure_db)) -> StatsResponse:
    record = database.get_link(slug)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slug not found")
    return StatsResponse(**record)
