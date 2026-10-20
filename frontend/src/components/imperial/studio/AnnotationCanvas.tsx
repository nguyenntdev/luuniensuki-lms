"use client";

import React, {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  calculateFitTransform,
  clampPan,
  clampUV,
  clampZoom,
  DEFAULT_ZOOM,
  isPointerInBounds,
  MAX_ZOOM,
  MIN_ZOOM,
  screenToUV,
  viewportPointerToUV,
} from "@/lib/imperial/coordinate-utils";
import type {
  ImperialMapAnnotation,
  ScreenCoordinate,
  UVCoordinate,
  ViewportTransform,
} from "@/lib/imperial/map-types";
import { StudioMarker } from "./StudioMarker";
import type { StudioToolMode } from "./AnnotationToolbar";
import { cn } from "@/lib/utils";

export interface AnnotationCanvasProps {
  mapImage: {
    url: string;
    width: number;
    height: number;
    title_vi?: string;
  };
  annotations: ImperialMapAnnotation[];
  selectedAnnotationId: string | null;
  mode: StudioToolMode;
  onSelectAnnotation: (annotation: ImperialMapAnnotation | null) => void;
  onAddPointAtUV: (uv: UVCoordinate) => void;
  onUpdateMarkerUV: (annotationId: string, uv: UVCoordinate) => void;
  onDeleteAnnotation: (annotation: ImperialMapAnnotation) => void;
  transform: ViewportTransform;
  onTransformChange: (transform: ViewportTransform) => void;
  className?: string;
}

export function AnnotationCanvas({
  mapImage,
  annotations,
  selectedAnnotationId,
  mode,
  onSelectAnnotation,
  onAddPointAtUV,
  onUpdateMarkerUV,
  onDeleteAnnotation,
  transform,
  onTransformChange,
  className,
}: AnnotationCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const imagePlaneRef = useRef<HTMLDivElement>(null);

  const intrinsicWidth = mapImage.width || 4096;
  const intrinsicHeight = mapImage.height || 3072;

  // Pan interaction state
  const [isPanning, setIsPanning] = useState(false);
  const panStartRef = useRef<{
    startX: number;
    startY: number;
    startTx: number;
    startTy: number;
  }>({ startX: 0, startY: 0, startTx: 0, startTy: 0 });

  // Marker drag state with rollback capability
  const [draggedMarkerId, setDraggedMarkerId] = useState<string | null>(null);
  const dragMarkerRef = useRef<{
    annotationId: string;
    originalUV: UVCoordinate;
    isDragging: boolean;
  } | null>(null);

  /**
   * Converts a client pointer event into normalized UV coordinates on the canonical image plane.
   * Utilizes DOMMatrix pointer inversion to accurately handle scale and translation.
   * Automatically rejects clicks inside the letterbox area.
   */
  const pointerEventToUV = useCallback(
    (e: React.PointerEvent | PointerEvent | React.MouseEvent): UVCoordinate | null => {
      if (!containerRef.current) return null;
      const rect = containerRef.current.getBoundingClientRect();
      const screenCoord: ScreenCoordinate = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      };

      // Check letterbox bounds
      if (!isPointerInBounds(screenCoord, transform, intrinsicWidth, intrinsicHeight)) {
        return null;
      }

      // Try DOMMatrix inversion if supported
      if (typeof window !== "undefined" && typeof DOMMatrix !== "undefined") {
        try {
          const matrix = new DOMMatrix([
            transform.scale,
            0,
            0,
            transform.scale,
            transform.translateX,
            transform.translateY,
          ]);
          const inverse = matrix.inverse();
          const uv = viewportPointerToUV(
            screenCoord,
            inverse,
            transform.fittedWidth ?? intrinsicWidth,
            transform.fittedHeight ?? intrinsicHeight,
          );
          if (uv) return uv;
        } catch {
          // Fall back to direct algebraic conversion
        }
      }

      return screenToUV(screenCoord, transform, intrinsicWidth, intrinsicHeight);
    },
    [transform, intrinsicWidth, intrinsicHeight],
  );

  /**
   * Pointer Down handler for Canvas
   */
  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    // Only primary button
    if (e.button !== 0) return;

    if (mode === "PAN" || e.altKey || (e as any).spaceKey) {
      setIsPanning(true);
      panStartRef.current = {
        startX: e.clientX,
        startY: e.clientY,
        startTx: transform.translateX,
        startTy: transform.translateY,
      };
      (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
      return;
    }

    if (mode === "ADD_POINT") {
      const uv = pointerEventToUV(e);
      if (uv) {
        onAddPointAtUV(uv);
      }
      return;
    }

    if (mode === "SELECT") {
      // Click on background deselects marker
      onSelectAnnotation(null);

      // Also allow panning when clicking blank space
      setIsPanning(true);
      panStartRef.current = {
        startX: e.clientX,
        startY: e.clientY,
        startTx: transform.translateX,
        startTy: transform.translateY,
      };
      (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    }
  };

  /**
   * Pointer Move handler for Canvas
   */
  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    // 1. Marker Relocation Dragging
    if (dragMarkerRef.current?.isDragging && draggedMarkerId) {
      const uv = pointerEventToUV(e);
      if (uv) {
        onUpdateMarkerUV(draggedMarkerId, uv);
      }
      return;
    }

    // 2. Viewport Panning
    if (isPanning) {
      const dx = e.clientX - panStartRef.current.startX;
      const dy = e.clientY - panStartRef.current.startY;

      onTransformChange({
        ...transform,
        translateX: panStartRef.current.startTx + dx,
        translateY: panStartRef.current.startTy + dy,
      });
    }
  };

  /**
   * Pointer Up handler for Canvas
   */
  const handlePointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    if (dragMarkerRef.current?.isDragging) {
      dragMarkerRef.current = null;
      setDraggedMarkerId(null);
    }

    if (isPanning) {
      setIsPanning(false);
      try {
        (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId);
      } catch {
        // Ignored
      }
    }
  };

  /**
   * Start dragging an individual marker
   */
  const handleMarkerDragStart = (
    annotation: ImperialMapAnnotation,
    e: React.PointerEvent<HTMLDivElement>,
  ) => {
    if (mode !== "SELECT") return;

    dragMarkerRef.current = {
      annotationId: annotation.id,
      originalUV: { u: annotation.u, v: annotation.v },
      isDragging: true,
    };
    setDraggedMarkerId(annotation.id);
  };

  /**
   * Mouse Wheel zoom
   */
  const handleWheel = (e: React.WheelEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const screenX = e.clientX - rect.left;
    const screenY = e.clientY - rect.top;

    const factor = e.deltaY < 0 ? 1.15 : 1 / 1.15;
    const newScale = clampZoom(transform.scale * factor, MIN_ZOOM, MAX_ZOOM);
    if (newScale === transform.scale) return;

    const qx = (screenX - transform.translateX) / transform.scale;
    const qy = (screenY - transform.translateY) / transform.scale;

    onTransformChange({
      ...transform,
      scale: newScale,
      translateX: screenX - qx * newScale,
      translateY: screenY - qy * newScale,
    });
  };

  /**
   * Cancel drag operation with Escape key (Rollback to original UV)
   */
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && dragMarkerRef.current) {
        onUpdateMarkerUV(
          dragMarkerRef.current.annotationId,
          dragMarkerRef.current.originalUV,
        );
        dragMarkerRef.current = null;
        setDraggedMarkerId(null);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onUpdateMarkerUV]);

  const imageWidth = transform.fittedWidth || intrinsicWidth;
  const imageHeight = transform.fittedHeight || intrinsicHeight;

  return (
    <div
      ref={containerRef}
      role="region"
      aria-label="Khung canvas biên tập bản đồ"
      tabIndex={0}
      onWheel={handleWheel}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
      className={cn(
        "relative w-full h-full overflow-hidden select-none bg-stone-950 focus:outline-none",
        mode === "PAN"
          ? isPanning
            ? "cursor-grabbing"
            : "cursor-grab"
          : mode === "ADD_POINT"
            ? "cursor-crosshair"
            : mode === "DELETE"
              ? "cursor-not-allowed"
              : isPanning
                ? "cursor-grabbing"
                : "cursor-default",
        className,
      )}
    >
      {/* Transform Plane */}
      <div
        ref={imagePlaneRef}
        className="absolute origin-top-left will-change-transform"
        style={{
          transform: `translate3d(${transform.translateX}px, ${transform.translateY}px, 0) scale(${transform.scale})`,
          width: `${imageWidth}px`,
          height: `${imageHeight}px`,
        }}
      >
        {/* Orthomosaic Base Map */}
        <img
          src={mapImage.url}
          alt={mapImage.title_vi || "Bản đồ không ảnh Đại Nội"}
          width={intrinsicWidth}
          height={intrinsicHeight}
          draggable={false}
          className="w-full h-full object-contain pointer-events-none drop-shadow-2xl"
        />

        {/* Marker Layer */}
        <div className="absolute inset-0 pointer-events-none">
          {annotations.map((anno) => (
            <StudioMarker
              key={anno.id}
              annotation={anno}
              isSelected={selectedAnnotationId === anno.id}
              scale={transform.scale}
              interactiveMode={mode}
              onSelect={onSelectAnnotation}
              onDragStart={handleMarkerDragStart}
              onDelete={onDeleteAnnotation}
            />
          ))}
        </div>
      </div>

      {/* Mode Status Pill Overlay */}
      <div className="absolute top-4 left-4 z-20 pointer-events-none flex items-center gap-2 px-3 py-1.5 rounded-xl bg-card/90 backdrop-blur-md border border-border/70 text-xs font-semibold shadow-lg">
        <span
          className={cn(
            "w-2 h-2 rounded-full animate-pulse",
            mode === "ADD_POINT"
              ? "bg-amber-400"
              : mode === "DELETE"
                ? "bg-destructive"
                : mode === "PAN"
                  ? "bg-sky-400"
                  : "bg-emerald-400",
          )}
        />
        <span className="text-foreground">
          {mode === "SELECT"
            ? "Chế độ: Chọn & Kéo di chuyển điểm ghim (Kéo chuột để định vị lại)"
            : mode === "ADD_POINT"
              ? "Chế độ: Nhấp vào vị trí bất kỳ trên ảnh để thêm điểm ghim mới"
              : mode === "PAN"
                ? "Chế độ: Kéo duyệt toàn cảnh bản đồ"
                : "Chế độ: Nhấp vào điểm ghim để xóa"}
        </span>
      </div>
    </div>
  );
}
