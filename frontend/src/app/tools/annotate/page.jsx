"use client";
import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, useGLTF } from "@react-three/drei";
import * as THREE from "three";
import { getUrns, saveMotifCoordinates } from "@/lib/api";

// Models hosted on store.histolab.icu (R2 bucket "histolab-ar"), served
// same-origin through the Nginx proxy at /assets/models/ → store.histolab.icu/.
// GLB models are loadable by three.js and can be annotated in-browser.
const MODEL_BASE = "/assets/models";
const storeUrl = (filename) => `${MODEL_BASE}/${filename}`;

// Annotatable GLB models (incl. Cao Đỉnh LOD variants and the full scene).
const STORE_MODELS = [
  { slug: "cao-dinh", label: "Cao Đỉnh", filename: "CAO-DINH-v1.glb", size: "73.96 MB" },
  { slug: "cao-dinh-2k", label: "Cao Đỉnh (LOD 2k)", filename: "CAO-DINH-v1-2k.glb", size: "30.35 MB" },
  { slug: "cao-dinh-1k", label: "Cao Đỉnh (LOD 1k)", filename: "CAO-DINH-v1-1k.glb", size: "27.42 MB" },
  { slug: "cao-dinh-512", label: "Cao Đỉnh (LOD 512)", filename: "CAO-DINH-v1-512.glb", size: "5.21 MB" },
  { slug: "chuong-dinh", label: "Chương Đỉnh", filename: "CHUONG-DINH-v1.glb", size: "84.78 MB" },
  { slug: "huyen-dinh", label: "Huyền Đỉnh", filename: "HUYEN-DINH-v1.glb", size: "89.71 MB" },
  { slug: "nghi-dinh", label: "Nghị Đỉnh", filename: "NGHI-DINH-v1.glb", size: "74.25 MB" },
  { slug: "thuan-dinh", label: "Thuần Đỉnh", filename: "THUAN-DINH-v1.glb", size: "94.70 MB" },
  { slug: "tuyen-dinh", label: "Tuyên Đỉnh", filename: "TUYEN-DINH-v1.glb", size: "84.27 MB" },
  { slug: "scene", label: "Scene (Đại Nội)", filename: "scene-v1.glb", size: "26.56 MB" },
];

// AR-only USDZ models (iOS QuickLook). Not loadable in the 3D annotator —
// listed as download/AR reference links.
const AR_MODELS = [
  { label: "Cao Đỉnh", filename: "CAO-DINH-v1.usdz", size: "60.79 MB" },
  { label: "Chương Đỉnh", filename: "CHUONG-DINH-v1.usdz", size: "89.44 MB" },
  { label: "Huyền Đỉnh", filename: "HUYEN-DINH-v1.usdz", size: "86.71 MB" },
  { label: "Nghị Đỉnh", filename: "NGHI-DINH-v1.usdz", size: "46.97 MB" },
  { label: "Thuần Đỉnh", filename: "THUAN-DINH-v1.usdz", size: "88.22 MB" },
  { label: "Tuyên Đỉnh", filename: "TUYEN-DINH-v1.usdz", size: "89.28 MB" },
  { label: "Đại Nội Huế — Cửu Đỉnh / Huyền Đỉnh", filename: "ĐẠI_NỘI_HUẾ_-_CỬU_ĐỈNH_HUYỀN_ĐỈNH.usdz", size: "24.33 MB" },
];

function AnnotationModel({ url, onClickPoint, markers }) {
  const gltf = useGLTF(url);
  const fit = useMemo(() => {
    const box = new THREE.Box3().setFromObject(gltf.scene);
    const size = new THREE.Vector3();
    const center = new THREE.Vector3();
    box.getSize(size); box.getCenter(center);
    const maxDim = Math.max(size.x, size.y, size.z);
    return { center, scale: maxDim > 0 ? 2.4 / maxDim : 1 };
  }, [gltf]);

  useEffect(() => {
    gltf.scene.traverse((obj) => { if (obj?.isMesh) { obj.castShadow = true; obj.receiveShadow = true; } });
  }, [gltf]);

  const handleClick = useCallback((e) => {
    e.stopPropagation();
    if (e.point) {
      const invScale = 1 / fit.scale;
      const original = e.point.clone().multiplyScalar(invScale).add(fit.center);
      onClickPoint({ x: original.x, y: original.y, z: original.z });
    }
  }, [onClickPoint, fit]);

  return (
    <group scale={fit.scale} position={fit.center.clone().multiplyScalar(-fit.scale)}>
      <primitive object={gltf.scene} onClick={handleClick} />
      {markers.map((m, idx) => (
        <mesh key={idx} position={[m.pos_x, m.pos_y, m.pos_z]}>
          <sphereGeometry args={[m.bounding_radius || 0.05, 16, 16]} />
          <meshStandardMaterial color="#10b981" transparent opacity={0.7} />
        </mesh>
      ))}
    </group>
  );
}

export default function AnnotatePage() {
  const [urns, setUrns] = useState([]);
  const [selectedUrn, setSelectedUrn] = useState(null);
  const [storeModel, setStoreModel] = useState(null);
  const [markers, setMarkers] = useState([]);
  const [pendingPoint, setPendingPoint] = useState(null);
  const [motifName, setMotifName] = useState("");
  const [meshName, setMeshName] = useState("");
  const [boundingRadius, setBoundingRadius] = useState(0.08);
  const [saveState, setSaveState] = useState("idle"); // idle | saving | saved | error
  const [autoSave, setAutoSave] = useState(true);
  const fileInputRef = useRef(null);

  useEffect(() => { getUrns().then(setUrns).catch(console.error); }, []);

  // Active slug + model URL come from either a seeded urn or a store-catalog model.
  const activeSlug = useMemo(
    () => storeModel?.slug || selectedUrn?.slug || "",
    [storeModel, selectedUrn]
  );
  const modelUrl = useMemo(
    () => (storeModel ? storeUrl(storeModel.filename) : selectedUrn?.model_url || null),
    [storeModel, selectedUrn]
  );
  const handleClickPoint = useCallback((point) => setPendingPoint(point), []);
  const urnMarkers = useMemo(
    () => markers.filter((m) => m.urn_slug === activeSlug),
    [markers, activeSlug]
  );

  const handleAddMarker = useCallback(() => {
    if (!pendingPoint || !motifName.trim()) return;
    const marker = { urn_slug: activeSlug, motif_name: motifName.trim(),
      mesh_name: meshName.trim() || motifName.trim(), pos_x: pendingPoint.x, pos_y: pendingPoint.y,
      pos_z: pendingPoint.z, bounding_radius: boundingRadius };
    setMarkers((prev) => [...prev, marker]);
    setPendingPoint(null); setMotifName(""); setMeshName("");
    // Auto-save the new marker immediately (admin-only endpoint).
    if (autoSave && activeSlug) {
      setSaveState("saving");
      saveMotifCoordinates({ coordinates: [marker] })
        .then(() => setSaveState("saved"))
        .catch(() => setSaveState("error"));
    }
  }, [pendingPoint, motifName, meshName, boundingRadius, activeSlug, autoSave]);

  const handleRemoveMarker = useCallback((idx) => setMarkers((prev) => prev.filter((_, i) => i !== idx)), []);

  // Persist all current markers (manual "Save to DB").
  const handleSaveAll = useCallback(() => {
    if (!markers.length) return;
    setSaveState("saving");
    saveMotifCoordinates({ coordinates: markers })
      .then(() => setSaveState("saved"))
      .catch(() => setSaveState("error"));
  }, [markers]);

  const handleExport = useCallback(() => {
    const blob = new Blob([JSON.stringify(markers, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = `motif-coordinates-${activeSlug || "all"}.json`;
    a.click(); URL.revokeObjectURL(url);
  }, [markers, activeSlug]);

  const handleImport = useCallback((e) => {
    const file = e.target.files?.[0]; if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => { try { const d = JSON.parse(ev.target?.result); if (Array.isArray(d)) setMarkers((p) => [...p, ...d]); } catch {} };
    reader.readAsText(file);
  }, []);

  return (
    <main className="flex h-screen">
      <div className="flex-1 bg-gray-900">
        <Canvas shadows camera={{ position: [0, 1.4, 3.6], fov: 45 }}>
          <ambientLight intensity={0.7} />
          <directionalLight position={[5, 8, 5]} intensity={1.2} castShadow />
          <Suspense fallback={null}>{modelUrl && <AnnotationModel url={modelUrl} onClickPoint={handleClickPoint} markers={urnMarkers} />}</Suspense>
          <OrbitControls enableDamping dampingFactor={0.08} />
          <gridHelper args={[10, 10, "#444", "#222"]} />
        </Canvas>
      </div>
      <aside className="w-96 overflow-y-auto border-l bg-white p-4">
        <h1 className="text-xl font-display font-bold text-gray-900">Motif Annotation Tool</h1>
        <p className="mt-1 text-sm text-gray-600">Click on model to mark motif positions</p>
        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700">Select Urn (seeded)</label>
          <select className="mt-1 block w-full rounded border-gray-300 shadow-sm" value={selectedUrn?.id || ""}
            onChange={(e) => { setSelectedUrn(urns.find((u) => String(u.id) === e.target.value) || null); setStoreModel(null); }}>
            <option value="">-- Choose Urn --</option>
            {urns.map((u) => <option key={u.id} value={u.id}>{u.name} ({u.slug})</option>)}
          </select>
        </div>
        <div className="mt-3">
          <label className="block text-sm font-medium text-gray-700">Or Store Model (store.histolab.icu)</label>
          <select className="mt-1 block w-full rounded border-gray-300 shadow-sm" value={storeModel?.filename || ""}
            onChange={(e) => { setStoreModel(STORE_MODELS.find((m) => m.filename === e.target.value) || null); setSelectedUrn(null); }}>
            <option value="">-- Choose GLB model --</option>
            {STORE_MODELS.map((m) => <option key={m.filename} value={m.filename}>{m.label} — {m.size}</option>)}
          </select>
        </div>
        <details className="mt-3 rounded bg-gray-50 p-2 text-xs text-gray-600">
          <summary className="cursor-pointer font-medium text-gray-700">AR models (USDZ, iOS QuickLook)</summary>
          <ul className="mt-2 space-y-1">
            {AR_MODELS.map((m) => (
              <li key={m.filename} className="flex items-center justify-between gap-2">
                <span className="truncate">{m.label}</span>
                <a href={storeUrl(m.filename)} target="_blank" rel="noopener noreferrer"
                   className="shrink-0 text-blue-600 underline">{m.size}</a>
              </li>
            ))}
          </ul>
          <p className="mt-2 text-gray-400">USDZ is AR-only and cannot be annotated in the 3D editor.</p>
        </details>
        {pendingPoint && (
          <div className="mt-4 rounded-lg bg-amber-50 p-3">
            <div className="text-sm font-medium text-amber-800">New Point</div>
            <div className="mt-1 font-mono text-xs">x:{pendingPoint.x.toFixed(3)} y:{pendingPoint.y.toFixed(3)} z:{pendingPoint.z.toFixed(3)}</div>
            <div className="mt-2 space-y-2">
              <input type="text" placeholder="Motif name" className="block w-full rounded border px-2 py-1 text-sm" value={motifName} onChange={(e) => setMotifName(e.target.value)} />
              <input type="text" placeholder="Mesh name (opt)" className="block w-full rounded border px-2 py-1 text-sm" value={meshName} onChange={(e) => setMeshName(e.target.value)} />
              <div className="flex items-center gap-2"><label className="text-xs">Radius:</label>
                <input type="number" step="0.01" min="0.01" className="w-20 rounded border px-2 py-1 text-sm" value={boundingRadius} onChange={(e) => setBoundingRadius(parseFloat(e.target.value) || 0.08)} />
              </div>
              <div className="flex gap-2">
                <button onClick={handleAddMarker} className="rounded bg-emerald-600 px-3 py-1 text-sm text-white">Add</button>
                <button onClick={() => setPendingPoint(null)} className="rounded border px-3 py-1 text-sm">Hủy</button>
              </div>
            </div>
          </div>
        )}
        <div className="mt-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-display font-semibold">
              Markers (<span className="font-display tabular-nums">{markers.length}</span>)
            </h2>
            <div className="flex gap-2">
              <input type="file" accept=".json" ref={fileInputRef} onChange={handleImport} className="hidden" />
              <button onClick={() => fileInputRef.current?.click()} className="rounded border px-2 py-1 text-xs">Import</button>
              <button onClick={handleExport} disabled={!markers.length} className="rounded bg-primary px-2 py-1 text-xs text-primary-foreground disabled:opacity-50">Export</button>
            </div>
          </div>
          <div className="mt-2 flex items-center justify-between rounded bg-emerald-50 px-2 py-1 text-xs">
            <label className="flex items-center gap-1 text-emerald-800">
              <input type="checkbox" checked={autoSave} onChange={(e) => setAutoSave(e.target.checked)} />
              Auto-save (admin)
            </label>
            <button onClick={handleSaveAll} disabled={!markers.length || saveState === "saving"}
              className="rounded bg-emerald-600 px-2 py-1 text-white disabled:opacity-50">
              {saveState === "saving" ? "Saving…" : "Save all to DB"}
            </button>
          </div>
          {saveState === "saved" && <div className="mt-1 text-[11px] text-emerald-700">Saved to database</div>}
          {saveState === "error" && <div className="mt-1 text-[11px] text-red-600">Save failed (admin role required)</div>}
          <div className="mt-2 max-h-64 space-y-1 overflow-y-auto">
            {markers.map((m, idx) => (
              <div key={idx} className="flex items-start justify-between rounded bg-gray-50 p-2 text-xs">
                <div><div className="font-medium">{m.motif_name}</div><div className="text-gray-500">{m.urn_slug}</div>
                  <div className="font-mono text-gray-400">({m.pos_x.toFixed(2)},{m.pos_y.toFixed(2)},{m.pos_z.toFixed(2)})</div></div>
                <button onClick={() => handleRemoveMarker(idx)} className="text-red-500">✕</button>
              </div>
            ))}
          </div>
        </div>
        <div className="mt-4 rounded bg-gray-100 p-3 text-xs text-gray-600">
          <b>Steps:</b> 1.Select urn 2.Click model 3.Enter name 4.Add marker 5.Export JSON
        </div>
      </aside>
    </main>
  );
}
