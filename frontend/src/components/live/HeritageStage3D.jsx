"use client";

import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Html, OrbitControls } from "@react-three/drei";

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
          color={active ? "#f97316" : "#22d3ee"}
          emissive={active ? "#ea580c" : "#0891b2"}
          emissiveIntensity={active ? 0.28 : 0.18}
          roughness={0.2}
          metalness={0.12}
        />
      </mesh>
      {active ? (
        <Html position={[0, 0.19, 0]} center>
          <div className="rounded bg-zinc-950/85 px-2 py-1 text-[10px] text-white shadow">
            {mission.label}
          </div>
        </Html>
      ) : null}
    </group>
  );
}

function Scene({ missions, selectedMissionId, onSelectMission }) {
  return (
    <>
      <color attach="background" args={["#0f172a"]} />
      <fog attach="fog" args={["#0f172a", 3.2, 8]} />

      <ambientLight intensity={0.68} />
      <directionalLight
        position={[2.6, 3.8, 2.2]}
        intensity={1}
        castShadow
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
      />
      <pointLight position={[-2.2, 1.5, -1.8]} intensity={0.35} color="#38bdf8" />

      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.52, 0]} receiveShadow>
        <circleGeometry args={[3.6, 72]} />
        <meshStandardMaterial color="#172554" roughness={0.85} />
      </mesh>

      <RotatingPedestal />

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
    <div className="h-60 w-full overflow-hidden rounded-lg border border-cyan-200/35 bg-zinc-900 shadow-inner">
      <Canvas shadows camera={{ position: [0, 1.65, 3.5], fov: 44 }}>
        <Scene
          missions={safeMissions}
          selectedMissionId={selectedMissionId}
          onSelectMission={onSelectMission}
        />
      </Canvas>
    </div>
  );
}

