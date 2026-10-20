"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Check,
  CheckCircle2,
  ChevronRight,
  Copy,
  ExternalLink,
  Eye,
  HelpCircle,
  History,
  Image as ImageIcon,
  Layers,
  MapPin,
  Minus,
  Move,
  Palette,
  Plus,
  Quote,
  RotateCcw,
  Save,
  Scroll,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ArtDetailModal } from "@/components/imperial/art-detail/ArtDetailModal";
import {
  deleteMediaHotspot,
  FALLBACK_ART_DETAILS,
  FALLBACK_LEARNING_MEDIA,
  fetchSiteArtDetails,
  fetchSiteLearningMedia,
  saveArtDetail,
  saveMediaHotspot,
} from "@/lib/imperial/v51-api";
import {
  ArtDetailKind,
  ArtDetailStoryType,
  EvidenceStrength,
  ImperialArtDetail,
  ImperialLearningMedia,
  ImperialMediaHotspot,
  PointKind,
  STORY_TYPE_METADATA,
} from "@/lib/imperial/v51-types";
import type { ImperialSite } from "@/lib/imperial/map-types";

interface ArtDetailStudioClientProps {
  initialSites: ImperialSite[];
  initialMedia?: ImperialLearningMedia[];
}

export function ArtDetailStudioClient({
  initialSites,
  initialMedia,
}: ArtDetailStudioClientProps) {
  const sites = initialSites || [];
  const [selectedSiteSlug, setSelectedSiteSlug] = useState<string>(
    sites[0]?.slug || "dien-thai-hoa",
  );

  // Media assets for the selected site
  const [mediaList, setMediaList] = useState<ImperialLearningMedia[]>(
    initialMedia || FALLBACK_LEARNING_MEDIA,
  );
  const [selectedMediaId, setSelectedMediaId] = useState<string>(
    mediaList[0]?.id || "media-thai-hoa-2d",
  );

  // Hotspots on active media
  const [hotspots, setHotspots] = useState<ImperialMediaHotspot[]>([]);
  const [selectedHotspotId, setSelectedHotspotId] = useState<string | null>(null);

  // Available art details for linking
  const [availableDetails, setAvailableDetails] = useState<ImperialArtDetail[]>(
    FALLBACK_ART_DETAILS,
  );

  // Active Art Detail bound to selected hotspot
  const [activeDetail, setActiveDetail] = useState<ImperialArtDetail | null>(null);

  // Editor states
  const [toolMode, setToolMode] = useState<"select" | "add-pin">("select");
  const [activeTab, setActiveTab] = useState<"hotspot" | "art-detail">("hotspot");
  const [zoomScale, setZoomScale] = useState(1);
  const [notice, setNotice] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [mobileView, setMobileView] = useState<"canvas" | "inspector">("canvas");

  // Image Ref & bounds
  const imageContainerRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);

  const activeSite = sites.find((s) => s.slug === selectedSiteSlug) || sites[0];
  const activeMedia =
    mediaList.find((m) => m.id === selectedMediaId) || mediaList[0];

  // Load media and details when selected site changes
  const loadSiteMedia = useCallback(async (siteSlug: string) => {
    try {
      const [mediaRes, detailsRes] = await Promise.all([
        fetchSiteLearningMedia(siteSlug),
        fetchSiteArtDetails(siteSlug),
      ]);
      setMediaList(mediaRes);
      if (mediaRes.length > 0) {
        setSelectedMediaId(mediaRes[0].id);
        setHotspots(mediaRes[0].hotspots || []);
        if (mediaRes[0].hotspots && mediaRes[0].hotspots.length > 0) {
          setSelectedHotspotId(mediaRes[0].hotspots[0].id);
        } else {
          setSelectedHotspotId(null);
        }
      }
      setAvailableDetails(detailsRes);
    } catch (err) {
      console.error("Failed to load site media:", err);
    }
  }, []);

  useEffect(() => {
    loadSiteMedia(selectedSiteSlug);
  }, [selectedSiteSlug, loadSiteMedia]);

  // Update hotspots when selected media changes
  useEffect(() => {
    if (activeMedia) {
      const hList = activeMedia.hotspots || [];
      setHotspots(hList);
      if (hList.length > 0) {
        setSelectedHotspotId(hList[0].id);
      } else {
        setSelectedHotspotId(null);
        setActiveDetail(null);
      }
    }
  }, [activeMedia]);

  // Sync active detail when selected hotspot changes
  useEffect(() => {
    if (!selectedHotspotId) {
      setActiveDetail(null);
      return;
    }
    const currentHotspot = hotspots.find((h) => h.id === selectedHotspotId);
    if (!currentHotspot) return;

    if (currentHotspot.detail_id) {
      const match = availableDetails.find(
        (d) => d.id === currentHotspot.detail_id || d.slug === currentHotspot.art_detail_slug,
      );
      if (match) {
        setActiveDetail(match);
        return;
      }
    }

    // Default template if no detail is linked
    setActiveDetail({
      id: `detail-${Date.now()}`,
      slug: `chi-tiet-${Date.now()}`,
      site_id: activeSite?.id || "",
      site_slug: activeSite?.slug || "",
      site_name_vi: activeSite?.name_vi || "",
      title: currentHotspot.title || "Chi tiết mỹ thuật",
      kind: "carving",
      motif: "",
      material: "",
      technique: "",
      description_observation: "",
      story_body: "",
      story_type: "documented_event",
      meaning_body: "",
      historical_value_body: "",
      cultural_value_body: "",
      art_value_body: "",
      review_status: "draft",
      claim_sources: [
        {
          section: "Nguồn chính sử",
          claim_text: "Ghi chép sự kiện liên quan đến chi tiết kiến trúc.",
          source_title: "Đại Nam Thực Lục Chính Biên",
          source_locator: "Quyển...",
          evidence_strength: "verified",
        },
      ],
      questions: [
        {
          id: `q-${Date.now()}`,
          question_type: "multiple_choice",
          prompt: "Chi tiết mỹ thuật này mang ý nghĩa gì trong nghi lễ cung đình?",
          options: ["Đáp án A", "Đáp án B", "Đáp án C", "Đáp án D"],
          answer_key: "0",
          explanation: "Giải thích đáp án chuẩn mực theo sử liệu triều Nguyễn.",
          display_order: 1,
        },
      ],
    });
  }, [selectedHotspotId, hotspots, availableDetails, activeSite]);

  const selectedHotspot = hotspots.find((h) => h.id === selectedHotspotId) || null;

  // Handle clicking on the image canvas
  const handleCanvasClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (toolMode !== "add-pin" || !activeMedia) return;

    const img = imageRef.current;
    if (!img) return;

    const rect = img.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    if (clickX < 0 || clickX > rect.width || clickY < 0 || clickY > rect.height) return;

    // Calculate normalized UV [0.0 .. 1.0]
    const u = Math.max(0, Math.min(1, clickX / rect.width));
    const v = Math.max(0, Math.min(1, clickY / rect.height));

    const newHotspotId = `draft-hotspot-${Date.now()}`;
    const newHotspot: ImperialMediaHotspot = {
      id: newHotspotId,
      media_id: activeMedia.id,
      point_kind: "point",
      u: Number(u.toFixed(4)),
      v: Number(v.toFixed(4)),
      title: "Điểm quan sát mới",
      description: "Nhập mô tả quan sát trực quan cho điểm ghim này.",
      review_status: "draft",
    };

    setHotspots((prev) => [...prev, newHotspot]);
    setSelectedHotspotId(newHotspotId);
    setToolMode("select");
    setNotice("Đã thêm điểm ghim mới tại tọa độ UV (" + Math.round(u * 100) + "%, " + Math.round(v * 100) + "%). Hãy hoàn thiện thông tin bên phải.");
  };

  // Hotspot field updater
  const updateSelectedHotspot = (fields: Partial<ImperialMediaHotspot>) => {
    if (!selectedHotspotId) return;
    setHotspots((prev) =>
      prev.map((h) => (h.id === selectedHotspotId ? { ...h, ...fields } : h)),
    );
  };

  // Art Detail field updater
  const updateActiveDetail = (fields: Partial<ImperialArtDetail>) => {
    if (!activeDetail) return;
    setActiveDetail((prev) => (prev ? { ...prev, ...fields } : null));
  };

  // Save Hotspot and Art Detail
  const handleSave = async () => {
    if (!selectedHotspot) return;

    setIsSaving(true);
    try {
      let savedDetailId = selectedHotspot.detail_id;
      let savedDetailSlug = selectedHotspot.art_detail_slug;

      // 1. Save or bind Art Detail if active
      if (activeDetail) {
        const savedDetail = await saveArtDetail({
          ...activeDetail,
          site_id: activeSite.id,
          site_slug: activeSite.slug,
          site_name_vi: activeSite.name_vi,
        });
        savedDetailId = savedDetail.id;
        savedDetailSlug = savedDetail.slug;

        // update in local available details
        setAvailableDetails((prev) => {
          const idx = prev.findIndex((d) => d.id === savedDetail.id);
          if (idx >= 0) {
            const copy = [...prev];
            copy[idx] = savedDetail;
            return copy;
          }
          return [...prev, savedDetail];
        });
      }

      // 2. Save Hotspot
      const savedSpot = await saveMediaHotspot({
        ...selectedHotspot,
        media_id: activeMedia.id,
        detail_id: savedDetailId,
        art_detail_slug: savedDetailSlug,
        review_status: "published",
      });

      setHotspots((prev) =>
        prev.map((h) => (h.id === selectedHotspot.id ? savedSpot : h)),
      );

      setNotice("Đã lưu thành công điểm quan sát và hồ sơ khảo cứu mỹ thuật!");
      setTimeout(() => setNotice(null), 4000);
    } catch (err) {
      console.error("Save error:", err);
      setNotice("Có lỗi khi lưu. Vui lòng kiểm tra lại kết nối.");
    } finally {
      setIsSaving(false);
    }
  };

  // Delete Hotspot
  const handleDeleteHotspot = async () => {
    if (!selectedHotspot) return;
    if (!confirm("Bạn có chắc chắn muốn xóa điểm ghim này khỏi hình ảnh?")) return;

    try {
      await deleteMediaHotspot(selectedHotspot.id);
      setHotspots((prev) => prev.filter((h) => h.id !== selectedHotspot.id));
      setSelectedHotspotId(null);
      setActiveDetail(null);
      setNotice("Đã xóa điểm ghim.");
      setTimeout(() => setNotice(null), 3000);
    } catch (err) {
      console.error("Delete error:", err);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-background overflow-hidden text-foreground">
      {/* Top Studio Bar */}
      <header className="h-14 border-b border-border bg-card/90 px-4 flex items-center justify-between gap-3 shrink-0 z-30">
        <div className="flex items-center gap-3">
          <Link href="/admin/dai-noi/annotate">
            <Button variant="ghost" size="sm" className="h-8 gap-1.5 text-xs">
              <ArrowLeft className="w-3.5 h-3.5" />
              Bản đồ không ảnh
            </Button>
          </Link>

          <div className="h-4 w-px bg-border" />

          <div className="flex items-center gap-2">
            <Palette className="w-4 h-4 text-primary" />
            <span className="font-serif font-bold text-sm">
              Art Detail Annotation Studio
            </span>
            <Badge variant="outline" className="text-[10px] bg-primary/10 text-primary border-primary/30">
              V5.1 Multi-Media
            </Badge>
          </div>
        </div>

        {/* Site & Media Switcher */}
        <div className="flex items-center gap-2">
          {/* Site Selector */}
          <select
            value={selectedSiteSlug}
            onChange={(e) => setSelectedSiteSlug(e.target.value)}
            className="text-xs bg-background border border-border rounded-md px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
          >
            {sites.map((s) => (
              <option key={s.id} value={s.slug}>
                {s.name_vi}
              </option>
            ))}
          </select>

          {/* Media Asset Selector */}
          <select
            value={selectedMediaId}
            onChange={(e) => setSelectedMediaId(e.target.value)}
            className="text-xs bg-background border border-border rounded-md px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary max-w-[200px]"
          >
            {mediaList.map((m) => (
              <option key={m.id} value={m.id}>
                {m.title_vi} ({m.kind === "panorama360" ? "360°" : "2D"})
              </option>
            ))}
          </select>

          {/* Mobile View Switcher (visible on screens < lg) */}
          <div className="flex lg:hidden items-center border border-border rounded-md p-0.5 bg-muted/60 text-xs">
            <button
              type="button"
              onClick={() => setMobileView("canvas")}
              className={`px-2 py-1 rounded text-xs transition-colors ${
                mobileView === "canvas" ? "bg-background font-semibold shadow-xs text-foreground" : "text-muted-foreground"
              }`}
            >
              Bản vẽ
            </button>
            <button
              type="button"
              onClick={() => setMobileView("inspector")}
              className={`px-2 py-1 rounded text-xs transition-colors ${
                mobileView === "inspector" ? "bg-background font-semibold shadow-xs text-foreground" : "text-muted-foreground"
              }`}
            >
              Biên tập
            </button>
          </div>

          {/* Preview Button */}
          {activeDetail && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsPreviewOpen(true)}
              className="h-8 text-xs gap-1"
            >
              <Eye className="w-3.5 h-3.5" />
              Xem trước
            </Button>
          )}

          {/* Save Button */}
          <Button
            size="sm"
            onClick={handleSave}
            disabled={!selectedHotspot || isSaving}
            className="h-8 text-xs gap-1.5 bg-primary text-primary-foreground"
          >
            <Save className="w-3.5 h-3.5" />
            {isSaving ? "Đang lưu..." : "Lưu thay đổi"}
          </Button>
        </div>
      </header>

      {/* Notice Banner */}
      {notice && (
        <div className="bg-primary/10 border-b border-primary/20 px-4 py-1.5 text-xs text-primary flex items-center justify-between">
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" />
            {notice}
          </span>
          <button onClick={() => setNotice(null)}>
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Main Studio Body: Left Canvas + Right Inspector */}
      <div className="flex-1 flex overflow-hidden">
        {/* LEFT: Interactive Media Canvas */}
        <div
          className={`flex-1 flex flex-col bg-stone-950 relative overflow-hidden ${
            mobileView === "canvas" ? "flex" : "hidden lg:flex"
          }`}
        >
          {/* Canvas Toolbar */}
          <div className="absolute top-3 left-3 z-20 flex items-center gap-1.5 bg-black/75 backdrop-blur-md p-1 rounded-lg border border-white/15 text-white">
            <Button
              size="sm"
              variant={toolMode === "select" ? "secondary" : "ghost"}
              onClick={() => setToolMode("select")}
              className="h-7 text-xs px-2.5 text-white"
            >
              <Move className="w-3.5 h-3.5 mr-1" />
              Chọn điểm
            </Button>

            <Button
              size="sm"
              variant={toolMode === "add-pin" ? "default" : "ghost"}
              onClick={() => setToolMode("add-pin")}
              className="h-7 text-xs px-2.5 text-white"
            >
              <Plus className="w-3.5 h-3.5 mr-1" />
              Thêm điểm ghim (Click ảnh)
            </Button>

            <div className="w-px h-4 bg-white/20 mx-1" />

            <Button
              size="icon"
              variant="ghost"
              onClick={() => setZoomScale((z) => Math.min(z + 0.25, 3))}
              className="w-7 h-7 text-white"
              title="Phóng to"
            >
              <Plus className="w-3.5 h-3.5" />
            </Button>

            <Button
              size="icon"
              variant="ghost"
              onClick={() => setZoomScale((z) => Math.max(z - 0.25, 0.75))}
              className="w-7 h-7 text-white"
              title="Thu nhỏ"
            >
              <Minus className="w-3.5 h-3.5" />
            </Button>

            <Button
              size="icon"
              variant="ghost"
              onClick={() => setZoomScale(1)}
              className="w-7 h-7 text-white"
              title="Reset"
            >
              <RotateCcw className="w-3 h-3" />
            </Button>
          </div>

          {/* Canvas Viewport */}
          <div
            ref={imageContainerRef}
            onClick={handleCanvasClick}
            className={`w-full h-full flex items-center justify-center p-6 select-none overflow-auto ${
              toolMode === "add-pin" ? "cursor-crosshair" : "cursor-default"
            }`}
          >
            {activeMedia ? (
              <div
                className="relative transition-transform duration-100 shadow-2xl"
                style={{ transform: `scale(${zoomScale})` }}
              >
                <img
                  ref={imageRef}
                  src={activeMedia.media_url}
                  alt={activeMedia.title_vi}
                  className="max-h-[75vh] w-auto max-w-full rounded border border-white/20 object-contain pointer-events-none"
                />

                {/* Hotspot Pins */}
                {hotspots.map((hotspot) => {
                  const isSelected = hotspot.id === selectedHotspotId;
                  return (
                    <button
                      key={hotspot.id}
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedHotspotId(hotspot.id);
                        setToolMode("select");
                      }}
                      className={`absolute z-20 -translate-x-1/2 -translate-y-1/2 group focus:outline-none`}
                      style={{
                        left: `${hotspot.u * 100}%`,
                        top: `${hotspot.v * 100}%`,
                      }}
                    >
                      <span
                        className={`flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold border-2 shadow-lg transition-transform ${
                          isSelected
                            ? "bg-amber-400 text-stone-950 border-white ring-4 ring-amber-400/50 scale-125"
                            : "bg-black/80 text-white border-amber-400 hover:scale-110"
                        }`}
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                      </span>
                      <span className="absolute left-1/2 -translate-x-1/2 top-8 whitespace-nowrap bg-black/85 text-white text-[10px] px-2 py-0.5 rounded shadow pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity">
                        {hotspot.title}
                      </span>
                    </button>
                  );
                })}
              </div>
            ) : (
              <div className="text-zinc-500 text-sm">Chưa có ảnh tư liệu cho công trình này.</div>
            )}
          </div>
        </div>

        {/* RIGHT: Inspector & Editor Panel */}
        <aside
          className={`lg:w-96 w-full border-l border-border bg-card flex flex-col shrink-0 overflow-y-auto ${
            mobileView === "inspector" ? "flex" : "hidden lg:flex"
          }`}
        >
          {/* Tab Switcher */}
          <div className="flex border-b border-border bg-muted/40 p-1">
            <button
              onClick={() => setActiveTab("hotspot")}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                activeTab === "hotspot"
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Điểm ghim ({hotspots.length})
            </button>
            <button
              onClick={() => setActiveTab("art-detail")}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                activeTab === "art-detail"
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Hồ sơ mỹ thuật & Điển tích
            </button>
          </div>

          <div className="p-4 space-y-5 flex-1">
            {selectedHotspot ? (
              activeTab === "hotspot" ? (
                /* TAB 1: HOTSPOT INSPECTOR */
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-xs text-muted-foreground uppercase tracking-wider">
                      Thông tin điểm ghim
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleDeleteHotspot}
                      className="text-rose-600 hover:bg-rose-500/10 h-7 text-xs px-2"
                    >
                      <Trash2 className="w-3 h-3 mr-1" />
                      Xóa ghim
                    </Button>
                  </div>

                  {/* Title */}
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-foreground">
                      Tiêu đề điểm quan sát
                    </label>
                    <Input
                      value={selectedHotspot.title}
                      onChange={(e) => updateSelectedHotspot({ title: e.target.value })}
                      placeholder="Ví dụ: Bức hoành phi ngự bút..."
                      className="text-xs h-8"
                    />
                  </div>

                  {/* Description */}
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-foreground">
                      Mô tả sơ lược (Tooltip)
                    </label>
                    <textarea
                      value={selectedHotspot.description || ""}
                      onChange={(e) => updateSelectedHotspot({ description: e.target.value })}
                      rows={2}
                      className="w-full text-xs bg-background border border-border rounded-md p-2 focus:ring-1 focus:ring-primary focus:outline-none"
                    />
                  </div>

                  {/* UV Coordinates */}
                  <div className="grid grid-cols-2 gap-2 bg-muted/40 p-2.5 rounded-lg border border-border/50 text-xs">
                    <div>
                      <label className="text-[11px] text-muted-foreground block">
                        Tọa độ U (trục ngang 0..1):
                      </label>
                      <Input
                        type="number"
                        step="0.01"
                        min="0"
                        max="1"
                        value={selectedHotspot.u}
                        onChange={(e) =>
                          updateSelectedHotspot({ u: parseFloat(e.target.value) || 0 })
                        }
                        className="h-7 text-xs mt-1"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] text-muted-foreground block">
                        Tọa độ V (trục dọc 0..1):
                      </label>
                      <Input
                        type="number"
                        step="0.01"
                        min="0"
                        max="1"
                        value={selectedHotspot.v}
                        onChange={(e) =>
                          updateSelectedHotspot({ v: parseFloat(e.target.value) || 0 })
                        }
                        className="h-7 text-xs mt-1"
                      />
                    </div>
                  </div>

                  {/* Point Kind */}
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-foreground">Loại điểm ghim</label>
                    <select
                      value={selectedHotspot.point_kind}
                      onChange={(e) =>
                        updateSelectedHotspot({ point_kind: e.target.value as PointKind })
                      }
                      className="w-full text-xs bg-background border border-border rounded-md p-2 focus:ring-1 focus:ring-primary focus:outline-none"
                    >
                      <option value="point">Điểm ghim đơn (Point)</option>
                      <option value="rect">Khung chữ nhật (Rect)</option>
                      <option value="polygon">Đa giác (Polygon)</option>
                    </select>
                  </div>

                  {/* Bound Art Detail Linker */}
                  <div className="pt-2 border-t border-border/60 space-y-2">
                    <label className="text-xs font-semibold text-foreground block">
                      Liên kết hồ sơ chi tiết mỹ thuật
                    </label>
                    <select
                      value={selectedHotspot.detail_id || ""}
                      onChange={(e) => {
                        const val = e.target.value;
                        const match = availableDetails.find((d) => d.id === val);
                        updateSelectedHotspot({
                          detail_id: val || null,
                          art_detail_slug: match?.slug || null,
                        });
                        if (match) setActiveDetail(match);
                      }}
                      className="w-full text-xs bg-background border border-border rounded-md p-2 focus:ring-1 focus:ring-primary focus:outline-none"
                    >
                      <option value="">-- Tạo hồ sơ mỹ thuật mới --</option>
                      {availableDetails.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.title} ({d.kind})
                        </option>
                      ))}
                    </select>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setActiveTab("art-detail")}
                      className="w-full text-xs h-8 gap-1.5 mt-1"
                    >
                      <Palette className="w-3.5 h-3.5" />
                      Chỉnh sửa nội dung hồ sơ mỹ thuật →
                    </Button>
                  </div>
                </div>
              ) : activeDetail ? (
                /* TAB 2: ART DETAIL FORM (6 SECTIONS) */
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-xs text-muted-foreground uppercase tracking-wider">
                      Hồ sơ Mỹ thuật & Điển tích
                    </span>
                    <Badge variant="outline" className="text-[10px]">
                      {activeDetail.kind}
                    </Badge>
                  </div>

                  {/* Title & Slug */}
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-foreground">
                      Tên chi tiết mỹ thuật
                    </label>
                    <Input
                      value={activeDetail.title}
                      onChange={(e) => updateActiveDetail({ title: e.target.value })}
                      placeholder="Ví dụ: Ngai vàng điện Thái Hòa..."
                      className="text-xs h-8"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-xs font-medium text-foreground">Slug định danh URL</label>
                    <Input
                      value={activeDetail.slug}
                      onChange={(e) => updateActiveDetail({ slug: e.target.value })}
                      placeholder="ngai-vang-dien-thai-hoa"
                      className="text-xs h-8"
                    />
                  </div>

                  {/* Kind & Story Type */}
                  <div className="grid grid-cols-2 gap-2">
                    <div className="space-y-1">
                      <label className="text-[11px] font-medium text-muted-foreground">Loại hình</label>
                      <select
                        value={activeDetail.kind}
                        onChange={(e) =>
                          updateActiveDetail({ kind: e.target.value as ArtDetailKind })
                        }
                        className="w-full text-xs bg-background border border-border rounded-md p-1.5 focus:ring-1 focus:ring-primary focus:outline-none"
                      >
                        <option value="carving">Chạm khắc (Carving)</option>
                        <option value="pattern">Hoa văn (Pattern)</option>
                        <option value="mosaic">Khảm cẩn sành sứ (Mosaic)</option>
                        <option value="painting">Bích họa (Painting)</option>
                        <option value="relief">Phù điêu (Relief)</option>
                      </select>
                    </div>

                    <div className="space-y-1">
                      <label className="text-[11px] font-medium text-muted-foreground">Nhóm dữ liệu</label>
                      <select
                        value={activeDetail.story_type}
                        onChange={(e) =>
                          updateActiveDetail({
                            story_type: e.target.value as ArtDetailStoryType,
                          })
                        }
                        className="w-full text-xs bg-background border border-border rounded-md p-1.5 focus:ring-1 focus:ring-primary focus:outline-none"
                      >
                        <option value="documented_event">Sử liệu thành văn</option>
                        <option value="legend">Huyền sử & Điển tích</option>
                        <option value="oral_account">Giai thoại dân gian</option>
                        <option value="interpretation">Khảo cứu mỹ thuật</option>
                      </select>
                    </div>
                  </div>

                  {/* Motif, Material, Technique */}
                  <div className="space-y-2 bg-muted/30 p-2.5 rounded-lg border border-border/50 text-xs">
                    <div>
                      <label className="text-[11px] text-muted-foreground block">Đồ án họa tiết:</label>
                      <Input
                        value={activeDetail.motif || ""}
                        onChange={(e) => updateActiveDetail({ motif: e.target.value })}
                        placeholder="Ví dụ: Cửu Long tranh châu..."
                        className="h-7 text-xs mt-0.5"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] text-muted-foreground block">Chất liệu:</label>
                      <Input
                        value={activeDetail.material || ""}
                        onChange={(e) => updateActiveDetail({ material: e.target.value })}
                        placeholder="Gỗ lim, thếp vàng quỳ..."
                        className="h-7 text-xs mt-0.5"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] text-muted-foreground block">Kỹ thuật:</label>
                      <Input
                        value={activeDetail.technique || ""}
                        onChange={(e) => updateActiveDetail({ technique: e.target.value })}
                        placeholder="Chạm lộng kênh bong..."
                        className="h-7 text-xs mt-0.5"
                      />
                    </div>
                  </div>

                  {/* 1. Observation */}
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-foreground flex items-center gap-1">
                      <Eye className="w-3.5 h-3.5 text-primary" />
                      1. Mô tả quan sát trực quan
                    </label>
                    <textarea
                      value={activeDetail.description_observation || ""}
                      onChange={(e) =>
                        updateActiveDetail({ description_observation: e.target.value })
                      }
                      rows={3}
                      className="w-full text-xs bg-background border border-border rounded-md p-2 focus:ring-1 focus:ring-primary focus:outline-none"
                      placeholder="Mô tả chi tiết những gì mắt thường và chuyên gia nhìn thấy..."
                    />
                  </div>

                  {/* 2. Story / Legend */}
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-foreground flex items-center gap-1">
                      <Scroll className="w-3.5 h-3.5 text-amber-600" />
                      2. Điển tích / Câu chuyện lịch sử
                    </label>
                    <textarea
                      value={activeDetail.story_body || ""}
                      onChange={(e) => updateActiveDetail({ story_body: e.target.value })}
                      rows={4}
                      className="w-full text-xs bg-background border border-border rounded-md p-2 focus:ring-1 focus:ring-primary focus:outline-none"
                      placeholder="Câu chuyện, sự kiện hoặc điển tích gắn với chi tiết này..."
                    />
                  </div>

                  {/* 3. Meaning */}
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-foreground flex items-center gap-1">
                      <Sparkles className="w-3.5 h-3.5 text-purple-600" />
                      3. Ý nghĩa biểu tượng
                    </label>
                    <textarea
                      value={activeDetail.meaning_body || ""}
                      onChange={(e) => updateActiveDetail({ meaning_body: e.target.value })}
                      rows={2}
                      className="w-full text-xs bg-background border border-border rounded-md p-2 focus:ring-1 focus:ring-primary focus:outline-none"
                      placeholder="Ý nghĩa triết lý, vũ trụ quan hoặc biểu tượng quyền lực..."
                    />
                  </div>

                  {/* 4. Values (Historical, Cultural, Art) */}
                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-foreground flex items-center gap-1">
                      <History className="w-3.5 h-3.5 text-emerald-600" />
                      4. Giá trị Lịch sử & Văn hóa
                    </label>
                    <Input
                      value={activeDetail.historical_value_body || ""}
                      onChange={(e) =>
                        updateActiveDetail({ historical_value_body: e.target.value })
                      }
                      placeholder="Giá trị lịch sử..."
                      className="text-xs h-7"
                    />
                    <Input
                      value={activeDetail.cultural_value_body || ""}
                      onChange={(e) =>
                        updateActiveDetail({ cultural_value_body: e.target.value })
                      }
                      placeholder="Giá trị văn hóa..."
                      className="text-xs h-7"
                    />
                  </div>

                  {/* 5. Claim Sources */}
                  <div className="space-y-2.5 pt-2 border-t border-border/60">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-semibold text-foreground flex items-center gap-1">
                        <Quote className="w-3.5 h-3.5 text-primary" />
                        5. Nguồn sử liệu đối chiếu ({activeDetail.claim_sources?.length || 0})
                      </label>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          const current = activeDetail.claim_sources || [];
                          updateActiveDetail({
                            claim_sources: [
                              ...current,
                              {
                                id: `src-${Date.now()}`,
                                section: "Trích dẫn bổ sung",
                                claim_text: "Nội dung ghi chép...",
                                source_title: "Đại Nam Thực Lục Chính Biên",
                                source_locator: "Quyển...",
                                evidence_strength: "verified",
                                citation_quote: "",
                              },
                            ],
                          });
                        }}
                        className="h-6 text-[10px] px-1.5"
                      >
                        + Thêm nguồn
                      </Button>
                    </div>

                    {activeDetail.claim_sources?.map((src, sIdx) => (
                      <div
                        key={src.id || sIdx}
                        className="p-2.5 rounded bg-muted/40 border border-border/50 text-[11px] space-y-2 relative group"
                      >
                        <div className="flex items-center justify-between gap-1">
                          <span className="font-semibold text-foreground/80 text-[11px]">
                            Nguồn #{sIdx + 1}
                          </span>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              const copy = [...(activeDetail.claim_sources || [])];
                              copy.splice(sIdx, 1);
                              updateActiveDetail({ claim_sources: copy });
                            }}
                            className="h-5 text-[10px] px-1.5 text-rose-500 hover:text-rose-600 hover:bg-rose-500/10"
                          >
                            Xóa
                          </Button>
                        </div>

                        <div className="space-y-1">
                          <label className="text-[10px] text-muted-foreground block">Tên tác phẩm / Nguồn sử liệu:</label>
                          <Input
                            value={src.source_title}
                            onChange={(e) => {
                              const copy = [...(activeDetail.claim_sources || [])];
                              copy[sIdx].source_title = e.target.value;
                              updateActiveDetail({ claim_sources: copy });
                            }}
                            placeholder="Ví dụ: Đại Nam Thực Lục Chính Biên"
                            className="h-6 text-[11px]"
                          />
                        </div>

                        <div className="grid grid-cols-2 gap-1.5">
                          <div>
                            <label className="text-[10px] text-muted-foreground block">Vị trí tra cứu:</label>
                            <Input
                              value={src.source_locator || ""}
                              onChange={(e) => {
                                const copy = [...(activeDetail.claim_sources || [])];
                                copy[sIdx].source_locator = e.target.value;
                                updateActiveDetail({ claim_sources: copy });
                              }}
                              placeholder="Quyển, trang..."
                              className="h-6 text-[11px]"
                            />
                          </div>
                          <div>
                            <label className="text-[10px] text-muted-foreground block">Độ tin cậy:</label>
                            <select
                              value={src.evidence_strength}
                              onChange={(e) => {
                                const copy = [...(activeDetail.claim_sources || [])];
                                copy[sIdx].evidence_strength = e.target.value as EvidenceStrength;
                                updateActiveDetail({ claim_sources: copy });
                              }}
                              className="w-full h-6 text-[11px] bg-background border border-border rounded px-1.5 focus:outline-none"
                            >
                              <option value="verified">Chính sử (Xác thực)</option>
                              <option value="probable">Khảo cứu (Khả tín)</option>
                              <option value="traditional">Dân gian (Truyền khẩu)</option>
                            </select>
                          </div>
                        </div>

                        <div className="space-y-1">
                          <label className="text-[10px] text-muted-foreground block">Nội dung luận cứ đối chiếu:</label>
                          <textarea
                            value={src.claim_text}
                            onChange={(e) => {
                              const copy = [...(activeDetail.claim_sources || [])];
                              copy[sIdx].claim_text = e.target.value;
                              updateActiveDetail({ claim_sources: copy });
                            }}
                            rows={2}
                            placeholder="Nội dung luận cứ..."
                            className="w-full text-[11px] bg-background border border-border rounded p-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
                          />
                        </div>

                        <div className="space-y-1">
                          <label className="text-[10px] text-muted-foreground block">Trích dẫn nguyên văn / Dịch nghĩa:</label>
                          <Input
                            value={src.citation_quote || ""}
                            onChange={(e) => {
                              const copy = [...(activeDetail.claim_sources || [])];
                              copy[sIdx].citation_quote = e.target.value;
                              updateActiveDetail({ claim_sources: copy });
                            }}
                            placeholder="Nguyên văn chữ Hán hoặc lời dịch..."
                            className="h-6 text-[11px]"
                          />
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* 6. Reinforcement Questions */}
                  <div className="space-y-2.5 pt-2 border-t border-border/60">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-semibold text-foreground flex items-center gap-1">
                        <HelpCircle className="w-3.5 h-3.5 text-emerald-600" />
                        6. Câu hỏi củng cố ({activeDetail.questions?.length || 0})
                      </label>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          const current = activeDetail.questions || [];
                          updateActiveDetail({
                            questions: [
                              ...current,
                              {
                                id: `q-${Date.now()}`,
                                question_type: "multiple_choice",
                                prompt: "Câu hỏi trắc nghiệm mới...",
                                options: ["Lựa chọn A", "Lựa chọn B", "Lựa chọn C", "Lựa chọn D"],
                                answer_key: "0",
                                explanation: "Giải thích đáp án chuẩn mực theo sử liệu triều Nguyễn.",
                                display_order: current.length + 1,
                              },
                            ],
                          });
                        }}
                        className="h-6 text-[10px] px-1.5"
                      >
                        + Thêm câu hỏi
                      </Button>
                    </div>

                    {activeDetail.questions?.map((q, qIdx) => (
                      <div
                        key={q.id || qIdx}
                        className="p-2.5 rounded bg-muted/40 border border-border/50 text-xs space-y-2"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-[11px] text-primary">
                            Câu hỏi #{qIdx + 1}
                          </span>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              const copy = [...(activeDetail.questions || [])];
                              copy.splice(qIdx, 1);
                              updateActiveDetail({ questions: copy });
                            }}
                            className="h-5 text-[10px] px-1.5 text-rose-500 hover:text-rose-600 hover:bg-rose-500/10"
                          >
                            Xóa
                          </Button>
                        </div>

                        <div className="space-y-1">
                          <label className="text-[10px] text-muted-foreground block">Đề bài câu hỏi:</label>
                          <Input
                            value={q.prompt}
                            onChange={(e) => {
                              const copy = [...(activeDetail.questions || [])];
                              copy[qIdx].prompt = e.target.value;
                              updateActiveDetail({ questions: copy });
                            }}
                            placeholder="Nội dung câu hỏi..."
                            className="h-7 text-xs"
                          />
                        </div>

                        <div className="space-y-1">
                          <label className="text-[10px] text-muted-foreground block">Các lựa chọn trả lời:</label>
                          {q.options.map((opt, oIdx) => (
                            <div key={oIdx} className="flex items-center gap-1.5">
                              <span className="text-[10px] font-bold text-muted-foreground w-4 shrink-0">
                                {String.fromCharCode(65 + oIdx)}.
                              </span>
                              <Input
                                value={opt}
                                onChange={(e) => {
                                  const copy = [...(activeDetail.questions || [])];
                                  const newOpts = [...copy[qIdx].options];
                                  newOpts[oIdx] = e.target.value;
                                  copy[qIdx].options = newOpts;
                                  updateActiveDetail({ questions: copy });
                                }}
                                placeholder={`Lựa chọn ${String.fromCharCode(65 + oIdx)}`}
                                className="h-6 text-[11px]"
                              />
                            </div>
                          ))}
                        </div>

                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <label className="text-[10px] text-muted-foreground block">Đáp án đúng:</label>
                            <select
                              value={q.answer_key}
                              onChange={(e) => {
                                const copy = [...(activeDetail.questions || [])];
                                copy[qIdx].answer_key = e.target.value;
                                updateActiveDetail({ questions: copy });
                              }}
                              className="w-full h-6 text-[11px] bg-background border border-border rounded px-1.5 focus:outline-none"
                            >
                              {q.options.map((_, oIdx) => (
                                <option key={oIdx} value={String(oIdx)}>
                                  Đáp án {String.fromCharCode(65 + oIdx)}
                                </option>
                              ))}
                            </select>
                          </div>
                        </div>

                        <div className="space-y-1">
                          <label className="text-[10px] text-muted-foreground block">Giải thích đáp án:</label>
                          <textarea
                            value={q.explanation || ""}
                            onChange={(e) => {
                              const copy = [...(activeDetail.questions || [])];
                              copy[qIdx].explanation = e.target.value;
                              updateActiveDetail({ questions: copy });
                            }}
                            rows={2}
                            placeholder="Giải thích vì sao đáp án này đúng..."
                            className="w-full text-[11px] bg-background border border-border rounded p-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null
            ) : (
              <div className="py-20 text-center text-xs text-muted-foreground space-y-3">
                <Sparkles className="w-8 h-8 mx-auto text-muted-foreground/40" />
                <p>Chưa chọn điểm quan sát nào.</p>
                <p className="text-[11px]">
                  Bấm &quot;Thêm điểm ghim&quot; rồi nhấp chuột vào hình ảnh bên trái để tạo điểm quan sát.
                </p>
              </div>
            )}
          </div>
        </aside>
      </div>

      {/* Preview Dialog */}
      <ArtDetailModal
        isOpen={isPreviewOpen}
        onClose={() => setIsPreviewOpen(false)}
        artDetail={activeDetail}
        variant="dialog"
      />
    </div>
  );
}
