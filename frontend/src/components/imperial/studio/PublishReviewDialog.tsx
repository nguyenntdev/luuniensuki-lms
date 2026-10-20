"use client";

import React, { useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Send,
  ShieldAlert,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { publishMap } from "@/lib/imperial/map-api";
import type {
  ImperialMapAnnotation,
  ImperialMapAsset,
} from "@/lib/imperial/map-types";

export interface PublishReviewDialogProps {
  mapAsset: ImperialMapAsset;
  annotations: ImperialMapAnnotation[];
  isOpen: boolean;
  onClose: () => void;
  onPublishedSuccess: (publishedAsset: ImperialMapAsset) => void;
}

export function PublishReviewDialog({
  mapAsset,
  annotations,
  isOpen,
  onClose,
  onPublishedSuccess,
}: PublishReviewDialogProps) {
  const [publishing, setPublishing] = useState(false);
  const [publishError, setPublishError] = useState<string | null>(null);

  // Check 1: License Approved
  const checkLicense = useMemo(() => {
    const isApproved =
      mapAsset.license_status === "approved" ||
      mapAsset.license_kind === "educational_fair_use" ||
      mapAsset.license_kind === "public_domain";

    return {
      passed: isApproved,
      title: "Bản quyền & Giấy phép sử dụng ảnh không ảnh",
      detail: isApproved
        ? `Đã thẩm định: ${mapAsset.license_kind} (${mapAsset.credit_text || "Đã kiểm duyệt"})`
        : "Chưa được duyệt bản quyền hoặc thiếu chứng nhận cấp phép",
    };
  }, [mapAsset]);

  // Check 2: Minimum 12 monuments
  const checkCount = useMemo(() => {
    const count = annotations.length;
    const passed = count >= 12;

    return {
      passed,
      title: "Số lượng điểm di tích tối thiểu (>= 12 công trình)",
      detail: passed
        ? `Đạt yêu cầu: hiện có ${count} công trình được gắn tọa độ.`
        : `Chưa đạt: hiện có ${count}/12 công trình. Cần gắn thêm ít nhất ${12 - count} điểm ghim.`,
    };
  }, [annotations]);

  // Check 3: Valid UV Bounds
  const checkUV = useMemo(() => {
    const invalidList = annotations.filter(
      (a) => a.u < 0 || a.u > 1 || a.v < 0 || a.v > 1,
    );
    const passed = invalidList.length === 0;

    return {
      passed,
      title: "Tính hợp lệ của tọa độ trực giao [0.0 .. 1.0]",
      detail: passed
        ? "100% điểm ghim nằm chính xác trong giới hạn khung ảnh."
        : `Có ${invalidList.length} điểm ghim vượt ngưỡng ảnh!`,
    };
  }, [annotations]);

  // Check 4: Position Confidence Warning
  const checkConfidence = useMemo(() => {
    const uncertainList = annotations.filter(
      (a) => a.position_confidence === "uncertain",
    );
    const hasWarnings = uncertainList.length > 0;

    return {
      passed: !hasWarnings,
      isWarning: true,
      title: "Độ tin cậy vị trí khảo cổ",
      detail: hasWarnings
        ? `Có ${uncertainList.length} điểm ghim ở mức "Chưa đủ chứng cứ". Khuyến nghị kiểm tra trước khi công bố.`
        : "Tất cả điểm ghim đều đạt mức Ước lượng hoặc Đã thẩm định.",
    };
  }, [annotations]);

  const canPublish = checkLicense.passed && checkCount.passed && checkUV.passed;

  const handleConfirmPublish = async () => {
    if (!canPublish) return;
    try {
      setPublishing(true);
      setPublishError(null);
      const res = await publishMap(mapAsset.id);
      if (res.success && res.map) {
        onPublishedSuccess(res.map);
        onClose();
      } else {
        setPublishError("Công bố thất bại. Vui lòng thử lại sau.");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Đã có lỗi xảy ra.";
      setPublishError(msg);
    } finally {
      setPublishing(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-xl bg-card/95 backdrop-blur-2xl border-border/80 p-6 rounded-3xl shadow-2xl">
        <DialogHeader className="space-y-1.5 text-left">
          <DialogTitle className="text-xl font-bold font-serif text-foreground flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-500" />
            <span>Thẩm định & Công bố bản đồ trực giao</span>
          </DialogTitle>
          <DialogDescription className="text-xs text-muted-foreground">
            Quy trình xuất bản tự động kiểm tra tính toàn vẹn dữ liệu, quyền sở hữu bản quyền và các chuẩn mực khảo cổ học trước khi phát hành cho học sinh và công chúng.
          </DialogDescription>
        </DialogHeader>

        <Separator className="my-3 bg-border/60" />

        {/* Verification Checklist */}
        <div className="space-y-3 my-2 text-xs">
          {/* Check 1 */}
          <div className="flex items-start gap-3 p-3 rounded-2xl bg-secondary/40 border border-border/60">
            {checkLicense.passed ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            ) : (
              <XCircle className="w-4 h-4 text-destructive shrink-0 mt-0.5" />
            )}
            <div className="flex-1">
              <span className="font-semibold block text-foreground">
                {checkLicense.title}
              </span>
              <span className="text-muted-foreground">{checkLicense.detail}</span>
            </div>
          </div>

          {/* Check 2 */}
          <div className="flex items-start gap-3 p-3 rounded-2xl bg-secondary/40 border border-border/60">
            {checkCount.passed ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            ) : (
              <XCircle className="w-4 h-4 text-destructive shrink-0 mt-0.5" />
            )}
            <div className="flex-1">
              <span className="font-semibold block text-foreground">
                {checkCount.title}
              </span>
              <span className="text-muted-foreground">{checkCount.detail}</span>
            </div>
          </div>

          {/* Check 3 */}
          <div className="flex items-start gap-3 p-3 rounded-2xl bg-secondary/40 border border-border/60">
            {checkUV.passed ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            ) : (
              <XCircle className="w-4 h-4 text-destructive shrink-0 mt-0.5" />
            )}
            <div className="flex-1">
              <span className="font-semibold block text-foreground">
                {checkUV.title}
              </span>
              <span className="text-muted-foreground">{checkUV.detail}</span>
            </div>
          </div>

          {/* Check 4 (Warning) */}
          <div className="flex items-start gap-3 p-3 rounded-2xl bg-secondary/40 border border-border/60">
            {checkConfidence.passed ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            )}
            <div className="flex-1">
              <span className="font-semibold block text-foreground">
                {checkConfidence.title}
              </span>
              <span className="text-muted-foreground">{checkConfidence.detail}</span>
            </div>
          </div>
        </div>

        {publishError && (
          <div className="p-3 rounded-xl bg-destructive/10 border border-destructive/30 text-destructive text-xs">
            {publishError}
          </div>
        )}

        <DialogFooter className="mt-4 flex sm:justify-between items-center gap-2">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="text-xs text-muted-foreground"
          >
            Hủy bỏ
          </Button>

          <Button
            type="button"
            size="sm"
            disabled={!canPublish || publishing}
            onClick={handleConfirmPublish}
            className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs gap-1.5 shadow-lg"
          >
            <Send className="w-3.5 h-3.5" />
            <span>{publishing ? "Đang công bố..." : "Xác nhận công bố chính thức"}</span>
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
