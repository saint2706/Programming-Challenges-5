# Practical / Document Template Filler

A small Python utility that loads structured data (JSON or YAML) and injects it
into Office and PDF templates. It demonstrates three flows:

1. Replace `{{placeholders}}` inside DOCX templates using **python-docx**.
2. Fill AcroForm fields in an existing PDF using **PyPDF2**.
3. Regenerate a data-driven PDF summary directly via **reportlab**.

## Project layout

```
Practical/Document Template Filler/
├── data/
│   ├── sample_data.json
│   └── sample_data.yaml
├── output/                # Generated files are written here (git-ignored)
├── templates/
│   ├── README.md                   # How to generate the templates
│   ├── letter_template.docx        # Generated DOCX with {{client_name}}, etc. (git-ignored)
│   └── service_form_template.pdf   # Generated PDF form for PyPDF2 (git-ignored)
├── template_filler.py     # CLI utility
└── requirements.txt       # Python dependencies
```

## Setup

1. Install dependencies

    ```bash
    pip install -r "Practical/Document Template Filler/requirements.txt"
    ```

2. Generate the sample templates (one-time)

    ```bash
    python "Practical/Document Template Filler/template_filler.py" --create-sample-templates
    ```

## CLI usage

Fill both the DOCX and PDF templates and generate a fresh summary PDF in one go:

```bash
python "Practical/Document Template Filler/template_filler.py" \
  --create-sample-templates \
  --data "Practical/Document Template Filler/data/sample_data.json" \
  --docx-template "Practical/Document Template Filler/templates/letter_template.docx" \
  --docx-output "Practical/Document Template Filler/output/filled_letter.docx" \
  --pdf-template "Practical/Document Template Filler/templates/service_form_template.pdf" \
  --pdf-output "Practical/Document Template Filler/output/filled_service_form.pdf" \
  --generated-pdf "Practical/Document Template Filler/output/service_summary.pdf"
```

You can also point `--data` to the YAML sample or your own file containing keys
like `client_name`, `service`, `appointment_date`, etc.

### Notes

- DOCX placeholders use double curly braces, e.g. `{{client_name}}`. The script
  rewrites paragraph text to catch placeholders even when Word splits them across
  multiple runs.
- The PDF template is generated with AcroForm fields that match the sample keys.
  PyPDF2 fills every page and keeps the fields editable.
- The generated summary PDF is created from scratch using reportlab so you can
  see a non-form option as well.
