"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  ArrowRight,
  BookOpen,
  Brain,
  Compass,
  Eye,
  Flame,
  Globe,
  Medal,
  Sparkles,
  Star,
  Trophy,
} from "lucide-react";

import { useAuthStore } from "@/stores/authStore";
import { getDashboardSummary } from "@/lib/api";
import Skeleton from "@/components/Skeleton";

function PrimaryLink({ href, children }) {
  return (
    <Link
      href={href}
      className="inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
    >
      {children}
    </Link>
  );
}

function SecondaryLink({ href, icon: Icon, children }) {
  return (
    <Link
      href={href}
      className="inline-flex items-center justify-center gap-2 rounded-lg border border-border bg-secondary/60 px-4 py-2.5 text-sm font-semibold text-foreground transition hover:border-primary/40 hover:bg-secondary"
    >
      <Icon className="h-4 w-4 text-primary" />
      {children}
    </Link>
  );
}

function GuestLanding() {
  return (
    <main className="site-shell">
      <section className="grid gap-5 lg:grid-cols-[1.25fr_0.75fr]">
        <div className="heritage-hero p-6 md:p-8">
          <div className="relative">
            <div className="heritage-chip">
              <Sparkles className="h-4 w-4" />
              Nền tảng học tập tương tác
            </div>
            <h1 className="mt-5 max-w-3xl font-display text-4xl font-bold tracking-tight text-foreground md:text-6xl">
              Lưu Niên Sử Kí
            </h1>
            <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground md:text-lg">
              Học về Cửu Đỉnh qua mô hình 3D, lộ trình ngắn, ôn tập thông minh,
              và bộ sưu tập họa tiết theo tiến độ cá nhân.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <PrimaryLink href="/login">
                Bắt đầu
                <ArrowRight className="h-4 w-4" />
              </PrimaryLink>
              <SecondaryLink href="/explore" icon={Eye}>
                Xem Cửu Đỉnh
              </SecondaryLink>
              <SecondaryLink href="/cuu-dinh" icon={BookOpen}>
                Tìm hiểu nhanh
              </SecondaryLink>
            </div>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
          <FeatureCard icon={Compass} title="Khám phá 3D" text="Chọn đỉnh, mở họa tiết, học trong ngữ cảnh." />
          <FeatureCard icon={Brain} title="Ôn đúng lúc" text="Ưu tiên nội dung cần nhớ lại trước." />
          <FeatureCard icon={Trophy} title="Tiến độ rõ" text="XP, streak, huy hiệu, bộ sưu tập trong một luồng." />
        </div>
      </section>

      <section className="mt-5 grid gap-4 lg:grid-cols-[0.8fr_1.2fr]">
        <div className="heritage-surface p-5">
          <div className="relative">
            <h2 className="font-display text-xl font-semibold text-foreground">
              Một màn hình, ít nhiễu
            </h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Bắt đầu bằng đỉnh đang học, chuyển nhanh sang ôn tập, mở bộ sưu tập
              khi cần tra cứu.
            </p>
          </div>
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          <MiniStep number="01" label="Chọn đỉnh" />
          <MiniStep number="02" label="Học họa tiết" />
          <MiniStep number="03" label="Ôn và thành thạo" />
        </div>
      </section>
    </main>
  );
}

function FeatureCard({ icon: Icon, title, text }) {
  return (
    <div className="heritage-card p-5">
      <div className="relative">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/12 text-primary">
            <Icon className="h-5 w-5" />
          </span>
          <h3 className="font-display text-lg font-semibold text-foreground">{title}</h3>
        </div>
        <p className="mt-3 text-sm leading-6 text-muted-foreground">{text}</p>
      </div>
    </div>
  );
}

function MiniStep({ number, label }) {
  return (
    <div className="heritage-card p-4">
      <div className="relative">
        <div className="text-xs font-bold text-primary">{number}</div>
        <div className="mt-1 font-display text-lg font-semibold text-foreground">{label}</div>
      </div>
    </div>
  );
}

function AuthenticatedDashboard() {
  const user = useAuthStore((s) => s.user);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      try {
        const summary = await getDashboardSummary();
        if (!cancelled) setData(summary);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const displayName = user?.display_name || user?.email?.split("@")[0] || "Nhà khám phá";
  const streak = data?.streak || { current_streak: 0 };
  const stats = data?.collection_stats || { total: 0, discovered: 0, learned: 0, mastered: 0 };
  const urns = data?.urns || [];
  const startingUrn = urns.find((u) => u.id === user?.starting_urn_id) || urns[0];
  const doneSteps = stats.discovered + stats.learned + stats.mastered;
  const totalSteps = stats.total * 3;
  const progressPercent = totalSteps > 0 ? Math.round((doneSteps / totalSteps) * 100) : 0;

  return (
    <main className="site-shell">
      <section className="grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="heritage-hero p-6 md:p-7">
          <div className="relative">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="heritage-chip">Bảng học tập</div>
                <h1 className="mt-4 font-display text-3xl font-bold text-foreground md:text-4xl">
                  Xin chào, {displayName}
                </h1>
                <p className="mt-2 text-sm text-muted-foreground">
                  Tiếp tục đúng chỗ, xem tiến độ, rồi chuyển sang ôn tập khi cần.
                </p>
              </div>
              <PrimaryLink href={startingUrn ? `/urns/${startingUrn.slug}` : "/explore"}>
                Tiếp tục
                <ArrowRight className="h-4 w-4" />
              </PrimaryLink>
            </div>

            <div className="mt-6">
              {loading ? (
                <Skeleton className="h-16 w-full" />
              ) : (
                <>
                  <div className="flex items-center justify-between gap-4 text-sm">
                    <div>
                      <div className="font-display text-xl font-semibold text-foreground">
                        {startingUrn?.name || "Chọn một đỉnh để bắt đầu"}
                      </div>
                      <div className="mt-1 text-muted-foreground">
                        {doneSteps}/{totalSteps || 0} bước hoàn thành
                      </div>
                    </div>
                    <div className="font-display text-3xl font-bold text-primary">{progressPercent}%</div>
                  </div>
                  <div className="mt-4 h-2 overflow-hidden rounded-full bg-muted">
                    <div className="h-full rounded-full bg-primary" style={{ width: `${progressPercent}%` }} />
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <StatCard icon={Flame} value={streak.current_streak} label="Chuỗi ngày" loading={loading} />
          <StatCard icon={Star} value={user?.total_xp || 0} label="Tổng XP" loading={loading} />
          <StatCard icon={Medal} value={stats.mastered} label="Thành thạo" loading={loading} />
        </div>
      </section>

      {error ? (
        <div className="mt-5 rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      ) : null}

      <section className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <QuickLink href="/explore" icon={Compass} title="Khám phá" text="Mở đỉnh và họa tiết" />
        <QuickLink href="/vr360" icon={Globe} title="Tham quan ảo 360°" text="Đi dạo Hoàng thành Huế" />
        <QuickLink href="/practice" icon={Brain} title="Ôn tập" text="Phiên ngắn theo trí nhớ" />
        <QuickLink href="/collection" icon={BookOpen} title="Bộ sưu tập" text={`${doneSteps} họa tiết đã mở`} />
        <QuickLink href="/achievements" icon={Trophy} title="Thành tích" text="Huy hiệu và bảng hạng" />
      </section>
    </main>
  );
}

function StatCard({ icon: Icon, value, label, loading }) {
  return (
    <div className="heritage-card p-4">
      <div className="relative">
        <Icon className="h-5 w-5 text-primary" />
        {loading ? (
          <Skeleton className="mt-3 h-8 w-14" />
        ) : (
          <div className="mt-3 font-display text-2xl font-bold text-foreground">{value}</div>
        )}
        <div className="mt-1 text-xs text-muted-foreground">{label}</div>
      </div>
    </div>
  );
}

function QuickLink({ href, icon: Icon, title, text }) {
  return (
    <Link href={href} className="heritage-card group p-4 transition hover:border-primary/35">
      <div className="relative flex items-center gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/12 text-primary">
          <Icon className="h-5 w-5" />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block font-semibold text-foreground">{title}</span>
          <span className="block truncate text-sm text-muted-foreground">{text}</span>
        </span>
        <ArrowRight className="h-4 w-4 text-muted-foreground transition group-hover:translate-x-0.5 group-hover:text-primary" />
      </div>
    </Link>
  );
}

export default function HomePage() {
  const status = useAuthStore((s) => s.status);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <div className="text-muted-foreground">Đang tải...</div>
      </main>
    );
  }

  if (status === "authed") return <AuthenticatedDashboard />;
  return <GuestLanding />;
}
