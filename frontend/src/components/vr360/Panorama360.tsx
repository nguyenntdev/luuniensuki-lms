"use client";

/**
 * Panorama360 — a fully self-hosted equirectangular 360° viewer built on Three.js
 * stack with verified historical museum provenance, source citations, accessibility,
 * reduced-motion support, and resilient 2D still fallbacks.
 *
 * Ref: Luu Nien STTTNND Follow-On SPEC V5.1 (Ticket V5-T047 / Wave W04-A07)
 */

import React, { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, useTexture } from "@react-three/drei";
import { BackSide } from "three";
import {
  AlertCircle,
  BookOpen,
  Compass,
  ExternalLink,
  Eye,
  Info,
  Layers,
  MapPin,
  Maximize2,
  RefreshCw,
  Sparkles,
  Volume2,
  X,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  type HistoricalMonumentLink,
  type HistoricalSourceCitation,
  type PanoramaViewpoint,
  getVerifiedMonumentOrFallback,
  isBrokenPanoramaUri,
  generateAccessible2DDescription,
  resolvePanorama2DFallback,
} from "@/lib/imperial/panorama-sources";

export type {
  HistoricalMonumentLink,
  HistoricalSourceCitation,
  PanoramaViewpoint,
};

function PanoSphere({ src }: { src: string }) {
  const texture = useTexture(src);
  return (
    // Negative x-scale flips the texture so it reads correctly from the inside.
    <mesh scale={[-1, 1, 1]}>
      <sphereGeometry args={[500, 64, 40]} />
      <meshBasicMaterial map={texture} side={BackSide} toneMapped={false} />
    </mesh>
  );
}

class PanoErrorBoundary extends React.Component<
  { fallback: React.ReactNode; children: React.ReactNode; onError?: () => void },
  { failed: boolean }
> {
  constructor(props: { fallback: React.ReactNode; children: React.ReactNode; onError?: () => void }) {
    super(props);
    this.state = { failed: false };
  }
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch(err: unknown) {
    console.warn("Panorama360 WebGL / Texture render failed:", err);
    this.props.onError?.();
  }
  render() {
    return this.state.failed ? this.props.fallback : this.props.children;
  }
}

export interface Panorama360Props {
  src: string;
  title?: string;
  subtitle?: string;
  alt?: string;
  ariaLabel?: string;
  monument?: HistoricalMonumentLink;
  monumentKey?: string;
  viewpoints?: PanoramaViewpoint[];
  fallbackImageUrl?: string;
  fallbackDescription?: string;
  reducedMotion?: boolean;
  className?: string;
  onSourceClick?: (source: HistoricalSourceCitation) => void;
}

export default function Panorama360({
  src,
  title,
  subtitle,
  alt,
  ariaLabel,
  monument: propMonument,
  monumentKey,
  viewpoints = [],
  fallbackImageUrl,
  fallbackDescription,
  reducedMotion: propReducedMotion = false,
  className = "",
  onSourceClick,
}: Panorama360Props) {
  // 1. Resolve Monument & Provenance
  const monument: HistoricalMonumentLink = useMemo(() => {
    if (propMonument) return propMonument;
    return getVerifiedMonumentOrFallback(monumentKey || title, title);
  }, [propMonument, monumentKey, title]);

  // 2. Reduced Motion Detection
  const [systemReducedMotion, setSystemReducedMotion] = useState(false);
  const [userForceStatic2D, setUserForceStatic2D] = useState(false);
  const [isSourceModalOpen, setIsSourceModalOpen] = useState(false);
  const [webGLFailed, setWebGLFailed] = useState(false);
  const [fallbackImageError, setFallbackImageError] = useState(false);
  const [announcement, setAnnouncement] = useState("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const mql = window.matchMedia("(prefers-reduced-motion: reduce)");
    setSystemReducedMotion(mql.matches);
    const handler = (e: MediaQueryListEvent) => setSystemReducedMotion(e.matches);
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, []);

  const effectiveReducedMotion = propReducedMotion || systemReducedMotion;
  const isBrokenSrc = isBrokenPanoramaUri(src);

  // 3. Fallback 2D Still & Description Resolution
  const resolved2D = useMemo(() => {
    return resolvePanorama2DFallback(src, fallbackImageUrl, monument.slug);
  }, [src, fallbackImageUrl, monument.slug]);

  const effectiveAlt =
    alt ||
    `Toàn cảnh không gian di sản 360 độ: ${monument.name} - ${title || monument.historicalPeriod}`;

  const effectiveAriaLabel =
    ariaLabel ||
    `Toàn cảnh di tích lịch sử ${monument.name}. Sử dụng chuột hoặc cảm ứng để xoay góc nhìn toàn cảnh 360 độ.`;

  const accessibleFullDescription =
    fallbackDescription ||
    generateAccessible2DDescription(monument, viewpoints);

  // Accessible 2D Still / Description Alternative Component
  const renderAccessible2DFallback = (
    <div
      className="flex flex-col h-full w-full bg-zinc-950 text-zinc-100 rounded-xl overflow-hidden border border-zinc-800"
      role="region"
      aria-roledescription="toàn cảnh 2D thay thế"
      aria-label={`Bản thể hiện 2D tĩnh tiếp cận của: ${monument.name}`}
    >
      {/* Notice Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 bg-amber-950/40 border-b border-amber-800/40 text-xs text-amber-200">
        <div className="flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            <strong>Chế độ toàn cảnh 2D tiếp cận:</strong> {isBrokenSrc ? "Không tìm thấy tệp toàn cảnh 360°" : "Chế độ hiển thị tĩnh thân thiện chuyển động"}. Cung cấp ảnh tư liệu 2D và hồ sơ sử liệu xác thực.
          </span>
        </div>
        {!isBrokenSrc && (
          <Button
            size="sm"
            variant="outline"
            className="h-6 text-xs border-amber-600/50 hover:bg-amber-800/30 text-amber-100"
            onClick={() => {
              setWebGLFailed(false);
              setUserForceStatic2D(false);
              setAnnouncement("Đã bật chế độ 3D tương tác");
            }}
          >
            <RefreshCw className="w-3 h-3 mr-1" />
            Bật 3D tương tác
          </Button>
        )}
      </div>

      {/* Screen Reader Live Region */}
      <div role="status" aria-live="polite" className="sr-only">
        {announcement}
      </div>

      {/* 2D Still Image Container */}
      <div className="relative w-full aspect-[16/9] max-h-[380px] bg-black overflow-hidden flex items-center justify-center">
        {!fallbackImageError ? (
          <img
            src={resolved2D.fallbackImageUrl}
            alt={effectiveAlt}
            className="w-full h-full object-cover"
            onError={() => setFallbackImageError(true)}
          />
        ) : (
          /* SVG Blueprint Fallback when image is missing */
          <div className="w-full h-full flex flex-col items-center justify-center p-6 bg-zinc-900 border border-zinc-800 text-center">
            <Layers className="w-12 h-12 text-amber-400/80 mb-2" />
            <h4 className="font-serif font-bold text-amber-200 text-base">
              Bản vẽ kiến trúc & tư liệu khảo sát di tích
            </h4>
            <p className="text-xs text-zinc-400 max-w-md mt-1">
              {monument.name} — {monument.architecturalStyle || "Kiến trúc Cung đình Huế"}
            </p>
          </div>
        )}

        {/* Floating Badges */}
        <div className="absolute top-3 left-3 flex items-center gap-2 rounded-full bg-black/75 px-3 py-1 text-xs font-medium text-amber-300 border border-amber-500/30 backdrop-blur">
          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
          {monument.verificationStatus === "canonical" ? "Di sản Chính thống" : "Đã xác thực sử liệu"}
        </div>
      </div>

      {/* Historical Dossier & Primary Sources */}
      <div className="p-4 sm:p-5 space-y-4 bg-zinc-950/90 text-sm overflow-y-auto">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="font-serif font-bold text-lg text-amber-100">
              {monument.name}
            </h3>
            {monument.nationalTreasure && (
              <Badge variant="outline" className="border-amber-500/50 text-amber-300 text-[11px]">
                {monument.nationalTreasure}
              </Badge>
            )}
          </div>
          <p className="text-xs text-zinc-400">
            Niên đại: <span className="text-zinc-200 font-medium">{monument.historicalPeriod}</span>
            {monument.coordinatesSummary && ` · ${monument.coordinatesSummary}`}
          </p>
        </div>

        <p className="text-xs sm:text-sm text-zinc-300 leading-relaxed">
          {monument.provenance}
        </p>

        {/* Primary Source Citations */}
        {monument.sourceCitations && monument.sourceCitations.length > 0 && (
          <div className="pt-2 border-t border-zinc-800/80 space-y-2">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-400">
              <BookOpen className="w-3.5 h-3.5" />
              Sử liệu và Thư mục gốc xác thực:
            </div>
            <ul className="space-y-1.5">
              {monument.sourceCitations.map((cite, idx) => (
                <li
                  key={cite.id || idx}
                  className="p-2 rounded bg-zinc-900/60 border border-zinc-800 text-xs space-y-0.5"
                >
                  <div className="font-medium text-zinc-200 flex items-center justify-between">
                    <span>
                      {cite.title} {cite.locator ? `— ${cite.locator}` : ""}
                    </span>
                    {cite.evidenceStrength && (
                      <span className="text-[10px] text-emerald-400 uppercase tracking-wider font-semibold">
                        {cite.evidenceStrength}
                      </span>
                    )}
                  </div>
                  {cite.citationQuote && (
                    <blockquote className="italic text-zinc-400 text-[11px] border-l-2 border-amber-500/40 pl-2 mt-1">
                      &ldquo;{cite.citationQuote}&rdquo;
                    </blockquote>
                  )}
                  {cite.author && (
                    <div className="text-[10px] text-zinc-500">
                      Tác giả: {cite.author} ({cite.year || "Triều Nguyễn"})
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Viewpoints list if present */}
        {viewpoints.length > 0 && (
          <div className="pt-2 border-t border-zinc-800/80 space-y-2">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-400">
              <MapPin className="w-3.5 h-3.5" />
              Điểm quan sát trong không gian ({viewpoints.length}):
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {viewpoints.map((vp, idx) => (
                <div
                  key={vp.id || idx}
                  className="p-2 rounded bg-zinc-900/40 border border-zinc-800/80 text-xs"
                >
                  <div className="font-medium text-zinc-200">
                    {idx + 1}. {vp.title}
                  </div>
                  {vp.description && (
                    <p className="text-[11px] text-zinc-400 mt-0.5 line-clamp-2">
                      {vp.description}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Footer attribution */}
        <div className="pt-3 border-t border-zinc-800 flex flex-wrap items-center justify-between gap-2 text-[11px] text-zinc-400">
          <div>
            Quản lý tư liệu: <span className="text-zinc-300">{monument.rightsOwner}</span> ({monument.license})
          </div>
          {monument.monumentUrl && (
            <a
              href={monument.monumentUrl}
              className="inline-flex items-center gap-1 text-amber-400 hover:underline font-medium"
            >
              Xem chuyên trang di tích <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
      </div>
    </div>
  );

  // If broken URI, WebGL failed, or user explicitly requested 2D mode:
  if (isBrokenSrc || webGLFailed || userForceStatic2D) {
    return (
      <div className={`relative h-full w-full overflow-hidden rounded-lg bg-black ring-1 ring-white/10 ${className}`}>
        {renderAccessible2DFallback}
      </div>
    );
  }

  return (
    <div
      className={`relative h-full w-full overflow-hidden rounded-lg bg-black ring-1 ring-white/10 contrast-more:border-2 contrast-more:border-foreground ${className}`}
      role="region"
      aria-roledescription="toàn cảnh 360 độ"
      aria-label={effectiveAriaLabel}
    >
      {/* Screen Reader Live Region */}
      <div role="status" aria-live="polite" className="sr-only">
        {announcement}
      </div>

      <PanoErrorBoundary
        fallback={renderAccessible2DFallback}
        onError={() => setWebGLFailed(true)}
      >
        <Canvas
          camera={{ position: [0, 0, 0.1], fov: 75, near: 0.1, far: 1000 }}
          dpr={[1, 1.6]}
          gl={{ antialias: true }}
          style={{ width: "100%", height: "100%" }}
          aria-label={effectiveAriaLabel}
        >
          <Suspense fallback={null}>
            <PanoSphere src={src} />
          </Suspense>
          <OrbitControls
            enableZoom
            enablePan={false}
            enableDamping={!effectiveReducedMotion}
            dampingFactor={effectiveReducedMotion ? 0 : 0.08}
            rotateSpeed={-0.4}
            minDistance={0.1}
            maxDistance={1}
            zoomSpeed={0.6}
            autoRotate={false}
          />
        </Canvas>
      </PanoErrorBoundary>

      {/* Top Left Branding & Monument badge */}
      <div className="absolute left-3 top-3 flex flex-wrap items-center gap-2 z-10 pointer-events-auto">
        <div className="flex items-center gap-2 rounded-full bg-black/60 backdrop-blur px-3 py-1.5 text-xs font-medium text-white border border-white/10">
          <span className="inline-block h-2 w-2 rounded-full bg-amber-400" />
          <span>Lưu Niên Sử Kí · {monument.name}</span>
        </div>

        {/* Source & Provenance Button */}
        <Button
          size="sm"
          variant="outline"
          onClick={() => setIsSourceModalOpen(true)}
          className="h-7 text-xs bg-black/65 border-amber-500/40 text-amber-200 hover:bg-amber-950/60 hover:text-amber-100 rounded-full px-2.5 backdrop-blur"
          aria-label="Xem chứng thực lịch sử và nguồn sử liệu"
        >
          <BookOpen className="w-3.5 h-3.5 mr-1 text-amber-400" />
          Sử liệu & Chứng thực
        </Button>
      </div>

      {/* Top Right Controls: Motion Mode & Gesture Hint */}
      <div className="absolute right-3 top-3 flex items-center gap-2 z-10 pointer-events-auto">
        <Button
          size="sm"
          variant="ghost"
          onClick={() => {
            setUserForceStatic2D(true);
            setAnnouncement("Đã chuyển sang chế độ ảnh tĩnh 2D tiếp cận");
          }}
          className="h-7 text-[11px] bg-black/50 text-zinc-300 hover:bg-black/80 hover:text-white rounded-full px-2.5 backdrop-blur border border-white/10"
          title="Chuyển sang chế độ ảnh tĩnh 2D (giảm chóng mặt / chuyển động)"
          aria-label="Chuyển sang chế độ toàn cảnh trải phẳng 2D"
        >
          <Layers className="w-3 h-3 mr-1 text-amber-400" />
          Chế độ 2D
        </Button>
        <div className="hidden sm:block rounded-full bg-black/40 px-3 py-1.5 text-[11px] text-zinc-200 backdrop-blur border border-white/5 pointer-events-none">
          Kéo để nhìn quanh · cuộn để phóng to
        </div>
      </div>

      {/* Bottom Scene Title & Historical Period */}
      <div className="pointer-events-none absolute bottom-3 left-3 z-10 rounded-lg bg-black/60 px-3 py-1.5 text-sm text-white backdrop-blur border border-white/10 max-w-[80%]">
        <div className="font-semibold text-xs sm:text-sm text-amber-200">
          {title || monument.name}
        </div>
        <div className="text-[11px] text-zinc-300">
          {subtitle || monument.historicalPeriod}
        </div>
      </div>

      {/* Slide-out / Modal for Historical Sources & Provenance */}
      {isSourceModalOpen && (
        <div
          className="absolute inset-0 z-30 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="sources-dialog-title"
        >
          <div className="bg-zinc-900 border border-zinc-700 rounded-2xl max-w-lg w-full max-h-[90%] overflow-y-auto p-5 text-zinc-100 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
              <div className="flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-amber-400" />
                <h3 id="sources-dialog-title" className="font-serif font-bold text-base text-amber-100">
                  Chứng thực Lịch sử & Nguồn tư liệu
                </h3>
              </div>
              <Button
                size="icon"
                variant="ghost"
                className="w-7 h-7 text-zinc-400 hover:text-white"
                onClick={() => setIsSourceModalOpen(false)}
                aria-label="Đóng"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>

            <div className="space-y-2 text-xs">
              <div className="font-medium text-amber-300 text-sm">{monument.name}</div>
              <div className="text-zinc-300">{monument.provenance}</div>
            </div>

            {monument.sourceCitations && monument.sourceCitations.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-amber-400 uppercase tracking-wider">
                  Thư mục nguồn sơ cấp & Sử liệu:
                </h4>
                <div className="space-y-2">
                  {monument.sourceCitations.map((c, i) => (
                    <div
                      key={c.id || i}
                      className="p-3 rounded-lg bg-zinc-950/70 border border-zinc-800 text-xs space-y-1"
                    >
                      <div className="font-semibold text-zinc-200">
                        {c.title} {c.locator ? `— ${c.locator}` : ""}
                      </div>
                      {c.citationQuote && (
                        <blockquote className="italic text-zinc-400 border-l-2 border-amber-500/50 pl-2">
                          &ldquo;{c.citationQuote}&rdquo;
                        </blockquote>
                      )}
                      <div className="text-[11px] text-zinc-500">
                        {c.author} ({c.year}) · Độ tin cậy: {c.evidenceStrength || "xác thực"}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="pt-3 border-t border-zinc-800 flex items-center justify-between text-xs text-zinc-400">
              <span>{monument.rightsOwner}</span>
              {monument.monumentUrl && (
                <a
                  href={monument.monumentUrl}
                  className="text-amber-400 hover:underline flex items-center gap-1 font-medium"
                >
                  Khám phá thêm <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
