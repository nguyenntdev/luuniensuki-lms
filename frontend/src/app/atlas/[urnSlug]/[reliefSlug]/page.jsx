import ReliefDetailClient from "./ReliefDetailClient";
import { reliefThumbnailUrl, urnNameFromSlug } from "@/lib/history";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://lms.histolab.icu";

export async function generateMetadata({ params }) {
  const urnSlug = params?.urnSlug || "";
  const reliefSlug = params?.reliefSlug || "";
  const urnName = urnNameFromSlug(urnSlug) || "Cửu Đỉnh";
  const imageUrl = reliefThumbnailUrl(reliefSlug) || `${SITE_URL}/assets/ban-duc-noi/CAO%20DINH/LONG.jpg`;
  const title = `Bản đúc ${reliefSlug} (${urnName}) — Cửu Đỉnh Triều Nguyễn | Lưu Niên Sử Kí`;
  const description = `Hồ sơ di sản, khảo chứng chữ Hán-Nôm và bằng chứng lịch sử của bản đúc ${reliefSlug} trên ${urnName} thuộc bảo vật quốc gia Cửu Đỉnh triều Nguyễn (Hoàng thành Huế).`;
  const url = `${SITE_URL}/atlas/${urnSlug}/${reliefSlug}`;

  return {
    title,
    description,
    keywords: [
      reliefSlug,
      `Bản đúc ${reliefSlug}`,
      `Phù điêu ${reliefSlug}`,
      `${urnName} Cửu Đỉnh`,
      "162 bản đúc nổi Cửu Đỉnh",
      "Di sản tư liệu thế giới UNESCO",
      "Hoàng thành Huế",
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
          url: imageUrl.startsWith("http") ? imageUrl : `${SITE_URL}${imageUrl}`,
          width: 1200,
          height: 630,
          alt: `Bản đúc ${reliefSlug} trên ${urnName} - Cửu Đỉnh`,
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [imageUrl.startsWith("http") ? imageUrl : `${SITE_URL}${imageUrl}`],
    },
  };
}

export default function ReliefPage({ params }) {
  const urnSlug = params?.urnSlug || "";
  const reliefSlug = params?.reliefSlug || "";
  const urnName = urnNameFromSlug(urnSlug) || "Cửu Đỉnh";
  const imageUrl = reliefThumbnailUrl(reliefSlug) || `${SITE_URL}/assets/ban-duc-noi/CAO%20DINH/LONG.jpg`;

  const jsonLd = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": ["VisualArtwork", "HistoricalObject"],
        "@id": `${SITE_URL}/atlas/${urnSlug}/${reliefSlug}#artwork`,
        "name": `Bản đúc nổi ${reliefSlug}`,
        "description": `Hồ sơ di sản và khảo chứng chữ Hán-Nôm bản đúc ${reliefSlug} trên ${urnName} thuộc Cửu Đỉnh triều Nguyễn.`,
        "artMedium": "Bronze relief",
        "locationCreated": {
          "@type": "Place",
          "name": "Hoàng thành Huế, Việt Nam",
        },
        "inLanguage": "vi",
        "url": `${SITE_URL}/atlas/${urnSlug}/${reliefSlug}`,
        "image": imageUrl.startsWith("http") ? imageUrl : `${SITE_URL}${imageUrl}`,
      },
      {
        "@type": "BreadcrumbList",
        "@id": `${SITE_URL}/atlas/${urnSlug}/${reliefSlug}#breadcrumb`,
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
          {
            "@type": "ListItem",
            "position": 3,
            "name": urnName,
            "item": `${SITE_URL}/cuu-dinh/${urnSlug}`,
          },
          {
            "@type": "ListItem",
            "position": 4,
            "name": reliefSlug,
            "item": `${SITE_URL}/atlas/${urnSlug}/${reliefSlug}`,
          },
        ],
      },
    ],
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <ReliefDetailClient />
    </>
  );
}
