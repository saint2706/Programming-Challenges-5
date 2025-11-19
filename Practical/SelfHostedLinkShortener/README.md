# Self-Hosted Link Shortener

A minimal FastAPI-based service for creating, managing, and tracking short URLs with SQLite persistence.

## Requirements

- Python 3.10+
- `fastapi`, `uvicorn`, `pydantic`

Install dependencies:

```bash
python -m pip install fastapi uvicorn "pydantic>=1.10" pytest
```

## Running the API

```bash
export SHORTENER_DB_PATH="$(pwd)/shortener.db"  # optional custom location
uvicorn Practical.SelfHostedLinkShortener.app:app --reload
```

The service exposes the following key endpoints:

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/links` | Create a short URL (optionally supply `custom_slug`). |
| `GET` | `/links` | List all known short links. |
| `GET` | `/links/{slug}` | Retrieve metadata about a short link. |
| `GET` | `/{slug}` | Redirect to the original URL while incrementing analytics. |
| `GET` | `/links/{slug}/stats` | Fetch hit counts and timestamps. |
| `DELETE` | `/links/{slug}` | Remove a short link. |

### Example payload

```json
{
  "url": "https://example.com/docs",
  "custom_slug": "docs"
}
```

### Redirects and analytics

- Visiting `/{slug}` issues an HTTP 307 redirect to the original URL and increments `hit_count`.
- `last_accessed_at` is updated every time a redirect occurs, enabling simple analytics.

## Running the tests

The test suite spins up the FastAPI TestClient and points the app at a temporary SQLite file.

```bash
pytest Practical/SelfHostedLinkShortener/tests -q
```

## Deployment notes

- The application is stateless aside from the SQLite database. For production use you can mount the `shortener.db` file on persistent storage or swap the `database.py` layer to target another RDBMS.
- Behind a reverse proxy (NGINX, Traefik, etc.), run with `uvicorn --host 0.0.0.0 --port 8000 Practical.SelfHostedLinkShortener.app:app`.
- Containerization is straightforward: copy the `Practical/SelfHostedLinkShortener` directory into an image, install the dependencies above, and set the default command to the uvicorn invocation.
