import React from "react";
import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { GoogleMapsImperial } from "@/components/imperial/map/GoogleMapsImperial";

export const metadata: Metadata = {
  title: "Bản đồ không ảnh toàn màn hình — Đại Nội Huế | Lưu Niên",
  description:
    "Trải nghiệm bản đồ Google Maps và không ảnh Đại Nội Huế toàn màn hình độ phân giải cao, hỗ trợ điều hướng trực giao và tra cứu di tích chuyên sâu.",
};

export const revalidate = 60;

export default async function DaiNoiMapFullscreenPage() {
  return (
    <div className="min-h-screen w-full bg-stone-950 p-2 md:p-6 flex flex-col justify-center relative">
      <div className="absolute top-4 left-4 md:left-8 z-30 pointer-events-none">
        <Link
          href="/dai-noi"
          className="pointer-events-auto inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-stone-900/90 border border-stone-800 text-stone-200 text-xs font-semibold shadow-xl hover:bg-stone-800 backdrop-blur-md"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Trở về Cổng Đại Nội</span>
        </Link>
      </div>

      <GoogleMapsImperial
        className="h-[calc(100vh-80px)] min-h-[600px] w-full"
        showZoneFilter={true}
        showMapTypeSelector={true}
        showZoomControls={true}
        showFullscreenToggle={true}
      />
    </div>
  );
}
