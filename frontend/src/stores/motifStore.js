"use client";

import { createWithEqualityFn } from "zustand/traditional";
import { createJSONStorage, persist } from "zustand/middleware";
import { shallow } from "zustand/shallow";
import toast from "react-hot-toast";

import { getMotifsByUrn, getUrnProgress, unlockProgress } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

export function deriveMotifStatus(state, motifId) {
    const progress = state.progressByMotifId?.[motifId];
    if (progress?.status) return progress.status;
    if (state.foundByMotifId?.[motifId]) return "discovered";
    return "hidden";
}

export const selectMotifListSorted = (state) => {
    const list = Object.values(state.motifsById || {});
    list.sort((a, b) => {
        const ao = typeof a?.display_order === "number" ? a.display_order : 0;
        const bo = typeof b?.display_order === "number" ? b.display_order : 0;
        return ao - bo;
    });
    return list;
};

export const selectMotifStatusById = (state) => {
    const map = {};
    for (const motifId of Object.keys(state.motifsById || {})) {
        map[motifId] = deriveMotifStatus(state, motifId);
    }
    return map;
};

export const selectMotifProgressSummary = (state) => {
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

export const makeSelectNextUnmasteredMotif = (originMotifId) => (state) => {
    const list = selectMotifListSorted(state);
    if (!list.length) return null;

    const isUnmastered = (motif) =>
        deriveMotifStatus(state, motif.id) !== "mastered";

    if (!originMotifId) {
        return list.find(isUnmastered) || null;
    }

    const originIndex = list.findIndex(
        (motif) => String(motif.id) === String(originMotifId),
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

export const useMotifStore = createWithEqualityFn(
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
            closeSidebar: () =>
                set({ sidebarOpen: false, selectedMotifId: null }),

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
                                discoveredAt ??
                                s.progressByMotifId[motifId]?.discoveredAt,
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
                    const payload = await getMotifsByUrn(urnSlug);
                    if (get().urnSlug !== urnSlug) return;
                    const motifs = payload.motifs || [];

                    const motifsByMesh = {};
                    const motifsById = {};
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
                if (
                    state.loadingProgress &&
                    state.progressLoadedUrn === urnSlug
                ) {
                    return null;
                }

                set({
                    loadingProgress: true,
                    progressError: null,
                    progressLoadedUrn: urnSlug,
                });

                try {
                    const res = await getUrnProgress({ urnSlug });
                    if (get().progressLoadedUrn !== urnSlug) return res;

                    set((s) => {
                        const nextFound = { ...s.foundByMotifId };
                        const nextProgress = { ...s.progressByMotifId };
                        const entries = Array.isArray(res?.motifs)
                            ? res.motifs
                            : [];

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
                    const msg =
                        err instanceof Error ? err.message : String(err);
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
                        motif.pos_x || motif.pos_y || motif.pos_z,
                    );
                    const tapPosition =
                        point && hasTrustedPosition
                            ? {
                                  x: Number(point.x),
                                  y: Number(point.y),
                                  z: Number(point.z),
                              }
                            : undefined;

                    const res = await unlockProgress({
                        motifId,
                        meshName,
                        tapPosition,
                    });
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
                            `🎯 Đã khám phá: ${motif.name} (+${res.xp_awarded} XP)`,
                        );
                    } else {
                        // Already discovered but maybe updated
                        toast.success(`🎯 ${motif.name}`);
                    }
                } catch (err) {
                    console.error("[motifStore] unlockProgress error", err);
                    const msg =
                        err instanceof Error ? err.message : String(err);
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
        },
    ),
    shallow,
);
