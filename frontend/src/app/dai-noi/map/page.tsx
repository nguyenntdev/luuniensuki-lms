import React from "react";
import type { Metadata } from "next";
import { DaiNoiClient } from "../DaiNoiClient";
import { fetchActiveMap, fetchSites, fetchZones } from "@/lib/imperial/map-api";

export const metadata: Metadata = {
  title: "Bản đồ không ảnh toàn màn hình — Đại Nội Huế | Lưu Niên",
  description:
    "Trải nghiệm bản đồ không ảnh Đại Nội Huế toàn màn hình độ phân giải cao, hỗ trợ điều hướng trực giao và tra cứu di tích chuyên sâu.",
};

export const revalidate = 60;

export default async function DaiNoiMapFullscreenPage() {
  const [activeMap, zones, sites] = await Promise.all([
    fetchActiveMap(),
    fetchZones(),
    fetchSites(),
  ]);

  return (
    <DaiNoiClient
      initialActiveMap={activeMap}
      initialZones={zones}
      initialSites={sites}
      fullscreen={true}
    />
  );
}
