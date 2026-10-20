/**
 * Service Worker: STTTNNĐ (Lưu Niên — Đại Nội Huế) PWA & Offline Engine
 * Spec: STTT-SPEC-PWA-PRINT-001
 * 
 * Strategy:
 * 1. Cache-First: Core shell assets (HTML landing, CSS, fonts, aerial map webp/svg, icons)
 * 2. Stale-While-Revalidate: API data endpoints (/api/v1/imperial/zones, /maps/active, /sites)
 * 3. Offline Navigation Fallback: Redirect failed document navigation to /dai-noi/offline
 */

const CACHE_VERSION = "imperial-v1.0.0";
const STATIC_CACHE_NAME = `imperial-static-${CACHE_VERSION}`;
const DATA_CACHE_NAME = `imperial-data-${CACHE_VERSION}`;
const AUDIO_CACHE_NAME = `imperial-audio-${CACHE_VERSION}`;

// Core static assets to precache immediately on install
const PRECACHE_ASSETS = [
  "/dai-noi",
  "/dai-noi/offline",
  "/manifest.webmanifest",
  "/favicon.svg",
  "/favicon.ico",
  "/assets/imperial/pwa-icon.svg",
  "/assets/imperial/pwa-icon-maskable.svg",
  "/assets/imperial/dai-noi-aerial-v1.svg",
  "/assets/imperial/maps/dai-noi-aerial-v1.webp",
  "/fonts/playfair-vietnamese.woff2",
  "/fonts/playfair-latin.woff2",
  "/fonts/inter-vietnamese.woff2",
  "/fonts/inter-latin.woff2",
  "/fonts/fonts.css",
];

// Imperial API routes that should use Stale-While-Revalidate
const IMPERIAL_API_ROUTES = [
  "/api/v1/imperial/zones",
  "/api/v1/imperial/maps/active",
  "/api/v1/imperial/sites",
  "/api/v1/imperial/audio-guides",
];

// Install event: Pre-cache core shell & assets
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(STATIC_CACHE_NAME)
      .then(async (cache) => {
        // Use individual add with catch so one failing asset does not abort entire SW installation
        const cachePromises = PRECACHE_ASSETS.map(async (url) => {
          try {
            const response = await fetch(url, { credentials: "same-origin" });
            if (response.ok || response.type === "opaque") {
              await cache.put(url, response);
            }
          } catch (err) {
            console.warn(`[sw-imperial] Precache skipped for ${url}:`, err);
          }
        });
        await Promise.allSettled(cachePromises);
      })
      .then(() => {
        return self.skipWaiting();
      }),
  );
});

// Activate event: Clean up legacy caches
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (
              cacheName.startsWith("imperial-") &&
              cacheName !== STATIC_CACHE_NAME &&
              cacheName !== DATA_CACHE_NAME &&
              cacheName !== AUDIO_CACHE_NAME
            ) {
              return caches.delete(cacheName);
            }
          }),
        );
      })
      .then(() => {
        return self.clients.claim();
      }),
  );
});

// Helper: Determine if URL is an Imperial API endpoint
function isImperialApiUrl(url) {
  return IMPERIAL_API_ROUTES.some((route) => url.pathname.startsWith(route));
}

// Helper: Determine if URL is an audio asset
function isAudioRequest(url) {
  return (
    url.pathname.startsWith("/assets/imperial/audio/") ||
    url.pathname.endsWith(".mp3") ||
    url.pathname.endsWith(".m4a") ||
    url.pathname.endsWith(".wav") ||
    url.pathname.endsWith(".ogg") ||
    url.pathname.endsWith(".aac")
  );
}

// Helper: Determine if URL is a static asset (non-audio)
function isStaticAsset(url) {
  if (isAudioRequest(url)) return false;
  return (
    url.pathname.startsWith("/_next/static/") ||
    url.pathname.startsWith("/assets/imperial/") ||
    url.pathname.startsWith("/fonts/") ||
    url.pathname.endsWith(".webp") ||
    url.pathname.endsWith(".svg") ||
    url.pathname.endsWith(".woff2") ||
    url.pathname.endsWith(".png") ||
    url.pathname.endsWith(".jpg") ||
    url.pathname.endsWith(".ico")
  );
}

// Fetch event router
self.addEventListener("fetch", (event) => {
  const request = event.request;

  // Only handle GET requests
  if (request.method !== "GET") {
    return;
  }

  const url = new URL(request.url);

  // Cross-origin request bypass (unless standard CDN fonts/images)
  if (url.origin !== self.location.origin) {
    return;
  }

  // 1. Navigation Requests (HTML Pages under /dai-noi)
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((networkResponse) => {
          // If page responded ok, cache a copy in static cache for offline read
          if (networkResponse && networkResponse.ok) {
            const responseClone = networkResponse.clone();
            caches.open(STATIC_CACHE_NAME).then((cache) => {
              cache.put(request, responseClone);
            });
          }
          return networkResponse;
        })
        .catch(async () => {
          // Attempt reading requested page from cache
          const cachedPage = await caches.match(request);
          if (cachedPage) {
            return cachedPage;
          }
          // If requested page is not cached, return the offline fallback page
          const offlineFallback = await caches.match("/dai-noi/offline");
          if (offlineFallback) {
            return offlineFallback;
          }
          // Fallback to cached root landing if present
          const rootLanding = await caches.match("/dai-noi");
          if (rootLanding) {
            return rootLanding;
          }
          return new Response(
            `<!DOCTYPE html>
            <html lang="vi">
            <head><meta charset="utf-8"><title>Ngoại tuyến — Lưu Niên Đại Nội</title></head>
            <body style="font-family:sans-serif;background:#F7F2E8;color:#2a231d;padding:2rem;text-align:center;">
              <h1>Đang ở chế độ ngoại tuyến</h1>
              <p>Không thể kết nối đến máy chủ. Vui lòng kiểm tra lại đường truyền.</p>
            </body>
            </html>`,
            { headers: { "Content-Type": "text/html; charset=utf-8" } },
          );
        }),
    );
    return;
  }

  // 2. Imperial API: Stale-While-Revalidate
  if (isImperialApiUrl(url)) {
    event.respondWith(
      caches.open(DATA_CACHE_NAME).then(async (cache) => {
        const cachedResponse = await cache.match(request);

        // Fetch fresh copy in background
        const networkFetchPromise = fetch(request)
          .then((networkResponse) => {
            if (networkResponse && networkResponse.ok) {
              cache.put(request, networkResponse.clone());
            }
            return networkResponse;
          })
          .catch((err) => {
            // Network failure: we rely on cached response or return 503
            return null;
          });

        // Return cached immediately if available, otherwise await network
        if (cachedResponse) {
          return cachedResponse;
        }

        const freshResponse = await networkFetchPromise;
        if (freshResponse) {
          return freshResponse;
        }

        return new Response(
          JSON.stringify({ error: "Offline: No cached data available for this endpoint" }),
          {
            status: 503,
            headers: { "Content-Type": "application/json; charset=utf-8" },
          },
        );
      }),
    );
    return;
  }

  // 2.5 Audio Asset Requests: Dedicated Audio Cache with HTTP Range Slicing for offline playback
  if (isAudioRequest(url)) {
    event.respondWith(
      (async () => {
        const cache = await caches.open(AUDIO_CACHE_NAME);
        const cleanRequest = new Request(url.pathname, { method: "GET" });
        let cachedResponse = await cache.match(cleanRequest);

        if (!cachedResponse) {
          try {
            // Fetch full asset without range header for pristine offline caching
            const networkResponse = await fetch(cleanRequest);
            if (networkResponse && (networkResponse.ok || networkResponse.status === 200)) {
              await cache.put(cleanRequest, networkResponse.clone());
              cachedResponse = networkResponse;
            } else {
              return await fetch(request);
            }
          } catch (err) {
            return new Response(null, { status: 504, statusText: "Offline Audio Unavailable" });
          }
        }

        // Handle HTTP Range header for streaming & seeking
        const rangeHeader = request.headers.get("range");
        if (!rangeHeader) {
          return cachedResponse;
        }

        try {
          const arrayBuffer = await cachedResponse.clone().arrayBuffer();
          const totalSize = arrayBuffer.byteLength;
          const parts = rangeHeader.replace(/bytes=/, "").split("-");
          const start = parseInt(parts[0], 10) || 0;
          const end = parts[1] ? parseInt(parts[1], 10) : totalSize - 1;

          if (start >= totalSize || end >= totalSize) {
            return new Response(null, {
              status: 416,
              statusText: "Range Not Satisfiable",
              headers: { "Content-Range": `bytes */${totalSize}` },
            });
          }

          const slicedBuffer = arrayBuffer.slice(start, end + 1);
          return new Response(slicedBuffer, {
            status: 206,
            statusText: "Partial Content",
            headers: {
              "Content-Type": cachedResponse.headers.get("Content-Type") || "audio/mpeg",
              "Content-Range": `bytes ${start}-${end}/${totalSize}`,
              "Content-Length": String(slicedBuffer.byteLength),
              "Accept-Ranges": "bytes",
              "Cache-Control": "public, max-age=31536000",
            },
          });
        } catch {
          return cachedResponse;
        }
      })(),
    );
    return;
  }

  // 3. Static Assets: Cache-First with Network Fallback
  if (isStaticAsset(url)) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(request)
          .then((networkResponse) => {
            if (networkResponse && (networkResponse.ok || networkResponse.type === "opaque")) {
              const responseClone = networkResponse.clone();
              caches.open(STATIC_CACHE_NAME).then((cache) => {
                cache.put(request, responseClone);
              });
            }
            return networkResponse;
          })
          .catch((err) => {
            // Return empty fallback or null
            return new Response(null, { status: 404 });
          });
      }),
    );
    return;
  }

  // Default: Network with Cache Fallback
  event.respondWith(
    fetch(request).catch(async () => {
      const cached = await caches.match(request);
      if (cached) return cached;
      return new Response(null, { status: 504, statusText: "Offline" });
    }),
  );
});
