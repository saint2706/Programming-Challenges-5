"""Configuration helpers for the notification hub."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:  # Optional dependency
    import yaml
except ImportError:  # pragma: no cover - handled gracefully at runtime
    yaml = None


@dataclass
class ProviderConfig:
    """Configuration for a single notification provider."""

    name: str
    options: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class NotificationSettings:
    """Top-level configuration for the notification hub."""

    providers: List[ProviderConfig] = field(default_factory=list)
    plugins_dir: Optional[Path] = None
    entry_point_group: str = "notification_providers"

    @classmethod
    def from_mapping(cls, data: Dict[str, Any]) -> "NotificationSettings":
        """
        Docstring for from_mapping.
        """
        provider_configs = [
            ProviderConfig(
                name=item.get("name", ""),
                options=item.get("options", {}),
                enabled=item.get("enabled", True),
            )
            for item in data.get("providers", [])
        ]
        plugins_dir = data.get("plugins_dir")
        return cls(
            providers=provider_configs,
            plugins_dir=Path(plugins_dir) if plugins_dir else None,
            entry_point_group=data.get("entry_point_group", "notification_providers"),
        )


def load_settings(path: Path | str) -> NotificationSettings:
    """
    Load notification settings from a JSON or YAML file.

    Args:
        path: Path to a JSON/YAML file.
    """

    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("PyYAML is required to parse YAML configuration files.")
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)

    if not isinstance(data, dict):
        raise ValueError("Configuration file must contain a mapping at the top level.")

    return NotificationSettings.from_mapping(data)


def providers_from_settings(settings: NotificationSettings) -> Iterable[ProviderConfig]:
    """Iterate over enabled providers in the configuration."""

    return (provider for provider in settings.providers if provider.enabled)
