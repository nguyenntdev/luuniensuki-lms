import React from "react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getTrailBySlug, IMPERIAL_TRAILS } from "@/lib/imperial/trails-data";
import TrailPlayerClient from "./TrailPlayerClient";

export async function generateStaticParams() {
  const slugs = IMPERIAL_TRAILS.map((trail) => ({
    slug: trail.slug,
  }));
  slugs.push({ slug: "truc-dung-dao-va-quyen-luc" });
  return slugs;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const trail = getTrailBySlug(slug);

  if (!trail) {
    return {
      title: "Không tìm thấy tuyến đường | Lưu Niên",
    };
  }

  return {
    title: `${trail.title} — Tuyến học tập Đại Nội | Lưu Niên`,
    description: trail.description,
    openGraph: {
      title: `${trail.title} — Khảo sát di sản Đại Nội Huế`,
      description: trail.description,
      images: [trail.cover_image],
    },
  };
}

export default async function TrailDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const trail = getTrailBySlug(slug);

  if (!trail) {
    notFound();
  }

  return <TrailPlayerClient trail={trail} />;
}
