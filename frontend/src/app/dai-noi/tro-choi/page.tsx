import React from "react";
import type { Metadata } from "next";
import GamesPageClient from "./GamesPageClient";

export const metadata: Metadata = {
  title: "Trò Chơi Tương Tác Di Sản — Đại Nội Huế | Lưu Niên",
  description:
    "Hệ thống trò chơi tương tác giáo dục di sản Cố đô Huế: Trắc nghiệm hiểu sâu 'Vì sao', Ghép chi tiết - Ý nghĩa biểu tượng, và Thử thách định vị không gian kiến trúc.",
  openGraph: {
    title: "Trò Chơi Di Sản — STTTNNĐ Đại Nội Huế",
    description: "Khám phá di sản Đại Nội qua các thử thách tư duy lịch sử và bằng chứng.",
  },
};

export default function GamesPage() {
  return <GamesPageClient />;
}
