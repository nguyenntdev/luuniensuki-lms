"use client";

import React, { useMemo, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  BookOpen,
  Calendar,
  Compass,
  FileText,
  Filter,
  Landmark,
  Search,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import type { ImperialSite, ImperialZone } from "@/lib/imperial/map-types";

export interface MapListFallbackProps {
  sites: ImperialSite[];
  zones: ImperialZone[];
  onSelectSite?: (site: ImperialSite) => void;
  className?: string;
}

export function MapListFallback({
  sites,
  zones,
  onSelectSite,
  className,
}: MapListFallbackProps) {
  const [search, setSearch] = useState("");
  const [selectedZone, setSelectedZone] = useState<string>("all");
  const [viewMode, setViewMode] = useState<"cards" | "table">("cards");

  const filteredSites = useMemo(() => {
    return sites.filter((site) => {
      if (selectedZone !== "all" && site.zone_slug !== selectedZone) {
        return false;
      }
      if (search.trim()) {
        const q = search.toLowerCase().trim();
        const matchName = site.name_vi.toLowerCase().includes(q);
        const matchHan =
          site.name_han_nom?.includes(q) || site.chinese_name?.includes(q);
        const matchAlt = site.alternative_names?.some((alt) =>
          alt.toLowerCase().includes(q),
        );
        const matchSummary =
          site.historical_summary?.toLowerCase().includes(q) ||
          site.description_vi?.toLowerCase().includes(q);
        if (!matchName && !matchHan && !matchAlt && !matchSummary) return false;
      }
      return true;
    });
  }, [sites, selectedZone, search]);

  const zoneTitleMap = useMemo(() => {
    const map: Record<string, string> = {};
    zones.forEach((z) => {
      map[z.slug] = z.title_vi;
    });
    return map;
  }, [zones]);

  return (
    <section
      id="danh-sach"
      aria-label="Danh mục công trình Đại Nội Huế"
      className={cn("w-full space-y-6", className)}
    >
      {/* Header & Accessibility Info */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl md:text-2xl font-serif font-bold text-foreground flex items-center gap-2">
            <Landmark className="w-5 h-5 text-primary" />
            <span>Danh mục di tích & công trình lịch sử</span>
          </h2>
          <p className="text-xs md:text-sm text-muted-foreground mt-0.5">
            Giao diện tra cứu dễ tiếp cận hỗ trợ trình đọc màn hình, kết nối băng thông thấp và tìm kiếm tức thì.
          </p>
        </div>

        {/* View Mode Toggle Buttons */}
        <div className="flex items-center gap-2 self-start md:self-auto">
          <Button
            variant={viewMode === "cards" ? "default" : "outline"}
            size="xs"
            onClick={() => setViewMode("cards")}
          >
            Thẻ tóm tắt
          </Button>
          <Button
            variant={viewMode === "table" ? "default" : "outline"}
            size="xs"
            onClick={() => setViewMode("table")}
          >
            Bảng tra cứu
          </Button>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Tìm theo tên (ví dụ: Ngọ Môn, Thái Hòa, 午門, lầu Ngũ Phụng)..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 bg-card/60 border-border/80 text-sm h-10 rounded-xl"
          />
        </div>

        {/* Zone Tabs */}
        <Tabs
          value={selectedZone}
          onValueChange={setSelectedZone}
          className="w-full sm:w-auto"
        >
          <TabsList className="bg-secondary/70 h-10 p-1 rounded-xl">
            <TabsTrigger value="all" className="text-xs rounded-lg px-3">
              Tất cả ({sites.length})
            </TabsTrigger>
            {zones.map((zone) => (
              <TabsTrigger
                key={zone.slug}
                value={zone.slug}
                className="text-xs rounded-lg px-2.5"
              >
                {zone.title_vi}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </div>

      {/* Results View */}
      {filteredSites.length === 0 ? (
        <div className="p-12 text-center rounded-2xl border border-dashed border-border/80 bg-card/40">
          <Filter className="w-8 h-8 text-muted-foreground mx-auto mb-2 opacity-50" />
          <p className="text-sm font-medium text-foreground">
            Không tìm thấy công trình phù hợp
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Vui lòng thử từ khóa khác hoặc chuyển phân khu tìm kiếm.
          </p>
        </div>
      ) : viewMode === "cards" ? (
        /* Cards View */
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredSites.map((site) => (
            <article
              key={site.slug}
              className="flex flex-col justify-between p-5 rounded-2xl bg-card/70 border border-border/70 hover:border-primary/50 hover:bg-card/90 transition-all duration-200 shadow-sm group"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <Badge
                    variant="outline"
                    className="text-[10px] font-medium bg-primary/10 text-primary border-primary/20"
                  >
                    {zoneTitleMap[site.zone_slug || ""] || "Đại Nội Huế"}
                  </Badge>
                  {site.condition === "extant" ? (
                    <Badge
                      variant="outline"
                      className="text-[10px] bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                    >
                      Bảo tồn nguyên vẹn
                    </Badge>
                  ) : site.condition === "reconstructed" ? (
                    <Badge
                      variant="outline"
                      className="text-[10px] bg-sky-500/10 text-sky-400 border-sky-500/20"
                    >
                      Đã phục dựng
                    </Badge>
                  ) : (
                    <Badge
                      variant="outline"
                      className="text-[10px] bg-amber-500/10 text-amber-400 border-amber-500/20"
                    >
                      Nền móng / Phế tích
                    </Badge>
                  )}
                </div>

                <div>
                  <h3 className="text-lg font-serif font-bold text-foreground group-hover:text-primary transition-colors flex items-baseline gap-2">
                    <span>{site.name_vi}</span>
                    {(site.name_han_nom || site.chinese_name) && (
                      <span className="text-amber-500 font-serif font-normal text-base">
                        {site.name_han_nom || site.chinese_name}
                      </span>
                    )}
                  </h3>
                  {(site.construction_year || site.reign) && (
                    <p className="text-xs text-muted-foreground mt-0.5 flex items-center gap-1">
                      <Calendar className="w-3 h-3 text-amber-500/80" />
                      <span>
                        {site.construction_year ? `Năm ${site.construction_year}` : ""}
                        {site.reign ? ` (Triều vua ${site.reign})` : ""}
                      </span>
                    </p>
                  )}
                </div>

                <p className="text-xs text-foreground/80 line-clamp-3 leading-relaxed">
                  {site.historical_summary ||
                    site.description_vi ||
                    "Công trình tiêu biểu thuộc Quần thể Di tích Cố đô Huế."}
                </p>
              </div>

              <div className="pt-4 mt-4 border-t border-border/50 flex items-center justify-between">
                <Button
                  variant="ghost"
                  size="xs"
                  onClick={() => onSelectSite?.(site)}
                  className="text-xs font-medium text-muted-foreground hover:text-foreground"
                >
                  <Compass className="w-3.5 h-3.5 mr-1" />
                  Định vị trên bản đồ
                </Button>

                <Button
                  asChild
                  variant="outline"
                  size="xs"
                  className="text-xs font-semibold group-hover:border-primary/40"
                >
                  <Link href={`/dai-noi/cong-trinh/${site.slug}`}>
                    Chi tiết &rarr;
                  </Link>
                </Button>
              </div>
            </article>
          ))}
        </div>
      ) : (
        /* Accessible Table View */
        <div className="rounded-2xl border border-border/70 overflow-hidden bg-card/60 shadow-sm">
          <Table>
            <TableHeader className="bg-secondary/60">
              <TableRow>
                <TableHead className="font-semibold text-xs">Tên công trình</TableHead>
                <TableHead className="font-semibold text-xs">Chữ Hán</TableHead>
                <TableHead className="font-semibold text-xs">Phân khu</TableHead>
                <TableHead className="font-semibold text-xs">Niên đại / Vua</TableHead>
                <TableHead className="font-semibold text-xs">Hiện trạng</TableHead>
                <TableHead className="text-right font-semibold text-xs">Thao tác</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredSites.map((site) => (
                <TableRow key={site.slug} className="hover:bg-secondary/30">
                  <TableCell className="font-serif font-bold text-sm text-foreground">
                    {site.name_vi}
                  </TableCell>
                  <TableCell className="font-serif text-amber-500 text-sm">
                    {site.name_han_nom || site.chinese_name || "—"}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {zoneTitleMap[site.zone_slug || ""] || "Đại Nội Huế"}
                  </TableCell>
                  <TableCell className="text-xs text-foreground/80">
                    {site.construction_year || "—"}
                    {site.reign ? ` (${site.reign})` : ""}
                  </TableCell>
                  <TableCell className="text-xs">
                    {site.condition === "extant" ? (
                      <span className="text-emerald-400 font-medium">Nguyên vẹn</span>
                    ) : site.condition === "reconstructed" ? (
                      <span className="text-sky-400 font-medium">Phục dựng</span>
                    ) : (
                      <span className="text-amber-400 font-medium">Nền móng</span>
                    )}
                  </TableCell>
                  <TableCell className="text-right space-x-2">
                    <Button
                      variant="ghost"
                      size="xs"
                      onClick={() => onSelectSite?.(site)}
                      className="text-xs text-muted-foreground"
                    >
                      Định vị
                    </Button>
                    <Button asChild variant="outline" size="xs" className="text-xs">
                      <Link href={`/dai-noi/cong-trinh/${site.slug}`}>
                        Hồ sơ
                      </Link>
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </section>
  );
}
