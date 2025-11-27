# Smart Screenshot Tool

A Tkinter-based desktop utility that captures screens with [MSS](https://github.com/BoboTiG/python-mss), lets you annotate with shapes/text, and indexes screenshots with [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for text search. Saved captures appear in a searchable gallery backed by a lightweight SQLite index.

## Features
- Full-screen capture via MSS
- Drawing tools: freehand pen, rectangles, ellipses, and text labels
- Color picker and stroke width control
- Save screenshots locally and OCR their contents in the background
- Minimal SQLite index to make screenshots searchable by text or filename
- Built-in gallery list with instant search and thumbnail preview

## Requirements
- Python 3.9+
- Tkinter (bundled with most CPython installs)
- Pillow
- mss
- pytesseract
- [Tesseract OCR](https://tesseract-ocr.github.io/) installed on your system and accessible in `PATH`

Install Python dependencies:

```bash
pip install pillow mss pytesseract
```

## Usage
Run the tool from the project root:

```bash
python "Practical/Smart Screenshot Tool/screenshot_tool.py"
```

1. Click **Capture Screen** to grab the current monitor. The app hides briefly so it stays out of the capture.
2. Choose a drawing tool (Pen, Rectangle, Ellipse, or Text), pick a color, and set the stroke width.
3. Draw annotations directly on the canvas. For the Text tool, click where you want to place text and enter your label.
4. Hit **Save & Index** to store the annotated image. The file dialog defaults to the `screenshots/` folder next to the script.
5. The image is OCR-indexed in the background. Use the search bar to filter the gallery by detected text or filename. Selecting an item shows a thumbnail preview.

SQLite index and screenshots are stored alongside the script (`index.db` and `screenshots/`).
