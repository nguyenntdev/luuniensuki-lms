const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://lms.histolab.icu";

/**
 * Safe JSON serializer for JSON-LD script tags.
 * Replaces `<` with `\u003c` to prevent script breakout and XSS attacks.
 *
 * @param {unknown} data
 * @returns {string}
 */
export function safeJsonLd(data) {
  return JSON.stringify(data).replace(/</g, "\\u003c");
}

export function setPageMeta({ title, description, path } = {}) {
  if (typeof document === "undefined") return;
  if (title) document.title = title;

  if (description) {
    let meta = document.querySelector('meta[name="description"]');
    if (!meta) {
      meta = document.createElement("meta");
      meta.name = "description";
      document.head.appendChild(meta);
    }
    meta.content = description;
  }

  if (path) {
    let canonical = document.querySelector('link[rel="canonical"]');
    if (!canonical) {
      canonical = document.createElement("link");
      canonical.rel = "canonical";
      document.head.appendChild(canonical);
    }
    canonical.href = `${SITE_URL}${path.startsWith("/") ? path : `/${path}`}`;
  }
}
