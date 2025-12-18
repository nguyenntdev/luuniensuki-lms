"use client";

import { Component, Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls, useCursor, useGLTF, Html, useProgress } from "@react-three/drei";
import * as THREE from "three";
import Link from "next/link";
import { Eye } from "lucide-react";

import { getUrnDetail } from "@/lib/api";
import { useMotifStore } from "@/stores/motifStore";
import LessonSidebar from "@/components/LessonSidebar";

// WebGL Error Boundary
class WebGLErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("WebGL Error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="absolute inset-0 flex items-center justify-center bg-background">
          <div className="max-w-md p-8 text-center">
            <div className="mb-4 text-6xl">⚠️</div>
            <h2 className="mb-4 text-xl font-display font-bold text-foreground">
              WebGL Không Khả Dụng
            </h2>
            <p className="mb-6 text-sm text-muted-foreground">
              Trình duyệt của bạn không hỗ trợ WebGL hoặc WebGL đã bị tắt.
              Vui lòng bật WebGL trong cài đặt trình duyệt hoặc sử dụng trình duyệt khác
              (Chrome, Firefox, Edge) để xem mô hình 3D.
            </p>
            <div className="space-y-2">
              <Link
                href="/explore"
                className="block w-full py-2 px-4 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
              >
                Quay Lại Khám Phá
              </Link>
              <Link
                href="/collection"
                className="block w-full py-2 px-4 bg-muted text-foreground rounded-lg text-sm font-medium hover:bg-muted/80 transition-colors"
              >
                Xem Bộ Sưu Tập
              </Link>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Loading component that shows progress
function Loader() {
  const { progress } = useProgress();
  return (
    <Html center>
      <div className="flex flex-col items-center gap-2 text-foreground">
        <div className="w-32 h-2 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className="font-display tabular-nums text-sm">{progress.toFixed(0)}%</span>
      </div>
    </Html>
  );
}

// Camera controller for smooth animation
function CameraController({ targetPosition, enabled }) {
  const { camera, controls } = useThree();
  const targetRef = useRef(new THREE.Vector3());
  const isAnimating = useRef(false);

  useEffect(() => {
    if (targetPosition && enabled) {
      // Calculate camera position: offset from target
      const offset = new THREE.Vector3(0.8, 0.5, 1.2);
      targetRef.current.set(
        targetPosition[0] + offset.x,
        targetPosition[1] + offset.y,
        targetPosition[2] + offset.z
      );
      isAnimating.current = true;
    }
  }, [targetPosition, enabled]);

  useFrame(() => {
    if (!isAnimating.current) return;

    const currentPos = camera.position;
    const target = targetRef.current;

    // Smooth lerp towards target
    currentPos.lerp(target, 0.05);

    // Stop animating when close enough
    if (currentPos.distanceTo(target) < 0.01) {
      isAnimating.current = false;
    }
  });

  return null;
}

function HotspotTooltip({ label }) {
  if (!label) return null;

  return (
    <div className="pointer-events-none select-none whitespace-nowrap rounded-md border border-border bg-popover/95 px-2 py-1 text-xs font-medium text-popover-foreground shadow-md">
      {label}
    </div>
  );
}

function FallbackScene({ motifs, foundByMotifId, showHints, onClickMesh, hotspotScale = 1 }) {
  // Render a simple "urn" + clickable spheres (so the app works even without GLB assets).
  const [hoveredMotifId, setHoveredMotifId] = useState(null);
  const hotspotRadius = 0.12 * hotspotScale;

  return (
    <group>
      <mesh position={[0, 0, 0]} receiveShadow>
        <cylinderGeometry args={[0.7, 0.9, 1.6, 32]} />
        <meshStandardMaterial color="#2b2b2b" />
      </mesh>

      {motifs.map((motif, idx) => {
        const unlocked = Boolean(foundByMotifId[motif.id]);
        const angle = (idx / Math.max(1, motifs.length)) * Math.PI * 2;
        const radius = 1.2;
        const x = Math.cos(angle) * radius;
        const z = Math.sin(angle) * radius;
        const y = 0.3 + (idx % 3) * 0.25;

        const color = unlocked ? "#318265" : "#d9a521";
        const opacity = showHints ? 0.8 : (unlocked ? 0.35 : 0);
        const emissiveIntensity = showHints ? 0.7 : (unlocked ? 0.3 : 0);

        return (
          <mesh
            key={motif.id}
            name={motif.mesh_name}
            position={[x, y, z]}
            onClick={onClickMesh}
            onPointerOver={(e) => {
              e.stopPropagation();
              setHoveredMotifId(motif.id);
            }}
	            onPointerOut={() => setHoveredMotifId(null)}
	            castShadow
	          >
	            <sphereGeometry args={[hotspotRadius, 16, 16]} />
	            <meshStandardMaterial
	              color={color}
	              transparent
	              opacity={opacity}
	              emissive={color}
	              emissiveIntensity={emissiveIntensity}
	              depthWrite={false}
	            />
	            {hoveredMotifId === motif.id && !unlocked && motif?.name && (
	              <Html
	                position={[0, hotspotRadius + 0.16, 0]}
	                center
	                zIndexRange={[200, 0]}
	                style={{ pointerEvents: "none" }}
	              >
	                <HotspotTooltip label={motif.name} />
              </Html>
            )}
          </mesh>
        );
      })}
    </group>
  );
}

class ModelErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error) {
    if (this.props.onError) this.props.onError(error);
  }

  render() {
    if (this.state.hasError) return this.props.fallback;
    return this.props.children;
  }
}

// Individual hotspot with hover state - invisible by default, glow on hover
function Hotspot({ motif, unlocked, showHints, position, hotspotRadius, onClickMesh }) {
  const [hovered, setHovered] = useState(false);
  useCursor(hovered);

  const shouldPulse = showHints && !unlocked;

  const color = unlocked ? "#318265" : "#d9a521"; // jade / gold
  let opacity = showHints ? 0.7 : (unlocked ? 0.35 : 0);
  let emissiveIntensity = showHints ? 0.55 : (unlocked ? 0.3 : 0);

  if (shouldPulse) {
    opacity = 0.6;
  }

  if (hovered) {
    opacity = showHints ? 0.85 : 0.55;
    emissiveIntensity = showHints ? 0.9 : 0.8;
  }

  return (
    <mesh
      name={motif.mesh_name}
      position={position}
      onClick={onClickMesh}
      onPointerOver={(e) => {
        e.stopPropagation();
        setHovered(true);
      }}
      onPointerOut={() => setHovered(false)}
    >
      <sphereGeometry args={[hotspotRadius, 24, 24]} />
      <meshStandardMaterial
        color={color}
        transparent
        opacity={opacity}
        emissive={color}
        emissiveIntensity={emissiveIntensity}
        depthWrite={false}
      />
      {shouldPulse && (
        <Html
          position={[0, 0, 0]}
          center
          zIndexRange={[150, 0]}
          style={{ pointerEvents: "none" }}
        >
          <div className="relative h-5 w-5">
            <div className="absolute inset-0 rounded-full bg-primary/25 ring-2 ring-primary/50 opacity-60 animate-hotspot-pulse" />
          </div>
        </Html>
      )}
      {hovered && !unlocked && motif?.name && (
        <Html
          position={[0, hotspotRadius + 0.18, 0]}
          center
          zIndexRange={[200, 0]}
          style={{ pointerEvents: "none" }}
        >
          <HotspotTooltip label={motif.name} />
        </Html>
      )}
    </mesh>
  );
}

function HotspotRing({ motifs, foundByMotifId, showHints, onClickMesh, radius, baseY, levelStep, hotspotScale = 1 }) {
  return (
    <group>
      {motifs.map((motif, idx) => {
        const unlocked = Boolean(foundByMotifId[motif.id]);

        // Use DB positions if available (non-zero), otherwise fallback to circular formula
        const hasDbPosition = motif.pos_x !== 0 || motif.pos_y !== 0 || motif.pos_z !== 0;
        let x, y, z;
        let hotspotRadius = 0.12; // Larger default for visibility

        if (hasDbPosition) {
          x = motif.pos_x;
          y = motif.pos_y;
          z = motif.pos_z;
          hotspotRadius = Math.max(motif.bounding_radius || 0.12, 0.08);
        } else {
          // Fallback: circular formula
          const angle = (idx / Math.max(1, motifs.length)) * Math.PI * 2;
          x = Math.cos(angle) * radius;
          z = Math.sin(angle) * radius;
          y = baseY + (idx % 3) * levelStep;
        }

        hotspotRadius *= hotspotScale;
        return (
          <Hotspot
            key={motif.id}
            motif={motif}
            unlocked={unlocked}
            showHints={showHints}
            position={[x, y, z]}
            hotspotRadius={hotspotRadius}
            onClickMesh={onClickMesh}
          />
        );
      })}
    </group>
  );
}

function UrnModel({ url, motifs, foundByMotifId, showHints, onClickMesh, hotspotScale }) {
  const gltf = useGLTF(url);

  const fit = useMemo(() => {
    const box = new THREE.Box3().setFromObject(gltf.scene);
    const size = new THREE.Vector3();
    const center = new THREE.Vector3();
    box.getSize(size);
    box.getCenter(center);

    const maxDim = Math.max(size.x, size.y, size.z);
    const scale = maxDim > 0 ? 2.4 / maxDim : 1;
    const scaledSize = size.clone().multiplyScalar(scale);

    return {
      center,
      scale,
      radius: (Math.max(scaledSize.x, scaledSize.z) * 0.62 + 0.2) / Math.max(1e-6, scale),
      baseY: (-scaledSize.y * 0.35) / Math.max(1e-6, scale),
      levelStep: Math.max(0.15, scaledSize.y * 0.15) / Math.max(1e-6, scale),
    };
  }, [gltf]);

  useEffect(() => {
    gltf.scene.traverse((obj) => {
      if (obj && obj.isMesh) {
        obj.castShadow = true;
        obj.receiveShadow = true;
      }
    });
  }, [gltf]);

  return (
    <group scale={fit.scale} position={fit.center.clone().multiplyScalar(-fit.scale)}>
      <primitive object={gltf.scene} onClick={onClickMesh} />
	      <HotspotRing
	        motifs={motifs}
	        foundByMotifId={foundByMotifId}
	        showHints={showHints}
	        onClickMesh={onClickMesh}
	        radius={fit.radius}
	        baseY={fit.baseY}
	        levelStep={fit.levelStep}
	        hotspotScale={hotspotScale}
	      />
	    </group>
	  );
}

export default function UrnViewer({ urnSlug, userId, className = "h-full w-full" }) {
  const ensureMotifsLoaded = useMotifStore((s) => s.ensureMotifsLoaded);
  const motifsByMesh = useMotifStore((s) => s.motifsByMesh);
  const motifsById = useMotifStore((s) => s.motifsById);
  const foundByMotifId = useMotifStore((s) => s.foundByMotifId);
  const setSelectedMotifId = useMotifStore((s) => s.setSelectedMotifId);
  const selectedMotifId = useMotifStore((s) => s.selectedMotifId);
  const unlockFromClick = useMotifStore((s) => s.unlockFromClick);

  const [hovered, setHovered] = useState(false);
  useCursor(hovered);

	  const [showHints, setShowHints] = useState(false);
	  const [modelUrl, setModelUrl] = useState(null);
	  const controlsRef = useRef();
	  const containerRef = useRef(null);

	  const [isTouchDevice, setIsTouchDevice] = useState(false);
	  const [isMobileViewport, setIsMobileViewport] = useState(false);

	  useEffect(() => {
	    setIsTouchDevice("ontouchstart" in window);

	    const media = window.matchMedia("(max-width: 767px)");
	    const handleChange = () => setIsMobileViewport(media.matches);

	    handleChange();
	    if (media.addEventListener) {
	      media.addEventListener("change", handleChange);
	    } else {
	      media.addListener(handleChange);
	    }

	    return () => {
	      if (media.removeEventListener) {
	        media.removeEventListener("change", handleChange);
	      } else {
	        media.removeListener(handleChange);
	      }
	    };
	  }, []);

	  const hotspotScale = useMemo(() => (isMobileViewport ? 1.5 : 1), [isMobileViewport]);

	  const [ripples, setRipples] = useState([]);
	  const rippleTimeoutsRef = useRef([]);

	  useEffect(() => {
	    return () => {
	      rippleTimeoutsRef.current.forEach((timeoutId) => clearTimeout(timeoutId));
	      rippleTimeoutsRef.current = [];
	    };
	  }, []);

	  const addRipple = useCallback((clientX, clientY) => {
	    const rect = containerRef.current?.getBoundingClientRect();
	    if (!rect) return;

	    const size = Math.max(90, Math.min(rect.width, rect.height) * 0.18);
	    const x = clientX - rect.left;
	    const y = clientY - rect.top;
	    const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`;

	    setRipples((prev) => [...prev, { id, x, y, size }]);
	    const timeoutId = setTimeout(() => {
	      setRipples((prev) => prev.filter((r) => r.id !== id));
	    }, 600);
	    rippleTimeoutsRef.current.push(timeoutId);
	  }, []);

	  // Get selected motif position for camera animation
	  const selectedMotifPosition = useMemo(() => {
    if (!selectedMotifId) return null;
    const motif = motifsById[selectedMotifId];
    if (!motif || (motif.pos_x === 0 && motif.pos_y === 0 && motif.pos_z === 0)) return null;
    return [motif.pos_x, motif.pos_y, motif.pos_z];
  }, [selectedMotifId, motifsById]);

  useEffect(() => {
    ensureMotifsLoaded(urnSlug);
  }, [urnSlug, ensureMotifsLoaded]);

  useEffect(() => {
    let cancelled = false;
    async function loadUrn() {
      try {
        const detail = await getUrnDetail(urnSlug);
        if (cancelled) return;
        setModelUrl(detail?.urn?.model_url || null);
      } catch {
        if (cancelled) return;
        setModelUrl(null);
      }
    }

    loadUrn();
    return () => {
      cancelled = true;
    };
  }, [urnSlug]);

  const motifsByMeshLower = useMemo(() => {
    const map = {};
    for (const [meshName, motif] of Object.entries(motifsByMesh || {})) {
      if (!meshName) continue;
      map[meshName.toLowerCase()] = motif;
    }
    return map;
  }, [motifsByMesh]);

  const clickableMeshesLower = useMemo(() => new Set(Object.keys(motifsByMeshLower)), [motifsByMeshLower]);
  const motifList = useMemo(() => {
    const list = Object.values(motifsById);
    list.sort((a, b) => {
      const ao = typeof a?.display_order === "number" ? a.display_order : 0;
      const bo = typeof b?.display_order === "number" ? b.display_order : 0;
      return ao - bo;
    });
    return list;
  }, [motifsById]);

  const handleHover = useCallback(
    (e) => {
      const meshName = e?.object?.name;
      const key = meshName ? meshName.toLowerCase() : "";
      setHovered(Boolean(meshName && (motifsByMesh[meshName] || clickableMeshesLower.has(key))));
    },
    [clickableMeshesLower, motifsByMesh]
  );

	  const handleClick = useCallback(
	    async (e) => {
	      e.stopPropagation();
	      const nativeEvent = e?.nativeEvent;
	      if (isTouchDevice && nativeEvent?.clientX != null && nativeEvent?.clientY != null) {
	        addRipple(nativeEvent.clientX, nativeEvent.clientY);
	      }
	      const meshName = e?.object?.name;
	      if (!meshName) return;

      let motif = motifsByMesh[meshName] || motifsByMeshLower[meshName.toLowerCase()];
      if (!motif) {
        await ensureMotifsLoaded(urnSlug);
        const refreshed = useMotifStore.getState().motifsByMesh || {};
        motif = refreshed[meshName];
        if (!motif) {
          const lower = meshName.toLowerCase();
          for (const [k, v] of Object.entries(refreshed)) {
            if (k && k.toLowerCase() === lower) {
              motif = v;
              break;
            }
          }
        }
      }
      if (!motif?.id) return;

      setSelectedMotifId(motif.id);
      unlockFromClick({ userId, motif, meshName, point: e.point });
	    },
	    [
	      addRipple,
	      ensureMotifsLoaded,
	      isTouchDevice,
	      motifsByMesh,
	      motifsByMeshLower,
	      setSelectedMotifId,
	      unlockFromClick,
	      urnSlug,
	      userId,
	    ]
	  );

	  const fallback = useMemo(
	    () => (
	      <FallbackScene
	        motifs={motifList}
	        foundByMotifId={foundByMotifId}
	        showHints={showHints}
	        onClickMesh={handleClick}
	        hotspotScale={hotspotScale}
	      />
	    ),
	    [foundByMotifId, handleClick, hotspotScale, motifList, showHints]
	  );

  const [webglFailed, setWebglFailed] = useState(false);

  // Listen for WebGL context creation errors (thrown as unhandled promise rejections)
  useEffect(() => {
    const handleError = (event) => {
      if (event.reason?.message?.includes('WebGL') ||
          event.reason?.message?.includes('context')) {
        event.preventDefault();
        setWebglFailed(true);
      }
    };

    window.addEventListener('unhandledrejection', handleError);
    return () => window.removeEventListener('unhandledrejection', handleError);
  }, []);

  // Fallback UI when WebGL fails
  if (webglFailed) {
    return (
      <div className={className}>
        <div className="absolute inset-0 flex items-center justify-center bg-background">
          <div className="max-w-md p-8 text-center">
            <div className="mb-4 text-6xl">⚠️</div>
            <h2 className="mb-4 text-xl font-display font-bold text-foreground">
              WebGL Không Khả Dụng
            </h2>
            <p className="mb-6 text-sm text-muted-foreground">
              Trình duyệt của bạn không hỗ trợ WebGL hoặc WebGL đã bị tắt.
              Vui lòng bật WebGL trong cài đặt trình duyệt hoặc sử dụng trình duyệt khác
              (Chrome, Firefox, Edge) để xem mô hình 3D.
            </p>
            <div className="space-y-2">
              <Link
                href="/explore"
                className="block w-full py-2 px-4 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
              >
                Quay Lại Khám Phá
              </Link>
              <Link
                href="/collection"
                className="block w-full py-2 px-4 bg-muted text-foreground rounded-lg text-sm font-medium hover:bg-muted/80 transition-colors"
              >
                Xem Bộ Sưu Tập
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

	  return (
	    <WebGLErrorBoundary>
	      <div ref={containerRef} className={`relative h-full w-full ${className}`}>
        <div className="absolute right-3 top-3 z-20 pointer-events-none">
          <button
            type="button"
            onClick={() => setShowHints((v) => !v)}
            aria-pressed={showHints}
            title={showHints ? "Ẩn Gợi Ý" : "Hiện Gợi Ý"}
            className={`pointer-events-auto inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium shadow-sm backdrop-blur transition-colors ${
              showHints
                ? "bg-primary text-primary-foreground border-transparent hover:bg-primary/90"
                : "bg-background/80 text-foreground border-border hover:bg-background/90"
            }`}
          >
            <Eye className="h-4 w-4" />
            <span>{showHints ? "Ẩn Gợi Ý" : "Hiện Gợi Ý"}</span>
          </button>
        </div>
	        {isTouchDevice && ripples.length ? (
	          <div className="absolute inset-0 z-10 overflow-hidden pointer-events-none">
	            {ripples.map((ripple) => (
	              <span
	                key={ripple.id}
	                className="ripple"
	                style={{
	                  width: ripple.size,
	                  height: ripple.size,
	                  left: ripple.x - ripple.size / 2,
	                  top: ripple.y - ripple.size / 2,
	                }}
	              />
	            ))}
	          </div>
	        ) : null}
	        <Canvas
	          shadows
	          camera={{ position: [0, 1.4, 3.6], fov: 45 }}
	          onPointerMissed={() => useMotifStore.getState().closeSidebar()}
	          onPointerMove={isTouchDevice ? undefined : handleHover}
	          onCreated={(state) => {
	            if (!state.gl) setWebglFailed(true);
	          }}
	          style={{ touchAction: "none" }}
	          fallback={
	            <div className="absolute inset-0 flex items-center justify-center bg-background">
	              <div className="text-center text-muted-foreground">
	                <div className="mb-2 text-4xl">⏳</div>
                <div>Đang tải 3D...</div>
              </div>
            </div>
          }
        >
          <ambientLight intensity={0.7} />
          <directionalLight position={[5, 8, 5]} intensity={1.2} castShadow />

          <Suspense fallback={<Loader />}>
            <ModelErrorBoundary key={modelUrl || urnSlug} fallback={fallback}>
	              {modelUrl ? (
	                <UrnModel
	                  url={modelUrl}
	                  motifs={motifList}
	                  foundByMotifId={foundByMotifId}
	                  showHints={showHints}
	                  onClickMesh={handleClick}
	                  hotspotScale={hotspotScale}
	                />
	              ) : (
	                fallback
	              )}
	            </ModelErrorBoundary>
	          </Suspense>

	          <OrbitControls
	            ref={controlsRef}
	            autoRotate={false}
	            enableDamping={false}
	            rotateSpeed={isTouchDevice ? 0.6 : 1}
	            zoomSpeed={isTouchDevice ? 0.75 : 1}
	            enablePan={!isTouchDevice}
	          />
	        </Canvas>
	        <LessonSidebar />
	      </div>
	    </WebGLErrorBoundary>
	  );
}
