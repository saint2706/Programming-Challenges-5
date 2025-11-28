"""Email Newsletter Engine

Reads subscriber data from YAML/JSON, personalizes Jinja2 templates, and sends batched emails
via SMTP. Includes logging, unsubscribe skipping, and optional scheduling hooks.
"""
from __future__ import annotations

import argparse
import json
import logging
import smtplib
import ssl
import time
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from threading import Timer
from typing import Any, Dict, Iterable, List

import yaml
from jinja2 import Environment, FileSystemLoader, Template


@dataclass
class SMTPConfig:
    """
    Docstring for SMTPConfig.
    """
    host: str
    port: int
    username: str
    password: str
    use_tls: bool = True


@dataclass
class CampaignConfig:
    """
    Docstring for CampaignConfig.
    """
    sender: str
    subject: str
    template_path: Path
    subscribers_path: Path
    smtp: SMTPConfig
    batch_size: int = 50
    delay_between_batches: float = 0
    unsubscribe_key: str = "unsubscribe"
    default_context: Dict[str, Any] = field(default_factory=dict)


class NewsletterEngine:
    """
    Docstring for NewsletterEngine.
    """
    def __init__(self, config: CampaignConfig) -> None:
        """
        Docstring for __init__.
        """
        self.config = config
        self.logger = logging.getLogger("newsletter_engine")
        self.template_env = Environment(loader=FileSystemLoader(config.template_path.parent))
        self.template_env.globals.update({"now": datetime.now})
        self.template: Template = self.template_env.get_template(config.template_path.name)

    def load_subscribers(self) -> List[Dict[str, Any]]:
        """
        Docstring for load_subscribers.
        """
        data = load_yaml_or_json(self.config.subscribers_path)
        subscribers = data.get("subscribers", data) if isinstance(data, dict) else data
        if not isinstance(subscribers, list):
            raise ValueError("Subscriber data must be a list or contain a 'subscribers' list")
        cleaned: List[Dict[str, Any]] = []
        for subscriber in subscribers:
            if not isinstance(subscriber, dict):
                self.logger.warning("Skipping malformed subscriber entry: %s", subscriber)
                continue
            email = subscriber.get("email")
            if not email:
                self.logger.warning("Skipping subscriber without email: %s", subscriber)
                continue
            preferences = subscriber.get("preferences", {}) or {}
            if preferences.get(self.config.unsubscribe_key, False):
                self.logger.info("Skipping unsubscribed recipient: %s", email)
                continue
            cleaned.append(subscriber)
        self.logger.info("Prepared %s subscribers for sending", len(cleaned))
        return cleaned

    def render_email(self, subscriber: Dict[str, Any]) -> str:
        """
        Docstring for render_email.
        """
        context = {**self.config.default_context, **subscriber}
        context.setdefault("subject", self.config.subject)
        return self.template.render(context)

    def send_batch(self, subscribers: Iterable[Dict[str, Any]]) -> None:
        """
        Docstring for send_batch.
        """
        for subscriber in subscribers:
            html = self.render_email(subscriber)
            self.send_email(subscriber["email"], html)

    def send_email(self, recipient: str, html_body: str) -> None:
        """
        Docstring for send_email.
        """
        message = MIMEMultipart("alternative")
        message["Subject"] = self.config.subject
        message["From"] = self.config.sender
        message["To"] = recipient
        message.attach(MIMEText(html_body, "html"))

        context = ssl.create_default_context()
        self.logger.debug("Connecting to SMTP server %s:%s", self.config.smtp.host, self.config.smtp.port)
        with smtplib.SMTP(self.config.smtp.host, self.config.smtp.port) as server:
            if self.config.smtp.use_tls:
                server.starttls(context=context)
            server.login(self.config.smtp.username, self.config.smtp.password)
            server.sendmail(self.config.sender, recipient, message.as_string())
            self.logger.info("Sent newsletter to %s", recipient)

    def send_campaign(self) -> None:
        """
        Docstring for send_campaign.
        """
        subscribers = self.load_subscribers()
        for i in range(0, len(subscribers), self.config.batch_size):
            batch = subscribers[i : i + self.config.batch_size]
            self.logger.info("Sending batch %s-%s", i + 1, i + len(batch))
            self.send_batch(batch)
            if self.config.delay_between_batches and i + len(batch) < len(subscribers):
                self.logger.info(
                    "Waiting %s seconds before next batch", self.config.delay_between_batches
                )
                time.sleep(self.config.delay_between_batches)

    def schedule_campaign(self, start_time: datetime) -> Timer:
        """
        Docstring for schedule_campaign.
        """
        delay = max(0, (start_time - datetime.now()).total_seconds())
        self.logger.info("Scheduling campaign in %s seconds", delay)
        timer = Timer(delay, self.send_campaign)
        timer.start()
        return timer


def load_yaml_or_json(path: Path) -> Any:
    """
    Docstring for load_yaml_or_json.
    """
    with open(path, "r", encoding="utf-8") as file:
        if path.suffix.lower() in {".yaml", ".yml"}:
            return yaml.safe_load(file)
        if path.suffix.lower() == ".json":
            return json.load(file)
        raise ValueError(f"Unsupported file format for {path}")


def setup_logging(level: str = "INFO") -> None:
    """
    Docstring for setup_logging.
    """
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def parse_args() -> argparse.Namespace:
    """
    Docstring for parse_args.
    """
    parser = argparse.ArgumentParser(description="Send personalized newsletters")
    parser.add_argument("--config", type=Path, required=True, help="Path to campaign config YAML/JSON")
    parser.add_argument("--log-level", default="INFO", help="Logging level (INFO, DEBUG, etc.)")
    parser.add_argument(
        "--schedule",
        type=str,
        help="Optional start time in ISO format (e.g., 2024-01-01T09:00:00)",
    )
    return parser.parse_args()


def build_config(config_path: Path) -> CampaignConfig:
    """
    Docstring for build_config.
    """
    raw = load_yaml_or_json(config_path)
    smtp_raw = raw.get("smtp")
    if not smtp_raw:
        raise ValueError("SMTP configuration required under 'smtp'")
    smtp_config = SMTPConfig(
        host=smtp_raw["host"],
        port=int(smtp_raw.get("port", 587)),
        username=smtp_raw["username"],
        password=smtp_raw["password"],
        use_tls=bool(smtp_raw.get("use_tls", True)),
    )
    template_path = Path(raw["template_path"])
    subscribers_path = Path(raw["subscribers_path"])
    return CampaignConfig(
        sender=raw["sender"],
        subject=raw["subject"],
        template_path=template_path,
        subscribers_path=subscribers_path,
        smtp=smtp_config,
        batch_size=int(raw.get("batch_size", 50)),
        delay_between_batches=float(raw.get("delay_between_batches", 0)),
        unsubscribe_key=str(raw.get("unsubscribe_key", "unsubscribe")),
        default_context=raw.get("default_context", {}),
    )


def main() -> None:
    """
    Docstring for main.
    """
    args = parse_args()
    setup_logging(args.log_level)
    config = build_config(args.config)
    engine = NewsletterEngine(config)
    if args.schedule:
        start_time = datetime.fromisoformat(args.schedule)
        engine.schedule_campaign(start_time)
    else:
        engine.send_campaign()


if __name__ == "__main__":
    main()
