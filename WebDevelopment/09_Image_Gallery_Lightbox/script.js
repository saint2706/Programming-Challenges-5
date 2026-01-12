const gallery = document.getElementById("gallery");
const lightbox = document.getElementById("lightbox");
const lightboxImg = document.getElementById("lightboxImg");
const lightboxCaption = document.getElementById("lightboxCaption");
const closeBtn = document.getElementById("closeBtn");
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");

let currentIndex = 0;
const images = Array.from(document.querySelectorAll(".gallery-item"));

// Open lightbox
gallery.addEventListener("click", (e) => {
  const item = e.target.closest(".gallery-item");
  if (!item) return;

  currentIndex = parseInt(item.dataset.index);
  showImage(currentIndex);
  lightbox.classList.add("active");
});

// Show image
function showImage(index) {
  const item = images[index];
  const placeholder = item.querySelector(".placeholder-img");
  const bg = placeholder.style.background;
  const text = placeholder.querySelector("span").textContent;

  lightboxImg.style.background = bg;
  lightboxImg.innerHTML = `<span style="padding: 4rem;">${text}</span>`;
  lightboxCaption.textContent = `${text} (${index + 1} of ${images.length})`;
}

// Close lightbox
closeBtn.addEventListener("click", () => lightbox.classList.remove("active"));
lightbox.addEventListener("click", (e) => {
  if (e.target === lightbox) lightbox.classList.remove("active");
});

// Navigation
prevBtn.addEventListener("click", () => {
  currentIndex = (currentIndex - 1 + images.length) % images.length;
  showImage(currentIndex);
});

nextBtn.addEventListener("click", () => {
  currentIndex = (currentIndex + 1) % images.length;
  showImage(currentIndex);
});

// Arrow keys
document.addEventListener("keydown", (e) => {
  if (!lightbox.classList.contains("active")) return;
  if (e.key === "Escape") lightbox.classList.remove("active");
  if (e.key === "ArrowLeft") prevBtn.click();
  if (e.key === "ArrowRight") nextBtn.click();
});
