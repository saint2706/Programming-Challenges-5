const targetDateInput = document.getElementById('targetDate');
const startBtn = document.getElementById('startBtn');
const daysEl = document.getElementById('days');
const hoursEl = document.getElementById('hours');
const minutesEl = document.getElementById('minutes');
const secondsEl = document.getElementById('seconds');
const messageEl = document.getElementById('message');

let countdownInterval;

// Start countdown
startBtn.addEventListener('click', () => {
    const targetDate = new Date(targetDateInput.value).getTime();

    if (!targetDate || isNaN(targetDate)) {
        messageEl.textContent = 'Please select a valid date and time';
        return;
    }

    if (countdownInterval) clearInterval(countdownInterval);

    countdownInterval = setInterval(() => updateCountdown(targetDate), 1000);
    updateCountdown(targetDate);
    messageEl.textContent = '';
});

// Update countdown
function updateCountdown(targetDate) {
    const now = new Date().getTime();
    const distance = targetDate - now;

    if (distance < 0) {
        clearInterval(countdownInterval);
        daysEl.textContent = '00';
        hoursEl.textContent = '00';
        minutesEl.textContent = '00';
        secondsEl.textContent = '00';
        messageEl.textContent = '🎉 Time\'s up!';
        return;
    }

    const days = Math.floor(distance / (1000 * 60 * 60 * 24));
    const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((distance % (1000 * 60)) / 1000);

    daysEl.textContent = String(days).padStart(2, '0');
    hoursEl.textContent = String(hours).padStart(2, '0');
    minutesEl.textContent = String(minutes).padStart(2, '0');
    secondsEl.textContent = String(seconds).padStart(2, '0');
}
