import CuuDinhLandingClient from "./CuuDinhLandingClient";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://lms.histolab.icu";
const TITLE = "Cửu Đỉnh Triều Nguyễn — Chín Chiếc Đỉnh Đồng Báu Vật | Lưu Niên Sử Kí";
const DESCRIPTION =
  "Tổng quan chín chiếc đỉnh đồng (Cửu Đỉnh) đúc dưới triều vua Minh Mạng (1835-1837) đặt tại Thế Miếu, Hoàng thành Huế. Khám phá toàn diện 9 đỉnh, 162 bản đúc nổi và mô hình 3D đa chiều.";

export const metadata = {
  title: TITLE,
  description: DESCRIPTION,
  keywords: [
    "Cửu Đỉnh",
    "Cửu Đỉnh Huế",
    "Chín chiếc đỉnh đồng",
    "Thế Miếu Hoàng thành Huế",
    "Cao Đỉnh",
    "Nhân Đỉnh",
    "Chương Đỉnh",
    "Anh Đỉnh",
    "Nghị Đỉnh",
    "Thuần Đỉnh",
    "Tuyên Đỉnh",
    "Dụ Đỉnh",
    "Huyền Đỉnh",
    "Bảo vật quốc gia Cửu Đỉnh",
    "UNESCO MOWCAP",
  ],
  alternates: {
    canonical: `${SITE_URL}/cuu-dinh`,
  },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `${SITE_URL}/cuu-dinh`,
    siteName: "Lưu Niên Sử Kí",
    locale: "vi_VN",
    type: "article",
    images: [
      {
        url: `${SITE_URL}/assets/ban-duc-noi/CAO%20DINH/CAO%20%C4%90%E1%BB%88NH.jpg`,
        width: 1200,
        height: 630,
        alt: "Chín chiếc đỉnh đồng Cửu Đỉnh triều Nguyễn",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: TITLE,
    description: DESCRIPTION,
    images: [`${SITE_URL}/assets/ban-duc-noi/CAO%20DINH/CAO%20%C4%90%E1%BB%88NH.jpg`],
  },
};

export default function CuuDinhPage() {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    "name": TITLE,
    "description": DESCRIPTION,
    "url": `${SITE_URL}/cuu-dinh`,
    "inLanguage": "vi",
    "about": {
      "@type": "VisualArtwork",
      "name": "Cửu Đỉnh triều Nguyễn",
      "artMedium": "Bronze",
      "locationCreated": {
        "@type": "Place",
        "name": "Thế Miếu, Hoàng thành Huế, Việt Nam",
      },
    },
    "breadcrumb": {
      "@type": "BreadcrumbList",
      "itemListElement": [
        {
          "@type": "ListItem",
          "position": 1,
          "name": "Trang chủ",
          "item": `${SITE_URL}/`,
        },
        {
          "@type": "ListItem",
          "position": 2,
          "name": "Cửu Đỉnh",
          "item": `${SITE_URL}/cuu-dinh`,
        },
      ],
    },
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <CuuDinhLandingClient />
    </>
  );
}
