"use client";

import React, { useEffect, useState } from "react";
import {
  initOfflineSyncListener,
  subscribeOfflineSync,
  syncOfflineQueue,
} from "@/lib/imperial/offline-sync";
import {
  AlertCircle,
  CheckCircle2,
  CloudOff,
  RefreshCw,
  Wifi,
  WifiOff,
  X,
} from "lucide-react";

export function ServiceWorkerRegister() {
  const [isOffline, setIsOffline] = useState(false);
  const [notification, setNotification] = useState<{
    type: "info" | "success" | "warning";
    message: string;
  } | null>(null);
  const [pendingCount, setPendingCount] = useState(0);
  const [isSyncing, setIsSyncing] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;

    // 1. Initial connectivity check
    setIsOffline(!navigator.onLine);

    // 2. Initialize Service Worker
    if ("serviceWorker" in navigator) {
      window.addEventListener("load", () => {
        navigator.serviceWorker
          .register("/sw-imperial.js", { scope: "/dai-noi" })
          .then((registration) => {
            // Check for updates
            registration.addEventListener("updatefound", () => {
              const installingWorker = registration.installing;
              if (installingWorker) {
                installingWorker.addEventListener("statechange", () => {
                  if (
                    installingWorker.state === "installed" &&
                    navigator.serviceWorker.controller
                  ) {
                    setNotification({
                      type: "info",
                      message: "Đã có bản cập nhật di sản mới. Tải lại trang để áp dụng.",
                    });
                  }
                });
              }
            });
          })
          .catch((err) => {
            console.warn("[sw-register] Service worker registration error:", err);
          });
      });
    }

    // 3. Initialize offline sync listeners
    initOfflineSyncListener();

    const unsubscribe = subscribeOfflineSync((event) => {
      setPendingCount(event.pendingCount);

      if (event.type === "offline") {
        setIsOffline(true);
        setNotification({
          type: "warning",
          message:
            event.message ||
            "Mất mạng Internet. Bạn đang ở chế độ ngoại tuyến thực địa.",
        });
      } else if (event.type === "online") {
        setIsOffline(false);
        setNotification({
          type: "info",
          message:
            event.message ||
            "Đã có mạng trở lại. Hệ thống đang tự động đồng bộ bài làm...",
        });
      } else if (event.type === "sync_start") {
        setIsSyncing(true);
      } else if (event.type === "sync_success") {
        setIsSyncing(false);
        setNotification({
          type: "success",
          message:
            event.message ||
            `Đã đồng bộ ${event.syncedCount || ""} bài nộp thành công!`,
        });
        // Auto dismiss success notice after 5 seconds
        setTimeout(() => {
          setNotification((curr) => (curr?.type === "success" ? null : curr));
        }, 5000);
      } else if (event.type === "sync_error") {
        setIsSyncing(false);
        setNotification({
          type: "warning",
          message: event.message || "Lỗi đồng bộ một số bài làm. Sẽ thử lại sau.",
        });
      }
    });

    return () => {
      unsubscribe();
    };
  }, []);

  const handleManualSync = async () => {
    setIsSyncing(true);
    try {
      await syncOfflineQueue();
    } finally {
      setIsSyncing(false);
    }
  };

  // If no notification and connected online with no pending queue, render nothing
  if (!notification && !isOffline && pendingCount === 0) {
    return null;
  }

  return (
    <aside
      aria-label="Thông báo trạng thái kết nối mạng và đồng bộ dữ liệu"
      className="fixed bottom-18 left-4 right-4 z-50 mx-auto max-w-md pointer-events-auto md:bottom-6 md:right-6 md:left-auto"
    >
      <div
        className={`flex items-start gap-3 rounded-2xl border p-4 shadow-xl backdrop-blur-md transition-all duration-300 ${
          isOffline || notification?.type === "warning"
            ? "border-amber-500/50 bg-[#2a231d]/95 text-[#f7f2e8]"
            : notification?.type === "success"
            ? "border-emerald-500/50 bg-[#17271c]/95 text-[#e8f7ec]"
            : "border-primary/50 bg-card/95 text-foreground"
        }`}
      >
        <div className="mt-0.5 shrink-0">
          {isOffline ? (
            <WifiOff className="h-5 w-5 text-amber-400 animate-pulse" />
          ) : isSyncing ? (
            <RefreshCw className="h-5 w-5 text-primary animate-spin" />
          ) : notification?.type === "success" ? (
            <CheckCircle2 className="h-5 w-5 text-emerald-400" />
          ) : (
            <Wifi className="h-5 w-5 text-primary" />
          )}
        </div>

        <div className="flex-1 text-xs leading-relaxed space-y-1">
          <div className="font-bold flex items-center justify-between">
            <span>
              {isOffline
                ? "Chế độ Ngoại Tuyến (Offline)"
                : isSyncing
                ? "Đang đồng bộ..."
                : "Thông báo kết nối"}
            </span>
            {pendingCount > 0 && (
              <span className="rounded-full bg-amber-500/20 px-2 py-0.5 text-[10px] font-semibold text-amber-300 border border-amber-500/30">
                {pendingCount} bài chờ đồng bộ
              </span>
            )}
          </div>

          <p className="opacity-90">
            {notification?.message ||
              (isOffline
                ? "Các chuyên khảo di tích và phiếu làm bài vẫn hoạt động. Dữ liệu sẽ lưu trên máy và tự đồng bộ khi có mạng."
                : "Đã sẵn sàng hoạt động.")}
          </p>

          {!isOffline && pendingCount > 0 && (
            <button
              onClick={handleManualSync}
              disabled={isSyncing}
              className="mt-2 inline-flex items-center gap-1.5 rounded-lg bg-primary/20 hover:bg-primary/30 px-2.5 py-1 text-[11px] font-semibold text-primary transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`h-3 w-3 ${isSyncing ? "animate-spin" : ""}`} />
              <span>Đồng bộ ngay ({pendingCount})</span>
            </button>
          )}
        </div>

        {notification && (
          <button
            onClick={() => setNotification(null)}
            className="shrink-0 p-1 opacity-70 hover:opacity-100 transition-opacity"
            aria-label="Đóng thông báo"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    </aside>
  );
}

export default ServiceWorkerRegister;
