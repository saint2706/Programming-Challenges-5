// ===========================
// Theme Management
// ===========================

const themeToggle = document.getElementById('themeToggle');
const useSystemPreference = document.getElementById('useSystemPreference');
const currentThemeEl = document.getElementById('currentTheme');
const systemPreferenceEl = document.getElementById('systemPreference');

// Check for saved theme or system preference
function getInitialTheme() {
    const savedTheme = localStorage.getItem('theme');
    const useSystem = localStorage.getItem('useSystemPreference') === 'true';
    
    if (useSystem || !savedTheme) {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    
    return savedTheme;
}

// Set theme
function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    updateThemeDisplay(theme);
}

// Update theme display in settings
function updateThemeDisplay(theme) {
    currentThemeEl.textContent = theme === 'dark' ? 'Dark Mode' : 'Light Mode';
}

// Toggle theme
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    
    // If manually toggled, disable system preference
    if (useSystemPreference.checked) {
        useSystemPreference.checked = false;
        localStorage.setItem('useSystemPreference', 'false');
    }
}

// Initialize theme
const initialTheme = getInitialTheme();
setTheme(initialTheme);

// Check if using system preference
const usingSysPref = localStorage.getItem('useSystemPreference') === 'true';
if (usingSysPref) {
    useSystemPreference.checked = true;
}

// Theme toggle button click
themeToggle.addEventListener('click', toggleTheme);

// ===========================
// System Preference Detection
// ===========================

// Display system preference
const systemPreference = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'Dark' : 'Light';
systemPreferenceEl.textContent = systemPreference;

// Listen for system preference changes
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    const newSystemPreference = e.matches ? 'Dark' : 'Light';
    systemPreferenceEl.textContent = newSystemPreference;
    
    // If using system preference, update theme
    if (useSystemPreference.checked) {
        setTheme(e.matches ? 'dark' : 'light');
    }
});

// Handle system preference toggle
useSystemPreference.addEventListener('change', (e) => {
    const useSysPref = e.target.checked;
    localStorage.setItem('useSystemPreference', useSysPref.toString());
    
    if (useSysPref) {
        // Switch to system preference
        const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        setTheme(systemDark ? 'dark' : 'light');
    }
});

// ===========================
// Keyboard Shortcuts
// ===========================

document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + Shift + D to toggle dark mode
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'D') {
        e.preventDefault();
        toggleTheme();
    }
});

// ===========================
// Form Submit Handler
// ===========================

const demoForm = document.querySelector('.demo-form form');
if (demoForm) {
    demoForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        // Create success alert
        const successAlert = document.createElement('div');
        successAlert.className = 'alert alert--success';
        successAlert.innerHTML = '<strong>Success:</strong> Form submitted (demo only)';
        successAlert.style.marginTop = '1rem';
        
        demoForm.appendChild(successAlert);
        
        // Remove after 3 seconds
        setTimeout(() => {
            successAlert.remove();
        }, 3000);
        
        // Reset form
        demoForm.reset();
    });
}

// ===========================
// Smooth Transitions on Load
// ===========================

// Disable transitions on page load to prevent flash
document.documentElement.style.setProperty('--transition-colors', 'none');

window.addEventListener('load', () => {
    // Re-enable transitions after page load
    setTimeout(() => {
        document.documentElement.style.removeProperty('--transition-colors');
    }, 100);
});

// ===========================
// Analytics (Demo)
// ===========================

// Track theme changes (in production, send to analytics)
function trackThemeChange(theme) {
    console.log(`%cTheme changed to: ${theme}`, 'color: #3b82f6; font-weight: bold;');
}

// Override setTheme to include tracking
const originalSetTheme = setTheme;
setTheme = function(theme) {
    originalSetTheme(theme);
    trackThemeChange(theme);
};

// ===========================
// Initialize
// ===========================

console.log('%c🌓 Dark Mode Toggle Demo', 'color: #3b82f6; font-size: 18px; font-weight: bold;');
console.log('%cKeyboard shortcut: Ctrl/Cmd + Shift + D', 'color: #6b7280; font-size: 12px;');
console.log(`%cCurrent theme: ${initialTheme}`, 'color: #6b7280; font-size: 12px;');
console.log(`%cSystem preference: ${systemPreference}`, 'color: #6b7280; font-size: 12px;');
