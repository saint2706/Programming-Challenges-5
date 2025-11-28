"""
Project implementation.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ApiError, ConnectionError, TransportError
from flask import Flask, abort, jsonify, render_template, request
from markdown import markdown


@dataclass
class MarkdownDocument:
    """A simple representation of a Markdown file."""

    identifier: str
    title: str
    content: str
    links: List[str]
    path: Path


BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
INDEX_NAME = os.environ.get("ES_INDEX", "markdown_docs")
ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")


def extract_links(markdown_text: str) -> List[str]:
    """Return links to Markdown files inside the document."""

    pattern = re.compile(r"\[[^\]]+\]\(([^)]+\.md)\)")
    return [match.group(1) for match in pattern.finditer(markdown_text)]


def extract_title(file_path: Path, markdown_text: str) -> str:
    """Use the first heading as the title, falling back to the filename."""

    for line in markdown_text.splitlines():
        if line.startswith("#"):
            return line.lstrip("# ").strip() or file_path.stem
    return file_path.stem


def load_documents() -> Dict[str, MarkdownDocument]:
    """Load Markdown documents into memory."""

    documents: Dict[str, MarkdownDocument] = {}
    for markdown_path in KNOWLEDGE_BASE_DIR.glob("*.md"):
        content = markdown_path.read_text(encoding="utf-8")
        identifier = markdown_path.name
        documents[identifier] = MarkdownDocument(
            identifier=identifier,
            title=extract_title(markdown_path, content),
            content=content,
            links=extract_links(content),
            path=markdown_path,
        )
    return documents


def get_elasticsearch_client() -> Elasticsearch:
    """
    Docstring for get_elasticsearch_client.
    """
    return Elasticsearch(ELASTICSEARCH_URL, request_timeout=10)


def ensure_index(client: Elasticsearch) -> None:
    """
    Docstring for ensure_index.
    """
    if client.indices.exists(index=INDEX_NAME):
        return

    mapping = {
        "mappings": {
            "properties": {
                "title": {"type": "text"},
                "content": {"type": "text"},
                "path": {"type": "keyword"},
            }
        }
    }
    client.indices.create(index=INDEX_NAME, **mapping)


def index_documents(client: Elasticsearch, documents: Dict[str, MarkdownDocument]) -> None:
    """
    Docstring for index_documents.
    """
    for document in documents.values():
        client.index(
            index=INDEX_NAME,
            id=document.identifier,
            document={
                "title": document.title,
                "content": document.content,
                "path": str(document.path),
            },
        )
    client.indices.refresh(index=INDEX_NAME)


def build_graph(documents: Dict[str, MarkdownDocument]) -> Dict[str, List[Dict[str, str]]]:
    """
    Docstring for build_graph.
    """
    nodes = [{"id": doc.identifier, "title": doc.title} for doc in documents.values()]
    node_ids = {doc.identifier for doc in documents.values()}

    edges: List[Dict[str, str]] = []
    for document in documents.values():
        for link in document.links:
            target = link if link in node_ids else None
            if target:
                edges.append({"source": document.identifier, "target": target})
    return {"nodes": nodes, "links": edges}


def create_app() -> Flask:
    """
    Docstring for create_app.
    """
    documents = load_documents()
    graph_data = build_graph(documents)

    app = Flask(__name__)
    app.config["documents"] = documents
    app.config["graph_data"] = graph_data

    try:
        es_client = get_elasticsearch_client()
        ensure_index(es_client)
        index_documents(es_client, documents)
        app.config["es_client"] = es_client
        app.config["search_available"] = True
    except (TransportError, ConnectionError, ApiError):
        app.config["es_client"] = None
        app.config["search_available"] = False

    @app.route("/")
    def home():
        """
        Docstring for home.
        """
        query = request.args.get("q")
        search_results = []
        search_error = None

        if query:
            client: Elasticsearch | None = app.config.get("es_client")
            if not client:
                search_error = "Elasticsearch is not available."
            else:
                try:
                    response = client.search(
                        index=INDEX_NAME,
                        query={"multi_match": {"query": query, "fields": ["title", "content"]}},
                        highlight={"fields": {"content": {}}},
                        size=10,
                    )
                    for hit in response["hits"]["hits"]:
                        search_results.append(
                            {
                                "id": hit["_id"],
                                "title": hit["_source"]["title"],
                                "score": hit["_score"],
                                "highlight": " ".join(hit.get("highlight", {}).get("content", [])).
                                replace("<em>", "<mark>").replace("</em>", "</mark>")
                                or None,
                            }
                        )
                except (TransportError, ConnectionError, ApiError) as exc:  # pragma: no cover - defensive
                    search_error = str(exc)

        return render_template(
            "index.html",
            documents=app.config["documents"],
            graph_data=app.config["graph_data"],
            results=search_results,
            query=query,
            search_error=search_error,
        )

    @app.route("/graph-data")
    def graph_data_endpoint():
        """
        Docstring for graph_data_endpoint.
        """
        return jsonify(app.config["graph_data"])

    @app.route("/document/<path:doc_id>")
    def show_document(doc_id: str):
        """
        Docstring for show_document.
        """
        documents: Dict[str, MarkdownDocument] = app.config["documents"]
        document = documents.get(doc_id)
        if not document:
            abort(404)

        html = markdown(document.content, extensions=["fenced_code", "tables"])
        return render_template("document.html", document=document, html=html)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
