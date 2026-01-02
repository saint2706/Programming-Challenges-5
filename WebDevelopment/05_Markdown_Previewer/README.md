# Markdown Previewer

A feature-rich, live markdown editor with split-pane layout, syntax highlighting for code blocks, and export functionality. Built with Marked.js and Highlight.js.

## Features

- **Live Preview**: See your markdown rendered in real-time as you type
- **Split-Pane Layout**: Editor and preview side-by-side
- **Syntax Highlighting**: Code blocks with automatic language detection
- **Formatting Toolbar**: Quick buttons for common markdown syntax
- **Keyboard Shortcuts**: Fast formatting with Ctrl/Cmd shortcuts
- **Word/Character Count**: Live statistics in the editor
- **Export HTML**: Download your markdown as a standalone HTML file
- **Auto-Save**: Content automatically saved to localStorage
- **View Modes**: Toggle between split, editor-only, and preview-only views
- **Responsive Design**: Works on mobile, tablet, and desktop

## Quick Start

Simply open `index.html` in your browser - no installation required!

## Usage

### Formatting Toolbar

- **Bold** (Ctrl+B): Wrap text in `**bold**`
- **Italic** (Ctrl+I): Wrap text in `*italic*`
- **Heading**: Cycle through heading levels (#, ##, ###)
- **Link** (Ctrl+K): Insert markdown link `[text](url)`
- **Code**: Inline code or code block
- **List**: Toggle between unordered (-), ordered (1.), and plain text

### Additional Features

- **Export HTML**: Download your markdown as a styled HTML file
- **View Toggle**: Switch between split, editor-only, and preview-only modes
- **Auto-Save**: Your work is automatically saved to browser storage

### Keyboard Shortcuts

- `Ctrl/Cmd + B`: Bold
- `Ctrl/Cmd + I`: Italic
- `Ctrl/Cmd + K`: Insert link
- `Tab`: Insert 2 spaces (for indentation)

## Supported Markdown

### Headers
```markdown
# H1
## H2
### H3
```

### Emphasis
```markdown
**bold text**
*italic text*
***bold and italic***
```

### Lists
```markdown
- Unordered item
- Another item

1. Ordered item
2. Another item
```

### Links & Images
```markdown
[Link text](https://example.com)
![Alt text](image.jpg)
```

### Code
```markdown
Inline `code` has backticks

```javascript
// Code block
function hello() {
  console.log('Hello!');
}
\```
```

### Blockquotes
```markdown
> This is a blockquote
> It can span multiple lines
```

### Tables
```markdown
| Header 1 | Header 2 |
| -------- | -------- |
| Cell 1   | Cell 2   |
```

### Horizontal Rules
```markdown
---
```

## Tech Stack

- **HTML5**: Semantic structure
- **CSS3**: Modern styling with grid layout
- **Vanilla JavaScript**: No framework dependencies
- **[Marked.js](https://marked.js.org/)**: Markdown parsing (~23KB)
- **[Highlight.js](https://highlightjs.org/)**: Syntax highlighting (~35KB)
- **Google Fonts**: Inter (sans-serif) + JetBrains Mono (monospace)

## File Structure

```
05_Markdown_Previewer/
├── README.md          # This file
├── index.html         # Main application
├── style.css          # Styling (~350 lines)
└── script.js          # Application logic (~250 lines)
```

## Customization

### Changing Theme Colors

Edit CSS variables in `style.css`:

```css
:root {
    --color-bg-primary: #0f172a;
    --color-accent: #3b82f6;
    /* ... more variables */
}
```

### Syntax Highlighting Theme

Change the Highlight.js theme in `index.html`:

```html
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
```

Available themes: `github-dark`, `monokai`, `atom-one-dark`, `vs2015`, etc.

### Markdown Configuration

Modify Marked.js options in `script.js`:

```javascript
marked.setOptions({
    breaks: true,        // GitHub-flavored line breaks
    gfm: true,          // GitHub Flavored Markdown
    headerIds: false,   // Generate heading IDs
    // ... more options
});
```

## Browser Support

✅ Chrome/Edge 90+  
✅ Firefox 88+  
✅ Safari 14+  
✅ Mobile browsers

Requires:
- ES6 JavaScript
- CSS Grid
- localStorage API

## Performance

- **Fast Rendering**: Marked.js parses markdown efficiently
- **Minimal Re-renders**: Only updates on input change
- **Lazy Loading**: Syntax highlighting applied after render
- **Lightweight**: ~60KB total (including libraries from CDN)

## Accessibility

- Semantic HTML structure
- Keyboard navigation support
- ARIA labels on toolbar buttons
- High contrast ratio (WCAG AA)
- Focus visible indicators

## Features Breakdown

### Live Preview
As you type in the editor, the preview pane updates instantly. This uses Marked.js to convert markdown to HTML.

### Syntax Highlighting
Code blocks are automatically detected and highlighted using Highlight.js. Supports 190+ languages.

### Export HTML
Generates a standalone HTML file with embedded CSS, perfect for sharing or archiving.

### Auto-Save
Content is automatically saved to localStorage after 1 second of inactivity. Never lose your work!

### View Modes
- **Split**: Editor and preview side-by-side (default)
- **Editor Only**: Focus on writing
- **Preview Only**: See final result

## Common Use Cases

1. **Documentation**: Write README files, technical docs, guides
2. **Blog Posts**: Draft articles in markdown
3. **Notes**: Quick markdown notes with preview
4. **Learning**: Experiment with markdown syntax
5. **Code Documentation**: Document code with syntax-highlighted examples

## Limitations

- No collaborative editing (single-user only)
- No cloud sync (localStorage only)
- Export is client-side only (no server upload)
- Images must be URLs or data URIs

## Potential Improvements

- Add dark/light theme toggle
- Implement drag-and-drop image upload
- Add markdown table generator
- Create PDF export option
- Implement version history
- Add collaborative editing with WebSockets
- Support for mermaid diagrams
- Add spell checker
- Implement search and replace
- Create markdown shortcuts cheat sheet
- Add distraction-free writing mode

## Learning Outcomes

This project demonstrates:

1. **Markdown Parsing**: Using Marked.js for conversion
2. **Syntax Highlighting**: Integrating Highlight.js
3. **Split Pane Layout**: CSS Grid for responsive layout
4. **Text Manipulation**: JavaScript string operations
5. **File Export**: Blob and download APIs
6. **LocalStorage**: Client-side persistence
7. **Keyboard Shortcuts**: Event handling
8. **Live Updates**: Real-time preview rendering

## Credits

- **Marked.js**: Christopher Jeffrey and contributors
- **Highlight.js**: Ivan Sagalaev and contributors
- **Fonts**: Google Fonts (Inter, JetBrains Mono)

---

**Challenge Difficulty**: Easy  
**Estimated Time**: 3-4 hours  
**Key Concepts**: Markdown Parsing, Live Preview, Text Manipulation
