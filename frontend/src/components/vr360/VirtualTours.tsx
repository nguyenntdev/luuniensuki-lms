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
import { ExternalLink, MapPin, Info, FileText, ChevronDown, ChevronUp } from "lucide-react";

interface Tour {
  key: string;
  title: string;
  source: string;
  credit: string;
  url: string;
  blurb: string;
  textAlternative: string;
}

const TOURS: Tour[] = [
  {
    key: "kinh-thanh",
    title: "Kinh thành Huế (Hoàng thành)",
    source: "360view.vn",
    credit: "© 360view.vn",
    url: "https://www.360view.vn/gallery/data/projects/vietnam/thuathien_hue/kinhthanh__092011/index.html",
    blurb:
      "Tham quan ảo 360° Kinh thành Huế — nơi đặt Cửu Đỉnh trước Thế Miếu trong Hoàng thành.",
    textAlternative:
      "Kinh thành Huế là tòa thành cổ thuộc quần thể di tích Cố đô Huế, được vua Gia Long tiến hành khảo sát từ năm 1803 và khởi công xây dựng từ năm 1805 dưới hình thái kiến trúc pháo đài Vauban kết hợp kiến trúc cung đình phương Đông. Bên trong Hoàng thành, sân Thế Miếu là nơi đặt chín đỉnh đồng Cửu Đỉnh đúc từ năm 1835 đến 1837 dưới thời vua Minh Mạng, khắc nổi 162 đồ án biểu trưng cho giang sơn gấm vóc và sự trường tồn của dân tộc.",
  },
  {
    key: "hue-tourist",
    title: "Hue Tourist — Cố đô Huế",
    source: "vr360.com.vn",
    credit: "© vr360.com.vn",
    url: "https://vr360.com.vn/projects/hue-tourist/",
    blurb: "Chuỗi điểm tham quan 360° quanh cố đô Huế và các di tích triều Nguyễn.",
    textAlternative:
      "Hệ thống di sản Cố đô Huế bao gồm quần thể di tích Kinh thành, Kỳ Đài, Ngọ Môn, Điện Thái Hòa, Cung Diên Thọ cùng hệ thống lăng tẩm hoàng gia của các vị hoàng đế triều Nguyễn (Lăng Gia Long, Lăng Minh Mạng, Lăng Thiệu Trị, Lăng Tự Đức, Lăng Khải Định) nằm dọc hai bên dòng sông Hương thơ mộng, được UNESCO công nhận là Di sản Văn hóa Thế giới năm 1993.",
  },
];

export default function VirtualTours() {
  const [active, setActive] = useState(TOURS[0].key);
  const [isLoaded, setIsLoaded] = useState(false);
  const [show2DText, setShow2DText] = useState(true);
  const [announcement, setAnnouncement] = useState("");
  const tour = TOURS.find((t) => t.key === active) || TOURS[0];

  const handleSelectTour = (t: Tour) => {
    setActive(t.key);
    setIsLoaded(false);
    setAnnouncement(`Đã chọn địa điểm tham quan: ${t.title}`);
  };

  return (
    <section className="px-6 py-6" aria-label="Tham quan ảo di sản Cố đô Huế">
      {/* Screen reader announcement live region */}
      <div role="status" aria-live="polite" className="sr-only">
        {announcement}
      </div>

      {/* Tour selector tablist */}
      <div
        role="tablist"
        aria-label="Chọn địa điểm tham quan 360°"
        className="mb-4 flex flex-wrap gap-2"
      >
        {TOURS.map((t) => (
          <button
            key={t.key}
            id={`tour-tab-${t.key}`}
            role="tab"
            aria-selected={t.key === active}
            aria-controls={`tour-panel-${t.key}`}
            type="button"
            onClick={() => handleSelectTour(t)}
            className={`inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary contrast-more:border-2 ${
              t.key === active
                ? "border-primary/50 bg-primary/10 text-foreground contrast-more:border-foreground contrast-more:bg-primary/20"
                : "border-border bg-secondary/50 text-muted-foreground hover:border-primary/30 hover:bg-secondary"
            }`}
          >
            <MapPin className="h-4 w-4 text-primary" aria-hidden="true" />
            {t.title}
          </button>
        ))}
      </div>

      <div
        id={`tour-panel-${tour.key}`}
        role="tabpanel"
        aria-labelledby={`tour-tab-${tour.key}`}
        className="rounded-xl border border-border bg-card/50 p-4 contrast-more:border-2 contrast-more:border-foreground"
      >
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="text-lg font-semibold text-foreground">{tour.title}</h2>
            <p className="text-sm text-muted-foreground">{tour.blurb}</p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <button
              type="button"
              onClick={() => setShow2DText(!show2DText)}
              aria-expanded={show2DText}
              aria-controls={`tour-2d-desc-${tour.key}`}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-secondary/60 px-3 py-2 text-xs font-semibold text-foreground hover:bg-secondary transition focus-visible:ring-2 focus-visible:ring-primary"
            >
              <FileText className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
              <span>{show2DText ? "Ẩn thuyết minh 2D" : "Thuyết minh văn bản 2D"}</span>
              {show2DText ? (
                <ChevronUp className="h-3 w-3" aria-hidden="true" />
              ) : (
                <ChevronDown className="h-3 w-3" aria-hidden="true" />
              )}
            </button>

            <a
              href={tour.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 focus-visible:ring-2 focus-visible:ring-primary"
              aria-label={`Mở tour ${tour.title} toàn màn hình trên trang gốc`}
            >
              <ExternalLink className="h-4 w-4" aria-hidden="true" />
              Mở tour toàn màn hình
            </a>
          </div>
        </div>

        {/* 2D Textual Alternative (WCAG 2.2 AA non-3D / screen reader equivalent) */}
        {show2DText && (
          <div
            id={`tour-2d-desc-${tour.key}`}
            className="mb-4 rounded-lg border border-border/80 bg-secondary/30 p-3.5 text-xs text-foreground leading-relaxed contrast-more:border-foreground"
          >
            <div className="flex items-center gap-1.5 font-semibold text-primary mb-1">
              <FileText className="h-3.5 w-3.5" aria-hidden="true" />
              <span>Thuyết minh di tích (Nội dung tiếp cận 2D):</span>
            </div>
            <p>{tour.textAlternative}</p>
          </div>
        )}

        {/* 360 embed with on-demand interactive launcher */}
        <div
          className="relative w-full overflow-hidden rounded-lg bg-black ring-1 ring-white/10"
          style={{ aspectRatio: "16 / 9", minHeight: "360px" }}
        >
          {isLoaded ? (
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
          ) : (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-br from-card via-background to-secondary p-6 text-center">
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/15 text-primary ring-1 ring-primary/30">
                <MapPin className="h-8 w-8" aria-hidden="true" />
              </div>
              <h3 className="font-serif text-xl font-bold text-foreground">{tour.title}</h3>
              <p className="mt-1 max-w-md text-xs text-muted-foreground">{tour.blurb}</p>
              <button
                type="button"
                onClick={() => {
                  setIsLoaded(true);
                  setAnnouncement(`Đang tải khung nhìn toàn cảnh 360 độ ${tour.title}`);
                }}
                className="mt-5 inline-flex items-center gap-2 rounded-xl bg-primary px-6 py-3 text-sm font-bold text-primary-foreground shadow-lg shadow-primary/25 transition hover:scale-105 hover:bg-primary/90 focus-visible:ring-2 focus-visible:ring-primary"
                aria-label={`Bắt đầu tham quan 360 độ ${tour.title}`}
              >
                <span>Bắt đầu tham quan 360°</span>
              </button>
            </div>
          )}
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
