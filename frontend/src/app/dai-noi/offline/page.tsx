import React from "react";
import type { Metadata } from "next";
import OfflinePageClient from "./OfflinePageClient";

export const metadata: Metadata = {
  title: "Chế Độ Ngoại Tuyến & Xuất Phiếu In Ấn A4 — Đại Nội Huế | Lưu Niên",
  description:
    "Trung tâm học tập ngoại tuyến (Offline PWA) và xuất phiếu học tập thực địa 4 cột M-E-E chuẩn A4 theo Công văn 5512/BGDĐT cho giáo viên và học sinh.",
  openGraph: {
    title: "Ngoại Tuyến & Phiếu In Di Sản — STTTNNĐ Đại Nội Huế",
    description: "Học tập di sản không cần mạng Internet và xuất phiếu in ấn thực địa 1-click.",
  },
};

export default function OfflinePage() {
  return <OfflinePageClient />;
}
