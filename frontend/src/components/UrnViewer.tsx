"use client";

import {
    Component,
    Suspense,
    useCallback,
    useEffect,
    useMemo,
    useRef,
    useState,
} from "react";
import type { ComponentProps, ErrorInfo, ReactNode, RefObject } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import type { ThreeEvent } from "@react-three/fiber";
import {
    OrbitControls,
    useCursor,
    useGLTF,
    Html,
    useProgress,
} from "@react-three/drei";
import * as THREE from "three";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import Link from "next/link";
import UrnAccessibleFallback from "./UrnAccessibleFallback";

import {
    selectMotifListSorted,
    selectMotifStatusById,
    useMotifStore,
    type Motif,
    type MotifStatus,
} from "@/stores/motifStore";
import { shallow } from "zustand/shallow";
import LessonSidebar from "@/components/LessonSidebar";
import useRenderPerf from "@/hooks/useRenderPerf";

THREE.Cache.enabled = true;

// ---------------------------------------------------------------------------
// Shared local types
// ---------------------------------------------------------------------------
type Vec3 = [number, number, number];
type ControlsRef = RefObject<OrbitControlsImpl | null>;
type ClickMeshHandler = (event: ThreeEvent<MouseEvent>) => void;

interface Ripple {
    id: string;
    x: number;
    y: number;
    size: number;
}

interface RewardBurst {
    id: string;
    position: Vec3;
    lines: string[];
}

interface RewardSnapshot {
    xpAwarded: number;
    status: MotifStatus | null;
}

interface WebGLErrorBoundaryProps {
    children?: ReactNode;
    urnSlug?: string;
}

interface WebGLErrorBoundaryState {
    hasError: boolean;
    error: unknown;
}

interface ModelErrorBoundaryProps {
    children?: ReactNode;
    fallback?: ReactNode;
    onError?: (error: unknown) => void;
}

interface ModelErrorBoundaryState {
    hasError: boolean;
}

interface CameraControllerProps {
    targetPosition: Vec3 | null;
    enabled: boolean;
    controlsRef: ControlsRef;
}

interface OrbitControlsWithInvalidationProps {
    controlsRef: ControlsRef;
    rotateSpeed: number;
    zoomSpeed: number;
    enablePan: boolean;
}

interface HotspotTooltipProps {
    label?: string;
}

interface ActionChipProps {
    motif: Motif | null;
    status: string;
    position: Vec3 | null;
}

interface FallbackSceneProps {
    motifs: Motif[];
    motifStatusById: Record<string, MotifStatus>;
    viewMode: string;
    onClickMesh: ClickMeshHandler;
    highlightedMotifId: string | number | null;
    hotspotScale?: number;
    hotspotSegments?: number;
    enableShadows?: boolean;
}

interface HotspotProps {
    motif: Motif;
    status: string;
    viewMode: string;
    position: Vec3;
    hotspotRadius: number;
    onClickMesh: ClickMeshHandler;
    isHighlighted: boolean;
    segments?: number;
}

interface HotspotRingProps {
    motifs: Motif[];
    motifStatusById: Record<string, MotifStatus>;
    viewMode: string;
    onClickMesh: ClickMeshHandler;
    highlightedMotifId: string | number | null;
    radius: number;
    baseY: number;
    levelStep: number;
    hotspotScale?: number;
    hotspotSegments?: number;
}

interface UrnModelProps {
    url: string;
    motifs: Motif[];
    motifStatusById: Record<string, MotifStatus>;
    viewMode: string;
    onClickMesh: ClickMeshHandler;
    highlightedMotifId: string | number | null;
    hotspotScale?: number;
    hotspotSegments?: number;
    enableShadows?: boolean;
    onModelReady?: () => void;
}

interface UrnViewerProps {
    urnSlug: string;
    userId?: string | number | null;
    highlightedMotifId?: string | number | null;
    focusMotifId?: string | number | null;
    viewMode?: string;
    className?: string;
}

// WebGL Error Boundary
class WebGLErrorBoundary extends Component<
    WebGLErrorBoundaryProps,
    WebGLErrorBoundaryState
> {
    constructor(props: WebGLErrorBoundaryProps) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error: unknown): WebGLErrorBoundaryState {
        return { hasError: true, error };
    }

    componentDidCatch(error: unknown, errorInfo: ErrorInfo) {
        console.error("WebGL Error:", error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="absolute inset-0 overflow-y-auto p-4 md:p-8 bg-background">
                    <UrnAccessibleFallback urnSlug={this.props.urnSlug} />
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
                <span className="font-display tabular-nums text-sm">
                    {progress.toFixed(0)}%
                </span>
            </div>
        </Html>
    );
}

// Camera controller for smooth animation
function CameraController({
    targetPosition,
    enabled,
    controlsRef,
}: CameraControllerProps) {
    const { camera, invalidate } = useThree();
    const targetRef = useRef(new THREE.Vector3());
    const lookAtRef = useRef(new THREE.Vector3());
    const isAnimating = useRef(false);

    useEffect(() => {
        if (targetPosition && enabled) {
            // Calculate camera position: offset from target
            const offset = new THREE.Vector3(0.8, 0.5, 1.2);
            targetRef.current.set(
                targetPosition[0] + offset.x,
                targetPosition[1] + offset.y,
                targetPosition[2] + offset.z,
            );
            lookAtRef.current.set(
                targetPosition[0],
                targetPosition[1],
                targetPosition[2],
            );
            isAnimating.current = true;
            invalidate();
        }
    }, [targetPosition, enabled, invalidate]);

    useFrame(() => {
        if (!isAnimating.current) return;

        const currentPos = camera.position;
        const target = targetRef.current;
        const lookAtTarget = lookAtRef.current;

        // Smooth lerp towards target
        currentPos.lerp(target, 0.05);
        if (controlsRef?.current) {
            controlsRef.current.target.lerp(lookAtTarget, 0.05);
            controlsRef.current.update();
        }

        // Stop animating when close enough
        if (currentPos.distanceTo(target) < 0.01) {
            isAnimating.current = false;
            return;
        }

        invalidate();
    });

    return null;
}

function OrbitControlsWithInvalidation({
    controlsRef,
    rotateSpeed,
    zoomSpeed,
    enablePan,
}: OrbitControlsWithInvalidationProps) {
    const { invalidate } = useThree();

    useEffect(() => {
        const controls = controlsRef?.current;
        if (!controls) return;

        const handleChange = () => invalidate();
        controls.addEventListener("change", handleChange);
        return () => controls.removeEventListener("change", handleChange);
    }, [controlsRef, invalidate]);

    return (
        <OrbitControls
            ref={controlsRef}
            autoRotate={false}
            enableDamping={false}
            rotateSpeed={rotateSpeed}
            zoomSpeed={zoomSpeed}
            enablePan={enablePan}
        />
    );
}

function HotspotTooltip({ label }: HotspotTooltipProps) {
    if (!label) return null;

    return (
        <div className="pointer-events-none select-none whitespace-nowrap rounded-md border border-border bg-popover/95 px-2 py-1 text-xs font-medium text-popover-foreground shadow-md">
            {label}
        </div>
    );
}

const MOTIF_STATUS_LABELS: Record<string, string> = {
    hidden: "Chưa mở",
    discovered: "Đã khám phá",
    learned: "Đã học",
    mastered: "Đã thành thạo",
};

function ActionChip({ motif, status, position }: ActionChipProps) {
    if (!motif || !position) return null;

    const statusLabel = MOTIF_STATUS_LABELS[status] || "Tiến độ";

    return (
        <Html
            position={[position[0], position[1] + 0.22, position[2]]}
            center
            zIndexRange={[300, 0]}
            style={{ pointerEvents: "auto" }}
        >
            <div className="min-w-[180px] rounded-xl border border-white/10 bg-black/70 p-3 text-xs text-white shadow-[0_10px_28px_rgba(0,0,0,0.4)] backdrop-blur-md">
                <div className="text-[10px] uppercase tracking-wide text-white/50">
                    {statusLabel}
                </div>
                <div className="mt-1 text-sm font-semibold text-white">
                    {motif.name}
                </div>
                {motif.name_en ? (
                    <div className="text-[11px] text-white/60">
                        {motif.name_en as string}
                    </div>
                ) : null}
                <div className="mt-3 flex flex-wrap gap-2">
                    <Link
                        href={`/motif/${motif.id}`}
                        className="rounded-lg border border-white/15 bg-white/5 px-2.5 py-1 text-[11px] font-semibold text-white hover:bg-white/10"
                    >
                        Bài học
                    </Link>
                    <Link
                        href={`/motif/${motif.id}/quiz`}
                        className="rounded-lg bg-primary px-2.5 py-1 text-[11px] font-semibold text-primary-foreground hover:bg-primary/90"
                    >
                        Quiz
                    </Link>
                </div>
            </div>
        </Html>
    );
}

function FallbackScene({
    motifs,
    motifStatusById,
    viewMode,
    onClickMesh,
    highlightedMotifId,
    hotspotScale = 1,
    hotspotSegments = 16,
    enableShadows = false,
}: FallbackSceneProps) {
    // Render a simple "urn" + clickable spheres (so the app works even without GLB assets).
    const [hoveredMotifId, setHoveredMotifId] = useState<
        string | number | null
    >(null);
    const hotspotRadius = 0.12 * hotspotScale;

    return (
        <group>
            <mesh
                position={[0, 0, 0]}
                receiveShadow={enableShadows}
                castShadow={enableShadows}
            >
                <cylinderGeometry args={[0.7, 0.9, 1.6, 32]} />
                <meshStandardMaterial color="#2b2b2b" />
            </mesh>

            {motifs.map((motif, idx) => {
                const status = motifStatusById[motif.id] || "hidden";
                const isHighlighted = highlightedMotifId === motif.id;
                const isHidden = status === "hidden";
                const isMastered = status === "mastered";
                const isScanMode = viewMode === "scan";
                const isMasteryMode = viewMode === "mastery";
                const isStandardMode = viewMode === "standard";
                const angle = (idx / Math.max(1, motifs.length)) * Math.PI * 2;
                const radius = 1.2;
                const x = Math.cos(angle) * radius;
                const z = Math.sin(angle) * radius;
                const y = 0.3 + (idx % 3) * 0.25;

                const color = isHidden ? "#d9a521" : "#318265";
                let opacity = isStandardMode
                    ? isHidden
                        ? 0
                        : isMastered
                          ? 0.28
                          : 0.4
                    : isScanMode
                      ? isHidden
                          ? 0.75
                          : isMastered
                            ? 0.2
                            : 0.45
                      : isMasteryMode
                        ? isHidden
                            ? 0
                            : isMastered
                              ? 0.18
                              : 0.4
                        : 0.4;
                let emissiveIntensity = opacity > 0 ? 0.4 : 0;
                const shouldPulse = (isScanMode && isHidden) || isHighlighted;

                if (isHighlighted) {
                    opacity = Math.max(opacity, 0.75);
                    emissiveIntensity = Math.max(emissiveIntensity, 0.9);
                }

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
                        castShadow={enableShadows}
                    >
                        <sphereGeometry
                            args={[
                                hotspotRadius,
                                hotspotSegments,
                                hotspotSegments,
                            ]}
                        />
                        <meshStandardMaterial
                            color={color}
                            transparent
                            opacity={opacity}
                            emissive={color}
                            emissiveIntensity={emissiveIntensity}
                            depthWrite={false}
                        />
                        {isStandardMode && isMastered ? (
                            <mesh scale={1.7}>
                                <sphereGeometry
                                    args={[
                                        hotspotRadius,
                                        hotspotSegments,
                                        hotspotSegments,
                                    ]}
                                />
                                <meshStandardMaterial
                                    color="#c7a056"
                                    transparent
                                    opacity={0.15}
                                    emissive="#c7a056"
                                    emissiveIntensity={0.5}
                                    depthWrite={false}
                                />
                            </mesh>
                        ) : null}
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
                        {(hoveredMotifId === motif.id || isHighlighted) &&
                            motif?.name && (
                                <Html
                                    position={[0, hotspotRadius + 0.16, 0]}
                                    center
                                    zIndexRange={[200, 0]}
                                    style={{ pointerEvents: "none" }}
                                >
                                    <HotspotTooltip
                                        label={
                                            isHighlighted
                                                ? `Tiếp theo: ${motif.name}`
                                                : motif.name
                                        }
                                    />
                                </Html>
                            )}
                    </mesh>
                );
            })}
        </group>
    );
}

class ModelErrorBoundary extends Component<
    ModelErrorBoundaryProps,
    ModelErrorBoundaryState
> {
    constructor(props: ModelErrorBoundaryProps) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(): ModelErrorBoundaryState {
        return { hasError: true };
    }

    componentDidCatch(error: unknown) {
        if (this.props.onError) this.props.onError(error);
    }

    render() {
        if (this.state.hasError) return this.props.fallback;
        return this.props.children;
    }
}

// Individual hotspot with hover state - invisible by default, glow on hover
function Hotspot({
    motif,
    status,
    viewMode,
    position,
    hotspotRadius,
    onClickMesh,
    isHighlighted,
    segments = 24,
}: HotspotProps) {
    const [hovered, setHovered] = useState(false);
    useCursor(hovered);

    const isHidden = status === "hidden";
    const isMastered = status === "mastered";
    const isScanMode = viewMode === "scan";
    const isMasteryMode = viewMode === "mastery";
    const isStandardMode = viewMode === "standard";

    const shouldPulse = (isScanMode && isHidden) || isHighlighted;
    const showMasteredHalo = isStandardMode && isMastered;

    const color = isHidden ? "#d9a521" : "#318265"; // gold / jade
    let opacity = isStandardMode
        ? isHidden
            ? 0
            : isMastered
              ? 0.28
              : 0.4
        : isScanMode
          ? isHidden
              ? 0.75
              : isMastered
                ? 0.2
                : 0.45
          : isMasteryMode
            ? isHidden
                ? 0
                : isMastered
                  ? 0.18
                  : 0.4
            : 0.4;
    let emissiveIntensity = opacity > 0 ? 0.4 : 0;

    if (isHighlighted) {
        opacity = Math.max(opacity, 0.75);
        emissiveIntensity = Math.max(emissiveIntensity, 0.9);
    }

    if (shouldPulse) {
        opacity = 0.6;
    }

    if (hovered) {
        opacity = Math.max(opacity, 0.55);
        emissiveIntensity = Math.max(emissiveIntensity, 0.8);
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
            <sphereGeometry args={[hotspotRadius, segments, segments]} />
            <meshStandardMaterial
                color={color}
                transparent
                opacity={opacity}
                emissive={color}
                emissiveIntensity={emissiveIntensity}
                depthWrite={false}
            />
            {showMasteredHalo ? (
                <mesh scale={1.7}>
                    <sphereGeometry
                        args={[hotspotRadius, segments, segments]}
                    />
                    <meshStandardMaterial
                        color="#c7a056"
                        transparent
                        opacity={0.15}
                        emissive="#c7a056"
                        emissiveIntensity={0.5}
                        depthWrite={false}
                    />
                </mesh>
            ) : null}
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
            {(hovered || isHighlighted) && motif?.name && (
                <Html
                    position={[0, hotspotRadius + 0.18, 0]}
                    center
                    zIndexRange={[200, 0]}
                    style={{ pointerEvents: "none" }}
                >
                    <HotspotTooltip
                        label={
                            isHighlighted
                                ? `Tiếp theo: ${motif.name}`
                                : motif.name
                        }
                    />
                </Html>
            )}
        </mesh>
    );
}

function HotspotRing({
    motifs,
    motifStatusById,
    viewMode,
    onClickMesh,
    highlightedMotifId,
    radius,
    baseY,
    levelStep,
    hotspotScale = 1,
    hotspotSegments = 24,
}: HotspotRingProps) {
    return (
        <group>
            {motifs.map((motif, idx) => {
                const isHighlighted = highlightedMotifId === motif.id;
                const status = motifStatusById[motif.id] || "hidden";

                // Use DB positions if available (non-zero), otherwise fallback to circular formula
                const hasDbPosition =
                    motif.pos_x !== 0 || motif.pos_y !== 0 || motif.pos_z !== 0;
                let x, y, z;
                let hotspotRadius = 0.12; // Larger default for visibility

                if (hasDbPosition) {
                    x = motif.pos_x;
                    y = motif.pos_y;
                    z = motif.pos_z;
                    hotspotRadius = Math.max(
                        (motif.bounding_radius as number) || 0.12,
                        0.08,
                    );
                } else {
                    // Fallback: circular formula
                    const angle =
                        (idx / Math.max(1, motifs.length)) * Math.PI * 2;
                    x = Math.cos(angle) * radius;
                    z = Math.sin(angle) * radius;
                    y = baseY + (idx % 3) * levelStep;
                }

                hotspotRadius *= hotspotScale;
                return (
                    <Hotspot
                        key={motif.id}
                        motif={motif}
                        status={status}
                        viewMode={viewMode}
                        position={[x, y, z] as Vec3}
                        hotspotRadius={hotspotRadius}
                        onClickMesh={onClickMesh}
                        isHighlighted={isHighlighted}
                        segments={hotspotSegments}
                    />
                );
            })}
        </group>
    );
}

function UrnModel({
    url,
    motifs,
    motifStatusById,
    viewMode,
    onClickMesh,
    highlightedMotifId,
    hotspotScale,
    hotspotSegments,
    enableShadows,
    onModelReady,
}: UrnModelProps) {
    const gltf = useGLTF(url) as unknown as { scene: THREE.Group };

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
            radius:
                (Math.max(scaledSize.x, scaledSize.z) * 0.62 + 0.2) /
                Math.max(1e-6, scale),
            baseY: (-scaledSize.y * 0.35) / Math.max(1e-6, scale),
            levelStep:
                Math.max(0.15, scaledSize.y * 0.15) / Math.max(1e-6, scale),
        };
    }, [gltf]);

    useEffect(() => {
        gltf.scene.traverse((obj: THREE.Object3D) => {
            if (obj && (obj as THREE.Mesh).isMesh) {
                obj.castShadow = Boolean(enableShadows);
                obj.receiveShadow = Boolean(enableShadows);
            }
        });
    }, [enableShadows, gltf]);

    // Notify parent that the GLTF finished loading and the scene graph is
    // attached. We schedule on the next animation frame so the first paint
    // has actually happened.
    useEffect(() => {
        if (!onModelReady) return undefined;
        let rafId = 0;
        rafId = requestAnimationFrame(() => onModelReady());
        return () => cancelAnimationFrame(rafId);
    }, [gltf, onModelReady]);

    return (
        <group
            scale={fit.scale}
            position={fit.center.clone().multiplyScalar(-fit.scale)}
        >
            <primitive object={gltf.scene} onClick={onClickMesh} />
            <HotspotRing
                motifs={motifs}
                motifStatusById={motifStatusById}
                viewMode={viewMode}
                onClickMesh={onClickMesh}
                highlightedMotifId={highlightedMotifId}
                radius={fit.radius}
                baseY={fit.baseY}
                levelStep={fit.levelStep}
                hotspotScale={hotspotScale}
                hotspotSegments={hotspotSegments}
            />
        </group>
    );
}

export default function UrnViewer({
    urnSlug,
    userId,
    highlightedMotifId = null,
    focusMotifId = null,
    viewMode = "standard",
    className = "h-full w-full",
}: UrnViewerProps) {
    const ensureMotifsLoaded = useMotifStore((s) => s.ensureMotifsLoaded);
    const motifsByMesh = useMotifStore((s) => s.motifsByMesh);
    const motifsById = useMotifStore((s) => s.motifsById);
    const progressByMotifId = useMotifStore((s) => s.progressByMotifId);
    const motifStatusById = useMotifStore(selectMotifStatusById, shallow);
    const motifList = useMotifStore(selectMotifListSorted, shallow);
    const urnModelUrl = useMotifStore((s) => s.urnModelUrl);
    const setSelectedMotifId = useMotifStore((s) => s.setSelectedMotifId);
    const selectedMotifId = useMotifStore((s) => s.selectedMotifId);
    const unlockFromClick = useMotifStore((s) => s.unlockFromClick);
    const selectedProgress = selectedMotifId
        ? progressByMotifId[selectedMotifId]
        : null;

    // Render performance instrumentation (Gap 4 — paper claim "+46% speedup").
    // Fires one analytics event per model load. Fire-and-forget; never blocks render.
    const { markFirstFrame, markFirstInteraction } = useRenderPerf({
        modelUrl: urnModelUrl,
    });

    const [hovered, setHovered] = useState(false);
    useCursor(hovered);

    const controlsRef = useRef<OrbitControlsImpl>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    const [isTouchDevice, setIsTouchDevice] = useState(false);
    const [isMobileViewport, setIsMobileViewport] = useState(false);
    const [isLowPowerDevice, setIsLowPowerDevice] = useState(false);

    useEffect(() => {
        setIsTouchDevice("ontouchstart" in window);

        const hardwareConcurrency = navigator.hardwareConcurrency || 4;
        const deviceMemory =
            (navigator as Navigator & { deviceMemory?: number })
                .deviceMemory || 4;
        const media = window.matchMedia("(max-width: 767px)");
        const handleChange = () => {
            const isMobile = media.matches;
            setIsMobileViewport(isMobile);
            setIsLowPowerDevice(
                isMobile || hardwareConcurrency <= 4 || deviceMemory <= 4,
            );
        };

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

    const hotspotScale = useMemo(
        () => (isMobileViewport ? 1.5 : 1),
        [isMobileViewport],
    );
    const enableShadows = !isLowPowerDevice;
    const hotspotSegments = isLowPowerDevice ? 12 : 24;
    const renderDpr = useMemo(() => {
        if (typeof window === "undefined") return 1;
        const deviceDpr = window.devicePixelRatio || 1;
        if (isLowPowerDevice) return 1;
        return Math.min(deviceDpr, 1.5);
    }, [isLowPowerDevice]);

    const [ripples, setRipples] = useState<Ripple[]>([]);
    const rippleTimeoutsRef = useRef<ReturnType<typeof setTimeout>[]>([]);

    useEffect(() => {
        return () => {
            rippleTimeoutsRef.current.forEach((timeoutId) =>
                clearTimeout(timeoutId),
            );
            rippleTimeoutsRef.current = [];
        };
    }, []);

    const addRipple = useCallback((clientX: number, clientY: number) => {
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

    const selectedMotif = selectedMotifId ? motifsById[selectedMotifId] : null;
    const selectedMotifStatus = selectedMotifId
        ? motifStatusById[selectedMotifId]
        : null;

    const resolveMotifPosition = useCallback(
        (motifId: string | number | null): Vec3 | null => {
            if (!motifId) return null;
            const motif = motifsById[motifId];
            if (!motif) return null;
            const hasDbPosition =
                motif.pos_x !== 0 || motif.pos_y !== 0 || motif.pos_z !== 0;
            if (hasDbPosition) {
                return [motif.pos_x, motif.pos_y, motif.pos_z] as Vec3;
            }
            const idx = motifList.findIndex(
                (item) => String(item.id) === String(motifId),
            );
            if (idx === -1) return null;
            const angle = (idx / Math.max(1, motifList.length)) * Math.PI * 2;
            const radius = 1.2;
            const x = Math.cos(angle) * radius;
            const z = Math.sin(angle) * radius;
            const y = 0.3 + (idx % 3) * 0.25;
            return [x, y, z];
        },
        [motifsById, motifList],
    );

    const selectedMotifPosition = useMemo(
        () => resolveMotifPosition(selectedMotifId),
        [resolveMotifPosition, selectedMotifId],
    );
    const focusMotifPosition = useMemo(
        () => resolveMotifPosition(focusMotifId),
        [resolveMotifPosition, focusMotifId],
    );
    const focusTargetPosition =
        focusMotifId && focusMotifId !== selectedMotifId
            ? focusMotifPosition
            : selectedMotifPosition || focusMotifPosition;

    const [rewardBurst, setRewardBurst] = useState<RewardBurst | null>(null);
    const rewardTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const lastRewardRef = useRef<Record<string, RewardSnapshot>>({});

    useEffect(() => {
        if (!selectedMotifId || !selectedProgress) return;
        const xpAwarded = Number(selectedProgress.xpAwarded || 0);
        const status = selectedProgress.status || null;
        const last = lastRewardRef.current[selectedMotifId];
        if (!last) {
            lastRewardRef.current[selectedMotifId] = { xpAwarded, status };
            return;
        }

        const gainedXp = xpAwarded > 0 && xpAwarded !== last.xpAwarded;
        const masteredNow =
            status === "mastered" && last.status && last.status !== "mastered";
        if (!gainedXp && !masteredNow) {
            lastRewardRef.current[selectedMotifId] = { xpAwarded, status };
            return;
        }

        const lines: string[] = [];
        if (gainedXp) lines.push(`+${xpAwarded} XP`);
        if (masteredNow) lines.push("Đã thành thạo!");

        if (selectedMotifPosition) {
            setRewardBurst({
                id: `${selectedMotifId}-${Date.now()}`,
                lines,
                position: selectedMotifPosition,
            });
            if (rewardTimeoutRef.current) {
                clearTimeout(rewardTimeoutRef.current);
            }
            rewardTimeoutRef.current = setTimeout(() => {
                setRewardBurst(null);
            }, 1800);
        }

        lastRewardRef.current[selectedMotifId] = { xpAwarded, status };
    }, [selectedMotifId, selectedMotifPosition, selectedProgress]);

    useEffect(() => {
        return () => {
            if (rewardTimeoutRef.current) {
                clearTimeout(rewardTimeoutRef.current);
            }
        };
    }, []);

    useEffect(() => {
        ensureMotifsLoaded(urnSlug);
    }, [urnSlug, ensureMotifsLoaded]);

    const motifsByMeshLower = useMemo(() => {
        const map: Record<string, Motif> = {};
        for (const [meshName, motif] of Object.entries(motifsByMesh || {})) {
            if (!meshName) continue;
            map[meshName.toLowerCase()] = motif;
        }
        return map;
    }, [motifsByMesh]);

    const clickableMeshesLower = useMemo(
        () => new Set(Object.keys(motifsByMeshLower)),
        [motifsByMeshLower],
    );
    const handleHover = useCallback(
        (e: ThreeEvent<PointerEvent>) => {
            const meshName = e?.object?.name;
            const key = meshName ? meshName.toLowerCase() : "";
            setHovered(
                Boolean(
                    meshName &&
                    (motifsByMesh[meshName] || clickableMeshesLower.has(key)),
                ),
            );
        },
        [clickableMeshesLower, motifsByMesh],
    );

    const handleClick = useCallback(
        async (e: ThreeEvent<MouseEvent>) => {
            e.stopPropagation();
            const nativeEvent = e?.nativeEvent;
            if (
                isTouchDevice &&
                nativeEvent?.clientX != null &&
                nativeEvent?.clientY != null
            ) {
                addRipple(nativeEvent.clientX, nativeEvent.clientY);
            }
            const meshName = e?.object?.name;
            if (!meshName) return;

            let motif =
                motifsByMesh[meshName] ||
                motifsByMeshLower[meshName.toLowerCase()];
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
            unlockFromClick({
                userId,
                motif,
                meshName,
                point: e.point,
            } as unknown as Parameters<typeof unlockFromClick>[0]);
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
        ],
    );

    const fallback = useMemo(
        () => (
            <FallbackScene
                motifs={motifList}
                motifStatusById={motifStatusById}
                viewMode={viewMode}
                onClickMesh={handleClick}
                highlightedMotifId={highlightedMotifId}
                hotspotScale={hotspotScale}
                hotspotSegments={hotspotSegments}
                enableShadows={enableShadows}
            />
        ),
        [
            enableShadows,
            handleClick,
            highlightedMotifId,
            hotspotScale,
            hotspotSegments,
            motifList,
            motifStatusById,
            viewMode,
        ],
    );

    const [webglFailed, setWebglFailed] = useState(false);

    // Listen for WebGL context creation errors (thrown as unhandled promise rejections)
    useEffect(() => {
        const handleError = (event: PromiseRejectionEvent) => {
            if (
                event.reason?.message?.includes("WebGL") ||
                event.reason?.message?.includes("context")
            ) {
                event.preventDefault();
                setWebglFailed(true);
            }
        };

        window.addEventListener("unhandledrejection", handleError);
        return () =>
            window.removeEventListener("unhandledrejection", handleError);
    }, []);

    // Fallback UI when WebGL fails
    if (webglFailed) {
        return (
            <div className={`relative h-full w-full overflow-y-auto p-4 md:p-8 bg-background ${className}`}>
                <UrnAccessibleFallback urnSlug={urnSlug} />
            </div>
        );
    }

    return (
        <WebGLErrorBoundary urnSlug={urnSlug}>
            <div
                ref={containerRef}
                className={`relative h-full w-full ${className}`}
            >
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
                    shadows={enableShadows}
                    frameloop="demand"
                    dpr={renderDpr}
                    camera={{ position: [0, 1.4, 3.6], fov: 45 }}
                    onPointerMissed={() =>
                        useMotifStore.getState().closeSidebar()
                    }
                    onPointerMove={
                        isTouchDevice
                            ? undefined
                            : (handleHover as unknown as ComponentProps<
                                  typeof Canvas
                              >["onPointerMove"])
                    }
                    onCreated={(state) => {
                        if (!state.gl) setWebglFailed(true);
                        // Render perf: WebGL context ready ≈ ready for user
                        // interaction (OrbitControls attached on next frame).
                        markFirstInteraction();
                    }}
                    gl={{
                        powerPreference: "high-performance",
                        antialias: !isLowPowerDevice,
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
                    <directionalLight
                        position={[5, 8, 5]}
                        intensity={1.2}
                        castShadow={enableShadows}
                    />

                    <Suspense fallback={<Loader />}>
                        <ModelErrorBoundary
                            key={urnModelUrl || urnSlug}
                            fallback={fallback}
                        >
                            {urnModelUrl ? (
                                <UrnModel
                                    url={urnModelUrl}
                                    motifs={motifList}
                                    motifStatusById={motifStatusById}
                                    viewMode={viewMode}
                                    onClickMesh={handleClick}
                                    highlightedMotifId={highlightedMotifId}
                                    hotspotScale={hotspotScale}
                                    hotspotSegments={hotspotSegments}
                                    enableShadows={enableShadows}
                                    onModelReady={markFirstFrame}
                                />
                            ) : (
                                fallback
                            )}
                        </ModelErrorBoundary>
                    </Suspense>

                    {selectedMotif && selectedMotifPosition ? (
                        <ActionChip
                            motif={selectedMotif}
                            status={selectedMotifStatus || "hidden"}
                            position={selectedMotifPosition}
                        />
                    ) : null}

                    {rewardBurst ? (
                        <Html
                            position={[
                                rewardBurst.position[0],
                                rewardBurst.position[1] + 0.32,
                                rewardBurst.position[2],
                            ]}
                            center
                            zIndexRange={[250, 0]}
                            style={{ pointerEvents: "none" }}
                        >
                            <div className="flex flex-col items-center gap-1 rounded-full border border-white/10 bg-black/70 px-3 py-1.5 text-[11px] font-semibold text-white shadow-[0_8px_24px_rgba(0,0,0,0.35)] backdrop-blur-md animate-fade-in-up">
                                {rewardBurst.lines.map((line) => (
                                    <span key={line}>{line}</span>
                                ))}
                            </div>
                        </Html>
                    ) : null}

                    <OrbitControlsWithInvalidation
                        controlsRef={controlsRef}
                        rotateSpeed={isTouchDevice ? 0.6 : 1}
                        zoomSpeed={isTouchDevice ? 0.75 : 1}
                        enablePan={!isTouchDevice}
                    />

                    <CameraController
                        targetPosition={focusTargetPosition}
                        enabled={Boolean(focusTargetPosition)}
                        controlsRef={controlsRef}
                    />
                </Canvas>
                <LessonSidebar />
            </div>
        </WebGLErrorBoundary>
    );
}
