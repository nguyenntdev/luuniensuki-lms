import ReliefDetailClient from "./ReliefDetailClient";
import { urnNameFromSlug } from "@/lib/history";

export async function generateMetadata({ params }) {
  const urnSlug = params?.urnSlug || "";
  const reliefSlug = params?.reliefSlug || "";
  const urnName = urnNameFromSlug(urnSlug) || "Cửu Đỉnh";
  const title = `Phù điêu ${reliefSlug} — Atlas (${urnName}) · Lưu Niên Sử Kí`;
  const description = `Hồ sơ di sản và bằng chứng lịch sử phù điêu ${reliefSlug} trên ${urnName} thuộc Cửu Đỉnh triều Nguyễn (Huế, Việt Nam).`;
  const url = `https://lms.histolab.icu/atlas/${urnSlug}/${reliefSlug}`;

  return {
    title,
    description,
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
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
    },
  };
}

export default function ReliefPage({ params }) {
  const urnSlug = params?.urnSlug || "";
  const reliefSlug = params?.reliefSlug || "";
  const urnName = urnNameFromSlug(urnSlug) || "Cửu Đỉnh";

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": ["VisualArtwork", "HistoricalObject"],
    "name": `Phù điêu ${reliefSlug}`,
    "description": `Chi tiết phù điêu ${reliefSlug} trên ${urnName} thuộc Cửu Đỉnh triều Nguyễn.`,
    "artMedium": "Bronze relief",
    "locationCreated": {
      "@type": "Place",
      "name": "Huế, Việt Nam",
    },
    "inLanguage": "vi",
    "url": `https://lms.histolab.icu/atlas/${urnSlug}/${reliefSlug}`,
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
