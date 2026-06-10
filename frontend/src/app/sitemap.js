const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://lms.histolab.icu";

// Public, indexable routes. Authed/private surfaces are intentionally excluded.
const ROUTES = [
  { path: "/", priority: 1.0, changeFrequency: "weekly" },
  { path: "/explore", priority: 0.9, changeFrequency: "weekly" },
  { path: "/vr360", priority: 0.7, changeFrequency: "monthly" },
  { path: "/cuu-dinh", priority: 0.7, changeFrequency: "monthly" },
  { path: "/trails", priority: 0.6, changeFrequency: "monthly" },
  { path: "/login", priority: 0.3, changeFrequency: "yearly" },
];

export default function sitemap() {
  const now = new Date();
  return ROUTES.map((r) => ({
    url: `${SITE_URL}${r.path}`,
    lastModified: now,
    changeFrequency: r.changeFrequency,
    priority: r.priority,
  }));
}
