// Bump VERSION after editing any (non-demo) file; it derives the precached track.js?v= below too, so
// also bump the matching <script src="track.js?v="> in index.html to the same number.
const VERSION = "v19";
const TRACKJS = "track.js?v=" + VERSION.slice(1);
const CORE = ["./", "index.html", TRACKJS, "manifest.webmanifest", "icon.svg", "icon-192.png", "icon-512.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(CORE.map(u => new Request(u, {cache: "reload"})))).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== VERSION && k !== "demos").map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
// Demos: one fixed cache name, never bumped (a re-render gets a new content-hashed URL instead, see apply_demos.py);
// cache-first by exact URL, fetch + cache on a miss. Own URLs carrying ?v= are content-addressed too (immutable):
// same cache-first-by-exact-URL treatment, under VERSION. Everything else: network first (fresh content when
// online), fall back to the cached copy after 3 s if nothing arrived yet (keep waiting for the network if
// there's no cached copy to fall back to). Own files revalidate (cache: no-cache) so a deploy never pairs a
// new index.html with a stale track.js from the HTTP cache. Caches Google Fonts as they load.
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);
  const own = url.origin === location.origin;
  if (url.pathname.includes("/demos/")) {
    e.respondWith(caches.match(e.request).then(c => c || fetch(e.request).then(r => {
      if (r.ok || r.type === "opaque") { const copy = r.clone(); e.waitUntil(caches.open("demos").then(c => c.put(e.request, copy)).catch(() => {})); }
      return r;
    })));
    return;
  }
  if (own && url.search.includes("v=")) {
    e.respondWith(caches.match(e.request).then(c => c || fetch(e.request).then(r => {
      if (r.ok) { const copy = r.clone(); e.waitUntil(caches.open(VERSION).then(c => c.put(e.request, copy)).catch(() => {})); }
      return r;
    })));
    return;
  }
  const net = own ? fetch(e.request.url, {cache: "no-cache"}) : fetch(e.request);
  let timer;
  e.respondWith(
    Promise.race([
      net,
      new Promise(res => { timer = setTimeout(() => caches.match(e.request, {ignoreSearch: true}).then(c => c && res(c)), 3000); })
    ]).catch(() => caches.match(e.request, {ignoreSearch: true}))
  );
  // Clone before anything else touches the body, and schedule the cache write right here (synchronously, while
  // respondWith's promise above is still pending) rather than nesting it inside caches.open().then() — nesting
  // it delays the clone until after the response has already been consumed ("body is already used").
  e.waitUntil(net.then(r => {
    clearTimeout(timer);
    if (r.ok || r.type === "opaque") { const copy = r.clone(); return caches.open(VERSION).then(c => c.put(e.request, copy)); }
  }).catch(() => {}));
});

// Workout reminder push (sent by .github/workflows/reminder.yml). Tapping it opens today's workout.
self.addEventListener("push", e => {
  const d = e.data ? e.data.json() : {};
  e.waitUntil(self.registration.showNotification(d.title || "Workout time", {
    body: d.body || "Today's Desk Reset session is ready.", icon: "icon-192.png", badge: "icon-192.png", tag: "workout-reminder"
  }));
});
self.addEventListener("notificationclick", e => {
  e.notification.close();
  e.waitUntil(clients.matchAll({type: "window", includeUncontrolled: true}).then(ws => {
    const w = ws.find(x => x.url.startsWith(self.registration.scope));
    return w ? w.focus() : clients.openWindow("./#workout");
  }));
});
