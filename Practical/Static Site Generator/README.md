# Static Site Generator

A simple static site generator that converts Markdown content to HTML using Jinja2 templates.

## Requirements
* Python 3.8+
* `markdown`
* `jinja2`

## Installation
```bash
pip install -r requirements.txt
```

## Directory Structure
Your input directory must look like this:
```
my_site/
├── content/       # Markdown files (.md)
├── templates/     # Jinja2 templates (.html)
└── static/        # CSS, JS, Images (optional)
```

## Usage
```bash
python -m Practical.StaticSiteGenerator --input ./my_site --output ./dist
```

## Metadata
The generator supports Markdown frontmatter (headers).
```markdown
title: My Post
date: 2023-10-27
template: post.html
---
# Content starts here
```
