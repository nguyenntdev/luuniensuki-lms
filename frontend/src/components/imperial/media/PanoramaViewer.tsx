"use client";

import React, { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import {
  AlertCircle,
  Compass,
  Eye,
  Maximize2,
  Minimize2,
  Minus,
  Plus,
  RefreshCw,
  RotateCcw,
  Sparkles,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  MapPin,
  HelpCircle,
  ExternalLink,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { ArtDetailModal } from "../art-detail/ArtDetailModal";
import type {
  ImperialArtDetail,
  ImperialMediaHotspot,
} from "@/lib/imperial/v51-types";
import {
  DEFAULT_SPHERE_RADIUS,
  cartesianToScreen,
  clampPitch,
  normalizeAngle,
  sphericalToCartesian,
  sphericalToUV,
  type ScreenPosition,
} from "@/lib/imperial/panorama-math";

export interface PanoramaHotspot {
  id: string;
  title: string;
  description?: string | null;
  yaw: number; // degrees -180..180
  pitch: number; // degrees -90..90
  art_detail_slug?: string | null;
  detail_id?: string | null;
  art_detail?: ImperialArtDetail | null;
  category?: "art_detail" | "architecture" | "monument" | "observation" | string;
  [key: string]: unknown;
}

export interface PanoramaViewerProps {
  src: string;
  title?: string;
  subtitle?: string;
  hotspots?: (PanoramaHotspot | ImperialMediaHotspot)[];
  initialYaw?: number; // default: 0
  initialPitch?: number; // default: 0
  initialFov?: number; // default: 75
  minFov?: number; // default: 35
  maxFov?: number; // default: 95
  className?: string;
  onHotspotClick?: (hotspot: PanoramaHotspot) => void;
  onYawPitchChange?: (yaw: number, pitch: number) => void;
  showControls?: boolean; // default: true
  showCompass?: boolean; // default: true
  autoRotate?: boolean; // default: false
  autoRotateSpeed?: number; // default: 0.1 deg/frame
  fallbackImageUrl?: string;
}

/**
 * Normalizes any hotspot item (either PanoramaHotspot or ImperialMediaHotspot)
 * into a consistent PanoramaHotspot with guaranteed yaw and pitch.
 */
function normalizeHotspotItem(
  item: PanoramaHotspot | ImperialMediaHotspot
): PanoramaHotspot {
  if ("yaw" in item && typeof item.yaw === "number") {
    return {
      ...(item as PanoramaHotspot),
      yaw: normalizeAngle(item.yaw),
      pitch: clampPitch(item.pitch ?? 0, -90, 90),
    };
  }

  const mediaHotspot = item as ImperialMediaHotspot;
  const payload = mediaHotspot.position_payload;
  const yaw =
    typeof payload?.yaw === "number"
      ? payload.yaw
      : (mediaHotspot.u ?? 0.5) * 360 - 180;
  const pitch =
    typeof payload?.pitch === "number"
      ? payload.pitch
      : 90 - (mediaHotspot.v ?? 0.5) * 180;

  return {
    id: mediaHotspot.id,
    title: mediaHotspot.title,
    description: mediaHotspot.description,
    yaw: normalizeAngle(yaw),
    pitch: clampPitch(pitch, -90, 90),
    art_detail_slug: mediaHotspot.art_detail_slug,
    detail_id: mediaHotspot.detail_id,
    art_detail: mediaHotspot.art_detail,
    category: "art_detail",
  };
}

/**
 * Check if the browser environment supports WebGL.
 */
function isWebGLAvailable(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const canvas = document.createElement("canvas");
    return !!(
      window.WebGLRenderingContext &&
      (canvas.getContext("webgl2") ||
        canvas.getContext("webgl") ||
        canvas.getContext("experimental-webgl"))
    );
  } catch {
    return false;
  }
}

/**
 * Get standard Vietnamese cardinal direction for a given yaw angle.
 */
function getVietnameseHeading(deg: number): string {
  const directions = [
    "Bắc (N)",
    "Đông Bắc (NE)",
    "Đông (E)",
    "Đông Nam (SE)",
    "Nam (S)",
    "Tây Nam (SW)",
    "Tây (W)",
    "Tây Bắc (NW)",
  ];
  const normalized = normalizeAngle(deg, 0, 360);
  const idx = Math.round(normalized / 45) % 8;
  return directions[idx];
}

export function PanoramaViewer({
  src,
  title,
  subtitle,
  hotspots: rawHotspots = [],
  initialYaw = 0,
  initialPitch = 0,
  initialFov = 75,
  minFov = 35,
  maxFov = 95,
  className = "",
  onHotspotClick,
  onYawPitchChange,
  showControls = true,
  showCompass = true,
  autoRotate = false,
  autoRotateSpeed = 0.1,
  fallbackImageUrl,
}: PanoramaViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const hotspotElementsRef = useRef<Map<string, HTMLDivElement>>(new Map());

  // Normalized hotspots memo
  const hotspots: PanoramaHotspot[] = useMemo(() => {
    return rawHotspots.map(normalizeHotspotItem);
  }, [rawHotspots]);

  // WebGL & load state
  const [webGLSupported, setWebGLSupported] = useState(true);
  const [hasWebGLError, setHasWebGLError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Fullscreen state
  const [isFullscreen, setIsFullscreen] = useState(false);

  // View state for overlay UI
  const [currentYawDisplay, setCurrentYawDisplay] = useState(initialYaw);
  const [currentPitchDisplay, setCurrentPitchDisplay] = useState(initialPitch);
  const [currentFov, setCurrentFov] = useState(initialFov);

  // Art Detail Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeHotspot, setActiveHotspot] = useState<PanoramaHotspot | null>(null);

  // Refs for animation loop and interaction
  const stateRef = useRef({
    yaw: initialYaw,
    pitch: initialPitch,
    targetYaw: initialYaw,
    targetPitch: initialPitch,
    yawVelocity: 0,
    pitchVelocity: 0,
    fov: initialFov,
    isDragging: false,
    pointerStartX: 0,
    pointerStartY: 0,
    lastPointerX: 0,
    lastPointerY: 0,
    lastPointerTime: 0,
    pinchStartDistance: 0,
    initialPinchFov: initialFov,
    autoRotate,
  });

  // Keep autoRotate in sync with prop
  useEffect(() => {
    stateRef.current.autoRotate = autoRotate;
  }, [autoRotate]);

  // Detect WebGL support on initial mount
  useEffect(() => {
    if (!isWebGLAvailable()) {
      setWebGLSupported(false);
      setIsLoading(false);
    }
  }, []);

  // Handle Hotspot Click
  const handleHotspotClick = useCallback(
    (hotspot: PanoramaHotspot) => {
      setActiveHotspot(hotspot);
      setIsModalOpen(true);
      onHotspotClick?.(hotspot);
    },
    [onHotspotClick]
  );

  // Smooth control step actions
  const handleLookLeft = useCallback(() => {
    stateRef.current.targetYaw -= 20;
    stateRef.current.yawVelocity = 0;
  }, []);

  const handleLookRight = useCallback(() => {
    stateRef.current.targetYaw += 20;
    stateRef.current.yawVelocity = 0;
  }, []);

  const handleLookUp = useCallback(() => {
    stateRef.current.targetPitch = clampPitch(stateRef.current.targetPitch + 15);
    stateRef.current.pitchVelocity = 0;
  }, []);

  const handleLookDown = useCallback(() => {
    stateRef.current.targetPitch = clampPitch(stateRef.current.targetPitch - 15);
    stateRef.current.pitchVelocity = 0;
  }, []);

  const handleResetView = useCallback(() => {
    stateRef.current.targetYaw = initialYaw;
    stateRef.current.targetPitch = initialPitch;
    stateRef.current.fov = initialFov;
    stateRef.current.yawVelocity = 0;
    stateRef.current.pitchVelocity = 0;
    setCurrentFov(initialFov);
  }, [initialYaw, initialPitch, initialFov]);

  const handleZoomIn = useCallback(() => {
    const nextFov = Math.max(minFov, stateRef.current.fov - 10);
    stateRef.current.fov = nextFov;
    setCurrentFov(nextFov);
  }, [minFov]);

  const handleZoomOut = useCallback(() => {
    const nextFov = Math.min(maxFov, stateRef.current.fov + 10);
    stateRef.current.fov = nextFov;
    setCurrentFov(nextFov);
  }, [maxFov]);

  // Fullscreen handler
  const toggleFullscreen = useCallback(() => {
    if (!containerRef.current) return;

    if (!document.fullscreenElement) {
      containerRef.current
        .requestFullscreen()
        .then(() => setIsFullscreen(true))
        .catch(() => {});
    } else {
      document
        .exitFullscreen()
        .then(() => setIsFullscreen(false))
        .catch(() => {});
    }
  }, []);

  // Listen to fullscreenchange
  useEffect(() => {
    const onFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener("fullscreenchange", onFullscreenChange);
    return () => {
      document.removeEventListener("fullscreenchange", onFullscreenChange);
    };
  }, []);

  // Three.js Scene, Camera, Texture, and Render Loop
  useEffect(() => {
    if (!webGLSupported || hasWebGLError) return;
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    let renderer: THREE.WebGLRenderer | null = null;
    let scene: THREE.Scene | null = null;
    let camera: THREE.PerspectiveCamera | null = null;
    let sphereMesh: THREE.Mesh | null = null;
    let texture: THREE.Texture | null = null;
    let animationFrameId: number | null = null;
    let isDisposed = false;

    try {
      const gl =
        canvas.getContext("webgl2") ||
        canvas.getContext("webgl") ||
        canvas.getContext("experimental-webgl");
      if (!gl) {
        setHasWebGLError(true);
        setIsLoading(false);
        return;
      }
    } catch {
      setHasWebGLError(true);
      setIsLoading(false);
      return;
    }

    try {
      // 1. Initialize WebGLRenderer
      renderer = new THREE.WebGLRenderer({
        canvas,
        antialias: true,
        alpha: false,
        powerPreference: "high-performance",
      });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

      const rect = container.getBoundingClientRect();
      const width = Math.max(1, rect.width);
      const height = Math.max(1, rect.height);
      renderer.setSize(width, height);

      // 2. Initialize Scene
      scene = new THREE.Scene();

      // 3. Initialize Camera
      camera = new THREE.PerspectiveCamera(
        stateRef.current.fov,
        width / height,
        0.1,
        1500
      );
      camera.position.set(0, 0, 0);

      // 4. Create Equirectangular Sphere Geometry with inverted normals
      // SphereGeometry with negative X scale flips texture so it is viewed correctly from inside
      const geometry = new THREE.SphereGeometry(DEFAULT_SPHERE_RADIUS, 64, 40);
      geometry.scale(-1, 1, 1);

      // 5. Load Texture with Three.js TextureLoader
      setIsLoading(true);
      setErrorMessage(null);

      const textureLoader = new THREE.TextureLoader();
      textureLoader.load(
        src,
        (loadedTexture) => {
          if (isDisposed || !scene) return;
          loadedTexture.colorSpace = THREE.SRGBColorSpace;
          loadedTexture.minFilter = THREE.LinearFilter;
          loadedTexture.generateMipmaps = false;
          texture = loadedTexture;

          const material = new THREE.MeshBasicMaterial({
            map: loadedTexture,
            side: THREE.DoubleSide,
            toneMapped: false,
          });

          sphereMesh = new THREE.Mesh(geometry, material);
          scene.add(sphereMesh);
          setIsLoading(false);
        },
        undefined,
        (err) => {
          if (isDisposed) return;
          console.error("Panorama texture loading error:", err);
          setErrorMessage("Không thể tải ảnh toàn cảnh 360°.");
          setHasWebGLError(true);
          setIsLoading(false);
        }
      );

      // 6. Project Hotspots to 2D Screen Space each frame
      const updateHotspotOverlays = (
        currentCamera: THREE.PerspectiveCamera,
        viewWidth: number,
        viewHeight: number
      ) => {
        for (const hp of hotspots) {
          const domEl = hotspotElementsRef.current.get(hp.id);
          if (!domEl) continue;

          const cartesian = sphericalToCartesian(
            hp.yaw,
            hp.pitch,
            DEFAULT_SPHERE_RADIUS
          );
          const screenPos = cartesianToScreen(
            cartesian,
            currentCamera as any,
            viewWidth,
            viewHeight
          );

          if (screenPos.isVisible) {
            domEl.style.display = "block";
            domEl.style.transform = `translate3d(${screenPos.x}px, ${screenPos.y}px, 0)`;
          } else {
            domEl.style.display = "none";
          }
        }
      };

      // 7. Animation / Render Loop with Inertial Damping
      let lastFrameTime = performance.now();
      let lastReportedYaw = initialYaw;
      let lastReportedPitch = initialPitch;

      const renderLoop = (time: number) => {
        if (isDisposed) return;

        const deltaTime = Math.min((time - lastFrameTime) / 1000, 0.1);
        lastFrameTime = time;

        const state = stateRef.current;

        // Auto-rotation when not dragging
        if (state.autoRotate && !state.isDragging && Math.abs(state.yawVelocity) < 0.01) {
          state.targetYaw += autoRotateSpeed;
        }

        // Inertial glide decay when not dragging
        if (!state.isDragging) {
          if (Math.abs(state.yawVelocity) > 0.0005) {
            state.targetYaw += state.yawVelocity;
            state.yawVelocity *= 0.92;
          } else {
            state.yawVelocity = 0;
          }

          if (Math.abs(state.pitchVelocity) > 0.0005) {
            state.targetPitch = clampPitch(state.targetPitch + state.pitchVelocity);
            state.pitchVelocity *= 0.92;
          } else {
            state.pitchVelocity = 0;
          }
        }

        // Smooth interpolation towards target angles
        const lerpFactor = Math.min(1, 14 * deltaTime);
        state.yaw += (state.targetYaw - state.yaw) * lerpFactor;
        state.pitch += (state.targetPitch - state.pitch) * lerpFactor;
        state.pitch = clampPitch(state.pitch);

        // Normalize yaw smoothly
        if (Math.abs(state.yaw) > 360) {
          state.yaw = normalizeAngle(state.yaw);
          state.targetYaw = normalizeAngle(state.targetYaw);
        }

        // Update Camera Field of View
        if (camera && Math.abs(camera.fov - state.fov) > 0.01) {
          camera.fov = state.fov;
          camera.updateProjectionMatrix();
        }

        // Orient Camera according to yaw & pitch
        if (camera) {
          const targetPoint = sphericalToCartesian(
            state.yaw,
            state.pitch,
            DEFAULT_SPHERE_RADIUS
          );
          camera.lookAt(targetPoint.x, targetPoint.y, targetPoint.z);
          camera.updateMatrixWorld();
        }

        // Render Three.js Scene
        if (renderer && scene && camera) {
          renderer.render(scene, camera);

          // Update Hotspot Screen Positions
          const curRect = container.getBoundingClientRect();
          updateHotspotOverlays(camera, curRect.width, curRect.height);
        }

        // Update React Display State periodically
        if (
          Math.abs(state.yaw - lastReportedYaw) > 0.5 ||
          Math.abs(state.pitch - lastReportedPitch) > 0.5
        ) {
          lastReportedYaw = state.yaw;
          lastReportedPitch = state.pitch;
          setCurrentYawDisplay(Math.round(normalizeAngle(state.yaw)));
          setCurrentPitchDisplay(Math.round(state.pitch));
          onYawPitchChange?.(state.yaw, state.pitch);
        }

        animationFrameId = requestAnimationFrame(renderLoop);
      };

      animationFrameId = requestAnimationFrame(renderLoop);

      // 8. Resize Observer
      const resizeObserver = new ResizeObserver((entries) => {
        for (const entry of entries) {
          const { width: newWidth, height: newHeight } = entry.contentRect;
          if (newWidth > 0 && newHeight > 0 && renderer && camera) {
            renderer.setSize(newWidth, newHeight);
            camera.aspect = newWidth / newHeight;
            camera.updateProjectionMatrix();
          }
        }
      });
      resizeObserver.observe(container);

      // 9. Pointer Drag & Touch Handling with Inertial Velocity Tracking
      const onPointerDown = (e: PointerEvent) => {
        // Ignore clicks directly on UI control overlays
        if ((e.target as HTMLElement).closest(".panorama-control-overlay")) return;

        stateRef.current.isDragging = true;
        stateRef.current.pointerStartX = e.clientX;
        stateRef.current.pointerStartY = e.clientY;
        stateRef.current.lastPointerX = e.clientX;
        stateRef.current.lastPointerY = e.clientY;
        stateRef.current.lastPointerTime = performance.now();
        stateRef.current.yawVelocity = 0;
        stateRef.current.pitchVelocity = 0;

        try {
          canvas.setPointerCapture(e.pointerId);
        } catch {
          // ignore pointer capture exceptions on older browsers
        }
      };

      const onPointerMove = (e: PointerEvent) => {
        if (!stateRef.current.isDragging) return;

        const now = performance.now();
        const dt = Math.max(1, now - stateRef.current.lastPointerTime);

        const deltaX = e.clientX - stateRef.current.lastPointerX;
        const deltaY = e.clientY - stateRef.current.lastPointerY;

        stateRef.current.lastPointerX = e.clientX;
        stateRef.current.lastPointerY = e.clientY;
        stateRef.current.lastPointerTime = now;

        // Rotational sensitivity based on current FOV
        const sensitivity = (stateRef.current.fov / 75) * 0.16;

        const stepYaw = -deltaX * sensitivity;
        const stepPitch = deltaY * sensitivity;

        stateRef.current.targetYaw += stepYaw;
        stateRef.current.targetPitch = clampPitch(
          stateRef.current.targetPitch + stepPitch
        );

        // Track velocity with exponential smoothing for inertial flick
        const instVelocityX = (-deltaX * sensitivity) / (dt / 16.6);
        const instVelocityY = (deltaY * sensitivity) / (dt / 16.6);

        stateRef.current.yawVelocity =
          stateRef.current.yawVelocity * 0.3 + instVelocityX * 0.7;
        stateRef.current.pitchVelocity =
          stateRef.current.pitchVelocity * 0.3 + instVelocityY * 0.7;
      };

      const onPointerUp = (e: PointerEvent) => {
        stateRef.current.isDragging = false;
        try {
          canvas.releasePointerCapture(e.pointerId);
        } catch {
          // ignore
        }
      };

      // Mouse Wheel Zoom
      const onWheel = (e: WheelEvent) => {
        e.preventDefault();
        const zoomDelta = e.deltaY > 0 ? 4 : -4;
        const nextFov = Math.max(
          minFov,
          Math.min(maxFov, stateRef.current.fov + zoomDelta)
        );
        stateRef.current.fov = nextFov;
        setCurrentFov(nextFov);
      };

      // Touch Pinch-to-zoom
      const onTouchStart = (e: TouchEvent) => {
        if (e.touches.length === 2) {
          const dx = e.touches[0].clientX - e.touches[1].clientX;
          const dy = e.touches[0].clientY - e.touches[1].clientY;
          stateRef.current.pinchStartDistance = Math.hypot(dx, dy);
          stateRef.current.initialPinchFov = stateRef.current.fov;
        }
      };

      const onTouchMove = (e: TouchEvent) => {
        if (e.touches.length === 2) {
          e.preventDefault();
          const dx = e.touches[0].clientX - e.touches[1].clientX;
          const dy = e.touches[0].clientY - e.touches[1].clientY;
          const currentDistance = Math.hypot(dx, dy);
          const diff = currentDistance - stateRef.current.pinchStartDistance;

          const nextFov = Math.max(
            minFov,
            Math.min(
              maxFov,
              stateRef.current.initialPinchFov - diff * 0.15
            )
          );
          stateRef.current.fov = nextFov;
          setCurrentFov(nextFov);
        }
      };

      // Attach events
      canvas.addEventListener("pointerdown", onPointerDown);
      canvas.addEventListener("pointermove", onPointerMove);
      canvas.addEventListener("pointerup", onPointerUp);
      canvas.addEventListener("pointercancel", onPointerUp);
      canvas.addEventListener("wheel", onWheel, { passive: false });
      canvas.addEventListener("touchstart", onTouchStart, { passive: true });
      canvas.addEventListener("touchmove", onTouchMove, { passive: false });

      // Cleanup
      return () => {
        isDisposed = true;
        if (animationFrameId !== null) {
          cancelAnimationFrame(animationFrameId);
        }
        resizeObserver.disconnect();

        canvas.removeEventListener("pointerdown", onPointerDown);
        canvas.removeEventListener("pointermove", onPointerMove);
        canvas.removeEventListener("pointerup", onPointerUp);
        canvas.removeEventListener("pointercancel", onPointerUp);
        canvas.removeEventListener("wheel", onWheel);
        canvas.removeEventListener("touchstart", onTouchStart);
        canvas.removeEventListener("touchmove", onTouchMove);

        geometry.dispose();
        if (sphereMesh) {
          if (Array.isArray(sphereMesh.material)) {
            sphereMesh.material.forEach((m) => m.dispose());
          } else {
            sphereMesh.material.dispose();
          }
        }
        if (texture) {
          texture.dispose();
        }
        if (renderer) {
          renderer.dispose();
        }
      };
    } catch (err) {
      console.error("Three.js WebGL initialization failure:", err);
      setHasWebGLError(true);
      setIsLoading(false);
    }
  }, [
    src,
    webGLSupported,
    hasWebGLError,
    initialYaw,
    initialPitch,
    initialFov,
    minFov,
    maxFov,
    autoRotate,
    autoRotateSpeed,
    hotspots,
    onYawPitchChange,
  ]);

  // Graceful Fallback Mode: When WebGL is unavailable or fails
  if (!webGLSupported || hasWebGLError) {
    const staticImage = fallbackImageUrl || src;

    return (
      <div
        className={`flex flex-col bg-card rounded-2xl border border-border shadow-md overflow-hidden ${className}`}
        role="region"
        aria-roledescription="toàn cảnh 360 độ"
        aria-label={title || "Toàn cảnh 360 độ"}
      >
        {/* Fallback Notice Banner */}
        <div className="flex items-center justify-between gap-3 px-4 py-3 bg-amber-500/10 border-b border-amber-500/30 text-amber-900 dark:text-amber-200 text-xs">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
            <span>
              <strong>Chế độ toàn cảnh trải phẳng:</strong> WebGL 3D không khả dụng. Hiển thị hình ảnh toàn cảnh tĩnh với đầy đủ điểm khảo sát và nội dung tư liệu.
            </span>
          </div>
          <Button
            size="sm"
            variant="outline"
            className="h-7 text-xs border-amber-500/40 hover:bg-amber-500/20"
            onClick={() => {
              setHasWebGLError(false);
              setWebGLSupported(true);
            }}
          >
            <RefreshCw className="w-3 h-3 mr-1" />
            Thử lại 3D
          </Button>
        </div>

        {/* Static High-Res Panoramic Strip with Interactive Hotspots */}
        <div className="relative w-full overflow-x-auto overflow-y-hidden bg-black py-2 scrollbar-thin">
          <div className="relative min-w-[900px] w-full aspect-[2/1] max-h-[480px]">
            <img
              src={staticImage}
              alt={title || "Toàn cảnh di sản Huế"}
              className="w-full h-full object-cover"
            />

            {/* Hotspot Pins at Static UV coordinates */}
            {hotspots.map((hp, idx) => {
              const { u, v } = sphericalToUV(hp.yaw, hp.pitch);
              return (
                <div
                  key={hp.id}
                  className="absolute -translate-x-1/2 -translate-y-1/2 group"
                  style={{
                    left: `${u * 100}%`,
                    top: `${v * 100}%`,
                  }}
                >
                  <button
                    type="button"
                    onClick={() => handleHotspotClick(hp)}
                    className="relative flex items-center justify-center w-7 h-7 rounded-full bg-amber-500 text-slate-950 font-bold shadow-lg border-2 border-white ring-2 ring-black/50 hover:scale-125 transition-transform"
                    aria-label={`Điểm ${idx + 1}: ${hp.title}`}
                  >
                    <span className="text-[11px]">{idx + 1}</span>
                  </button>
                  <span className="sr-only">{hp.title}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Accessible List of Hotspots and Historical Descriptions */}
        <div className="p-4 sm:p-6 space-y-4 bg-card">
          <div className="flex items-center justify-between">
            <h3 className="font-serif font-bold text-base sm:text-lg text-foreground flex items-center gap-2">
              <MapPin className="w-4 h-4 text-amber-500" />
              Điểm quan sát trong toàn cảnh ({hotspots.length})
            </h3>
            {title && (
              <span className="text-xs text-muted-foreground font-medium">
                {title}
              </span>
            )}
          </div>

          {hotspots.length === 0 ? (
            <p className="text-sm text-muted-foreground italic">
              Chưa có điểm quan sát nào được ghim trên toàn cảnh này.
            </p>
          ) : (
            <ol className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {hotspots.map((hp, idx) => (
                <li
                  key={hp.id}
                  className="flex flex-col justify-between p-3.5 rounded-xl border border-border/80 bg-muted/30 hover:border-amber-500/50 hover:bg-muted/60 transition-colors"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2">
                      <span className="flex items-center justify-center w-5 h-5 rounded-full bg-amber-500 text-slate-950 font-bold text-xs">
                        {idx + 1}
                      </span>
                      <h4 className="font-semibold text-sm text-foreground">
                        {hp.title}
                      </h4>
                    </div>
                    {hp.description && (
                      <p className="text-xs text-muted-foreground line-clamp-3">
                        {hp.description}
                      </p>
                    )}
                  </div>

                  <div className="mt-3 pt-2 border-t border-border/50 flex items-center justify-between text-xs">
                    <span className="text-[11px] text-muted-foreground">
                      Góc nhìn: {hp.yaw}° ({getVietnameseHeading(hp.yaw)})
                    </span>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-7 text-xs text-primary hover:text-primary hover:bg-primary/10 px-2"
                      onClick={() => handleHotspotClick(hp)}
                    >
                      <Eye className="w-3.5 h-3.5 mr-1" />
                      Xem chi tiết
                    </Button>
                  </div>
                </li>
              ))}
            </ol>
          )}
        </div>

        {/* Modal for Art Details */}
        <ArtDetailModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          artDetail={activeHotspot?.art_detail}
          detailSlug={activeHotspot?.art_detail_slug || activeHotspot?.detail_id}
        />
      </div>
    );
  }

  // Interactive 360° Three.js Panorama Viewer
  return (
    <div
      ref={containerRef}
      className={`relative w-full rounded-2xl border border-border shadow-lg overflow-hidden bg-black select-none ${
        isFullscreen ? "fixed inset-0 z-50 rounded-none border-none" : ""
      } ${className}`}
      style={{
        aspectRatio: isFullscreen ? undefined : "16 / 9",
        minHeight: isFullscreen ? "100vh" : "400px",
      }}
      role="region"
      aria-roledescription="toàn cảnh 360 độ tương tác"
      aria-label={title || "Toàn cảnh tương tác 360 độ"}
    >
      {/* Three.js Rendering Canvas */}
      <canvas
        ref={canvasRef}
        className="w-full h-full block cursor-grab active:cursor-grabbing outline-none"
        tabIndex={0}
        aria-label="Khung hình toàn cảnh 360 độ. Dùng chuột hoặc chạm để xoay góc nhìn."
      />

      {/* Loading Overlay */}
      {isLoading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/75 backdrop-blur-sm z-30 space-y-3 text-white">
          <div className="w-8 h-8 rounded-full border-2 border-amber-400 border-t-transparent animate-spin" />
          <p className="text-xs font-medium tracking-wide text-zinc-300">
            Đang tải không gian toàn cảnh 360°...
          </p>
        </div>
      )}

      {/* Error Overlay */}
      {errorMessage && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/85 z-30 p-6 text-center text-white space-y-3">
          <AlertCircle className="w-8 h-8 text-rose-400" />
          <p className="text-sm text-zinc-200">{errorMessage}</p>
          <Button
            size="sm"
            variant="secondary"
            onClick={() => setHasWebGLError(true)}
          >
            Chuyển sang chế độ trải phẳng
          </Button>
        </div>
      )}

      {/* Interactive 3D -> 2D Projected Hotspots Layer */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden z-20">
        {hotspots.map((hp) => (
          <div
            key={hp.id}
            ref={(el) => {
              if (el) {
                hotspotElementsRef.current.set(hp.id, el);
              } else {
                hotspotElementsRef.current.delete(hp.id);
              }
            }}
            className="absolute top-0 left-0 -translate-x-1/2 -translate-y-1/2 pointer-events-auto will-change-transform"
            style={{ display: "none" }}
          >
            <TooltipProvider delayDuration={150}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleHotspotClick(hp);
                    }}
                    className="relative flex items-center justify-center w-8 h-8 rounded-full bg-amber-500 text-slate-950 font-bold shadow-xl border-2 border-white ring-2 ring-black/40 hover:scale-125 transition-transform focus:outline-none focus:ring-4 focus:ring-amber-400"
                    aria-label={`Điểm quan sát: ${hp.title}`}
                  >
                    {/* Pulsing beacon ring */}
                    <span className="absolute -inset-2 rounded-full bg-amber-400/35 animate-ping duration-1000 pointer-events-none" />
                    <Sparkles className="w-4 h-4 text-slate-950" />
                  </button>
                </TooltipTrigger>
                <TooltipContent
                  side="top"
                  sideOffset={8}
                  className="bg-card/95 backdrop-blur text-foreground border border-border shadow-2xl p-3 max-w-xs space-y-1"
                >
                  <div className="font-semibold text-xs text-primary flex items-center gap-1.5">
                    <Eye className="w-3.5 h-3.5" />
                    {hp.title}
                  </div>
                  {hp.description && (
                    <p className="text-[11px] text-muted-foreground line-clamp-2">
                      {hp.description}
                    </p>
                  )}
                  <div className="text-[10px] text-amber-600 dark:text-amber-400 font-medium pt-0.5">
                    Nhấn để xem câu chuyện & chi tiết mỹ thuật →
                  </div>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        ))}
      </div>

      {/* Top Banner: Title & Compass Heading */}
      <div className="panorama-control-overlay absolute top-3 left-3 right-3 flex items-center justify-between gap-2 pointer-events-none z-20">
        {/* Title or Branding badge */}
        <div className="flex items-center gap-2 rounded-full bg-black/60 backdrop-blur-md px-3.5 py-1.5 text-xs font-medium text-white border border-white/15 pointer-events-auto">
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
          <span className="font-semibold truncate max-w-[200px] sm:max-w-xs">
            {title || "Toàn cảnh 360° Đại Nội Huế"}
          </span>
          {subtitle && (
            <span className="hidden sm:inline text-white/60 text-[11px] border-l border-white/20 pl-2">
              {subtitle}
            </span>
          )}
        </div>

        {/* Compass & Heading */}
        {showCompass && (
          <div className="flex items-center gap-2 rounded-full bg-black/60 backdrop-blur-md px-3 py-1.5 text-xs text-white border border-white/15 pointer-events-auto">
            <Compass
              className="w-4 h-4 text-amber-400 transition-transform duration-75"
              style={{ transform: `rotate(${-currentYawDisplay}deg)` }}
            />
            <span className="font-medium text-[11px]">
              {getVietnameseHeading(currentYawDisplay)}
            </span>
            <span className="text-white/50 text-[10px]">
              ({currentYawDisplay}°)
            </span>
          </div>
        )}
      </div>

      {/* Floating Interactive Controls (Left/Right/Up/Down, Zoom, Reset, Fullscreen) */}
      {showControls && (
        <div className="panorama-control-overlay absolute bottom-4 right-4 flex items-center gap-1.5 bg-black/70 backdrop-blur-md p-1.5 rounded-xl border border-white/15 text-white z-20 shadow-2xl">
          {/* Directional Navigation */}
          <div className="grid grid-cols-3 gap-0.5 pr-1 border-r border-white/15">
            <div />
            <Button
              size="icon"
              variant="ghost"
              onClick={handleLookUp}
              className="w-7 h-7 text-white hover:bg-white/20"
              title="Nhìn lên (Look up)"
              aria-label="Nhìn lên"
            >
              <ChevronUp className="w-4 h-4" />
            </Button>
            <div />
            <Button
              size="icon"
              variant="ghost"
              onClick={handleLookLeft}
              className="w-7 h-7 text-white hover:bg-white/20"
              title="Nhìn sang trái (Look left)"
              aria-label="Nhìn sang trái"
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <Button
              size="icon"
              variant="ghost"
              onClick={handleResetView}
              className="w-7 h-7 text-amber-400 hover:bg-white/20"
              title="Đặt lại góc nhìn (Reset view)"
              aria-label="Đặt lại góc nhìn"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </Button>
            <Button
              size="icon"
              variant="ghost"
              onClick={handleLookRight}
              className="w-7 h-7 text-white hover:bg-white/20"
              title="Nhìn sang phải (Look right)"
              aria-label="Nhìn sang phải"
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
            <div />
            <Button
              size="icon"
              variant="ghost"
              onClick={handleLookDown}
              className="w-7 h-7 text-white hover:bg-white/20"
              title="Nhìn xuống (Look down)"
              aria-label="Nhìn xuống"
            >
              <ChevronDown className="w-4 h-4" />
            </Button>
            <div />
          </div>

          {/* Zoom In & Out */}
          <Button
            size="icon"
            variant="ghost"
            onClick={handleZoomIn}
            disabled={currentFov <= minFov}
            className="w-7 h-7 text-white hover:bg-white/20 disabled:opacity-30"
            title="Phóng to"
            aria-label="Phóng to"
          >
            <Plus className="w-4 h-4" />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            onClick={handleZoomOut}
            disabled={currentFov >= maxFov}
            className="w-7 h-7 text-white hover:bg-white/20 disabled:opacity-30"
            title="Thu nhỏ"
            aria-label="Thu nhỏ"
          >
            <Minus className="w-4 h-4" />
          </Button>

          {/* Fullscreen Toggle */}
          <Button
            size="icon"
            variant="ghost"
            onClick={toggleFullscreen}
            className="w-7 h-7 text-white hover:bg-white/20 ml-0.5 border-l border-white/15 pl-1"
            title={isFullscreen ? "Thoát toàn màn hình" : "Toàn màn hình"}
            aria-label={isFullscreen ? "Thoát toàn màn hình" : "Toàn màn hình"}
          >
            {isFullscreen ? (
              <Minimize2 className="w-3.5 h-3.5" />
            ) : (
              <Maximize2 className="w-3.5 h-3.5" />
            )}
          </Button>
        </div>
      )}

      {/* Helpful Gesture Hint for First-time Users */}
      <div className="panorama-control-overlay pointer-events-none absolute bottom-4 left-4 rounded-full bg-black/50 backdrop-blur px-3 py-1 text-[11px] text-zinc-300 border border-white/10 hidden sm:block">
        Kéo để xoay góc nhìn 360° · Cuộn chuột hoặc chụm ngón tay để thu phóng
      </div>

      {/* Art Detail Modal */}
      <ArtDetailModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        artDetail={activeHotspot?.art_detail}
        detailSlug={activeHotspot?.art_detail_slug || activeHotspot?.detail_id}
      />
    </div>
  );
}

export default PanoramaViewer;
