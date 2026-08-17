const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://lms.histolab.icu";

// Public, indexable routes. Authed/private surfaces are intentionally excluded.
const URNS = [
  "cao-dinh",
  "nhan-dinh",
  "chuong-dinh",
  "anh-dinh",
  "nghi-dinh",
  "thuan-dinh",
  "tuyen-dinh",
  "du-dinh",
  "huyen-dinh",
];

const ROUTES = [
  { path: "/", priority: 1.0, changeFrequency: "weekly" },
  { path: "/cuu-dinh", priority: 0.95, changeFrequency: "weekly" },
  { path: "/atlas", priority: 0.95, changeFrequency: "weekly" },
  { path: "/map", priority: 0.8, changeFrequency: "monthly" },
  { path: "/timeline", priority: 0.8, changeFrequency: "monthly" },
  { path: "/stories", priority: 0.8, changeFrequency: "weekly" },
  { path: "/sources", priority: 0.7, changeFrequency: "monthly" },
  { path: "/explore/connections", priority: 0.7, changeFrequency: "monthly" },
  { path: "/explore", priority: 0.7, changeFrequency: "weekly" },
  { path: "/vr360", priority: 0.5, changeFrequency: "monthly" },
  ...URNS.flatMap((urn) => [
    { path: `/cuu-dinh/${urn}`, priority: 0.85, changeFrequency: "monthly" },
    ...Array.from({ length: 17 }, (_, index) => ({
      path: `/atlas/${urn}/${urn}-${String(index + 2).padStart(2, "0")}`,
      priority: 0.65,
      changeFrequency: "monthly",
    })),
  ]),
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
