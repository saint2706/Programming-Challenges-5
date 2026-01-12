// ===========================
// Elements
// ===========================

const editor = document.getElementById("editor");
const preview = document.getElementById("preview");
const wordCount = document.getElementById("wordCount");
const charCount = document.getElementById("charCount");
const mainContainer = document.getElementById("mainContainer");

// Toolbar buttons
const boldBtn = document.getElementById("boldBtn");
const italicBtn = document.getElementById("italicBtn");
const headingBtn = document.getElementById("headingBtn");
const linkBtn = document.getElementById("linkBtn");
const codeBtn = document.getElementById("codeBtn");
const listBtn = document.getElementById("listBtn");
const exportBtn = document.getElementById("exportBtn");
const toggleModeBtn = document.getElementById("toggleModeBtn");

// ===========================
// Markdown Rendering
// ===========================

// Configure marked
marked.setOptions({
  breaks: true,
  highlight: function (code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(code, { language: lang }).value;
      } catch (e) {}
    }
    return hljs.highlightAuto(code).value;
  },
});

function updatePreview() {
  const markdown = editor.value;
  preview.innerHTML = marked.parse(markdown);
  updateStats(markdown);

  // Save to localStorage
  localStorage.setItem("markdown-content", markdown);
}

function updateStats(text) {
  const chars = text.length;
  const words = text.trim() === "" ? 0 : text.trim().split(/\s+/).length;

  charCount.textContent = `${chars} character${chars !== 1 ? "s" : ""}`;
  wordCount.textContent = `${words} word${words !== 1 ? "s" : ""}`;
}

// Initial render
editor.addEventListener("input", updatePreview);

// Load saved content
const savedContent = localStorage.getItem("markdown-content");
if (savedContent) {
  editor.value = savedContent;
}
updatePreview();

// ===========================
// Toolbar Functions
// ===========================

function wrapSelection(before, after = before) {
  const start = editor.selectionStart;
  const end = editor.selectionEnd;
  const selectedText = editor.value.substring(start, end);
  const replacement = before + selectedText + after;

  editor.value =
    editor.value.substring(0, start) +
    replacement +
    editor.value.substring(end);

  // Set cursor position
  if (selectedText) {
    editor.selectionStart = start;
    editor.selectionEnd = start + replacement.length;
  } else {
    editor.selectionStart = editor.selectionEnd = start + before.length;
  }

  editor.focus();
  updatePreview();
}

function insertAtCursor(text) {
  const start = editor.selectionStart;
  const end = editor.selectionEnd;

  editor.value =
    editor.value.substring(0, start) + text + editor.value.substring(end);
  editor.selectionStart = editor.selectionEnd = start + text.length;
  editor.focus();
  updatePreview();
}

// Bold
boldBtn.addEventListener("click", () => {
  wrapSelection("**");
});

// Italic
italicBtn.addEventListener("click", () => {
  wrapSelection("*");
});

// Heading
headingBtn.addEventListener("click", () => {
  const start = editor.selectionStart;
  const lineStart = editor.value.lastIndexOf("\n", start - 1) + 1;
  const lineEnd = editor.value.indexOf("\n", start);
  const line = editor.value.substring(
    lineStart,
    lineEnd === -1 ? editor.value.length : lineEnd,
  );

  // Count current hashes
  const hashMatch = line.match(/^(#{1,6})\s/);
  const currentLevel = hashMatch ? hashMatch[1].length : 0;

  // Cycle through heading levels (1-3, then remove)
  let newLine;
  if (currentLevel === 0) {
    newLine = "# " + line;
  } else if (currentLevel < 3) {
    newLine = "#".repeat(currentLevel + 1) + line.substring(currentLevel);
  } else {
    newLine = line.substring(currentLevel + 1);
  }

  editor.value =
    editor.value.substring(0, lineStart) +
    newLine +
    editor.value.substring(lineEnd === -1 ? editor.value.length : lineEnd);
  editor.selectionStart = editor.selectionEnd = lineStart + newLine.length;
  editor.focus();
  updatePreview();
});

// Link
linkBtn.addEventListener("click", () => {
  const start = editor.selectionStart;
  const end = editor.selectionEnd;
  const selectedText = editor.value.substring(start, end);
  const linkText = selectedText || "link text";
  const replacement = `[${linkText}](url)`;

  editor.value =
    editor.value.substring(0, start) +
    replacement +
    editor.value.substring(end);

  // Select 'url' part
  const urlStart = start + linkText.length + 3;
  editor.selectionStart = urlStart;
  editor.selectionEnd = urlStart + 3;

  editor.focus();
  updatePreview();
});

// Code Block
codeBtn.addEventListener("click", () => {
  const start = editor.selectionStart;
  const end = editor.selectionEnd;
  const selectedText = editor.value.substring(start, end);

  if (selectedText.includes("\n")) {
    // Multi-line: code block
    const replacement = "```\n" + selectedText + "\n```";
    editor.value =
      editor.value.substring(0, start) +
      replacement +
      editor.value.substring(end);
    editor.selectionStart = start + 4;
    editor.selectionEnd = start + 4 + selectedText.length;
  } else {
    // Single line: inline code
    wrapSelection("`");
  }

  editor.focus();
  updatePreview();
});

// List
listBtn.addEventListener("click", () => {
  const start = editor.selectionStart;
  const lineStart = editor.value.lastIndexOf("\n", start - 1) + 1;
  const lineEnd = editor.value.indexOf("\n", start);
  const line = editor.value.substring(
    lineStart,
    lineEnd === -1 ? editor.value.length : lineEnd,
  );

  let newLine;
  if (line.match(/^\d+\.\s/)) {
    // Remove ordered list
    newLine = line.replace(/^\d+\.\s/, "");
  } else if (line.match(/^[-*]\s/)) {
    // Convert to ordered list
    newLine = "1. " + line.substring(2);
  } else {
    // Add unordered list
    newLine = "- " + line;
  }

  editor.value =
    editor.value.substring(0, lineStart) +
    newLine +
    editor.value.substring(lineEnd === -1 ? editor.value.length : lineEnd);
  editor.selectionStart = editor.selectionEnd = lineStart + newLine.length;
  editor.focus();
  updatePreview();
});

// ===========================
// Export HTML
// ===========================

exportBtn.addEventListener("click", () => {
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Markdown Export</title>
    <style>
        body {
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            line-height: 1.6;
            color: #333;
        }
        code {
            background: #f4f4f4;
            padding: 0.2em 0.4em;
            border-radius: 3px;
            font-size: 0.9em;
        }
        pre {
            background: #f4f4f4;
            padding: 1rem;
            border-radius: 5px;
            overflow-x: auto;
        }
        pre code {
            background: none;
            padding: 0;
        }
        blockquote {
            border-left: 4px solid #ddd;
            padding-left: 1rem;
            color: #666;
            margin: 1.5rem 0;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 1.5rem 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 0.75rem;
            text-align: left;
        }
        th {
            background: #f4f4f4;
        }
    </style>
</head>
<body>
${preview.innerHTML}
</body>
</html>`;

  const blob = new Blob([html], { type: "text/html" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "markdown-export.html";
  a.click();
  URL.revokeObjectURL(url);
});

// ===========================
// View Mode Toggle
// ===========================

let viewMode = "split"; // 'split', 'editor', 'preview'

toggleModeBtn.addEventListener("click", () => {
  if (viewMode === "split") {
    viewMode = "editor";
    mainContainer.className = "container mode-editor";
  } else if (viewMode === "editor") {
    viewMode = "preview";
    mainContainer.className = "container mode-preview";
  } else {
    viewMode = "split";
    mainContainer.className = "container";
  }
});

// ===========================
// Keyboard Shortcuts
// ===========================

editor.addEventListener("keydown", (e) => {
  // Ctrl/Cmd + B = Bold
  if ((e.ctrlKey || e.metaKey) && e.key === "b") {
    e.preventDefault();
    wrapSelection("**");
  }

  // Ctrl/Cmd + I = Italic
  if ((e.ctrlKey || e.metaKey) && e.key === "i") {
    e.preventDefault();
    wrapSelection("*");
  }

  // Ctrl/Cmd + K = Link
  if ((e.ctrlKey || e.metaKey) && e.key === "k") {
    e.preventDefault();
    linkBtn.click();
  }

  // Tab = Insert 2 spaces (or 4 if you prefer)
  if (e.key === "Tab") {
    e.preventDefault();
    insertAtCursor("  ");
  }
});

// ===========================
// Auto-save indicator
// ===========================

let saveTimeout;
editor.addEventListener("input", () => {
  clearTimeout(saveTimeout);
  saveTimeout = setTimeout(() => {
    console.log("Auto-saved");
  }, 1000);
});

// ===========================
// Initialize
// ===========================

console.log(
  "%c📝 Markdown Previewer",
  "color: #3b82f6; font-size: 18px; font-weight: bold;",
);
console.log("%cKeyboard shortcuts:", "color: #94a3b8; font-size: 12px;");
console.log("%c  Ctrl/Cmd + B: Bold", "color: #94a3b8; font-size: 12px;");
console.log("%c  Ctrl/Cmd + I: Italic", "color: #94a3b8; font-size: 12px;");
console.log("%c  Ctrl/Cmd + K: Link", "color: #94a3b8; font-size: 12px;");
console.log("%c  Tab: Insert spaces", "color: #94a3b8; font-size: 12px;");
