"use client";

import React, { useMemo, useState } from "react";
import Link from "next/link";
import {
  BookOpen,
  Check,
  ChevronRight,
  ExternalLink,
  Eye,
  Filter,
  History,
  Layers,
  MapPin,
  Palette,
  Search,
  Sparkles,
  Volume2,
} from "lucide-react";

import ImperialHeader from "@/components/imperial/shell/ImperialHeader";
import ImperialAiAssistant from "@/components/imperial/ai/ImperialAiAssistant";
import { ArtDetailModal } from "@/components/imperial/art-detail/ArtDetailModal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  STORY_TYPE_METADATA,
  type ImperialArtDetail,
} from "@/lib/imperial/v51-types";

interface MyThuatGalleryClientProps {
  initialDetails: ImperialArtDetail[];
}

type ArtThemeFilter =
  | "all"
  | "mosaic"
  | "phap-lam"
  | "bronze"
  | "woodcarving"
  | "throne";

interface ThemeTab {
  id: ArtThemeFilter;
  label: string;
  countKey?: string;
}

const THEME_TABS: ThemeTab[] = [
  { id: "all", label: "Tất cả mỹ thuật" },
  { id: "mosaic", label: "Khảm sành sứ (Kiến Trung, Khải Thành)" },
  { id: "phap-lam", label: "Pháp lam hoàng cung (Bờ nóc, Nghi môn)" },
  { id: "bronze", label: "Đúc đồng Vạc đồng & Thần công" },
  { id: "woodcarving", label: "Chạm thủng sơn thếp (Thái Hòa, Thế Miếu)" },
  { id: "throne", label: "Ngai vàng Hoàng đế" },
];

export default function MyThuatGalleryClient({
  initialDetails,
}: MyThuatGalleryClientProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTheme, setSelectedTheme] = useState<ArtThemeFilter>("all");
  const [selectedSite, setSelectedSite] = useState<string>("all");
  const [quickViewDetail, setQuickViewDetail] = useState<ImperialArtDetail | null>(null);

  // Extract unique sites from details
  const siteOptions = useMemo(() => {
    const map = new Map<string, string>();
    initialDetails.forEach((d) => {
      if (d.site_slug && d.site_name_vi) {
        map.set(d.site_slug, d.site_name_vi);
      }
    });
    return Array.from(map.entries());
  }, [initialDetails]);

  // Filter logic
  const filteredDetails = useMemo(() => {
    return initialDetails.filter((item) => {
      // 1. Text Search
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase().trim();
        const matchesQuery =
          item.title.toLowerCase().includes(query) ||
          (item.motif && item.motif.toLowerCase().includes(query)) ||
          (item.material && item.material.toLowerCase().includes(query)) ||
          (item.technique && item.technique.toLowerCase().includes(query)) ||
          (item.site_name_vi && item.site_name_vi.toLowerCase().includes(query)) ||
          (item.description_observation &&
            item.description_observation.toLowerCase().includes(query));

        if (!matchesQuery) return false;
      }

      // 2. Site Filter
      if (selectedSite !== "all" && item.site_slug !== selectedSite) {
        return false;
      }

      // 3. Theme Filter
      if (selectedTheme === "mosaic") {
        return (
          item.kind === "mosaic" ||
          item.slug.includes("kham-sanh-su") ||
          item.title.toLowerCase().includes("sành sứ")
        );
      }
      if (selectedTheme === "phap-lam") {
        return (
          item.slug.includes("phap-lam") ||
          item.title.toLowerCase().includes("pháp lam") ||
          (item.technique && item.technique.toLowerCase().includes("pháp lam"))
        );
      }
      if (selectedTheme === "bronze") {
        return (
          item.slug.includes("vac-dong") ||
          item.slug.includes("than-cong") ||
          item.title.toLowerCase().includes("vạc đồng") ||
          item.title.toLowerCase().includes("súng thần công") ||
          (item.material && item.material.toLowerCase().includes("đồng"))
        );
      }
      if (selectedTheme === "woodcarving") {
        return (
          item.slug.includes("cham-thung") ||
          item.slug.includes("rong-may") ||
          (item.kind === "carving" && !item.slug.includes("vac-dong") && !item.slug.includes("than-cong")) ||
          item.title.toLowerCase().includes("sơn son")
        );
      }
      if (selectedTheme === "throne") {
        return (
          item.slug.includes("ngai-vang") ||
          item.title.toLowerCase().includes("ngai vàng")
        );
      }

      return true;
    });
  }, [initialDetails, searchQuery, selectedSite, selectedTheme]);

  return (
    <div className="min-h-screen bg-background flex flex-col selection:bg-primary/20 selection:text-primary">
      {/* Imperial Navigation Bar */}
      <ImperialHeader />

      <main className="flex-1">
        {/* Breadcrumb Navigation */}
        <div className="border-b border-border/60 bg-muted/20">
          <div className="mx-auto flex h-11 max-w-7xl items-center px-4 sm:px-6">
            <nav
              aria-label="Breadcrumb"
              className="flex items-center space-x-1.5 text-xs text-muted-foreground"
            >
              <Link href="/dai-noi" className="hover:text-foreground transition-colors">
                Đại Nội Huế
              </Link>
              <ChevronRight className="w-3.5 h-3.5 shrink-0" />
              <span className="font-medium text-foreground">
                Mỹ thuật Hoàng cung Triều Nguyễn
              </span>
            </nav>
          </div>
        </div>

        {/* Hero Section */}
        <section className="relative overflow-hidden border-b border-border/70 bg-gradient-to-b from-[#5C1010]/15 via-background to-background py-10 sm:py-14">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 relative z-10 space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="bg-primary/10 text-primary border-primary/30 text-xs">
                <Sparkles className="w-3.5 h-3.5 mr-1" />
                STTTNNĐ V5.1 Khảo Cứu Mỹ Thuật
              </Badge>
              <Badge variant="secondary" className="text-xs">
                100% Đối chiếu Chính sử & Hồ sơ Bảo vật Quốc gia
              </Badge>
            </div>

            <div className="max-w-3xl space-y-2">
              <h1 className="text-2xl sm:text-4xl font-serif font-black tracking-tight text-foreground">
                Mỹ Thuật Cung Đình Triều Nguyễn
              </h1>
              <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
                Khám phá kho tư liệu khảo cứu đồ án trang trí, kỹ nghệ tạo tác cung đình và biểu tượng quyền lực: từ nghệ thuật khảm sành sứ đa sắc, pháp lam nung trên cốt đồng, đúc đồng súng thần công & vạc đồng, đến chạm thủng sơn son thếp vàng và chiếc Ngai vàng tối thượng.
              </p>
            </div>

            {/* Quick Stats Banner */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 max-w-3xl">
              <div className="bg-card/70 border border-border/60 rounded-lg p-3">
                <span className="text-xl sm:text-2xl font-serif font-bold text-primary block">
                  {initialDetails.length}
                </span>
                <span className="text-xs text-muted-foreground">Hồ sơ khảo cứu chi tiết</span>
              </div>
              <div className="bg-card/70 border border-border/60 rounded-lg p-3">
                <span className="text-xl sm:text-2xl font-serif font-bold text-amber-600 dark:text-amber-400 block">
                  5
                </span>
                <span className="text-xs text-muted-foreground">Chuyên đề mỹ thuật cung đình</span>
              </div>
              <div className="bg-card/70 border border-border/60 rounded-lg p-3">
                <span className="text-xl sm:text-2xl font-serif font-bold text-emerald-600 dark:text-emerald-400 block">
                  100%
                </span>
                <span className="text-xs text-muted-foreground">Có nguồn sử liệu đối chiếu</span>
              </div>
              <div className="bg-card/70 border border-border/60 rounded-lg p-3">
                <span className="text-xl sm:text-2xl font-serif font-bold text-purple-600 dark:text-purple-400 block">
                  UNESCO
                </span>
                <span className="text-xs text-muted-foreground">Bảo vật & Ký ức Thế giới</span>
              </div>
            </div>
          </div>
        </section>

        {/* Filter and Content Container */}
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 space-y-6">
          {/* Controls Bar: Search & Selectors */}
          <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
            {/* Search Input */}
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Tìm theo họa tiết, chất liệu, kỹ thuật hoặc công trình..."
                className="pl-9 text-xs sm:text-sm h-10 bg-card border-border/70"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery("")}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground hover:text-foreground"
                >
                  Xóa
                </button>
              )}
            </div>

            {/* Site selector dropdown */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground flex items-center gap-1 shrink-0">
                <Filter className="w-3.5 h-3.5" />
                Công trình:
              </span>
              <select
                value={selectedSite}
                onChange={(e) => setSelectedSite(e.target.value)}
                className="text-xs bg-card border border-border/70 rounded-md px-3 py-2 focus:ring-1 focus:ring-primary focus:outline-none"
              >
                <option value="all">Tất cả di tích ({initialDetails.length})</option>
                {siteOptions.map(([slug, name]) => (
                  <option key={slug} value={slug}>
                    {name}
                  </option>
                ))}
              </select>

              {/* Admin Studio link */}
              <Link href="/admin/dai-noi/chi-tiet-my-thuat">
                <Button variant="outline" size="sm" className="h-9 text-xs gap-1.5 hidden sm:flex">
                  <Palette className="w-3.5 h-3.5 text-primary" />
                  Studio Biên tập
                </Button>
              </Link>
            </div>
          </div>

          {/* Theme Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-2 scrollbar-none">
            {THEME_TABS.map((tab) => {
              const active = selectedTheme === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setSelectedTheme(tab.id)}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors shrink-0 ${
                    active
                      ? "bg-primary text-primary-foreground shadow-xs font-semibold"
                      : "bg-muted/50 text-muted-foreground hover:bg-muted hover:text-foreground border border-border/40"
                  }`}
                >
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Gallery Grid */}
          {filteredDetails.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 pt-2">
              {filteredDetails.map((detail) => {
                const storyMeta =
                  STORY_TYPE_METADATA[detail.story_type] ||
                  STORY_TYPE_METADATA.documented_event;

                return (
                  <Card
                    key={detail.id || detail.slug}
                    className="overflow-hidden border-border/70 hover:border-primary/50 transition-all duration-200 flex flex-col bg-card/70 group hover:shadow-md"
                  >
                    {/* Media Preview Box */}
                    <div className="relative aspect-[16/10] bg-muted overflow-hidden">
                      {detail.image_url ? (
                        <img
                          src={detail.image_url}
                          alt={detail.title}
                          className="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-300"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                          <Palette className="w-10 h-10 opacity-30" />
                        </div>
                      )}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent pointer-events-none" />

                      {/* Top Badges */}
                      <div className="absolute top-2.5 left-2.5 right-2.5 flex items-center justify-between gap-2">
                        <Badge
                          variant="secondary"
                          className="text-[11px] backdrop-blur-md bg-black/60 text-white border-white/20 capitalize"
                        >
                          {detail.kind === "carving"
                            ? "Chạm khắc"
                            : detail.kind === "mosaic"
                            ? "Khảm sành sứ"
                            : detail.kind === "relief"
                            ? "Pháp lam / Phù điêu"
                            : "Mỹ thuật cung đình"}
                        </Badge>

                        <Badge
                          variant="outline"
                          className={`text-[10px] font-medium backdrop-blur-md bg-black/60 ${storyMeta.badgeColor}`}
                        >
                          {storyMeta.label}
                        </Badge>
                      </div>

                      {/* Bottom Site Name overlay */}
                      <div className="absolute bottom-2.5 left-2.5 right-2.5 text-white flex items-center justify-between text-xs">
                        <span className="flex items-center gap-1 font-medium text-white/90 truncate">
                          <MapPin className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                          {detail.site_name_vi || "Đại Nội Huế"}
                        </span>
                        {detail.claim_sources && detail.claim_sources.length > 0 && (
                          <span className="text-[11px] text-white/80 shrink-0">
                            {detail.claim_sources.length} sử liệu
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Card Body */}
                    <CardContent className="p-4 flex-1 flex flex-col justify-between space-y-3">
                      <div className="space-y-1.5">
                        <h2 className="font-serif font-bold text-base text-foreground group-hover:text-primary transition-colors line-clamp-2">
                          {detail.title}
                        </h2>

                        {detail.motif && (
                          <p className="text-xs text-muted-foreground line-clamp-1">
                            <span className="font-medium text-foreground/80">Đồ án:</span>{" "}
                            {detail.motif}
                          </p>
                        )}

                        {detail.description_observation && (
                          <p className="text-xs text-muted-foreground line-clamp-3 leading-relaxed pt-1">
                            {detail.description_observation}
                          </p>
                        )}
                      </div>

                      {/* Material & Technique Tags */}
                      <div className="pt-2 border-t border-border/50 flex flex-wrap gap-1.5 text-[11px]">
                        {detail.material && (
                          <span className="bg-muted px-2 py-0.5 rounded text-muted-foreground truncate max-w-[150px]">
                            {detail.material}
                          </span>
                        )}
                        {detail.technique && (
                          <span className="bg-muted px-2 py-0.5 rounded text-muted-foreground truncate max-w-[150px]">
                            {detail.technique}
                          </span>
                        )}
                      </div>

                      {/* Card Action Buttons */}
                      <div className="pt-2 flex items-center justify-between gap-2 border-t border-border/40">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setQuickViewDetail(detail)}
                          className="h-8 text-xs gap-1 text-muted-foreground hover:text-foreground"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          Xem nhanh
                        </Button>

                        <Link href={`/dai-noi/my-thuat/${detail.slug}`} className="flex-1">
                          <Button
                            variant="secondary"
                            size="sm"
                            className="w-full h-8 text-xs gap-1 font-medium group/btn"
                          >
                            <span>Hồ sơ 6 phần</span>
                            <ExternalLink className="w-3 h-3 group-hover/btn:translate-x-0.5 transition-transform" />
                          </Button>
                        </Link>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          ) : (
            <div className="py-20 text-center rounded-xl border border-dashed border-border p-8 space-y-3">
              <Palette className="w-10 h-10 mx-auto text-muted-foreground/40" />
              <p className="font-serif font-semibold text-foreground">
                Không tìm thấy chi tiết mỹ thuật phù hợp
              </p>
              <p className="text-xs text-muted-foreground max-w-md mx-auto">
                Hãy thử thay đổi từ khóa tìm kiếm hoặc chọn lại chuyên đề mỹ thuật khác.
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSearchQuery("");
                  setSelectedTheme("all");
                  setSelectedSite("all");
                }}
                className="text-xs mt-2"
              >
                Đặt lại bộ lọc
              </Button>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border/60 bg-card/40 py-8 text-center text-xs text-muted-foreground mt-16">
        <div className="mx-auto max-w-7xl px-4 space-y-2">
          <p className="font-semibold text-foreground/80">
            Lưu Niên — Khảo cứu mỹ thuật & điển tích Đại Nội Huế
          </p>
          <p>
            Dữ liệu đối chiếu từ Đại Nam Thực Lục Chính Biên & Khâm Định Đại Nam Hội Điển Sự Lệ
          </p>
          <div className="pt-2 flex justify-center gap-4 text-primary">
            <Link href="/dai-noi" className="hover:underline">Bản đồ không ảnh</Link>
            <span>•</span>
            <Link href="/dai-noi/thu-vien-anh" className="hover:underline">Kho ảnh di sản</Link>
            <span>•</span>
            <Link href="/dai-noi/nguon" className="hover:underline">Mục lục nguồn sử liệu</Link>
          </div>
        </div>
      </footer>

      {/* Quick View Modal */}
      <ArtDetailModal
        isOpen={Boolean(quickViewDetail)}
        onClose={() => setQuickViewDetail(null)}
        artDetail={quickViewDetail}
        variant="dialog"
      />

      {/* Scope-Locked Cultural AI Assistant */}
      <ImperialAiAssistant />
    </div>
  );
}
