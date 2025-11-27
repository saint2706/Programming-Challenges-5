# Email Newsletter Engine

A practical script for sending personalized HTML newsletters. Subscriber data is loaded from YAML or JSON files, merged into a Jinja2 template, and sent in batches via SMTP with logging, unsubscribe handling, and optional scheduling hooks.

## Requirements
- Python 3.9+
- See `requirements.txt`

Install dependencies:
```bash
pip install -r "Practical/Email Newsletter Engine/requirements.txt"
```

## Configuration
Campaign settings are defined in a YAML or JSON file. See `config.sample.yaml` for a complete example:

```yaml
sender: "News Bot <newsletter@example.com>"
subject: "Weekly Highlights"
template_path: "Practical/Email Newsletter Engine/templates/newsletter.html"
subscribers_path: "Practical/Email Newsletter Engine/subscribers.sample.yaml"
batch_size: 100
delay_between_batches: 1
unsubscribe_key: "unsubscribe"
default_context:
  company: "Example Corp"
  unsubscribe_url: "https://example.com/unsubscribe"
smtp:
  host: "smtp.example.com"
  port: 587
  username: "smtp-user"
  password: "smtp-password"
  use_tls: true
```

Subscriber data can be provided as either a list or under a `subscribers` key. YAML and JSON samples are provided in `subscribers.sample.yaml` and `subscribers.sample.json`.
Example JSON subscriber entry:

```json
[
  {
    "email": "user@example.com",
    "name": "User",
    "preferences": {"topics": ["product"], "unsubscribe": false}
  }
]
```

## Templates
Templates live alongside the campaign config. The default sample uses `templates/newsletter.html` and exposes the subscriber fields and `default_context` values to Jinja2. A `now()` helper is also available for timestamps.

## Usage
Run the campaign immediately:
```bash
python "Practical/Email Newsletter Engine/newsletter_engine.py" --config "Practical/Email Newsletter Engine/config.sample.yaml"
```

Schedule delivery for a future time (ISO 8601):
```bash
python "Practical/Email Newsletter Engine/newsletter_engine.py" \
  --config "Practical/Email Newsletter Engine/config.sample.yaml" \
  --schedule "2024-01-01T09:00:00"
```

Adjust logging verbosity with `--log-level DEBUG` to see SMTP steps and filtering decisions.

## Features
- YAML/JSON configuration and subscriber loading
- Jinja2 HTML rendering with per-recipient context
- SMTP delivery with TLS support
- Batch sending with optional delays
- Unsubscribe skipping via a configurable preference key
- Logging for processing, delivery, and filtering
- Lightweight scheduling hook using `threading.Timer`
