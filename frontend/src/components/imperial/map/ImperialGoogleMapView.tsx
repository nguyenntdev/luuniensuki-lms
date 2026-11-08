"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  Compass,
  ExternalLink,
  Layers,
  MapPin,
  Maximize2,
  Navigation,
  RotateCcw,
  Sparkles,
  Volume2,
} from "lucide-react";
import { setOptions, importLibrary } from "@googlemaps/js-api-loader";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  HUE_IMPERIAL_CITY_CENTER,
  HUE_IMPERIAL_CITY_BOUNDS,
  MONUMENT_GPS_REGISTRY,
  getGoogleMapsDirectionsUrl,
  getGoogleMapsEmbedUrl,
  getGoogleMapsUrl,
  getMonumentGps,
  type MonumentGpsCoordinate,
} from "@/lib/imperial/gps-coordinates";
import type { ImperialMapAnnotation, ImperialSite } from "@/lib/imperial/map-types";
import { cn } from "@/lib/utils";

export interface ImperialGoogleMapViewProps {
  annotations?: ImperialMapAnnotation[];
  selectedSlug?: string | null;
  activeZoneSlug?: string | null;
  onSelectMonument?: (slug: string) => void;
  className?: string;
  defaultZoom?: number;
}

const ZONE_COLORS: Record<string, { bg: string; border: string; text: string; pin: string }> = {
  "central-ceremonial-axis": {
    bg: "bg-red-500/10",
    border: "border-red-500/40",
    text: "text-red-500",
    pin: "#EF4444",
  },
  "ancestral-worship-space": {
    bg: "bg-amber-500/10",
    border: "border-amber-500/40",
    text: "text-amber-500",
    pin: "#F59E0B",
  },
  "purple-forbidden-city": {
    bg: "bg-purple-500/10",
    border: "border-purple-500/40",
    text: "text-purple-400",
    pin: "#A855F7",
  },
  "royal-living-gardens": {
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/40",
    text: "text-emerald-400",
    pin: "#10B981",
  },
};

export function ImperialGoogleMapView({
  annotations = [],
  selectedSlug,
  activeZoneSlug,
  onSelectMonument,
  className,
  defaultZoom = 17,
}: ImperialGoogleMapViewProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const [mapType, setMapType] = useState<"hybrid" | "satellite" | "roadmap">("hybrid");
  const [googleMapInstance, setGoogleMapInstance] = useState<google.maps.Map | null>(null);
  const markersRef = useRef<google.maps.Marker[]>([]);
  const [infoWindow, setInfoWindow] = useState<google.maps.InfoWindow | null>(null);
  const [activeSite, setActiveSite] = useState<MonumentGpsCoordinate | null>(() => {
    return selectedSlug ? getMonumentGps(selectedSlug) : null;
  });
  const [useFallbackEmbed, setUseFallbackEmbed] = useState(false);

  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;

  // Filter monuments by active zone
  const visibleMonuments = Object.values(MONUMENT_GPS_REGISTRY).filter((m) => {
    if (!activeZoneSlug) return true;
    return m.zone_slug === activeZoneSlug;
  });

  // Handle SDK Loading
  useEffect(() => {
    if (!apiKey) {
      setUseFallbackEmbed(true);
      return;
    }

    let isMounted = true;
    setOptions({
      key: apiKey,
      v: "weekly",
    });

    Promise.all([
      importLibrary("maps") as Promise<google.maps.MapsLibrary>,
    ])
      .then(([{ Map, InfoWindow }]) => {
        if (!isMounted || !mapRef.current) return;

        const map = new Map(mapRef.current, {
          center: {
            lat: HUE_IMPERIAL_CITY_CENTER.lat,
            lng: HUE_IMPERIAL_CITY_CENTER.lng,
          },
          zoom: defaultZoom,
          mapTypeId: mapType,
          tilt: 45,
          mapTypeControl: false,
          streetViewControl: true,
          fullscreenControl: false,
          zoomControl: true,
          restriction: {
            latLngBounds: {
              north: HUE_IMPERIAL_CITY_BOUNDS.north,
              south: HUE_IMPERIAL_CITY_BOUNDS.south,
              east: HUE_IMPERIAL_CITY_BOUNDS.east,
              west: HUE_IMPERIAL_CITY_BOUNDS.west,
            },
            strictBounds: false,
          },
        });

        const iWindow = new InfoWindow();
        setInfoWindow(iWindow);
        setGoogleMapInstance(map);
      })
      .catch((err: unknown) => {
        console.warn("Google Maps JS API failed to load, falling back to satellite embed:", err);
        if (isMounted) {
          setUseFallbackEmbed(true);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [apiKey, defaultZoom, mapType]);

  // Update Map Type
  useEffect(() => {
    if (googleMapInstance) {
      googleMapInstance.setMapTypeId(mapType);
    }
  }, [mapType, googleMapInstance]);

  // Render or Update Markers on Google Map
  useEffect(() => {
    if (!googleMapInstance || typeof google === "undefined") return;

    // Clear previous markers
    markersRef.current.forEach((m) => m.setMap(null));
    const newMarkers: google.maps.Marker[] = [];

    visibleMonuments.forEach((monument) => {
      const isSelected = selectedSlug === monument.slug;
      const zoneStyle = ZONE_COLORS[monument.zone_slug] || { pin: "#D4AF37" };

      const marker = new google.maps.Marker({
        position: { lat: monument.lat, lng: monument.lng },
        map: googleMapInstance,
        title: monument.name_vi,
        animation: isSelected ? google.maps.Animation.BOUNCE : undefined,
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: isSelected ? 9 : 7,
          fillColor: zoneStyle.pin,
          fillOpacity: 0.95,
          strokeColor: "#FFFFFF",
          strokeWeight: 2,
        },
      });

      marker.addListener("click", () => {
        setActiveSite(monument);
        onSelectMonument?.(monument.slug);

        if (infoWindow) {
          const content = `
            <div style="font-family: ui-sans-serif, system-ui, sans-serif; padding: 6px; max-width: 260px; color: #1c1917;">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                <span style="font-size: 10px; font-weight: 700; color: #b45309; text-transform: uppercase;">${monument.zone_title_vi}</span>
                <span style="font-size: 11px; font-family: serif; color: #78716c;">${monument.name_han_nom}</span>
              </div>
              <h3 style="font-size: 15px; font-weight: 800; margin: 0 0 4px 0; color: #0c0a09;">${monument.name_vi}</h3>
              <p style="font-size: 11px; color: #57534e; margin: 0 0 8px 0;">${monument.name_en}</p>
              <div style="display: flex; gap: 6px;">
                <a href="/dai-noi/cong-trinh/${monument.slug}" style="display: inline-block; background: #8e2323; color: #ffffff; text-decoration: none; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: 600;">Xem hồ sơ</a>
                <a href="${getGoogleMapsDirectionsUrl(monument.lat, monument.lng, monument.name_vi)}" target="_blank" rel="noopener noreferrer" style="display: inline-block; background: #f5f5f4; color: #292524; text-decoration: none; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: 600; border: 1px solid #d6d3d1;">Chỉ đường</a>
              </div>
            </div>
          `;
          infoWindow.setContent(content);
          infoWindow.open(googleMapInstance, marker);
        }
      });

      newMarkers.push(marker);
    });

    markersRef.current = newMarkers;

    return () => {
      newMarkers.forEach((m) => m.setMap(null));
    };
  }, [googleMapInstance, visibleMonuments, selectedSlug, infoWindow, onSelectMonument]);

  // Center on Selected Monument
  useEffect(() => {
    if (!googleMapInstance || !selectedSlug) return;
    const monument = MONUMENT_GPS_REGISTRY[selectedSlug];
    if (monument) {
      googleMapInstance.panTo({ lat: monument.lat, lng: monument.lng });
      googleMapInstance.setZoom(19);
      setActiveSite(monument);
    }
  }, [selectedSlug, googleMapInstance]);

  const handleResetCenter = useCallback(() => {
    if (googleMapInstance) {
      googleMapInstance.panTo({
        lat: HUE_IMPERIAL_CITY_CENTER.lat,
        lng: HUE_IMPERIAL_CITY_CENTER.lng,
      });
      googleMapInstance.setZoom(17);
      setActiveSite(null);
    }
  }, [googleMapInstance]);

  const activeCoord = activeSite || (selectedSlug ? getMonumentGps(selectedSlug) : null);

  return (
    <div className={cn("relative w-full h-full min-h-[460px] rounded-3xl overflow-hidden bg-stone-950 flex flex-col", className)}>
      {/* Top Map Layer Switcher & Tools */}
      <div className="absolute top-4 inset-x-4 z-20 flex flex-wrap items-center justify-between gap-2 pointer-events-none">
        {/* Layer Modes */}
        <div className="pointer-events-auto flex items-center gap-1 p-1 rounded-2xl bg-stone-900/90 backdrop-blur-xl border border-stone-800 text-xs shadow-xl">
          <Button
            type="button"
            size="xs"
            variant={mapType === "hybrid" ? "default" : "ghost"}
            onClick={() => setMapType("hybrid")}
            className="rounded-xl text-[11px] font-semibold h-7 px-2.5"
          >
            <Layers className="w-3.5 h-3.5 mr-1" />
            Vệ tinh kết hợp
          </Button>
          <Button
            type="button"
            size="xs"
            variant={mapType === "satellite" ? "default" : "ghost"}
            onClick={() => setMapType("satellite")}
            className="rounded-xl text-[11px] font-semibold h-7 px-2.5"
          >
            Vệ tinh thuần
          </Button>
          <Button
            type="button"
            size="xs"
            variant={mapType === "roadmap" ? "default" : "ghost"}
            onClick={() => setMapType("roadmap")}
            className="rounded-xl text-[11px] font-semibold h-7 px-2.5"
          >
            Bản đồ đường
          </Button>
        </div>

        {/* Action Controls */}
        <div className="pointer-events-auto flex items-center gap-2">
          <Button
            type="button"
            size="xs"
            variant="secondary"
            onClick={handleResetCenter}
            className="rounded-xl shadow-lg bg-stone-900/90 hover:bg-stone-800 border border-stone-800 text-stone-200 text-xs font-semibold h-8 px-3"
            title="Trở về trung tâm Đại Nội"
          >
            <RotateCcw className="w-3.5 h-3.5 mr-1" />
            Trung tâm Cố đô
          </Button>

          <Button
            asChild
            size="xs"
            variant="outline"
            className="rounded-xl shadow-lg bg-stone-900/90 hover:bg-stone-800 border-stone-700 text-stone-200 text-xs font-semibold h-8 px-3"
          >
            <a
              href={
                activeCoord
                  ? getGoogleMapsUrl(activeCoord.lat, activeCoord.lng, activeCoord.name_vi)
                  : getGoogleMapsUrl(HUE_IMPERIAL_CITY_CENTER.lat, HUE_IMPERIAL_CITY_CENTER.lng, "Đại Nội Huế")
              }
              target="_blank"
              rel="noopener noreferrer"
            >
              <ExternalLink className="w-3.5 h-3.5 mr-1 text-primary" />
              Mở Google Maps
            </a>
          </Button>
        </div>
      </div>

      {/* Primary Map Viewport Container */}
      {!useFallbackEmbed ? (
        <div ref={mapRef} className="w-full h-full flex-1" role="region" aria-label="Bản đồ vệ tinh Google Maps Đại Nội Huế" />
      ) : (
        /* Fallback Satellite Embed when API key is not present or failed */
        <div className="relative w-full h-full flex-1">
          <iframe
            title="Bản đồ vệ tinh Google Maps Đại Nội Huế"
            src={getGoogleMapsEmbedUrl(
              activeCoord?.lat || HUE_IMPERIAL_CITY_CENTER.lat,
              activeCoord?.lng || HUE_IMPERIAL_CITY_CENTER.lng,
              activeCoord ? 19 : 17,
            )}
            className="w-full h-full border-0 filter contrast-105"
            loading="lazy"
            allowFullScreen
          />

          {/* Quick-select monument pill bar in embed mode */}
          <div className="absolute bottom-4 inset-x-4 z-20 flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar pointer-events-auto">
            {visibleMonuments.map((m) => {
              const isSelected = (activeCoord?.slug || selectedSlug) === m.slug;
              return (
                <button
                  key={m.slug}
                  type="button"
                  onClick={() => {
                    setActiveSite(m);
                    onSelectMonument?.(m.slug);
                  }}
                  className={cn(
                    "shrink-0 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all border shadow-lg flex items-center gap-1.5",
                    isSelected
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-stone-900/90 hover:bg-stone-800 text-stone-200 border-stone-800",
                  )}
                >
                  <MapPin className="w-3 h-3 text-amber-400" />
                  <span>{m.name_vi}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Floating Selected Monument Detail Card */}
      {activeCoord && (
        <div className="absolute bottom-4 left-4 z-20 max-w-sm rounded-2xl bg-stone-950/95 backdrop-blur-xl border border-stone-800 p-4 shadow-2xl text-stone-200 pointer-events-auto space-y-2">
          <div className="flex items-center justify-between gap-2">
            <Badge variant="outline" className="text-[10px] uppercase font-bold text-amber-400 border-amber-500/30">
              {activeCoord.zone_title_vi}
            </Badge>
            <span className="font-serif text-xs text-stone-400">{activeCoord.name_han_nom}</span>
          </div>

          <div>
            <h3 className="font-serif font-bold text-base text-stone-100">{activeCoord.name_vi}</h3>
            <p className="text-xs text-stone-400 italic">{activeCoord.name_en}</p>
          </div>

          <div className="flex items-center gap-2 text-[11px] text-stone-400 font-mono">
            <MapPin className="w-3 h-3 text-red-400 shrink-0" />
            <span>GPS: {activeCoord.lat.toFixed(4)}°N, {activeCoord.lng.toFixed(4)}°E</span>
          </div>

          <div className="pt-2 flex items-center gap-2 border-t border-stone-800">
            <Button asChild size="xs" className="flex-1 rounded-xl text-xs font-semibold bg-primary hover:bg-primary/90 text-primary-foreground">
              <Link href={`/dai-noi/cong-trinh/${activeCoord.slug}`}>
                Hồ sơ di tích
              </Link>
            </Button>
            <Button asChild size="xs" variant="outline" className="rounded-xl text-xs font-semibold border-stone-700 hover:bg-stone-800 text-stone-200">
              <a
                href={getGoogleMapsDirectionsUrl(activeCoord.lat, activeCoord.lng, activeCoord.name_vi)}
                target="_blank"
                rel="noopener noreferrer"
              >
                <Navigation className="w-3.5 h-3.5 mr-1 text-emerald-400" />
                Chỉ đường
              </a>
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
