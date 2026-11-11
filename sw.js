/* Service worker — makes the site work with no signal.
 *
 * Strategy: cache-first for the shell, network-in-the-background to refresh.
 * The whole app is one 79 KB file, so "the shell" is literally everything the
 * search box needs. A candidate standing outside an exam centre on a congested
 * Dhaka mobile network gets an instant answer from cache, and the next time
 * they have signal the cache silently updates.
 *
 * Bump CACHE when you deploy — old caches are deleted on activate.
 */
const CACHE = "bb-roll-v1";
const SHELL = ["./", "./index.html", "./manifest.webmanifest"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);

  // never cache the PDFs (big) or anything cross-origin (maps, fonts)
  if (url.origin !== location.origin || url.pathname.endsWith(".pdf")) return;

  e.respondWith(
    caches.match(req).then(hit => {
      const net = fetch(req).then(res => {
        if (res && res.status === 200) {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put(req, copy));
        }
        return res;
      }).catch(() => hit);           // offline: fall back to whatever we have
      return hit || net;             // cache-first, refresh behind the scenes
    })
  );
});
