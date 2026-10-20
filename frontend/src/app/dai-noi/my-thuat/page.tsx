import type { Metadata } from "next";
import { FALLBACK_ART_DETAILS, fetchSiteArtDetails } from "@/lib/imperial/v51-api";
import MyThuatGalleryClient from "./MyThuatGalleryClient";

export const metadata: Metadata = {
  title: "Mỹ Thuật Cung Đình Triều Nguyễn — Tinh Hoa Hoàng Cung Đại Nội Huế | Lưu Niên",
  description:
    "Khảo cứu chuyên sâu các chuyên đề mỹ thuật cung đình triều Nguyễn: Nghệ thuật khảm sành sứ (Kiến Trung, Khải Thành), Pháp lam hoàng cung (bờ nóc, đầu đao, nghi môn), Nghệ thuật đúc đồng Vạc đồng & súng thần công, Chạm khắc gỗ chạm thủng sơn son thếp vàng, và Ngai vàng chí tôn.",
  keywords: [
    "Mỹ thuật triều Nguyễn",
    "Khảm sành sứ Huế",
    "Pháp lam hoàng cung",
    "Vạc Đồng Thế Miếu",
    "Cửu Vị Thần Công",
    "Điện Thái Hòa",
    "Ngai vàng hoàng đế",
    "Điện Kiến Trung",
    "Điện Khải Thành",
    "Di sản Huế",
  ],
  openGraph: {
    title: "Mỹ Thuật Cung Đình Triều Nguyễn — Tinh Hoa Hoàng Cung Đại Nội Huế",
    description:
      "Khám phá các chuyên đề mỹ thuật cung đình đỉnh cao triều Nguyễn với hồ sơ khảo cứu 6 phần, nguồn sử liệu đối chiếu và câu hỏi củng cố hiểu biết.",
    type: "website",
    images: [
      {
        url: "/assets/imperial/heritage/dainoitrencao.jpg",
        width: 1200,
        height: 630,
        alt: "Mỹ thuật cung đình triều Nguyễn Đại Nội Huế",
      },
    ],
  },
};

export default async function MyThuatPage() {
  // Load initial details from fallback/API
  const initialDetails = FALLBACK_ART_DETAILS;

  return <MyThuatGalleryClient initialDetails={initialDetails} />;
}
