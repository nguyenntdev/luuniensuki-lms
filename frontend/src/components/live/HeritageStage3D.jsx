"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Html, OrbitControls } from "@react-three/drei";
import { Box3, Vector3 } from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

function RotatingPedestal() {
  const groupRef = useRef(null);

  useFrame((_, delta) => {
    if (!groupRef.current) return;
    groupRef.current.rotation.y += delta * 0.18;
  });

  return (
    <group ref={groupRef}>
      <mesh position={[0, -0.3, 0]} receiveShadow castShadow>
        <cylinderGeometry args={[1.65, 1.65, 0.4, 64]} />
        <meshStandardMaterial color="#3b3028" roughness={0.75} />
      </mesh>

      <mesh position={[0, 0.3, 0]} receiveShadow castShadow>
        <cylinderGeometry args={[1.2, 1.2, 0.85, 64]} />
        <meshStandardMaterial color="#8f7347" roughness={0.45} metalness={0.3} />
      </mesh>

      <mesh position={[0, 0.85, 0]} castShadow>
        <torusGeometry args={[1.05, 0.07, 22, 120]} />
        <meshStandardMaterial color="#d5b27a" metalness={0.4} roughness={0.3} />
      </mesh>
    </group>
  );
}

function SceneStatusBadge({ tone = "info", message }) {
  const palette =
    tone === "error"
      ? "border-red-500/40 bg-red-500/10 text-red-200"
      : "border-amber-500/40 bg-amber-500/10 text-amber-100";

  return (
    <Html position={[0, 1.55, 0]} center>
      <div
        className={`rounded-full border px-3 py-1 text-[10px] font-medium shadow ${palette}`}
      >
        {message}
      </div>
    </Html>
  );
}

function MissionMarker({ mission, active, onSelect }) {
  return (
    <group position={mission.position}>
      <mesh
        castShadow
        onClick={(event) => {
          event.stopPropagation();
          onSelect(mission.id);
        }}
      >
        <sphereGeometry args={[active ? 0.095 : 0.075, 28, 28]} />
        <meshStandardMaterial
          color={active ? "#d9a441" : "#14b8a6"}
          emissive={active ? "#b45309" : "#0f766e"}
          emissiveIntensity={active ? 0.35 : 0.2}
          roughness={0.2}
          metalness={0.12}
        />
      </mesh>
      {active ? (
        <Html position={[0, 0.19, 0]} center>
          <div className="rounded-full border border-amber-400/25 bg-black/80 px-2.5 py-1 text-[10px] text-amber-100 shadow">
            {mission.label}
          </div>
        </Html>
      ) : null}
    </group>
  );
}

function Scene({ missions, selectedMissionId, onSelectMission, modelUrl }) {
  const modelGroupRef = useRef(null);
  const [modelScene, setModelScene] = useState(null);
  const [modelLoading, setModelLoading] = useState(false);
  const [modelFailed, setModelFailed] = useState(false);

  useEffect(() => {
    const normalized = String(modelUrl || "").trim();
    if (!normalized) {
      setModelScene(null);
      setModelLoading(false);
      setModelFailed(false);
      return undefined;
    }

    let cancelled = false;
    const loader = new GLTFLoader();
    setModelLoading(true);
    setModelFailed(false);
    setModelScene(null);

    loader.load(
      normalized,
      (gltf) => {
        if (cancelled) return;
        const scene = gltf?.scene?.clone(true) || null;
        if (!scene) {
          setModelFailed(true);
          setModelLoading(false);
          return;
        }
        scene.traverse((node) => {
          if (!node || !node.isMesh) return;
          node.castShadow = true;
          node.receiveShadow = true;
        });
        setModelScene(scene);
        setModelLoading(false);
        setModelFailed(false);
      },
      undefined,
      () => {
        if (cancelled) return;
        setModelScene(null);
        setModelLoading(false);
        setModelFailed(true);
      },
    );

    return () => {
      cancelled = true;
    };
  }, [modelUrl]);

  const modelLayout = useMemo(() => {
    if (!modelScene) return null;
    modelScene.updateMatrixWorld(true);
    const box = new Box3().setFromObject(modelScene);
    if (box.isEmpty()) return null;

    const size = new Vector3();
    const center = new Vector3();
    box.getSize(size);
    box.getCenter(center);
    const maxEdge = Math.max(size.x, size.y, size.z, 0.001);
    const scale = 1.85 / maxEdge;
    return {
      center,
      floorY: box.min.y,
      scale,
    };
  }, [modelScene]);

  const hasModel = Boolean(modelScene && modelLayout);
  useFrame((_, delta) => {
    if (!hasModel || !modelGroupRef.current) return;
    modelGroupRef.current.rotation.y += delta * 0.16;
  });

  return (
    <>
      <color attach="background" args={["#120c07"]} />
      <fog attach="fog" args={["#120c07", 3.0, 8.2]} />

      <ambientLight intensity={0.58} />
      <directionalLight
        position={[2.4, 4.2, 2.1]}
        intensity={1.15}
        castShadow
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
        color="#ffd39a"
      />
      <pointLight position={[-2.4, 1.7, -1.9]} intensity={0.32} color="#14b8a6" />
      <pointLight position={[0.1, 0.55, 2.4]} intensity={0.24} color="#d97706" />

      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.52, 0]} receiveShadow>
        <circleGeometry args={[3.6, 72]} />
        <meshStandardMaterial color="#26170b" roughness={0.88} metalness={0.08} />
      </mesh>

      {hasModel ? (
        <group
          ref={modelGroupRef}
          position={[0, -0.36, 0]}
          scale={modelLayout.scale}
        >
          <primitive
            object={modelScene}
            position={[
              -modelLayout.center.x,
              -modelLayout.floorY,
              -modelLayout.center.z,
            ]}
          />
        </group>
      ) : (
        <RotatingPedestal />
      )}

      {modelLoading ? (
        <SceneStatusBadge message="Đang tải model 3D nhẹ..." />
      ) : null}
      {modelFailed ? (
        <SceneStatusBadge
          tone="error"
          message="Không tải được model. Đang dùng mô hình dự phòng."
        />
      ) : null}

      {missions.map((mission) => (
        <MissionMarker
          key={mission.id}
          mission={mission}
          active={mission.id === selectedMissionId}
          onSelect={onSelectMission}
        />
      ))}

      <OrbitControls
        enablePan={false}
        enableZoom={true}
        minDistance={2.2}
        maxDistance={5}
        minPolarAngle={0.75}
        maxPolarAngle={1.45}
      />
    </>
  );
}

export default function HeritageStage3D({
  missions = [],
  selectedMissionId = null,
  onSelectMission,
  modelUrl = "",
}) {
  const safeMissions = useMemo(
    () =>
      missions.filter(
        (mission) =>
          mission &&
          mission.id &&
          Array.isArray(mission.position) &&
          mission.position.length === 3,
      ),
    [missions],
  );

  return (
    <div className="relative h-64 w-full overflow-hidden rounded-2xl border border-amber-500/20 bg-[#0b0704] shadow-inner shadow-black sm:h-72">
      <div className="pointer-events-none absolute inset-0 z-10 bg-[radial-gradient(circle_at_50%_10%,rgba(217,164,65,0.14),transparent_36%),linear-gradient(180deg,transparent_62%,rgba(0,0,0,0.35))]" />
      <Canvas shadows camera={{ position: [0, 1.65, 3.5], fov: 44 }}>
        <Scene
          missions={safeMissions}
          selectedMissionId={selectedMissionId}
          onSelectMission={onSelectMission}
          modelUrl={modelUrl}
        />
      </Canvas>
    </div>
  );
}
