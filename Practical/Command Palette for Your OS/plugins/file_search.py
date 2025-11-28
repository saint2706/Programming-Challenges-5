"""Search for files containing the query string."""
from pathlib import Path

METADATA = {
    "name": "Search Files",
    "description": "Find files in your home directory that match the query",
    "keywords": ["files", "search", "finder"],
}

DEFAULT_ROOTS = [Path.home() / "Documents", Path.home()]


def execute(query: str) -> str:
    """
    Docstring for execute.
    """
    query = query.strip()
    if not query:
        return "Type part of a filename to search."

    matches = []
    for root in DEFAULT_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if query.lower() in path.name.lower():
                matches.append(path)
            if len(matches) >= 15:
                break
        if len(matches) >= 15:
            break

    if not matches:
        return f"No files matching '{query}' were found in {', '.join(str(r) for r in DEFAULT_ROOTS)}."

    lines = ["Top matches:"]
    lines.extend(f"- {path}" for path in matches)
    return "\n".join(lines)
