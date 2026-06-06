"use client";

/**
 * VirtualTours — embeds official third-party 360° virtual tours of Huế as
 * supplementary heritage context for the LMS.
 *
 * IMPORTANT (licensing): these tours are produced and owned by their creators
 * (360view.vn, vr360.com.vn). We DO NOT copy or rehost their panoramas/source.
 * We embed via <iframe> and credit the source, with an "open in new tab"
 * fallback in case a provider disallows framing (X-Frame-Options/CSP).
 */

import { useState } from "react";
import { ExternalLink, MapPin, Info } from "lucide-react";

const TOURS = [
  {
    key: "kinh-thanh",
    title: "Kinh thành Huế (Hoàng thành)",
    source: "360view.vn",
    credit: "© 360view.vn",
    url: "https://www.360view.vn/gallery/data/projects/vietnam/thuathien_hue/kinhthanh__092011/index.html",
    blurb:
      "Tham quan ảo 360° Kinh thành Huế — nơi đặt Cửu Đỉnh trước Thế Miếu trong Hoàng thành.",
  },
  {
    key: "hue-tourist",
    title: "Hue Tourist — Cố đô Huế",
    source: "vr360.com.vn",
    credit: "© vr360.com.vn",
    url: "https://vr360.com.vn/projects/hue-tourist/",
    blurb: "Chuỗi điểm tham quan 360° quanh cố đô Huế và các di tích triều Nguyễn.",
  },
];

export default function VirtualTours() {
  const [active, setActive] = useState(TOURS[0].key);
  const tour = TOURS.find((t) => t.key === active) || TOURS[0];

  return (
    <section className="px-6 py-6">
      {/* Tour selector */}
      <div className="mb-4 flex flex-wrap gap-2">
        {TOURS.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => setActive(t.key)}
            className={`inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition ${
              t.key === active
                ? "border-primary/50 bg-primary/10 text-foreground"
                : "border-border bg-secondary/50 text-muted-foreground hover:border-primary/30 hover:bg-secondary"
            }`}
          >
            <MapPin className="h-4 w-4 text-primary" />
            {t.title}
          </button>
        ))}
      </div>

      <div className="rounded-xl border border-border bg-card/50 p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="text-lg font-semibold text-foreground">{tour.title}</h2>
            <p className="text-sm text-muted-foreground">{tour.blurb}</p>
          </div>
          <a
            href={tour.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
          >
            <ExternalLink className="h-4 w-4" />
            Mở tour toàn màn hình
          </a>
        </div>

        {/* 360 embed (16:9, tall on mobile). If the provider blocks framing,
            the "Mở tour" button above always works. */}
        <div className="relative w-full overflow-hidden rounded-lg bg-black ring-1 ring-white/10" style={{ aspectRatio: "16 / 9", minHeight: "360px" }}>
          <iframe
            key={tour.key}
            src={tour.url}
            title={tour.title}
            className="absolute inset-0 h-full w-full"
            style={{ border: 0 }}
            loading="lazy"
            allow="fullscreen; accelerometer; gyroscope; xr-spatial-tracking"
            allowFullScreen
            referrerPolicy="no-referrer-when-downgrade"
          />
        </div>

        <p className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
          <Info className="h-3.5 w-3.5" />
          Nội dung tham quan ảo thuộc bản quyền của {tour.credit}. Nếu khung hiển thị
          trống, hãy nhấn “Mở tour toàn màn hình”.
        </p>
      </div>

      <p className="mt-4 max-w-3xl text-sm text-muted-foreground">
        Mẹo: Sau khi “đi dạo” trong Hoàng thành, hãy quay lại trang{" "}
        <a href="/explore" className="text-primary hover:underline">Khám phá</a> để mở
        mô hình 3D Cửu Đỉnh và tìm từng họa tiết bạn vừa thấy ngoài thực địa.
      </p>
    </section>
  );
}
