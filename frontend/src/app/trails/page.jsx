import ErrorBoundary from "@/components/ErrorBoundary";
import TrailsClient from "@/components/trails/TrailsClient";

export const metadata = {
  title: "Lộ trình di sản — Lưu Niên Sử Kí",
  description:
    "Khám phá các lộ trình di sản được biên soạn — chuỗi 5 đến 15 hoạ tiết theo chủ đề.",
};

export const dynamic = "force-dynamic";

export default function TrailsPage() {
  return (
    <main
      className="min-h-screen bg-background text-foreground"
      aria-labelledby="trails-heading"
    >
      <header className="border-b border-border bg-card/50 px-6 py-8">
        <h1 id="trails-heading" className="text-3xl font-bold tracking-tight">
          Lộ trình di sản
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          Mỗi lộ trình là một chuỗi 5 đến 15 hoạ tiết kết nối với nhau theo
          một chủ đề. Đọc lời dẫn, hoàn thành từng bước, dừng lại ở các điểm
          suy ngẫm và nhận chứng chỉ khi hoàn tất.
        </p>
      </header>
      <ErrorBoundary>
        <TrailsClient />
      </ErrorBoundary>
    </main>
  );
}
