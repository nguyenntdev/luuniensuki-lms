import Link from "next/link";
import { Compass, Home } from "lucide-react";

export const metadata = {
  title: "Không tìm thấy trang — Lưu Niên Sử Kí",
};

export default function NotFound() {
  return (
    <main className="grid min-h-[70vh] place-items-center px-6">
      <div className="heritage-surface w-full max-w-md p-8 text-center">
        <div className="relative">
          <div className="font-display text-6xl font-bold text-gradient-gold">404</div>
          <h1 className="mt-3 font-display text-xl font-semibold text-foreground">
            Không tìm thấy trang
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Trang bạn tìm có thể đã được di dời hoặc không tồn tại. Hãy quay về
            và tiếp tục hành trình khám phá Cửu Đỉnh.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
            >
              <Home className="h-4 w-4" /> Về bảng học tập
            </Link>
            <Link
              href="/explore"
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-secondary/60 px-4 py-2.5 text-sm font-semibold text-foreground transition hover:bg-secondary"
            >
              <Compass className="h-4 w-4" /> Khám phá
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
