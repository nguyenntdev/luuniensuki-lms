"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import Image, { type ImageProps } from "next/image";
import { RotateCcw, Landmark, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

export type ImageLayoutPreset = "full" | "hero" | "card" | "half" | "thumbnail";

/**
 * Derives a WebP image URL from a standard JPEG/PNG image path.
 * Leaves already WebP, SVG, or data URI sources unaltered.
 * Preserves query strings and URL fragments.
 *
 * @example
 * deriveWebpSrc("/assets/ban-duc-noi/cao-dinh.jpg") // => "/assets/ban-duc-noi/cao-dinh.webp"
 * deriveWebpSrc("https://example.com/gate.png?w=800") // => "https://example.com/gate.webp?w=800"
 */
export function deriveWebpSrc(src: string): string {
  if (!src || typeof src !== "string") return src;
  if (src.startsWith("data:") || src.startsWith("blob:")) return src;
  if (/\.webp(\?.*)?$/i.test(src) || /\.svg(\?.*)?$/i.test(src)) return src;

  return src.replace(/\.(jpe?g|png)(\?.*)?$/i, (match, ext, query) => {
    return `.webp${query || ""}`;
  });
}

/**
 * Returns optimized responsive sizes strings matching breakpoint standards:
 * - Mobile: < 640px
 * - Tablet: 640px - 1024px
 * - Desktop: > 1024px
 */
export function getResponsiveSizes(
  preset?: ImageLayoutPreset,
  customSizes?: string,
): string {
  if (customSizes) return customSizes;

  switch (preset) {
    case "full":
      return "100vw";
    case "hero":
      return "(max-width: 640px) 100vw, (max-width: 1024px) 90vw, 1200px";
    case "card":
      return "(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw";
    case "half":
      return "(max-width: 640px) 100vw, 50vw";
    case "thumbnail":
      return "(max-width: 640px) 80px, 120px";
    default:
      return "(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw";
  }
}

/**
 * Generates an authentic low-quality image placeholder (LQIP) data URI.
 * Produces a warm, amber-tinted imperial silk gradient blur SVG.
 */
export function generateImperialLqipDataUrl(hue: number = 38): string {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 10">
    <defs>
      <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="hsl(${hue}, 28%, 14%)"/>
        <stop offset="50%" stop-color="hsl(${hue + 6}, 32%, 18%)"/>
        <stop offset="100%" stop-color="hsl(${hue - 4}, 25%, 11%)"/>
      </linearGradient>
      <filter id="b"><feGaussianBlur stdDeviation="1.5"/></filter>
    </defs>
    <rect width="16" height="10" fill="url(#g)" filter="url(#b)"/>
  </svg>`;

  if (typeof window !== "undefined" && typeof window.btoa === "function") {
    return `data:image/svg+xml;base64,${window.btoa(svg)}`;
  }
  // SSR fallback
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
}

export interface CulturalPlaceholderProps {
  title?: string;
  subtitle?: string;
  alt?: string;
  onRetry?: () => void;
  className?: string;
  showRetry?: boolean;
}

/**
 * Cultural Placeholder Illustration
 * Renders an authentic Vietnamese Imperial architecture vector silhouette
 * (Ngọ Môn / Lầu Ngũ Phụng palace motif) with royal amber accents.
 */
export function CulturalPlaceholderIllustration({
  title = "Tư liệu di sản Hoàng Thành Huế",
  subtitle = "Hình ảnh đang được số hoá & kiểm chứng khảo cứu",
  alt,
  onRetry,
  className,
  showRetry = true,
}: CulturalPlaceholderProps) {
  return (
    <div
      role="img"
      aria-label={alt || title}
      className={cn(
        "relative flex h-full w-full flex-col items-center justify-center overflow-hidden rounded-xl border border-amber-900/40 bg-gradient-to-b from-stone-900/95 via-stone-950 to-stone-900 p-6 text-center select-none shadow-inner",
        className,
      )}
    >
      {/* Subtle traditional corner ornament accents */}
      <div className="absolute top-2 left-2 h-4 w-4 border-t-2 border-l-2 border-amber-500/30" />
      <div className="absolute top-2 right-2 h-4 w-4 border-t-2 border-r-2 border-amber-500/30" />
      <div className="absolute bottom-2 left-2 h-4 w-4 border-b-2 border-l-2 border-amber-500/30" />
      <div className="absolute bottom-2 right-2 h-4 w-4 border-b-2 border-r-2 border-amber-500/30" />

      {/* Stylized Ngọ Môn (Lầu Ngũ Phụng) Imperial Gate Silhouette */}
      <div className="relative mb-3 flex items-center justify-center">
        <svg
          viewBox="0 0 100 70"
          className="h-16 w-24 drop-shadow-[0_0_12px_rgba(245,158,11,0.25)] stroke-amber-500/80 fill-none"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
        >
          {/* Upper Pavilion (Lầu Ngũ Phụng upper curved eaves) */}
          <path
            d="M 28 22 Q 50 14 72 22 L 67 26 Q 50 20 33 26 Z"
            className="fill-amber-500/20 stroke-amber-400 stroke-1"
          />
          {/* Main Ridge Finials */}
          <path d="M 50 12 L 50 16 M 26 21 Q 23 18 20 22 M 74 21 Q 77 18 80 22" strokeWidth="1.2" />

          {/* Lower Pavilion Roof (Tier 2) */}
          <path
            d="M 16 34 Q 50 24 84 34 L 79 38 Q 50 30 21 38 Z"
            className="fill-amber-500/15 stroke-amber-400 stroke-1"
          />

          {/* Pavilion Pillars */}
          <line x1="32" y1="26" x2="32" y2="46" strokeWidth="1.2" />
          <line x1="44" y1="26" x2="44" y2="46" strokeWidth="1.2" />
          <line x1="56" y1="26" x2="56" y2="46" strokeWidth="1.2" />
          <line x1="68" y1="26" x2="68" y2="46" strokeWidth="1.2" />

          {/* Fortress Foundation Wall (Nền đài Thanh Câu) */}
          <path
            d="M 12 46 L 88 46 L 84 66 L 16 66 Z"
            className="fill-stone-800/80 stroke-amber-600/60 stroke-1"
          />

          {/* 3 Arched Gateways (Ngọ Môn 3 cửa chính giữa) */}
          {/* Center Royal Gate (Cửa Ngọ Môn dành cho Vua) */}
          <path
            d="M 44 66 L 44 54 Q 50 51 56 54 L 56 66 Z"
            className="fill-stone-950 stroke-amber-400/80 stroke-1"
          />
          {/* Left Gate (Tả Ngọ Môn) */}
          <path
            d="M 28 66 L 28 56 Q 33 54 38 56 L 38 66 Z"
            className="fill-stone-950 stroke-amber-500/50 stroke-1"
          />
          {/* Right Gate (Hữu Ngọ Môn) */}
          <path
            d="M 62 66 L 62 56 Q 67 54 72 56 L 72 66 Z"
            className="fill-stone-950 stroke-amber-500/50 stroke-1"
          />
        </svg>
      </div>

      {/* Cultural Information */}
      <div className="max-w-xs space-y-1">
        <div className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-0.5 text-[10px] font-semibold text-amber-300">
          <Sparkles className="h-3 w-3 text-amber-400" />
          <span>{title}</span>
        </div>

        <p className="text-[11px] text-stone-400 leading-snug line-clamp-2">
          {subtitle}
        </p>
      </div>

      {/* Optional Retry Button */}
      {showRetry && onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3.5 inline-flex items-center gap-1.5 rounded-lg border border-border/70 bg-stone-800/80 px-3 py-1.5 text-xs font-medium text-stone-200 transition-colors hover:bg-stone-700 hover:text-white focus:outline-none focus:ring-2 focus:ring-amber-500/50"
        >
          <RotateCcw className="h-3 w-3 text-amber-400" />
          <span>Thử tải lại</span>
        </button>
      )}
    </div>
  );
}

export interface OptimizedImageProps
  extends Omit<ImageProps, "src" | "onLoad" | "onError"> {
  /** Primary image source (JPEG, PNG, or WebP). */
  src: string;
  /** Accessible alternative description. */
  alt: string;
  /** Explicit WebP variant URL. If omitted and preferWebp is true, derived automatically from src. */
  webpSrc?: string;
  /** Whether to prefer WebP format with graceful fallback. Defaults to true. */
  preferWebp?: boolean;
  /** Secondary fallback image URL if primary fails before falling back to cultural illustration. */
  fallbackSrc?: string;
  /** Responsive layout preset matching common STTTNNĐ UI components. */
  layoutPreset?: ImageLayoutPreset;
  /** Low-quality image placeholder blur base64 URI. If omitted, uses authentic imperial SVG LQIP. */
  blurDataURL?: string;
  /** Aspect ratio container class when neither explicit width/height nor fill is set. */
  aspectRatioClass?: string;
  /** Outer container className. */
  containerClassName?: string;
  /** Custom title for cultural placeholder illustration. */
  culturalFallbackTitle?: string;
  /** Custom subtitle for cultural placeholder illustration. */
  culturalFallbackSubtitle?: string;
  /** Show cultural illustration on failure. Defaults to true. */
  showCulturalFallback?: boolean;
  /** Show retry button on cultural placeholder. Defaults to true. */
  showRetry?: boolean;
  /** Callback invoked on successful high-res load. */
  onLoad?: (e: React.SyntheticEvent<HTMLImageElement, Event>) => void;
  /** Callback invoked if all image source attempts fail. */
  onError?: (e: React.SyntheticEvent<HTMLImageElement, Event>) => void;
}

/**
 * High-Performance Imperial Image Component for STTTNNĐ.
 * Features:
 * 1. WebP format preference with seamless degradation to original JPEG/PNG.
 * 2. Low-quality image placeholder (LQIP) blur-up smooth CSS transition.
 * 3. Responsive `sizes` tailored to mobile, tablet, and desktop breakpoints.
 * 4. Built-in error fallback to authentic Vietnamese Imperial cultural illustration.
 */
export function OptimizedImage({
  src,
  alt,
  webpSrc,
  preferWebp = true,
  fallbackSrc,
  layoutPreset = "card",
  sizes,
  width,
  height,
  fill,
  priority = false,
  blurDataURL,
  aspectRatioClass = "aspect-[16/10]",
  className,
  containerClassName,
  culturalFallbackTitle,
  culturalFallbackSubtitle,
  showCulturalFallback = true,
  showRetry = true,
  onLoad,
  onError,
  ...restProps
}: OptimizedImageProps) {
  // Determine WebP candidate source
  const webpCandidate = useMemo(() => {
    if (webpSrc) return webpSrc;
    if (preferWebp && src) {
      return deriveWebpSrc(src);
    }
    return src;
  }, [src, webpSrc, preferWebp]);

  // Track candidate URL being currently attempted
  const [currentSrc, setCurrentSrc] = useState<string>(() => webpCandidate);
  const [isLoaded, setIsLoaded] = useState<boolean>(false);
  const [hasError, setHasError] = useState<boolean>(false);
  const [failedSources, setFailedSources] = useState<Set<string>>(new Set());

  // Reset internal states if primary src prop changes
  useEffect(() => {
    setCurrentSrc(webpCandidate);
    setIsLoaded(false);
    setHasError(false);
    setFailedSources(new Set());
  }, [webpCandidate]);

  // Compute responsive sizes attribute
  const resolvedSizes = useMemo(
    () => getResponsiveSizes(layoutPreset, sizes),
    [layoutPreset, sizes],
  );

  // Compute LQIP blur placeholder
  const resolvedBlurDataURL = useMemo(
    () => blurDataURL || generateImperialLqipDataUrl(),
    [blurDataURL],
  );

  const handleLoadSuccess = useCallback(
    (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
      setIsLoaded(true);
      setHasError(false);
      onLoad?.(e);
    },
    [onLoad],
  );

  const handleImageError = useCallback(
    (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
      const nextFailed = new Set(failedSources);
      nextFailed.add(currentSrc);
      setFailedSources(nextFailed);

      // 1. If currently on WebP candidate and original src is different and not failed, try original src
      if (currentSrc !== src && !nextFailed.has(src)) {
        setCurrentSrc(src);
        return;
      }

      // 2. If fallbackSrc provided and not failed, try fallbackSrc
      if (fallbackSrc && !nextFailed.has(fallbackSrc)) {
        setCurrentSrc(fallbackSrc);
        return;
      }

      // 3. All sources exhausted: activate cultural fallback
      setHasError(true);
      setIsLoaded(false);
      onError?.(e);
    },
    [currentSrc, src, fallbackSrc, failedSources, onError],
  );

  const handleRetry = useCallback(() => {
    setFailedSources(new Set());
    setHasError(false);
    setIsLoaded(false);
    setCurrentSrc(webpCandidate);
  }, [webpCandidate]);

  // Error Fallback: Render authentic Vietnamese imperial placeholder illustration
  if (hasError && showCulturalFallback) {
    return (
      <div
        className={cn(
          "relative w-full overflow-hidden",
          !width && !height && aspectRatioClass,
          containerClassName,
        )}
      >
        <CulturalPlaceholderIllustration
          title={culturalFallbackTitle}
          subtitle={culturalFallbackSubtitle}
          alt={alt}
          onRetry={handleRetry}
          showRetry={showRetry}
          className={className}
        />
      </div>
    );
  }

  // Determine layout mode: if neither explicit dimensions nor fill are given, default fill within container
  const useFill = fill ?? (!width && !height);

  return (
    <div
      className={cn(
        "relative overflow-hidden bg-stone-900/40",
        useFill && "w-full",
        !width && !height && aspectRatioClass,
        containerClassName,
      )}
    >
      {/* LQIP Blur-up Background / Shimmer */}
      {!isLoaded && (
        <div
          aria-hidden="true"
          className="absolute inset-0 z-0 bg-cover bg-center transition-opacity duration-500 ease-out"
          style={{
            backgroundImage: `url("${resolvedBlurDataURL}")`,
            filter: "blur(12px)",
            transform: "scale(1.08)",
          }}
        />
      )}

      {/* Main High-Performance Image */}
      <Image
        src={currentSrc}
        alt={alt}
        sizes={resolvedSizes}
        width={width}
        height={height}
        fill={useFill}
        priority={priority}
        onLoad={handleLoadSuccess}
        onError={handleImageError}
        className={cn(
          "transition-all duration-500 ease-out",
          useFill && "object-cover",
          isLoaded
            ? "opacity-100 blur-0 scale-100"
            : "opacity-0 blur-sm scale-[1.02]",
          className,
        )}
        {...restProps}
      />
    </div>
  );
}

export default OptimizedImage;
