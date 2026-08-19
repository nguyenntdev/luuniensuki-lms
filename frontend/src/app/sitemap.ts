import type { MetadataRoute } from "next";

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

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();

  const staticRoutes: MetadataRoute.Sitemap = [
    { url: `${SITE_URL}/`, lastModified: now, changeFrequency: "weekly", priority: 1.0 },
    { url: `${SITE_URL}/cuu-dinh`, lastModified: now, changeFrequency: "weekly", priority: 0.95 },
    { url: `${SITE_URL}/atlas`, lastModified: now, changeFrequency: "weekly", priority: 0.95 },
    { url: `${SITE_URL}/map`, lastModified: now, changeFrequency: "monthly", priority: 0.8 },
    { url: `${SITE_URL}/timeline`, lastModified: now, changeFrequency: "monthly", priority: 0.8 },
    { url: `${SITE_URL}/stories`, lastModified: now, changeFrequency: "weekly", priority: 0.8 },
    { url: `${SITE_URL}/sources`, lastModified: now, changeFrequency: "monthly", priority: 0.7 },
  ];

  const urnRoutes: MetadataRoute.Sitemap = URNS.map((urn) => ({
    url: `${SITE_URL}/cuu-dinh/${urn}`,
    lastModified: now,
    changeFrequency: "monthly",
    priority: 0.85,
  }));

  const reliefRoutes: MetadataRoute.Sitemap = URNS.flatMap((urn) =>
    Array.from({ length: 17 }, (_, index) => ({
      url: `${SITE_URL}/atlas/${urn}/${urn}-${String(index + 2).padStart(2, "0")}`,
      lastModified: now,
      changeFrequency: "monthly" as const,
      priority: 0.65,
    }))
  );

  return [...staticRoutes, ...urnRoutes, ...reliefRoutes];
}
