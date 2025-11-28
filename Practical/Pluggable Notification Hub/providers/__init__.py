"""Provider discovery and initialization."""

from __future__ import annotations

import importlib
import importlib.metadata
import pkgutil
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Type

from .base import NotificationProvider
from .email import EmailProvider
from .slack import SlackProvider
from .sms import SMSProvider

BUILTIN_PROVIDERS: Dict[str, Type[NotificationProvider]] = {
    "email": EmailProvider,
    "slack": SlackProvider,
    "sms": SMSProvider,
}


def discover_builtin_plugins() -> MutableMapping[str, Type[NotificationProvider]]:
    """Return a registry of built-in providers."""

    return dict(BUILTIN_PROVIDERS)


def discover_entry_points(
    group: str,
) -> MutableMapping[str, Type[NotificationProvider]]:
    """Discover providers exposed via Python entry points."""

    registry: MutableMapping[str, Type[NotificationProvider]] = {}
    for entry_point in importlib.metadata.entry_points().select(group=group):  # type: ignore[attr-defined]
        provider_class = entry_point.load()
        if isinstance(provider_class, type) and issubclass(
            provider_class, NotificationProvider
        ):
            registry[entry_point.name] = provider_class
    return registry


def discover_plugins_directory(
    plugins_dir: Path | None,
) -> MutableMapping[str, Type[NotificationProvider]]:
    """
    Dynamically load provider modules from a plugins directory.

    The directory should contain Python files that define a subclass of
    :class:`NotificationProvider` and expose it via a ``provider`` variable.
    """

    registry: MutableMapping[str, Type[NotificationProvider]] = {}
    if not plugins_dir:
        return registry

    plugin_path = str(plugins_dir)
    sys.path.insert(0, plugin_path)
    try:
        for module_info in pkgutil.iter_modules([plugin_path]):
            module = importlib.import_module(module_info.name)
            provider_class = getattr(module, "provider", None)
            if isinstance(provider_class, type) and issubclass(
                provider_class, NotificationProvider
            ):
                registry[module_info.name] = provider_class
    finally:
        if plugin_path in sys.path:
            sys.path.remove(plugin_path)
    return registry


def load_provider_class(
    name: str,
    *,
    entry_point_group: str,
    plugins_dir: Path | None,
) -> Type[NotificationProvider]:
    registry: MutableMapping[str, Type[NotificationProvider]] = {}
    registry.update(discover_builtin_plugins())
    registry.update(discover_entry_points(entry_point_group))
    registry.update(discover_plugins_directory(plugins_dir))

    key = name.lower()
    if key not in registry:
        available = ", ".join(sorted(registry)) or "none"
        raise ValueError(
            f"Unknown provider '{name}'. Available providers: {available}."
        )
    return registry[key]


def initialize_providers(
    provider_configs: Iterable[Mapping[str, object] | object],
    *,
    entry_point_group: str = "notification_providers",
    plugins_dir: Path | None = None,
) -> List[NotificationProvider]:
    """Instantiate providers from configuration items."""

    providers: List[NotificationProvider] = []
    for item in provider_configs:
        name = None
        options: Mapping[str, object] | object | None = None
        if isinstance(item, Mapping):
            name = str(item.get("name"))
            options = item.get("options", {})
        else:
            name = getattr(item, "name", None)
            options = getattr(item, "options", {})
        if not name:
            continue
        cls = load_provider_class(
            name, entry_point_group=entry_point_group, plugins_dir=plugins_dir
        )
        providers.append(cls(**(options if isinstance(options, dict) else {})))
    return providers


__all__ = [
    "NotificationProvider",
    "initialize_providers",
    "load_provider_class",
    "discover_builtin_plugins",
    "discover_entry_points",
    "discover_plugins_directory",
]
