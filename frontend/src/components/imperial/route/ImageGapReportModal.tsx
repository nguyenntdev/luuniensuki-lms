"use client";

import React, { useState } from "react";
import {
  Camera,
  CameraOff,
  CheckCircle2,
  AlertTriangle,
  Info,
  Shield,
  Upload,
  Search,
  Filter,
  X,
  Layers,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  getAllSitesImageCompleteness,
  type ImageCompletenessStatus,
  type SiteImageCompleteness,
} from "@/lib/imperial/image-completeness";

interface ImageGapReportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ImageGapReportModal({ isOpen, onClose }: ImageGapReportModalProps) {
  const allCompleteness = getAllSitesImageCompleteness();
  const [filterStatus, setFilterStatus] = useState<ImageCompletenessStatus | "all">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedSite, setExpandedSite] = useState<string | null>(null);

  // Statistics
  const totalSites = allCompleteness.length; // 16
  const completeSites = allCompleteness.filter((s) => s.status === "complete").length;
  const partialSites = allCompleteness.filter((s) => s.status === "partial").length;
  const missingSites = allCompleteness.filter((s) => s.status === "missing").length;

  const filteredSites = allCompleteness.filter((site) => {
    if (filterStatus !== "all" && site.status !== filterStatus) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        site.siteNameVi.toLowerCase().includes(q) ||
        site.zoneTitle.toLowerCase().includes(q) ||
        site.siteSlug.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-3xl p-6 max-h-[90vh] flex flex-col">
        <DialogHeader className="space-y-1.5 text-left border-b border-border/70 pb-4">
          <div className="flex items-center gap-2">
            <Camera className="h-5 w-5 text-primary" />
            <span className="text-xs font-bold uppercase tracking-wider text-primary">
              Báo cáo nghiệm thu tư liệu hình ảnh
            </span>
          </div>

          <DialogTitle className="font-serif text-xl sm:text-2xl font-bold text-foreground">
            Báo cáo độ hoàn thiện ảnh di tích Đại Nội Huế (16 công trình)
          </DialogTitle>

          <DialogDescription className="text-xs text-muted-foreground leading-relaxed">
            Kiểm kê và minh bạch 100% tình trạng dữ liệu ảnh thực tế, ảnh đã xử lý và ảnh thiếu theo chuẩn đặc tả khoa học Spec Patch V2.2.
          </DialogDescription>
        </DialogHeader>

        {/* Aggregated Statistics Summary */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 py-3 border-b border-border/50 text-xs">
          <div className="rounded-xl border border-border/70 bg-card p-3">
            <span className="text-[10px] uppercase font-bold text-muted-foreground block">
              Tổng số công trình
            </span>
            <strong className="text-lg font-bold text-foreground">{totalSites} di tích</strong>
          </div>

          <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3">
            <span className="text-[10px] uppercase font-bold text-emerald-700 dark:text-emerald-400 block">
              Đầy đủ ảnh hiện trạng
            </span>
            <strong className="text-lg font-bold text-emerald-700 dark:text-emerald-400">
              {completeSites} di tích
            </strong>
          </div>

          <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3">
            <span className="text-[10px] uppercase font-bold text-amber-700 dark:text-amber-400 block">
              Một phần (Cần thêm chi tiết)
            </span>
            <strong className="text-lg font-bold text-amber-700 dark:text-amber-400">
              {partialSites} di tích
            </strong>
          </div>

          <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3">
            <span className="text-[10px] uppercase font-bold text-red-700 dark:text-red-400 block">
              Chưa có ảnh thực tế
            </span>
            <strong className="text-lg font-bold text-red-700 dark:text-red-400">
              {missingSites} di tích
            </strong>
          </div>
        </div>

        {/* Search & Filter Toolbar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 py-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Tìm theo tên công trình hoặc phân khu..."
              className="w-full rounded-xl border border-border bg-background pl-9 pr-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-primary/40"
            />
          </div>

          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={() => setFilterStatus("all")}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-colors ${
                filterStatus === "all" ? "bg-primary text-primary-foreground" : "bg-secondary text-muted-foreground"
              }`}
            >
              Tất cả ({totalSites})
            </button>
            <button
              type="button"
              onClick={() => setFilterStatus("complete")}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-colors ${
                filterStatus === "complete" ? "bg-emerald-600 text-white" : "bg-secondary text-muted-foreground"
              }`}
            >
              Đầy đủ ({completeSites})
            </button>
            <button
              type="button"
              onClick={() => setFilterStatus("partial")}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-colors ${
                filterStatus === "partial" ? "bg-amber-600 text-white" : "bg-secondary text-muted-foreground"
              }`}
            >
              Một phần ({partialSites})
            </button>
            <button
              type="button"
              onClick={() => setFilterStatus("missing")}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-colors ${
                filterStatus === "missing" ? "bg-red-600 text-white" : "bg-secondary text-muted-foreground"
              }`}
            >
              Thiếu ảnh ({missingSites})
            </button>
          </div>
        </div>

        {/* Scrollable Monument Completeness List */}
        <div className="flex-1 overflow-y-auto space-y-2.5 pr-1 scrollbar-thin">
          {filteredSites.map((site) => {
            const isExpanded = expandedSite === site.siteSlug;

            return (
              <div
                key={site.siteSlug}
                className="rounded-xl border border-border/70 bg-card p-3.5 transition-all space-y-2"
              >
                <div
                  className="flex items-center justify-between gap-3 cursor-pointer select-none"
                  onClick={() => setExpandedSite(isExpanded ? null : site.siteSlug)}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span
                      className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                        site.status === "complete"
                          ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400"
                          : site.status === "partial"
                          ? "bg-amber-500/15 text-amber-600 dark:text-amber-400"
                          : "bg-red-500/15 text-red-600 dark:text-red-400"
                      }`}
                    >
                      {site.status === "complete" ? (
                        <CheckCircle2 className="h-3.5 w-3.5" />
                      ) : site.status === "partial" ? (
                        <AlertTriangle className="h-3.5 w-3.5" />
                      ) : (
                        <CameraOff className="h-3.5 w-3.5" />
                      )}
                    </span>

                    <div className="min-w-0">
                      <div className="flex items-baseline gap-2">
                        <strong className="font-serif text-sm font-bold text-foreground truncate">
                          {site.siteNameVi}
                        </strong>
                      </div>
                      <span className="text-[10px] text-muted-foreground">
                        {site.zoneTitle}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold ${
                        site.status === "complete"
                          ? "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30"
                          : site.status === "partial"
                          ? "bg-amber-500/15 text-amber-700 dark:text-amber-400 border border-amber-500/30"
                          : "bg-red-500/15 text-red-700 dark:text-red-400 border border-red-500/30"
                      }`}
                    >
                      {site.status === "complete"
                        ? `${site.totalImages} ảnh thực tế`
                        : site.status === "partial"
                        ? `${site.totalImages} ảnh (Một phần)`
                        : "0 ảnh (Chưa có)"}
                    </span>

                    {isExpanded ? (
                      <ChevronUp className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-muted-foreground" />
                    )}
                  </div>
                </div>

                {/* Expanded Details View */}
                {isExpanded && (
                  <div className="pt-2 border-t border-border/50 text-xs space-y-2 animate-in fade-in duration-150">
                    <p className="text-muted-foreground leading-relaxed italic font-serif">
                      {site.historicalContextNote}
                    </p>

                    {site.missingItems.length > 0 ? (
                      <div className="rounded-lg bg-secondary/40 p-2.5 space-y-1">
                        <strong className="text-foreground text-[11px] block">
                          Các danh mục ảnh cần bổ sung:
                        </strong>
                        <ul className="space-y-1 text-muted-foreground text-[11px]">
                          {site.missingItems.map((item, i) => (
                            <li key={i} className="flex items-start gap-1.5">
                              <span className="h-1 w-1 rounded-full bg-amber-500 mt-1.5 shrink-0" />
                              <span>{item}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ) : (
                      <div className="rounded-lg bg-emerald-500/10 border border-emerald-500/20 p-2 text-xs text-emerald-700 dark:text-emerald-400 flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 shrink-0" />
                        <span>Đã có đầy đủ góc chụp mặt tiền, cấu kiện và bối cảnh phục vụ học tập.</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Footer info note */}
        <div className="pt-3 border-t border-border/70 flex items-center justify-between text-xs text-muted-foreground">
          <span className="italic text-[11px]">
            * 100% hình ảnh trong kho Lưu Niên được thẩm định bản quyền giáo dục Fair-Use.
          </span>
          <Button variant="outline" size="sm" onClick={onClose} className="h-8 text-xs">
            Đóng báo cáo
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
