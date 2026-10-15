import HomePageClient from "./HomePageClient";
import { safeJsonLd } from "@/lib/seo";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://lms.histolab.icu";
const TITLE = "Lưu Niên Sử Kí — Cửu Đỉnh Triều Nguyễn | Bảo Vật Hoàng Cung & 162 Bản Đúc Nổi 3D";
const DESCRIPTION =
  "Bách khoa toàn thư số về di sản Cửu Đỉnh triều Nguyễn (Hoàng thành Huế) — Di sản Tư liệu Ký ức Thế giới UNESCO. Khám phá 162 bản đúc nổi, mô hình 3D tương tác, bản đồ WGS84 và Trợ giảng AI có trích dẫn chính sử.";

export const metadata = {
  title: TITLE,
  description: DESCRIPTION,
  keywords: [
    "Cửu Đỉnh",
    "Cửu Đỉnh Huế",
    "Cửu Đỉnh triều Nguyễn",
    "162 bản đúc nổi Cửu Đỉnh",
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
    "UNESCO MOWCAP Cửu Đỉnh",
    "Mô hình 3D Cửu Đỉnh",
    "Lưu Niên Sử Kí",
    "Đại Nam Thực Lục",
    "Khâm Định Đại Nam Hội Điển Sự Lệ",
    "Bản đồ di sản Cửu Đỉnh",
  ],
  alternates: {
    canonical: `${SITE_URL}/`,
  },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `${SITE_URL}/`,
    siteName: "Lưu Niên Sử Kí",
    locale: "vi_VN",
    type: "website",
    images: [
      {
        url: `${SITE_URL}/assets/ban-duc-noi/CAO%20DINH/CAO%20%C4%90%E1%BB%88NH.jpg`,
        width: 1200,
        height: 630,
        alt: "Cửu Đỉnh triều Nguyễn - Lưu Niên Sử Kí",
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

export default function HomePage() {
  const structuredData = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "WebSite",
        "@id": `${SITE_URL}/#website`,
        "url": `${SITE_URL}/`,
        "name": "Lưu Niên Sử Kí",
        "description": DESCRIPTION,
        "inLanguage": "vi",
        "potentialAction": {
          "@type": "SearchAction",
          "target": `${SITE_URL}/atlas?q={search_term_string}`,
          "query-input": "required name=search_term_string",
        },
      },
      {
        "@type": "EducationalOrganization",
        "@id": `${SITE_URL}/#organization`,
        "name": "Lưu Niên Sử Kí — Bảo tàng số Cửu Đỉnh triều Nguyễn",
        "url": `${SITE_URL}/`,
        "logo": `${SITE_URL}/favicon.svg`,
        "description": "Nền tảng bách khoa số hóa và học tập tương tác về bảo vật quốc gia Cửu Đỉnh triều Nguyễn.",
        "address": {
          "@type": "PostalAddress",
          "addressLocality": "Huế",
          "addressCountry": "VN",
        },
      },
      {
        "@type": "FAQPage",
        "@id": `${SITE_URL}/#faq`,
        "mainEntity": [
          {
            "@type": "Question",
            "name": "Cửu Đỉnh triều Nguyễn là gì và được đúc vào thời gian nào?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "Cửu Đỉnh là bộ chín chiếc đỉnh bằng đồng lớn nhất Việt Nam, được vua Minh Mạng chuẩn chỉ cho đúc vào mùa đông năm 1835 (năm Minh Mạng thứ 16) và hoàn thành vào năm 1837, đặt tại sân trước Thế Miếu trong Hoàng thành Huế.",
            },
          },
          {
            "@type": "Question",
            "name": "Cửu Đỉnh gồm những chiếc đỉnh nào và tương ứng với vị vua nào?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "Cửu Đỉnh gồm 9 chiếc: Cao Đỉnh (vua Gia Long), Nhân Đỉnh (vua Minh Mạng), Chương Đỉnh (vua Thiệu Trị), Anh Đỉnh (vua Tự Đức), Nghị Đỉnh (vua Kiến Phúc), Thuần Đỉnh (vua Đồng Khánh), Tuyên Đỉnh (vua Khải Định), Dụ Đỉnh và Huyền Đỉnh.",
            },
          },
          {
            "@type": "Question",
            "name": "Trên Cửu Đỉnh có tổng cộng bao nhiêu bản đúc nổi?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "Mỗi chiếc đỉnh mang 18 bản đúc nổi (gồm 1 đồ án chữ Hán thụy hiệu mang tên đỉnh ở chính diện hàng trên và 17 bức phù điêu cảnh vật, vũ trụ, muông thú, cây cỏ, binh khí). Tổng cộng chín chiếc đỉnh có đúng 162 bản đúc nổi độc bản.",
            },
          },
          {
            "@type": "Question",
            "name": "Cửu Đỉnh đã được UNESCO công nhận là di sản gì?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "Cửu Đỉnh triều Nguyễn tại Hoàng thành Huế đã được Ủy ban Quốc tế UNESCO khu vực Châu Á - Thái Bình Dương (MOWCAP) chính thức ghi danh là Di sản Tư liệu Ký ức Thế giới vào tháng 5/2024.",
            },
          },
        ],
      },
    ],
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: safeJsonLd(structuredData) }}
      />
      <HomePageClient />
    </>
  );
}
