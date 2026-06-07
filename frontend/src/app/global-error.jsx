"use client";

import { useEffect } from "react";
import "./globals.css";

export default function GlobalError({ error, reset }) {
  useEffect(() => {
    console.error("Global error boundary:", error);
  }, [error]);

  return (
    <html lang="vi" className="dark">
      <body className="min-h-dvh bg-background text-foreground">
        <main className="grid min-h-screen place-items-center px-6">
          <div className="w-full max-w-md rounded-2xl border border-border bg-card p-8 text-center">
            <h1 className="text-xl font-semibold">Đã xảy ra lỗi nghiêm trọng</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Ứng dụng gặp sự cố không mong muốn. Vui lòng tải lại trang.
            </p>
            <button
              type="button"
              onClick={() => reset()}
              className="mt-6 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
            >
              Tải lại
            </button>
          </div>
        </main>
      </body>
    </html>
  );
}
