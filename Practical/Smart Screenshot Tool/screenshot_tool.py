"""Smart Screenshot Tool using Tkinter, MSS, and pytesseract.

This module provides a simple desktop GUI that can capture screens,
annotate screenshots with drawing tools, and index the saved images with
OCR text to enable search.
"""

from __future__ import annotations

import sqlite3
import threading
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, simpledialog
from typing import List, Optional, Tuple

import mss
import pytesseract
from PIL import Image, ImageDraw, ImageTk

APP_NAME = "Smart Screenshot Tool"
DEFAULT_COLOR = "#ff0000"
DB_NAME = "index.db"
SCREENSHOT_DIR = "screenshots"
SUPPORTED_TOOLS = ("pen", "rectangle", "ellipse", "text")


class IndexStore:
    """Minimal SQLite-based index for OCR text and file metadata."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.db_path = base_path / DB_NAME
        self._ensure_database()

    def _ensure_database(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS screenshots (
                    id INTEGER PRIMARY KEY,
                    path TEXT UNIQUE,
                    created_at TEXT,
                    ocr_text TEXT
                )
                """
            )
            conn.commit()

    def index_image(self, image_path: Path, ocr_text: str) -> None:
        created_at = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO screenshots(path, created_at, ocr_text) VALUES(?, ?, ?)",
                (str(image_path), created_at, ocr_text),
            )
            conn.commit()

    def search(self, query: str) -> List[Tuple[str, str]]:
        like_query = f"%{query}%"
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT path, created_at
                FROM screenshots
                WHERE ocr_text LIKE ? OR path LIKE ?
                ORDER BY created_at DESC
                """,
                (like_query, like_query),
            ).fetchall()
        return [(path, created_at) for path, created_at in rows]

    def all(self) -> List[Tuple[str, str]]:
        return self.search("")


class SmartScreenshotApp(tk.Tk):
    def __init__(self, base_path: Path):
        super().__init__()
        self.title(APP_NAME)

        self.base_path = base_path
        self.screenshot_dir = base_path / SCREENSHOT_DIR
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.index = IndexStore(base_path)

        self.current_image: Optional[Image.Image] = None
        self.current_photo: Optional[ImageTk.PhotoImage] = None
        self.draw_color = DEFAULT_COLOR
        self.draw_width = 3
        self.tool = "pen"
        self.preview_shape = None
        self.start_x: Optional[int] = None
        self.start_y: Optional[int] = None

        self._build_ui()

    # UI SETUP
    def _build_ui(self) -> None:
        toolbar = tk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        capture_btn = tk.Button(
            toolbar, text="Capture Screen", command=self.capture_screen
        )
        capture_btn.pack(side=tk.LEFT, padx=4, pady=4)

        save_btn = tk.Button(toolbar, text="Save & Index", command=self.save_image)
        save_btn.pack(side=tk.LEFT, padx=4, pady=4)

        clear_btn = tk.Button(toolbar, text="Clear", command=self.clear_canvas)
        clear_btn.pack(side=tk.LEFT, padx=4, pady=4)

        tk.Label(toolbar, text="Tool:").pack(side=tk.LEFT, padx=(8, 2))
        self.tool_var = tk.StringVar(value=self.tool)
        for tool in SUPPORTED_TOOLS:
            tk.Radiobutton(
                toolbar,
                text=tool.title(),
                variable=self.tool_var,
                value=tool,
                command=self._set_tool,
            ).pack(side=tk.LEFT)

        color_btn = tk.Button(toolbar, text="Pick Color", command=self.pick_color)
        color_btn.pack(side=tk.LEFT, padx=4)

        tk.Label(toolbar, text="Stroke:").pack(side=tk.LEFT, padx=(8, 2))
        self.width_var = tk.IntVar(value=self.draw_width)
        width_entry = tk.Spinbox(
            toolbar,
            from_=1,
            to=12,
            textvariable=self.width_var,
            width=4,
            command=self._set_width,
        )
        width_entry.pack(side=tk.LEFT, padx=(0, 8))

        search_frame = tk.Frame(self)
        search_frame.pack(side=tk.TOP, fill=tk.X, pady=(4, 2))
        tk.Label(search_frame, text="Search gallery:").pack(side=tk.LEFT, padx=4)
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        search_entry.bind("<KeyRelease>", lambda _event: self.refresh_gallery())

        self.canvas = tk.Canvas(
            self, bg="#1e1e1e", width=900, height=520, cursor="cross"
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        gallery_frame = tk.Frame(self)
        gallery_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=4, pady=4)
        tk.Label(gallery_frame, text="Saved Screenshots").pack()
        self.gallery_list = tk.Listbox(gallery_frame, width=40)
        self.gallery_list.pack(fill=tk.BOTH, expand=True)
        self.gallery_list.bind(
            "<<ListboxSelect>>", lambda _event: self.preview_selected()
        )

        self.preview_label = tk.Label(gallery_frame)
        self.preview_label.pack(fill=tk.BOTH, padx=4, pady=4)

        self.refresh_gallery()

    # Toolbar handlers
    def _set_tool(self) -> None:
        self.tool = self.tool_var.get()

    def _set_width(self) -> None:
        self.draw_width = max(1, int(self.width_var.get()))

    def pick_color(self) -> None:
        color = colorchooser.askcolor(title="Pick color", initialcolor=self.draw_color)
        if color[1]:
            self.draw_color = color[1]

    # Canvas logic
    def capture_screen(self) -> None:
        self.withdraw()
        time.sleep(0.3)
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            shot = sct.grab(monitor)
            self.current_image = Image.frombytes("RGB", shot.size, shot.rgb)
        self.deiconify()
        self._render_canvas()

    def clear_canvas(self) -> None:
        self.canvas.delete("all")
        self.preview_shape = None
        self.current_photo = None
        if self.current_image is not None:
            self._render_canvas()

    def on_press(self, event: tk.Event) -> None:
        if not self.current_image:
            return
        self.start_x, self.start_y = event.x, event.y
        if self.tool == "text":
            self._place_text(event.x, event.y)

    def on_drag(self, event: tk.Event) -> None:
        if (
            not self.current_image
            or self.tool == "text"
            or self.start_x is None
            or self.start_y is None
        ):
            return

        if self.tool == "pen":
            self.canvas.create_line(
                self.start_x,
                self.start_y,
                event.x,
                event.y,
                fill=self.draw_color,
                width=self.draw_width,
                capstyle=tk.ROUND,
            )
            draw = ImageDraw.Draw(self.current_image)
            draw.line(
                (self.start_x, self.start_y, event.x, event.y),
                fill=self.draw_color,
                width=self.draw_width,
            )
            self.start_x, self.start_y = event.x, event.y
            self._render_canvas(live_only=True)
            return

        # Shape preview
        if self.preview_shape:
            self.canvas.delete(self.preview_shape)
        if self.tool == "rectangle":
            self.preview_shape = self.canvas.create_rectangle(
                self.start_x,
                self.start_y,
                event.x,
                event.y,
                outline=self.draw_color,
                width=self.draw_width,
            )
        elif self.tool == "ellipse":
            self.preview_shape = self.canvas.create_oval(
                self.start_x,
                self.start_y,
                event.x,
                event.y,
                outline=self.draw_color,
                width=self.draw_width,
            )

    def on_release(self, event: tk.Event) -> None:
        if (
            not self.current_image
            or self.tool == "text"
            or self.start_x is None
            or self.start_y is None
        ):
            return

        draw = ImageDraw.Draw(self.current_image)
        coords = (self.start_x, self.start_y, event.x, event.y)

        if self.tool == "rectangle":
            draw.rectangle(coords, outline=self.draw_color, width=self.draw_width)
        elif self.tool == "ellipse":
            draw.ellipse(coords, outline=self.draw_color, width=self.draw_width)

        self.start_x = self.start_y = None
        if self.preview_shape:
            self.canvas.delete(self.preview_shape)
            self.preview_shape = None
        self._render_canvas()

    def _place_text(self, x: int, y: int) -> None:
        if not self.current_image:
            return
        text = simpledialog.askstring("Add text", "Enter text to place:")
        if not text:
            return
        draw = ImageDraw.Draw(self.current_image)
        draw.text((x, y), text, fill=self.draw_color)
        self._render_canvas()

    def _render_canvas(self, live_only: bool = False) -> None:
        if not self.current_image:
            self.canvas.delete("all")
            return
        self.current_photo = ImageTk.PhotoImage(self.current_image)
        if not live_only:
            self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_photo)

    # Saving & OCR
    def save_image(self) -> None:
        if not self.current_image:
            messagebox.showinfo(APP_NAME, "Capture a screenshot first.")
            return
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", ".png"), ("JPEG", ".jpg")],
            initialdir=self.screenshot_dir,
            initialfile=datetime.now().strftime("screenshot_%Y%m%d_%H%M%S.png"),
        )
        if not filename:
            return
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.current_image.save(path)
        messagebox.showinfo(APP_NAME, f"Saved screenshot to {path}")
        threading.Thread(target=self._ocr_and_index, args=(path,), daemon=True).start()
        self.refresh_gallery()

    def _ocr_and_index(self, image_path: Path) -> None:
        try:
            text = pytesseract.image_to_string(image_path)
        except Exception as exc:  # pragma: no cover - depends on local tesseract
            text = ""
            print(f"OCR failed: {exc}")
        self.index.index_image(image_path, text)
        self.refresh_gallery()

    # Gallery
    def refresh_gallery(self) -> None:
        query = self.search_var.get()
        rows = self.index.search(query)
        self.gallery_list.delete(0, tk.END)
        for path, created in rows:
            timestamp = created.split("T")[0] if created else ""
            self.gallery_list.insert(tk.END, f"{Path(path).name} — {timestamp}")
        self.gallery_paths = [Path(path) for path, _ in rows]

    def preview_selected(self) -> None:
        if not self.gallery_list.curselection():
            return
        idx = self.gallery_list.curselection()[0]
        path = self.gallery_paths[idx]
        if not path.exists():
            messagebox.showwarning(APP_NAME, f"File missing: {path}")
            return
        image = Image.open(path)
        image.thumbnail((320, 320))
        photo = ImageTk.PhotoImage(image)
        self.preview_label.configure(image=photo)
        self.preview_label.image = photo


def main() -> None:
    base_path = Path(__file__).resolve().parent
    app = SmartScreenshotApp(base_path)
    app.mainloop()


if __name__ == "__main__":
    main()
