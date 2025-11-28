"""Utilities for loading unit conversion metadata from JSON or YAML files."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class ConfigurationError(RuntimeError):
    """Raised when the configuration file cannot be parsed."""


class ConversionDataSource:
    """Loads and caches conversion metadata from disk.

    The loader keeps the parsed configuration in memory and only reloads the
    source file when it changes on disk or when ``force=True`` is passed to
    :meth:`load`.
    """

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self._data: Optional[Dict[str, Any]] = None
        self._last_mtime: Optional[float] = None
        self._lock = threading.Lock()
        self._version = 0

    @property
    def version(self) -> int:
        return self._version

    def load(self, force: bool = False) -> Dict[str, Any]:
        """Return the parsed configuration, reloading it if necessary."""
        with self._lock:
            if force or self._needs_reload():
                self._data = self._read_file()
                self._version += 1
                try:
                    self._last_mtime = self.path.stat().st_mtime
                except FileNotFoundError:
                    self._last_mtime = None
            if self._data is None:
                raise ConfigurationError("Configuration could not be loaded.")
            return self._data

    # ------------------------------------------------------------------
    def _needs_reload(self) -> bool:
        if self._data is None:
            return True
        try:
            current_mtime = self.path.stat().st_mtime
        except FileNotFoundError as exc:
            raise ConfigurationError(
                f"Configuration file {self.path} does not exist"
            ) from exc
        return self._last_mtime is None or current_mtime > self._last_mtime

    def _read_file(self) -> Dict[str, Any]:
        if not self.path.exists():
            raise ConfigurationError(f"Configuration file {self.path} does not exist")
        text = self.path.read_text()
        suffix = self.path.suffix.lower()
        try:
            if suffix == ".json":
                return json.loads(text)
            if suffix in {".yaml", ".yml"}:
                return yaml.safe_load(text)
        except (json.JSONDecodeError, yaml.YAMLError) as exc:
            raise ConfigurationError(f"Failed to parse configuration: {exc}") from exc
        raise ConfigurationError(
            f"Unsupported configuration format '{suffix}'. Use JSON or YAML."
        )
