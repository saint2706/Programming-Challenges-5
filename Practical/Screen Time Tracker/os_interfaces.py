"""Operating-system specific active window detection."""

from __future__ import annotations

import importlib
import platform
import subprocess
from dataclasses import dataclass
from typing import Optional


def _load_module(name: str):
    """Load a module only if present to avoid hard dependencies."""
    spec = importlib.util.find_spec(name)
    if spec is None:
        return None
    return importlib.import_module(name)


@dataclass
class WindowInfo:
    """Details about an active window."""

    title: str
    application: Optional[str] = None


class ActiveWindowProvider:
    """Contract for retrieving the active window title."""

    def get_active_window(self) -> Optional[WindowInfo]:
        """Fetch the currently focused window."""

        raise NotImplementedError


class WindowsWindowProvider(ActiveWindowProvider):
    """Active window detection for Windows via pywin32."""

    def __init__(self) -> None:
        self.win32gui = _load_module("win32gui")
        self.win32process = _load_module("win32process")
        self.psutil = _load_module("psutil")

    def get_active_window(self) -> Optional[WindowInfo]:
        if self.win32gui is None:
            return None
        hwnd = self.win32gui.GetForegroundWindow()
        if not hwnd:
            return None
        title = self.win32gui.GetWindowText(hwnd)
        application = None
        if self.win32process and self.psutil:
            _, pid = self.win32process.GetWindowThreadProcessId(hwnd)
            try:
                process = self.psutil.Process(pid)
                application = process.name()
            except self.psutil.NoSuchProcess:
                application = None
        return WindowInfo(title=title.strip(), application=application)


class MacWindowProvider(ActiveWindowProvider):
    """Active window detection for macOS using AppleScript."""

    def get_active_window(self) -> Optional[WindowInfo]:
        script = (
            'tell application "System Events" to get {name of first process whose frontmost is true, '
            "name of window 1 of (first process whose frontmost is true)}"
        )
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            return None
        parts = result.stdout.strip().split(",")
        if not parts:
            return None
        app_name = parts[0].strip()
        window_title = ",".join(parts[1:]).strip() if len(parts) > 1 else ""
        return WindowInfo(title=window_title, application=app_name)


class LinuxWindowProvider(ActiveWindowProvider):
    """Active window detection for X11 desktops using python-ewmh when available."""

    def __init__(self) -> None:
        self.ewmh_module = _load_module("ewmh")
        self.xlib_display = _load_module("Xlib.display")
        self.ewmh_instance = None
        if self.ewmh_module and self.xlib_display:
            self.ewmh_instance = self.ewmh_module.EWMH()

    def _via_ewmh(self) -> Optional[WindowInfo]:
        if not self.ewmh_instance:
            return None
        window = self.ewmh_instance.getActiveWindow()
        if not window:
            return None
        title = window.get_wm_name() or ""
        cls = window.get_wm_class()
        application = cls[0] if cls else None
        return WindowInfo(title=title, application=application)

    def _via_xprop(self) -> Optional[WindowInfo]:
        window_id_proc = subprocess.run(
            ["xprop", "-root", "_NET_ACTIVE_WINDOW"],
            capture_output=True,
            text=True,
            check=False,
        )
        if window_id_proc.returncode != 0:
            return None
        parts = window_id_proc.stdout.strip().split()
        if not parts:
            return None
        win_hex = parts[-1]
        window_info = subprocess.run(
            ["xprop", "-id", win_hex, "_NET_WM_NAME", "WM_CLASS"],
            capture_output=True,
            text=True,
            check=False,
        )
        if window_info.returncode != 0:
            return None
        title = ""
        application = None
        for line in window_info.stdout.splitlines():
            if "_NET_WM_NAME" in line:
                title = line.split("=", 1)[-1].strip().strip('"')
            if "WM_CLASS" in line:
                class_parts = line.split("=", 1)[-1].split(",")
                if class_parts:
                    application = class_parts[-1].strip().strip('"')
        return WindowInfo(title=title, application=application)

    def get_active_window(self) -> Optional[WindowInfo]:
        return self._via_ewmh() or self._via_xprop()


def get_provider_for_platform(system: Optional[str] = None) -> ActiveWindowProvider:
    """Return an appropriate window provider for the OS."""

    platform_name = system or platform.system().lower()
    if platform_name.startswith("win"):
        return WindowsWindowProvider()
    if platform_name.startswith("darwin") or platform_name == "mac":
        return MacWindowProvider()
    return LinuxWindowProvider()
