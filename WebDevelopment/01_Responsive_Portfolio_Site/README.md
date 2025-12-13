# Responsive Portfolio Site

**Web Development Challenge #1** — A modern, responsive portfolio site built with pure HTML, CSS, and JavaScript.

## 🎯 Challenge Requirements

| Requirement | Status |
|-------------|--------|
| Mobile-first responsive design | ✅ |
| CSS Grid/Flexbox layouts | ✅ |
| Contact form (frontend) | ✅ |
| HTML/CSS only (no frameworks) | ✅ |

## ✨ Features

- **Dark/Light Theme** — Toggle with localStorage persistence
- **Responsive Navigation** — Hamburger menu on mobile
- **Smooth Animations** — Fade-ins, hover effects, skill bar reveals
- **Form Validation** — Client-side validation with error messages
- **Modern Design** — Glassmorphism, gradients, custom properties

## 🚀 Quick Start

```bash
# Option 1: Open directly in browser
# Just double-click index.html

# Option 2: Use a local server
python -m http.server 8080
# Then open http://localhost:8080
```

## 📁 Project Structure

```text
01_Responsive_Portfolio_Site/
├── index.html    # Main HTML structure
├── style.css     # Design system & styles
├── script.js     # Interactivity
└── README.md     # This file
```

## 🎨 Design Decisions

- **Typography**: Inter (primary) + Fira Code (mono)
- **Colors**: Dark theme default with cyan/purple/pink accents
- **Layout**: CSS Grid for sections, Flexbox for components
- **Animations**: CSS keyframes with subtle, non-distracting effects

## 📱 Responsive Breakpoints

| Breakpoint | Design |
|------------|--------|
| < 768px | Mobile (hamburger menu, stacked layout) |
| 768px+ | Tablet (2-column grids) |
| 1024px+ | Desktop (3-column grids, full navigation) |

## 🧪 Testing

1. **Responsive**: Test at widths 375px, 768px, and 1200px+
2. **Theme**: Click theme toggle, refresh — preference persists
3. **Form**: Submit empty form to see validation errors
4. **Navigation**: Test smooth scroll and mobile menu
