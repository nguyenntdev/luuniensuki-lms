import type { Metadata } from "next";
import { MediaCmsClient } from "./MediaCmsClient";

export const metadata: Metadata = {
  title: "Museum Operator Media CMS | Quản lý Tư liệu & Hiện vật Số Lưu Niên",
  description:
    "Hệ thống quản lý, kiểm duyệt bản quyền và xuất bản theo giai đoạn cho tư liệu ảnh, bản dập 2D và mô hình 3D Cửu Đỉnh & Đại Nội Huế.",
};

export const dynamic = "force-dynamic";

export default function MediaCmsPage() {
  return <MediaCmsClient />;
}
