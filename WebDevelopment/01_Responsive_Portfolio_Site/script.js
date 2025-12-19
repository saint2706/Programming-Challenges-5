/**
 * Portfolio Site - JavaScript
 * Handles theme toggle, mobile menu, smooth scroll, and form validation
 */

// ==========================================================================
// Theme Toggle
// ==========================================================================

/**
 * Initialize theme from localStorage or system preference
 */
function initTheme() {
  const savedTheme = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

  if (savedTheme) {
    document.documentElement.setAttribute('data-theme', savedTheme);
  } else if (!prefersDark) {
    document.documentElement.setAttribute('data-theme', 'light');
  }
}

/**
 * Toggle between light and dark themes
 */
function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute('data-theme');
  const newTheme = currentTheme === 'light' ? 'dark' : 'light';

  document.documentElement.setAttribute('data-theme', newTheme);
  localStorage.setItem('theme', newTheme);
}

// Initialize theme immediately to prevent flash
initTheme();

// ==========================================================================
// Mobile Navigation
// ==========================================================================

/**
 * Set up mobile navigation toggle
 */
function initMobileNav() {
  const toggle = document.getElementById('nav-toggle');
  const close = document.getElementById('nav-close');
  const menu = document.getElementById('nav-menu');
  const links = document.querySelectorAll('.nav__link');

  // Create overlay element
  const overlay = document.createElement('div');
  overlay.classList.add('nav-overlay');
  document.body.appendChild(overlay);

  function openMenu() {
    menu.classList.add('active');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeMenu() {
    menu.classList.remove('active');
    overlay.classList.remove('active');
    document.body.style.overflow = '';
  }

  if (toggle) {
    toggle.addEventListener('click', openMenu);
  }

  if (close) {
    close.addEventListener('click', closeMenu);
  }

  overlay.addEventListener('click', closeMenu);

  // Close menu when clicking nav links
  links.forEach((link) => {
    link.addEventListener('click', closeMenu);
  });

  // Close menu on escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && menu.classList.contains('active')) {
      closeMenu();
    }
  });
}

// ==========================================================================
// Smooth Scroll
// ==========================================================================

/**
 * Add smooth scroll behavior to anchor links
 */
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener('click', function (e) {
      const href = this.getAttribute('href');

      if (href === '#') return;

      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({
          behavior: 'smooth',
          block: 'start',
        });
      }
    });
  });
}

// ==========================================================================
// Header Scroll Effect
// ==========================================================================

/**
 * Add scroll effect to header
 */
function initHeaderScroll() {
  const header = document.getElementById('header');
  let lastScroll = 0;

  window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;

    if (currentScroll > 100) {
      header.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.3)';
    } else {
      header.style.boxShadow = 'none';
    }

    lastScroll = currentScroll;
  });
}

// ==========================================================================
// Form Validation & Submission
// ==========================================================================

/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {boolean} - True if valid
 */
function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Show error message for a field
 * @param {string} fieldId - Field ID
 * @param {string} message - Error message
 */
function showError(fieldId, message) {
  const field = document.getElementById(fieldId);
  const error = document.getElementById(`${fieldId}-error`);

  if (field) {
    field.classList.add('error');
  }

  if (error) {
    error.textContent = message;
    error.classList.add('visible');
  }
}

/**
 * Clear error for a field
 * @param {string} fieldId - Field ID
 */
function clearError(fieldId) {
  const field = document.getElementById(fieldId);
  const error = document.getElementById(`${fieldId}-error`);

  if (field) {
    field.classList.remove('error');
  }

  if (error) {
    error.textContent = '';
    error.classList.remove('visible');
  }
}

/**
 * Clear all form errors
 */
function clearAllErrors() {
  ['name', 'email', 'subject', 'message'].forEach(clearError);
}

/**
 * Validate the contact form
 * @returns {boolean} - True if form is valid
 */
function validateForm() {
  let isValid = true;
  clearAllErrors();

  const name = document.getElementById('name').value.trim();
  const email = document.getElementById('email').value.trim();
  const subject = document.getElementById('subject').value.trim();
  const message = document.getElementById('message').value.trim();

  if (!name) {
    showError('name', 'Please enter your name');
    isValid = false;
  } else if (name.length < 2) {
    showError('name', 'Name must be at least 2 characters');
    isValid = false;
  }

  if (!email) {
    showError('email', 'Please enter your email');
    isValid = false;
  } else if (!isValidEmail(email)) {
    showError('email', 'Please enter a valid email address');
    isValid = false;
  }

  if (!subject) {
    showError('subject', 'Please enter a subject');
    isValid = false;
  } else if (subject.length < 3) {
    showError('subject', 'Subject must be at least 3 characters');
    isValid = false;
  }

  if (!message) {
    showError('message', 'Please enter your message');
    isValid = false;
  } else if (message.length < 10) {
    showError('message', 'Message must be at least 10 characters');
    isValid = false;
  }

  return isValid;
}

/**
 * Initialize contact form handling
 */
function initContactForm() {
  const form = document.getElementById('contact-form');
  const success = document.getElementById('form-success');

  if (!form) return;

  // Clear errors on input
  ['name', 'email', 'subject', 'message'].forEach((fieldId) => {
    const field = document.getElementById(fieldId);
    if (field) {
      field.addEventListener('input', () => clearError(fieldId));
    }
  });

  form.addEventListener('submit', (e) => {
    e.preventDefault();

    if (validateForm()) {
      // In a real implementation, you would send the form data to a server
      // For this demo, we just show a success message

      // Hide the form submit button and show success
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span>Sending...</span>';
      }

      // Simulate sending delay
      setTimeout(() => {
        if (success) {
          success.classList.add('visible');
        }

        // Reset form
        form.reset();

        // Re-enable button
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = `
                        <span>Send Message</span>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="22" y1="2" x2="11" y2="13"></line>
                            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                        </svg>
                    `;
        }

        // Hide success message after 5 seconds
        setTimeout(() => {
          if (success) {
            success.classList.remove('visible');
          }
        }, 5000);
      }, 1000);
    }
  });
}

// ==========================================================================
// Skill Progress Animation
// ==========================================================================

/**
 * Animate skill bars when they come into view
 */
function initSkillAnimation() {
  const skillBars = document.querySelectorAll('.skill-item__progress');

  if (!skillBars.length) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const bar = entry.target;
          const progress = getComputedStyle(bar).getPropertyValue('--progress');
          bar.style.width = progress;
          observer.unobserve(bar);
        }
      });
    },
    { threshold: 0.5 }
  );

  skillBars.forEach((bar) => {
    bar.style.width = '0';
    observer.observe(bar);
  });
}

// ==========================================================================
// Section Reveal Animation
// ==========================================================================

/**
 * Reveal sections as they scroll into view
 */
function initScrollReveal() {
  const sections = document.querySelectorAll('.section');

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed');
        }
      });
    },
    {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px',
    }
  );

  sections.forEach((section) => {
    observer.observe(section);
  });
}

// ==========================================================================
// Active Navigation Link
// ==========================================================================

/**
 * Highlight current section in navigation
 */
function initActiveNavLink() {
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav__link');

  function updateActiveLink() {
    const scrollY = window.pageYOffset;

    sections.forEach((section) => {
      const sectionHeight = section.offsetHeight;
      const sectionTop = section.offsetTop - 150;
      const sectionId = section.getAttribute('id');

      if (scrollY >= sectionTop && scrollY < sectionTop + sectionHeight) {
        navLinks.forEach((link) => {
          link.classList.remove('active');
          if (link.getAttribute('href') === `#${sectionId}`) {
            link.classList.add('active');
          }
        });
      }
    });
  }

  window.addEventListener('scroll', updateActiveLink);
  updateActiveLink();
}

// ==========================================================================
// Initialize All Features
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
  // Theme toggle button
  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', toggleTheme);
  }

  // Initialize all features
  initMobileNav();
  initSmoothScroll();
  initHeaderScroll();
  initContactForm();
  initSkillAnimation();
  initScrollReveal();
  initActiveNavLink();

  console.log('Portfolio site initialized successfully! 🚀');
});
