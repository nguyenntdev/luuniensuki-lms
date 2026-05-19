"use client";

/**
 * useRenderPerf — measures 3D model render performance for one model load.
 *
 * Tracks three metrics per model:
 *   - ttf_ms   : time-to-first-frame (request start → first painted frame)
 *   - ttfi_ms  : time-to-first-interaction (request start → ready for user input)
 *   - avg_fps  : averaged frames-per-second over the first 5 seconds after first frame
 *
 * On unmount, model change, or after the FPS window completes, fires a
 * fire-and-forget POST /api/v1/analytics/events with event_name='render_performance'
 * and a payload describing the model + measured metrics + device context.
 *
 * Networking is best-effort and never blocks rendering.
 */

import { useEffect, useRef } from "react";

const FPS_WINDOW_MS = 5000;

function deriveLodLabel(modelUrl) {
    if (!modelUrl) return null;
    // Match e.g. CAO-DINH-v1-512.glb, CAO-DINH-v1-1k.glb, CAO-DINH-v1-2k.glb
    const m = String(modelUrl).match(/-(\d+k?)\.glb(?:$|\?)/i);
    return m ? m[1].toLowerCase() : null;
}

function readGpuRenderer() {
    if (typeof document === "undefined") return null;
    try {
        const canvas = document.createElement("canvas");
        const gl =
            canvas.getContext("webgl2") ||
            canvas.getContext("webgl") ||
            canvas.getContext("experimental-webgl");
        if (!gl) return null;
        const ext = gl.getExtension("WEBGL_debug_renderer_info");
        if (!ext) {
            // Some browsers (Firefox in privacy mode, Safari) block this.
            return gl.getParameter(gl.RENDERER) || null;
        }
        return gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) || null;
    } catch {
        return null;
    }
}

async function fireRenderPerfEvent(payload) {
    if (typeof window === "undefined") return;
    try {
        const body = JSON.stringify({
            events: [
                {
                    event_name: "render_performance",
                    event_category: "performance",
                    path:
                        typeof window !== "undefined"
                            ? window.location?.pathname || null
                            : null,
                    payload,
                },
            ],
        });
        const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "";
        // keepalive lets the request survive page unload — important because the
        // hook may flush on unmount.
        await fetch(`${apiBase}/api/v1/analytics/events`, {
            method: "POST",
            headers: { "content-type": "application/json" },
            body,
            credentials: "include",
            keepalive: true,
            cache: "no-store",
        });
    } catch {
        // Fire-and-forget. Never throw into the render path.
    }
}

/**
 * @param {object} args
 * @param {string|null} args.modelUrl — the GLB URL being loaded
 * @param {number|null} args.fileSizeBytes — optional, if known ahead of time
 * @param {boolean} [args.enabled=true] — set false to disable instrumentation
 */
export default function useRenderPerf({
    modelUrl,
    fileSizeBytes = null,
    enabled = true,
} = {}) {
    // Track per-model state in a ref so React re-renders don't reset it.
    const stateRef = useRef(null);

    // Mark first-frame painted (called from <Canvas>'s onCreated or first useFrame).
    const markFirstFrame = useRef(() => {});
    // Mark first-interaction-ready.
    const markFirstInteraction = useRef(() => {});

    useEffect(() => {
        if (!enabled || !modelUrl || typeof window === "undefined") {
            return undefined;
        }

        const startedAt = performance.now();
        const lodLabel = deriveLodLabel(modelUrl);
        const gpuRenderer = readGpuRenderer();

        const state = {
            startedAt,
            firstFrameAt: null,
            firstInteractionAt: null,
            frameCount: 0,
            fpsWindowStartedAt: null,
            avgFps: null,
            rafId: null,
            timeoutId: null,
            sent: false,
        };
        stateRef.current = state;

        const sendOnce = () => {
            if (state.sent) return;
            state.sent = true;
            const ttf =
                state.firstFrameAt != null
                    ? Math.round(state.firstFrameAt - state.startedAt)
                    : null;
            const ttfi =
                state.firstInteractionAt != null
                    ? Math.round(state.firstInteractionAt - state.startedAt)
                    : null;
            // If FPS window never completed, compute a partial average.
            let avgFps = state.avgFps;
            if (avgFps == null && state.fpsWindowStartedAt != null) {
                const elapsed = performance.now() - state.fpsWindowStartedAt;
                if (elapsed > 0 && state.frameCount > 0) {
                    avgFps =
                        Math.round(
                            (state.frameCount / (elapsed / 1000)) * 10,
                        ) / 10;
                }
            }

            fireRenderPerfEvent({
                model_url: modelUrl,
                lod_label: lodLabel,
                file_size_bytes: fileSizeBytes,
                ttf_ms: ttf,
                ttfi_ms: ttfi,
                avg_fps: avgFps,
                gpu_renderer: gpuRenderer,
                device_pixel_ratio:
                    typeof window !== "undefined"
                        ? window.devicePixelRatio || 1
                        : 1,
                viewport_width:
                    typeof window !== "undefined"
                        ? window.innerWidth || null
                        : null,
                viewport_height:
                    typeof window !== "undefined"
                        ? window.innerHeight || null
                        : null,
            });
        };

        const tickFps = () => {
            if (!state.fpsWindowStartedAt) return;
            state.frameCount += 1;
            const elapsed = performance.now() - state.fpsWindowStartedAt;
            if (elapsed >= FPS_WINDOW_MS) {
                state.avgFps =
                    Math.round((state.frameCount / (elapsed / 1000)) * 10) /
                    10;
                state.rafId = null;
                sendOnce();
                return;
            }
            state.rafId = window.requestAnimationFrame(tickFps);
        };

        markFirstFrame.current = () => {
            if (state.firstFrameAt != null) return;
            state.firstFrameAt = performance.now();
            // First interaction defaults to first frame if not separately marked.
            if (state.firstInteractionAt == null) {
                state.firstInteractionAt = state.firstFrameAt;
            }
            state.fpsWindowStartedAt = state.firstFrameAt;
            state.rafId = window.requestAnimationFrame(tickFps);
            // Safety net: if the FPS window never ticks (page hidden), still flush.
            state.timeoutId = window.setTimeout(
                () => sendOnce(),
                FPS_WINDOW_MS + 1500,
            );
        };

        markFirstInteraction.current = () => {
            if (state.firstInteractionAt != null) return;
            state.firstInteractionAt = performance.now();
        };

        return () => {
            if (state.rafId != null) {
                window.cancelAnimationFrame(state.rafId);
            }
            if (state.timeoutId != null) {
                window.clearTimeout(state.timeoutId);
            }
            // Flush whatever we have so far on unmount / model change.
            sendOnce();
            stateRef.current = null;
        };
    }, [modelUrl, fileSizeBytes, enabled]);

    return {
        markFirstFrame: () => markFirstFrame.current(),
        markFirstInteraction: () => markFirstInteraction.current(),
    };
}
