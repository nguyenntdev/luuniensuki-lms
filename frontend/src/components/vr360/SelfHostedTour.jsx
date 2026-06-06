"use client";

/**
 * SelfHostedTour — our OWN branded 360° walkthrough, served from our assets and
 * rendered by the self-hosted three.js viewer (Panorama360). Add scenes by
 * dropping equirectangular images into frontend/public/panoramas/ and listing
 * them below.
 */

import { useState } from "react";
import { ImageIcon } from "lucide-react";

import Panorama360 from "./Panorama360";

// Our own panorama scenes. `src` must point at an image we have rights to use,
// placed under frontend/public/panoramas/<slug>.jpg (served at /panoramas/...).
const SCENES = [
  { key: "kinh-thanh", title: "Kinh thành Huế", src: "/panoramas/kinh-thanh.jpg" },
  { key: "ngo-mon", title: "Ngọ Môn", src: "/panoramas/ngo-mon.jpg" },
  { key: "the-mieu", title: "Thế Miếu", src: "/panoramas/the-mieu.jpg" },
  { key: "cuu-dinh", title: "Sân Cửu Đỉnh", src: "/panoramas/cuu-dinh.jpg" },
];

export default function SelfHostedTour() {
  const [active, setActive] = useState(SCENES[0].key);
  const scene = SCENES.find((s) => s.key === active) || SCENES[0];

  return (
    <div className="rounded-xl border border-border bg-card/50 p-4">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        {SCENES.map((s) => (
          <button
            key={s.key}
            type="button"
            onClick={() => setActive(s.key)}
            className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-medium transition ${
              s.key === active
                ? "border-primary/50 bg-primary/10 text-foreground"
                : "border-border bg-secondary/50 text-muted-foreground hover:border-primary/30 hover:bg-secondary"
            }`}
          >
            <ImageIcon className="h-3.5 w-3.5 text-primary" />
            {s.title}
          </button>
        ))}
      </div>

      <div className="w-full" style={{ aspectRatio: "16 / 9", minHeight: "360px" }}>
        <Panorama360 key={scene.key} src={scene.src} title={scene.title} />
      </div>

      <p className="mt-2 text-xs text-muted-foreground">
        Bản dựng 360° nội bộ (self-host, không phụ thuộc bên thứ ba). Chỉ sử dụng ảnh
        toàn cảnh mà dự án có quyền sử dụng.
      </p>
    </div>
  );
}
