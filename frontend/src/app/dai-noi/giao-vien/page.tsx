import React from "react";
import type { Metadata } from "next";
import TeacherDashboardClient from "./TeacherDashboardClient";

export const metadata: Metadata = {
  title: "Bảng Đánh Giá Giáo Viên — Đại Nội Huế | Lưu Niên",
  description:
    "Giao diện quản lý bài nộp khảo sát lịch sử và chấm điểm theo Rubric S1-S4 cho giáo viên THPT. Đánh giá năng lực Không gian, Thời gian, Sử liệu và Lập luận.",
  openGraph: {
    title: "Bảng Đánh Giá Giáo Viên — STTTNNĐ Đại Nội Huế",
    description: "Công cụ chấm bài khảo sát di sản lịch sử theo chuẩn Rubric S1-S4.",
  },
};

export default function TeacherDashboardPage() {
  return <TeacherDashboardClient />;
}
