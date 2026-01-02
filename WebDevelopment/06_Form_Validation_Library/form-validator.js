/**
 * FormValidator - Lightweight form validation library
 * @version 1.0.0
 */

class FormValidator {
    constructor(formSelector, options = {}) {
        this.form = document.querySelector(formSelector);
        this.fields = [];
        this.options = {
            validateOnBlur: true,
            validateOnInput: false,
            ...options
        };

        if (!this.form) {
            throw new Error(`Form not found: ${formSelector}`);
        }
    }

    // Initialize the validator
    init() {
        this.fields = Array.from(this.form.querySelectorAll('[data-validate]'));
        this.attachEventListeners();
        return this;
    }

    // Attach event listeners
    attachEventListeners() {
        // Form submit
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.validateAll();
        });

        // Field validation
        this.fields.forEach(field => {
            if (this.options.validateOnBlur) {
                field.addEventListener('blur', () => this.validateField(field));
            }

            if (this.options.validateOnInput) {
                field.addEventListener('input', () => this.validateField(field));
            }

            // Clear error on focus
            field.addEventListener('focus', () => this.clearError(field));
        });
    }

    // Validate single field
    validateField(field) {
        const rules = field.dataset.validate.split('|');
        const value = field.type === 'checkbox' ? field.checked : field.value.trim();
        const label = field.dataset.label || field.name;

        for (const rule of rules) {
            const [ruleName, ruleValue] = rule.split(':');
            const validator = this.validators[ruleName];

            if (!validator) {
                console.warn(`Unknown validation rule: ${ruleName}`);
                continue;
            }

            const result = validator.validate(value, ruleValue, field);

            if (!result.isValid) {
                this.showError(field, result.message || validator.message(label, ruleValue, field));
                return false;
            }
        }

        this.showSuccess(field);
        return true;
    }

    // Validate all fields
    validateAll() {
        let isValid = true;

        this.fields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });

        if (isValid) {
            this.onSuccess();
        }

        return isValid;
    }

    // Show error
    showError(field, message) {
        const formGroup = field.closest('.form-group') || field.parentElement;
        const errorElement = formGroup.querySelector('.form-error');

        field.classList.remove('is-valid');
        field.classList.add('is-invalid');

        if (errorElement) {
            errorElement.textContent = message;
        }
    }

    // Show success
    showSuccess(field) {
        const formGroup = field.closest('.form-group') || field.parentElement;
        const errorElement = formGroup.querySelector('.form-error');

        field.classList.remove('is-invalid');
        field.classList.add('is-valid');

        if (errorElement) {
            errorElement.textContent = '';
        }
    }

    // Clear error
    clearError(field) {
        const formGroup = field.closest('.form-group') || field.parentElement;
        const errorElement = formGroup.querySelector('.form-error');

        field.classList.remove('is-invalid');

        if (errorElement) {
            errorElement.textContent = '';
        }
    }

    // Success callback
    onSuccess() {
        console.log('Form validated successfully');

        // Get form data
        const formData = new FormData(this.form);
        const data = Object.fromEntries(formData.entries());
        console.log('Form data:', data);

        // Show success message
        const successMessage = document.getElementById('successMessage');
        if (successMessage) {
            successMessage.style.display = 'block';
            setTimeout(() => {
                successMessage.style.display = 'none';
            }, 5000);
        }

        // Optionally reset form
        // this.form.reset();
        // this.fields.forEach(field => field.classList.remove('is-valid'));
    }

    // Validation rules
    validators = {
        required: {
            validate: (value) => {
                if (typeof value === 'boolean') {
                    return { isValid: value === true };
                }
                return { isValid: value !== '' };
            },
            message: (label) => `${label} is required`
        },

        email: {
            validate: (value) => {
                if (!value) return { isValid: true }; // Empty is valid (use 'required' for mandatory)
                const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                return { isValid: pattern.test(value) };
            },
            message: (label) => `${label} must be a valid email address`
        },

        url: {
            validate: (value) => {
                if (!value) return { isValid: true };
                try {
                    new URL(value);
                    return { isValid: true };
                } catch {
                    return { isValid: false };
                }
            },
            message: (label) => `${label} must be a valid URL`
        },

        phone: {
            validate: (value) => {
                if (!value) return { isValid: true };
                const pattern = /^[\d\s\-\+\(\)]+$/;
                return { isValid: pattern.test(value) && value.replace(/\D/g, '').length >= 10 };
            },
            message: (label) => `${label} must be a valid phone number`
        },

        password: {
            validate: (value) => {
                if (!value) return { isValid: true };
                // At least 8 chars, 1 uppercase, 1 lowercase, 1 number
                const hasLength = value.length >= 8;
                const hasUpper = /[A-Z]/.test(value);
                const hasLower = /[a-z]/.test(value);
                const hasNumber = /\d/.test(value);
                return { isValid: hasLength && hasUpper && hasLower && hasNumber };
            },
            message: (label) => `${label} must contain at least 8 characters with uppercase, lowercase, and number`
        },

        minLength: {
            validate: (value, min) => {
                if (!value) return { isValid: true };
                return { isValid: value.length >= parseInt(min) };
            },
            message: (label, min) => `${label} must be at least ${min} characters`
        },

        maxLength: {
            validate: (value, max) => {
                return { isValid: value.length <= parseInt(max) };
            },
            message: (label, max) => `${label} must not exceed ${max} characters`
        },

        min: {
            validate: (value, min) => {
                if (!value) return { isValid: true };
                return { isValid: parseFloat(value) >= parseFloat(min) };
            },
            message: (label, min) => `${label} must be at least ${min}`
        },

        max: {
            validate: (value, max) => {
                if (!value) return { isValid: true };
                return { isValid: parseFloat(value) <= parseFloat(max) };
            },
            message: (label, max) => `${label} must not exceed ${max}`
        },

        matchField: {
            validate: (value, fieldName, currentField) => {
                const form = currentField.closest('form');
                const matchField = form.querySelector(`[name="${fieldName}"]`);
                if (!matchField) return { isValid: false };
                return { isValid: value === matchField.value };
            },
            message: (label, fieldName, field) => {
                const matchLabel = field.dataset.matchLabel || fieldName;
                return `${label} must match ${matchLabel}`;
            }
        }
    };

    // Add custom validator
    addValidator(name, validator) {
        this.validators[name] = validator;
        return this;
    }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FormValidator;
}
