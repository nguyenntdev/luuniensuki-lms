"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  CheckCircle2,
  FileCode,
  Layers,
  MapPin,
  RefreshCw,
  Send,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AnnotationToolbar,
  FilterStatus,
  StudioToolMode,
} from "@/components/imperial/studio/AnnotationToolbar";
import { AnnotationCanvas } from "@/components/imperial/studio/AnnotationCanvas";
import { MarkerInspector } from "@/components/imperial/studio/MarkerInspector";
import { PublishReviewDialog } from "@/components/imperial/studio/PublishReviewDialog";
import { ImportExportModal } from "@/components/imperial/studio/ImportExportModal";
import {
  calculateFitTransform,
  clampZoom,
  DEFAULT_ZOOM,
  MAX_ZOOM,
  MIN_ZOOM,
} from "@/lib/imperial/coordinate-utils";
import {
  createAnnotation,
  deleteAnnotation,
  fetchAdminAnnotations,
  fetchAdminMaps,
  fetchSites,
  updateAnnotation,
} from "@/lib/imperial/map-api";
import type {
  ImperialMapAnnotation,
  ImperialMapAsset,
  ImperialSite,
  UVCoordinate,
  ViewportTransform,
} from "@/lib/imperial/map-types";

export interface AnnotationStudioClientProps {
  initialMap?: ImperialMapAsset | null;
  initialAnnotations?: ImperialMapAnnotation[] | null;
  initialSites?: ImperialSite[] | null;
}

export function AnnotationStudioClient({
  initialMap,
  initialAnnotations,
  initialSites,
}: AnnotationStudioClientProps) {
  const [activeMap, setActiveMap] = useState<ImperialMapAsset | null>(
    initialMap || null,
  );
  const [annotations, setAnnotations] = useState<ImperialMapAnnotation[]>(
    initialAnnotations || [],
  );
  const [sites, setSites] = useState<ImperialSite[]>(initialSites || []);
  const [loading, setLoading] = useState(!initialMap);

  // Editor Interaction State
  const [mode, setMode] = useState<StudioToolMode>("SELECT");
  const [filterStatus, setFilterStatus] = useState<FilterStatus>("ALL");
  const [selectedAnnotationId, setSelectedAnnotationId] = useState<
    string | null
  >(null);
  const [draftChanges, setDraftChanges] = useState<
    Record<string, ImperialMapAnnotation>
  >({});
  const [isSaving, setIsSaving] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  // Modal Dialogs
  const [isPublishModalOpen, setIsPublishModalOpen] = useState(false);
  const [isImportExportModalOpen, setIsImportExportModalOpen] = useState(false);

  // Viewport Transform
  const [transform, setTransform] = useState<ViewportTransform>({
    scale: DEFAULT_ZOOM,
    translateX: 0,
    translateY: 0,
    fittedWidth: activeMap?.width_px || 4096,
    fittedHeight: activeMap?.height_px || 3072,
  });

  // Load initial studio data
  const reloadData = useCallback(async () => {
    try {
      setLoading(true);
      const [maps, fetchedSites] = await Promise.all([
        fetchAdminMaps(),
        fetchSites(),
      ]);

      const currentMap = maps[0] || null;
      setActiveMap(currentMap);
      setSites(fetchedSites);

      if (currentMap) {
        const fetchedAnnos = await fetchAdminAnnotations(currentMap.id);
        setAnnotations(fetchedAnnos);
      }
      setDraftChanges({});
    } catch (err) {
      console.error("Studio data reload error:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!initialMap || !initialAnnotations || !initialSites) {
      reloadData();
    }
  }, [initialMap, initialAnnotations, initialSites, reloadData]);

  // Selected annotation object
  const selectedAnnotation = useMemo(() => {
    if (!selectedAnnotationId) return null;
    return annotations.find((a) => a.id === selectedAnnotationId) || null;
  }, [selectedAnnotationId, annotations]);

  // Filtered annotations according to review status
  const visibleAnnotations = useMemo(() => {
    if (filterStatus === "ALL") return annotations;
    if (filterStatus === "DRAFT") {
      return annotations.filter((a) => a.review_status === "draft");
    }
    return annotations.filter((a) => a.review_status === "published");
  }, [annotations, filterStatus]);

  const isDirty = Object.keys(draftChanges).length > 0;

  /**
   * Add a new draft pin at the clicked UV coordinate
   */
  const handleAddPointAtUV = (uv: UVCoordinate) => {
    if (!activeMap) return;

    const newId = `draft-${Date.now()}`;
    const defaultSite = sites[0];

    const newDraft: ImperialMapAnnotation = {
      id: newId,
      map_asset_id: activeMap.id,
      site_id: defaultSite?.id || "",
      shape_type: "point",
      u: uv.u,
      v: uv.v,
      label: defaultSite?.name_vi || "Điểm ghim mới",
      marker_style: "monument",
      review_status: "draft",
      position_confidence: "approximate",
      row_version: 1,
      site: defaultSite
        ? {
            id: defaultSite.id,
            slug: defaultSite.slug,
            name_vi: defaultSite.name_vi,
            name_han_nom: defaultSite.name_han_nom,
            chinese_name: defaultSite.chinese_name,
            summary_vi: defaultSite.description_vi,
            zone_slug: defaultSite.zone_slug || undefined,
            learning_level: defaultSite.learning_level,
            condition: defaultSite.condition,
          }
        : undefined,
    };

    setAnnotations((prev) => [...prev, newDraft]);
    setDraftChanges((prev) => ({ ...prev, [newId]: newDraft }));
    setSelectedAnnotationId(newId);
    setMode("SELECT");
    setNotice("Đã thêm điểm ghim nháp. Chọn công trình liên kết bên phải.");
  };

  /**
   * Update marker UV (during drag or precision input)
   */
  const handleUpdateMarkerUV = (id: string, uv: UVCoordinate) => {
    setAnnotations((prev) =>
      prev.map((a) => (a.id === id ? { ...a, u: uv.u, v: uv.v } : a)),
    );

    setDraftChanges((prev) => {
      const existing = prev[id] || annotations.find((a) => a.id === id);
      if (!existing) return prev;
      return {
        ...prev,
        [id]: { ...existing, u: uv.u, v: uv.v },
      };
    });
  };

  /**
   * Save property changes from Inspector
   */
  const handleInspectorSave = (updated: ImperialMapAnnotation) => {
    setAnnotations((prev) =>
      prev.map((a) => (a.id === updated.id ? updated : a)),
    );
    setDraftChanges((prev) => ({
      ...prev,
      [updated.id]: updated,
    }));
    setNotice("Đã cập nhật thuộc tính nháp. Nhấn 'Lưu nháp' để lưu vào máy chủ.");
  };

  /**
   * Delete marker
   */
  const handleDeleteAnnotation = async (anno: ImperialMapAnnotation) => {
    if (
      !confirm(
        `Bạn có chắc chắn muốn xóa điểm ghim "${anno.label || anno.site?.name_vi}" không?`,
      )
    ) {
      return;
    }

    try {
      if (!anno.id.startsWith("draft-")) {
        await deleteAnnotation(anno.id);
      }
      setAnnotations((prev) => prev.filter((a) => a.id !== anno.id));
      setDraftChanges((prev) => {
        const copy = { ...prev };
        delete copy[anno.id];
        return copy;
      });
      if (selectedAnnotationId === anno.id) {
        setSelectedAnnotationId(null);
      }
      setNotice("Đã xóa điểm ghim thành công.");
    } catch (err) {
      console.error("Delete error:", err);
    }
  };

  /**
   * Save all pending draft modifications to backend API
   */
  const handleSaveDrafts = async () => {
    if (!activeMap || !isDirty) return;

    try {
      setIsSaving(true);
      const itemsToSave = Object.values(draftChanges);

      for (const item of itemsToSave) {
        if (item.id.startsWith("draft-")) {
          // Create new marker
          await createAnnotation(activeMap.id, {
            site_id: item.site_id,
            u: item.u,
            v: item.v,
            label: item.label,
            marker_style: item.marker_style,
            position_confidence: item.position_confidence,
            editorial_notes: item.editorial_notes,
          });
        } else {
          // Update existing marker with optimistic row_version check
          await updateAnnotation(item.id, {
            ...item,
            row_version: item.row_version,
          });
        }
      }

      setDraftChanges({});
      setNotice("Đã lưu toàn bộ bản nháp thành công!");
      await reloadData();
    } catch (err: unknown) {
      console.error("Save drafts error:", err);
      alert("Lỗi khi lưu dữ liệu: " + (err instanceof Error ? err.message : ""));
    } finally {
      setIsSaving(false);
    }
  };

  /**
   * Discard unsaved changes
   */
  const handleDiscardDrafts = () => {
    if (confirm("Hủy bỏ tất cả thay đổi chưa lưu?")) {
      reloadData();
    }
  };

  // Zoom helpers
  const handleZoomIn = () => {
    setTransform((prev) => ({
      ...prev,
      scale: clampZoom(prev.scale * 1.25, MIN_ZOOM, MAX_ZOOM),
    }));
  };

  const handleZoomOut = () => {
    setTransform((prev) => ({
      ...prev,
      scale: clampZoom(prev.scale / 1.25, MIN_ZOOM, MAX_ZOOM),
    }));
  };

  const handleFitToScreen = () => {
    if (!activeMap) return;
    const containerW = window.innerWidth - 380;
    const containerH = window.innerHeight - 140;
    const fit = calculateFitTransform(
      containerW,
      containerH,
      activeMap.width_px,
      activeMap.height_px,
    );

    setTransform({
      scale: 1,
      translateX: fit.offsetX ?? 0,
      translateY: fit.offsetY ?? 0,
      fittedWidth: fit.fittedWidth,
      fittedHeight: fit.fittedHeight,
    });
  };

  const handleScale1To1 = () => {
    if (!activeMap) return;
    setTransform((prev) => ({
      ...prev,
      scale: 1,
      translateX: 0,
      translateY: 0,
    }));
  };

  if (loading || !activeMap) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-stone-950 p-6">
        <div className="space-y-4 w-full max-w-lg text-center">
          <Skeleton className="h-10 w-64 mx-auto rounded-xl bg-stone-800" />
          <Skeleton className="h-4 w-96 mx-auto rounded-lg bg-stone-800" />
          <Skeleton className="h-[450px] w-full rounded-3xl bg-stone-900" />
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex flex-col h-screen w-full overflow-hidden bg-stone-950 text-foreground selection:bg-primary/20">
      {/* Top Banner & Navigation */}
      <header className="h-14 shrink-0 px-4 flex items-center justify-between border-b border-border/70 bg-card/90 backdrop-blur-xl z-30">
        <div className="flex items-center gap-3">
          <Button
            asChild
            variant="ghost"
            size="xs"
            className="text-xs text-muted-foreground hover:text-foreground gap-1"
          >
            <Link href="/dai-noi">
              <ArrowLeft className="w-4 h-4" />
              <span>Xem trang công khai</span>
            </Link>
          </Button>

          <div className="h-4 w-px bg-border/60" />

          <div className="flex items-center gap-2">
            <span className="font-serif font-bold text-sm tracking-tight text-foreground flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-primary" />
              Studio Biên tập Không ảnh Đại Nội
            </span>
            <Badge
              variant="outline"
              className="text-[10px] font-mono bg-amber-500/10 text-amber-400 border-amber-500/20"
            >
              PREVIEW / ADMIN
            </Badge>
          </div>
        </div>

        {/* Notice or Active Map Pill */}
        <div className="flex items-center gap-3">
          {notice && (
            <span className="text-xs text-amber-400 bg-amber-950/40 px-3 py-1 rounded-lg border border-amber-500/30 font-medium">
              {notice}
            </span>
          )}

          <Badge
            variant="outline"
            className="text-xs font-mono bg-secondary/80 text-muted-foreground border-border/70"
          >
            {activeMap.slug} (v{activeMap.version})
          </Badge>
        </div>
      </header>

      {/* Main Studio Work Area */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left / Center Canvas Area */}
        <div className="flex-1 flex flex-col relative overflow-hidden">
          {/* Top Floating Toolbar */}
          <div className="absolute top-4 inset-x-4 z-20 pointer-events-none flex justify-center">
            <div className="pointer-events-auto max-w-full">
              <AnnotationToolbar
                mode={mode}
                onSetMode={setMode}
                filterStatus={filterStatus}
                onSetFilterStatus={setFilterStatus}
                isDirty={isDirty}
                isSaving={isSaving}
                onSaveDrafts={handleSaveDrafts}
                onDiscardDrafts={handleDiscardDrafts}
                onOpenPublishModal={() => setIsPublishModalOpen(true)}
                onOpenImportExportModal={() => setIsImportExportModalOpen(true)}
                onZoomIn={handleZoomIn}
                onZoomOut={handleZoomOut}
                onFitToScreen={handleFitToScreen}
                onScale1To1={handleScale1To1}
                zoomScale={transform.scale}
              />
            </div>
          </div>

          {/* Interactive Annotation Canvas */}
          <AnnotationCanvas
            mapImage={{
              url: activeMap.image_url,
              width: activeMap.width_px,
              height: activeMap.height_px,
              title_vi: activeMap.title_vi,
            }}
            annotations={visibleAnnotations}
            selectedAnnotationId={selectedAnnotationId}
            mode={mode}
            onSelectAnnotation={(anno) =>
              setSelectedAnnotationId(anno ? anno.id : null)
            }
            onAddPointAtUV={handleAddPointAtUV}
            onUpdateMarkerUV={handleUpdateMarkerUV}
            onDeleteAnnotation={handleDeleteAnnotation}
            transform={transform}
            onTransformChange={setTransform}
            className="w-full h-full"
          />
        </div>

        {/* Right Sidebar: Property Inspector */}
        <div className="shrink-0 h-full z-20">
          <MarkerInspector
            annotation={selectedAnnotation}
            sites={sites}
            onSave={handleInspectorSave}
            onDelete={handleDeleteAnnotation}
            onClose={() => setSelectedAnnotationId(null)}
          />
        </div>
      </div>

      {/* Publish Review Dialog */}
      <PublishReviewDialog
        mapAsset={activeMap}
        annotations={annotations}
        isOpen={isPublishModalOpen}
        onClose={() => setIsPublishModalOpen(false)}
        onPublishedSuccess={(publishedAsset) => {
          setActiveMap(publishedAsset);
          setNotice("Đã công bố bản đồ chính thức thành công!");
          reloadData();
        }}
      />

      {/* Import / Export Modal */}
      <ImportExportModal
        mapAsset={activeMap}
        isOpen={isImportExportModalOpen}
        onClose={() => setIsImportExportModalOpen(false)}
        onImportComplete={() => {
          setNotice("Đã nhập dữ liệu điểm ghim thành công!");
          reloadData();
        }}
      />
    </div>
  );
}
