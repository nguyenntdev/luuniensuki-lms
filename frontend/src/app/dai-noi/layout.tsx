import React from "react";
import type { Metadata } from "next";
import ImperialHeader from "@/components/imperial/shell/ImperialHeader";
import ImperialMobileNav from "@/components/imperial/shell/ImperialMobileNav";
import SkipToContent from "@/components/imperial/a11y/SkipToContent";
import ScreenReaderAnnouncer from "@/components/imperial/a11y/ScreenReaderAnnouncer";
import ServiceWorkerRegister from "@/components/imperial/pwa/ServiceWorkerRegister";
import { FloatingAudioPlayer } from "@/components/imperial/audio/FloatingAudioPlayer";

export const metadata: Metadata = {
  title: "Đại Nội Huế — Bản đồ không ảnh học tập số | Lưu Niên",
  description:
    "Khám phá không gian kiến trúc Hoàng Thành và Tử Cấm Thành triều Nguyễn qua bản đồ không ảnh trực giao, tư liệu chính sử và bài tập nghiên cứu lịch sử.",
  manifest: "/manifest.webmanifest",
  openGraph: {
    title: "Đại Nội Huế — Bản đồ di sản số | Lưu Niên",
    description:
      "Bản đồ không ảnh học tập số tương tác trực giao các di tích Đại Nội Huế.",
  },
};

export default function ImperialLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground selection:bg-primary/20 selection:text-primary">
      {/* Skip to Content for Keyboard and Screen Reader Users (WCAG 2.2 AA) */}
      <SkipToContent targetId="imperial-main-content" />

      {/* Screen Reader Live Region Announcer for Map, Markers, and Pedagogy */}
      <ScreenReaderAnnouncer />

      {/* Universal Imperial Top Navigation */}
      <ImperialHeader />

      {/* Main Content Area */}
      <main
        id="imperial-main-content"
        tabIndex={-1}
        className="flex-1 pb-16 md:pb-0 focus:outline-none"
      >
        {children}
      </main>

      {/* Mobile Sticky Navigation Shell */}
      <ImperialMobileNav />

      {/* PWA Service Worker Registration & Offline Sync Engine */}
      <ServiceWorkerRegister />

      {/* Persistent Heritage Floating Audio Player & Synchronized Transcript */}
      <FloatingAudioPlayer />
    </div>
  );
}
