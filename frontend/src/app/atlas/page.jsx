import AtlasClient from "./AtlasClient";
import { safeJsonLd } from "@/lib/seo";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://lms.histolab.icu";
const TITLE = "Atlas 162 Bản Đúc Nổi Cửu Đỉnh Triều Nguyễn | Lưu Niên Sử Kí";
const DESCRIPTION =
  "Tra cứu trọn vẹn 162 bản đúc nổi trên chín chiếc đỉnh đồng triều Nguyễn (Hoàng thành Huế). Phân loại chi tiết theo vũ trụ khí tượng, sông núi biển đảo, muông thú, thảo mộc và vũ khí võ bị.";

export const metadata = {
  title: TITLE,
  description: DESCRIPTION,
  keywords: [
    "Atlas 162 bản đúc nổi",
    "162 phù điêu Cửu Đỉnh",
    "Họa tiết Cửu Đỉnh",
    "Bản đúc nổi Cửu Đỉnh triều Nguyễn",
    "Đông Hải Cửu Đỉnh",
    "Nam Hải",
    "Tây Hải",
    "Kênh Vĩnh Tế",
    "Sông Hương",
    "Sông Bến Nghé",
    "Núi Thiên Tôn",
    "Bảo vật quốc gia Cửu Đỉnh",
    "Lưu Niên Sử Kí",
  ],
  alternates: {
    canonical: `${SITE_URL}/atlas`,
  },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `${SITE_URL}/atlas`,
    siteName: "Lưu Niên Sử Kí",
    locale: "vi_VN",
    type: "website",
    images: [
      {
        url: `${SITE_URL}/assets/ban-duc-noi/CAO%20DINH/LONG.jpg`,
        width: 1200,
        height: 630,
        alt: "Atlas 162 bản đúc nổi Cửu Đỉnh - Rồng (Long)",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: TITLE,
    description: DESCRIPTION,
    images: [`${SITE_URL}/assets/ban-duc-noi/CAO%20DINH/LONG.jpg`],
  },
};

export default function AtlasPage() {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    "name": TITLE,
    "description": DESCRIPTION,
    "url": `${SITE_URL}/atlas`,
    "inLanguage": "vi",
    "about": {
      "@type": "VisualArtwork",
      "name": "162 Bản đúc nổi Cửu Đỉnh triều Nguyễn",
      "artMedium": "Bronze Relief",
      "locationCreated": {
        "@type": "Place",
        "name": "Hoàng thành Huế, Việt Nam",
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
          "name": "Atlas 162",
          "item": `${SITE_URL}/atlas`,
        },
      ],
    },
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: safeJsonLd(jsonLd) }}
      />
      <AtlasClient />
    </>
  );
}
