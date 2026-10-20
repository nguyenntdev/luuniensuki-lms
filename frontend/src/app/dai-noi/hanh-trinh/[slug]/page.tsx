import React from "react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import JourneyPlayerClient from "./JourneyPlayerClient";
import { IMPERIAL_TRAILS } from "@/lib/imperial/trails-data";

interface JourneyPageProps {
  params: Promise<{
    slug: string;
  }>;
}

export async function generateMetadata({
  params,
}: JourneyPageProps): Promise<Metadata> {
  const { slug } = await params;
  const trail = IMPERIAL_TRAILS.find((t) => t.slug === slug);

  if (!trail) {
    return {
      title: "Hành Trình Khám Phá — Đại Nội Huế | Lưu Niên",
      description: "Hành trình điều tra di sản 35-45 phút tại Đại Nội Huế.",
    };
  }

  return {
    title: `${trail.title} (35-45p) — Hành Trình Khảo Sát | Lưu Niên`,
    description: trail.description,
  };
}

export default async function JourneyPage({ params }: JourneyPageProps) {
  const { slug } = await params;
  const trail = IMPERIAL_TRAILS.find((t) => t.slug === slug);

  if (!trail) {
    notFound();
  }

  return <JourneyPlayerClient trail={trail} />;
}
