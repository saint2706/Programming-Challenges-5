"""
Command Palette for Your OS
---------------------------
A lightweight background command palette that listens for a global hotkey and
launches a PyQt input dialog to trigger plugins. Plugins are simple Python files
living in the ``plugins`` folder and expose a ``METADATA`` dict and ``execute``
callable.

Run with:
    python Practical/Command\ Palette\ for\ Your\ OS/command_palette.py
"""

from __future__ import annotations

import importlib.util
import logging
import sys
import threading
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

from PyQt6 import QtCore, QtWidgets


@dataclass
class PluginDefinition:
    """Validated plugin metadata and executable hook."""

    name: str
    description: str
    keywords: List[str] = field(default_factory=list)
    execute: Callable[[str], Optional[str]] = lambda _: None
    path: Path = Path()


class PluginLoader:
    """Load plugins from a folder, isolating failures per plugin."""

    def __init__(self, plugin_dir: Path):
        self.plugin_dir = plugin_dir
        self.plugin_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> List[PluginDefinition]:
        plugins: List[PluginDefinition] = []
        for file in sorted(self.plugin_dir.glob("*.py")):
            if file.name.startswith("__"):
                continue
            try:
                plugin = self._load_plugin(file)
                if plugin:
                    plugins.append(plugin)
            except Exception:  # noqa: BLE001
                logging.exception("Failed to load plugin %s", file)
        return plugins

    def _load_plugin(self, file: Path) -> Optional[PluginDefinition]:
        spec = importlib.util.spec_from_file_location(file.stem, file)
        if not spec or not spec.loader:  # pragma: no cover - defensive
            logging.error("Could not create spec for %s", file)
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[arg-type]

        metadata = getattr(module, "METADATA", {})
        name = metadata.get("name")
        description = metadata.get("description")
        keywords = metadata.get("keywords", [])
        execute = getattr(module, "execute", None)

        if not name or not description or not callable(execute):
            logging.warning("Skipping %s: missing metadata or execute()", file)
            return None

        if not isinstance(keywords, list):
            keywords = [str(keywords)]

        return PluginDefinition(
            name=name,
            description=description,
            keywords=[str(k).lower() for k in keywords],
            execute=execute,
            path=file,
        )


class HotkeyListener(QtCore.QThread):
    """Background listener that fires a signal when the hotkey is pressed."""

    hotkey_pressed = QtCore.pyqtSignal()

    def __init__(self, hotkey: str):
        super().__init__()
        self.hotkey = hotkey
        self._running = threading.Event()
        self._running.set()
        self._registered = False

    def run(self) -> None:  # pragma: no cover - requires OS hooks
        try:
            import keyboard
        except Exception as exc:  # noqa: BLE001
            logging.error("Keyboard hook unavailable: %s", exc)
            return

        try:
            keyboard.add_hotkey(self.hotkey, self.hotkey_pressed.emit)
            self._registered = True
            logging.info("Registered hotkey %s", self.hotkey)
        except Exception as exc:  # noqa: BLE001
            logging.error("Failed to register hotkey %s: %s", self.hotkey, exc)
            return

        while self._running.is_set():
            time.sleep(0.2)

        if self._registered:
            try:
                keyboard.remove_hotkey(self.hotkey)
            except Exception:  # noqa: BLE001
                logging.warning("Failed to clean up hotkey %s", self.hotkey)

    def stop(self) -> None:
        self._running.clear()


class PluginExecutionBridge(QtCore.QObject):
    """Signals for plugin execution completion or failure."""

    success = QtCore.pyqtSignal(str, str)
    failure = QtCore.pyqtSignal(str, str)


class CommandPaletteDialog(QtWidgets.QDialog):
    """A searchable palette that lists plugins and runs them with a query."""

    def __init__(self, plugins: List[PluginDefinition]):
        super().__init__()
        self.setWindowTitle("Command Palette")
        self.setModal(True)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.resize(520, 360)

        self.plugins = plugins
        self.filtered_plugins = plugins

        layout = QtWidgets.QVBoxLayout(self)
        info = QtWidgets.QLabel(
            "Type to search plugins. Enter runs the highlighted plugin."
        )
        self.input = QtWidgets.QLineEdit()
        self.input.setPlaceholderText("Search plugins or type a query...")
        self.list_widget = QtWidgets.QListWidget()
        self.status_label = QtWidgets.QLabel()

        layout.addWidget(info)
        layout.addWidget(self.input)
        layout.addWidget(self.list_widget)
        layout.addWidget(self.status_label)

        self.bridge = PluginExecutionBridge()
        self.bridge.success.connect(self._on_success)
        self.bridge.failure.connect(self._on_failure)

        self.input.textChanged.connect(self._filter_plugins)
        self.input.returnPressed.connect(self.run_selected_plugin)
        self.list_widget.itemDoubleClicked.connect(lambda _: self.run_selected_plugin())

        self._filter_plugins("")

    def update_plugins(self, plugins: List[PluginDefinition]) -> None:
        self.plugins = plugins
        self._filter_plugins(self.input.text())
        self.status_label.setText(f"Loaded {len(plugins)} plugins")

    def _filter_plugins(self, text: str) -> None:
        query = text.lower().strip()
        if not query:
            self.filtered_plugins = sorted(self.plugins, key=lambda p: p.name.lower())
        else:

            def matches(plugin: PluginDefinition) -> bool:
                haystack = " ".join(
                    [plugin.name, plugin.description, " ".join(plugin.keywords)]
                )
                return query in haystack.lower()

            self.filtered_plugins = [p for p in self.plugins if matches(p)]

        self.list_widget.clear()
        for plugin in self.filtered_plugins:
            item = QtWidgets.QListWidgetItem(f"{plugin.name} — {plugin.description}")
            self.list_widget.addItem(item)

        if self.filtered_plugins:
            self.list_widget.setCurrentRow(0)
        else:
            self.status_label.setText("No plugins match your query")

    def run_selected_plugin(self) -> None:
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self.filtered_plugins):
            self.status_label.setText("Select a plugin to run")
            return

        plugin = self.filtered_plugins[row]
        query = self.input.text().strip()
        self.status_label.setText(f"Running {plugin.name}…")

        threading.Thread(
            target=self._execute_plugin,
            args=(plugin, query),
            daemon=True,
        ).start()

    def _execute_plugin(self, plugin: PluginDefinition, query: str) -> None:
        try:
            result = plugin.execute(query)
            message = (
                str(result) if result is not None else "Plugin executed successfully."
            )
            self.bridge.success.emit(plugin.name, message)
        except Exception as exc:  # noqa: BLE001
            logging.exception("Plugin %s failed", plugin.name)
            self.bridge.failure.emit(plugin.name, f"{exc}\n{traceback.format_exc()}")

    @QtCore.pyqtSlot(str, str)
    def _on_success(self, plugin_name: str, message: str) -> None:
        self.status_label.setText(f"{plugin_name} completed")
        QtWidgets.QMessageBox.information(self, plugin_name, message)

    @QtCore.pyqtSlot(str, str)
    def _on_failure(self, plugin_name: str, message: str) -> None:
        self.status_label.setText(f"{plugin_name} failed")
        QtWidgets.QMessageBox.critical(self, f"Error in {plugin_name}", message)

    def open_palette(self) -> None:
        self._filter_plugins(self.input.text())
        self.show()
        self.raise_()
        self.activateWindow()
        self.input.setFocus()


class CommandPaletteApplication(QtCore.QObject):
    """Glue together the loader, dialog, hotkey listener, and system tray."""

    def __init__(self, hotkey: str = "ctrl+shift+p"):
        super().__init__()
        plugin_dir = Path(__file__).parent / "plugins"
        self.loader = PluginLoader(plugin_dir)
        self.dialog = CommandPaletteDialog(self.loader.load())

        self.tray_icon = self._build_tray_icon()
        self.hotkey_listener = HotkeyListener(hotkey)
        self.hotkey_listener.hotkey_pressed.connect(self.dialog.open_palette)
        self.hotkey_listener.start()

    def _build_tray_icon(self) -> QtWidgets.QSystemTrayIcon:
        icon = QtWidgets.QApplication.style().standardIcon(
            QtWidgets.QStyle.StandardPixmap.SP_ComputerIcon
        )
        tray = QtWidgets.QSystemTrayIcon(icon)
        menu = QtWidgets.QMenu()

        open_action = menu.addAction("Open Command Palette")
        open_action.triggered.connect(self.dialog.open_palette)

        reload_action = menu.addAction("Reload Plugins")
        reload_action.triggered.connect(self.reload_plugins)

        menu.addSeparator()
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self.shutdown)

        tray.setContextMenu(menu)
        tray.setToolTip("Command Palette is running (" + sys.platform + ")")
        tray.show()
        return tray

    @QtCore.pyqtSlot()
    def reload_plugins(self) -> None:
        plugins = self.loader.load()
        self.dialog.update_plugins(plugins)

    @QtCore.pyqtSlot()
    def shutdown(self) -> None:
        if self.hotkey_listener.isRunning():
            self.hotkey_listener.stop()
            self.hotkey_listener.wait(1000)
        QtWidgets.QApplication.quit()


def main() -> None:  # pragma: no cover - interactive GUI
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    palette = CommandPaletteApplication()
    palette.dialog.open_palette()

    exit_code = app.exec()
    palette.shutdown()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
