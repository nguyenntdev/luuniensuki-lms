/**
 * Offline Sync & IndexedDB Engine for STTTNNĐ (Lưu Niên — Đại Nội Huế).
 * Spec: STTT-SPEC-PWA-PRINT-001 (§2.2 Dynamic Content & Submissions)
 *
 * Stores student responses, M-E-E research claims, and field-work worksheets
 * when network connection is severed. Automatically synchronizes to server upon
 * reconnection via `window.addEventListener('online')` and notifies subscribers.
 */

import type { StudentSubmission } from "./map-types";

const DB_NAME = "luunien_imperial_offline_db";
const DB_VERSION = 1;
const STORE_NAME = "offline_submissions_queue";

export interface QueuedOfflineSubmission {
  id: string; // generated client-side id
  submission: Omit<StudentSubmission, "id" | "submitted_at" | "status">;
  enqueued_at: string;
  retry_count: number;
  last_error?: string;
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
    getPendingSubmissions()
      .then((pending) => {
        const isOnline =
          typeof navigator !== "undefined" && typeof navigator.onLine === "boolean"
            ? navigator.onLine
            : true;
        listener({
          type: isOnline ? "online" : "offline",
          pendingCount: pending.length,
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

/**
 * Enqueue a student submission into IndexedDB when offline.
 */
export async function enqueueOfflineSubmission(
  submissionData: Omit<StudentSubmission, "id" | "submitted_at" | "status">,
): Promise<QueuedOfflineSubmission> {
  const item: QueuedOfflineSubmission = {
    id: `queue-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
    submission: submissionData,
    enqueued_at: new Date().toISOString(),
    retry_count: 0,
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
        localStorage.removeItem("luunien_offline_queue_fallback");
      } catch {}
    }
  }
}

/**
 * Synchronize the offline queue with the server endpoint.
 * Dispatches sync events and removes successfully synced items.
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
    try {
      const response = await fetch(apiEndpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(item.submission),
      });

      if (response.ok || response.status === 201 || response.status === 200) {
        await clearPendingSubmission(item.id);
        syncedCount++;
      } else {
        // If server returns error, increment retry count
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
 * Increment retry count on failed attempt.
 */
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

/**
 * Fallback to localStorage if browser has indexedDB disabled or restricted.
 */
const LS_FALLBACK_KEY = "luunien_offline_queue_fallback";

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
    getPendingSubmissions().then((pending) => {
      notifyListeners({
        type: "online",
        pendingCount: pending.length,
        message: "Thiết bị đã kết nối lại mạng Internet. Bắt đầu tự động đồng bộ...",
      });
      // Trigger synchronization
      syncOfflineQueue(apiEndpoint);
    });
  });

  window.addEventListener("offline", () => {
    getPendingSubmissions().then((pending) => {
      notifyListeners({
        type: "offline",
        pendingCount: pending.length,
        message: "Mất kết nối mạng. Ứng dụng đã chuyển sang chế độ ngoại tuyến.",
      });
    });
  });
}
