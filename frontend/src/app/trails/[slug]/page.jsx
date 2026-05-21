import ErrorBoundary from "@/components/ErrorBoundary";
import TrailPlayer from "@/components/trails/TrailPlayer";

export const metadata = {
  title: "Lộ trình — Lưu Niên Sử Kí",
};

export const dynamic = "force-dynamic";

export default function TrailDetailPage({ params }) {
  return (
    <main
      className="min-h-screen bg-background text-foreground"
      aria-labelledby="trail-heading"
    >
      <ErrorBoundary>
        <TrailPlayer slug={params.slug} />
      </ErrorBoundary>
    </main>
  );
}
