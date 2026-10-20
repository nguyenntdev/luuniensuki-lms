"use client";

import { useState } from "react";
import Image from "next/image";
import { Camera, Eye, Info, Shield, ZoomIn, X, ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { HistoricalImage } from "@/lib/imperial/map-types";

interface HistoricalImagerySectionProps {
  imagery: HistoricalImage[];
  monumentName: string;
}

export default function HistoricalImagerySection({
  imagery,
  monumentName,
}: HistoricalImagerySectionProps) {
  const [selectedImage, setSelectedImage] = useState<HistoricalImage | null>(null);

  if (!imagery || imagery.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
        Đang cập nhật hồ sơ ảnh tư liệu lưu trữ cho công trình này.
      </div>
    );
  }

  return (
    <section aria-labelledby="imagery-heading" className="space-y-6">
      <div className="flex items-center justify-between border-b border-border/70 pb-3">
        <div className="flex items-center gap-2.5">
          <Camera className="h-5 w-5 text-primary" />
          <h2 id="imagery-heading" className="font-display text-xl font-bold tracking-tight text-foreground md:text-2xl">
            Tư liệu hình ảnh & Bản vẽ kiến trúc
          </h2>
        </div>
        <Badge variant="secondary" className="text-xs">
          {imagery.length} tư liệu thị giác
        </Badge>
      </div>

      <p className="text-sm text-muted-foreground leading-relaxed">
        Các bức ảnh đầu thế kỷ 20 từ kho lưu trữ EFEO / Albert Kahn, bản vẽ bình đồ và mặt cắt phục dựng khoa học, được cấp phép cho mục đích giáo dục phi thương mại.
      </p>

      {/* Grid of Historical Photos & Plans */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        {imagery.map((item, idx) => (
          <div
            key={item.id || idx}
            className="group flex flex-col overflow-hidden rounded-xl border border-border/70 bg-card transition-all hover:border-primary/50 hover:shadow-lg"
          >
            {/* Image Preview Container */}
            <div
              className="relative aspect-[16/10] w-full overflow-hidden bg-neutral-900 cursor-pointer"
              onClick={() => setSelectedImage(item)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === "Enter" && setSelectedImage(item)}
              aria-label={`Xem ảnh lớn: ${item.title}`}
            >
              {/* Authentic image or placeholder */}
              {item.url ? (
                <>
                  <Image
                    src={item.url}
                    alt={item.title}
                    fill
                    className="object-cover group-hover:scale-105 transition-transform duration-500"
                    sizes="(max-width: 768px) 100vw, 500px"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-3">
                    <span className="text-[11px] font-medium text-white flex items-center gap-1.5 drop-shadow">
                      <ZoomIn className="h-3.5 w-3.5" /> Bấm để phóng to chi tiết
                    </span>
                  </div>
                </>
              ) : (
                <div className="absolute inset-0 flex items-center justify-center p-4 bg-gradient-to-br from-stone-900 via-neutral-800 to-stone-900">
                  <div className="text-center space-y-2 opacity-80 group-hover:opacity-100 transition-opacity">
                    <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-white/10 text-white">
                      <ZoomIn className="h-6 w-6" />
                    </div>
                    <p className="font-mono text-xs text-white/90 font-medium">
                      {item.year ? `Năm ${item.year}` : "Tư liệu di sản"}
                    </p>
                    <p className="text-xs text-stone-300 max-w-[240px] truncate">
                      {item.archive || item.author_or_source}
                    </p>
                  </div>
                </div>
              )}

              {/* Tag pill */}
              <div className="absolute top-2.5 left-2.5 z-10">
                <span className="rounded bg-black/75 px-2 py-0.5 text-[11px] font-mono font-medium text-white shadow">
                  {item.year ? `${item.year}` : "Lưu trữ"}
                </span>
              </div>

              <div className="absolute top-2.5 right-2.5 z-10">
                <span className="rounded-full bg-primary/90 px-2 py-0.5 text-[10px] font-semibold text-white shadow">
                  EFEO / Lưu trữ
                </span>
              </div>
            </div>

            {/* Description & Source Info */}
            <div className="flex flex-1 flex-col justify-between p-4 space-y-3">
              <div>
                <h3 className="font-display text-sm font-bold text-foreground line-clamp-2">
                  {item.title}
                </h3>
                {item.caption && (
                  <p className="mt-1 text-xs text-muted-foreground leading-relaxed line-clamp-3">
                    {item.caption}
                  </p>
                )}
              </div>

              {/* Metadata & Legal Footer */}
              <div className="border-t border-border/50 pt-2 text-[11px] text-muted-foreground space-y-1">
                <div className="flex items-center justify-between">
                  <span className="truncate max-w-[180px]">
                    <strong>Nguồn:</strong> {item.author_or_source}
                  </span>
                  <span className="text-primary font-medium">
                    {item.license_kind}
                  </span>
                </div>
                {item.copyright_note && (
                  <p className="text-[10px] text-muted-foreground/80 italic line-clamp-1">
                    {item.copyright_note}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Lightbox Modal for detailed inspection */}
      {selectedImage && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-sm p-4 animate-in fade-in duration-200"
          onClick={() => setSelectedImage(null)}
        >
          <div
            className="relative max-w-3xl w-full rounded-2xl bg-card border border-border p-6 shadow-2xl space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-4 border-b border-border pb-3">
              <div>
                <h3 className="font-display text-lg font-bold text-foreground">
                  {selectedImage.title}
                </h3>
                <p className="text-xs text-muted-foreground font-mono">
                  Thời điểm: {selectedImage.year || "Đầu thế kỷ 20"} • Nguồn: {selectedImage.author_or_source}
                </p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSelectedImage(null)}
                aria-label="Đóng cửa sổ xem ảnh"
              >
                <X className="h-5 w-5" />
              </Button>
            </div>

            {selectedImage.url ? (
              <div className="space-y-3">
                <div className="relative aspect-[16/10] max-h-[58vh] w-full rounded-xl overflow-hidden bg-neutral-950 border border-border/50">
                  <Image
                    src={selectedImage.url}
                    alt={selectedImage.title}
                    fill
                    className="object-contain"
                    sizes="(max-width: 1024px) 100vw, 900px"
                    priority
                  />
                </div>
                {selectedImage.caption && (
                  <p className="text-xs text-muted-foreground leading-relaxed px-1">
                    {selectedImage.caption}
                  </p>
                )}
                {selectedImage.archive && (
                  <div className="rounded bg-secondary/40 px-3 py-1.5 text-[11px] font-mono text-muted-foreground">
                    Lưu trữ: {selectedImage.archive}
                  </div>
                )}
              </div>
            ) : (
              <div className="relative aspect-video w-full rounded-xl bg-neutral-950 flex flex-col items-center justify-center p-6 text-center text-white">
                <Camera className="h-14 w-14 text-white/30 mb-2" />
                <p className="font-display text-base font-semibold">{selectedImage.title}</p>
                <p className="text-xs text-white/70 max-w-md mt-1">{selectedImage.caption}</p>
                <div className="mt-4 rounded bg-white/10 px-3 py-1 text-xs font-mono">
                  Lưu trữ: {selectedImage.archive || "Trung tâm Bảo tồn Di tích Cố đô Huế"}
                </div>
              </div>
            )}

            <div className="rounded-lg bg-secondary/50 p-3 text-xs space-y-1">
              <div className="flex items-center gap-1.5 font-semibold text-foreground">
                <Shield className="h-3.5 w-3.5 text-primary" />
                Quyền sử dụng và Tuyên bố giáo dục (Fair-Use):
              </div>
              <p className="text-muted-foreground leading-relaxed">
                {selectedImage.copyright_note ||
                  "Tư liệu lịch sử được số hóa phục vụ độc quyền mục đích học tập, nghiên cứu và giáo dục di sản phi thương mại."}
              </p>
            </div>

            <div className="flex justify-end">
              <Button variant="outline" size="sm" onClick={() => setSelectedImage(null)}>
                Đóng
              </Button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
