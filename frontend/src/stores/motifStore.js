"use client";

import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import toast from "react-hot-toast";

import { getMotifsByUrn, unlockProgress } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

export const useMotifStore = create(
    persist(
        (set, get) => ({
            urnSlug: null,
            urnId: null,
            motifsByMesh: {}, // { [mesh_name]: motif }
            motifsById: {}, // { [motif_id]: motif }

            foundByMotifId: {}, // persisted: { [motif_id]: true }
            progressByMotifId: {}, // persisted-ish: { [motif_id]: { status, discoveredAt, xpAwarded, totalXp } }

            selectedMotifId: null,
            sidebarOpen: false,

            loadingMotifs: false,
            error: null,
            unlockingByMotifId: {},

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
);
