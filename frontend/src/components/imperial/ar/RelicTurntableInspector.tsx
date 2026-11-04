"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import Image from "next/image";
import {
  RotateCcw,
  RotateCw,
  ZoomIn,
  ZoomOut,
  Maximize2,
  CheckCircle2,
  Sparkles,
  Layers,
  Eye,
  CameraOff,
  Info,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  createEquivalentInspectionSession,
  recordInspectedAngle,
  recordExaminedHotspot,
  validateInspectionCompletion,
  type ARInspectionMode,
  type RelicInspectionSession,
} from "@/lib/imperial/ar-capabilities";
import {
  completeRelicInspection,
  fetchRelicInspectionStatus,
} from "@/lib/imperial/v51-api";
import type { ImperialInspectionCompleteResponse } from "@/lib/imperial/v51-types";

export interface RelicHotspot {
  id: string;
  label: string;
  angle: number; // 0..360 deg
  u: number; // 0..1 x percentage
  v: number; // 0..1 y percentage
  description: string;
  sourceCitation?: string;
}

export interface RelicTurntableInspectorProps {
  targetSlug: string;
  targetTitle: string;
  photoUrl?: string;
  rubbingUrl?: string;
  hotspots?: RelicHotspot[];
  inspectionMode?: ARInspectionMode;
  cameraGranted?: boolean;
  onInspectionComplete?: (result: ImperialInspectionCompleteResponse) => void;
  className?: string;
}

const DEFAULT_ANGLES = [
  { label: "Chính diện (0°)", value: 0, code: "front" },
  { label: "Bên hữu (90°)", value: 90, code: "right" },
  { label: "Mặt sau (180°)", value: 180, code: "back" },
  { label: "Bên tả (270°)", value: 270, code: "left" },
];

export function RelicTurntableInspector({
  targetSlug,
  targetTitle,
  photoUrl = "/assets/imperial/heritage/dienthaihoa.jpg",
  rubbingUrl = "/assets/ban-duc-noi/CAO DINH/CAO ĐỈNH.jpg",
  hotspots = [
    {
      id: "h1",
      label: "Họa tiết Chính diện",
      angle: 0,
      u: 0.5,
      v: 0.45,
      description: "Chạm khắc rồng mây tinh xảo thế kỷ XIX, sơn thếp vàng rực rỡ.",
      sourceCitation: "Đại Nam Thực Lục Chính Biên (Đệ nhất kỷ)",
    },
    {
      id: "h2",
      label: "Bệ đế & Hoa văn hồi văn",
      angle: 90,
      u: 0.52,
      v: 0.75,
      description: "Cấu trúc tam cấp vững chắc biểu thị nền tảng non sông xã tắc.",
      sourceCitation: "Khâm Định Đại Nam Hội Điển Sự Lệ",
    },
  ],
  inspectionMode = "turntable_2d",
  cameraGranted = false,
  onInspectionComplete,
  className = "",
}: RelicTurntableInspectorProps) {
  // Viewer state
  const [currentAngle, setCurrentAngle] = useState<number>(0);
  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const [activeLayer, setActiveLayer] = useState<"photo" | "rubbing">("photo");
  const [selectedHotspot, setSelectedHotspot] = useState<RelicHotspot | null>(null);

  // Drag interaction
  const isDragging = useRef<boolean>(false);
  const startX = useRef<number>(0);
  const startAngle = useRef<number>(0);

  // Task & Inspection Session state
  const sessionRef = useRef<RelicInspectionSession>(
    createEquivalentInspectionSession(targetSlug, inspectionMode, cameraGranted),
  );
  const [anglesViewed, setAnglesViewed] = useState<string[]>(["front"]);
  const [hotspotsExamined, setHotspotsExamined] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [completedResult, setCompletedResult] = useState<ImperialInspectionCompleteResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Initialize session and record default front angle
  useEffect(() => {
    sessionRef.current = createEquivalentInspectionSession(
      targetSlug,
      inspectionMode,
      cameraGranted,
    );
    recordInspectedAngle(sessionRef.current, "front");

    // Check if user already completed this inspection previously
    fetchRelicInspectionStatus(targetSlug).then((status) => {
      if (status.is_completed) {
        setCompletedResult({
          success: true,
          task_id: "prior-completed",
          target_slug: targetSlug,
          target_title: targetTitle,
          inspection_mode: status.completed_mode || inspectionMode,
          camera_permission_granted: status.camera_permission_granted ?? cameraGranted,
          equivalent_learning_completed: true,
          xp_awarded: 0,
          total_xp: status.xp_earned || 25,
          already_completed: true,
          feedback: "Hiện vật này đã được bạn hoàn thành khảo sát trong hồ sơ.",
          recorded_at: status.completed_at || new Date().toISOString(),
        });
      }
    });
  }, [targetSlug, inspectionMode, cameraGranted, targetTitle]);

  // Rotate helper
  const handleAngleChange = useCallback((newAngle: number, code?: string) => {
    const normalized = ((newAngle % 360) + 360) % 360;
    setCurrentAngle(normalized);

    const angleCode =
      code ||
      (normalized >= 315 || normalized < 45
        ? "front"
        : normalized >= 45 && normalized < 135
        ? "right"
        : normalized >= 135 && normalized < 225
        ? "back"
        : "left");

    recordInspectedAngle(sessionRef.current, angleCode);
    setAnglesViewed((prev) => (prev.includes(angleCode) ? prev : [...prev, angleCode]));
  }, []);

  // Hotspot click helper
  const handleHotspotClick = useCallback((hotspot: RelicHotspot) => {
    setSelectedHotspot(hotspot);
    recordExaminedHotspot(sessionRef.current, hotspot.id);
    setHotspotsExamined((prev) =>
      prev.includes(hotspot.id) ? prev : [...prev, hotspot.id],
    );
  }, []);

  // Keyboard navigation
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "ArrowLeft" || e.key === "a" || e.key === "A") {
        e.preventDefault();
        handleAngleChange(currentAngle - 15);
      } else if (e.key === "ArrowRight" || e.key === "d" || e.key === "D") {
        e.preventDefault();
        handleAngleChange(currentAngle + 15);
      } else if (e.key === "+" || e.key === "=") {
        e.preventDefault();
        setZoomLevel((z) => Math.min(2.5, z + 0.25));
      } else if (e.key === "-" || e.key === "_") {
        e.preventDefault();
        setZoomLevel((z) => Math.max(1, z - 0.25));
      }
    },
    [currentAngle, handleAngleChange],
  );

  // Mouse / Touch drag to spin
  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    isDragging.current = true;
    startX.current = e.clientX;
    startAngle.current = currentAngle;
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!isDragging.current) return;
    const deltaX = e.clientX - startX.current;
    // Map drag distance to rotation degrees
    const degDelta = Math.round(deltaX * 0.75);
    handleAngleChange(startAngle.current + degDelta);
  };

  const handlePointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    isDragging.current = false;
    try {
      (e.target as HTMLElement).releasePointerCapture(e.pointerId);
    } catch {
      // Ignored
    }
  };

  // Submit completion to backend
  const handleCompleteInspection = async () => {
    setErrorMessage(null);
    const elapsedSeconds = Math.max(
      3,
      Math.floor((Date.now() - sessionRef.current.startTime) / 1000),
    );

    const validation = validateInspectionCompletion(sessionRef.current);
    if (!validation.valid) {
      setErrorMessage(validation.reason || "Chưa đạt yêu cầu quan sát.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await completeRelicInspection({
        target_slug: targetSlug,
        inspection_mode: inspectionMode,
        camera_permission_granted: cameraGranted,
        device_tier: "desktop",
        time_spent_seconds: elapsedSeconds,
        angles_inspected: Array.from(sessionRef.current.anglesInspected),
        hotspots_examined: Array.from(sessionRef.current.hotspotsExamined),
        idempotency_key: `insp-${targetSlug}-${sessionRef.current.startTime}`,
      });

      setCompletedResult(res);
      onInspectionComplete?.(res);
    } catch (err: unknown) {
      setErrorMessage(
        err instanceof Error ? err.message : "Có lỗi xảy ra khi lưu kết quả.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  const activeImage = activeLayer === "photo" ? photoUrl : rubbingUrl;

  return (
    <Card
      tabIndex={0}
      onKeyDown={handleKeyDown}
      className={`border border-border/80 shadow-md overflow-hidden bg-card focus:outline-none focus:ring-2 focus:ring-primary/40 ${className}`}
      aria-label={`Bộ quan sát Mâm xoay tương tác cho ${targetTitle}. Sử dụng phím mũi tên Trái/Phải để xoay, dấu cộng/trừ để thu phóng.`}
    >
      <CardContent className="p-0">
        {/* TOP STATUS BAR */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-4 border-b border-border/60 bg-muted/30">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs font-semibold">
                Góc xoay: {currentAngle}°
              </Badge>
              <Badge variant="secondary" className="text-xs">
                {activeLayer === "photo" ? "Ảnh chụp tư liệu" : "Bản rập 2D (HMCC)"}
              </Badge>
            </div>
            <h4 className="font-serif font-bold text-base text-foreground">
              {targetTitle}
            </h4>
          </div>

          {/* LAYER & ZOOM CONTROLS */}
          <div className="flex items-center gap-1.5">
            <Button
              size="sm"
              variant={activeLayer === "photo" ? "default" : "outline"}
              onClick={() => setActiveLayer("photo")}
              className="text-xs h-8 px-2.5 gap-1"
            >
              <Eye className="w-3.5 h-3.5" />
              Ảnh tư liệu
            </Button>
            <Button
              size="sm"
              variant={activeLayer === "rubbing" ? "default" : "outline"}
              onClick={() => setActiveLayer("rubbing")}
              className="text-xs h-8 px-2.5 gap-1"
            >
              <Layers className="w-3.5 h-3.5" />
              Bản rập
            </Button>
            <Button
              size="icon"
              variant="outline"
              onClick={() => setZoomLevel((z) => Math.min(2.5, z + 0.25))}
              className="h-8 w-8 text-foreground"
              aria-label="Phóng to"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </Button>
            <Button
              size="icon"
              variant="outline"
              onClick={() => setZoomLevel((z) => Math.max(1, z - 0.25))}
              className="h-8 w-8 text-foreground"
              aria-label="Thu nhỏ"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </Button>
          </div>
        </div>

        {/* 360 INTERACTIVE CANVAS AREA */}
        <div
          role="img"
          aria-label={`Hiện vật ${targetTitle} hiển thị tại góc ${currentAngle} độ. Nhấn kéo chuột hoặc phím mũi tên để xoay 360 độ.`}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          className="relative w-full h-80 sm:h-96 bg-neutral-950 flex items-center justify-center overflow-hidden cursor-grab active:cursor-grabbing select-none"
        >
          {/* Main Visual Image with perspective rotation transform */}
          <div
            className="relative transition-transform duration-75"
            style={{
              transform: `scale(${zoomLevel}) rotateY(${currentAngle}deg)`,
              transformStyle: "preserve-3d",
            }}
          >
            <div className="relative w-72 h-72 sm:w-80 sm:h-80">
              <Image
                src={activeImage}
                alt={`${targetTitle} góc ${currentAngle}°`}
                fill
                sizes="(max-width: 640px) 288px, 320px"
                className="object-contain drop-shadow-2xl pointer-events-none"
                priority
              />
            </div>
          </div>

          {/* HOTSPOT OVERLAYS */}
          {hotspots.map((hs, idx) => {
            // Hotspots are visible near their target viewing angle (+/- 60 degrees)
            const angleDiff = Math.abs(((hs.angle - currentAngle + 180) % 360) - 180);
            const isVisible = angleDiff <= 60;
            if (!isVisible) return null;

            return (
              <button
                key={hs.id}
                onClick={(e) => {
                  e.stopPropagation();
                  handleHotspotClick(hs);
                }}
                style={{
                  left: `${hs.u * 100}%`,
                  top: `${hs.v * 100}%`,
                }}
                className="absolute transform -translate-x-1/2 -translate-y-1/2 flex items-center justify-center w-7 h-7 rounded-full bg-primary text-primary-foreground font-bold text-xs shadow-lg hover:scale-125 transition-transform border-2 border-white focus:outline-none focus:ring-2 focus:ring-primary"
                aria-label={`Khảo sát chi tiết: ${hs.label}`}
              >
                {idx + 1}
              </button>
            );
          })}

          {/* HINT OVERLAY */}
          <div className="absolute bottom-3 left-3 bg-black/60 backdrop-blur-xs text-white/80 rounded-lg px-2.5 py-1 text-[11px] pointer-events-none flex items-center gap-1.5">
            <RotateCcw className="w-3 h-3 animate-spin-slow" />
            <span>Kéo chuột hoặc vuốt để xoay 360°</span>
          </div>
        </div>

        {/* ANGLE PRESET BUTTONS */}
        <div className="flex flex-wrap items-center justify-between gap-2 p-3 bg-muted/20 border-b border-border/50 text-xs">
          <span className="text-muted-foreground font-medium">Góc nhìn mẫu:</span>
          <div className="flex items-center gap-2 flex-wrap">
            {DEFAULT_ANGLES.map((a) => (
              <Button
                key={a.code}
                size="sm"
                variant={anglesViewed.includes(a.code) ? "secondary" : "outline"}
                onClick={() => handleAngleChange(a.value, a.code)}
                className={`text-xs h-7 px-2.5 gap-1 ${
                  Math.abs(currentAngle - a.value) < 15
                    ? "border-primary font-bold text-primary"
                    : ""
                }`}
              >
                {anglesViewed.includes(a.code) && (
                  <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                )}
                {a.label}
              </Button>
            ))}
          </div>
        </div>

        {/* SELECTED HOTSPOT DETAILS DRAWER */}
        {selectedHotspot && (
          <div className="p-4 bg-muted/40 border-b border-border/60 text-xs space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-foreground flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5 text-primary" />
                {selectedHotspot.label}
              </span>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setSelectedHotspot(null)}
                className="h-6 px-1.5 text-muted-foreground hover:text-foreground text-[11px]"
              >
                Đóng
              </Button>
            </div>
            <p className="text-muted-foreground leading-relaxed">
              {selectedHotspot.description}
            </p>
            {selectedHotspot.sourceCitation && (
              <p className="text-[11px] text-primary/80 italic font-serif">
                Nguồn dẫn: {selectedHotspot.sourceCitation}
              </p>
            )}
          </div>
        )}

        {/* BOTTOM TASK PROGRESS & SUBMISSION STRIP */}
        <div className="p-4 sm:p-5 flex flex-col sm:flex-row items-center justify-between gap-4 bg-card">
          <div className="space-y-1 w-full sm:w-auto">
            <div className="flex items-center gap-2 text-xs">
              <span className="font-semibold text-foreground">Tiến trình khảo sát:</span>
              <Badge variant="outline" className="text-[11px]">
                {anglesViewed.length}/4 góc nhìn
              </Badge>
              {hotspots.length > 0 && (
                <Badge variant="outline" className="text-[11px]">
                  {hotspotsExamined.length}/{hotspots.length} chi tiết
                </Badge>
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              Khảo sát các mặt hiện vật để hoàn thành nhiệm vụ và nhận +25 XP học tập.
            </p>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            {completedResult ? (
              <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 text-xs font-semibold">
                <CheckCircle2 className="w-4 h-4" />
                <span>Đã ghi nhận khảo sát (+{completedResult.xp_awarded} XP)</span>
              </div>
            ) : (
              <Button
                onClick={handleCompleteInspection}
                disabled={submitting}
                className="w-full sm:w-auto gap-2 bg-primary text-primary-foreground font-semibold h-9 px-4 text-xs"
              >
                {submitting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Đang lưu...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    Hoàn thành Khảo sát (+25 XP)
                  </>
                )}
              </Button>
            )}
          </div>
        </div>

        {/* FEEDBACK OR ERROR ALERTS */}
        {completedResult && (
          <div className="p-3 bg-emerald-500/10 border-t border-emerald-500/30 text-emerald-800 dark:text-emerald-300 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{completedResult.feedback}</span>
          </div>
        )}

        {errorMessage && (
          <div className="p-3 bg-destructive/10 border-t border-destructive/30 text-destructive text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
export default RelicTurntableInspector;
