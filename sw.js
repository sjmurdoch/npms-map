/* Service worker: keeps the NPMS TL3443 field map usable with no signal.
   The app shell and the georeferenced sheet are precached on install, so the
   overlay, plot positions and live GPS all work offline. OSM base tiles are
   cached opportunistically as they are viewed, and in bulk via "Save offline". */

const VERSION = "v5";
const SHELL = "npms-tl3443-shell-" + VERSION;
const TILES = "npms-tl3443-tiles-v1";        // tiles survive shell upgrades

// Big, effectively immutable assets: always served from cache when present, so a
// field phone never re-downloads the 1.5 MB sheet over mobile data.
const IMMUTABLE = /\.(png|webmanifest)$|vendor\//;

const SHELL_FILES = [
  "./",
  "index.html",
  "app.js",
  "geo.js",
  "tl3443_overlay.png",
  "manifest.webmanifest",
  "vendor/leaflet.js",
  "vendor/leaflet.css",
  "icons/icon-180.png",
  "icons/icon-192.png",
  "icons/icon-512.png"
];

const TILE_HOSTS = ["tile.openstreetmap.org", "a.tile.openstreetmap.org",
                    "b.tile.openstreetmap.org", "c.tile.openstreetmap.org"];

// 1x1 transparent PNG, shown where a tile was never cached
const BLANK = Uint8Array.from(atob(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
), c => c.charCodeAt(0));

// Shell entries are keyed by URL with any query string removed, so that a
// request for "?v=whatever" both matches and *updates* the same cached entry.
function shellKey(u) {
  const x = new URL(u, self.location);
  x.search = "";
  x.hash = "";
  return x.href;
}

self.addEventListener("install", (e) => {
  e.waitUntil((async () => {
    const cache = await caches.open(SHELL);
    // cache: "reload" bypasses the HTTP cache, which on GitHub Pages would
    // otherwise hand back the previous deploy's index.html for several minutes.
    await Promise.all(SHELL_FILES.map(async (u) => {
      const res = await fetch(new Request(u, { cache: "reload" }));
      if (res && res.ok) await cache.put(shellKey(u), res);
    }));
    await self.skipWaiting();
  })());
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((k) => k !== SHELL && k !== TILES).map((k) => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);

  if (TILE_HOSTS.includes(url.hostname)) {
    e.respondWith(
      caches.open(TILES).then(async (cache) => {
        const hit = await cache.match(e.request, { ignoreVary: true, ignoreSearch: true });
        if (hit) return hit;
        try {
          const res = await fetch(e.request);
          if (res && (res.ok || res.type === "opaque")) cache.put(e.request, res.clone());
          return res;
        } catch (err) {
          return new Response(BLANK, { headers: { "Content-Type": "image/png" } });
        }
      })
    );
    return;
  }

  if (url.origin === self.location.origin) {
    e.respondWith(
      caches.open(SHELL).then(async (cache) => {
        const key = shellKey(e.request.url);
        const hit = await cache.match(key);

        if (hit && IMMUTABLE.test(url.pathname)) return hit;   // cache-first

        // stale-while-revalidate: instant offline start, picks up deploys next load
        const net = fetch(e.request).then((res) => {
          if (res && res.ok) cache.put(key, res.clone());
          return res;
        }).catch(() => null);

        if (hit) { e.waitUntil(net); return hit; }
        return (await net) || cache.match(shellKey("index.html"));
      })
    );
  }
});

self.addEventListener("message", async (e) => {
  const msg = e.data || {};
  const send = (m) => e.source && e.source.postMessage(m);

  if (msg.type === "STATUS") {
    const cache = await caches.open(TILES);
    send({ type: "STATUS", tiles: (await cache.keys()).length });
    return;
  }

  if (msg.type === "PREFETCH") {
    const cache = await caches.open(TILES);
    const urls = msg.urls || [];
    let done = 0, failed = 0;

    // Modest concurrency: this is a one-off personal download of a few hundred
    // tiles, and OSM's tile policy asks that bulk fetching stays gentle.
    const CONCURRENCY = 2;
    const queue = urls.slice();

    async function worker() {
      while (queue.length) {
        const u = queue.shift();
        try {
          if (!(await cache.match(u, { ignoreVary: true }))) {
            const res = await fetch(u, { mode: "cors", cache: "no-cache" });
            if (res && res.ok) await cache.put(u, res.clone());
            else failed++;
          }
        } catch (err) { failed++; }
        done++;
        if (done % 5 === 0 || done === urls.length) {
          send({ type: "PROGRESS", done, total: urls.length });
        }
      }
    }

    await Promise.all(Array.from({ length: CONCURRENCY }, worker));
    send({ type: "DONE", tiles: (await cache.keys()).length, failed });
  }
});
