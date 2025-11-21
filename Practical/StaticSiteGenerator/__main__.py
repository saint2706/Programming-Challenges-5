"""
Static Site Generator

Builds a static website from Markdown files and Jinja2 templates.
"""

import argparse
import os
import shutil
import logging
from typing import Dict, Any, List
import markdown
from jinja2 import Environment, FileSystemLoader

logging.basicConfig(level=logging.INFO, format='%(message)s')

class StaticSiteGenerator:
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.content_dir = os.path.join(input_dir, 'content')
        self.templates_dir = os.path.join(input_dir, 'templates')
        self.static_dir = os.path.join(input_dir, 'static')

        if not os.path.exists(self.templates_dir):
            raise FileNotFoundError(f"Templates directory not found: {self.templates_dir}")

        self.env = Environment(loader=FileSystemLoader(self.templates_dir))
        self.md = markdown.Markdown(extensions=['meta', 'fenced_code'])
        self.posts: List[Dict[str, Any]] = []

    def clean_output(self):
        """Remove existing output directory."""
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
        os.makedirs(self.output_dir)

    def copy_static(self):
        """Copy static assets."""
        if os.path.exists(self.static_dir):
            dest = os.path.join(self.output_dir, 'static')
            shutil.copytree(self.static_dir, dest)
            logging.info(f"Copied static assets to {dest}")

    def parse_file(self, filepath: str) -> Dict[str, Any]:
        """Parse a markdown file and return metadata and html."""
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()

        self.md.reset()
        html_content = self.md.convert(text)
        meta = self.md.Meta # type: ignore

        # Flatten meta lists (markdown returns values as lists)
        flat_meta = {k: v[0] if len(v) == 1 else v for k, v in meta.items()}

        return {
            'content': html_content,
            'meta': flat_meta,
            'filename': os.path.basename(filepath),
            'rel_path': os.path.relpath(filepath, self.content_dir)
        }

    def build(self):
        """Main build process."""
        self.clean_output()
        self.copy_static()

        # Walk through content directory
        for root, _, files in os.walk(self.content_dir):
            for file in files:
                if file.endswith('.md'):
                    filepath = os.path.join(root, file)
                    data = self.parse_file(filepath)
                    self.posts.append(data)

        # Sort posts by date if available
        self.posts.sort(key=lambda x: x['meta'].get('date', ''), reverse=True)

        # Render pages
        for post in self.posts:
            self.render_post(post)

        # Render index/home page if a template exists
        self.render_index()

        logging.info(f"Successfully built {len(self.posts)} pages.")

    def render_post(self, post: Dict[str, Any]):
        """Render a single post."""
        template_name = post['meta'].get('template', 'post.html')
        try:
            template = self.env.get_template(template_name)
        except Exception:
             logging.warning(f"Template {template_name} not found, falling back to base.html or skipping.")
             return

        output_html = template.render(post=post, site_title="My Static Site")

        # Determine output path (convert .md path to .html path)
        rel_path = post['rel_path']
        html_path = os.path.splitext(rel_path)[0] + '.html'
        out_path = os.path.join(self.output_dir, html_path)

        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(output_html)
        logging.info(f"Generated {out_path}")

    def render_index(self):
        """Render the homepage listing all posts."""
        try:
            template = self.env.get_template('index.html')
            output_html = template.render(posts=self.posts, site_title="My Static Site")
            out_path = os.path.join(self.output_dir, 'index.html')
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(output_html)
            logging.info("Generated index.html")
        except Exception:
            logging.info("No index.html template found, skipping homepage generation.")

def main():
    parser = argparse.ArgumentParser(description="Static Site Generator")
    parser.add_argument("--input", required=True, help="Input directory containing content/, templates/, and static/")
    parser.add_argument("--output", required=True, help="Output directory for the built site")

    args = parser.parse_args()

    try:
        generator = StaticSiteGenerator(args.input, args.output)
        generator.build()
    except Exception as e:
        logging.error(f"Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
