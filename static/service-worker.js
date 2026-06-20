const CACHE_NAME = 'portal-cache-v1';
const urlsToCache = [
  '/static/assets/css/main.css',
  '/static/styles.css',
  '/static/assets/vendor/bootstrap/css/bootstrap.min.css',
  '/static/assets/vendor/bootstrap-icons/bootstrap-icons.css'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response; // Return cached asset
        }
        return fetch(event.request);
      })
  );
});
