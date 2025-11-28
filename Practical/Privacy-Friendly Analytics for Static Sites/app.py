"""FastAPI app for recording privacy-friendly page views."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import FastAPI, Header, Request, Response
from fastapi.middleware.cors import CORSMiddleware

if __package__:
    from .db import Base, engine, get_session
    from .models import PageView
    from .rate_limit import RateLimiter, get_client_ip, is_bot_user_agent
    from .schemas import PageViewCreate, PageViewOut
else:  # Enable running as a script despite spaces in folder name
    sys.path.append(os.path.dirname(__file__))
    from db import Base, engine, get_session  # type: ignore
    from models import PageView  # type: ignore
    from rate_limit import RateLimiter, get_client_ip, is_bot_user_agent  # type: ignore
    from schemas import PageViewCreate, PageViewOut  # type: ignore

app = FastAPI(title="Privacy-Friendly Analytics")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

rate_limiter = RateLimiter(limit=120, window_seconds=60)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


def store_pageview(
    payload: PageViewCreate, user_agent: str | None, request: Request
) -> Optional[PageView]:
    client_ip = get_client_ip(request)
    rate_limiter.touch(client_ip)

    ua = payload.user_agent or user_agent
    if is_bot_user_agent(ua):
        return None  # type: ignore[return-value]

    aware_timestamp = payload.timestamp or datetime.now(timezone.utc)
    utc_timestamp = aware_timestamp.astimezone(timezone.utc).replace(tzinfo=None)

    with get_session() as session:
        pageview = PageView(
            url=str(payload.url),
            referrer=str(payload.referrer) if payload.referrer else None,
            timestamp=utc_timestamp,
            user_agent=ua,
        )
        session.add(pageview)
        session.flush()
        session.refresh(pageview)
        return pageview


@app.post("/pageviews", response_model=PageViewOut, status_code=201)
async def record_pageview(
    payload: PageViewCreate,
    request: Request,
    response: Response,
    user_agent: Annotated[
        str | None, Header(default=None, convert_underscores=False)
    ] = None,
):
    pageview = store_pageview(payload, user_agent, request)
    if pageview is None:
        response.status_code = 204
        return None
    return pageview


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
