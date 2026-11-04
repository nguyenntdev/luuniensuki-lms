/**
 * Offline Sync & IndexedDB Engine for STTTNNĐ (Lưu Niên — Đại Nội Huế).
 * Spec: STTT-SPEC-PWA-PRINT-001 (§2.2 Dynamic Content & Submissions)
 * Ticket: V5-T056 (Wave W05, Slot A06)
 *
 * Stores student responses, M-E-E research claims, field-work worksheets,
 * 3D/AR relic inspections, and progression actions when network connection is severed.
 * Automatically synchronizes to server upon reconnection via `window.addEventListener('online')`
 * with client idempotency keys, retry logic, conflict resolution, and server ACK verification.
 */

import type { StudentSubmission } from "./map-types";

const DB_NAME = "luunien_imperial_offline_db";
const DB_VERSION = 2;
const STORE_NAME = "offline_submissions_queue";
const ACTIONS_STORE_NAME = "offline_actions_queue";

export type OfflineActionType = "inspection" | "submission" | "progression";

export interface QueuedOfflineSubmission {
  id: string; // generated client-side id
  idempotency_key?: string;
  submission: Omit<StudentSubmission, "id" | "submitted_at" | "status">;
  enqueued_at: string;
  retry_count: number;
  status?: "pending" | "syncing" | "synced" | "acknowledged" | "updated" | "conflict" | "failed";
  last_error?: string;
  server_ack?: Record<string, any>;
  xp_awarded?: number;
  conflict_resolution?: string;
}

export interface QueuedOfflineAction {
  id: string;
  idempotency_key: string;
  action_type: OfflineActionType;
  resource: string;
  payload: Record<string, any>;
  enqueued_at: string;
  retry_count: number;
  status: "pending" | "syncing" | "synced" | "acknowledged" | "updated" | "conflict" | "failed";
  last_error?: string;
  server_ack?: Record<string, any>;
  xp_awarded?: number;
  conflict_resolution?: string;
}

export type SyncStatusListener = (event: {
  type: "online" | "offline" | "sync_start" | "sync_success" | "sync_error";
  pendingCount: number;
  syncedCount?: number;
  message?: string;
}) => void;

let dbPromise: Promise<IDBDatabase> | null = null;
const statusListeners = new Set<SyncStatusListener>();

/**
 * Open or initialize the IndexedDB database.
 */
function getDB(): Promise<IDBDatabase> {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("IndexedDB is not available in SSR"));
  }

  if (!("indexedDB" in window)) {
    return Promise.reject(new Error("Browser does not support IndexedDB"));
  }

  if (dbPromise) {
    return dbPromise;
  }

  dbPromise = new Promise((resolve, reject) => {
    const request = window.indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, { keyPath: "id" });
        store.createIndex("enqueued_at", "enqueued_at", { unique: false });
      }
      if (!db.objectStoreNames.contains(ACTIONS_STORE_NAME)) {
        const actionsStore = db.createObjectStore(ACTIONS_STORE_NAME, { keyPath: "id" });
        actionsStore.createIndex("enqueued_at", "enqueued_at", { unique: false });
        actionsStore.createIndex("action_type", "action_type", { unique: false });
      }
    };

    request.onsuccess = () => {
      resolve(request.result);
    };

    request.onerror = () => {
      dbPromise = null;
      reject(request.error || new Error("Failed to open IndexedDB"));
    };
  });

  return dbPromise;
}

/**
 * Notify all subscribed listeners of connectivity or sync changes.
 */
function notifyListeners(payload: Parameters<SyncStatusListener>[0]) {
  statusListeners.forEach((listener) => {
    try {
      listener(payload);
    } catch (err) {
      console.error("[offline-sync] Listener error:", err);
    }
  });
}

/**
 * Subscribe to sync state changes (syncing, success, offline, online).
 * Returns an unsubscribe callback.
 */
export function subscribeOfflineSync(listener: SyncStatusListener): () => void {
  statusListeners.add(listener);
  // Emit current pending count immediately if in browser
  if (typeof window !== "undefined" || typeof localStorage !== "undefined") {
    Promise.all([getPendingSubmissions(), getPendingActions()])
      .then(([pendingSubs, pendingActions]) => {
        const totalPending = pendingSubs.length + pendingActions.length;
        const isOnline =
          typeof navigator !== "undefined" && typeof navigator.onLine === "boolean"
            ? navigator.onLine
            : true;
        listener({
          type: isOnline ? "online" : "offline",
          pendingCount: totalPending,
          message: isOnline
            ? undefined
            : "Đang hoạt động ở chế độ ngoại tuyến",
        });
      })
      .catch(() => {});
  }
  return () => {
    statusListeners.delete(listener);
  };
}

// ============================================================================
// 1. Student Submission Queue Management
// ============================================================================

/**
 * Enqueue a student submission into IndexedDB when offline.
 */
export async function enqueueOfflineSubmission(
  submissionData: Omit<StudentSubmission, "id" | "submitted_at" | "status">,
  idempotencyKey?: string,
): Promise<QueuedOfflineSubmission> {
  const opId = `queue-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
  const item: QueuedOfflineSubmission = {
    id: opId,
    idempotency_key: idempotencyKey || `idemp_sub_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    submission: submissionData,
    enqueued_at: new Date().toISOString(),
    retry_count: 0,
    status: "pending",
  };

  try {
    const db = await getDB();
    await new Promise<void>((resolve, reject) => {
      const transaction = db.transaction([STORE_NAME], "readwrite");
      const store = transaction.objectStore(STORE_NAME);
      const request = store.add(item);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });

    const pending = await getPendingSubmissions();
    notifyListeners({
      type: "sync_start",
      pendingCount: pending.length,
      message: "Đã lưu bài làm vào bộ nhớ ngoại tuyến cục bộ.",
    });

    return item;
  } catch (err) {
    console.warn("[offline-sync] IndexedDB unavailable, using localStorage fallback:", err);
    fallbackLocalStorageEnqueue(item);
    const pending = await getPendingSubmissions();
    notifyListeners({
      type: "sync_start",
      pendingCount: pending.length,
      message: "Đã lưu bài làm vào bộ nhớ ngoại tuyến cục bộ.",
    });
    return item;
  }
}

/**
 * Retrieve all pending queued submissions from IndexedDB.
 */
export async function getPendingSubmissions(): Promise<QueuedOfflineSubmission[]> {
  try {
    const db = await getDB();
    return await new Promise<QueuedOfflineSubmission[]>((resolve, reject) => {
      const transaction = db.transaction([STORE_NAME], "readonly");
      const store = transaction.objectStore(STORE_NAME);
      const request = store.getAll();

      request.onsuccess = () => {
        const results = (request.result as QueuedOfflineSubmission[]) || [];
        resolve(results);
      };
      request.onerror = () => reject(request.error);
    });
  } catch (err) {
    console.warn("[offline-sync] IndexedDB read failed, checking localStorage fallback:", err);
    return fallbackLocalStorageGet();
  }
}

/**
 * Remove a single submission from the offline queue by ID.
 */
export async function clearPendingSubmission(id: string): Promise<void> {
  try {
    const db = await getDB();
    await new Promise<void>((resolve, reject) => {
      const transaction = db.transaction([STORE_NAME], "readwrite");
      const store = transaction.objectStore(STORE_NAME);
      const request = store.delete(id);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  } catch (err) {
    console.error(`[offline-sync] Failed to clear item ${id}:`, err);
  } finally {
    fallbackLocalStorageDelete(id);
  }
}

/**
 * Clear all submissions from the queue.
 */
export async function clearAllPendingSubmissions(): Promise<void> {
  try {
    const db = await getDB();
    await new Promise<void>((resolve, reject) => {
      const transaction = db.transaction([STORE_NAME], "readwrite");
      const store = transaction.objectStore(STORE_NAME);
      const request = store.clear();

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  } catch (err) {
    console.error("[offline-sync] Failed to clear all items:", err);
  } finally {
    if (typeof window !== "undefined" || typeof localStorage !== "undefined") {
      try {
        localStorage.removeItem(LS_FALLBACK_KEY);
      } catch {}
    }
  }
}

// ============================================================================
// 2. Generic Offline Action Queue (Inspections, Progression, Submissions)
// ============================================================================

/**
 * Enqueue a generic offline action (inspection, progression, or submission).
 */
export async function enqueueOfflineAction(
  actionType: OfflineActionType,
  resource: string,
  payload: Record<string, any>,
  idempotencyKey?: string,
): Promise<QueuedOfflineAction> {
  const opId = `act-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
  const item: QueuedOfflineAction = {
    id: opId,
    idempotency_key: idempotencyKey || `idemp_${actionType}_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    action_type: actionType,
    resource,
    payload,
    enqueued_at: new Date().toISOString(),
    retry_count: 0,
    status: "pending",
  };

  try {
    const db = await getDB();
    await new Promise<void>((resolve, reject) => {
      const transaction = db.transaction([ACTIONS_STORE_NAME], "readwrite");
      const store = transaction.objectStore(ACTIONS_STORE_NAME);
      const request = store.add(item);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  } catch (err) {
    console.warn("[offline-sync] Actions IndexedDB unavailable, using fallback:", err);
    fallbackActionEnqueue(item);
  }

  const pending = await getPendingActions();
  notifyListeners({
    type: "sync_start",
    pendingCount: pending.length,
    message: `Đã lưu thao tác ${actionType} vào bộ nhớ ngoại tuyến.`,
  });

  return item;
}

/**
 * Enqueue an inspection task (AR or turntable 2D/3D).
 */
export async function enqueueOfflineInspection(
  targetSlug: string,
  inspectionData: {
    inspection_mode?: string;
    camera_permission_granted?: boolean;
    device_tier?: string;
    time_spent_seconds?: number;
    angles_inspected?: string[];
    hotspots_examined?: string[];
  } = {},
  idempotencyKey?: string,
): Promise<QueuedOfflineAction> {
  return enqueueOfflineAction(
    "inspection",
    "inspection",
    {
      target_slug: targetSlug,
      inspection_mode: inspectionData.inspection_mode || "turntable_3d",
      camera_permission_granted: inspectionData.camera_permission_granted || false,
      device_tier: inspectionData.device_tier || "desktop",
      time_spent_seconds: inspectionData.time_spent_seconds ?? 10,
      angles_inspected: inspectionData.angles_inspected || ["front"],
      hotspots_examined: inspectionData.hotspots_examined || [],
    },
    idempotencyKey,
  );
}

/**
 * Enqueue a learning progression action (discover, complete_lesson, submit_quiz).
 */
export async function enqueueOfflineProgression(
  action: "discover" | "complete_lesson" | "submit_quiz",
  motifId: string,
  progressionData: {
    time_spent_seconds?: number;
    answers?: Record<string, string>;
  } = {},
  idempotencyKey?: string,
): Promise<QueuedOfflineAction> {
  return enqueueOfflineAction(
    "progression",
    "progression",
    {
      action,
      motif_id: motifId,
      time_spent_seconds: progressionData.time_spent_seconds ?? 10,
      answers: progressionData.answers,
    },
    idempotencyKey,
  );
}

/**
 * Retrieve all pending queued generic actions.
 */
export async function getPendingActions(): Promise<QueuedOfflineAction[]> {
  try {
    const db = await getDB();
    return await new Promise<QueuedOfflineAction[]>((resolve, reject) => {
      const transaction = db.transaction([ACTIONS_STORE_NAME], "readonly");
      const store = transaction.objectStore(ACTIONS_STORE_NAME);
      const request = store.getAll();
      request.onsuccess = () => {
        const results = (request.result as QueuedOfflineAction[]) || [];
        resolve(results.filter((a) => a.status === "pending" || a.status === "failed"));
      };
      request.onerror = () => reject(request.error);
    });
  } catch (err) {
    return fallbackActionGet().filter((a) => a.status === "pending" || a.status === "failed");
  }
}

/**
 * Clear or remove a queued action by ID.
 */
export async function clearPendingAction(id: string): Promise<void> {
  try {
    const db = await getDB();
    await new Promise<void>((resolve, reject) => {
      const transaction = db.transaction([ACTIONS_STORE_NAME], "readwrite");
      const store = transaction.objectStore(ACTIONS_STORE_NAME);
      const request = store.delete(id);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  } catch (err) {
    console.error(`[offline-sync] Failed to clear action ${id}:`, err);
  } finally {
    fallbackActionDelete(id);
  }
}

/**
 * Clear all queued actions.
 */
export async function clearAllPendingActions(): Promise<void> {
  try {
    const db = await getDB();
    await new Promise<void>((resolve, reject) => {
      const transaction = db.transaction([ACTIONS_STORE_NAME], "readwrite");
      const store = transaction.objectStore(ACTIONS_STORE_NAME);
      const request = store.clear();
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  } catch (err) {
    console.error("[offline-sync] Failed to clear all actions:", err);
  } finally {
    if (typeof window !== "undefined" || typeof localStorage !== "undefined") {
      try {
        localStorage.removeItem(LS_ACTIONS_FALLBACK_KEY);
      } catch {}
    }
  }
}

// ============================================================================
// 3. Synchronization Engines with Idempotency & Conflict Resolution
// ============================================================================

/**
 * Synchronize the submissions offline queue with the server endpoint.
 * Dispatches sync events, enforces client idempotency keys, and handles conflicts.
 */
export async function syncOfflineQueue(
  apiEndpoint: string = "/api/v1/imperial/submissions",
): Promise<{ syncedCount: number; errorsCount: number }> {
  const isOnline =
    typeof navigator !== "undefined" && typeof navigator.onLine === "boolean"
      ? navigator.onLine
      : true;
  if (!isOnline) {
    return { syncedCount: 0, errorsCount: 0 };
  }

  const pending = await getPendingSubmissions();
  if (pending.length === 0) {
    return { syncedCount: 0, errorsCount: 0 };
  }

  notifyListeners({
    type: "sync_start",
    pendingCount: pending.length,
    message: `Đang đồng bộ ${pending.length} bài nộp ngoại tuyến...`,
  });

  let syncedCount = 0;
  let errorsCount = 0;

  for (const item of pending) {
    if (item.retry_count >= 5) {
      await updateRetryCount(item.id, "Max retries reached (5)");
      errorsCount++;
      continue;
    }

    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (item.idempotency_key) {
        headers["X-Idempotency-Key"] = item.idempotency_key;
      }

      const response = await fetch(apiEndpoint, {
        method: "POST",
        headers,
        body: JSON.stringify(item.submission),
      });

      if (response.ok || response.status === 201 || response.status === 200) {
        await clearPendingSubmission(item.id);
        syncedCount++;
      } else if (response.status === 409) {
        // Conflict resolution: server state already exists or is finalized; clear to avoid infinite loop
        await clearPendingSubmission(item.id);
        syncedCount++;
      } else {
        await updateRetryCount(item.id, `Server returned status ${response.status}`);
        errorsCount++;
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      await updateRetryCount(item.id, message);
      errorsCount++;
    }
  }

  const remaining = await getPendingSubmissions();

  if (syncedCount > 0) {
    notifyListeners({
      type: "sync_success",
      pendingCount: remaining.length,
      syncedCount,
      message: `Đã đồng bộ thành công ${syncedCount} bài làm lên máy chủ!`,
    });
  }

  if (errorsCount > 0 && remaining.length > 0) {
    notifyListeners({
      type: "sync_error",
      pendingCount: remaining.length,
      message: `Còn ${remaining.length} bài chưa thể đồng bộ do lỗi kết nối.`,
    });
  }

  return { syncedCount, errorsCount };
}

/**
 * Synchronize the generic actions offline queue (inspections, submissions, progression).
 * Posts to `/api/v1/offline/sync` with client idempotency keys, handling server ACK & conflicts.
 */
export async function syncOfflineActionQueue(
  apiEndpoint: string = "/api/v1/offline/sync",
): Promise<{ syncedCount: number; errorsCount: number; totalXpAwarded: number; results: any[] }> {
  const isOnline =
    typeof navigator !== "undefined" && typeof navigator.onLine === "boolean"
      ? navigator.onLine
      : true;
  if (!isOnline) {
    return { syncedCount: 0, errorsCount: 0, totalXpAwarded: 0, results: [] };
  }

  const pending = await getPendingActions();
  if (pending.length === 0) {
    return { syncedCount: 0, errorsCount: 0, totalXpAwarded: 0, results: [] };
  }

  notifyListeners({
    type: "sync_start",
    pendingCount: pending.length,
    message: `Đang đồng bộ ${pending.length} thao tác ngoại tuyến...`,
  });

  let syncedCount = 0;
  let errorsCount = 0;
  let totalXpAwarded = 0;
  const results: any[] = [];

  for (const item of pending) {
    if (item.retry_count >= 5) {
      await updateActionRetryCount(item.id, "Max retries reached (5)");
      errorsCount++;
      continue;
    }

    try {
      const response = await fetch(apiEndpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Idempotency-Key": item.idempotency_key,
        },
        body: JSON.stringify({
          operation_id: item.id,
          resource: item.resource,
          payload: item.payload,
          created_at: item.enqueued_at,
          idempotency_key: item.idempotency_key,
        }),
      });

      if (response.ok || response.status === 200 || response.status === 201) {
        const body = await response.json();
        const serverStatus = body.status || "synced";
        const xp = body.xp_awarded || 0;
        totalXpAwarded += xp;
        results.push(body);

        // Server confirmed processing: remove from pending queue
        await clearPendingAction(item.id);
        syncedCount++;
      } else if (response.status === 409) {
        // Conflict resolution: server state preserved, clear to avoid infinite loop
        await clearPendingAction(item.id);
        syncedCount++;
        results.push({ status: "conflict", conflict_resolution: "server_preserved" });
      } else {
        const errText = `Server error ${response.status}`;
        await updateActionRetryCount(item.id, errText);
        errorsCount++;
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      await updateActionRetryCount(item.id, message);
      errorsCount++;
    }
  }

  const remaining = await getPendingActions();

  if (syncedCount > 0) {
    notifyListeners({
      type: "sync_success",
      pendingCount: remaining.length,
      syncedCount,
      message: `Đã đồng bộ thành công ${syncedCount} thao tác lên máy chủ!`,
    });
  }

  if (errorsCount > 0 && remaining.length > 0) {
    notifyListeners({
      type: "sync_error",
      pendingCount: remaining.length,
      message: `Còn ${remaining.length} thao tác chưa thể đồng bộ do lỗi kết nối.`,
    });
  }

  return { syncedCount, errorsCount, totalXpAwarded, results };
}

// ============================================================================
// 4. Retry Logic & Storage Fallbacks
// ============================================================================

async function updateRetryCount(id: string, errorMsg: string): Promise<void> {
  try {
    const db = await getDB();
    const item = await new Promise<QueuedOfflineSubmission | undefined>((resolve, reject) => {
      const transaction = db.transaction([STORE_NAME], "readonly");
      const store = transaction.objectStore(STORE_NAME);
      const req = store.get(id);
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });

    if (item) {
      item.retry_count = (item.retry_count || 0) + 1;
      item.last_error = errorMsg;
      await new Promise<void>((resolve, reject) => {
        const transaction = db.transaction([STORE_NAME], "readwrite");
        const store = transaction.objectStore(STORE_NAME);
        const req = store.put(item);
        req.onsuccess = () => resolve();
        req.onerror = () => reject(req.error);
      });
    }
  } catch (err) {
    fallbackLocalStorageUpdateRetry(id, errorMsg);
  }
}

async function updateActionRetryCount(id: string, errorMsg: string): Promise<void> {
  try {
    const db = await getDB();
    const item = await new Promise<QueuedOfflineAction | undefined>((resolve, reject) => {
      const transaction = db.transaction([ACTIONS_STORE_NAME], "readonly");
      const store = transaction.objectStore(ACTIONS_STORE_NAME);
      const req = store.get(id);
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });

    if (item) {
      item.retry_count = (item.retry_count || 0) + 1;
      item.last_error = errorMsg;
      if (item.retry_count >= 5) {
        item.status = "failed";
      }
      await new Promise<void>((resolve, reject) => {
        const transaction = db.transaction([ACTIONS_STORE_NAME], "readwrite");
        const store = transaction.objectStore(ACTIONS_STORE_NAME);
        const req = store.put(item);
        req.onsuccess = () => resolve();
        req.onerror = () => reject(req.error);
      });
    }
  } catch (err) {
    fallbackActionUpdateRetry(id, errorMsg);
  }
}

const LS_FALLBACK_KEY = "luunien_offline_queue_fallback";
const LS_ACTIONS_FALLBACK_KEY = "luunien_offline_actions_queue_fallback";

function fallbackLocalStorageGet(): QueuedOfflineSubmission[] {
  if (typeof window === "undefined" && typeof localStorage === "undefined") return [];
  try {
    const raw = typeof localStorage !== "undefined" ? localStorage.getItem(LS_FALLBACK_KEY) : null;
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function fallbackLocalStorageEnqueue(item: QueuedOfflineSubmission) {
  if (typeof window === "undefined" && typeof localStorage === "undefined") return;
  try {
    const items = fallbackLocalStorageGet();
    items.push(item);
    localStorage.setItem(LS_FALLBACK_KEY, JSON.stringify(items));
  } catch (err) {
    console.error("[offline-sync] LocalStorage fallback enqueue failed:", err);
  }
}

function fallbackLocalStorageDelete(id: string) {
  if (typeof window === "undefined" && typeof localStorage === "undefined") return;
  try {
    const items = fallbackLocalStorageGet().filter((x) => x.id !== id);
    localStorage.setItem(LS_FALLBACK_KEY, JSON.stringify(items));
  } catch {}
}

function fallbackLocalStorageUpdateRetry(id: string, errorMsg: string) {
  if (typeof window === "undefined" && typeof localStorage === "undefined") return;
  try {
    const items = fallbackLocalStorageGet();
    const updated = items.map((x) =>
      x.id === id
        ? { ...x, retry_count: (x.retry_count || 0) + 1, last_error: errorMsg }
        : x,
    );
    localStorage.setItem(LS_FALLBACK_KEY, JSON.stringify(updated));
  } catch {}
}

function fallbackActionGet(): QueuedOfflineAction[] {
  if (typeof window === "undefined" && typeof localStorage === "undefined") return [];
  try {
    const raw = typeof localStorage !== "undefined" ? localStorage.getItem(LS_ACTIONS_FALLBACK_KEY) : null;
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function fallbackActionEnqueue(item: QueuedOfflineAction) {
  if (typeof window === "undefined" && typeof localStorage === "undefined") return;
  try {
    const items = fallbackActionGet();
    items.push(item);
    localStorage.setItem(LS_ACTIONS_FALLBACK_KEY, JSON.stringify(items));
  } catch (err) {
    console.error("[offline-sync] LocalStorage action enqueue failed:", err);
  }
}

function fallbackActionDelete(id: string) {
  if (typeof window === "undefined" && typeof localStorage === "undefined") return;
  try {
    const items = fallbackActionGet().filter((x) => x.id !== id);
    localStorage.setItem(LS_ACTIONS_FALLBACK_KEY, JSON.stringify(items));
  } catch {}
}

function fallbackActionUpdateRetry(id: string, errorMsg: string) {
  if (typeof window === "undefined" && typeof localStorage === "undefined") return;
  try {
    const items = fallbackActionGet();
    const updated = items.map((x) =>
      x.id === id
        ? {
            ...x,
            retry_count: (x.retry_count || 0) + 1,
            last_error: errorMsg,
            status: (x.retry_count || 0) + 1 >= 5 ? ("failed" as const) : x.status,
          }
        : x,
    );
    localStorage.setItem(LS_ACTIONS_FALLBACK_KEY, JSON.stringify(updated));
  } catch {}
}

/**
 * Initialize automatic background online listener.
 * Safe to call multiple times (idempotent).
 */
let isAutoListenerInitialized = false;

export function initOfflineSyncListener(apiEndpoint?: string) {
  if (typeof window === "undefined" || isAutoListenerInitialized) {
    return;
  }

  isAutoListenerInitialized = true;

  window.addEventListener("online", () => {
    Promise.all([getPendingSubmissions(), getPendingActions()]).then(([pendingSubs, pendingActs]) => {
      const totalPending = pendingSubs.length + pendingActs.length;
      notifyListeners({
        type: "online",
        pendingCount: totalPending,
        message: "Thiết bị đã kết nối lại mạng Internet. Bắt đầu tự động đồng bộ...",
      });
      // Trigger synchronization
      syncOfflineQueue(apiEndpoint);
      syncOfflineActionQueue();
    });
  });

  window.addEventListener("offline", () => {
    Promise.all([getPendingSubmissions(), getPendingActions()]).then(([pendingSubs, pendingActs]) => {
      const totalPending = pendingSubs.length + pendingActs.length;
      notifyListeners({
        type: "offline",
        pendingCount: totalPending,
        message: "Mất kết nối mạng. Ứng dụng đã chuyển sang chế độ ngoại tuyến.",
      });
    });
  });
}
