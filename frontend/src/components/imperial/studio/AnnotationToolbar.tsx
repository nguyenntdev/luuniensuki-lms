"use client";

import React from "react";
import {
  CheckCircle2,
  Download,
  Eye,
  Hand,
  Maximize2,
  Minus,
  MousePointer,
  Plus,
  PlusCircle,
  RotateCcw,
  Save,
  Send,
  Trash2,
  Upload,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

export type StudioToolMode = "SELECT" | "ADD_POINT" | "PAN" | "DELETE";
export type FilterStatus = "ALL" | "DRAFT" | "PUBLISHED";

export interface AnnotationToolbarProps {
  mode: StudioToolMode;
  onSetMode: (mode: StudioToolMode) => void;
  filterStatus: FilterStatus;
  onSetFilterStatus: (filter: FilterStatus) => void;
  isDirty: boolean;
  isSaving: boolean;
  onSaveDrafts: () => void;
  onDiscardDrafts: () => void;
  onOpenPublishModal: () => void;
  onOpenImportExportModal: () => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onFitToScreen: () => void;
  onScale1To1: () => void;
  zoomScale: number;
}

export function AnnotationToolbar({
  mode,
  onSetMode,
  filterStatus,
  onSetFilterStatus,
  isDirty,
  isSaving,
  onSaveDrafts,
  onDiscardDrafts,
  onOpenPublishModal,
  onOpenImportExportModal,
  onZoomIn,
  onZoomOut,
  onFitToScreen,
  onScale1To1,
  zoomScale,
}: AnnotationToolbarProps) {
  return (
    <div
      role="toolbar"
      aria-label="Thanh công cụ biên tập bản đồ"
      className="flex flex-wrap items-center justify-between gap-3 p-2.5 rounded-2xl bg-card/90 backdrop-blur-2xl border border-border/80 shadow-xl"
    >
      {/* Tool Mode Buttons */}
      <div className="flex items-center gap-1 bg-secondary/60 p-1 rounded-xl border border-border/50">
        <Button
          type="button"
          size="xs"
          variant={mode === "SELECT" ? "default" : "ghost"}
          onClick={() => onSetMode("SELECT")}
          className="rounded-lg text-xs font-semibold gap-1.5"
          title="Chọn và kéo di chuyển điểm ghim (V)"
        >
          <MousePointer className="w-3.5 h-3.5" />
          <span>Chọn / Di chuyển</span>
        </Button>

        <Button
          type="button"
          size="xs"
          variant={mode === "ADD_POINT" ? "default" : "ghost"}
          onClick={() => onSetMode("ADD_POINT")}
          className="rounded-lg text-xs font-semibold gap-1.5"
          title="Thêm điểm ghim mới trên bản đồ (A)"
        >
          <PlusCircle className="w-3.5 h-3.5" />
          <span>Thêm điểm</span>
        </Button>

        <Button
          type="button"
          size="xs"
          variant={mode === "PAN" ? "default" : "ghost"}
          onClick={() => onSetMode("PAN")}
          className="rounded-lg text-xs font-semibold gap-1.5"
          title="Kéo rê bản đồ (H)"
        >
          <Hand className="w-3.5 h-3.5" />
          <span>Kéo xem</span>
        </Button>

        <Button
          type="button"
          size="xs"
          variant={mode === "DELETE" ? "destructive" : "ghost"}
          onClick={() => onSetMode("DELETE")}
          className="rounded-lg text-xs font-semibold gap-1.5"
          title="Nhấp vào điểm ghim để xóa (D)"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>Xóa điểm</span>
        </Button>
      </div>

      <Separator orientation="vertical" className="h-6 hidden md:block bg-border/70" />

      {/* Filter Status Selector */}
      <div className="flex items-center gap-1 text-xs">
        <span className="text-muted-foreground mr-1 hidden lg:inline">Hiển thị:</span>
        <div className="flex items-center bg-secondary/50 p-0.5 rounded-lg border border-border/50">
          <button
            type="button"
            onClick={() => onSetFilterStatus("ALL")}
            className={cn(
              "px-2.5 py-1 rounded-md text-[11px] font-medium transition-all",
              filterStatus === "ALL"
                ? "bg-card text-foreground shadow-sm font-semibold"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            Tất cả
          </button>
          <button
            type="button"
            onClick={() => onSetFilterStatus("DRAFT")}
            className={cn(
              "px-2.5 py-1 rounded-md text-[11px] font-medium transition-all",
              filterStatus === "DRAFT"
                ? "bg-amber-500 text-stone-950 shadow-sm font-semibold"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            Bản nháp
          </button>
          <button
            type="button"
            onClick={() => onSetFilterStatus("PUBLISHED")}
            className={cn(
              "px-2.5 py-1 rounded-md text-[11px] font-medium transition-all",
              filterStatus === "PUBLISHED"
                ? "bg-emerald-500 text-stone-950 shadow-sm font-semibold"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            Đã công bố
          </button>
        </div>
      </div>

      <Separator orientation="vertical" className="h-6 hidden md:block bg-border/70" />

      {/* Zoom Controls */}
      <div className="flex items-center gap-1">
        <Button
          type="button"
          size="icon-xs"
          variant="outline"
          onClick={onZoomIn}
          title="Phóng to (+)"
        >
          <Plus className="w-3.5 h-3.5" />
        </Button>
        <Button
          type="button"
          size="icon-xs"
          variant="outline"
          onClick={onZoomOut}
          title="Thu nhỏ (-)"
        >
          <Minus className="w-3.5 h-3.5" />
        </Button>
        <Button
          type="button"
          size="icon-xs"
          variant="outline"
          onClick={onFitToScreen}
          title="Vừa vặn khung nhìn (0)"
        >
          <Maximize2 className="w-3.5 h-3.5" />
        </Button>
        <Button
          type="button"
          size="xs"
          variant="outline"
          onClick={onScale1To1}
          className="text-[10px] font-bold px-2"
          title="Tỷ lệ 100%"
        >
          1:1
        </Button>
        <span className="text-[11px] text-muted-foreground font-mono ml-1 w-10 text-right hidden sm:inline-block">
          {Math.round(zoomScale * 100)}%
        </span>
      </div>

      <Separator orientation="vertical" className="h-6 hidden md:block bg-border/70" />

      {/* Persistence & Publish Actions */}
      <div className="flex items-center gap-2">
        {isDirty && (
          <Button
            type="button"
            size="xs"
            variant="ghost"
            onClick={onDiscardDrafts}
            className="text-xs text-muted-foreground hover:text-destructive"
            title="Hủy các thay đổi chưa lưu"
          >
            <RotateCcw className="w-3.5 h-3.5 mr-1" />
            Hủy
          </Button>
        )}

        <Button
          type="button"
          size="xs"
          variant={isDirty ? "default" : "secondary"}
          disabled={!isDirty || isSaving}
          onClick={onSaveDrafts}
          className="text-xs font-semibold gap-1.5"
        >
          <Save className="w-3.5 h-3.5" />
          <span>{isSaving ? "Đang lưu..." : "Lưu nháp"}</span>
        </Button>

        <Button
          type="button"
          size="xs"
          variant="outline"
          onClick={onOpenImportExportModal}
          className="text-xs font-semibold gap-1.5"
          title="Nhập hoặc xuất JSON"
        >
          <Upload className="w-3.5 h-3.5" />
          <span>Nhập / Xuất</span>
        </Button>

        <Button
          type="button"
          size="xs"
          onClick={onOpenPublishModal}
          className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs gap-1.5 shadow-md"
        >
          <Send className="w-3.5 h-3.5" />
          <span>Công bố bản đồ</span>
        </Button>
      </div>
    </div>
  );
}
