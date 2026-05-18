"use client";

import { useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, CheckCircle2, CircleAlert, Sparkles } from "lucide-react";

import { usePracticeStore } from "@/stores/practiceStore";
import { useAuthStore } from "@/stores/authStore";

export default function PracticeResultsPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const { sessionResults, endSession, loadStats } = usePracticeStore();

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }

    if (sessionResults.length === 0) {
      router.push("/practice");
      return;
    }

    loadStats();
  }, [isAuthenticated, sessionResults, router, loadStats]);

  const summary = useMemo(() => {
    const totalCards = sessionResults.length;
    const perfectCards = sessionResults.filter((r) => r.quality === 5).length;
    const goodCards = sessionResults.filter(
      (r) => r.quality >= 3 && r.quality < 5,
    ).length;
    const needReviewCards = sessionResults.filter((r) => r.quality < 3).length;
    const averageQuality =
      totalCards > 0
        ? sessionResults.reduce((sum, r) => sum + r.quality, 0) / totalCards
        : 0;

    return {
      totalCards,
      perfectCards,
      goodCards,
      needReviewCards,
      averageQuality,
    };
  }, [sessionResults]);

  const handleContinue = () => {
    endSession();
    router.push("/practice");
  };

  const handleReviewAgain = () => {
    router.push("/practice/smart");
  };

  return (
    <main className="site-shell">
      <section className="relative overflow-hidden rounded-lg border border-border/70 bg-card/70 p-6 shadow-[0_18px_50px_-22px_hsl(0_0%_0%_/_0.45)] backdrop-blur-xl md:p-8">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_90%_0%,hsl(var(--success)/0.15),transparent_45%)]" />
        <div className="relative text-center">
          <div className="mx-auto inline-flex h-14 w-14 items-center justify-center rounded-lg border border-success/35 bg-success/10">
            <Sparkles className="h-7 w-7 text-success" />
          </div>
          <h1 className="mt-4 text-3xl font-display font-bold text-foreground">Hoàn Thành Phiên Ôn Tập</h1>
          <p className="mt-2 text-sm text-muted-foreground md:text-base">
            Bạn đã ôn tập {summary.totalCards} thẻ. Tiếp tục nhịp học để giữ độ nhớ ổn định.
          </p>
        </div>
      </section>

      <section className="mt-6 grid grid-cols-2 gap-4">
        <ResultCard label="Hoàn hảo" value={summary.perfectCards} tone="success" />
        <ResultCard label="Tốt" value={summary.goodCards} tone="info" />
        <ResultCard label="Cần ôn lại" value={summary.needReviewCards} tone="warning" />
        <ResultCard label="Điểm TB" value={`${summary.averageQuality.toFixed(1)}/5`} tone="primary" />
      </section>

      <section className="mt-8 rounded-lg border border-border/70 bg-card/70 p-6 shadow-[0_12px_28px_-16px_rgba(0,0,0,0.55)] backdrop-blur-xl">
        <h2 className="text-lg font-display font-semibold text-foreground">Chi Tiết Kết Quả</h2>
        <div className="mt-4 max-h-80 space-y-2 overflow-y-auto pr-1">
          {sessionResults.map((result, index) => (
            <div
              key={index}
              className="flex items-center justify-between rounded-lg border border-border/60 bg-background/70 px-4 py-3"
            >
              <p className="text-sm font-semibold text-foreground">Thẻ {index + 1}</p>
              <QualityBadge quality={result.quality} />
            </div>
          ))}
        </div>
      </section>

      {summary.needReviewCards > 0 ? (
        <section className="mt-6 rounded-lg border border-warning/35 bg-warning/10 p-4 text-sm text-warning">
          <div className="flex items-center gap-2 font-semibold">
            <CircleAlert className="h-4 w-4" />
            Còn {summary.needReviewCards} thẻ cần ôn lại.
          </div>
        </section>
      ) : (
        <section className="mt-6 rounded-lg border border-success/35 bg-success/10 p-4 text-sm text-success">
          <div className="flex items-center gap-2 font-semibold">
            <CheckCircle2 className="h-4 w-4" />
            Phiên này rất tốt, bạn có thể chuyển sang nội dung mới.
          </div>
        </section>
      )}

      <section className="mt-6 space-y-3">
        <button
          onClick={handleContinue}
          className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-6 py-4 text-base font-semibold text-primary-foreground transition hover:bg-primary/90"
          type="button"
        >
          Về trang ôn tập
          <ArrowRight className="h-5 w-5" />
        </button>

        <button
          onClick={handleReviewAgain}
          className="w-full rounded-lg border border-border/70 bg-background/70 px-6 py-4 text-base font-semibold text-foreground transition hover:bg-muted"
          type="button"
        >
          Ôn tập tiếp
        </button>
      </section>
    </main>
  );
}

function ResultCard({ label, value, tone }) {
  const toneClasses = {
    success: "border-success/35 bg-success/10 text-success",
    info: "border-info/35 bg-info/10 text-info",
    warning: "border-warning/35 bg-warning/10 text-warning",
    primary: "border-primary/35 bg-primary/10 text-primary",
  };

  return (
    <div className={`rounded-lg border p-4 ${toneClasses[tone]}`}>
      <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{label}</p>
      <p className="mt-2 text-3xl font-display font-bold">{value}</p>
    </div>
  );
}

function QualityBadge({ quality }) {
  const badges = {
    5: { label: "Hoàn hảo", color: "border-success/35 bg-success/10 text-success" },
    4: { label: "Tốt", color: "border-info/35 bg-info/10 text-info" },
    3: { label: "Được", color: "border-warning/35 bg-warning/10 text-warning" },
    2: { label: "Khó", color: "border-accent/35 bg-accent/10 text-accent" },
    1: { label: "Rất khó", color: "border-destructive/35 bg-destructive/10 text-destructive" },
    0: { label: "Không nhớ", color: "border-border bg-muted text-muted-foreground" },
  };

  const badge = badges[quality] || badges[0];

  return <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${badge.color}`}>{badge.label}</span>;
}
