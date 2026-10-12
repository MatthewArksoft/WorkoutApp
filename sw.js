// Bump VERSION after editing any file so clients pick up the change (and the ?v= on track.js in index.html).
const VERSION = "v11";
const CORE = ["./", "index.html", "track.js", "manifest.webmanifest", "icon.svg", "icon-192.png", "icon-512.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(CORE.map(u => new Request(u, {cache: "reload"})))).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== VERSION).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
// Network first (fresh content when online), fall back to cache offline. Caches Google Fonts as they load.
// Own files revalidate (cache: no-cache) so a deploy never pairs a new index.html with a stale track.js from the HTTP cache.
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  const own = new URL(e.request.url).origin === location.origin;
  e.respondWith(
    (own ? fetch(e.request.url, {cache: "no-cache"}) : fetch(e.request)).then(r => {
      if (r.ok || r.type === "opaque") { const copy = r.clone(); caches.open(VERSION).then(c => c.put(e.request, copy)); }
      return r;
    }).catch(() => caches.match(e.request, {ignoreSearch: true}))
  );
});
