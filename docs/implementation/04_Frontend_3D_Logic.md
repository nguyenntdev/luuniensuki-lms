# 04_Frontend_3D_Logic.md

Frontend “Click-to-Learn” glue for **Next.js + Tailwind + React Three Fiber (R3F)**.

## Deployment Note

- Target domain: `lms.histolab.icu` (recommend serving API behind the same origin or enabling CORS on FastAPI).
- Do **not** store server passwords/SSH credentials in the repo.

---

## Backend Contracts (from `03_Backend_Implementation.md`)

### `GET {API_BASE_URL}/motifs/{urn_name}`

Returns motifs for a given urn (accepts slug like `cao-dinh` or exact name like `Cao Đỉnh`):

```json
{
  "urn": { "id": "uuid", "slug": "cao-dinh", "name": "Cao Đỉnh" },
  "motifs": [
    {
      "id": "uuid",
      "urn_id": "uuid",
      "mesh_name": "mesh_urn_cao_dragon_v1",
      "name": "Long",
      "name_en": "Dragon",
      "category": "thao_moc",
      "rarity": "common",
      "pos_x": 0,
      "pos_y": 0,
      "pos_z": 0,
      "bounding_radius": 1,
      "thumbnail_url": null,
      "silhouette_url": null,
      "is_demo": false,
      "display_order": 1,
      "lesson_intro": "..."
    }
  ]
}
```

### `POST {API_BASE_URL}/progress/unlock`

Unlocks (discovers) a motif for the user:

```json
{
  "user_id": "uuid",
  "mesh_name": "mesh_urn_cao_dragon_v1",
  "tap_position": { "x": 1.23, "y": 4.56, "z": 7.89 }
}
```

Response:

```json
{
  "user_id": "uuid",
  "motif_id": "uuid",
  "status": "discovered",
  "discovered_at": "2025-12-13T10:30:00Z",
  "xp_awarded": 25,
  "total_xp": 250
}
```

---

## 1) Component Structure

Suggested Next.js (App Router) layout:

```txt
src/
  app/
    urns/
      [urnSlug]/
        page.jsx               # Composes UrnViewer + LessonSidebar
  components/
    UrnViewer.js               # R3F Canvas + click picking
    LessonSidebar.js           # Overlay panel for lesson content
  lib/
    api.js                     # Thin fetch wrappers
  stores/
    motifStore.js              # Zustand: motifs, selection, unlocked list
```

Dependencies:

```bash
npm i three @react-three/fiber @react-three/drei zustand
```

---

## 2) “Click-to-Learn” Logic (Crucial)

### Core idea

1) Load motif metadata from the backend (keyed by `mesh_name`).  
2) Render the urn GLB using R3F (`useGLTF`).  
3) On click, read `event.object.name` (the clicked mesh name).  
4) Lookup motif details by `mesh_name` → open the sidebar.  
5) Call `POST /progress/unlock` → mark as **Found** in local state.

> The **mesh names inside the GLB must match** the DB `mesh_name` exactly.

---

## 3) State Management (Zustand)

### `src/lib/api.js`

```js
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function request(path, { method = "GET", body } = {}) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: body ? { "content-type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status} ${res.statusText}: ${text}`);
  }

  return res.json();
}

export async function getMotifsByUrn(urnNameOrSlug) {
  const encoded = encodeURIComponent(urnNameOrSlug);
  return request(`/motifs/${encoded}`);
}

export async function unlockMotifProgress({ userId, motifId, meshName, tapPosition }) {
  return request(`/progress/unlock`, {
    method: "POST",
    body: {
      user_id: userId,
      motif_id: motifId,
      mesh_name: meshName,
      tap_position: tapPosition,
    },
  });
}
```

### `src/stores/motifStore.js`

Stores:

- `motifsByMesh`: lookup from GLB mesh name → motif details (for sidebar).
- `foundByMotifId`: local “Found” flags (persisted).
- `selectedMotifId`: drives sidebar visibility/content.

```js
"use client";

import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import { getMotifsByUrn, unlockMotifProgress } from "@/lib/api";

export const useMotifStore = create(
  persist(
    (set, get) => ({
      urnSlug: null,
      motifsByMesh: {}, // { [mesh_name]: motif }
      motifsById: {}, // { [motif_id]: motif }

      foundByMotifId: {}, // persisted: { [motif_id]: true }
      progressByMotifId: {}, // { [motif_id]: { status, discoveredAt, xpAwarded, totalXp } }

      selectedMotifId: null,
      sidebarOpen: false,

      loadingMotifs: false,
      error: null,
      unlockingByMotifId: {}, // { [motif_id]: true }

      setSelectedMotifId: (motifId) => set({ selectedMotifId: motifId, sidebarOpen: true }),
      closeSidebar: () => set({ sidebarOpen: false, selectedMotifId: null }),

      ensureMotifsLoaded: async (urnSlug) => {
        const state = get();
        if (state.urnSlug === urnSlug && Object.keys(state.motifsByMesh).length > 0) return;

        set({ loadingMotifs: true, error: null, urnSlug });
        try {
          const payload = await getMotifsByUrn(urnSlug);
          const motifs = payload.motifs || [];

          const motifsByMesh = {};
          const motifsById = {};
          for (const m of motifs) {
            if (m?.mesh_name) motifsByMesh[m.mesh_name] = m;
            if (m?.id) motifsById[m.id] = m;
          }

          set({ motifsByMesh, motifsById, loadingMotifs: false });
        } catch (err) {
          set({ loadingMotifs: false, error: err instanceof Error ? err.message : String(err) });
        }
      },

      markFoundLocal: (motifId) =>
        set((state) => ({ foundByMotifId: { ...state.foundByMotifId, [motifId]: true } })),

      unlockFromClick: async ({ userId, motif, meshName, point }) => {
        if (!userId) return;
        if (!motif?.id) return;

        const motifId = motif.id;
        const state = get();
        if (state.unlockingByMotifId[motifId]) return;

        set((s) => ({ unlockingByMotifId: { ...s.unlockingByMotifId, [motifId]: true }, error: null }));
        try {
          const tapPosition = point
            ? { x: Number(point.x), y: Number(point.y), z: Number(point.z) }
            : undefined;

          const res = await unlockMotifProgress({
            userId,
            motifId,
            meshName,
            tapPosition,
          });

          set((s) => ({
            foundByMotifId: { ...s.foundByMotifId, [motifId]: true },
            progressByMotifId: {
              ...s.progressByMotifId,
              [motifId]: {
                status: res.status,
                discoveredAt: res.discovered_at,
                xpAwarded: res.xp_awarded,
                totalXp: res.total_xp,
              },
            },
          }));
        } catch (err) {
          set({ error: err instanceof Error ? err.message : String(err) });
        } finally {
          set((s) => {
            const next = { ...s.unlockingByMotifId };
            delete next[motifId];
            return { unlockingByMotifId: next };
          });
        }
      },
    }),
    {
      name: "luuniensuki-motif-progress",
      version: 1,
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        foundByMotifId: state.foundByMotifId,
        progressByMotifId: state.progressByMotifId,
      }),
    }
  )
);
```

---

## `UrnViewer.js` — 3D Canvas + Mesh Picking

### `src/components/UrnViewer.js`

```jsx
"use client";

import { Component, Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, useCursor, useGLTF } from "@react-three/drei";

import { getUrnDetail } from "@/lib/api";
import { useMotifStore } from "@/stores/motifStore";

function FallbackScene({ motifs, foundByMotifId, onClickMesh }) {
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

        return (
          <mesh
            key={motif.id}
            name={motif.mesh_name}
            position={[x, y, z]}
            onClick={onClickMesh}
            castShadow
          >
            <sphereGeometry args={[0.12, 16, 16]} />
            <meshStandardMaterial color={unlocked ? "#10b981" : "#f59e0b"} />
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

  render() {
    if (this.state.hasError) return this.props.fallback;
    return this.props.children;
  }
}

function UrnModel({ url, onClickMesh }) {
  const gltf = useGLTF(url);

  useEffect(() => {
    gltf.scene.traverse((obj) => {
      if (obj && obj.isMesh) {
        obj.castShadow = true;
        obj.receiveShadow = true;
      }
    });
  }, [gltf]);

  // Attach handler at the root; R3F bubbles events from child meshes.
  return <primitive object={gltf.scene} onClick={onClickMesh} />;
}

export default function UrnViewer({ urnSlug, userId, className = "h-full w-full" }) {
  const ensureMotifsLoaded = useMotifStore((s) => s.ensureMotifsLoaded);
  const motifsByMesh = useMotifStore((s) => s.motifsByMesh);
  const motifsById = useMotifStore((s) => s.motifsById);
  const foundByMotifId = useMotifStore((s) => s.foundByMotifId);
  const setSelectedMotifId = useMotifStore((s) => s.setSelectedMotifId);
  const unlockFromClick = useMotifStore((s) => s.unlockFromClick);

  const [hovered, setHovered] = useState(false);
  useCursor(hovered);

  const [modelUrl, setModelUrl] = useState(null);

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
  const motifList = useMemo(() => Object.values(motifsById), [motifsById]);

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

      const meshName = e?.object?.name;
      if (!meshName) return;

      // 1) Resolve motif details for this mesh (this is the “click -> backend data” bridge).
      let motif = motifsByMesh[meshName] || motifsByMeshLower[meshName.toLowerCase()];
      if (!motif) {
        // If motifs aren't loaded yet (slow network), fetch and try again.
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

      // 2) Open the lesson sidebar immediately (fast UX).
      setSelectedMotifId(motif.id);

      // 3) Persist unlock/progress in backend and mark “Found” locally.
      //    NOTE: If your DB has accurate pos_x/pos_y/pos_z/bounding_radius,
      //    sending e.point enables server-side interaction verification.
      unlockFromClick({
        userId,
        motif,
        meshName,
        point: e.point,
      });
    },
    [ensureMotifsLoaded, motifsByMesh, motifsByMeshLower, setSelectedMotifId, unlockFromClick, urnSlug, userId]
  );

  const fallback = useMemo(
    () => <FallbackScene motifs={motifList} foundByMotifId={foundByMotifId} onClickMesh={handleClick} />,
    [foundByMotifId, handleClick, motifList]
  );

  return (
    <div className={className}>
      <Canvas
        shadows
        camera={{ position: [0, 1.4, 3.6], fov: 45 }}
        onPointerMissed={() => {
          // optional: click empty space to close sidebar
          useMotifStore.getState().closeSidebar();
        }}
        onPointerMove={handleHover}
      >
        <ambientLight intensity={0.7} />
        <directionalLight position={[5, 8, 5]} intensity={1.2} castShadow />

        <Suspense fallback={fallback}>
          <ModelErrorBoundary key={modelUrl || urnSlug} fallback={fallback}>
            {modelUrl ? <UrnModel url={modelUrl} onClickMesh={handleClick} /> : fallback}
          </ModelErrorBoundary>
        </Suspense>

        <OrbitControls enableDamping dampingFactor={0.08} />
      </Canvas>

      {/* Optional UI hint: show “found count” */}
      <div className="pointer-events-none absolute left-4 top-4 rounded bg-black/60 px-3 py-2 text-xs text-white">
        Found: {Object.keys(foundByMotifId).length}
      </div>
    </div>
  );
}
```

---

## `LessonSidebar.js` — Overlay Content Panel

### `src/components/LessonSidebar.js`

```jsx
"use client";

import { useMemo } from "react";
import { useMotifStore } from "@/stores/motifStore";

export default function LessonSidebar() {
  const sidebarOpen = useMotifStore((s) => s.sidebarOpen);
  const selectedMotifId = useMotifStore((s) => s.selectedMotifId);
  const motifsById = useMotifStore((s) => s.motifsById);
  const foundByMotifId = useMotifStore((s) => s.foundByMotifId);
  const progressByMotifId = useMotifStore((s) => s.progressByMotifId);
  const closeSidebar = useMotifStore((s) => s.closeSidebar);

  const motif = useMemo(() => (selectedMotifId ? motifsById[selectedMotifId] : null), [motifsById, selectedMotifId]);
  const isFound = Boolean(selectedMotifId && foundByMotifId[selectedMotifId]);
  const progress = selectedMotifId ? progressByMotifId[selectedMotifId] : null;

  if (!sidebarOpen || !motif) return null;

  return (
    <aside className="absolute right-0 top-0 z-20 h-full w-full max-w-[520px] bg-white shadow-2xl">
      <div className="flex h-full flex-col">
        <div className="flex items-start justify-between gap-4 border-b p-5">
          <div className="min-w-0">
            <h2 className="truncate text-xl font-semibold text-gray-900">{motif.name}</h2>
            {motif.name_en ? (
              <p className="truncate text-sm text-gray-600">{motif.name_en}</p>
            ) : null}
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-700">
                {motif.category} · {motif.rarity}
              </span>
              <span
                className={[
                  "rounded-full px-2 py-1 text-xs font-medium",
                  isFound ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800",
                ].join(" ")}
              >
                {isFound ? "Found" : "Not found yet"}
              </span>
              {progress?.status ? (
                <span className="rounded-full bg-indigo-100 px-2 py-1 text-xs font-medium text-indigo-800">
                  {progress.status}
                </span>
              ) : null}
            </div>
          </div>

          <button
            onClick={closeSidebar}
            className="shrink-0 rounded-md border border-gray-200 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
          >
            Close
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          <h3 className="text-sm font-semibold text-gray-900">Lesson</h3>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-gray-700">
            {motif.lesson_intro || "No lesson content yet."}
          </p>

          {/* If/when you add a backend endpoint for full lesson content:
              fetch it here when selectedMotifId changes, then render it. */}

          {progress?.xpAwarded ? (
            <div className="mt-6 rounded-lg bg-gray-50 p-4 text-sm text-gray-700">
              <div>XP earned: {progress.xpAwarded}</div>
              <div>Total XP: {progress.totalXp}</div>
            </div>
          ) : null}
        </div>
      </div>
    </aside>
  );
}
```

---

## Minimal Page Composition (Example)

### `src/app/urns/[urnSlug]/page.jsx`

```jsx
import UrnExperience from "@/components/UrnExperience";

export default function UrnPage({ params }) {
  return <UrnExperience urnSlug={params.urnSlug} />;
}
```

---

## Notes for Production UX

- `@react-three/fiber` should be loaded **client-only**. If you see SSR crashes on `/urns/*`, wrap your R3F canvas component with `next/dynamic(..., { ssr: false })` (as in `UrnExperience`).
- If the frontend and backend run on different origins, add CORS middleware to FastAPI **or** proxy `/motifs/*` and `/progress/*` through Next.js.
- Ensure GLB mesh names are stable and unique; `event.object.name` must match `mesh_name` in DB.
- For server-side interaction verification (tap distance), keep `pos_x/pos_y/pos_z` and `bounding_radius` accurate in the DB; then sending `e.point` enables robust validation.
