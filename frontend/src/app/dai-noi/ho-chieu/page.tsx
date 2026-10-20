import React from "react";
import type { Metadata } from "next";
import PassportClient from "./PassportClient";

export const metadata: Metadata = {
  title: "Hộ Chiếu Di Sản Hoàng Gia — Đại Nội Huế | Lưu Niên",
  description:
    "Sổ hộ chiếu di sản số đóng dấu ấn triện son hoàng triều khi học sinh hoàn thành khảo sát 16 công trình trọng điểm Đại Nội Huế.",
  openGraph: {
    title: "Hộ Chiếu Di Sản Hoàng Gia — Đại Nội Huế | Lưu Niên",
    description:
      "Khảo cứu 16 di tích Hoàng Thành và Tử Cấm Thành, thu thập trọn bộ 16 con dấu triện son và xuất chứng nhận vinh danh hoàng triều.",
  },
};

export default function PassportPage() {
  return <PassportClient />;
}
