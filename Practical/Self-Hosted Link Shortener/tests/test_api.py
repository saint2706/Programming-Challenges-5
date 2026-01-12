import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from Practical.SelfHostedLinkShortener import database  # noqa: E402
from Practical.SelfHostedLinkShortener.app import app  # noqa: E402


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("SHORTENER_DB_PATH", str(db_path))
    # ensure a clean database for each test run
    database.initialize_db()
    with TestClient(app) as test_client:
        yield test_client


def test_create_and_follow_link(client):
    payload = {"url": "https://example.com"}
    resp = client.post("/links", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    slug = data["slug"]

    # follow redirect
    redirect_resp = client.get(f"/{slug}", follow_redirects=False)
    assert redirect_resp.status_code == 307
    assert redirect_resp.headers["location"].rstrip("/") == payload["url"].rstrip("/")

    stats = client.get(f"/links/{slug}/stats").json()
    assert stats["hit_count"] == 1
    assert stats["slug"] == slug


def test_custom_slug_validation(client):
    resp = client.post(
        "/links", json={"url": "https://example.com", "custom_slug": "??"}
    )
    assert resp.status_code == 422


def test_duplicate_slug(client):
    payload = {"url": "https://example.com/a", "custom_slug": "docs"}
    resp = client.post("/links", json=payload)
    assert resp.status_code == 201

    resp_dup = client.post(
        "/links", json={"url": "https://example.com/b", "custom_slug": "docs"}
    )
    assert resp_dup.status_code == 409
