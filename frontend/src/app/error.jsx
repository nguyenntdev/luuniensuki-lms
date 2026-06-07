"use client";

import { useEffect } from "react";
import Link from "next/link";
import { RotateCw, Home } from "lucide-react";

export default function Error({ error, reset }) {
  useEffect(() => {
    // Surface to the console for debugging; analytics hook could go here.
    console.error("App error boundary:", error);
  }, [error]);

  return (
    <main className="grid min-h-[70vh] place-items-center px-6">
      <div className="heritage-surface w-full max-w-md p-8 text-center">
        <div className="relative">
          <h1 className="font-display text-xl font-semibold text-foreground">
            Đã xảy ra lỗi
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Rất tiếc, có sự cố khi tải nội dung này. Bạn có thể thử lại hoặc quay
            về bảng học tập.
          </p>
          {error?.digest ? (
            <p className="mt-2 text-[11px] text-muted-foreground/70">
              Mã lỗi: <span className="font-mono">{error.digest}</span>
            </p>
          ) : null}
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <button
              type="button"
              onClick={() => reset()}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
            >
              <RotateCw className="h-4 w-4" /> Thử lại
            </button>
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-secondary/60 px-4 py-2.5 text-sm font-semibold text-foreground transition hover:bg-secondary"
            >
              <Home className="h-4 w-4" /> Về bảng học tập
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
