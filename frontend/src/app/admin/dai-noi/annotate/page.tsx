import React from "react";
import type { Metadata } from "next";
import { AnnotationStudioClient } from "./AnnotationStudioClient";
import {
  fetchAdminAnnotations,
  fetchAdminMaps,
  fetchSites,
} from "@/lib/imperial/map-api";

export const metadata: Metadata = {
  title: "Studio Biên tập Bản đồ Không ảnh Đại Nội Huế | Quản trị Lưu Niên",
  description:
    "Công cụ biên tập trực giao, gắn tọa độ di tích UV và kiểm định bản quyền bản đồ không ảnh Đại Nội Huế.",
};

export const dynamic = "force-dynamic";

export default async function AnnotateStudioPage() {
  const [maps, sites] = await Promise.all([
    fetchAdminMaps(),
    fetchSites(),
  ]);

  const activeMap = maps[0] || null;
  const annotations = activeMap
    ? await fetchAdminAnnotations(activeMap.id)
    : [];

  return (
    <AnnotationStudioClient
      initialMap={activeMap}
      initialAnnotations={annotations}
      initialSites={sites}
    />
  );
}
