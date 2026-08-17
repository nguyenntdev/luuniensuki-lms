const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://lms.histolab.icu";

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
