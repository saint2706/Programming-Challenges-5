# CSS Component Library

A comprehensive, production-ready CSS component library built with modern web standards. Features reusable components styled with BEM methodology and CSS custom properties for easy theming.

## 📸 Preview

![Desktop View](./screenshots/desktop.png)
*Desktop view showcasing component library*

![Mobile View](./screenshots/mobile.png)
*Responsive mobile layout*


## Features

### Component Collection
- **Buttons**: Multiple variants (primary, secondary, outline, ghost), sizes, and states
- **Cards**: Flexible card layouts with headers, bodies, footers, and images
- **Forms**: Complete form elements including inputs, selects, textareas, checkboxes, radios, and switches
- **Modals**: Accessible modal dialogs with overlay and animations
- **Badges**: Status indicators and labels with various styles
- **Tooltips**: Directional tooltips (top, right, bottom, left)

### Design System
- **BEM Naming Convention**: Consistent, maintainable class names
- **CSS Custom Properties**: Full theming support via CSS variables
- **Responsive Design**: Mobile-first approach with breakpoints
- **Accessibility**: WCAG-compliant with keyboard support
- **Modern CSS**: Grid, Flexbox, custom properties, animations

### Developer Experience
- **No Build Required**: Pure CSS, works out of the box
- **Easy Customization**: Change colors/sizing via CSS variables
- **Comprehensive Examples**: Live demos of all components
- **Code Snippets**: Copy-paste ready HTML examples
- **Lightweight**: ~30KB CSS (unminified)

## Quick Start

### Installation

Simply include the CSS file in your HTML:

```html
<link rel="stylesheet" href="style.css">
```

### Basic Usage

```html
<!-- Button -->
<button class="btn btn--primary">Click me</button>

<!-- Card -->
<div class="card">
    <div class="card__header">
        <h3 class="card__title">Card Title</h3>
    </div>
    <div class="card__body">
        <p class="card__text">Card content goes here</p>
    </div>
</div>

<!-- Form  Input -->
<div class="form-group">
    <label class="form-label" for="email">Email</label>
    <input type="email" id="email" class="form-input" placeholder="your@email.com">
</div>
```

## BEM Naming Convention

This library follows the **Block Element Modifier** (BEM) methodology:

- **Block**: `.card` - standalone component
- **Element**: `.card__title` - part of a block
- **Modifier**: `.card--highlight` - variant of a block

### Example

```html
<!-- Block -->
<div class="card">
    <!-- Element -->
    <div class="card__header">
        <!-- Element -->
        <h3 class="card__title">Title</h3>
    </div>
</div>

<!-- Block with Modifier -->
<div class="card card--hover">
    <!-- ... -->
</div>
```

## Customization

### Theming with CSS Variables

All colors, spacing, and typography are defined as CSS custom properties in `:root`. Edit these to match your brand:

```css
:root {
    /* Colors */
    --color-primary: #3b82f6;
    --color-success: #10b981;
    --color-danger: #ef4444;
    
    /* Spacing */
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    
    /* Typography */
    --font-family-base: 'Inter', sans-serif;
    --font-size-base: 1rem;
}
```

### Dark Mode Support

To add dark mode, override variables in a dark theme class:

```css
.theme-dark {
    --bg-body: #111827;
    --text-primary: #f9fafb;
    --border-color: #374151;
}
```

## Component Documentation

### Buttons

**Variants:**
- `.btn--primary` - Primary action
- `.btn--secondary` - Secondary action
- `.btn--outline` - Outlined style
- `.btn--ghost` - Minimal style
- `.btn--success` / `.btn--danger` / `.btn--warning` - State colors

**Sizes:**
- `.btn--sm` - Small button
- (default) - Medium button
- `.btn--lg` - Large button

**States:**
- `:disabled` - Disabled state
- `.btn--loading` - Loading spinner

**Example:**
```html
<button class="btn btn--primary btn--lg">Large Primary</button>
<button class="btn btn--outline" disabled>Disabled</button>
```

### Cards

**Basic Structure:**
```html
<div class="card">
    <div class="card__header"><!-- Optional --></div>
    <div class="card__body"><!-- Required --></div>
    <div class="card__footer"><!-- Optional --></div>
</div>
```

**Variants:**
- `.card--hover` - Interactive hover effect
- `.card--highlight` - Left border accent
- `.card--pricing` - Pricing card layout

### Forms

**Input Types:**
- `.form-input` - Text inputs
- `.form-select` - Select dropdowns
- `.form-textarea` - Text areas
- `.form-checkbox` - Checkboxes
- `.form-radio` - Radio buttons
- `.form-switch` - Toggle switches

**Input States:**
- `.form-input--error` - Error state
- `.form-input--success` - Success state
- `.form-input--icon` - With icon (requires `.form-input-group`)

**Example:**
```html
<div class="form-group">
    <label class="form-label" for="name">Name</label>
    <input type="text" id="name" class="form-input">
    <p class="form-help">Enter your full name</p>
</div>
```

### Modals

**Structure:**
```html
<div class="modal" id="myModal">
    <div class="modal__overlay"></div>
    <div class="modal__content">
        <button class="modal__close">×</button>
        <div class="modal__header"><!-- Optional --></div>
        <div class="modal__body"><!-- Required --></div>
        <div class="modal__footer"><!-- Optional --></div>
    </div>
</div>
```

**JavaScript:**
```javascript
modal.classList.add('is-active'); // Open
modal.classList.remove('is-active'); // Close
```

### Badges

**Variants:**
- `.badge--primary` / `.badge--success` / `.badge--danger` / etc.
- `.badge--pill` - Rounded pill shape
- `.badge--outline` - Outlined style
- `.badge--dot` - With status dot

**Example:**
```html
<span class="badge badge--success">Success</span>
<span class="badge badge--danger badge--pill">Error</span>
```

### Tooltips

Add `data-tooltip` attribute and `.tooltip` class:

```html
<button class="btn btn--primary tooltip" data-tooltip="Helpful hint">
    Hover me
</button>
```

**Positions:**
- `.tooltip--top` (default)
- `.tooltip--right`
- `.tooltip--bottom`
- `.tooltip--left`

## Browser Support

- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Mobile browsers

Requires support for:
- CSS Custom Properties
- CSS Grid and Flexbox
- CSS `:focus-visible`

## Accessibility

- Semantic HTML structure
- ARIA labels where needed
- Keyboard navigation support
- Focus visible indicators
- Color contrast WCAG AA compliant
- Screen reader friendly

## File Structure

```
03_CSS_Component_Library/
├── README.md          # This file
├── index.html         # Component showcase
├── style.css          # All component styles
└── script.js          # Modal interactions
```

## Extending the Library

### Adding New Components

1. Follow BEM naming: `.component`, `.component__element`, `.component--modifier`
2. Use CSS custom properties for colors/spacing
3. Ensure responsive behavior
4. Add accessibility attributes
5. Test keyboard navigation

### Example New Component

```css
/* Block */
.alert {
    padding: var(--spacing-md);
    border-radius: var(--border-radius-md);
    border: 1px solid var(--border-color);
}

/* Element */
.alert__title {
    font-weight: 600;
    margin-bottom: var(--spacing-xs);
}

/* Modifier */
.alert--success {
    background-color: rgba(16, 185, 129, 0.1);
    border-color: var(--color-success);
    color: var(--color-success-dark);
}
```

## Performance

- **Minimal CSS**: Uses efficient selectors
- **No JavaScript Dependencies**: Vanilla JS for modals only
- **GPU Accelerated**: Uses `transform` and `opacity` for animations
- **Lazy Loading Ready**: Can be split into modules

## Best Practices

1. **Use semantic HTML** - Don't use `<div class="btn">`, use `<button class="btn">`
2. **Don't override base styles** - Use modifiers instead
3. **Combine modifiers** - `class="btn btn--primary btn--lg"`
4. **Keep specificity low** - Avoid nested selectors when possible
5. **Use custom properties** - Don't hardcode colors/values

## Learning Outcomes

This component library demonstrates:

- **BEM Methodology**: Scalable CSS architecture
- **Design Systems**: Consistent theming and spacing
- **CSS Custom Properties**: Dynamic theming capabilities
- **Accessibility**: Creating inclusive components
- **Component Design**: Reusable, composable patterns

## Potential Improvements

- Add more components (alerts, progress bars, breadcrumbs, pagination)
- Create JavaScript component initialization system
- Add CSS-in-JS or Sass version
- Create React/Vue component wrappers
- Add animation utilities
- Build theme generator tool
- Create npm package

## Credits

- Design inspired by modern UI libraries (Tailwind, Bootstrap, Material)
- BEM methodology by Yandex
- Icons: Custom SVG icons

---

**Challenge Difficulty**: Easy  
**Estimated Time**: 3-4 hours  
**Key Concepts**: BEM Methodology, CSS Custom Properties, Component Design
