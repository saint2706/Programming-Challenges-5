"""Resume portfolio generator using Jinja2 templates and WeasyPrint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML


class ResumePortfolioGenerator:
    """Render resume/portfolio data into HTML and PDF outputs."""

    def __init__(self, template_dir: Path) -> None:
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def load_data(self, data_path: Path) -> Dict[str, Any]:
        data = json.loads(data_path.read_text(encoding="utf-8"))
        return data

    def render_html(
        self, data: Dict[str, Any], template_name: str = "resume.html"
    ) -> str:
        template = self.env.get_template(template_name)
        return template.render(data=data)

    def export_html(
        self,
        data: Dict[str, Any],
        output_path: Path,
        template_name: str = "resume.html",
    ) -> Path:
        html = self.render_html(data, template_name=template_name)
        output_path.write_text(html, encoding="utf-8")
        return output_path

    def export_pdf(
        self,
        data: Dict[str, Any],
        output_path: Path,
        template_name: str = "resume.html",
    ) -> Path:
        html = self.render_html(data, template_name=template_name)
        HTML(string=html, base_url=str(self.template_dir)).write_pdf(str(output_path))
        return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate resume HTML and PDF from JSON data."
    )
    parser.add_argument(
        "--data",
        required=True,
        type=Path,
        help="Path to JSON data matching data_schema.json.",
    )
    parser.add_argument(
        "--template",
        default="resume.html",
        help="Template filename in the templates directory (default: resume.html).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory to write generated files (default: ./output).",
    )
    parser.add_argument(
        "--html-name",
        default="resume.html",
        help="Filename for generated HTML output (default: resume.html).",
    )
    parser.add_argument(
        "--pdf-name",
        default="resume.pdf",
        help="Filename for generated PDF output (default: resume.pdf).",
    )
    parser.add_argument(
        "--skip-pdf",
        action="store_true",
        help="Only export HTML and skip generating a PDF.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generator = ResumePortfolioGenerator(
        template_dir=Path(__file__).parent / "templates"
    )

    data = generator.load_data(args.data)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    html_path = args.output_dir / args.html_name
    generator.export_html(data, html_path, template_name=args.template)

    if not args.skip_pdf:
        pdf_path = args.output_dir / args.pdf_name
        generator.export_pdf(data, pdf_path, template_name=args.template)

    print(f"Generated HTML at {html_path.resolve()}")
    if not args.skip_pdf:
        print(f"Generated PDF at {pdf_path.resolve()}")


if __name__ == "__main__":
    main()
