"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  Camera,
  Rotate3d,
  AlertCircle,
  CheckCircle2,
  Sparkles,
  ShieldCheck,
  Zap,
  Info,
  ChevronRight,
  RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  getDeviceCapabilityReport,
  requestCameraAccess,
  resolveInspectionMode,
  type ARInspectionMode,
  type DeviceCapabilityReport,
} from "@/lib/imperial/ar-capabilities";

export interface ARCapabilityGateProps {
  targetSlug: string;
  targetTitle: string;
  onModeChange?: (mode: ARInspectionMode, cameraGranted: boolean) => void;
  forceFallback?: boolean;
  className?: string;
  children?: (props: {
    activeMode: ARInspectionMode;
    cameraGranted: boolean;
    report: DeviceCapabilityReport | null;
    requestCamera: () => Promise<void>;
    switchToFallback: () => void;
  }) => React.ReactNode;
}

export function ARCapabilityGate({
  targetSlug,
  targetTitle,
  onModeChange,
  forceFallback = false,
  className = "",
  children,
}: ARCapabilityGateProps) {
  const [loading, setLoading] = useState<boolean>(true);
  const [report, setReport] = useState<DeviceCapabilityReport | null>(null);
  const [activeMode, setActiveMode] = useState<ARInspectionMode>("turntable_2d");
  const [cameraGranted, setCameraGranted] = useState<boolean>(false);
  const [showConsentPrompt, setShowConsentPrompt] = useState<boolean>(false);
  const [denialDismissed, setDenialDismissed] = useState<boolean>(false);

  // Initialize capability audit
  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    getDeviceCapabilityReport().then((rep) => {
      if (!isMounted) return;
      setReport(rep);

      if (forceFallback) {
        setActiveMode("turntable_2d");
        setCameraGranted(false);
        onModeChange?.("turntable_2d", false);
      } else if (rep.supportsAR && rep.cameraPermission === "prompt") {
        // Device is capable of AR but needs user consent first
        setShowConsentPrompt(true);
        setActiveMode("turntable_2d");
        setCameraGranted(false);
        onModeChange?.("turntable_2d", false);
      } else if (rep.supportsAR && rep.cameraPermission === "granted") {
        setActiveMode(rep.recommendedMode);
        setCameraGranted(true);
        onModeChange?.(rep.recommendedMode, true);
      } else {
        // Fallback (denied, unsupported, budget exceeded)
        const resolved = resolveInspectionMode(rep, false);
        setActiveMode(resolved);
        setCameraGranted(false);
        onModeChange?.(resolved, false);
      }

      setLoading(false);
    });

    return () => {
      isMounted = false;
    };
  }, [forceFallback, onModeChange]);

  const handleRequestCamera = useCallback(async () => {
    setShowConsentPrompt(false);
    const result = await requestCameraAccess();

    if (result === "granted") {
      setActiveMode("webxr_ar");
      setCameraGranted(true);
      onModeChange?.("webxr_ar", true);
    } else {
      // Gracefully fall back to 2D turntable without punishment
      setActiveMode("turntable_2d");
      setCameraGranted(false);
      onModeChange?.("turntable_2d", false);
    }

    // Refresh report state
    const updated = await getDeviceCapabilityReport();
    setReport(updated);
  }, [onModeChange]);

  const handleContinueWithTurntable = useCallback(() => {
    setShowConsentPrompt(false);
    setActiveMode("turntable_2d");
    setCameraGranted(false);
    onModeChange?.("turntable_2d", false);
  }, [onModeChange]);

  return (
    <div className={`space-y-4 ${className}`}>
      {/* 1. GRACEFUL CONSENT MODAL / CALLOUT */}
      {showConsentPrompt && (
        <div
          role="dialog"
          aria-labelledby="ar-consent-title"
          className="rounded-2xl border-2 border-primary/30 bg-card p-5 sm:p-6 shadow-lg space-y-4 animate-in fade-in-50"
        >
          <div className="flex items-start gap-3">
            <div className="p-2.5 rounded-xl bg-primary/10 text-primary shrink-0">
              <Camera className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs font-semibold text-primary border-primary/30">
                  <Sparkles className="w-3 h-3 mr-1" />
                  Trải nghiệm Không gian AR
                </Badge>
                <span className="text-xs text-muted-foreground">Tuỳ chọn hiển thị</span>
              </div>
              <h3 id="ar-consent-title" className="font-serif font-bold text-lg text-foreground">
                Xem hiện vật {targetTitle} trong không gian thực
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Hệ thống hỗ trợ đặt mô hình hiện vật vào môi trường của bạn qua công nghệ WebXR. Để sử dụng,
                trình duyệt cần quyền truy cập camera tạm thời.
              </p>
            </div>
          </div>

          <div className="rounded-xl border border-border/80 bg-muted/40 p-3 text-xs text-muted-foreground flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>
              <strong>Bảo đảm quyền riêng tư:</strong> Antigravity không lưu trữ hay truyền tải bất kỳ hình ảnh nào từ camera. Bạn hoàn toàn có thể từ chối mà vẫn nhận trọn vẹn điểm học tập (+25 XP).
            </span>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3 pt-1">
            <Button
              onClick={handleRequestCamera}
              className="w-full sm:w-auto gap-2 bg-primary text-primary-foreground font-semibold h-10 px-5"
            >
              <Camera className="w-4 h-4" />
              Kích hoạt Camera để xem AR
            </Button>

            <Button
              variant="outline"
              onClick={handleContinueWithTurntable}
              className="w-full sm:w-auto gap-2 h-10 px-5 text-foreground"
            >
              <Rotate3d className="w-4 h-4" />
              Xem Mâm xoay 360° / Bản rập (Không cần Camera)
            </Button>
          </div>
        </div>
      )}

      {/* 2. REASSURING CAMERA DENIED / REJECTED NOTICE (NEGATIVE ABUSE SHIELD) */}
      {report?.cameraPermission === "denied" && !denialDismissed && (
        <div
          role="status"
          aria-live="polite"
          className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-amber-900 dark:text-amber-200 flex items-start justify-between gap-3 text-xs"
        >
          <div className="flex items-start gap-2.5">
            <Info className="w-4 h-4 text-amber-600 dark:text-amber-400 mt-0.5 shrink-0" />
            <div className="space-y-1">
              <strong className="font-semibold block text-sm">
                Đang sử dụng chế độ Mâm xoay 360° & Bản rập 2D
              </strong>
              <p className="leading-relaxed opacity-90">
                Camera không được cấp quyền hoặc không khả dụng. Bạn có thể quan sát trọn vẹn các chi tiết,
                xoay mọi góc nhìn và hoàn thành bài học tương đương với 100% điểm thưởng (+25 XP).
              </p>
            </div>
          </div>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setDenialDismissed(true)}
            className="text-[11px] h-7 px-2 shrink-0 hover:bg-amber-500/20"
          >
            Đã hiểu
          </Button>
        </div>
      )}

      {/* 3. PERFORMANCE BUDGET LIMITATION NOTICE */}
      {report && !report.performanceBudget.meetsArBudget && (
        <div
          role="status"
          aria-live="polite"
          className="rounded-xl border border-blue-500/30 bg-blue-500/10 p-4 text-blue-900 dark:text-blue-200 flex items-start gap-3 text-xs"
        >
          <Zap className="w-4 h-4 text-blue-600 dark:text-blue-400 mt-0.5 shrink-0" />
          <div className="space-y-1">
            <strong className="font-semibold block">
              Tự động tối ưu hóa thiết bị & mạng ({report.deviceTier.replace("_", " ")})
            </strong>
            <p className="leading-relaxed opacity-90">
              Để bảo đảm tốc độ mượt mà và tiết kiệm lưu lượng dữ liệu (
              {report.performanceBudget.budgetViolations.join(", ")}
              ), hệ thống ưu tiên hiển thị chế độ Mâm xoay 2D siêu nhẹ.
            </p>
          </div>
        </div>
      )}

      {/* 4. MODE TOGGLE STRIP */}
      <div className="flex items-center justify-between gap-3 text-xs border-b border-border/50 pb-2">
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">Chế độ khảo sát hiện tại:</span>
          <Badge variant="secondary" className="font-medium text-xs">
            {activeMode === "webxr_ar" ? (
              <>
                <Camera className="w-3 h-3 mr-1 text-emerald-600" />
                Thực tế tăng cường (AR)
              </>
            ) : (
              <>
                <Rotate3d className="w-3 h-3 mr-1 text-primary" />
                Mâm xoay 360° / Bản rập 2D
              </>
            )}
          </Badge>
        </div>

        {report?.supportsAR && activeMode !== "webxr_ar" && (
          <Button
            size="sm"
            variant="ghost"
            onClick={handleRequestCamera}
            className="text-xs h-7 gap-1 text-primary hover:text-primary/80"
          >
            <Camera className="w-3 h-3" />
            Thử chế độ AR
          </Button>
        )}
      </div>

      {/* 5. RENDER ACTIVE VIEW */}
      {children &&
        children({
          activeMode,
          cameraGranted,
          report,
          requestCamera: handleRequestCamera,
          switchToFallback: handleContinueWithTurntable,
        })}
    </div>
  );
}
export default ARCapabilityGate;
