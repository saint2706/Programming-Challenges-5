"""Tkinter GUI for viewing screen time summaries."""

from __future__ import annotations

import tkinter as tk
from datetime import date
from typing import Dict

from .storage import JSONStorage, SQLiteStorage


class SummaryGUI:
    """Simple GUI to display aggregated daily usage."""

    def __init__(self, backend: str = "sqlite", path: str | None = None) -> None:
        """
        Docstring for __init__.
        """
        self.backend = backend
        self.path = path
        self.root = tk.Tk()
        self.root.title("Screen Time Tracker")
        self.listbox = tk.Listbox(self.root, width=60)
        self.listbox.pack(padx=10, pady=10)
        refresh_button = tk.Button(self.root, text="Refresh", command=self.refresh)
        refresh_button.pack(pady=(0, 10))
        self.refresh()

    def _storage(self):
        """
        Docstring for _storage.
        """
        if self.backend == "json":
            return JSONStorage(self.path or "screen_time.json")
        return SQLiteStorage(self.path or "screen_time.sqlite")

    def refresh(self) -> None:
        """
        Docstring for refresh.
        """
        self.listbox.delete(0, tk.END)
        summary = self._storage().daily_summary(date.today())
        if not summary:
            self.listbox.insert(tk.END, "No data recorded for today yet.")
            return
        for app, seconds in summary.items():
            hours = seconds / 3600
            self.listbox.insert(tk.END, f"{app}: {hours:.2f}h")

    def run(self) -> None:
        """
        Docstring for run.
        """
        self.root.mainloop()


def launch(backend: str = "sqlite", path: str | None = None) -> None:
    """
    Docstring for launch.
    """
    gui = SummaryGUI(backend=backend, path=path)
    gui.run()


if __name__ == "__main__":
    launch()
