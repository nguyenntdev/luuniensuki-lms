"use client";

import React, { useEffect, useState } from "react";
import {
  Check,
  Compass,
  FileText,
  Info,
  Layers,
  MapPin,
  Save,
  ShieldAlert,
  Tag,
  Trash2,
  X,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import type {
  ImperialMapAnnotation,
  ImperialSite,
  MarkerStyle,
  PositionConfidence,
  ReviewStatus,
} from "@/lib/imperial/map-types";

export interface MarkerInspectorProps {
  annotation: ImperialMapAnnotation | null;
  sites: ImperialSite[];
  onSave: (updated: ImperialMapAnnotation) => void;
  onDelete: (annotation: ImperialMapAnnotation) => void;
  onClose: () => void;
  className?: string;
}

const MARKER_STYLES: Array<{ value: MarkerStyle; label: string }> = [
  { value: "monument", label: "Đài tưởng niệm / Di tích" },
  { value: "gate", label: "Cổng / Ngọ Môn / Thành môn" },
  { value: "palace", label: "Điện chính / Hoàng cung" },
  { value: "temple", label: "Tổ Miếu / Đền phụng tự" },
  { value: "pavilion", label: "Gác lầu / Đình tạ / Thư viện" },
  { value: "garden", label: "Hoa viên / Vườn ngự" },
  { value: "bridge", label: "Cầu cẩm thạch / Đường chuyển" },
  { value: "bastion", label: "Pháo đài / Giác đài" },
  { value: "residence", label: "Cung thất sinh hoạt" },
  { value: "ruins", label: "Phế tích / Nền móng khảo cổ" },
];

export function MarkerInspector({
  annotation,
  sites,
  onSave,
  onDelete,
  onClose,
  className,
}: MarkerInspectorProps) {
  const [siteId, setSiteId] = useState("");
  const [label, setLabel] = useState("");
  const [markerStyle, setMarkerStyle] = useState<MarkerStyle>("monument");
  const [confidence, setConfidence] = useState<PositionConfidence>("approximate");
  const [reviewStatus, setReviewStatus] = useState<ReviewStatus>("draft");
  const [editorialNotes, setEditorialNotes] = useState("");
  const [isDirty, setIsDirty] = useState(false);

  // Sync state when selected annotation changes
  useEffect(() => {
    if (annotation) {
      setSiteId(annotation.site_id || "");
      setLabel(annotation.label || "");
      setMarkerStyle(annotation.marker_style || "monument");
      setConfidence(annotation.position_confidence || "approximate");
      setReviewStatus(annotation.review_status || "draft");
      setEditorialNotes(annotation.editorial_notes || "");
      setIsDirty(false);
    }
  }, [annotation]);

  if (!annotation) {
    return (
      <aside
        aria-label="Bảng thuộc tính điểm ghim"
        className={cn(
          "w-80 h-full p-6 flex flex-col items-center justify-center text-center bg-card/90 backdrop-blur-2xl border-l border-border/80 text-muted-foreground",
          className,
        )}
      >
        <MapPin className="w-10 h-10 mb-3 opacity-30 text-primary" />
        <h3 className="text-sm font-semibold text-foreground">
          Chưa chọn điểm ghim nào
        </h3>
        <p className="text-xs text-muted-foreground mt-1 max-w-[220px]">
          Nhấp vào một điểm ghim trên bản đồ hoặc chọn công cụ &quot;Thêm điểm&quot; để tạo điểm mới.
        </p>
      </aside>
    );
  }

  const selectedSite = sites.find((s) => s.id === siteId);

  const handleSave = () => {
    if (!annotation) return;
    const updated: ImperialMapAnnotation = {
      ...annotation,
      site_id: siteId,
      label: label.trim() || selectedSite?.name_vi || "Điểm ghim",
      marker_style: markerStyle,
      position_confidence: confidence,
      review_status: reviewStatus,
      editorial_notes: editorialNotes.trim() || null,
      site: selectedSite
        ? {
            id: selectedSite.id,
            slug: selectedSite.slug,
            name_vi: selectedSite.name_vi,
            name_han_nom: selectedSite.name_han_nom,
            chinese_name: selectedSite.chinese_name,
            summary_vi: selectedSite.description_vi,
            zone_slug: selectedSite.zone_slug || undefined,
            learning_level: selectedSite.learning_level,
            condition: selectedSite.condition,
          }
        : annotation.site,
    };
    onSave(updated);
    setIsDirty(false);
  };

  return (
    <aside
      aria-label="Bảng chỉnh sửa thuộc tính điểm ghim"
      className={cn(
        "w-88 h-full flex flex-col bg-card/95 backdrop-blur-2xl border-l border-border/80 shadow-2xl overflow-y-auto no-scrollbar",
        className,
      )}
    >
      {/* Header */}
      <div className="p-4 border-b border-border/70 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MapPin className="w-4 h-4 text-primary" />
          <h3 className="text-sm font-bold text-foreground font-serif">
            Thuộc tính điểm ghim
          </h3>
        </div>
        <div className="flex items-center gap-1.5">
          <Badge
            variant="outline"
            className="text-[10px] font-mono font-semibold bg-secondary/80"
          >
            v{annotation.row_version}
          </Badge>
          <Button
            type="button"
            size="icon-xs"
            variant="ghost"
            onClick={onClose}
            className="rounded-lg text-muted-foreground hover:text-foreground"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Body Form */}
      <div className="p-4 space-y-4 flex-1 text-xs">
        {/* Normalized UV Coordinates Readout */}
        <div className="p-3 rounded-xl bg-secondary/50 border border-border/60 space-y-1.5">
          <div className="flex items-center justify-between text-[11px] font-semibold text-foreground">
            <span>Tọa độ trực giao (UV)</span>
            <span className="text-[10px] text-muted-foreground font-mono">
              Sai số: ±1e-7
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2 font-mono text-[11px]">
            <div className="bg-background/80 p-1.5 rounded-lg border border-border/60">
              <span className="text-muted-foreground mr-1">U:</span>
              <span className="font-semibold text-foreground">
                {annotation.u.toFixed(7)}
              </span>
            </div>
            <div className="bg-background/80 p-1.5 rounded-lg border border-border/60">
              <span className="text-muted-foreground mr-1">V:</span>
              <span className="font-semibold text-foreground">
                {annotation.v.toFixed(7)}
              </span>
            </div>
          </div>
        </div>

        {/* Site Picker */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-foreground flex items-center gap-1">
            <Compass className="w-3.5 h-3.5 text-primary" />
            <span>Liên kết công trình di tích:</span>
          </label>
          <Select
            value={siteId}
            onValueChange={(val) => {
              setSiteId(val);
              setIsDirty(true);
              const target = sites.find((s) => s.id === val);
              if (target && !label) {
                setLabel(target.name_vi);
              }
            }}
          >
            <SelectTrigger className="w-full bg-background/70 border-border/80 h-9 rounded-xl text-xs">
              <SelectValue placeholder="Chọn di tích..." />
            </SelectTrigger>
            <SelectContent className="max-h-60">
              {sites.map((s) => (
                <SelectItem key={s.id} value={s.id} className="text-xs">
                  {s.name_vi}
                  {s.name_han_nom ? ` (${s.name_han_nom})` : ""}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Display Label */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-foreground flex items-center gap-1">
            <Tag className="w-3.5 h-3.5 text-primary" />
            <span>Nhãn hiển thị trên bản đồ:</span>
          </label>
          <Input
            value={label}
            onChange={(e) => {
              setLabel(e.target.value);
              setIsDirty(true);
            }}
            placeholder="Tên hiển thị..."
            className="h-9 bg-background/70 border-border/80 rounded-xl text-xs"
          />
        </div>

        {/* Marker Style */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-foreground flex items-center gap-1">
            <Layers className="w-3.5 h-3.5 text-primary" />
            <span>Kiểu biểu tượng (Marker Style):</span>
          </label>
          <Select
            value={markerStyle}
            onValueChange={(val) => {
              setMarkerStyle(val as MarkerStyle);
              setIsDirty(true);
            }}
          >
            <SelectTrigger className="w-full bg-background/70 border-border/80 h-9 rounded-xl text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {MARKER_STYLES.map((st) => (
                <SelectItem key={st.value} value={st.value} className="text-xs">
                  {st.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Position Confidence */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-foreground flex items-center gap-1">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-500" />
            <span>Độ tin cậy vị trí:</span>
          </label>
          <Select
            value={confidence}
            onValueChange={(val) => {
              setConfidence(val as PositionConfidence);
              setIsDirty(true);
            }}
          >
            <SelectTrigger className="w-full bg-background/70 border-border/80 h-9 rounded-xl text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="verified" className="text-xs text-emerald-400">
                Đã thẩm định chuẩn xác (Verified)
              </SelectItem>
              <SelectItem value="approximate" className="text-xs text-amber-400">
                Ước lượng theo không ảnh (Approximate)
              </SelectItem>
              <SelectItem value="uncertain" className="text-xs text-destructive">
                Chưa đủ chứng cứ (Uncertain)
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Review Status */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-foreground">
            Trạng thái xét duyệt:
          </label>
          <Select
            value={reviewStatus}
            onValueChange={(val) => {
              setReviewStatus(val as ReviewStatus);
              setIsDirty(true);
            }}
          >
            <SelectTrigger className="w-full bg-background/70 border-border/80 h-9 rounded-xl text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="draft" className="text-xs">
                Bản nháp (Draft)
              </SelectItem>
              <SelectItem value="in_review" className="text-xs">
                Đang thẩm định (In Review)
              </SelectItem>
              <SelectItem value="approved" className="text-xs">
                Đã phê duyệt (Approved)
              </SelectItem>
              <SelectItem value="published" className="text-xs">
                Đã công bố (Published)
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Editorial Notes */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-foreground flex items-center gap-1">
            <FileText className="w-3.5 h-3.5 text-muted-foreground" />
            <span>Ghi chú biên tập / Giám định:</span>
          </label>
          <textarea
            value={editorialNotes}
            onChange={(e) => {
              setEditorialNotes(e.target.value);
              setIsDirty(true);
            }}
            placeholder="Ghi chú về nguồn ảnh, sai lệch vị trí, niên đại phục dựng..."
            rows={3}
            className="w-full p-2.5 rounded-xl bg-background/70 border border-border/80 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary resize-none"
          />
        </div>
      </div>

      {/* Footer Actions */}
      <div className="p-4 border-t border-border/70 space-y-2 bg-card/90">
        <Button
          type="button"
          onClick={handleSave}
          className="w-full bg-primary text-primary-foreground font-semibold text-xs h-9 rounded-xl shadow-md gap-1.5"
        >
          <Save className="w-3.5 h-3.5" />
          <span>Lưu thay đổi</span>
        </Button>

        <Button
          type="button"
          variant="destructive"
          size="xs"
          onClick={() => onDelete(annotation)}
          className="w-full text-xs h-8 rounded-xl font-medium gap-1.5"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>Xóa điểm ghim này</span>
        </Button>
      </div>
    </aside>
  );
}
