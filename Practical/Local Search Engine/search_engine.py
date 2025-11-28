"""CLI search engine for local files using Whoosh."""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import fnmatch
import importlib.util
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import yaml
from whoosh import index
from whoosh.fields import DATETIME, ID, TEXT, Schema
from whoosh.qparser import MultifieldParser, OrGroup


SUPPORTED_EXTENSIONS = {".txt", ".md", ".rtf", ".pdf", ".docx"}


@dataclass
class SearchConfig:
    """
    Docstring for SearchConfig.
    """
    roots: List[Path] = field(default_factory=lambda: [Path.cwd()])
    index_dir: Path = field(default_factory=lambda: Path.cwd() / ".local_index")
    ignored: List[str] = field(
        default_factory=lambda: ["**/.git/**", "**/__pycache__/**", "*.log", "*.tmp"]
    )
    max_workers: int = max(os.cpu_count() or 2, 2)
    snippet_length: int = 240
    use_tika: bool = False

    @classmethod
    def from_file(cls, path: Optional[Path]) -> "SearchConfig":
        """
        Docstring for from_file.
        """
        defaults = cls()
        if path is None:
            return defaults
        with open(path, "r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}
        return cls(
            roots=[Path(p) for p in loaded.get("roots", defaults.roots)],
            index_dir=Path(loaded.get("index_dir", defaults.index_dir)),
            ignored=loaded.get("ignored", defaults.ignored),
            max_workers=int(loaded.get("max_workers", defaults.max_workers)),
            snippet_length=int(loaded.get("snippet_length", defaults.snippet_length)),
            use_tika=bool(loaded.get("use_tika", defaults.use_tika)),
        )


def get_schema() -> Schema:
    """
    Docstring for get_schema.
    """
    return Schema(
        path=ID(stored=True, unique=True),
        modified=DATETIME(stored=True),
        content=TEXT(stored=True),
    )


def open_or_create_index(index_dir: Path) -> index.Index:
    """
    Docstring for open_or_create_index.
    """
    index_dir.mkdir(parents=True, exist_ok=True)
    if index.exists_in(index_dir):
        return index.open_dir(index_dir)
    return index.create_in(index_dir, schema=get_schema())


def collect_files(roots: Sequence[Path], ignored: Sequence[str]) -> List[Path]:
    """
    Docstring for collect_files.
    """
    files: List[Path] = []
    for root in roots:
        if not root.exists():
            logging.warning("Skipping missing root %s", root)
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirpath_path = Path(dirpath)
            dirnames[:] = [d for d in dirnames if not is_ignored(dirpath_path / d, ignored)]
            for name in filenames:
                path = dirpath_path / name
                if is_ignored(path, ignored):
                    continue
                if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    files.append(path)
    return files


def is_ignored(path: Path, patterns: Sequence[str]) -> bool:
    """
    Docstring for is_ignored.
    """
    return any(fnmatch.fnmatch(path.as_posix(), pattern) for pattern in patterns)


def extract_text(path: Path, use_tika: bool = False) -> str:
    """
    Docstring for extract_text.
    """
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".rtf"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        return extract_pdf_text(path, use_tika)
    if suffix == ".docx":
        return extract_docx_text(path)
    return ""


def extract_pdf_text(path: Path, use_tika: bool) -> str:
    """
    Docstring for extract_pdf_text.
    """
    pymupdf_available = importlib.util.find_spec("fitz") is not None
    if pymupdf_available:
        import fitz  # type: ignore

        try:
            text_parts = []
            with fitz.open(path) as doc:
                for page in doc:
                    text_parts.append(page.get_text())
            text = "\n".join(text_parts)
            if text.strip():
                return text
        except Exception as exc:  # noqa: BLE001
            logging.warning("PyMuPDF failed for %s: %s", path, exc)
            if not use_tika:
                return ""
    if use_tika:
        if importlib.util.find_spec("tika") is None:
            logging.error("Tika is not installed but 'use_tika' is enabled")
            return ""
        from tika import parser  # type: ignore

        try:
            parsed = parser.from_file(str(path))
            return (parsed.get("content") or "").strip()
        except Exception as exc:  # noqa: BLE001
            logging.error("Tika failed for %s: %s", path, exc)
    return ""


def extract_docx_text(path: Path) -> str:
    """
    Docstring for extract_docx_text.
    """
    if importlib.util.find_spec("docx") is None:
        logging.error("python-docx is not installed but a .docx file was encountered")
        return ""
    from docx import Document  # type: ignore

    try:
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as exc:  # noqa: BLE001
        logging.error("docx parsing failed for %s: %s", path, exc)
        return ""


def parse_file(args: Tuple[Path, bool]) -> Tuple[Path, str]:
    """
    Docstring for parse_file.
    """
    path, use_tika = args
    try:
        return path, extract_text(path, use_tika)
    except Exception as exc:  # noqa: BLE001
        logging.error("Failed to parse %s: %s", path, exc)
        return path, ""


def build_index(config: SearchConfig) -> None:
    """
    Docstring for build_index.
    """
    ix = open_or_create_index(config.index_dir)
    files = collect_files(config.roots, config.ignored)
    logging.info("Discovered %d files to index", len(files))
    with concurrent.futures.ProcessPoolExecutor(max_workers=config.max_workers) as executor:
        parsed = list(executor.map(parse_file, [(path, config.use_tika) for path in files]))
    with ix.writer(limitmb=512) as writer:
        for path, text in parsed:
            if not text.strip():
                continue
            writer.update_document(
                path=str(path),
                modified=dt.datetime.fromtimestamp(path.stat().st_mtime),
                content=text,
            )
    logging.info("Index built at %s", config.index_dir)


def read_index_state(ix: index.Index) -> Dict[str, dt.datetime]:
    """
    Docstring for read_index_state.
    """
    state: Dict[str, dt.datetime] = {}
    with ix.searcher() as searcher:
        for fields in searcher.all_stored_fields():
            state[fields["path"]] = fields["modified"]
    return state


def reindex(config: SearchConfig) -> None:
    """
    Docstring for reindex.
    """
    ix = open_or_create_index(config.index_dir)
    indexed = read_index_state(ix)
    to_process: List[Path] = []

    current_files = collect_files(config.roots, config.ignored)
    current_set = {str(p) for p in current_files}

    with ix.writer(limitmb=512) as writer:
        for indexed_path in indexed:
            if indexed_path not in current_set:
                writer.delete_by_term("path", indexed_path)
                logging.info("Removed missing file %s", indexed_path)

    for path in current_files:
        modified = dt.datetime.fromtimestamp(path.stat().st_mtime)
        stored_modified = indexed.get(str(path))
        if stored_modified is None or modified > stored_modified:
            to_process.append(path)

    logging.info("Reindexing %d updated files", len(to_process))
    if not to_process:
        return

    with concurrent.futures.ProcessPoolExecutor(max_workers=config.max_workers) as executor:
        parsed = list(executor.map(parse_file, [(path, config.use_tika) for path in to_process]))
    with ix.writer(limitmb=512) as writer:
        for path, text in parsed:
            if not text.strip():
                continue
            writer.update_document(
                path=str(path),
                modified=dt.datetime.fromtimestamp(path.stat().st_mtime),
                content=text,
            )


def search(config: SearchConfig, query_text: str, limit: int = 10) -> None:
    """
    Docstring for search.
    """
    ix = open_or_create_index(config.index_dir)
    parser = MultifieldParser(["content"], schema=ix.schema, group=OrGroup.factory(0.9))
    query = parser.parse(query_text)
    with ix.searcher() as searcher:
        results = searcher.search(query, limit=limit)
        results.fragmenter.charlimit = config.snippet_length
        for hit in results:
            snippet = hit.highlights("content")
            if not snippet:
                snippet = (hit.get("content", "") or "")[: config.snippet_length]
            print(f"\nPath: {hit['path']}")
            print(f"Modified: {hit['modified']}")
            print(f"Snippet: {snippet}")


def parse_args() -> argparse.Namespace:
    """
    Docstring for parse_args.
    """
    parser = argparse.ArgumentParser(description="Local search engine powered by Whoosh")
    parser.add_argument("command", choices=["index", "reindex", "search"], help="Action to perform")
    parser.add_argument("query", nargs="?", help="Query text for search")
    parser.add_argument("--config", type=Path, help="Path to YAML configuration file")
    parser.add_argument("--limit", type=int, default=10, help="Number of search results to return")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def main() -> None:
    """
    Docstring for main.
    """
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="[%(levelname)s] %(message)s")
    config = SearchConfig.from_file(args.config)

    if args.command == "index":
        build_index(config)
    elif args.command == "reindex":
        reindex(config)
    elif args.command == "search":
        if not args.query:
            raise SystemExit("A query string is required for search")
        search(config, args.query, limit=args.limit)


if __name__ == "__main__":
    main()
