"use client";

/**
 * Panorama360 — a fully self-hosted equirectangular 360° viewer built on the
 * three.js stack already in the project (no CDN, no extra dependency). Renders
 * the panorama on the inside of a sphere and lets the user look around / zoom.
 *
 * Images are served from our OWN assets (e.g. /panoramas/<slug>.jpg). Place
 * only panoramas you have the rights to use.
 */

import React, { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, useTexture } from "@react-three/drei";
import { BackSide } from "three";

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
  { fallback: React.ReactNode; children: React.ReactNode },
  { failed: boolean }
> {
  constructor(props: { fallback: React.ReactNode; children: React.ReactNode }) {
    super(props);
    this.state = { failed: false };
  }
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch() {}
  render() {
    return this.state.failed ? this.props.fallback : this.props.children;
  }
}

interface Panorama360Props {
  src: string;
  title?: string;
}

export default function Panorama360({ src, title }: Panorama360Props) {
  const fallback = (
    <div className="grid h-full w-full place-items-center bg-zinc-900 text-center text-sm text-zinc-400">
      <div className="px-6">
        <p className="font-medium text-zinc-200">Chưa có ảnh panorama cho cảnh này</p>
        <p className="mt-1">
          Đặt ảnh toàn cảnh (equirectangular .jpg) vào{" "}
          <code className="rounded bg-zinc-800 px-1">/panoramas/</code> rồi tải lại.
        </p>
      </div>
    </div>
  );

  return (
    <div className="relative h-full w-full overflow-hidden rounded-lg bg-black ring-1 ring-white/10">
      <PanoErrorBoundary fallback={fallback}>
        <Canvas
          camera={{ position: [0, 0, 0.1], fov: 75, near: 0.1, far: 1000 }}
          dpr={[1, 1.6]}
          gl={{ antialias: true }}
          style={{ width: "100%", height: "100%" }}
        >
          <Suspense fallback={null}>
            <PanoSphere src={src} />
          </Suspense>
          <OrbitControls
            enableZoom
            enablePan={false}
            enableDamping
            dampingFactor={0.08}
            rotateSpeed={-0.4}
            minDistance={0.1}
            maxDistance={1}
            zoomSpeed={0.6}
          />
        </Canvas>
      </PanoErrorBoundary>

      {/* Branding overlay */}
      <div className="pointer-events-none absolute left-3 top-3 flex items-center gap-2 rounded-full bg-black/45 px-3 py-1.5 text-xs font-medium text-white backdrop-blur">
        <span className="inline-block h-2 w-2 rounded-full bg-amber-400" />
        Lưu Niên Sử Kí · Tham quan 360°
      </div>
      {title ? (
        <div className="pointer-events-none absolute bottom-3 left-3 rounded-lg bg-black/45 px-3 py-1.5 text-sm text-white backdrop-blur">
          {title}
        </div>
      ) : null}
      <div className="pointer-events-none absolute right-3 top-3 rounded-full bg-black/40 px-3 py-1.5 text-[11px] text-zinc-200 backdrop-blur">
        Kéo để nhìn quanh · cuộn để phóng to
      </div>
    </div>
  );
}
