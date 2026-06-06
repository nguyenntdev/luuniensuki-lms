import ErrorBoundary from "@/components/ErrorBoundary";
import VirtualTours from "@/components/vr360/VirtualTours";
import SelfHostedTour from "@/components/vr360/SelfHostedTour";

export const metadata = {
  title: "Tham quan ảo 360° — Lưu Niên Sử Kí",
  description:
    "Tham quan ảo 360° Hoàng thành Huế và cố đô Huế — nơi gắn liền với Cửu Đỉnh triều Nguyễn.",
};

export const dynamic = "force-dynamic";

export default function Vr360Page() {
  return (
    <main className="min-h-screen bg-background text-foreground" aria-labelledby="vr360-heading">
      <header className="border-b border-border bg-card/50 px-6 py-8">
        <h1 id="vr360-heading" className="text-3xl font-bold tracking-tight">
          Tham quan ảo 360°
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          Bước vào Hoàng thành Huế và cố đô bằng ảnh toàn cảnh 360° để cảm nhận không gian
          thật nơi đặt Cửu Đỉnh, rồi quay lại khám phá mô hình 3D và từng họa tiết.
        </p>
      </header>
      <ErrorBoundary>
        <VirtualTours />
      </ErrorBoundary>

      <section className="px-6 pb-10">
        <h2 className="mb-1 text-xl font-semibold text-foreground">Bản dựng 360° nội bộ</h2>
        <p className="mb-4 max-w-2xl text-sm text-muted-foreground">
          Trình xem 360° tự lưu trữ của Lưu Niên Sử Kí — không phụ thuộc bên thứ ba.
          Kéo để nhìn quanh, cuộn để phóng to.
        </p>
        <ErrorBoundary>
          <SelfHostedTour />
        </ErrorBoundary>
      </section>
    </main>
  );
}
