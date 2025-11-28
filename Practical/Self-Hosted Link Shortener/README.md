# Self-Hosted Link Shortener

A minimal FastAPI-based service for creating, managing, and tracking short URLs with SQLite persistence.

## 📋 Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Running the API](#running-the-api)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Deployment](#deployment)

## 📋 Requirements

- Python 3.10+
- `fastapi`, `uvicorn`, `pydantic`

## 💻 Installation

Install dependencies:

```bash
python -m pip install fastapi uvicorn "pydantic>=1.10" pytest
```

## 🚀 Running the API

Start the development server:

```bash
# Optional: Set custom database path
export SHORTENER_DB_PATH="$(pwd)/shortener.db"

# Run via uvicorn
uvicorn Practical.SelfHostedLinkShortener.app:app --reload
```

The API will be available at `http://127.0.0.1:8000`.
Auto-generated docs are available at `http://127.0.0.1:8000/docs`.

## 📚 API Reference

| Method   | Path                  | Description                                                |
| :------- | :-------------------- | :--------------------------------------------------------- |
| `POST`   | `/links`              | Create a short URL (optionally supply `custom_slug`).      |
| `GET`    | `/links`              | List all known short links.                                |
| `GET`    | `/links/{slug}`       | Retrieve metadata about a short link.                      |
| `GET`    | `/{slug}`             | Redirect to the original URL while incrementing analytics. |
| `GET`    | `/links/{slug}/stats` | Fetch hit counts and timestamps.                           |
| `DELETE` | `/links/{slug}`       | Remove a short link.                                       |

### Example Creation Payload

```json
{
  "url": "https://example.com/docs",
  "custom_slug": "docs"
}
```

### Analytics

- Visiting `/{slug}` issues an HTTP 307 redirect to the original URL and increments `hit_count`.
- `last_accessed_at` is updated every time a redirect occurs.

## 🧪 Testing

The test suite spins up the FastAPI TestClient and points the app at a temporary SQLite file.

```bash
pytest Practical/SelfHostedLinkShortener/tests -q
```

## ☁️ Deployment

- **State**: The application is stateless aside from the SQLite database.
- **Persistence**: Mount the directory containing `shortener.db` to persistent storage.
- **Reverse Proxy**: Behind NGINX/Traefik, run with `uvicorn --host 0.0.0.0 --port 8000 Practical.SelfHostedLinkShortener.app:app`.
- **Container**: Copy the `Practical` directory into a Docker image, install dependencies, and set the default command to the uvicorn invocation.
