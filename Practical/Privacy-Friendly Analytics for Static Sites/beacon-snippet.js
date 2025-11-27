// Lightweight beacon for static sites (no cookies, CORS-friendly)
(function () {
  const endpoint = 'https://your-domain.example.com/pageviews';
  const payload = {
    url: window.location.href,
    referrer: document.referrer || null,
    timestamp: new Date().toISOString(),
    user_agent: navigator.userAgent,
  };

  const body = JSON.stringify(payload);

  if (navigator.sendBeacon) {
    const blob = new Blob([body], { type: 'application/json' });
    navigator.sendBeacon(endpoint, blob);
  } else {
    fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
      credentials: 'omit',
      cache: 'no-store',
      keepalive: true,
      mode: 'cors',
    }).catch(() => {
      /* silently ignore */
    });
  }
})();
