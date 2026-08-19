import type { MetadataRoute } from "next";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://lms.histolab.icu";

// Public, indexable routes across Nine Dynastic Urns (Cửu Đỉnh).
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
    { url: `${SITE_URL}/`, lastModified: now, changeFrequency: "daily", priority: 1.0 },
    { url: `${SITE_URL}/cuu-dinh`, lastModified: now, changeFrequency: "weekly", priority: 0.95 },
    { url: `${SITE_URL}/atlas`, lastModified: now, changeFrequency: "weekly", priority: 0.95 },
    { url: `${SITE_URL}/map`, lastModified: now, changeFrequency: "weekly", priority: 0.9 },
    { url: `${SITE_URL}/vr360`, lastModified: now, changeFrequency: "monthly", priority: 0.85 },
    { url: `${SITE_URL}/timeline`, lastModified: now, changeFrequency: "monthly", priority: 0.85 },
    { url: `${SITE_URL}/stories`, lastModified: now, changeFrequency: "weekly", priority: 0.85 },
    { url: `${SITE_URL}/sources`, lastModified: now, changeFrequency: "monthly", priority: 0.8 },
    { url: `${SITE_URL}/explore`, lastModified: now, changeFrequency: "weekly", priority: 0.8 },
    { url: `${SITE_URL}/explore/connections`, lastModified: now, changeFrequency: "weekly", priority: 0.8 },
    { url: `${SITE_URL}/compare`, lastModified: now, changeFrequency: "monthly", priority: 0.75 },
    { url: `${SITE_URL}/collection`, lastModified: now, changeFrequency: "weekly", priority: 0.75 },
    { url: `${SITE_URL}/ai`, lastModified: now, changeFrequency: "weekly", priority: 0.75 },
  ];

  // 9 Urn profile pages (/cuu-dinh/cao-dinh)
  const urnProfileRoutes: MetadataRoute.Sitemap = URNS.map((urn) => ({
    url: `${SITE_URL}/cuu-dinh/${urn}`,
    lastModified: now,
    changeFrequency: "weekly",
    priority: 0.9,
  }));

  // 9 Urn 3D interactive viewer pages (/urns/cao-dinh)
  const urn3dRoutes: MetadataRoute.Sitemap = URNS.map((urn) => ({
    url: `${SITE_URL}/urns/${urn}`,
    lastModified: now,
    changeFrequency: "weekly",
    priority: 0.9,
  }));

  // 162 Bronze Relief Motif individual dossier pages (/atlas/cao-dinh/cao-dinh-02 ...)
  const reliefRoutes: MetadataRoute.Sitemap = URNS.flatMap((urn) =>
    Array.from({ length: 18 }, (_, index) => {
      const numStr = String(index + 1).padStart(2, "0");
      const reliefSlug = `${urn}-${numStr}`;
      return {
        url: `${SITE_URL}/atlas/${urn}/${reliefSlug}`,
        lastModified: now,
        changeFrequency: "monthly" as const,
        priority: 0.75,
      };
    })
  );

  return [...staticRoutes, ...urnProfileRoutes, ...urn3dRoutes, ...reliefRoutes];
}
