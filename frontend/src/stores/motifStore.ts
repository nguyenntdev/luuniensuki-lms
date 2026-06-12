"use client";

import { createWithEqualityFn } from "zustand/traditional";
import { createJSONStorage, persist } from "zustand/middleware";
import { shallow } from "zustand/shallow";
import toast from "react-hot-toast";

import { getMotifsByUrn, getUrnProgress, unlockProgress } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

export type MotifStatus = "hidden" | "discovered" | "mastered" | string;

export interface Motif {
  id: string | number;
  name?: string;
  mesh_name?: string;
  display_order?: number;
  pos_x?: number;
  pos_y?: number;
  pos_z?: number;
  [key: string]: unknown;
}

export interface MotifProgressEntry {
  status: MotifStatus;
  discoveredAt?: string | null;
  xpAwarded?: number;
  totalXp?: number;
  quizAttempts?: number;
  quizBestScore?: number;
}

interface ProgressUpdatePayload {
  motifId: string | number;
  status: MotifStatus;
  discoveredAt?: string | null;
  xpAwarded?: number;
  totalXp?: number;
}

interface UnlockClickPayload {
  motif: Motif;
  meshName?: string;
  point?: { x: number; y: number; z: number } | null;
}

interface MotifProgressSummary {
  total: number;
  discovered: number;
  mastered: number;
  undiscovered: number;
  unmastered: number;
}

export interface MotifState {
  urnSlug: string | null;
  urnId: string | number | null;
  urnModelUrl: string | null;
  motifsByMesh: Record<string, Motif>;
  motifsById: Record<string, Motif>;
  foundByMotifId: Record<string, boolean>;
  progressByMotifId: Record<string, MotifProgressEntry>;
  selectedMotifId: string | number | null;
  sidebarOpen: boolean;
  loadingMotifs: boolean;
  error: string | null;
  unlockingByMotifId: Record<string, boolean>;
  loadingProgress: boolean;
  progressError: string | null;
  progressLoadedUrn: string | null;
  setSelectedMotifId: (motifId: string | number) => void;
  closeSidebar: () => void;
  applyProgressUpdate: (payload: ProgressUpdatePayload) => void;
  ensureMotifsLoaded: (urnSlug: string) => Promise<void>;
  hydrateProgressForUrn: (urnSlug: string) => Promise<unknown>;
  unlockFromClick: (payload: UnlockClickPayload) => Promise<void>;
}

export function deriveMotifStatus(
  state: MotifState,
  motifId: string | number
): MotifStatus {
  const progress = state.progressByMotifId?.[motifId];
  if (progress?.status) return progress.status;
  if (state.foundByMotifId?.[motifId]) return "discovered";
  return "hidden";
}

export const selectMotifListSorted = (state: MotifState): Motif[] => {
  const list = Object.values(state.motifsById || {});
  list.sort((a, b) => {
    const ao = typeof a?.display_order === "number" ? a.display_order : 0;
    const bo = typeof b?.display_order === "number" ? b.display_order : 0;
    return ao - bo;
  });
  return list;
};

export const selectMotifStatusById = (
  state: MotifState
): Record<string, MotifStatus> => {
  const map: Record<string, MotifStatus> = {};
  for (const motifId of Object.keys(state.motifsById || {})) {
    map[motifId] = deriveMotifStatus(state, motifId);
  }
  return map;
};

export const selectMotifProgressSummary = (
  state: MotifState
): MotifProgressSummary => {
  const motifIds = Object.keys(state.motifsById || {});
  const total = motifIds.length;
  let discovered = 0;
  let mastered = 0;
  for (const motifId of motifIds) {
    const status = deriveMotifStatus(state, motifId);
    if (status !== "hidden") discovered += 1;
    if (status === "mastered") mastered += 1;
  }
  return {
    total,
    discovered,
    mastered,
    undiscovered: Math.max(0, total - discovered),
    unmastered: Math.max(0, total - mastered),
  };
};

export const makeSelectNextUnmasteredMotif =
  (originMotifId?: string | number | null) =>
  (state: MotifState): Motif | null => {
    const list = selectMotifListSorted(state);
    if (!list.length) return null;

    const isUnmastered = (motif: Motif) =>
      deriveMotifStatus(state, motif.id) !== "mastered";

    if (!originMotifId) {
      return list.find(isUnmastered) || null;
    }

    const originIndex = list.findIndex(
      (motif) => String(motif.id) === String(originMotifId)
    );
    if (originIndex === -1) {
      return list.find(isUnmastered) || null;
    }

    for (let offset = 1; offset <= list.length; offset += 1) {
      const idx = (originIndex + offset) % list.length;
      const candidate = list[idx];
      if (candidate && isUnmastered(candidate)) return candidate;
    }
    return null;
  };

export const useMotifStore = createWithEqualityFn<MotifState>()(
  persist(
    (set, get) => ({
      urnSlug: null,
      urnId: null,
      urnModelUrl: null,
      motifsByMesh: {}, // { [mesh_name]: motif }
      motifsById: {}, // { [motif_id]: motif }

      foundByMotifId: {}, // persisted: { [motif_id]: true }
      progressByMotifId: {}, // persisted-ish: { [motif_id]: { status, discoveredAt, xpAwarded, totalXp } }

      selectedMotifId: null,
      sidebarOpen: false,

      loadingMotifs: false,
      error: null,
      unlockingByMotifId: {},
      loadingProgress: false,
      progressError: null,
      progressLoadedUrn: null,

      setSelectedMotifId: (motifId) =>
        set({ selectedMotifId: motifId, sidebarOpen: true }),
      closeSidebar: () => set({ sidebarOpen: false, selectedMotifId: null }),

      applyProgressUpdate: ({
        motifId,
        status,
        discoveredAt,
        xpAwarded,
        totalXp,
      }) =>
        set((s) => ({
          foundByMotifId: { ...s.foundByMotifId, [motifId]: true },
          progressByMotifId: {
            ...s.progressByMotifId,
            [motifId]: {
              status,
              discoveredAt:
                discoveredAt ?? s.progressByMotifId[motifId]?.discoveredAt,
              xpAwarded,
              totalXp,
            },
          },
        })),

      ensureMotifsLoaded: async (urnSlug) => {
        const state = get();
        const hasMotifs =
          Object.keys(state.motifsByMesh).length > 0 ||
          Object.keys(state.motifsById).length > 0;
        if (state.urnSlug === urnSlug && hasMotifs) return;
        if (state.loadingMotifs && state.urnSlug === urnSlug) return;

        const switchingUrn = state.urnSlug !== urnSlug;
        set({
          loadingMotifs: true,
          error: null,
          urnSlug,
          urnId: switchingUrn ? null : state.urnId,
          urnModelUrl: switchingUrn ? null : state.urnModelUrl,
          motifsByMesh: switchingUrn ? {} : state.motifsByMesh,
          motifsById: switchingUrn ? {} : state.motifsById,
        });
        try {
          const payload = (await getMotifsByUrn(urnSlug)) as {
            motifs?: Motif[];
            urn?: { id?: string | number; model_url?: string };
          };
          if (get().urnSlug !== urnSlug) return;
          const motifs: Motif[] = payload.motifs || [];

          const motifsByMesh: Record<string, Motif> = {};
          const motifsById: Record<string, Motif> = {};
          for (const m of motifs) {
            if (m?.mesh_name) motifsByMesh[m.mesh_name] = m;
            if (m?.id) motifsById[m.id] = m;
          }

          set({
            urnId: payload?.urn?.id || null,
            urnModelUrl: payload?.urn?.model_url || null,
            motifsByMesh,
            motifsById,
            loadingMotifs: false,
          });
        } catch (err) {
          if (get().urnSlug !== urnSlug) return;
          set({
            loadingMotifs: false,
            error: err instanceof Error ? err.message : String(err),
          });
        }
      },

      hydrateProgressForUrn: async (urnSlug) => {
        if (!urnSlug) return null;
        const authStatus = useAuthStore.getState().status;
        if (authStatus !== "authed") return null;

        const state = get();
        if (state.loadingProgress && state.progressLoadedUrn === urnSlug) {
          return null;
        }

        set({
          loadingProgress: true,
          progressError: null,
          progressLoadedUrn: urnSlug,
        });

        try {
          const res = (await getUrnProgress({ urnSlug })) as {
            motifs?: Array<{
              motif_id?: string | number;
              status?: MotifStatus;
              discovered_at?: string | null;
              xp_earned?: number;
              quiz_attempts?: number;
              quiz_best_score?: number;
            }>;
          };
          if (get().progressLoadedUrn !== urnSlug) return res;

          set((s) => {
            const nextFound = { ...s.foundByMotifId };
            const nextProgress = { ...s.progressByMotifId };
            const entries = Array.isArray(res?.motifs) ? res.motifs : [];

            for (const entry of entries) {
              if (!entry?.motif_id) continue;
              const motifId = entry.motif_id;
              const status = entry.status || "hidden";
              nextProgress[motifId] = {
                status,
                discoveredAt: entry.discovered_at ?? null,
                xpAwarded: 0,
                totalXp: entry.xp_earned ?? 0,
                quizAttempts: entry.quiz_attempts ?? 0,
                quizBestScore: entry.quiz_best_score ?? 0,
              };
              if (status !== "hidden") {
                nextFound[motifId] = true;
              }
            }

            return {
              foundByMotifId: nextFound,
              progressByMotifId: nextProgress,
              loadingProgress: false,
              progressError: null,
            };
          });

          return res;
        } catch (err) {
          const msg = err instanceof Error ? err.message : String(err);
          set({ loadingProgress: false, progressError: msg });
          return null;
        }
      },

      unlockFromClick: async ({ motif, meshName, point }) => {
        const status = useAuthStore.getState().status;
        console.log("[motifStore] unlockFromClick called", {
          motifId: motif?.id,
          meshName,
          status,
        });
        if (status !== "authed") {
          toast.error("Vui lòng đăng nhập để khám phá!");
          console.log("[motifStore] No session - user not logged in");
          return;
        }
        if (!motif?.id) return;

        const motifId = motif.id;
        const state = get();
        if (state.unlockingByMotifId[motifId]) return;

        set((s) => ({
          unlockingByMotifId: {
            ...s.unlockingByMotifId,
            [motifId]: true,
          },
          error: null,
        }));
        try {
          const hasTrustedPosition = Boolean(
            motif.pos_x || motif.pos_y || motif.pos_z
          );
          const tapPosition =
            point && hasTrustedPosition
              ? {
                  x: Number(point.x),
                  y: Number(point.y),
                  z: Number(point.z),
                }
              : undefined;

          const res = (await unlockProgress({
            motifId,
            meshName,
            tapPosition,
          })) as {
            status: MotifStatus;
            discovered_at?: string | null;
            xp_awarded: number;
            total_xp: number;
          };
          console.log("[motifStore] unlockProgress response", res);

          set((s) => ({
            foundByMotifId: {
              ...s.foundByMotifId,
              [motifId]: true,
            },
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

          if (res.xp_awarded > 0) {
            toast.success(
              `🎯 Đã khám phá: ${motif.name} (+${res.xp_awarded} XP)`
            );
          } else {
            // Already discovered but maybe updated
            toast.success(`🎯 ${motif.name}`);
          }
        } catch (err) {
          console.error("[motifStore] unlockProgress error", err);
          const msg = err instanceof Error ? err.message : String(err);
          set({ error: msg });
          toast.error(`❌ Lỗi: ${msg}`);
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
  ),
  shallow
);
