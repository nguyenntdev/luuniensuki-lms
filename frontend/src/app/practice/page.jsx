"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  Brain,
  Flame,
  Sparkles,
  Target,
  BookOpen,
} from "lucide-react";

import { usePracticeStore } from "@/stores/practiceStore";
import { useAuthStore } from "@/stores/authStore";

export default function PracticePage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const { stats, loadStats, loadDueCards, error } = usePracticeStore();
  const [isLoadingData, setIsLoadingData] = useState(true);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }

    async function loadData() {
      try {
        await Promise.all([loadStats(), loadDueCards()]);
      } catch (err) {
        console.error("Failed to load practice data:", err);
      } finally {
        setIsLoadingData(false);
      }
    }

    loadData();
  }, [isAuthenticated, router, loadStats, loadDueCards]);

  const masteryRate = useMemo(() => {
    if (!stats?.total_cards) return 0;
    return Math.round((stats.mastered_cards / stats.total_cards) * 100);
  }, [stats]);

  if (isLoadingData) {
    return (
      <main className="site-shell flex items-center justify-center">
        <div className="heritage-surface p-8 text-center">
          <div className="relative">
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-b-2 border-primary" />
          <p className="mt-4 text-sm text-muted-foreground">Đang tải dữ liệu ôn tập...</p>
          </div>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="site-shell">
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-6 text-destructive">
          <p className="text-sm font-semibold uppercase tracking-wider">Lỗi</p>
          <p className="mt-2 text-sm">{error}</p>
        </div>
      </main>
    );
  }

  const modeCards = [
    {
      title: "Ôn ngay",
      description: "Làm các thẻ đang đến hạn. Phù hợp nhất để bắt đầu.",
      href: "/practice/smart",
      icon: Brain,
      tone: "primary",
      badge: stats?.due_cards || 0,
    },
    {
      title: "Xem lại bộ sưu tập",
      description: "Mở các họa tiết đã học để đọc lại trước khi làm bài.",
      href: "/collection",
      icon: BookOpen,
      tone: "info",
    },
    {
      title: "Xem kết quả",
      description: "Nhìn lại phần đúng sai để biết mình cần cải thiện gì.",
      href: "/practice/results?focus=weak",
      icon: Target,
      tone: "warning",
    },
  ];

  return (
    <main className="site-shell">
      <section className="heritage-hero md:p-6">
        <div className="relative grid gap-5 lg:grid-cols-[1fr_320px] lg:items-end">
          <div>
            <div className="heritage-chip">
              Trung tâm ôn tập
            </div>
            <h1 className="mt-3 text-3xl font-display font-bold text-foreground">Ôn tập chủ động</h1>
            <p className="mt-2 max-w-2xl text-sm text-muted-foreground md:text-base">
              Ôn những gì đang cần nhất. Ít lựa chọn hơn, bắt đầu nhanh hơn.
            </p>
          </div>
          <button
            type="button"
            onClick={() => router.push("/practice/smart")}
            className="focus-card p-4 text-left transition hover:border-primary/35"
          >
            <div className="text-xs font-semibold uppercase tracking-wider text-primary">
              Nên ôn ngay
            </div>
            <div className="mt-2 flex items-end justify-between gap-3">
              <div>
                <div className="text-2xl font-display font-bold text-foreground">
                  {stats?.due_cards || 0} thẻ
                </div>
                <div className="mt-1 text-xs text-muted-foreground">
                  Đang đến hạn ôn
                </div>
              </div>
              <ArrowRight className="h-5 w-5 text-primary" />
            </div>
          </button>
        </div>
      </section>

      <section className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Cần ôn ngay" count={stats?.due_cards || 0} tone="warning" icon={Flame} />
        <StatCard label="Đang học" count={stats?.learning_cards || 0} tone="info" icon={Brain} />
        <StatCard label="Đã thành thạo" count={stats?.mastered_cards || 0} tone="success" icon={Sparkles} />
        <StatCard label="Tỷ lệ thành thạo" count={`${masteryRate}%`} tone="primary" icon={Target} />
      </section>

      <section className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-3">
        {modeCards.map((mode) => (
          <PracticeModeCard key={mode.title} {...mode} onClick={() => router.push(mode.href)} />
        ))}
      </section>

      {stats ? (
        <section className="heritage-surface mt-5 p-5">
          <div className="relative">
          <h2 className="text-lg font-display font-semibold text-foreground">Tổng quan phiên ôn</h2>
          <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
            <MetricItem label="Tổng thẻ" value={stats.total_cards} />
            <MetricItem label="Ôn hôm nay" value={stats.reviewed_today} />
            <MetricItem label="Tổng lần ôn" value={stats.total_reviews} />
            <MetricItem label="Đã thành thạo" value={stats.mastered_cards} />
          </div>
          </div>
        </section>
      ) : null}
    </main>
  );
}

function StatCard({ label, count, tone, icon: Icon }) {
  const toneClasses = {
    warning: "border-warning/40 bg-warning/10 text-warning",
    info: "border-info/40 bg-info/10 text-info",
    success: "border-success/40 bg-success/10 text-success",
    primary: "border-primary/40 bg-primary/10 text-primary",
  };

  return (
    <div className={`focus-card p-4 ${toneClasses[tone]}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{label}</p>
          <p className="mt-2 text-3xl font-display font-bold">{count}</p>
        </div>
        <Icon className="h-8 w-8" />
      </div>
    </div>
  );
}

function PracticeModeCard({ title, description, icon: Icon, tone, badge, onClick }) {
  const toneClasses = {
    primary: "border-primary/35 bg-primary/10",
    info: "border-info/35 bg-info/10",
    warning: "border-warning/35 bg-warning/10",
    success: "border-success/35 bg-success/10",
  };

  return (
    <button
      onClick={onClick}
      className={`group focus-card min-h-[210px] p-5 text-left transition duration-300 hover:-translate-y-0.5 hover:border-primary/40 ${toneClasses[tone]}`}
      type="button"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-border/60 bg-background/70">
            <Icon className="h-5 w-5 text-foreground" />
          </div>
          <h3 className="mt-3 text-lg font-display font-semibold text-foreground">{title}</h3>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{description}</p>
        </div>
        {badge ? (
          <span className="rounded-md border border-destructive/40 bg-destructive/10 px-2.5 py-1 text-xs font-bold text-destructive">
            {badge}
          </span>
        ) : null}
      </div>
      <div className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-primary">
        Bắt đầu phiên
        <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
      </div>
    </button>
  );
}

function MetricItem({ label, value }) {
  return (
    <div className="metric-pill p-4">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-display font-semibold text-foreground">{value}</p>
    </div>
  );
}
