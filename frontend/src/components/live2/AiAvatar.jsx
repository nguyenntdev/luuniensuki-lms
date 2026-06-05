"use client";

/**
 * AiAvatar — a 3D "live teacher" avatar (Ready Player Me GLB) rendered with
 * react-three-fiber. It reflects the conversation turn state and lip-syncs to
 * the AI's speech amplitude (`outputLevel`) by driving the `jawOpen` / viseme
 * morph targets, plus idle breathing and periodic blinking.
 *
 * Robust by design: if the GLB fails to load (network/CORS), an error boundary
 * falls back to the lightweight <ConversationOrb> so the room never breaks.
 */

import React, { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { useGLTF } from "@react-three/drei";

import ConversationOrb from "./ConversationOrb";
import { TURN } from "./useRealtimeVoice";

// A Ready Player Me half-body avatar with ARKit + Oculus viseme morph targets.
// Configurable via NEXT_PUBLIC_AI_AVATAR_URL; falls back to a hosted default.
const DEFAULT_AVATAR_URL =
  (typeof process !== "undefined" && process.env && process.env.NEXT_PUBLIC_AI_AVATAR_URL) ||
  "https://models.readyplayer.me/64bfa15f0e72c63d7c3934a6.glb?morphTargets=ARKit,Oculus%20Visemes&textureAtlas=512&pose=A&lod=1";

const STATE_LABELS = {
  [TURN.IDLE]: { label: "Sẵn sàng", sub: "Nhấn micro để bắt đầu" },
  [TURN.LISTENING]: { label: "Đang nghe…", sub: "Cô giáo AI đang lắng nghe" },
  [TURN.THINKING]: { label: "Đang suy nghĩ…", sub: "Đang soạn câu trả lời" },
  [TURN.SPEAKING]: { label: "Đang giảng…", sub: "Nói chen vào để ngắt lời" },
};

const STATE_LIGHT = {
  [TURN.IDLE]: "#a1a1aa",
  [TURN.LISTENING]: "#34d399",
  [TURN.THINKING]: "#fbbf24",
  [TURN.SPEAKING]: "#38bdf8",
};

function AvatarModel({ url, state, outputLevel }) {
  const { scene } = useGLTF(url);
  const groupRef = useRef(null);
  // Collect meshes that carry morph targets (face/teeth) once.
  const morphMeshes = useMemo(() => {
    const meshes = [];
    scene.traverse((node) => {
      if (node.isMesh && node.morphTargetDictionary && node.morphTargetInfluences) {
        meshes.push(node);
      }
    });
    return meshes;
  }, [scene]);

  const blink = useRef({ next: 1.5, closing: 0 });
  const mouth = useRef(0);

  const setMorph = (mesh, name, value) => {
    const idx = mesh.morphTargetDictionary[name];
    if (idx != null) mesh.morphTargetInfluences[idx] = value;
  };

  useFrame((stateCtx, delta) => {
    const t = stateCtx.clock.elapsedTime;
    // Idle breathing + gentle sway.
    if (groupRef.current) {
      groupRef.current.position.y = -1.45 + Math.sin(t * 1.1) * 0.01;
      groupRef.current.rotation.y = Math.sin(t * 0.4) * 0.06;
      groupRef.current.rotation.x = Math.sin(t * 0.55) * 0.02;
    }

    // Blink: schedule random blinks, ~120ms close.
    blink.current.next -= delta;
    let blinkVal = 0;
    if (blink.current.next <= 0) {
      blink.current.closing = 0.12;
      blink.current.next = 2.2 + Math.random() * 2.8;
    }
    if (blink.current.closing > 0) {
      blink.current.closing -= delta;
      blinkVal = 1;
    }

    // Mouth: smooth toward target amplitude while speaking, else close.
    const target = state === TURN.SPEAKING ? Math.min(1, (outputLevel || 0) * 1.4) : 0;
    mouth.current += (target - mouth.current) * Math.min(1, delta * 18);
    const jaw = mouth.current;

    for (const mesh of morphMeshes) {
      setMorph(mesh, "eyeBlinkLeft", blinkVal);
      setMorph(mesh, "eyeBlinkRight", blinkVal);
      setMorph(mesh, "jawOpen", jaw * 0.6);
      setMorph(mesh, "mouthOpen", jaw * 0.5);
      setMorph(mesh, "viseme_aa", jaw * 0.7);
      // A faint smile at rest / while listening.
      const smile = state === TURN.LISTENING ? 0.18 : 0.08;
      setMorph(mesh, "mouthSmileLeft", smile);
      setMorph(mesh, "mouthSmileRight", smile);
    }
  });

  return (
    <group ref={groupRef} position={[0, -1.45, 0]}>
      <primitive object={scene} scale={1} />
    </group>
  );
}

// Error boundary: any failure inside the Canvas (GLB load, WebGL) falls back
// to the orb so the room keeps working.
class AvatarErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { failed: false };
  }
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch() {
    /* swallow — fallback rendered below */
  }
  render() {
    if (this.state.failed) return this.props.fallback;
    return this.props.children;
  }
}

function AvatarScene({ url, state, outputLevel }) {
  const speaking = state === TURN.SPEAKING;
  const listening = state === TURN.LISTENING;
  const keyColor = STATE_LIGHT[state] || STATE_LIGHT[TURN.IDLE];
  return (
    <Canvas
      camera={{ position: [0, 0.05, 0.95], fov: 28 }}
      dpr={[1, 1.6]}
      gl={{ antialias: true, alpha: true, powerPreference: "low-power" }}
      style={{ width: "100%", height: "100%" }}
    >
      <ambientLight intensity={0.85} />
      <directionalLight position={[1.5, 2, 2]} intensity={1.1} />
      {/* state-tinted rim light */}
      <pointLight
        position={[-1.2, 0.6, 1.4]}
        intensity={speaking ? 2.2 : listening ? 1.6 : 1.1}
        color={keyColor}
        distance={6}
      />
      <Suspense fallback={null}>
        <AvatarModel url={url} state={state} outputLevel={outputLevel} />
      </Suspense>
    </Canvas>
  );
}

export default function AiAvatar({ state, level = 0, outputLevel = 0, onClick, avatarUrl }) {
  const url = avatarUrl || DEFAULT_AVATAR_URL;
  const meta = STATE_LABELS[state] || STATE_LABELS[TURN.IDLE];
  const orb = <ConversationOrb state={state} level={level} onClick={onClick} />;

  return (
    <div className="flex h-full w-full flex-col items-center justify-center gap-3 select-none">
      <AvatarErrorBoundary fallback={orb}>
        <button
          type="button"
          onClick={onClick}
          aria-label={meta.label}
          className="relative h-[clamp(220px,42vh,420px)] w-[clamp(220px,32vw,360px)] overflow-hidden rounded-3xl outline-none"
        >
          <span
            className="pointer-events-none absolute inset-0 rounded-3xl opacity-70 blur-2xl transition-colors"
            style={{ background: `radial-gradient(circle at 50% 35%, ${STATE_LIGHT[state]}33, transparent 70%)` }}
          />
          <AvatarScene url={url} state={state} outputLevel={outputLevel} />
        </button>
      </AvatarErrorBoundary>
      <div className="text-center">
        <div className="text-lg font-semibold text-zinc-100">{meta.label}</div>
        <div className="mt-1 text-xs text-zinc-400">{meta.sub}</div>
      </div>
    </div>
  );
}

// Preload the default avatar (best-effort).
try {
  useGLTF.preload(DEFAULT_AVATAR_URL);
} catch {
  /* ignore */
}
