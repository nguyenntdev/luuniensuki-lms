import type { Metadata } from "next";
import { EditorialReviewClient } from "./EditorialReviewClient";

export const metadata: Metadata = {
  title: "Hàng đợi Biên tập Nhân văn & Kiểm duyệt Sử liệu (P09–P10) | Quản trị Lưu Niên",
  description:
    "Hệ thống duyệt sử liệu P09–P10: Hàng đợi biên tập nhân văn, nguyên tắc 4 mắt (Four-Eyes Principle), sổ cái giải quyết tranh chấp và ký duyệt bản quyền.",
};

export const dynamic = "force-dynamic";

export default function EditorialReviewPage() {
  return <EditorialReviewClient />;
}
