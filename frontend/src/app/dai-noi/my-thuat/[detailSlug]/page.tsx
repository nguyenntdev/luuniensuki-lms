import type { Metadata } from "next";
import { notFound } from "next/navigation";
import type { ImperialArtDetail } from "@/lib/imperial/v51-types";
import {
  FALLBACK_ART_DETAILS,
  fetchArtDetail,
  fetchSiteArtDetails,
} from "@/lib/imperial/v51-api";
import ArtDetailClient from "./ArtDetailClient";

interface PageProps {
  params: Promise<{ detailSlug: string }>;
}

export async function generateStaticParams() {
  return FALLBACK_ART_DETAILS.map((detail) => ({
    detailSlug: detail.slug,
  }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const resolvedParams = await Promise.resolve(params);
  const detailSlug = resolvedParams.detailSlug;
  const detail = await fetchArtDetail(detailSlug);

  if (!detail) {
    return {
      title: "Không tìm thấy chi tiết mỹ thuật | Lưu Niên — Đại Nội Huế",
    };
  }

  const title = `${detail.title} — Mỹ thuật Hoàng Cung Đại Nội Huế`;
  const description =
    detail.description_observation ||
    detail.meaning_body ||
    `Khảo cứu đồ án họa tiết, điển tích lịch sử và giá trị văn hóa của ${detail.title} tại Đại Nội Huế.`;

  return {
    title,
    description,
    keywords: [
      detail.title,
      detail.motif || "",
      detail.site_name_vi || "Đại Nội Huế",
      "Mỹ thuật triều Nguyễn",
      "Điển tích cung đình Huế",
      "Di sản Huế",
    ].filter(Boolean),
    openGraph: {
      title,
      description,
      type: "article",
      images: [
        {
          url: detail.image_url || "/assets/imperial/maps/dai-noi-aerial-v1.webp",
          width: 1200,
          height: 630,
          alt: detail.title,
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [detail.image_url || "/assets/imperial/maps/dai-noi-aerial-v1.webp"],
    },
  };
}

export default async function ArtDetailPage({ params }: PageProps) {
  const resolvedParams = await Promise.resolve(params);
  const detailSlug = resolvedParams.detailSlug;
  const detail = await fetchArtDetail(detailSlug);

  if (!detail) {
    notFound();
  }

  let relatedDetails: ImperialArtDetail[] = [];
  if (detail.site_slug) {
    const siteDetails = await fetchSiteArtDetails(detail.site_slug);
    relatedDetails = siteDetails.filter((d) => d.slug !== detail.slug);
  }

  return <ArtDetailClient detail={detail} relatedDetails={relatedDetails} />;
}
