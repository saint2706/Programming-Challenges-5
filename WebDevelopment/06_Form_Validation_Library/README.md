# Form Validation Library

A lightweight, dependency-free form validation library with real-time feedback and extensive validation rules.

## Features

- ✅ **10+ Built-in Validators**: Email, URL, phone, password strength, length, numeric ranges, and more
- ✅ **Real-time Validation**: Validate on blur or input
- ✅ **Custom Error Messages**: Automatic or custom messages
- ✅ **Chained Rules**: Multiple validation rules per field
- ✅ **Extensible**: Easy to add custom validators
- ✅ **No Dependencies**: Pure vanilla JavaScript
- ✅ **Lightweight**: ~3KB minified
- ✅ **Visual Feedback**: Success/error states with colors

## Quick Start

### 1. Include the Library

```html
<script src="form-validator.js"></script>
```

### 2. Add Validation Attributes

```html
<input
  type="text"
  name="email"
  data-validate="required|email"
  data-label="Email Address"
/>
<div class="form-error"></div>
```

### 3. Initialize

```javascript
const validator = new FormValidator("#myForm");
validator.init();
```

## Available Validation Rules

| Rule              | Usage                                 | Description                                      |
| ----------------- | ------------------------------------- | ------------------------------------------------ |
| `required`        | `data-validate="required"`            | Field must not be empty                          |
| `email`           | `data-validate="email"`               | Valid email format                               |
| `url`             | `data-validate="url"`                 | Valid URL format                                 |
| `phone`           | `data-validate="phone"`               | Valid phone number (10+ digits)                  |
| `password`        | `data-validate="password"`            | Strong password (8+ chars, upper, lower, number) |
| `minLength:n`     | `data-validate="minLength:3"`         | Minimum character length                         |
| `maxLength:n`     | `data-validate="maxLength:50"`        | Maximum character length                         |
| `min:n`           | `data-validate="min:18"`              | Minimum numeric value                            |
| `max:n`           | `data-validate="max:120"`             | Maximum numeric value                            |
| `matchField:name` | `data-validate="matchField:password"` | Must match another field                         |

## Usage Examples

### Basic Validation

```html
<form id="myForm">
  <div class="form-group">
    <label>Email</label>
    <input
      type="email"
      name="email"
      data-validate="required|email"
      data-label="Email"
    />
    <div class="form-error"></div>
  </div>

  <button type="submit">Submit</button>
</form>

<script>
  const validator = new FormValidator("#myForm");
  validator.init();
</script>
```

### Chained Validation

```html
<input
  type="text"
  name="username"
  data-validate="required|minLength:3|maxLength:20"
  data-label="Username"
/>
```

### Password Matching

```html
<input
  type="password"
  name="password"
  data-validate="required|password"
  data-label="Password"
/>

<input
  type="password"
  name="confirmPassword"
  data-validate="required|matchField:password"
  data-label="Confirm Password"
  data-match-label="Password"
/>
```

### Numeric Validation

```html
<input
  type="number"
  name="age"
  data-validate="required|min:18|max:120"
  data-label="Age"
/>
```

## Configuration Options

```javascript
const validator = new FormValidator("#myForm", {
  validateOnBlur: true, // Validate when field loses focus
  validateOnInput: false, // Validate on every keystroke
});
```

## Custom Validators

Add your own validation rules:

```javascript
validator.addValidator("custom", {
  validate: (value) => {
    // Your validation logic
    return { isValid: value.startsWith("ABC") };
  },
  message: (label) => `${label} must start with ABC`,
});
```

## HTML Structure

Required structure for each form field:

```html
<div class="form-group">
  <label class="form-label"> Field Name <span class="required">*</span> </label>
  <input
    type="text"
    name="fieldName"
    class="form-input"
    data-validate="required"
    data-label="Field Name"
  />
  <div class="form-error"></div>
</div>
```

## CSS Classes

The library automatically adds these classes:

- `.is-valid` - Field is valid
- `.is-invalid` - Field has errors

Style them in your CSS:

```css
.form-input.is-valid {
  border-color: #10b981;
}

.form-input.is-invalid {
  border-color: #ef4444;
}

.form-error {
  color: #ef4444;
  font-size: 0.875rem;
}
```

## Methods

### `init()`

Initialize the validator and attach event listeners.

```javascript
validator.init();
```

### `validateField(field)`

Validate a single field.

```javascript
const field = document.querySelector("#email");
const isValid = validator.validateField(field);
```

### `validateAll()`

Validate all fields in the form.

```javascript
const isValid = validator.validateAll();
```

### `addValidator(name, validator)`

Add a custom validation rule.

```javascript
validator.addValidator("zipcode", {
  validate: (value) => {
    return { isValid: /^\d{5}$/.test(value) };
  },
  message: (label) => `${label} must be a 5-digit ZIP code`,
});
```

## Browser Support

✅ Chrome/Edge 90+  
✅ Firefox 88+  
✅ Safari 14+  
✅ All modern browsers with ES6 support

## File Size

- Unminified: ~8KB
- Minified: ~3KB
- Gzipped: ~1.5KB

## No Dependencies

This library has zero dependencies. Just include the JavaScript file and you're ready to go.

## Examples

### Login Form

```html
<form id="loginForm">
  <input type="email" data-validate="required|email" data-label="Email" />
  <input
    type="password"
    data-validate="required|minLength:8"
    data-label="Password"
  />
  <button type="submit">Login</button>
</form>
```

### Registration Form

```html
<form id="registerForm">
  <input
    type="text"
    data-validate="required|minLength:3|maxLength:50"
    data-label="Full Name"
  />
  <input type="email" data-validate="required|email" data-label="Email" />
  <input
    type="password"
    data-validate="required|password"
    data-label="Password"
  />
  <input
    type="password"
    data-validate="required|matchField:password"
    data-label="Confirm Password"
  />
  <button type="submit">Register</button>
</form>
```

## Advanced Usage

### Custom Success Handler

Override the `onSuccess` method:

```javascript
validator.onSuccess = function () {
  const formData = new FormData(this.form);

  // Send to API
  fetch("/api/submit", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => console.log("Success:", data));
};
```

### Programmatic Validation

```javascript
// Validate specific field
const emailField = document.querySelector("#email");
if (validator.validateField(emailField)) {
  console.log("Email is valid");
}

// Validate entire form
if (validator.validateAll()) {
  console.log("All fields are valid");
}
```

## License

MIT License - Free to use in personal and commercial projects.

---

**Challenge Difficulty**: Easy  
**Estimated Time**: 3-4 hours  
**Key Concepts**: Form validation, regex patterns, DOM manipulation, event handling
