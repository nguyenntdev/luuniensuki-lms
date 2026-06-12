"use client";

/**
 * AiAvatar — a friendly stylized 3D "live teacher" avatar rendered with
 * react-three-fiber. It is built from procedural primitives (no external CDN
 * asset, so it always loads), and reflects the conversation turn state with:
 *   - idle floating + gentle head sway
 *   - periodic eye blinks
 *   - audio-amplitude lip-sync (mouth opens with the AI's speech `outputLevel`)
 *   - a state-tinted halo (idle/listening/thinking/speaking)
 *
 * An optional self-hosted Ready Player Me GLB can be used by setting
 * NEXT_PUBLIC_AI_AVATAR_URL (or the `avatarUrl` prop). If that GLB fails to
 * load, an error boundary falls back to the procedural avatar so the room
 * never breaks.
 */

import React, { Suspense, useMemo, useRef } from "react";
import type { ReactNode } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { useGLTF } from "@react-three/drei";

import ConversationOrb from "./ConversationOrb";
import { TURN } from "./useRealtimeVoice";
import type { TurnState } from "./useRealtimeVoice";

/**
 * Minimal subset of the three.js Object3D API this avatar mutates each frame.
 * The full three types aren't needed here — we only read/write transforms and
 * (for the halo) a basic material opacity.
 */
interface Object3DLike {
  position: { x: number; y: number; z: number };
  rotation: { x: number; y: number; z: number };
  scale: { x: number; y: number; z: number };
  material?: { opacity: number };
}

/** Per-frame state passed to react-three-fiber's useFrame callback (subset). */
interface FrameState {
  clock: { elapsedTime: number };
}

/** A mesh node carrying morph targets (Ready Player Me GLB face). */
interface MorphMesh {
  isMesh?: boolean;
  morphTargetDictionary?: Record<string, number>;
  morphTargetInfluences?: number[];
  traverse?: (cb: (node: MorphMesh) => void) => void;
}

const GLB_URL =
  (typeof process !== "undefined" && process.env && process.env.NEXT_PUBLIC_AI_AVATAR_URL) || "";

const STATE_LABELS: Record<TurnState, { label: string; sub: string }> = {
  [TURN.IDLE]: { label: "Sẵn sàng", sub: "Nhấn micro để bắt đầu" },
  [TURN.LISTENING]: { label: "Đang nghe…", sub: "Cô giáo AI đang lắng nghe" },
  [TURN.THINKING]: { label: "Đang suy nghĩ…", sub: "Đang soạn câu trả lời" },
  [TURN.SPEAKING]: { label: "Đang giảng…", sub: "Nói chen vào để ngắt lời" },
};

const STATE_LIGHT: Record<TurnState, string> = {
  [TURN.IDLE]: "#a1a1aa",
  [TURN.LISTENING]: "#34d399",
  [TURN.THINKING]: "#fbbf24",
  [TURN.SPEAKING]: "#38bdf8",
};

const SKIN = "#f1c9a5";
const SKIN_SHADOW = "#e0a87f";
const HAIR = "#2b2b33";
const AODAI = "#0ea5b7";

interface TeacherCharacterProps {
  state: TurnState;
  outputLevel: number;
  level: number;
}

function TeacherCharacter({ state, outputLevel, level }: TeacherCharacterProps) {
  const root = useRef<Object3DLike | null>(null);
  const head = useRef<Object3DLike | null>(null);
  const mouth = useRef<Object3DLike | null>(null);
  const eyeL = useRef<Object3DLike | null>(null);
  const eyeR = useRef<Object3DLike | null>(null);
  const haloRef = useRef<Object3DLike | null>(null);

  const blink = useRef({ next: 1.6, closing: 0 });
  const mouthVal = useRef(0);
  const color = useMemo(
    () => STATE_LIGHT[state] || STATE_LIGHT[TURN.IDLE],
    [state],
  );

  useFrame((ctx: FrameState, delta: number) => {
    const t = ctx.clock.elapsedTime;

    // Whole-avatar gentle float.
    if (root.current) {
      root.current.position.y = Math.sin(t * 1.2) * 0.04;
    }
    // Head sway / nod.
    if (head.current) {
      head.current.rotation.y = Math.sin(t * 0.5) * 0.13;
      head.current.rotation.z = Math.sin(t * 0.7) * 0.03;
      head.current.rotation.x = Math.sin(t * 0.9) * 0.02;
      // Backchannel: while listening, nod along with the student's voice energy
      // (a gentle "I'm following you" motion) plus a slow attentive bob.
      if (state === TURN.LISTENING) {
        const lvl = Math.min(1, level || 0);
        head.current.rotation.x += Math.sin(t * 6) * (0.015 + lvl * 0.06);
        head.current.position && (head.current.position.z = 0.04 + lvl * 0.06);
      } else if (head.current.position) {
        head.current.position.z += (0 - head.current.position.z) * Math.min(1, delta * 6);
      }
    }

    // Blink: schedule random blinks; ~120ms close (scale eyes' Y).
    blink.current.next -= delta;
    if (blink.current.next <= 0) {
      blink.current.closing = 0.12;
      blink.current.next = 2.0 + Math.random() * 3.0;
    }
    let eyeScale = 1;
    if (blink.current.closing > 0) {
      blink.current.closing -= delta;
      eyeScale = 0.12;
    }
    if (eyeL.current) eyeL.current.scale.y = eyeScale;
    if (eyeR.current) eyeR.current.scale.y = eyeScale;

    // Mouth: smooth toward target amplitude while speaking, else nearly closed.
    const target = state === TURN.SPEAKING ? Math.min(1, (outputLevel || 0) * 1.6) : 0;
    mouthVal.current += (target - mouthVal.current) * Math.min(1, delta * 16);
    if (mouth.current) {
      // Pseudo-viseme: drive vertical (jaw open) and horizontal (spread) with
      // slightly different phases so the mouth looks like it's forming sounds
      // rather than just scaling uniformly.
      const m = mouthVal.current;
      const wobble = state === TURN.SPEAKING ? (0.85 + 0.15 * Math.sin(t * 22)) : 1;
      mouth.current.scale.y = 0.16 + m * 1.5 * wobble;
      mouth.current.scale.x = 1 - m * 0.18 + (state === TURN.SPEAKING ? Math.sin(t * 17) * 0.06 * m : 0);
    }

    // Halo: pulse a bit while speaking/listening.
    if (haloRef.current && haloRef.current.material) {
      const base = state === TURN.SPEAKING ? 0.6 : state === TURN.LISTENING ? 0.45 : 0.3;
      const pulse = state === TURN.IDLE ? 0 : Math.abs(Math.sin(t * 3)) * 0.18;
      haloRef.current.material.opacity = base + pulse;
    }
  });

  return (
    <group ref={root}>
      {/* state-tinted halo behind the head */}
      <mesh ref={haloRef} position={[0, 0.15, -0.6]}>
        <circleGeometry args={[1.15, 48]} />
        <meshBasicMaterial color={color} transparent opacity={0.3} />
      </mesh>

      {/* shoulders / áo dài */}
      <mesh position={[0, -1.15, 0]}>
        <cylinderGeometry args={[0.5, 0.85, 0.9, 32]} />
        <meshStandardMaterial color={AODAI} roughness={0.6} metalness={0.05} />
      </mesh>
      <mesh position={[0, -0.62, 0.02]}>
        <sphereGeometry args={[0.42, 24, 24]} />
        <meshStandardMaterial color={AODAI} roughness={0.6} />
      </mesh>

      {/* head group */}
      <group ref={head} position={[0, 0.2, 0]}>
        {/* face */}
        <mesh scale={[0.92, 1, 0.9]}>
          <sphereGeometry args={[0.62, 48, 48]} />
          <meshStandardMaterial color={SKIN} roughness={0.55} metalness={0.02} />
        </mesh>
        {/* hair cap */}
        <mesh position={[0, 0.28, -0.02]} scale={[1.02, 0.78, 1.02]}>
          <sphereGeometry args={[0.64, 36, 36, 0, Math.PI * 2, 0, Math.PI * 0.62]} />
          <meshStandardMaterial color={HAIR} roughness={0.7} />
        </mesh>
        {/* side hair */}
        <mesh position={[0, -0.05, -0.16]} scale={[1.06, 1.1, 1.0]}>
          <sphereGeometry args={[0.6, 32, 32, 0, Math.PI * 2, Math.PI * 0.55, Math.PI * 0.45]} />
          <meshStandardMaterial color={HAIR} roughness={0.7} />
        </mesh>
        {/* eyes (whites) with pupils */}
        <group position={[-0.2, 0.06, 0.55]}>
          <mesh ref={eyeL}>
            <sphereGeometry args={[0.085, 24, 24]} />
            <meshStandardMaterial color="#ffffff" roughness={0.3} />
          </mesh>
          <mesh position={[0, 0, 0.06]}>
            <sphereGeometry args={[0.045, 16, 16]} />
            <meshStandardMaterial color="#26221f" />
          </mesh>
        </group>
        <group position={[0.2, 0.06, 0.55]}>
          <mesh ref={eyeR}>
            <sphereGeometry args={[0.085, 24, 24]} />
            <meshStandardMaterial color="#ffffff" roughness={0.3} />
          </mesh>
          <mesh position={[0, 0, 0.06]}>
            <sphereGeometry args={[0.045, 16, 16]} />
            <meshStandardMaterial color="#26221f" />
          </mesh>
        </group>
        {/* eyebrows */}
        <mesh position={[-0.2, 0.2, 0.56]} rotation={[0, 0, 0.08]}>
          <boxGeometry args={[0.16, 0.025, 0.04]} />
          <meshStandardMaterial color={HAIR} />
        </mesh>
        <mesh position={[0.2, 0.2, 0.56]} rotation={[0, 0, -0.08]}>
          <boxGeometry args={[0.16, 0.025, 0.04]} />
          <meshStandardMaterial color={HAIR} />
        </mesh>
        {/* nose */}
        <mesh position={[0, -0.05, 0.62]}>
          <sphereGeometry args={[0.05, 16, 16]} />
          <meshStandardMaterial color={SKIN_SHADOW} roughness={0.5} />
        </mesh>
        {/* mouth (opens with speech) */}
        <mesh ref={mouth} position={[0, -0.26, 0.56]}>
          <sphereGeometry args={[0.12, 24, 16]} />
          <meshStandardMaterial color="#7a2f2f" roughness={0.4} />
        </mesh>
      </group>
    </group>
  );
}

// Optional: a self-hosted Ready Player Me GLB driven by morph targets.
interface GlbModelProps {
  url: string;
  state: TurnState;
  outputLevel: number;
}

function GlbModel({ url, state, outputLevel }: GlbModelProps) {
  const { scene } = useGLTF(url);
  const groupRef = useRef<Object3DLike | null>(null);
  const morphMeshes = useMemo(() => {
    const meshes: MorphMesh[] = [];
    (scene as MorphMesh).traverse?.((node: MorphMesh) => {
      if (node.isMesh && node.morphTargetDictionary && node.morphTargetInfluences) meshes.push(node);
    });
    return meshes;
  }, [scene]);
  const blink = useRef({ next: 1.6, closing: 0 });
  const mouth = useRef(0);
  const set = (mesh: MorphMesh, name: string, v: number) => {
    const i = mesh.morphTargetDictionary?.[name];
    if (i != null && mesh.morphTargetInfluences) mesh.morphTargetInfluences[i] = v;
  };
  useFrame((ctx: FrameState, delta: number) => {
    const t = ctx.clock.elapsedTime;
    if (groupRef.current) {
      groupRef.current.position.y = -1.45 + Math.sin(t * 1.1) * 0.01;
      groupRef.current.rotation.y = Math.sin(t * 0.4) * 0.06;
    }
    blink.current.next -= delta;
    let bv = 0;
    if (blink.current.next <= 0) { blink.current.closing = 0.12; blink.current.next = 2.2 + Math.random() * 2.8; }
    if (blink.current.closing > 0) { blink.current.closing -= delta; bv = 1; }
    const target = state === TURN.SPEAKING ? Math.min(1, (outputLevel || 0) * 1.4) : 0;
    mouth.current += (target - mouth.current) * Math.min(1, delta * 18);
    for (const m of morphMeshes) {
      set(m, "eyeBlinkLeft", bv); set(m, "eyeBlinkRight", bv);
      set(m, "jawOpen", mouth.current * 0.6); set(m, "mouthOpen", mouth.current * 0.5);
      set(m, "viseme_aa", mouth.current * 0.7);
    }
  });
  return (
    <group ref={groupRef} position={[0, -1.45, 0]}>
      <primitive object={scene} />
    </group>
  );
}

interface AvatarErrorBoundaryProps {
  fallback: ReactNode;
  children: ReactNode;
}

interface AvatarErrorBoundaryState {
  failed: boolean;
}

class AvatarErrorBoundary extends React.Component<
  AvatarErrorBoundaryProps,
  AvatarErrorBoundaryState
> {
  constructor(props: AvatarErrorBoundaryProps) { super(props); this.state = { failed: false }; }
  static getDerivedStateFromError(): AvatarErrorBoundaryState { return { failed: true }; }
  componentDidCatch() { /* fallback below */ }
  render() { return this.state.failed ? this.props.fallback : this.props.children; }
}

interface AvatarSceneProps {
  state: TurnState;
  outputLevel: number;
  level: number;
  useGlb: boolean;
  glbUrl: string;
}

function AvatarScene({ state, outputLevel, level, useGlb, glbUrl }: AvatarSceneProps) {
  const speaking = state === TURN.SPEAKING;
  const keyColor = STATE_LIGHT[state] || STATE_LIGHT[TURN.IDLE];
  return (
    <Canvas
      camera={{ position: [0, 0.1, 2.7], fov: 30 }}
      dpr={[1, 1.6]}
      gl={{ antialias: true, alpha: true, powerPreference: "low-power" }}
      style={{ width: "100%", height: "100%" }}
    >
      <ambientLight intensity={0.9} />
      <directionalLight position={[2, 3, 3]} intensity={1.0} />
      <pointLight position={[-1.6, 0.8, 2]} intensity={speaking ? 2.4 : 1.4} color={keyColor} distance={8} />
      <Suspense fallback={null}>
        {useGlb ? (
          <GlbModel url={glbUrl} state={state} outputLevel={outputLevel} />
        ) : (
          <TeacherCharacter state={state} outputLevel={outputLevel} level={level} />
        )}
      </Suspense>
    </Canvas>
  );
}

interface AiAvatarProps {
  state: TurnState;
  level?: number;
  outputLevel?: number;
  onClick?: () => void;
  avatarUrl?: string;
}

export default function AiAvatar({ state, level = 0, outputLevel = 0, onClick, avatarUrl }: AiAvatarProps) {
  const glbUrl = avatarUrl || GLB_URL;
  const useGlb = Boolean(glbUrl);
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
            style={{ background: `radial-gradient(circle at 50% 40%, ${STATE_LIGHT[state]}33, transparent 70%)` }}
          />
          <AvatarScene state={state} outputLevel={outputLevel} level={level} useGlb={useGlb} glbUrl={glbUrl} />
        </button>
      </AvatarErrorBoundary>
      <div className="text-center">
        <div className="text-lg font-semibold text-zinc-100">{meta.label}</div>
        <div className="mt-1 text-xs text-zinc-400">{meta.sub}</div>
      </div>
    </div>
  );
}

if (GLB_URL) {
  try {
    useGLTF.preload(GLB_URL);
  } catch {
    /* ignore */
  }
}
