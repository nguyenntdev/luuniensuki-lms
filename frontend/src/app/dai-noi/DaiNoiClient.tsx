"use client";

import React, { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  Compass,
  FileText,
  Info,
  Layers,
  List,
  MapPin,
  Maximize2,
  Minimize2,
  RotateCcw,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { AerialMapViewer } from "@/components/imperial/map/AerialMapViewer";
import { MapZoneFilter } from "@/components/imperial/map/MapZoneFilter";
import { MonumentDrawer } from "@/components/imperial/map/MonumentDrawer";
import { MapListFallback } from "@/components/imperial/map/MapListFallback";
import ImperialAiAssistant from "@/components/imperial/ai/ImperialAiAssistant";
import { HeritageDetectiveWidget } from "@/components/imperial/detective/HeritageDetectiveWidget";
import { HeritageDetectiveModal } from "@/components/imperial/detective/HeritageDetectiveModal";
import { ImperialCinematicHero } from "@/components/imperial/hero/ImperialCinematicHero";
import { MonumentVisualCarousel } from "@/components/imperial/home/MonumentVisualCarousel";
import { FALLBACK_CLUES } from "@/lib/imperial/v51-api";
import {
  fetchActiveMap,
  fetchSites,
  fetchZones,
} from "@/lib/imperial/map-api";
import type {
  ActiveMapResponse,
  ImperialMapAnnotation,
  ImperialSite,
  ImperialZone,
} from "@/lib/imperial/map-types";
import { cn } from "@/lib/utils";

export interface DaiNoiClientProps {
  initialActiveMap?: ActiveMapResponse | null;
  initialZones?: ImperialZone[] | null;
  initialSites?: ImperialSite[] | null;
  fullscreen?: boolean;
}

export function DaiNoiClient({
  initialActiveMap,
  initialZones,
  initialSites,
  fullscreen = false,
}: DaiNoiClientProps) {
  const [mapData, setMapData] = useState<ActiveMapResponse | null>(
    initialActiveMap || null,
  );
  const [zones, setZones] = useState<ImperialZone[]>(initialZones || []);
  const [sites, setSites] = useState<ImperialSite[]>(initialSites || []);
  const [loading, setLoading] = useState(!initialActiveMap);

  // Interaction State
  const [selectedZoneSlug, setSelectedZoneSlug] = useState<string | null>(null);
  const [selectedAnnotation, setSelectedAnnotation] =
    useState<ImperialMapAnnotation | null>(null);
  const [focusAnnotationId, setFocusAnnotationId] = useState<string | null>(
    null,
  );
  const [viewMode, setViewMode] = useState<"map" | "list">("map");
  const [isDetectiveOpen, setIsDetectiveOpen] = useState(false);

  // Fetch initial data if not passed from SSR
  useEffect(() => {
    if (initialActiveMap && initialZones && initialSites) {
      return;
    }

    let isMounted = true;
    async function loadData() {
      try {
        setLoading(true);
        const [activeMap, fetchedZones, fetchedSites] = await Promise.all([
          fetchActiveMap(),
          fetchZones(),
          fetchSites(),
        ]);

        if (isMounted) {
          setMapData(activeMap);
          setZones(fetchedZones);
          setSites(fetchedSites);
        }
      } catch (err) {
        console.error("Failed to load Imperial Map data:", err);
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    loadData();
    return () => {
      isMounted = false;
    };
  }, [initialActiveMap, initialZones, initialSites]);

  // Compute counts per zone
  const countsByZone = useMemo(() => {
    const counts: Record<string, number> = {};
    if (!mapData) return counts;

    mapData.annotations.forEach((anno) => {
      const z = anno.site?.zone_slug;
      if (z) {
        counts[z] = (counts[z] || 0) + 1;
      }
    });
    return counts;
  }, [mapData]);

  // Find site detail matching selected annotation
  const selectedSiteDetail = useMemo(() => {
    if (!selectedAnnotation) return null;
    const slug = selectedAnnotation.site?.slug;
    return sites.find((s) => s.slug === slug) || null;
  }, [selectedAnnotation, sites]);

  /**
   * Handle locating a site selected from the List view on the Map
   */
  const handleSelectSiteFromList = (site: ImperialSite) => {
    setViewMode("map");
    const matchingAnno = mapData?.annotations.find(
      (a) => a.site?.slug === site.slug || a.site_id === site.id,
    );

    if (matchingAnno) {
      setSelectedAnnotation(matchingAnno);
      setFocusAnnotationId(matchingAnno.id);
    }
  };

  /**
   * Handle selecting a monument from the Visual Carousel strip
   */
  const handleSelectMonumentFromVisualCarousel = (slug: string) => {
    setViewMode("map");
    const matchingAnno = mapData?.annotations.find(
      (a) => a.site?.slug === slug || a.site_id === slug,
    );

    if (matchingAnno) {
      setSelectedAnnotation(matchingAnno);
      setFocusAnnotationId(matchingAnno.id);
    }

    const mapWorkspace = document.getElementById("aerial-map-workspace");
    if (mapWorkspace) {
      mapWorkspace.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  if (loading || !mapData) {
    return (
      <div className="mx-auto max-w-[94rem] p-4 lg:p-8 space-y-6">
        <div className="flex flex-col gap-2">
          <Skeleton className="h-10 w-72 rounded-xl" />
          <Skeleton className="h-4 w-96 rounded-lg" />
        </div>
        <Skeleton className="h-[600px] w-full rounded-3xl" />
      </div>
    );
  }

  // Fullscreen Layout Mode (/dai-noi/map)
  if (fullscreen) {
    return (
      <div className="relative w-full h-[calc(100dvh-3.5rem)] overflow-hidden bg-stone-950">
        {/* Floating Top Bar in Fullscreen */}
        <div className="absolute top-4 inset-x-4 z-30 flex items-center justify-between gap-3 pointer-events-none">
          <div className="pointer-events-auto shadow-xl rounded-2xl">
            <MapZoneFilter
              zones={zones}
              selectedZoneSlug={selectedZoneSlug}
              onSelectZone={setSelectedZoneSlug}
              countsByZone={countsByZone}
              totalCount={mapData.annotations.length}
            />
          </div>

          <div className="flex items-center gap-2 pointer-events-auto">
            <Button
              asChild
              variant="secondary"
              size="sm"
              className="rounded-xl shadow-xl bg-card/90 backdrop-blur-xl border border-border/80 text-xs font-semibold"
            >
              <Link href="/dai-noi">
                <Minimize2 className="w-4 h-4 mr-1.5" />
                Thoát toàn màn hình
              </Link>
            </Button>
          </div>
        </div>

        {/* Aerial Map Canvas */}
        <AerialMapViewer
          mapImage={{
            url: mapData.map.image.url,
            width: mapData.map.image.width,
            height: mapData.map.image.height,
            credit: mapData.map.credit,
            title_vi: mapData.map.title_vi,
          }}
          annotations={mapData.annotations}
          selectedAnnotationId={selectedAnnotation?.id}
          activeZoneSlug={selectedZoneSlug}
          focusAnnotationId={focusAnnotationId}
          onSelectAnnotation={setSelectedAnnotation}
          className="w-full h-full"
        />

        {/* Monument Inspector Drawer */}
        <MonumentDrawer
          annotation={selectedAnnotation}
          siteDetail={selectedSiteDetail}
          isOpen={selectedAnnotation !== null}
          onClose={() => setSelectedAnnotation(null)}
        />
      </div>
    );
  }

  // Standard Page Layout Mode (/dai-noi)
  return (
    <div className="mx-auto max-w-[94rem] px-4 py-6 lg:px-8 lg:py-8 space-y-8">
      {/* 1. Màn chào thị giác điện ảnh Cố đô Huế (Spec Patch V2.4) */}
      <ImperialCinematicHero
        onExploreMap={() => {
          const mapEl = document.getElementById("aerial-map-workspace");
          mapEl?.scrollIntoView({ behavior: "smooth", block: "start" });
        }}
      />

      {/* 2. Dải thẻ ảnh di tích lướt ngang (Spec Patch V2.4) */}
      <MonumentVisualCarousel
        onSelectMonument={handleSelectMonumentFromVisualCarousel}
        selectedSlug={selectedAnnotation?.site?.slug}
      />

      {/* Spatial Zone Header & Map Controls */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-2 border-b border-border/60">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-500/10 text-amber-500 border border-amber-500/20">
              <Sparkles className="w-3 h-3" />
              Bản đồ không ảnh di sản số
            </span>
            <span className="text-xs text-muted-foreground">• Hoàng Thành & Tử Cấm Thành</span>
          </div>
          <h1 className="text-2xl md:text-4xl font-serif font-bold tracking-tight text-foreground">
            Bản đồ không ảnh Đại Nội Huế
          </h1>
          <p className="text-sm md:text-base text-muted-foreground max-w-3xl leading-relaxed">
            Khám phá quy hoạch kiến trúc Hoàng Thành và Tử Cấm Thành triều Nguyễn theo không gian trực giao, tra cứu chứng tích sử liệu và thực hiện các nhiệm vụ nghiên cứu lịch sử.
          </p>
        </div>

        {/* Mode Switcher Buttons */}
        <div className="flex items-center gap-2 shrink-0">
          <div className="p-1 rounded-xl bg-secondary/80 border border-border/60 flex items-center gap-1 shadow-sm">
            <Button
              type="button"
              variant={viewMode === "map" ? "default" : "ghost"}
              size="xs"
              onClick={() => setViewMode("map")}
              className="rounded-lg text-xs font-semibold"
            >
              <Compass className="w-3.5 h-3.5 mr-1" />
              Bản đồ
            </Button>
            <Button
              type="button"
              variant={viewMode === "list" ? "default" : "ghost"}
              size="xs"
              onClick={() => setViewMode("list")}
              className="rounded-lg text-xs font-semibold"
            >
              <List className="w-3.5 h-3.5 mr-1" />
              Danh mục ({sites.length})
            </Button>
          </div>

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setIsDetectiveOpen(true)}
            className="rounded-xl border-border/80 text-xs font-semibold gap-1.5"
            title="Thám tử di sản Đại Nội"
          >
            <Compass className="w-3.5 h-3.5 text-primary" />
            <span>Thám tử di sản</span>
          </Button>

          <Button
            asChild
            variant="outline"
            size="sm"
            className="rounded-xl border-border/80 text-xs font-semibold hidden sm:inline-flex"
            title="Chế độ toàn màn hình"
          >
            <Link href="/dai-noi/map">
              <Maximize2 className="w-3.5 h-3.5 mr-1.5" />
              Toàn màn hình
            </Link>
          </Button>
        </div>
      </div>

      {/* Spatial Zone Filter Bar */}
      <div className="flex items-center justify-between gap-4">
        <MapZoneFilter
          zones={zones}
          selectedZoneSlug={selectedZoneSlug}
          onSelectZone={setSelectedZoneSlug}
          countsByZone={countsByZone}
          totalCount={mapData.annotations.length}
        />

        {selectedZoneSlug && (
          <Button
            variant="ghost"
            size="xs"
            onClick={() => setSelectedZoneSlug(null)}
            className="text-xs text-muted-foreground hover:text-foreground shrink-0 hidden md:inline-flex"
          >
            <RotateCcw className="w-3 h-3 mr-1" />
            Bỏ lọc phân khu
          </Button>
        )}
      </div>

      {/* Active Heritage Detective Riddle Challenge Banner */}
      <HeritageDetectiveWidget
        clue={FALLBACK_CLUES[0]}
        currentSiteSlug={selectedSiteDetail?.slug}
        currentSiteId={selectedSiteDetail?.id}
        onOpenFullModal={() => setIsDetectiveOpen(true)}
      />

      {/* Main Viewport Container */}
      {viewMode === "map" ? (
        <div id="aerial-map-workspace" className="relative w-full h-[620px] md:h-[760px] lg:h-[820px] rounded-3xl border border-border/80 shadow-2xl overflow-hidden bg-stone-950 scroll-mt-20">
          <AerialMapViewer
            mapImage={{
              url: mapData.map.image.url,
              width: mapData.map.image.width,
              height: mapData.map.image.height,
              credit: mapData.map.credit,
              title_vi: mapData.map.title_vi,
            }}
            annotations={mapData.annotations}
            selectedAnnotationId={selectedAnnotation?.id}
            activeZoneSlug={selectedZoneSlug}
            focusAnnotationId={focusAnnotationId}
            onSelectAnnotation={setSelectedAnnotation}
            className="w-full h-full"
          />

          {/* Quick Info Chip */}
          <div className="absolute top-4 left-4 z-20 pointer-events-none hidden sm:flex items-center gap-2 p-2 px-3 rounded-xl bg-card/80 backdrop-blur-md border border-border/70 text-xs text-muted-foreground shadow-lg">
            <Info className="w-3.5 h-3.5 text-primary" />
            <span>Kéo chuột để di chuyển • Cuộn để phóng to • Nhấp vào điểm ghim để xem tư liệu</span>
          </div>
        </div>
      ) : (
        /* Accessible List & Card View Fallback */
        <MapListFallback
          sites={sites}
          zones={zones}
          onSelectSite={handleSelectSiteFromList}
        />
      )}

      {/* Supplementary List Section when in Map mode */}
      {viewMode === "map" && (
        <div className="pt-6 border-t border-border/60">
          <MapListFallback
            sites={sites}
            zones={zones}
            onSelectSite={handleSelectSiteFromList}
          />
        </div>
      )}

      {/* Monument Detail Drawer */}
      <MonumentDrawer
        annotation={selectedAnnotation}
        siteDetail={selectedSiteDetail}
        isOpen={selectedAnnotation !== null}
        onClose={() => setSelectedAnnotation(null)}
      />

      {/* Scope-Locked Cultural AI Tutor Assistant Widget */}
      <ImperialAiAssistant
        contextMonumentSlug={selectedSiteDetail?.slug}
        contextMonumentName={selectedSiteDetail?.name_vi}
      />

      {/* Heritage Detective Clue Riddle Modal */}
      <HeritageDetectiveModal
        open={isDetectiveOpen}
        onOpenChange={setIsDetectiveOpen}
        currentSiteSlug={selectedSiteDetail?.slug}
        currentSiteId={selectedSiteDetail?.id}
      />
    </div>
  );
}
