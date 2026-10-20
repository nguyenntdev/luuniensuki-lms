import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { fetchSiteDossier, fetchSites } from "@/lib/imperial/map-api";
import { fetchSiteLearningMedia } from "@/lib/imperial/v51-api";
import MonumentDossierClient from "./MonumentDossierClient";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateStaticParams() {
  const sites = await fetchSites();
  return sites.map((site) => ({
    slug: site.slug,
  }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const resolvedParams = await Promise.resolve(params);
  const slug = resolvedParams.slug;
  const dossier = await fetchSiteDossier(slug);

  if (!dossier) {
    return {
      title: "Không tìm thấy công trình | Lưu Niên — Đại Nội Huế",
    };
  }

  const { site, zone } = dossier;
  const title = `${site.name_vi} — Hồ sơ di tích Đại Nội Huế`;
  const description =
    site.historical_summary ||
    `Khảo cứu lịch sử, không gian kiến trúc, sử liệu và nhiệm vụ học tập của ${site.name_vi} trong Hoàng Thành Huế.`;

  return {
    title,
    description,
    keywords: [
      site.name_vi,
      "Đại Nội Huế",
      "Hoàng Thành Huế",
      "Tử Cấm Thành",
      zone?.title_vi || "",
      "Di sản Huế",
      "Học tập lịch sử",
    ].filter(Boolean),
    openGraph: {
      title,
      description,
      type: "article",
      images: [
        {
          url: "/assets/imperial/maps/dai-noi-aerial-v1.webp",
          width: 4096,
          height: 3072,
          alt: `Không ảnh và vị trí của ${site.name_vi} tại Đại Nội Huế`,
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: ["/assets/imperial/maps/dai-noi-aerial-v1.webp"],
    },
  };
}

export default async function MonumentDossierPage({ params }: PageProps) {
  const resolvedParams = await Promise.resolve(params);
  const slug = resolvedParams.slug;
  const dossier = await fetchSiteDossier(slug);

  if (!dossier) {
    notFound();
  }

  const { site, zone, guiding_question } = dossier;

  // JSON-LD structured data for search engines & heritage indexing
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "LandmarksOrHistoricalBuildings",
    name: site.name_vi,
    alternateName: site.name_han_nom,
    description: site.historical_summary,
    containedInPlace: {
      "@type": "Place",
      name: "Đại Nội Huế (Quần thể Di tích Cố đô Huế)",
    },
    geo: {
      "@type": "GeoCoordinates",
      latitude: 16.4686,
      longitude: 107.5776,
    },
    educationalUse: "Lịch sử và Giáo dục địa phương THPT",
    about: {
      "@type": "Thing",
      name: guiding_question,
    },
  };

  const learningMedia = await fetchSiteLearningMedia(slug);

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <MonumentDossierClient
        initialData={dossier}
        initialLearningMedia={learningMedia}
      />
    </>
  );
}
