# Markdown Search Knowledge Graph (Practical 16)

This Flask web app imports Markdown knowledge base files, indexes them into Elasticsearch for full-text search, and renders a D3.js visualization of cross-reference links between documents.

## Features

- Loads Markdown files from `knowledge_base/` and extracts their titles and cross-document links.
- Indexes content into Elasticsearch for multi-field full-text search.
- Displays search results with hyperlinks to the rendered Markdown documents and highlighted snippets.
- Serves a force-directed D3.js graph showing how Markdown files link to one another.

## Running locally

1. Install dependencies (consider using a virtual environment):
   ```bash
   pip install -r requirements.txt
   ```
2. Start Elasticsearch (Docker example):
   ```bash
   docker run -p 9200:9200 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:8.14.0
   ```
3. Launch the Flask app:
   ```bash
   export FLASK_APP=app.py
   export ELASTICSEARCH_URL=http://localhost:9200
   flask run --debug
   ```
4. Open `http://localhost:5000` to search and explore the graph.

The app automatically indexes Markdown files on startup. Add new `.md` files to `knowledge_base/` and restart the server to refresh both the index and graph.
