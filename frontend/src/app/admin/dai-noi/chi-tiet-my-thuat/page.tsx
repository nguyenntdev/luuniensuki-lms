import type { Metadata } from "next";
import { fetchSites } from "@/lib/imperial/map-api";
import { fetchSiteLearningMedia } from "@/lib/imperial/v51-api";
import { ArtDetailStudioClient } from "./ArtDetailStudioClient";

export const metadata: Metadata = {
  title: "Art Detail Studio | Studio Biên tập Chi tiết Mỹ thuật Đại Nội Huế",
  description:
    "Công cụ biên tập điểm ghim (UV hotspots) và hồ sơ khảo cứu mỹ thuật, điển tích, nguồn sử liệu cho Đại Nội Huế.",
};

export default async function ArtDetailStudioPage() {
  const sites = await fetchSites();
  const defaultSlug = sites[0]?.slug || "dien-thai-hoa";
  const initialMedia = await fetchSiteLearningMedia(defaultSlug);

  return (
    <ArtDetailStudioClient
      initialSites={sites}
      initialMedia={initialMedia}
    />
  );
}
