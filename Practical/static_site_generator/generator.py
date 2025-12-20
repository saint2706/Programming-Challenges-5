"""Core logic for the Static Site Generator."""

import os
import shutil
from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape


class SiteGenerator:
    def __init__(self, input_dir: Path, output_dir: Path, base_url: str = "/"):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.base_url = base_url
        self.content_dir = input_dir / "content"
        self.templates_dir = input_dir / "templates"
        self.static_dir = input_dir / "static"

        if not self.templates_dir.exists():
            raise FileNotFoundError(
                f"Templates directory not found: {self.templates_dir}"
            )

        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def build(self):
        # Clean output
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True)

        # Copy static
        if self.static_dir.exists():
            shutil.copytree(self.static_dir, self.output_dir / "static")

        # Process content
        if not self.content_dir.exists():
            print(f"Warning: Content directory not found: {self.content_dir}")
            return

        for root, _, files in os.walk(self.content_dir):
            for file in files:
                if file.endswith(".md"):
                    self._process_file(Path(root) / file)

    def _process_file(self, file_path: Path):
        rel_path = file_path.relative_to(self.content_dir)
        output_path = self.output_dir / rel_path.with_suffix(".html")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        content = file_path.read_text(encoding="utf-8")

        # Simple frontmatter parsing
        meta = {}
        body = content
        if content.startswith("---\n"):
            parts = content.split("---\n", 2)
            if len(parts) >= 3:
                frontmatter = parts[1]
                body = parts[2]
                for line in frontmatter.splitlines():
                    if ":" in line:
                        key, value = line.split(":", 1)
                        meta[key.strip()] = value.strip()

        html_content = markdown.markdown(body)

        template_name = meta.get("template", "base.html")
        try:
            template = self.env.get_template(template_name)
            render = template.render(
                content=html_content, meta=meta, base_url=self.base_url
            )
            output_path.write_text(render, encoding="utf-8")
        except Exception as e:
            print(f"Error rendering {file_path}: {e}")
