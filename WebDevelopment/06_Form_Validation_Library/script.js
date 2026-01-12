// Initialize the form validator
const validator = new FormValidator("#demoForm", {
  validateOnBlur: true,
  validateOnInput: false,
});

validator.init();

console.log("Form Validator initialized");
console.log("Available validation rules:", Object.keys(validator.validators));
