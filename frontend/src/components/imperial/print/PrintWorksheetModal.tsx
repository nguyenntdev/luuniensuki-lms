"use client";

import React, { useState, useMemo } from "react";
import {
  Printer,
  Sparkles,
  Layers,
  FileSpreadsheet,
  QrCode,
  GraduationCap,
  Eye,
  Settings2,
  Check,
  CheckCircle2,
  FileCheck,
  Building2,
  RotateCcw,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  ALL_16_PRINTABLE_STATIONS,
  STANDARD_4_STATIONS_SLUGS,
  STATION_CLUSTERS,
} from "./worksheetData";
import { WorksheetPrintConfig } from "./types";
import PrintableFieldworkWorksheet from "./PrintableFieldworkWorksheet";
import { cn } from "@/lib/utils";

interface PrintWorksheetModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initialTeacherMode?: boolean;
}

export default function PrintWorksheetModal({
  open,
  onOpenChange,
  initialTeacherMode = false,
}: PrintWorksheetModalProps) {
  const [config, setConfig] = useState<WorksheetPrintConfig>({
    school_name: "TRƯỜNG THPT CHUYÊN QUỐC HỌC HUẾ",
    department_name: "Tổ Lịch sử - Địa lý",
    lesson_code: "KHTN-LS10-DN01",
    grade_level: "Lớp 10 THPT",
    class_name: "10 Sử",
    student_name: "",
    teacher_name: "",
    date_vi: "",
    orientation: "landscape",
    teacher_key_mode: initialTeacherMode,
    include_qr: true,
    include_rubric: true,
    include_exit_ticket: true,
    selected_monument_slugs: STANDARD_4_STATIONS_SLUGS,
  });

  const [activeCluster, setActiveCluster] = useState<string>("standard_4");
  const [activeTab, setActiveTab] = useState<"config" | "preview">("config");

  // Filter stations based on selection
  const selectedStations = useMemo(() => {
    const slugSet = new Set(config.selected_monument_slugs);
    return ALL_16_PRINTABLE_STATIONS.filter((st) => slugSet.has(st.monument_slug));
  }, [config.selected_monument_slugs]);

  const handleSelectCluster = (clusterId: string, slugs: string[]) => {
    setActiveCluster(clusterId);
    setConfig((prev) => ({
      ...prev,
      selected_monument_slugs: slugs,
    }));
  };

  const handleToggleMonument = (slug: string) => {
    setActiveCluster("custom");
    setConfig((prev) => {
      const exists = prev.selected_monument_slugs.includes(slug);
      let nextSlugs: string[];
      if (exists) {
        if (prev.selected_monument_slugs.length <= 1) return prev; // Keep at least 1
        nextSlugs = prev.selected_monument_slugs.filter((s) => s !== slug);
      } else {
        nextSlugs = [...prev.selected_monument_slugs, slug];
      }
      return {
        ...prev,
        selected_monument_slugs: nextSlugs,
      };
    });
  };

  const handlePrint = () => {
    if (typeof window !== "undefined") {
      window.print();
    }
  };

  const handleResetDefaults = () => {
    setActiveCluster("standard_4");
    setConfig({
      school_name: "TRƯỜNG THPT CHUYÊN QUỐC HỌC HUẾ",
      department_name: "Tổ Lịch sử - Địa lý",
      lesson_code: "KHTN-LS10-DN01",
      grade_level: "Lớp 10 THPT",
      class_name: "10 Sử",
      student_name: "",
      teacher_name: "",
      date_vi: "",
      orientation: "landscape",
      teacher_key_mode: initialTeacherMode,
      include_qr: true,
      include_rubric: true,
      include_exit_ticket: true,
      selected_monument_slugs: STANDARD_4_STATIONS_SLUGS,
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="max-w-5xl w-[96vw] max-h-[92vh] flex flex-col p-0 overflow-hidden bg-background border-border shadow-2xl print:border-none print:shadow-none print:max-w-none print:w-full print:h-auto print:static print:inset-0"
      >
        {/* Modal Header */}
        <div className="p-4 sm:p-5 border-b border-border/80 bg-card flex flex-wrap items-center justify-between gap-3 print:hidden">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs bg-primary/10 text-primary border-primary/20 gap-1.5">
                <FileSpreadsheet className="size-3.5" />
                <span>Chuẩn Công văn 5512/BGDĐT & CT GDPT 2018</span>
              </Badge>
              <Badge
                variant={config.teacher_key_mode ? "default" : "secondary"}
                className={cn(
                  "text-xs transition-colors",
                  config.teacher_key_mode && "bg-amber-600 hover:bg-amber-700 text-white"
                )}
              >
                {config.teacher_key_mode ? "Bản Giáo Viên (Có Đáp Án)" : "Bản Học Sinh (Điền Dã)"}
              </Badge>
            </div>
            <DialogTitle className="font-serif font-bold text-lg sm:text-xl text-foreground">
              Xuất Phiếu Điền Dã 4 Cột In Sẵn (Khổ A4 Chuẩn In 1-Click)
            </DialogTitle>
            <DialogDescription className="text-xs text-muted-foreground">
              Tùy biến trạm khảo sát, chọn chế độ đáp án giáo viên và xuất in trực tiếp ra giấy chất lượng cao.
            </DialogDescription>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center rounded-xl border border-border bg-secondary/50 p-1 text-xs font-medium">
              <button
                type="button"
                onClick={() => setActiveTab("config")}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all",
                  activeTab === "config"
                    ? "bg-card text-foreground shadow-sm font-semibold"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                <Settings2 className="size-3.5" />
                <span>Cấu hình in</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("preview")}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all",
                  activeTab === "preview"
                    ? "bg-card text-foreground shadow-sm font-semibold"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                <Eye className="size-3.5" />
                <span>Xem trước ({selectedStations.length} trạm)</span>
              </button>
            </div>

            <Button
              onClick={handlePrint}
              size="sm"
              className="gap-2 bg-primary text-primary-foreground font-semibold shadow-md"
            >
              <Printer className="size-4" />
              <span>In ngay (Print)</span>
            </Button>
          </div>
        </div>

        {/* Modal Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {/* TAB 1: CONFIGURATION */}
          {activeTab === "config" && (
            <div className="space-y-6 animate-in fade-in duration-150 print:hidden">
              {/* Option 1: Teacher Key Mode Switch */}
              <div className="p-4 rounded-2xl border border-border/80 bg-gradient-to-r from-card via-card to-primary/5 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="space-y-1">
                    <span className="font-serif font-bold text-sm text-foreground flex items-center gap-2">
                      <GraduationCap className="size-4 text-primary" />
                      <span>Chế độ in phiếu (Worksheet Mode)</span>
                    </span>
                    <p className="text-xs text-muted-foreground">
                      Lựa chọn in bản trống có dòng kẻ cho học sinh viết tay hoặc bản hướng dẫn chấm có đáp án chuẩn.
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      type="button"
                      variant={!config.teacher_key_mode ? "default" : "outline"}
                      size="sm"
                      onClick={() => setConfig((p) => ({ ...p, teacher_key_mode: false }))}
                      className="text-xs font-medium"
                    >
                      Bản Học Sinh (Trống)
                    </Button>
                    <Button
                      type="button"
                      variant={config.teacher_key_mode ? "default" : "outline"}
                      size="sm"
                      onClick={() => setConfig((p) => ({ ...p, teacher_key_mode: true }))}
                      className={cn(
                        "text-xs font-medium",
                        config.teacher_key_mode && "bg-amber-600 hover:bg-amber-700 text-white"
                      )}
                    >
                      <Sparkles className="size-3.5 mr-1.5" />
                      Bản Giáo Viên (Có Đáp Án)
                    </Button>
                  </div>
                </div>

                {config.teacher_key_mode && (
                  <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-800 dark:text-amber-300">
                    💡 <strong>Chế độ Giáo viên đang bật:</strong> Bản in sẽ kèm câu trích sử liệu chi tiết, gợi ý quan sát hiện trạng, phân tích M-E-E mẫu chuẩn mức điểm tối đa và khung chấm điểm Rubric S1–S4.
                  </div>
                )}
              </div>

              {/* Option 2: Cluster Selection & Scope */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-serif font-bold text-sm text-foreground flex items-center gap-2">
                    <Layers className="size-4 text-primary" />
                    <span>Phạm vi trạm điền dã di tích</span>
                  </span>
                  <span className="text-xs text-muted-foreground">
                    Đã chọn: <strong className="text-foreground">{selectedStations.length} / 16</strong> công trình
                  </span>
                </div>

                {/* Preset Cluster Pills */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                  {STATION_CLUSTERS.map((cl) => {
                    const isSelected = activeCluster === cl.id;
                    return (
                      <button
                        key={cl.id}
                        type="button"
                        onClick={() => handleSelectCluster(cl.id, cl.slugs)}
                        className={cn(
                          "p-3 rounded-xl border text-left transition-all space-y-1",
                          isSelected
                            ? "border-primary bg-primary/10 shadow-sm ring-1 ring-primary/30"
                            : "border-border/70 bg-card hover:bg-secondary/40"
                        )}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-xs text-foreground line-clamp-1">
                            {cl.title_vi}
                          </span>
                          {isSelected && <Check className="size-3.5 text-primary shrink-0" />}
                        </div>
                        <p className="text-[11px] text-muted-foreground line-clamp-1">
                          {cl.description_vi}
                        </p>
                      </button>
                    );
                  })}
                </div>

                {/* All 16 Monuments Checkbox Grid for Custom Selection */}
                <div className="p-4 rounded-2xl border border-border/80 bg-secondary/20 space-y-3">
                  <div className="flex items-center justify-between text-xs font-semibold text-foreground">
                    <span>Hoặc tùy chọn từng công trình cụ thể (16 di tích):</span>
                    <button
                      type="button"
                      onClick={() =>
                        handleSelectCluster(
                          "all_16",
                          ALL_16_PRINTABLE_STATIONS.map((s) => s.monument_slug)
                        )
                      }
                      className="text-primary hover:underline text-[11px]"
                    >
                      Chọn tất cả 16
                    </button>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                    {ALL_16_PRINTABLE_STATIONS.map((site) => {
                      const isChecked = config.selected_monument_slugs.includes(site.monument_slug);
                      return (
                        <button
                          key={site.monument_slug}
                          type="button"
                          onClick={() => handleToggleMonument(site.monument_slug)}
                          className={cn(
                            "flex items-center gap-2 p-2 rounded-lg border text-left text-xs transition-colors",
                            isChecked
                              ? "border-primary/60 bg-primary/10 text-foreground font-medium"
                              : "border-border/60 bg-card text-muted-foreground hover:text-foreground"
                          )}
                        >
                          <div
                            className={cn(
                              "size-4 rounded border flex items-center justify-center shrink-0 text-[10px]",
                              isChecked
                                ? "bg-primary border-primary text-primary-foreground font-bold"
                                : "border-muted-foreground/40"
                            )}
                          >
                            {isChecked && "✓"}
                          </div>
                          <span className="truncate">{site.monument_name_vi}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Option 3: School Regulations & Header Metadata (Công văn 5512/BGDĐT) */}
              <div className="p-4 rounded-2xl border border-border/80 bg-card space-y-3">
                <span className="font-serif font-bold text-sm text-foreground flex items-center gap-2">
                  <Building2 className="size-4 text-primary" />
                  <span>Thông tin hành chính sư phạm (Chuẩn Công văn 5512/BGDĐT)</span>
                </span>

                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-xs">
                  <div className="space-y-1">
                    <label className="text-[11px] font-medium text-muted-foreground">Tên trường THPT:</label>
                    <Input
                      value={config.school_name}
                      onChange={(e) => setConfig((p) => ({ ...p, school_name: e.target.value }))}
                      placeholder="THPT Chuyên Quốc Học Huế"
                      className="h-9 text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[11px] font-medium text-muted-foreground">Tổ chuyên môn:</label>
                    <Input
                      value={config.department_name}
                      onChange={(e) => setConfig((p) => ({ ...p, department_name: e.target.value }))}
                      placeholder="Tổ Lịch sử - Địa lý"
                      className="h-9 text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[11px] font-medium text-muted-foreground">Mã bài học / chuyên đề:</label>
                    <Input
                      value={config.lesson_code}
                      onChange={(e) => setConfig((p) => ({ ...p, lesson_code: e.target.value }))}
                      placeholder="KHTN-LS10-DN01"
                      className="h-9 text-xs font-mono"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[11px] font-medium text-muted-foreground">Lớp học thực địa:</label>
                    <Input
                      value={config.class_name}
                      onChange={(e) => setConfig((p) => ({ ...p, class_name: e.target.value }))}
                      placeholder="10 Sử"
                      className="h-9 text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[11px] font-medium text-muted-foreground">Giáo viên hướng dẫn (tùy chọn):</label>
                    <Input
                      value={config.teacher_name || ""}
                      onChange={(e) => setConfig((p) => ({ ...p, teacher_name: e.target.value }))}
                      placeholder="Họ tên thầy/cô"
                      className="h-9 text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[11px] font-medium text-muted-foreground">Ngày điền dã (tùy chọn):</label>
                    <Input
                      value={config.date_vi || ""}
                      onChange={(e) => setConfig((p) => ({ ...p, date_vi: e.target.value }))}
                      placeholder="dd/mm/yyyy"
                      className="h-9 text-xs"
                    />
                  </div>
                </div>
              </div>

              {/* Option 4: Layout & Inclusions Toggles */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Orientation */}
                <div className="p-4 rounded-2xl border border-border/80 bg-card space-y-2">
                  <span className="font-serif font-bold text-xs uppercase tracking-wider text-muted-foreground block">
                    Định hướng trang in (Page Orientation)
                  </span>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <button
                      type="button"
                      onClick={() => setConfig((p) => ({ ...p, orientation: "landscape" }))}
                      className={cn(
                        "p-2.5 rounded-xl border text-center transition-all",
                        config.orientation === "landscape"
                          ? "border-primary bg-primary/10 font-bold text-primary shadow-sm"
                          : "border-border/70 hover:bg-secondary/40 text-muted-foreground"
                      )}
                    >
                      <span>Khổ Ngang (A4 Landscape)</span>
                      <span className="text-[10px] block opacity-70 mt-0.5">Khuyến nghị cho bảng 4 cột</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setConfig((p) => ({ ...p, orientation: "portrait" }))}
                      className={cn(
                        "p-2.5 rounded-xl border text-center transition-all",
                        config.orientation === "portrait"
                          ? "border-primary bg-primary/10 font-bold text-primary shadow-sm"
                          : "border-border/70 hover:bg-secondary/40 text-muted-foreground"
                      )}
                    >
                      <span>Khổ Dọc (A4 Portrait)</span>
                      <span className="text-[10px] block opacity-70 mt-0.5">Tiết kiệm số trang</span>
                    </button>
                  </div>
                </div>

                {/* Inclusions */}
                <div className="p-4 rounded-2xl border border-border/80 bg-card space-y-2">
                  <span className="font-serif font-bold text-xs uppercase tracking-wider text-muted-foreground block">
                    Thành phần tích hợp trên phiếu in
                  </span>
                  <div className="space-y-2 text-xs">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={config.include_qr}
                        onChange={(e) => setConfig((p) => ({ ...p, include_qr: e.target.checked }))}
                        className="rounded border-border"
                      />
                      <QrCode className="size-3.5 text-primary" />
                      <span>In mã QR định danh số kết nối trực tiếp tọa độ 3D</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={config.include_rubric}
                        onChange={(e) => setConfig((p) => ({ ...p, include_rubric: e.target.checked }))}
                        className="rounded border-border"
                      />
                      <FileCheck className="size-3.5 text-primary" />
                      <span>In khung chấm điểm Rubric S1–S4 dành cho giáo viên</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={config.include_exit_ticket}
                        onChange={(e) => setConfig((p) => ({ ...p, include_exit_ticket: e.target.checked }))}
                        className="rounded border-border"
                      />
                      <CheckCircle2 className="size-3.5 text-primary" />
                      <span>In phần thu hoạch cuối giờ (Exit Ticket 5 phút)</span>
                    </label>
                  </div>
                </div>
              </div>

              {/* Bottom Actions */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-border/60">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handleResetDefaults}
                  className="gap-1.5 text-xs text-muted-foreground hover:text-foreground"
                >
                  <RotateCcw className="size-3.5" />
                  <span>Khôi phục mặc định</span>
                </Button>

                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setActiveTab("preview")}
                    className="gap-1.5 text-xs"
                  >
                    <Eye className="size-3.5" />
                    <span>Xem trước trang in</span>
                  </Button>

                  <Button
                    type="button"
                    onClick={handlePrint}
                    size="sm"
                    className="gap-2 bg-primary text-primary-foreground font-semibold shadow-md"
                  >
                    <Printer className="size-4" />
                    <span>In ngay (Print)</span>
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: LIVE A4 PRINT PREVIEW */}
          {activeTab === "preview" && (
            <div className="space-y-4 animate-in fade-in duration-150">
              <div className="flex items-center justify-between print:hidden">
                <span className="text-xs text-muted-foreground">
                  Xem trước bản in A4 ({config.orientation === "landscape" ? "Khổ Ngang" : "Khổ Dọc"}) • {selectedStations.length} trạm khảo sát
                </span>
                <Button
                  onClick={handlePrint}
                  size="sm"
                  className="gap-2 bg-primary text-primary-foreground font-semibold shadow-md"
                >
                  <Printer className="size-4" />
                  <span>Bắt đầu In (Ctrl + P)</span>
                </Button>
              </div>

              <div className="bg-neutral-200/80 p-3 sm:p-6 rounded-2xl border border-neutral-300 overflow-x-auto">
                <PrintableFieldworkWorksheet
                  stations={selectedStations}
                  config={config}
                />
              </div>
            </div>
          )}

          {/* Hidden printable worksheet that is ALWAYS mounted and picked up by @media print */}
          {activeTab !== "preview" && (
            <div className="hidden print:block">
              <PrintableFieldworkWorksheet
                stations={selectedStations}
                config={config}
              />
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
