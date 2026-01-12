import "./style.css";

const API_KEY = "e42ea32d5f05bb14013e5a95250c825b";
const API_BASE = "https://api.openweathermap.org/data/2.5";

let units = "metric"; // or 'imperial'

const app = document.getElementById("app");

// Render app
function render(weatherData = null, forecastData = null, error = null) {
  app.innerHTML = `
        <div class="container">
            <header class="header">
                <h1>🌤️ Weather Dashboard</h1>
                <div class="search-box">
                    <input type="text" id="cityInput" placeholder="Search for a city..." />
                    <button id="searchBtn">Search</button>
                    <button id="locationBtn" title="Use my location">📍</button>
                </div>
                <div class="units-toggle">
                    <button class="unit-btn ${units === "metric" ? "active" : ""}" data-unit="metric">°C</button>
                    <button class="unit-btn ${units === "imperial" ? "active" : ""}" data-unit="imperial">°F</button>
                </div>
            </header>

            ${error ? `<div class="error">${error}</div>` : ""}

            ${
              weatherData
                ? renderCurrentWeather(weatherData)
                : `
                <div class="placeholder">
                    <p>🔍 Search for a city or use your location to see the weather</p>
                </div>
            `
            }

            ${forecastData ? renderForecast(forecastData) : ""}
        </div>
    `;

  attachEventListeners();
}

// Render current weather
function renderCurrentWeather(data) {
  const temp = Math.round(data.main.temp);
  const feelsLike = Math.round(data.main.feels_like);
  const tempUnit = units === "metric" ? "°C" : "°F";
  const windUnit = units === "metric" ? "m/s" : "mph";

  return `
        <div class="current-weather">
            <div class="weather-main">
                <div class="location">
                    <h2>${data.name}, ${data.sys.country}</h2>
                    <p class="date">${formatDate(new Date())}</p>
                </div>
                <div class="temperature">
                    <div class="temp-value">${temp}${tempUnit}</div>
                    <div class="weather-icon">${getWeatherIcon(data.weather[0].icon)}</div>
                </div>
                <div class="weather-desc">${data.weather[0].description}</div>
                <div class="feels-like">Feels like ${feelsLike}${tempUnit}</div>
            </div>
            <div class="weather-details">
                <div class="detail-item">
                    <span class="detail-label">💧 Humidity</span>
                    <span class="detail-value">${data.main.humidity}%</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">💨 Wind Speed</span>
                    <span class="detail-value">${data.wind.speed} ${windUnit}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">🌡️ Pressure</span>
                    <span class="detail-value">${data.main.pressure} hPa</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">👁️ Visibility</span>
                    <span class="detail-value">${(data.visibility / 1000).toFixed(1)} km</span>
                </div>
            </div>
        </div>
    `;
}

// Render forecast
function renderForecast(data) {
  // Get one forecast per day (at 12:00)
  const dailyForecasts = data.list
    .filter((item) => item.dt_txt.includes("12:00:00"))
    .slice(0, 5);
  const tempUnit = units === "metric" ? "°C" : "°F";

  return `
        <div class="forecast">
            <h3>5-Day Forecast</h3>
            <div class="forecast-grid">
                ${dailyForecasts
                  .map(
                    (day) => `
                    <div class="forecast-card">
                        <div class="forecast-day">${formatDay(new Date(day.dt * 1000))}</div>
                        <div class="forecast-icon">${getWeatherIcon(day.weather[0].icon)}</div>
                        <div class="forecast-temp">${Math.round(day.main.temp)}${tempUnit}</div>
                        <div class="forecast-desc">${day.weather[0].main}</div>
                    </div>
                `,
                  )
                  .join("")}
            </div>
        </div>
    `;
}

// Attach event listeners
function attachEventListeners() {
  const searchBtn = document.getElementById("searchBtn");
  const cityInput = document.getElementById("cityInput");
  const locationBtn = document.getElementById("locationBtn");
  const unitBtns = document.querySelectorAll(".unit-btn");

  searchBtn?.addEventListener("click", () => searchCity(cityInput.value));
  cityInput?.addEventListener("keypress", (e) => {
    if (e.key === "Enter") searchCity(cityInput.value);
  });
  locationBtn?.addEventListener("click", getCurrentLocation);
  unitBtns.forEach((btn) => {
    btn.addEventListener("click", () => toggleUnits(btn.dataset.unit));
  });
}

// Search city
async function searchCity(city) {
  if (!city.trim()) return;

  try {
    const weatherData = await fetchWeather(
      `${API_BASE}/weather?q=${city}&units=${units}&appid=${API_KEY}`,
    );
    const forecastData = await fetchWeather(
      `${API_BASE}/forecast?q=${city}&units=${units}&appid=${API_KEY}`,
    );
    render(weatherData, forecastData);
  } catch (error) {
    render(null, null, `City not found. Please try again.`);
  }
}

// Get current location
function getCurrentLocation() {
  if (!navigator.geolocation) {
    render(null, null, "Geolocation is not supported by your browser");
    return;
  }

  navigator.geolocation.getCurrentPosition(
    async (position) => {
      const { latitude, longitude } = position.coords;
      try {
        const weatherData = await fetchWeather(
          `${API_BASE}/weather?lat=${latitude}&lon=${longitude}&units=${units}&appid=${API_KEY}`,
        );
        const forecastData = await fetchWeather(
          `${API_BASE}/forecast?lat=${latitude}&lon=${longitude}&units=${units}&appid=${API_KEY}`,
        );
        render(weatherData, forecastData);
      } catch (error) {
        render(null, null, "Unable to fetch weather data");
      }
    },
    () => {
      render(null, null, "Unable to retrieve your location");
    },
  );
}

// Toggle units
async function toggleUnits(newUnits) {
  units = newUnits;

  // Get current city from display (if any)
  const locationHeader = document.querySelector(".location h2");
  if (locationHeader) {
    const cityName = locationHeader.textContent.split(",")[0];
    await searchCity(cityName);
  } else {
    render();
  }
}

// Fetch weather data
async function fetchWeather(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error("Weather data not available");
  return response.json();
}

// Get weather icon
function getWeatherIcon(iconCode) {
  const icons = {
    "01d": "☀️",
    "01n": "🌙",
    "02d": "⛅",
    "02n": "☁️",
    "03d": "☁️",
    "03n": "☁️",
    "04d": "☁️",
    "04n": "☁️",
    "09d": "🌧️",
    "09n": "🌧️",
    "10d": "🌦️",
    "10n": "🌧️",
    "11d": "⛈️",
    "11n": "⛈️",
    "13d": "❄️",
    "13n": "❄️",
    "50d": "🌫️",
    "50n": "🌫️",
  };
  return icons[iconCode] || "🌤️";
}

// Format date
function formatDate(date) {
  return date.toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

// Format day
function formatDay(date) {
  return date.toLocaleDateString("en-US", { weekday: "short" });
}

// Initial render
render();
