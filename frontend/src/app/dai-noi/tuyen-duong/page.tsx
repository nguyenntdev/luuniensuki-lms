import React from "react";
import type { Metadata } from "next";
import TrailsListClient from "./TrailsListClient";

export const metadata: Metadata = {
  title: "Tuyến đường học tập lịch sử — Đại Nội Huế | Lưu Niên",
  description:
    "Các tuyến khảo sát thực địa và học tập tương tác tại Hoàng Thành và Tử Cấm Thành Huế. Rèn luyện năng lực lịch sử theo chuẩn GDPT 2018 với mô hình M-E-E và Rubric S1-S4.",
  openGraph: {
    title: "Tuyến đường khảo sát lịch sử Đại Nội Huế | Lưu Niên",
    description:
      "Khám phá 4 tuyến đường học tập lịch sử chuyên sâu: Trục Dũng Đạo, Không Gian Ký Ức, Tử Cấm Thành và Đời Sống Cung Đình.",
  },
};

export default function TrailsPage() {
  return <TrailsListClient />;
}
