import React, { Suspense } from "react";
import type { Metadata } from "next";
import CertificateClient from "./CertificateClient";

export const metadata: Metadata = {
  title: "Giấy Chứng Nhận Khảo Cứu Di Sản Hoàng Thành Huế | Lưu Niên",
  description:
    "Bản chứng nhận vinh danh hoàng triều phong cách sắc phong triều Nguyễn dành cho học sinh hoàn thành khảo sát, giải mã di tích Đại Nội Huế.",
  openGraph: {
    title: "Chứng Nhận Khảo Cứu Di Sản Cố Đô Huế — Lưu Niên",
    description:
      "Vinh danh thành tích điền dã khảo cứu di sản Cố đô Huế với hoa văn mộc son hoàng triều và mã QR tra cứu trực tuyến.",
  },
};

export default function CertificatePage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#F7F2E8] flex items-center justify-center p-6">
          <div className="flex flex-col items-center gap-3">
            <div className="size-10 animate-spin rounded-full border-2 border-amber-600 border-t-transparent" />
            <span className="font-serif text-sm font-semibold text-amber-900">
              Đang tải Chứng Nhận Hoàng Triều...
            </span>
          </div>
        </div>
      }
    >
      <CertificateClient />
    </Suspense>
  );
}
