const billingToggle = document.getElementById('billingToggle');
const prices = document.querySelectorAll('.price');
const monthlyLabel = document.getElementById('monthlyLabel');
const annualLabel = document.getElementById('annualLabel');

// Handle billing toggle
billingToggle.addEventListener('change', (e) => {
    const isAnnual = e.target.checked;

    // Update labels
    if (isAnnual) {
        monthlyLabel.classList.remove('active');
        annualLabel.classList.add('active');
    } else {
        monthlyLabel.classList.add('active');
        annualLabel.classList.remove('active');
    }

    // Update prices
    prices.forEach(priceElement => {
        const monthly = priceElement.dataset.monthly;
        const annual = priceElement.dataset.annual;
        const newPrice = isAnnual ? annual : monthly;

        // Add animation
        priceElement.classList.add('animating');

        // Update price
        setTimeout(() => {
            priceElement.textContent = newPrice;
        }, 150);

        // Remove animation
        setTimeout(() => {
            priceElement.classList.remove('animating');
        }, 300);
    });
});

// Initialize active label
monthlyLabel.classList.add('active');
