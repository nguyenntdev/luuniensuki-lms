"use client";

/**
 * SelfHostedTour — our OWN branded 360° walkthrough, served from our assets and
 * rendered by the self-hosted three.js viewer (Panorama360) with verified historical
 * monument source links and 2D accessible still fallbacks.
 */

import { useState } from "react";
import { ImageIcon } from "lucide-react";

import Panorama360 from "./Panorama360";
import { VERIFIED_VIRTUAL_MUSEUM_MONUMENTS } from "@/lib/imperial/panorama-sources";

interface TourScene {
  key: string;
  title: string;
  src: string;
  monumentKey: string;
  fallbackImageUrl: string;
  alt: string;
}

// Our verified panorama scenes linked to historical monuments and 2D rubbings/images.
const SCENES: TourScene[] = [
  {
    key: "cuu-dinh",
    title: "Sân Cửu Đỉnh",
    src: "/panoramas/cuu-dinh.jpg",
    monumentKey: "cuu-dinh",
    fallbackImageUrl: "/ban-duc-noi/CAO DINH/CAO ĐỈNH.jpg",
    alt: "Không gian toàn cảnh Cửu Đỉnh tại sân Thế Miếu, Hoàng thành Huế",
  },
  {
    key: "the-mieu",
    title: "Thế Miếu",
    src: "/panoramas/the-mieu.jpg",
    monumentKey: "the-mieu",
    fallbackImageUrl: "/ban-duc-noi/NHAN DINH/NHÂN ĐỈNH.jpg",
    alt: "Toàn cảnh sân Thế Tổ Miếu và hàng đỉnh đồng",
  },
  {
    key: "ngo-mon",
    title: "Ngọ Môn",
    src: "/panoramas/ngo-mon.jpg",
    monumentKey: "ngo-mon",
    fallbackImageUrl: "/ban-duc-noi/CAO DINH/ĐÔNG HẢI.jpg",
    alt: "Toàn cảnh cửa Ngọ Môn và Lầu Ngũ Phụng",
  },
  {
    key: "kinh-thanh",
    title: "Kinh thành Huế",
    src: "/panoramas/kinh-thanh.jpg",
    monumentKey: "kinh-thanh",
    fallbackImageUrl: "/ban-duc-noi/NHAN DINH/NGỰ BÌNH SƠN.jpg",
    alt: "Toàn cảnh phòng tuyến Kinh thành Huế nhìn ra sông Hương núi Ngự",
  },
];

export default function SelfHostedTour() {
  const [active, setActive] = useState(SCENES[0].key);
  const scene = SCENES.find((s) => s.key === active) || SCENES[0];
  const monument = VERIFIED_VIRTUAL_MUSEUM_MONUMENTS[scene.monumentKey];

  return (
    <div className="rounded-xl border border-border bg-card/50 p-4 contrast-more:border-2 contrast-more:border-foreground">
      <div
        role="tablist"
        aria-label="Chọn bối cảnh toàn cảnh 360°"
        className="mb-3 flex flex-wrap items-center gap-2"
      >
        {SCENES.map((s) => (
          <button
            key={s.key}
            role="tab"
            aria-selected={s.key === active}
            aria-controls={`scene-panel-${s.key}`}
            id={`scene-tab-${s.key}`}
            type="button"
            onClick={() => setActive(s.key)}
            className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-medium transition focus-visible:ring-2 focus-visible:ring-primary contrast-more:border-2 ${
              s.key === active
                ? "border-primary/50 bg-primary/10 text-foreground contrast-more:border-foreground contrast-more:bg-primary/20"
                : "border-border bg-secondary/50 text-muted-foreground hover:border-primary/30 hover:bg-secondary"
            }`}
            aria-label={`Xem cảnh 360: ${s.title}`}
          >
            <ImageIcon className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
            {s.title}
          </button>
        ))}
      </div>

      <div
        id={`scene-panel-${scene.key}`}
        role="tabpanel"
        aria-labelledby={`scene-tab-${scene.key}`}
        className="w-full"
        style={{ aspectRatio: "16 / 9", minHeight: "360px" }}
      >
        <Panorama360
          key={scene.key}
          src={scene.src}
          title={scene.title}
          monument={monument}
          monumentKey={scene.monumentKey}
          fallbackImageUrl={scene.fallbackImageUrl}
          alt={scene.alt}
        />
      </div>

      <p className="mt-2 text-xs text-muted-foreground">
        Bản dựng 360° nội bộ (self-host, không phụ thuộc bên thứ ba). Liên kết chứng thực sử
        liệu từ Quốc Sử Quán triều Nguyễn và Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC).
      </p>
    </div>
  );
}
