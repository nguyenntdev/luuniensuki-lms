import type { Metadata } from "next";
import GalleryClient from "./GalleryClient";

export const metadata: Metadata = {
  title: "Kho ảnh di sản Cố đô Huế — Lưu Niên",
  description:
    "Kho tư liệu hình ảnh di sản có cấu trúc gồm 27 ảnh hiện trạng, chi tiết kiến trúc, không ảnh trực giao và mỹ thuật cung đình triều Nguyễn.",
};

export default function ThuVienAnhPage() {
  return <GalleryClient />;
}
