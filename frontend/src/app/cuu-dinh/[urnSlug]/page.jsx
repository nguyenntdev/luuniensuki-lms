import UrnDetailClient from "./UrnDetailClient";
import { urnNameFromSlug } from "@/lib/history";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://lms.histolab.icu";

export async function generateMetadata({ params }) {
  const urnSlug = params?.urnSlug || "cao-dinh";
  const urnName = urnNameFromSlug(urnSlug) || "Cửu Đỉnh";
  const title = `${urnName} — Cửu Đỉnh Triều Nguyễn (Hoàng Thành Huế) | Lưu Niên Sử Kí`;
  const description = `Hồ sơ di sản bảo vật quốc gia ${urnName} thuộc Cửu Đỉnh triều Nguyễn tại Thế Miếu (Hoàng thành Huế). Khảo cứu 18 bản đúc nổi, miếu hiệu phụng thờ, không gian 3D và nguồn sử liệu chính thống.`;
  const url = `${SITE_URL}/cuu-dinh/${urnSlug}`;

  return {
    title,
    description,
    keywords: [
      urnName,
      `${urnName} Cửu Đỉnh`,
      `Đỉnh ${urnName}`,
      "Cửu Đỉnh triều Nguyễn",
      "Thế Miếu Hoàng thành Huế",
      "Bảo vật quốc gia Cửu Đỉnh",
      "18 bản đúc nổi",
      "UNESCO MOWCAP",
      "Lưu Niên Sử Kí",
    ],
    alternates: {
      canonical: url,
    },
    openGraph: {
      title,
      description,
      url,
      siteName: "Lưu Niên Sử Kí",
      locale: "vi_VN",
      type: "article",
      images: [
        {
          url: `${SITE_URL}/assets/ban-duc-noi/${urnSlug.toUpperCase().replace("-", "%20")}/${urnSlug.toUpperCase().replace("-", "%20")}.jpg`,
          width: 1200,
          height: 630,
          alt: `Chiếc đỉnh ${urnName} thuộc Cửu Đỉnh triều Nguyễn`,
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
    },
  };
}

export default function UrnPage({ params }) {
  const urnSlug = params?.urnSlug || "cao-dinh";
  const urnName = urnNameFromSlug(urnSlug) || "Cửu Đỉnh";

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "ItemPage",
    "name": `${urnName} — Cửu Đỉnh triều Nguyễn`,
    "description": `Hồ sơ di sản bảo vật quốc gia ${urnName} thuộc Cửu Đỉnh triều Nguyễn tại Thế Miếu (Hoàng thành Huế).`,
    "url": `${SITE_URL}/cuu-dinh/${urnSlug}`,
    "inLanguage": "vi",
    "mainEntity": {
      "@type": "VisualArtwork",
      "name": urnName,
      "artMedium": "Bronze",
      "locationCreated": {
        "@type": "Place",
        "name": "Thế Miếu, Hoàng thành Huế, Việt Nam",
      },
      "image": `${SITE_URL}/assets/ban-duc-noi/${urnSlug.toUpperCase().replace("-", "%20")}/${urnSlug.toUpperCase().replace("-", "%20")}.jpg`,
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
        {
          "@type": "ListItem",
          "position": 3,
          "name": urnName,
          "item": `${SITE_URL}/cuu-dinh/${urnSlug}`,
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
      <UrnDetailClient />
    </>
  );
}
