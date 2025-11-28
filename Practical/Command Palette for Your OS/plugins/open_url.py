"""Open a URL in the default browser."""

import webbrowser
from urllib.parse import urlparse

METADATA = {
    "name": "Open URL",
    "description": "Open a URL or search term in the default browser",
    "keywords": ["web", "browser", "http"],
}


def _normalise(query: str) -> str:
    if not query:
        return "https://www.google.com"
    parsed = urlparse(query)
    if parsed.scheme:
        return query
    if "." in query:
        return "https://" + query
    return f"https://www.google.com/search?q={query}"


def execute(query: str) -> str:
    url = _normalise(query.strip())
    webbrowser.open(url)
    return f"Opening {url} in your browser"
