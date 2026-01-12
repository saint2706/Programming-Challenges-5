const accordionHeaders = document.querySelectorAll('.accordion-header');
const searchInput = document.getElementById('searchInput');
const accordionItems = document.querySelectorAll('.accordion-item');

// Accordion toggle
accordionHeaders.forEach(header => {
    header.addEventListener('click', () => {
        const isExpanded = header.getAttribute('aria-expanded') === 'true';

        // Close all other items (single-open mode)
        accordionHeaders.forEach(h => {
            h.setAttribute('aria-expanded', 'false');
        });

        // Toggle current item
        header.setAttribute('aria-expanded', !isExpanded);
    });

    // Keyboard navigation
    header.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            header.click();
        }
    });
});

// Search functionality
searchInput.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();

    accordionItems.forEach(item => {
        const text = item.textContent.toLowerCase();
        if (text.includes(query)) {
            item.classList.remove('hidden');
        } else {
            item.classList.add('hidden');
        }
    });
});
