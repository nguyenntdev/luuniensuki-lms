"use client";

import React, { useEffect, useRef, useState, useMemo, useCallback } from "react";
import Link from "next/link";
import Image from "next/image";
import {
  Maximize2,
  Minimize2,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Layers,
  MapPin,
  ExternalLink,
  Info,
  Calendar,
  Compass,
  Sparkles,
  AlertTriangle,
} from "lucide-react";
import { setOptions, importLibrary } from "@googlemaps/js-api-loader";
import { cn } from "@/lib/utils";
import {
  DAI_NOI_CENTER,
  IMPERIAL_MONUMENTS_GEO,
  type ImperialMonumentGeo,
} from "@/lib/imperial/monuments-geo";

export type GoogleMapType = "HYBRID" | "ROADMAP" | "TERRAIN";

export interface GoogleMapsImperialProps {
  apiKey?: string;
  className?: string;
  initialCenter?: { lat: number; lng: number };
  initialZoom?: number;
  initialMapType?: GoogleMapType;
  monuments?: ImperialMonumentGeo[];
  selectedMonumentSlug?: string | null;
  onSelectMonument?: (monument: ImperialMonumentGeo | null) => void;
  showZoneFilter?: boolean;
  showMapTypeSelector?: boolean;
  showZoomControls?: boolean;
  showFullscreenToggle?: boolean;
  interactiveFallbackOnly?: boolean;
}

// Imperial Hue aesthetic palettes: gold / crimson / jade
const ZONE_METADATA: Record<
  string,
  { label: string; stroke: string; fill: string; badge: string; glow: string }
> = {
  "central-ceremonial-axis": {
    label: "Trục trung tâm",
    stroke: "#DC2626", // Imperial Crimson
    fill: "#FEF2F2",
    badge: "bg-red-500/15 text-red-700 dark:text-red-300 border-red-500/30",
    glow: "#EF4444",
  },
  "ancestral-worship-space": {
    label: "Không gian thờ tự",
    stroke: "#D97706", // Imperial Gold / Amber
    fill: "#FFFBEB",
    badge: "bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/30",
    glow: "#F59E0B",
  },
  "purple-forbidden-city": {
    label: "Tử Cấm Thành",
    stroke: "#9333EA", // Royal Purple
    fill: "#FAF5FF",
    badge: "bg-purple-500/15 text-purple-700 dark:text-purple-300 border-purple-500/30",
    glow: "#A855F7",
  },
  "royal-living-gardens": {
    label: "Không gian sinh hoạt",
    stroke: "#059669", // Jade Emerald
    fill: "#ECFDF5",
    badge: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-500/30",
    glow: "#10B981",
  },
};

/**
 * Creates SVG Data URI for custom Imperial Gold / Crimson Pins
 */
function createImperialPinSvg(zoneSlug: string, isSelected: boolean): string {
  const meta = ZONE_METADATA[zoneSlug] || ZONE_METADATA["central-ceremonial-axis"];
  const pinColor = isSelected ? "#F59E0B" : meta.stroke; // Gold if selected, else zone crimson/gold/purple/emerald
  const strokeColor = isSelected ? "#FFFFFF" : "#FDE68A"; // Pale gold border
  const glowCircle = isSelected
    ? `<circle cx="20" cy="20" r="19" fill="#F59E0B" fill-opacity="0.35" stroke="#FBBF24" stroke-width="1.5"/>`
    : "";

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="40" height="48" viewBox="0 0 40 48">
    ${glowCircle}
    <defs>
      <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="2" stdDeviation="2.5" flood-color="#000" flood-opacity="0.45"/>
      </filter>
      <linearGradient id="pinGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="${pinColor}"/>
        <stop offset="100%" stop-color="#7F1D1D"/>
      </linearGradient>
    </defs>
    <!-- Pin Body -->
    <path d="M20 4 C11.16 4 4 11.16 4 20 C4 29.5 17.5 43 20 45 C22.5 43 36 29.5 36 20 C36 11.16 28.84 4 20 4 Z"
          fill="url(#pinGrad)" stroke="${strokeColor}" stroke-width="2" filter="url(#shadow)"/>
    <!-- Central Imperial Lotus / Crown Gem -->
    <circle cx="20" cy="18" r="7.5" fill="#FEF3C7" stroke="#B45309" stroke-width="1.5"/>
    <circle cx="20" cy="18" r="3.5" fill="${pinColor}"/>
  </svg>`;

  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

/**
 * Build rich HTML content for Google Maps InfoWindow
 */
function buildInfoWindowHtml(monument: ImperialMonumentGeo): string {
  const meta = ZONE_METADATA[monument.zone_slug] || { label: monument.zone_name_vi };
  const hanNomSpan = monument.name_han_nom
    ? `<span style="font-family:serif;font-size:12px;color:#d97706;margin-left:6px;font-weight:normal;">(${monument.name_han_nom})</span>`
    : "";

  return `
    <div style="font-family:ui-sans-serif,system-ui,sans-serif;max-width:280px;padding:4px 2px;color:#18181b;line-height:1.45;">
      <div style="position:relative;width:100%;height:120px;border-radius:8px;overflow:hidden;background-color:#1c1917;margin-bottom:8px;">
        <img src="${monument.photo}" alt="${monument.name_vi}"
             style="width:100%;height:100%;object-fit:cover;display:block;"
             onerror="this.style.display='none';" />
        <span style="position:absolute;top:6px;left:6px;background:rgba(0,0,0,0.72);color:#fef3c7;font-size:10px;padding:2px 6px;border-radius:4px;font-weight:600;letter-spacing:0.5px;">
          ${monument.era}
        </span>
      </div>
      <div style="font-size:15px;font-weight:700;color:#09090b;margin-bottom:2px;display:flex;align-items:center;">
        <span>${monument.name_vi}</span>${hanNomSpan}
      </div>
      <div style="font-size:11px;color:#71717a;margin-bottom:6px;font-weight:500;">
        Phân khu: <strong style="color:#b45309;">${meta.label}</strong> · Khởi dựng: <strong>${monument.construction_year}</strong>
      </div>
      <p style="font-size:12px;color:#3f3f46;margin:0 0 10px 0;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">
        ${monument.summary}
      </p>
      <div style="display:flex;justify-content:flex-end;">
        <a href="/dai-noi/cong-trinh/${monument.slug}"
           style="display:inline-flex;align-items:center;gap:4px;font-size:11px;font-weight:600;color:#b45309;text-decoration:none;padding:5px 10px;border-radius:6px;background:#fef3c7;border:1px solid #fde68a;">
          <span>Hồ sơ chi tiết</span> &rarr;
        </a>
      </div>
    </div>
  `;
}

export function GoogleMapsImperial({
  apiKey,
  className,
  initialCenter = DAI_NOI_CENTER,
  initialZoom = DAI_NOI_CENTER.zoom,
  initialMapType = "HYBRID",
  monuments = IMPERIAL_MONUMENTS_GEO,
  selectedMonumentSlug = null,
  onSelectMonument,
  showZoneFilter = true,
  showMapTypeSelector = true,
  showZoomControls = true,
  showFullscreenToggle = true,
  interactiveFallbackOnly = false,
}: GoogleMapsImperialProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<google.maps.Map | null>(null);
  const infoWindowRef = useRef<google.maps.InfoWindow | null>(null);
  const markersRef = useRef<Map<string, google.maps.Marker>>(new Map());

  // Interactive UI state
  const [activeZone, setActiveZone] = useState<string | null>(null);
  const [mapType, setMapType] = useState<GoogleMapType>(initialMapType);
  const [zoomLevel, setZoomLevel] = useState<number>(initialZoom);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [selectedMonument, setSelectedMonument] = useState<ImperialMonumentGeo | null>(() => {
    if (selectedMonumentSlug) {
      return monuments.find((m) => m.slug === selectedMonumentSlug) || null;
    }
    return null;
  });

  // Loading & fallback state
  const [isGoogleMapsReady, setIsGoogleMapsReady] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  // Synchronize internal selectedMonument when prop changes
  useEffect(() => {
    if (selectedMonumentSlug !== undefined) {
      const match = monuments.find((m) => m.slug === selectedMonumentSlug) || null;
      setSelectedMonument(match);
    }
  }, [selectedMonumentSlug, monuments]);

  // Determine active API key
  const effectiveApiKey = apiKey || process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;

  // Filtered monuments based on selected zone
  const filteredMonuments = useMemo(() => {
    if (!activeZone) return monuments;
    return monuments.filter((m) => m.zone_slug === activeZone);
  }, [monuments, activeZone]);

  // Zone counts
  const zoneCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const m of monuments) {
      counts[m.zone_slug] = (counts[m.zone_slug] || 0) + 1;
    }
    return counts;
  }, [monuments]);

  /**
   * Initialize Google Maps API via @googlemaps/js-api-loader
   */
  useEffect(() => {
    // If no key provided, or interactive fallback requested, skip Google Maps load safely
    if (interactiveFallbackOnly || !effectiveApiKey || typeof window === "undefined") {
      setIsGoogleMapsReady(false);
      return;
    }

    let isSubscribed = true;

    async function initGoogleMaps() {
      try {
        setOptions({
          key: effectiveApiKey,
          v: "weekly",
        });

        const { Map, InfoWindow } = (await importLibrary("maps")) as google.maps.MapsLibrary;
        const { Marker } = (await importLibrary("marker")) as google.maps.MarkerLibrary;

        if (!isSubscribed || !containerRef.current) return;

        const map = new Map(containerRef.current, {
          center: initialCenter,
          zoom: initialZoom,
          mapTypeId: mapType.toLowerCase(),
          disableDefaultUI: true, // Custom imperial controls
          zoomControl: false,
          gestureHandling: "greedy",
        });

        const infoWindow = new InfoWindow({
          disableAutoPan: false,
        });

        mapInstanceRef.current = map;
        infoWindowRef.current = infoWindow;

        // Sync zoom state
        map.addListener("zoom_changed", () => {
          const currentZoom = map.getZoom();
          if (typeof currentZoom === "number") {
            setZoomLevel(currentZoom);
          }
        });

        // Close InfoWindow on map click
        map.addListener("click", () => {
          infoWindow.close();
          setSelectedMonument(null);
          onSelectMonument?.(null);
        });

        setIsGoogleMapsReady(true);
        setLoadError(null);
      } catch (err: unknown) {
        if (!isSubscribed) return;
        const msg = err instanceof Error ? err.message : "Failed to load Google Maps";
        console.warn("[GoogleMapsImperial] Falling back to interactive canvas/SVG view:", msg);
        setLoadError(msg);
        setIsGoogleMapsReady(false);
      }
    }

    initGoogleMaps();

    const currentMarkers = markersRef.current;
    return () => {
      isSubscribed = false;
      // Clear markers
      currentMarkers.forEach((marker) => marker.setMap(null));
      currentMarkers.clear();
      mapInstanceRef.current = null;
      infoWindowRef.current = null;
    };
  }, [effectiveApiKey, interactiveFallbackOnly, initialCenter, initialZoom, mapType, onSelectMonument]);

  /**
   * Update Google Maps markers when ready and monuments/filtering/selection change
   */
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!isGoogleMapsReady || !map || typeof window === "undefined" || !window.google?.maps) {
      return;
    }

    // Clear old markers that are no longer in filtered list
    const activeSlugs = new Set(filteredMonuments.map((m) => m.slug));
    markersRef.current.forEach((marker, slug) => {
      if (!activeSlugs.has(slug)) {
        marker.setMap(null);
        markersRef.current.delete(slug);
      }
    });

    // Add or update markers
    filteredMonuments.forEach((monument) => {
      const isSelected = selectedMonument?.slug === monument.slug;
      const pinIconUrl = createImperialPinSvg(monument.zone_slug, isSelected);

      let marker = markersRef.current.get(monument.slug);
      if (!marker) {
        marker = new google.maps.Marker({
          position: { lat: monument.lat, lng: monument.lng },
          map,
          title: monument.name_vi,
          icon: {
            url: pinIconUrl,
            scaledSize: new google.maps.Size(40, 48),
            anchor: new google.maps.Point(20, 45),
          },
          animation: isSelected ? google.maps.Animation.BOUNCE : undefined,
          zIndex: isSelected ? 99 : 10,
        });

        marker.addListener("click", () => {
          setSelectedMonument(monument);
          onSelectMonument?.(monument);

          if (infoWindowRef.current && marker) {
            infoWindowRef.current.setContent(buildInfoWindowHtml(monument));
            infoWindowRef.current.open({
              anchor: marker,
              map,
              shouldFocus: false,
            });
          }
        });

        markersRef.current.set(monument.slug, marker);
      } else {
        marker.setIcon({
          url: pinIconUrl,
          scaledSize: new google.maps.Size(40, 48),
          anchor: new google.maps.Point(20, 45),
        });
        marker.setZIndex(isSelected ? 99 : 10);
      }

      // If selected, ensure InfoWindow is open
      if (isSelected && infoWindowRef.current) {
        infoWindowRef.current.setContent(buildInfoWindowHtml(monument));
        infoWindowRef.current.open({
          anchor: marker,
          map,
          shouldFocus: false,
        });
      }
    });
  }, [isGoogleMapsReady, filteredMonuments, selectedMonument, onSelectMonument]);

  /**
   * Handle Map Type changes
   */
  const handleMapTypeChange = useCallback((newType: GoogleMapType) => {
    setMapType(newType);
    if (mapInstanceRef.current && window.google?.maps) {
      const gType =
        newType === "HYBRID"
          ? google.maps.MapTypeId.HYBRID
          : newType === "ROADMAP"
          ? google.maps.MapTypeId.ROADMAP
          : google.maps.MapTypeId.TERRAIN;
      mapInstanceRef.current.setMapTypeId(gType);
    }
  }, []);

  /**
   * Handle Zoom controls
   */
  const handleZoomIn = useCallback(() => {
    if (mapInstanceRef.current) {
      const z = (mapInstanceRef.current.getZoom() || 16) + 1;
      mapInstanceRef.current.setZoom(z);
      setZoomLevel(z);
    } else {
      setZoomLevel((prev) => Math.min(prev + 1, 20));
    }
  }, []);

  const handleZoomOut = useCallback(() => {
    if (mapInstanceRef.current) {
      const z = (mapInstanceRef.current.getZoom() || 16) - 1;
      mapInstanceRef.current.setZoom(z);
      setZoomLevel(z);
    } else {
      setZoomLevel((prev) => Math.max(prev - 1, 14));
    }
  }, []);

  const handleResetCenter = useCallback(() => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.setCenter(DAI_NOI_CENTER);
      mapInstanceRef.current.setZoom(DAI_NOI_CENTER.zoom);
    }
    setZoomLevel(DAI_NOI_CENTER.zoom);
  }, []);

  /**
   * Fallback coordinate projection:
   * Maps GPS (lat: 16.4660 - 16.4755, lng: 107.5740 - 107.5815)
   * to container percentage coordinates (0% - 100%)
   */
  const projectToFallbackPercent = useCallback((lat: number, lng: number) => {
    const minLat = 16.4655;
    const maxLat = 16.4760;
    const minLng = 16.4735;
    const maxLng = 16.4815;

    // Invert lat (north is top / 0%)
    const y = ((maxLat - lat) / (maxLat - minLat)) * 100;
    const x = ((lng - minLng) / (maxLng - minLng)) * 100;

    return {
      x: Math.max(4, Math.min(96, x)),
      y: Math.max(4, Math.min(96, y)),
    };
  }, []);

  const handleSelectMonumentItem = useCallback(
    (monument: ImperialMonumentGeo) => {
      setSelectedMonument(monument);
      onSelectMonument?.(monument);

      if (mapInstanceRef.current) {
        mapInstanceRef.current.panTo({ lat: monument.lat, lng: monument.lng });
        const marker = markersRef.current.get(monument.slug);
        if (marker && infoWindowRef.current) {
          infoWindowRef.current.setContent(buildInfoWindowHtml(monument));
          infoWindowRef.current.open({
            anchor: marker,
            map: mapInstanceRef.current,
            shouldFocus: false,
          });
        }
      }
    },
    [onSelectMonument]
  );

  return (
    <div
      data-testid="google-maps-imperial-container"
      className={cn(
        "relative w-full overflow-hidden rounded-2xl border border-border bg-stone-950 font-sans shadow-2xl transition-all",
        isFullscreen ? "fixed inset-0 z-50 h-screen w-screen rounded-none" : "h-[620px] md:h-[720px]",
        className
      )}
    >
      {/* 1. TOP BAR: Zone Filters & Title Header */}
      <div className="absolute left-3 right-3 top-3 z-20 flex flex-wrap items-center justify-between gap-2 pointer-events-none">
        {/* Title badge */}
        <div className="pointer-events-auto flex items-center gap-2 rounded-xl bg-stone-900/90 px-3 py-1.5 backdrop-blur-md border border-amber-500/30 shadow-lg text-amber-200">
          <Compass className="h-4 w-4 text-amber-400" />
          <span className="text-xs font-bold tracking-wide uppercase">
            Đại Nội Huế — Tọa độ Google Maps
          </span>
          {!isGoogleMapsReady && (
            <span
              data-testid="interactive-fallback-badge"
              className="ml-1 rounded bg-amber-500/20 px-1.5 py-0.5 text-[10px] font-semibold text-amber-300 border border-amber-500/40"
            >
              Mô phỏng vệ tinh
            </span>
          )}
        </div>

        {/* Zone Filters */}
        {showZoneFilter && (
          <div
            data-testid="zone-filters"
            className="pointer-events-auto flex items-center gap-1.5 overflow-x-auto rounded-xl bg-stone-900/90 p-1 backdrop-blur-md border border-stone-800 shadow-lg"
          >
            <button
              type="button"
              onClick={() => setActiveZone(null)}
              className={cn(
                "rounded-lg px-2.5 py-1 text-xs font-medium transition-colors",
                activeZone === null
                  ? "bg-amber-500 text-stone-950 font-semibold shadow"
                  : "text-stone-300 hover:bg-stone-800"
              )}
            >
              Tất cả ({monuments.length})
            </button>
            {Object.entries(ZONE_METADATA).map(([slug, meta]) => {
              const count = zoneCounts[slug] || 0;
              const isSelected = activeZone === slug;
              return (
                <button
                  key={slug}
                  type="button"
                  onClick={() => setActiveZone(slug)}
                  className={cn(
                    "flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-medium transition-colors",
                    isSelected
                      ? "bg-amber-500 text-stone-950 font-semibold shadow"
                      : "text-stone-300 hover:bg-stone-800"
                  )}
                >
                  <span
                    className="h-2 w-2 rounded-full"
                    style={{ backgroundColor: meta.stroke }}
                  />
                  <span>{meta.label}</span>
                  <span className="text-[10px] opacity-75">({count})</span>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* 2. REAL GOOGLE MAP CONTAINER */}
      <div
        ref={containerRef}
        data-testid="google-maps-canvas"
        className={cn(
          "h-full w-full",
          !isGoogleMapsReady && "hidden" // hidden when fallback is active
        )}
      />

      {/* 3. GRACEFUL INTERACTIVE FALLBACK (SVG / Canvas Satellite Representation) */}
      {!isGoogleMapsReady && (
        <div
          data-testid="interactive-fallback-view"
          className="relative h-full w-full select-none overflow-hidden bg-gradient-to-b from-[#111827] via-[#064e3b]/30 to-[#1f2937]"
        >
          {/* Stylized Satellite / Grid Background */}
          <div
            className="absolute inset-0 opacity-40"
            style={{
              backgroundImage: `
                radial-gradient(circle at 50% 50%, rgba(217, 119, 6, 0.15) 0%, transparent 60%),
                linear-gradient(to right, rgba(255,255,255,0.05) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(255,255,255,0.05) 1px, transparent 1px)
              `,
              backgroundSize: "100% 100%, 32px 32px, 32px 32px",
            }}
          />

          {/* Citadel Outline representation (Hoàng Thành & Tử Cấm Thành) */}
          <svg
            className="pointer-events-none absolute inset-0 h-full w-full opacity-60"
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
          >
            {/* Outer Moat / Kim Long canal */}
            <rect
              x="15"
              y="10"
              width="70"
              height="80"
              rx="2"
              fill="none"
              stroke="#0284c7"
              strokeWidth="1.2"
              strokeDasharray="2,2"
            />
            {/* Hoang Thanh Wall */}
            <rect
              x="22"
              y="16"
              width="56"
              height="68"
              rx="1.5"
              fill="rgba(217, 119, 6, 0.05)"
              stroke="#d97706"
              strokeWidth="1"
            />
            {/* Tu Cam Thanh Wall */}
            <rect
              x="32"
              y="25"
              width="36"
              height="35"
              rx="1"
              fill="rgba(147, 51, 234, 0.08)"
              stroke="#a855f7"
              strokeWidth="0.8"
            />
            {/* Central Axis Line */}
            <line
              x1="50"
              y1="16"
              x2="50"
              y2="84"
              stroke="#ef4444"
              strokeWidth="0.5"
              strokeDasharray="1,1"
            />
          </svg>

          {/* Satellite Map Label */}
          <div className="absolute bottom-4 left-4 z-10 flex items-center gap-2 rounded-lg bg-stone-900/80 px-2.5 py-1 text-[11px] text-stone-400 backdrop-blur-sm border border-stone-800">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Kinh thành Huế: 16.4697° N, 107.5779° E (Đại Nội)</span>
          </div>

          {/* Interactive Monument Markers on Fallback Plane */}
          {filteredMonuments.map((monument) => {
            const pos = projectToFallbackPercent(monument.lat, monument.lng);
            const isSelected = selectedMonument?.slug === monument.slug;
            const meta = ZONE_METADATA[monument.zone_slug] || ZONE_METADATA["central-ceremonial-axis"];

            return (
              <div
                key={monument.slug}
                data-testid={`marker-pin-${monument.slug}`}
                className="absolute z-20 -translate-x-1/2 -translate-y-full transition-transform hover:scale-110 focus:outline-none"
                style={{ left: `${pos.x}%`, top: `${pos.y}%` }}
              >
                <button
                  type="button"
                  onClick={() => handleSelectMonumentItem(monument)}
                  className="group relative flex flex-col items-center cursor-pointer focus:outline-none"
                  aria-label={`${monument.name_vi} - ${meta.label}`}
                >
                  {/* Pin Pulse Glow */}
                  {isSelected && (
                    <span className="absolute -inset-2 rounded-full bg-amber-400/40 animate-ping pointer-events-none" />
                  )}

                  {/* Marker Pin Icon */}
                  <div
                    className={cn(
                      "flex h-8 w-8 items-center justify-center rounded-full border-2 text-white shadow-xl transition-all",
                      isSelected
                        ? "bg-amber-500 border-white ring-4 ring-amber-400/50 scale-110"
                        : "bg-stone-900 border-amber-400 hover:border-white"
                    )}
                    style={{ borderColor: isSelected ? "#ffffff" : meta.stroke }}
                  >
                    <span
                      className="h-3 w-3 rounded-full"
                      style={{ backgroundColor: isSelected ? "#78350f" : meta.stroke }}
                    />
                  </div>

                  {/* Pin Point Needle */}
                  <div
                    className="h-0 w-0 border-l-[4px] border-l-transparent border-r-[4px] border-r-transparent border-t-[6px] -mt-0.5"
                    style={{ borderTopColor: isSelected ? "#ffffff" : meta.stroke }}
                  />

                  {/* Label */}
                  <div
                    className={cn(
                      "mt-1 rounded px-1.5 py-0.5 text-[10px] font-semibold whitespace-nowrap shadow-md backdrop-blur-md transition-all",
                      isSelected
                        ? "bg-amber-500 text-stone-950 ring-2 ring-white"
                        : "bg-stone-900/90 text-stone-200 border border-stone-700 group-hover:bg-stone-800"
                    )}
                  >
                    {monument.name_vi}
                  </div>
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* 4. RICH INFOWINDOW / PREVIEW MODAL FOR SELECTED MONUMENT */}
      {selectedMonument && (
        <div
          data-testid="monument-infowindow"
          className="absolute bottom-5 right-5 z-30 w-80 max-w-[calc(100vw-40px)] rounded-2xl border border-amber-500/30 bg-stone-900/95 p-4 shadow-2xl backdrop-blur-xl text-stone-100 animate-in fade-in-0 zoom-in-95 duration-150"
        >
          <div className="relative mb-3 h-36 w-full overflow-hidden rounded-xl bg-stone-950">
            <Image
              src={selectedMonument.photo}
              alt={selectedMonument.name_vi}
              fill
              className="object-cover transition-transform duration-500 hover:scale-105"
              sizes="320px"
            />
            <span className="absolute left-2.5 top-2.5 rounded-md bg-stone-950/80 px-2 py-0.5 text-[10px] font-semibold tracking-wide text-amber-300 backdrop-blur-sm border border-amber-500/30">
              {selectedMonument.era}
            </span>
            <button
              type="button"
              onClick={() => setSelectedMonument(null)}
              className="absolute right-2 top-2 flex h-6 w-6 items-center justify-center rounded-full bg-stone-950/70 text-stone-400 hover:bg-stone-900 hover:text-white"
              aria-label="Đóng bảng thông tin"
            >
              &times;
            </button>
          </div>

          <div className="mb-1 flex items-start justify-between gap-2">
            <div>
              <h3 className="font-serif text-base font-bold text-amber-200">
                {selectedMonument.name_vi}
                {selectedMonument.name_han_nom && (
                  <span className="ml-1.5 font-normal text-amber-500 font-serif">
                    ({selectedMonument.name_han_nom})
                  </span>
                )}
              </h3>
              <p className="text-[11px] text-stone-400">
                {selectedMonument.zone_name_vi} · Khởi dựng {selectedMonument.construction_year}
              </p>
            </div>
            <span
              className={cn(
                "rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase shrink-0",
                selectedMonument.condition === "extant"
                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                  : selectedMonument.condition === "reconstructed"
                  ? "bg-purple-500/20 text-purple-400 border border-purple-500/40"
                  : "bg-amber-500/20 text-amber-400 border border-amber-500/40"
              )}
            >
              {selectedMonument.condition === "extant"
                ? "Nguyên vẹn"
                : selectedMonument.condition === "reconstructed"
                ? "Phục dựng"
                : "Phế tích"}
            </span>
          </div>

          <p className="mb-3 line-clamp-2 text-xs leading-relaxed text-stone-300">
            {selectedMonument.summary}
          </p>

          <div className="flex items-center justify-between border-t border-stone-800 pt-2.5">
            <span className="text-[11px] font-mono text-stone-500">
              {selectedMonument.lat.toFixed(4)}°N, {selectedMonument.lng.toFixed(4)}°E
            </span>
            <Link
              href={`/dai-noi/cong-trinh/${selectedMonument.slug}`}
              className="inline-flex items-center gap-1.5 rounded-lg bg-amber-500 px-3 py-1.5 text-xs font-bold text-stone-950 transition-colors hover:bg-amber-400 shadow-md"
            >
              <span>Xem chi tiết</span>
              <ExternalLink className="h-3 w-3" />
            </Link>
          </div>
        </div>
      )}

      {/* 5. FLOATING MAP CONTROLS (Right Rail) */}
      <div className="absolute bottom-5 left-4 z-20 flex flex-col gap-2">
        {/* Map Type Switcher */}
        {showMapTypeSelector && (
          <div
            data-testid="map-type-controls"
            className="flex items-center gap-1 rounded-xl bg-stone-900/90 p-1 backdrop-blur-md border border-stone-800 shadow-xl"
          >
            {(["HYBRID", "ROADMAP", "TERRAIN"] as GoogleMapType[]).map((type) => (
              <button
                key={type}
                type="button"
                onClick={() => handleMapTypeChange(type)}
                className={cn(
                  "rounded-lg px-2.5 py-1 text-xs font-semibold transition-all",
                  mapType === type
                    ? "bg-amber-500 text-stone-950 shadow"
                    : "text-stone-300 hover:bg-stone-800"
                )}
              >
                {type === "HYBRID" ? "Vệ tinh" : type === "ROADMAP" ? "Đường phố" : "Địa hình"}
              </button>
            ))}
          </div>
        )}

        {/* Zoom & Fullscreen Controls */}
        <div className="flex items-center gap-1.5">
          {showZoomControls && (
            <div className="flex items-center gap-1 rounded-xl bg-stone-900/90 p-1 backdrop-blur-md border border-stone-800 shadow-xl">
              <button
                type="button"
                data-testid="btn-zoom-in"
                onClick={handleZoomIn}
                className="flex h-7 w-7 items-center justify-center rounded-lg text-stone-200 hover:bg-stone-800 focus:outline-none"
                aria-label="Phóng to"
              >
                <ZoomIn className="h-4 w-4" />
              </button>
              <button
                type="button"
                data-testid="btn-zoom-out"
                onClick={handleZoomOut}
                className="flex h-7 w-7 items-center justify-center rounded-lg text-stone-200 hover:bg-stone-800 focus:outline-none"
                aria-label="Thu nhỏ"
              >
                <ZoomOut className="h-4 w-4" />
              </button>
              <button
                type="button"
                data-testid="btn-zoom-reset"
                onClick={handleResetCenter}
                className="flex h-7 w-7 items-center justify-center rounded-lg text-stone-200 hover:bg-stone-800 focus:outline-none"
                title="Về trung tâm Đại Nội"
                aria-label="Về trung tâm"
              >
                <RotateCcw className="h-3.5 w-3.5" />
              </button>
            </div>
          )}

          {showFullscreenToggle && (
            <button
              type="button"
              data-testid="btn-fullscreen-toggle"
              onClick={() => setIsFullscreen((prev) => !prev)}
              className="flex h-9 w-9 items-center justify-center rounded-xl bg-stone-900/90 text-amber-300 hover:bg-stone-800 backdrop-blur-md border border-stone-800 shadow-xl focus:outline-none"
              title={isFullscreen ? "Thu nhỏ" : "Toàn màn hình"}
              aria-label={isFullscreen ? "Thu nhỏ" : "Toàn màn hình"}
            >
              {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default GoogleMapsImperial;
