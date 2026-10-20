"use client";

import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Check, RotateCcw, Sparkles } from "lucide-react";
import {
  getHonorsTitle,
  type CertificateData,
} from "@/lib/imperial/certificate-utils";
import {
  PASSPORT_SEALS,
  PASSPORT_ZONE_META,
  type SpatialZoneSlug,
} from "@/lib/imperial/passport-storage";
import { cn } from "@/lib/utils";

export interface CertificateCustomizeModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  data: CertificateData;
  onSave: (updated: CertificateData) => void;
}

export function CertificateCustomizeModal({
  open,
  onOpenChange,
  data,
  onSave,
}: CertificateCustomizeModalProps) {
  const [studentName, setStudentName] = useState(data.studentName);
  const [schoolName, setSchoolName] = useState(data.schoolName);
  const [issueDate, setIssueDate] = useState(data.issueDate);
  const [selectedSlugs, setSelectedSlugs] = useState<string[]>(
    data.unlockedSiteSlugs,
  );

  const previewTitle = getHonorsTitle(selectedSlugs.length);

  const handleApplyPreset = (count: number) => {
    const slugs = PASSPORT_SEALS.slice(0, count).map((s) => s.slug);
    setSelectedSlugs(slugs);
  };

  const handleToggleSeal = (slug: string) => {
    setSelectedSlugs((prev) =>
      prev.includes(slug) ? prev.filter((s) => s !== slug) : [...prev, slug],
    );
  };

  const handleSave = () => {
    onSave({
      ...data,
      studentName: studentName.trim() || "Nguyễn Hoàng Minh",
      schoolName: schoolName.trim() || "Trường THPT Chuyên Quốc Học Huế",
      issueDate: issueDate.trim() || data.issueDate,
      unlockedSiteSlugs: selectedSlugs,
      totalScore: selectedSlugs.length * 100,
    });
    onOpenChange(false);
  };

  const handleReset = () => {
    setStudentName("Nguyễn Hoàng Minh");
    setSchoolName("Trường THPT Chuyên Quốc Học Huế");
    setSelectedSlugs(PASSPORT_SEALS.map((s) => s.slug));
  };

  const zones: SpatialZoneSlug[] = [
    "central-ceremonial-axis",
    "ancestral-worship-space",
    "purple-forbidden-city",
    "royal-living-gardens",
  ];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto bg-card text-foreground border-border shadow-2xl p-5 sm:p-6">
        <DialogHeader className="space-y-1">
          <DialogTitle className="font-serif text-xl sm:text-2xl font-bold flex items-center gap-2 text-foreground">
            <Sparkles className="size-5 text-amber-600" />
            <span>Tùy Chỉnh Thông Tin Chứng Nhận</span>
          </DialogTitle>
          <DialogDescription className="text-xs text-muted-foreground">
            Chỉnh sửa tên học sinh, trường lớp và mức độ ấn triện di sản để cấp bản in chính xác.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 pt-2">
          {/* Recipient Details */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label
                htmlFor="student-name-input"
                className="text-xs font-semibold text-foreground block"
              >
                Họ và Tên Học Sinh
              </label>
              <Input
                id="student-name-input"
                value={studentName}
                onChange={(e) => setStudentName(e.target.value)}
                placeholder="Nhập họ tên học sinh..."
                className="h-9 text-sm"
              />
            </div>

            <div className="space-y-1.5">
              <label
                htmlFor="school-name-input"
                className="text-xs font-semibold text-foreground block"
              >
                Trường / Lớp / Đơn Vị
              </label>
              <Input
                id="school-name-input"
                value={schoolName}
                onChange={(e) => setSchoolName(e.target.value)}
                placeholder="Trường THPT, lớp hoặc câu lạc bộ..."
                className="h-9 text-sm"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label
              htmlFor="issue-date-input"
              className="text-xs font-semibold text-foreground block"
            >
              Ngày Cấp Chứng Nhận
            </label>
            <Input
              id="issue-date-input"
              value={issueDate}
              onChange={(e) => setIssueDate(e.target.value)}
              placeholder="Huế, ngày... tháng... năm 2026"
              className="h-9 text-sm"
            />
          </div>

          {/* Honors Title Live Indicator */}
          <div className="rounded-xl border border-border/80 bg-secondary/40 p-3.5 space-y-1">
            <div className="flex items-center justify-between gap-2">
              <span className="text-[11px] uppercase font-bold text-muted-foreground tracking-wider">
                Danh hiệu tương ứng ({selectedSlugs.length}/16 ấn triện):
              </span>
              <span
                className={cn(
                  "px-2.5 py-0.5 rounded-full text-xs font-bold font-serif",
                  previewTitle.badgeClass,
                )}
              >
                {previewTitle.title}
              </span>
            </div>
            <p className="text-xs text-muted-foreground italic font-serif">
              {previewTitle.descriptionVi}
            </p>
          </div>

          {/* Quick Presets */}
          <div className="space-y-2">
            <span className="text-xs font-semibold text-foreground block">
              Mức Đóng Dấu Triện Mẫu (Presets):
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <Button
                type="button"
                variant={selectedSlugs.length === 16 ? "default" : "outline"}
                size="sm"
                className="text-xs h-8"
                onClick={() => handleApplyPreset(16)}
              >
                Bậc Thầy (16/16)
              </Button>
              <Button
                type="button"
                variant={selectedSlugs.length === 14 ? "default" : "outline"}
                size="sm"
                className="text-xs h-8"
                onClick={() => handleApplyPreset(14)}
              >
                Học Giả (14/16)
              </Button>
              <Button
                type="button"
                variant={selectedSlugs.length === 10 ? "default" : "outline"}
                size="sm"
                className="text-xs h-8"
                onClick={() => handleApplyPreset(10)}
              >
                Thám Hiểm (10/16)
              </Button>
              <Button
                type="button"
                variant={selectedSlugs.length === 6 ? "default" : "outline"}
                size="sm"
                className="text-xs h-8"
                onClick={() => handleApplyPreset(6)}
              >
                Tập Sự (6/16)
              </Button>
            </div>
          </div>

          {/* Granular Seal Checklist across 4 Zones */}
          <div className="space-y-2.5 pt-1">
            <span className="text-xs font-semibold text-foreground block">
              Chọn Từng Con Dấu Ấn Triện Đã Mở Khóa:
            </span>

            <div className="space-y-3 max-h-52 overflow-y-auto pr-1">
              {zones.map((zoneSlug) => {
                const zoneMeta = PASSPORT_ZONE_META[zoneSlug];
                const seals = PASSPORT_SEALS.filter((s) => s.zoneSlug === zoneSlug);

                return (
                  <div key={zoneSlug} className="space-y-1.5 border-b border-border/50 pb-2">
                    <span className="text-[11px] font-bold text-amber-700 dark:text-amber-400 font-serif">
                      {zoneMeta?.title} ({seals.filter((s) => selectedSlugs.includes(s.slug)).length}/{seals.length})
                    </span>

                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
                      {seals.map((seal) => {
                        const checked = selectedSlugs.includes(seal.slug);
                        return (
                          <button
                            key={seal.slug}
                            type="button"
                            onClick={() => handleToggleSeal(seal.slug)}
                            className={cn(
                              "flex items-center gap-1.5 px-2 py-1 rounded text-left text-xs border transition-colors",
                              checked
                                ? "border-amber-600 bg-amber-500/15 text-foreground font-medium"
                                : "border-border/70 bg-card/60 text-muted-foreground opacity-60 hover:opacity-100",
                            )}
                          >
                            <span
                              className={cn(
                                "size-3.5 rounded flex items-center justify-center text-[10px] shrink-0 border",
                                checked
                                  ? "bg-amber-600 text-white border-amber-600"
                                  : "border-border",
                              )}
                            >
                              {checked && <Check className="size-2.5" />}
                            </span>
                            <span className="truncate">{seal.name}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <DialogFooter className="flex flex-wrap items-center justify-between gap-2 pt-4 border-t border-border">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleReset}
            className="text-xs gap-1 text-muted-foreground hover:text-foreground"
          >
            <RotateCcw className="size-3.5" />
            <span>Khôi phục mặc định</span>
          </Button>

          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => onOpenChange(false)}
              className="text-xs"
            >
              Hủy
            </Button>
            <Button
              type="button"
              size="sm"
              onClick={handleSave}
              className="text-xs font-bold bg-amber-600 hover:bg-amber-700 text-white shadow-sm"
            >
              Áp Dụng Cho Chứng Nhận
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default CertificateCustomizeModal;
