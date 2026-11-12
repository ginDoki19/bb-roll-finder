/* Service worker — makes the site work with no signal.
 *
 * Strategy depends on what is being asked for:
 *
 *   HTML (the page itself)  -> NETWORK FIRST, cache as fallback.
 *       The page has every roll number inlined in it, so "the HTML" and "the
 *       data" are the same file. Cache-first here meant a returning visitor saw
 *       yesterday's notices on their next visit and only got the new ones the
 *       visit after that — i.e. someone checking the morning a seat plan drops
 *       would be told their roll was not found. Online users must always get
 *       the live copy; offline users still fall back to the cached one, so the
 *       no-signal behaviour is unchanged.
 *
 *   Everything else (icons, manifest) -> CACHE FIRST, refreshed in background.
 *       Static and content-addressed enough that staleness does not matter.
 *
 * PDFs and cross-origin requests are never cached (too big / not ours).
 * Bump CACHE when you deploy — old caches are deleted on activate.
 */
const CACHE = "bb-roll-457c139e";
const SHELL = ["./", "./index.html", "./manifest.webmanifest",
  "./fonts/noto-sans-bengali-bengali-400-normal.woff2", "./fonts/noto-sans-bengali-bengali-600-normal.woff2",
  "./fonts/noto-sans-bengali-latin-400-normal.woff2",   "./fonts/noto-sans-bengali-latin-600-normal.woff2",
  "./fonts/noto-serif-bengali-bengali-600-normal.woff2", "./fonts/noto-serif-bengali-latin-600-normal.woff2"];

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

const isHTML = (req, url) =>
  req.mode === "navigate" ||
  (req.headers.get("accept") || "").includes("text/html") ||
  url.pathname === "/" ||
  url.pathname.endsWith(".html");

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);

  // never cache the PDFs (big) or anything cross-origin (maps embeds).
  // The Noto woff2 files ARE same-origin, so they fall through to the
  // cache-first branch below and stay available offline.
  if (url.origin !== location.origin || url.pathname.endsWith(".pdf")) return;

  if (isHTML(req, url)) {
    e.respondWith(
      fetch(req)
        .then(res => {
          if (res && res.status === 200) {
            const copy = res.clone();
            caches.open(CACHE).then(c => c.put(req, copy));
          }
          return res;
        })
        .catch(() =>                       // offline: serve the last good copy
          caches.match(req).then(hit => hit || caches.match("./index.html"))
        )
    );
    return;
  }

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
