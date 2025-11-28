# Privacy-Friendly Analytics for Static Sites

A lightweight FastAPI service that records page views (URL, referrer, timestamp, and user agent) without cookies. It includes a CLI for aggregating hits per page and date plus a CORS-friendly beacon snippet for static sites.

## Quick start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API
env ANALYTICS_DATABASE_URL="sqlite:///analytics.db" \
  uvicorn app:app --app-dir "Practical/Privacy-Friendly Analytics for Static Sites" \
  --host 0.0.0.0 --port 8000 --reload
```

The server creates the SQLite schema automatically on startup.

## API

### `POST /pageviews`

Payload (JSON):

```json
{
  "url": "https://example.com/posts/welcome",
  "referrer": "https://news.ycombinator.com/",
  "timestamp": "2024-01-01T12:00:00Z",
  "user_agent": "Mozilla/5.0 ..."
}
```

- `timestamp` is optional; when omitted, the server stores the current time in UTC.
- Requests with obvious bot user agents (`bot`, `spider`, `crawl`, `slurp`, `mediapartners-google`) return `204 No Content` without recording.
- A best-effort rate limit rejects clients exceeding 120 requests per minute per IP with HTTP 429.

### `GET /health`

Health probe returning `{ "status": "ok" }`.

## Beacon snippet (no cookies)

Use the provided [`beacon-snippet.js`](./beacon-snippet.js) or inline the following:

```html
<script>
  (function () {
    const endpoint = 'https://your-domain.example.com/pageviews';
    const payload = {
      url: window.location.href,
      referrer: document.referrer || null,
      timestamp: new Date().toISOString(),
      user_agent: navigator.userAgent,
    };

    const body = JSON.stringify(payload);

    if (navigator.sendBeacon) {
      const blob = new Blob([body], { type: 'application/json' });
      navigator.sendBeacon(endpoint, blob);
    } else {
      fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body,
        credentials: 'omit',
        cache: 'no-store',
        keepalive: true,
        mode: 'cors',
      }).catch(() => {});
    }
  })();
</script>
```

The API allows CORS requests from any origin and does not depend on cookies.

## CLI report

Aggregate page views by day and URL:

```bash
python "Practical/Privacy-Friendly Analytics for Static Sites/cli_report.py" \
  --start-date 2024-01-01 --end-date 2024-01-31
```

Output format:

```
Using database at sqlite:///analytics.db
Day         | Count | URL
------------+-------+------------------------------------------
2024-01-31 |     42 | https://example.com/
```

## Deployment notes

- The service runs with `uvicorn` as shown above; set `ANALYTICS_DATABASE_URL` to move beyond the default `analytics.db` file.
- For containerization, create a simple `Dockerfile` that installs `requirements.txt`, copies this folder, and starts `uvicorn app:app --app-dir "Practical/Privacy-Friendly Analytics for Static Sites" --host 0.0.0.0 --port 8000`.
- When deploying behind a reverse proxy, pass `X-Forwarded-For` so the rate limiter uses client IPs.
- SQLite works for small sites; switch to Postgres/MySQL by changing `ANALYTICS_DATABASE_URL`.

## Database migrations

Schema is defined in [`models.py`](./models.py) and created on startup. When changing models, bump the schema by rerunning the app or the CLI, which both call `Base.metadata.create_all(...)`.
