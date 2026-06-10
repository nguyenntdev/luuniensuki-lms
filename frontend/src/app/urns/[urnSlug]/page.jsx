import UrnExperience from "@/components/UrnExperience";

// Readable Vietnamese names for the nine đỉnh (slugs can't carry diacritics).
const URN_NAMES = {
  "cao-dinh": "Cao Đỉnh",
  "nhan-dinh": "Nhân Đỉnh",
  "chuong-dinh": "Chương Đỉnh",
  "anh-dinh": "Anh Đỉnh",
  "nghi-dinh": "Nghị Đỉnh",
  "thuan-dinh": "Thuần Đỉnh",
  "tuyen-dinh": "Tuyên Đỉnh",
  "du-dinh": "Dụ Đỉnh",
  "huyen-dinh": "Huyền Đỉnh",
};

export function generateMetadata({ params }) {
  const slug = params?.urnSlug || "";
  const name = URN_NAMES[slug];
  const title = name ? `${name} — Trình xem 3D` : "Trình xem 3D Cửu Đỉnh";
  return {
    title,
    description: name
      ? `Khám phá ${name} bằng mô hình 3D: xoay, phóng to và mở từng họa tiết trên đỉnh.`
      : "Khám phá Cửu Đỉnh triều Nguyễn bằng mô hình 3D tương tác.",
    openGraph: { title },
  };
}

export default function Page({ params }) {
  return <UrnExperience urnSlug={params.urnSlug} />;
}
