// Modal functionality
const openModalBtn = document.getElementById("openModal");
const openSmallModalBtn = document.getElementById("openSmallModal");
const demoModal = document.getElementById("demoModal");
const smallModal = document.getElementById("smallModal");
const closeModalBtn = document.getElementById("closeModal");
const cancelModalBtn = document.getElementById("cancelModal");
const modalOverlay = document.getElementById("modalOverlay");
const closeSmallModalBtn = document.getElementById("closeSmallModal");
const smallModalOverlay = document.getElementById("smallModalOverlay");

// Open main modal
openModalBtn.addEventListener("click", () => {
  demoModal.classList.add("is-active");
  document.body.style.overflow = "hidden";
});

// Open small modal
openSmallModalBtn.addEventListener("click", () => {
  smallModal.classList.add("is-active");
  document.body.style.overflow = "hidden";
});

// Close main modal
function closeMainModal() {
  demoModal.classList.remove("is-active");
  document.body.style.overflow = "";
}

closeModalBtn.addEventListener("click", closeMainModal);
cancelModalBtn.addEventListener("click", closeMainModal);
modalOverlay.addEventListener("click", closeMainModal);

// Close small modal
function closeSmallModalFunc() {
  smallModal.classList.remove("is-active");
  document.body.style.overflow = "";
}

closeSmallModalBtn.addEventListener("click", closeSmallModalFunc);
smallModalOverlay.addEventListener("click", closeSmallModalFunc);

// Close modals with ESC key
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    if (demoModal.classList.contains("is-active")) {
      closeMainModal();
    }
    if (smallModal.classList.contains("is-active")) {
      closeSmallModalFunc();
    }
  }
});

// Smooth scroll for navigation
document.querySelectorAll(".navbar__link").forEach((link) => {
  link.addEventListener("click", (e) => {
    e.preventDefault();
    const targetId = link.getAttribute("href");
    const targetElement = document.querySelector(targetId);
    if (targetElement) {
      const navbarHeight = document.querySelector(".navbar").offsetHeight;
      const targetPosition = targetElement.offsetTop - navbarHeight - 20;
      window.scrollTo({
        top: targetPosition,
        behavior: "smooth",
      });
    }
  });
});

// Copy code snippets (if we add copy buttons later)
console.log(
  "%cPrism UI Component Library",
  "color: #3b82f6; font-size: 18px; font-weight: bold;",
);
console.log(
  "%cBuilt with BEM methodology and CSS custom properties",
  "color: #6b7280; font-size: 12px;",
);
