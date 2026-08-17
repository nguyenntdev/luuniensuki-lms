import ErrorBoundary from "@/components/ErrorBoundary";
import TimelineClient from "@/components/timeline/TimelineClient";

export const metadata = {
  title: "Dòng thời gian di sản — Lưu Niên Sử Kí",
  description:
    "Khám phá lịch sử Cửu Đỉnh và triều Nguyễn theo dòng thời gian từ 1802 đến 1945.",
};

export const dynamic = "force-dynamic";

export default async function TimelinePage({ searchParams }) {
  const sp = await searchParams;
  const entity = sp?.entity ? String(sp.entity).trim() : null;
  return (
    <main
      className="min-h-screen bg-background text-foreground"
      aria-labelledby="timeline-heading"
    >
      <a
        href="#timeline-events"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:rounded-md focus:bg-primary focus:px-3 focus:py-2 focus:text-primary-foreground focus:shadow-lg"
      >
        Bỏ qua đến nội dung
      </a>
      <header className="border-b border-border bg-card/50 px-6 py-8">
        <h1
          id="timeline-heading"
          className="text-3xl font-bold tracking-tight"
        >
          Dòng thời gian di sản
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          Bộ sưu tập các sự kiện quan trọng từ năm 1802 đến 1945 xoay quanh
          Cửu Đỉnh và triều Nguyễn. Dùng phím mũi tên để di chuyển giữa các
          sự kiện và Enter để mở chi tiết.
        </p>
      </header>
      <ErrorBoundary>
        <TimelineClient entity={entity} />
      </ErrorBoundary>
    </main>
  );
}
