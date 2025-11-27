# Resume Portfolio Generator

Generate resume-style HTML and PDF files from structured JSON data using Jinja2 templates and WeasyPrint.

## Contents
- `data_schema.json`: JSON Schema describing required data fields.
- `example_data.json`: Sample data to render a portfolio.
- `generator.py`: CLI utility and helper class to render templates.
- `templates/`: Jinja2 HTML and CSS assets (default `resume.html` and `style.css`).

## Usage
1. Install dependencies:
   ```bash
   pip install jinja2 weasyprint
   ```
2. Generate HTML and PDF using the example data:
   ```bash
   python generator.py --data example_data.json
   ```
   Outputs are written to `./output/resume.html` and `./output/resume.pdf` by default.
3. Customize template or filenames:
   ```bash
   python generator.py --data my_resume.json \
     --template resume.html \
     --output-dir build \
     --html-name portfolio.html \
     --pdf-name portfolio.pdf
   ```
4. To only render HTML:
   ```bash
   python generator.py --data example_data.json --skip-pdf
   ```

Place additional Jinja2 templates in the `templates/` directory and reference them via `--template`.
