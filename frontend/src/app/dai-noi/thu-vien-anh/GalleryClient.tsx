"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  Camera,
  Compass,
  Filter,
  Hammer,
  HelpCircle,
  Landmark,
  Layers,
  MapPin,
  Shield,
  Sparkles,
  ZoomIn,
  X,
  ExternalLink,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  getAllHeritageImages,
  HERITAGE_CATEGORIES,
  HERITAGE_IMAGE_TYPES,
  type HeritageCategory,
  type HeritageImage,
  type HeritageImageType,
} from "@/lib/imperial/heritage-images";

export default function GalleryClient() {
  const allImages = getAllHeritageImages();
  const [selectedCategory, setSelectedCategory] = useState<HeritageCategory | "all">("all");
  const [selectedType, setSelectedType] = useState<HeritageImageType | "all">("all");
  const [activeImage, setActiveImage] = useState<HeritageImage | null>(null);

  const filteredImages = allImages.filter((img) => {
    if (selectedCategory !== "all" && img.category !== selectedCategory) return false;
    if (selectedType !== "all" && img.imageType !== selectedType) return false;
    return true;
  });

  return (
    <div className="min-h-screen bg-background text-foreground pb-20">
      {/* Hero Header */}
      <div className="relative border-b border-border/70 bg-gradient-to-b from-card via-background to-background pt-10 pb-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-600 dark:text-amber-400">
              <Camera className="h-3.5 w-3.5" />
              Tư liệu thị giác di sản • Spec Patch V2.2
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
              <Shield className="h-3.5 w-3.5" />
              {allImages.length} tư liệu đã kiểm duyệt & phân loại
            </span>
          </div>

          <h1 className="font-display text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-foreground">
            Kho ảnh di sản Cố đô Huế
          </h1>

          <p className="text-base text-muted-foreground max-w-3xl leading-relaxed">
            Học liệu thị giác có cấu trúc phục vụ nghiên cứu và học tập lịch sử theo chu trình:{" "}
            <strong className="text-foreground">Định vị không ảnh → Quan sát kiến trúc → Đối chiếu sử liệu → Đúc kết kết luận</strong>.
            Mỗi hình ảnh được xác minh nguồn gốc, phân định rõ giữa hiện trạng thực tế, ảnh đã xử lý và ảnh phục chế.
          </p>

          {/* Category Filter Pills */}
          <div className="pt-4 flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => setSelectedCategory("all")}
              className={cn(
                "px-3.5 py-1.5 rounded-full text-xs font-medium transition-all border",
                selectedCategory === "all"
                  ? "bg-primary text-primary-foreground border-primary shadow-sm"
                  : "bg-secondary/60 text-muted-foreground border-border/60 hover:text-foreground",
              )}
            >
              Tất cả ({allImages.length})
            </button>
            {Object.entries(HERITAGE_CATEGORIES).map(([catKey, catMeta]) => {
              const count = allImages.filter((img) => img.category === catKey).length;
              return (
                <button
                  key={catKey}
                  type="button"
                  onClick={() => setSelectedCategory(catKey as HeritageCategory)}
                  className={cn(
                    "px-3.5 py-1.5 rounded-full text-xs font-medium transition-all border flex items-center gap-1.5",
                    selectedCategory === catKey
                      ? "bg-primary text-primary-foreground border-primary shadow-sm"
                      : "bg-secondary/60 text-muted-foreground border-border/60 hover:text-foreground",
                  )}
                >
                  <span>{catMeta.label}</span>
                  <span className="opacity-70 text-[10px]">({count})</span>
                </button>
              );
            })}
          </div>

          {/* Image Type Filter Pills */}
          <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
            <span className="text-muted-foreground flex items-center gap-1 mr-1">
              <Filter className="h-3.5 w-3.5" /> Phân loại:
            </span>
            <button
              type="button"
              onClick={() => setSelectedType("all")}
              className={cn(
                "px-2.5 py-1 rounded-md text-[11px] font-medium transition-all",
                selectedType === "all"
                  ? "bg-secondary text-foreground font-semibold"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              Mọi loại ảnh
            </button>
            {Object.entries(HERITAGE_IMAGE_TYPES).map(([typeKey, typeMeta]) => {
              const count = allImages.filter((img) => img.imageType === typeKey).length;
              if (count === 0) return null;
              return (
                <button
                  key={typeKey}
                  type="button"
                  onClick={() => setSelectedType(typeKey as HeritageImageType)}
                  className={cn(
                    "px-2.5 py-1 rounded-md text-[11px] font-medium transition-all border",
                    selectedType === typeKey
                      ? `${typeMeta.badgeClass} font-semibold shadow-sm`
                      : "border-transparent text-muted-foreground hover:text-foreground",
                  )}
                >
                  {typeMeta.label} ({count})
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Grid of Heritage Images */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        {filteredImages.length === 0 ? (
          <div className="text-center py-16 rounded-2xl border border-dashed border-border p-8">
            <HelpCircle className="h-10 w-10 mx-auto text-muted-foreground/60 mb-3" />
            <p className="text-sm text-muted-foreground">
              Không tìm thấy hình ảnh nào phù hợp với bộ lọc hiện tại.
            </p>
            <Button
              variant="outline"
              size="sm"
              className="mt-4"
              onClick={() => {
                setSelectedCategory("all");
                setSelectedType("all");
              }}
            >
              Xóa bộ lọc
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredImages.map((img) => {
              const typeMeta = HERITAGE_IMAGE_TYPES[img.imageType];
              return (
                <div
                  key={img.id}
                  className="group flex flex-col overflow-hidden rounded-2xl border border-border/70 bg-card transition-all hover:border-primary/50 hover:shadow-lg"
                >
                  {/* Image Viewport */}
                  <div
                    className="relative aspect-[16/10] w-full overflow-hidden bg-neutral-950 cursor-pointer"
                    onClick={() => setActiveImage(img)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => e.key === "Enter" && setActiveImage(img)}
                    aria-label={`Xem ảnh lớn: ${img.title}`}
                  >
                    <Image
                      src={img.src}
                      alt={img.alt}
                      fill
                      className="object-cover group-hover:scale-105 transition-transform duration-500"
                      sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-transparent to-black/20 pointer-events-none" />

                    {/* Type Badge */}
                    <div className="absolute top-2.5 left-2.5">
                      <span
                        className={cn(
                          "rounded-md px-2 py-0.5 text-[10px] font-semibold shadow backdrop-blur-md border",
                          typeMeta?.badgeClass || "bg-black/60 text-white border-white/10",
                        )}
                      >
                        {typeMeta?.label || "Hiện trạng"}
                      </span>
                    </div>

                    {/* Site link badge if linked */}
                    {img.siteSlug && (
                      <div className="absolute top-2.5 right-2.5">
                        <Link
                          href={`/dai-noi/cong-trinh/${img.siteSlug}`}
                          onClick={(e) => e.stopPropagation()}
                          className="rounded-full bg-primary/90 hover:bg-primary px-2.5 py-0.5 text-[10px] font-medium text-white shadow transition-colors flex items-center gap-1"
                        >
                          Hồ sơ di tích
                          <ExternalLink className="h-2.5 w-2.5" />
                        </Link>
                      </div>
                    )}

                    <div className="absolute bottom-2 left-3 right-3 text-white pointer-events-none">
                      <p className="text-xs font-semibold text-white/95 line-clamp-1 drop-shadow">
                        {img.title}
                      </p>
                    </div>
                  </div>

                  {/* Caption & Metadata */}
                  <div className="flex flex-1 flex-col justify-between p-4 space-y-3">
                    <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2">
                      {img.caption}
                    </p>

                    <div className="border-t border-border/50 pt-2 text-[11px] text-muted-foreground/80 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="truncate max-w-[180px]">
                          <strong>Nguồn:</strong> {img.creditLine}
                        </span>
                        <span className="text-primary font-medium text-[10px]">
                          {img.rightsStatus === "verified" ? "Đã cấp phép" : "Khảo sát"}
                        </span>
                      </div>
                      {img.editDisclosure && (
                        <p className="text-[10px] text-amber-600 dark:text-amber-400 font-medium">
                          Ghi chú xử lý: {img.editDisclosure}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Lightbox Modal */}
      {activeImage && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-sm p-4 animate-in fade-in duration-200"
          onClick={() => setActiveImage(null)}
        >
          <div
            className="relative max-w-4xl w-full rounded-2xl bg-card border border-border p-6 shadow-2xl space-y-4 max-h-[92vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-4 border-b border-border pb-3">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className={cn(
                      "rounded px-2 py-0.5 text-[10px] font-semibold border",
                      HERITAGE_IMAGE_TYPES[activeImage.imageType]?.badgeClass,
                    )}
                  >
                    {HERITAGE_IMAGE_TYPES[activeImage.imageType]?.label}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    Danh mục: {HERITAGE_CATEGORIES[activeImage.category]?.label}
                  </span>
                </div>
                <h3 className="font-display text-xl font-bold text-foreground">
                  {activeImage.title}
                </h3>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setActiveImage(null)}
                aria-label="Đóng cửa sổ xem ảnh"
              >
                <X className="h-5 w-5" />
              </Button>
            </div>

            <div className="relative aspect-[16/10] max-h-[60vh] w-full rounded-xl overflow-hidden bg-neutral-950 border border-border/50">
              <Image
                src={activeImage.src}
                alt={activeImage.alt}
                fill
                className="object-contain"
                sizes="(max-width: 1200px) 100vw, 1100px"
                priority
              />
            </div>

            <div className="space-y-3">
              <p className="text-sm text-foreground/90 leading-relaxed">
                {activeImage.caption}
              </p>

              <div className="rounded-xl bg-secondary/50 p-4 text-xs space-y-2 border border-border/50">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-muted-foreground">
                  <div>
                    <strong className="text-foreground">Đơn vị tư liệu / Bản quyền:</strong>{" "}
                    {activeImage.creditLine}
                  </div>
                  <div>
                    <strong className="text-foreground">Tình trạng xác minh:</strong>{" "}
                    <span className="text-emerald-600 dark:text-emerald-400 font-medium">
                      Đã thẩm định khoa học di sản
                    </span>
                  </div>
                  {activeImage.editDisclosure && (
                    <div className="sm:col-span-2 text-amber-600 dark:text-amber-400">
                      <strong>Minh bạch kỹ thuật:</strong> {activeImage.editDisclosure}
                    </div>
                  )}
                </div>

                {activeImage.siteSlug && (
                  <div className="pt-2 border-t border-border/50 flex items-center justify-between">
                    <span className="text-muted-foreground">
                      Liên kết hồ sơ công trình chính thức:
                    </span>
                    <Link
                      href={`/dai-noi/cong-trinh/${activeImage.siteSlug}`}
                      className="inline-flex items-center gap-1.5 text-primary hover:underline font-semibold"
                    >
                      Mở hồ sơ khảo cứu 7 phần
                      <ExternalLink className="h-3.5 w-3.5" />
                    </Link>
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <Button variant="outline" size="sm" onClick={() => setActiveImage(null)}>
                Đóng cửa sổ
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
