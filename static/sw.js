// ConnectHub PWA — simple offline cache (real-world app-like)
const CACHE = 'connecthub-v1';
const URLS = ['/', '/static/css/style.css', '/static/js/main.js', '/static/manifest.json'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(URLS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const req = e.request;
  // Only cache GET, same-origin navigation + static
  if (req.method !== 'GET' || new URL(req.url).origin !== location.origin) return;
  // Never cache /admin /api POST side-effects — just pass through
  if (req.url.includes('/api/') || req.url.includes('/admin/')) return;
  e.respondWith(
    caches.match(req).then(cached => {
      const fetchPromise = fetch(req).then(res => {
        if (res.ok) caches.open(CACHE).then(c => c.put(req, res.clone()));
        return res;
      }).catch(() => cached);
      return cached || fetchPromise;
    })
  );
});
