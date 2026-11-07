"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  RefreshCcw,
  ShieldCheck,
  TrendingUp,
  Users,
  BookOpen,
  MessageSquare,
  CalendarCheck,
  Award,
  Filter,
  BarChart3,
  Layers,
  Sparkles,
} from "lucide-react";

import { useAuthStore } from "@/stores/authStore";
import {
  getTruthFunnelDashboard,
  TruthFunnelDashboardData,
} from "@/lib/api";

type TruthTab = "observed" | "hypothesis" | "forecast" | "audit";

export function FunnelDashboardClient({
  initialData,
}: {
  initialData?: TruthFunnelDashboardData;
} = {}) {
  const status = useAuthStore((s) => s.status);
  const user = useAuthStore((s) => s.user);
  const isStaff = ["teacher", "admin", "super_admin"].includes(user?.role || "");

  const [activeTab, setActiveTab] = useState<TruthTab>("observed");
  const [data, setData] = useState<TruthFunnelDashboardData | null>(initialData || null);
  const [loading, setLoading] = useState<boolean>(!initialData);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [channelFilter, setChannelFilter] = useState<string>("");
  const [cohortFilter, setCohortFilter] = useState<string>("");

  const loadData = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getTruthFunnelDashboard({
        channel: channelFilter || undefined,
        cohort: cohortFilter || undefined,
      });
      setData(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể tải dữ liệu phễu chuyển đổi.");
    } finally {
      setLoading(false);
    }
  }, [channelFilter, cohortFilter]);

  useEffect(() => {
    if (status === "authed" && isStaff) {
      loadData();
    }
  }, [status, isStaff, loadData]);

  if (status !== "authed") {
    return (
      <main className="site-shell py-8">
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <h1 className="text-xl font-display font-semibold text-foreground">
            Truth-Level Funnel Dashboard
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Vui lòng đăng nhập với tài khoản Quản trị viên để truy cập bảng điều khiển.
          </p>
        </div>
      </main>
    );
  }

  if (!isStaff) {
    return (
      <main className="site-shell py-8">
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <h1 className="text-xl font-display font-semibold text-foreground">
            Truth-Level Funnel Dashboard
          </h1>
          <p className="mt-2 text-sm text-destructive">
            Bạn không có quyền truy cập bảng điều khiển này (Yêu cầu vai trò Staff / Admin).
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="site-shell py-8 space-y-6">
      {/* Header and Back Link */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground mb-1">
            <Link href="/admin" className="hover:text-foreground inline-flex items-center gap-1">
              <ArrowLeft className="h-3 w-3" /> Admin Studio
            </Link>
            <span>/</span>
            <span>Analytics</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-display font-bold text-foreground">
            Truth-Level Conversion Funnel
          </h1>
          <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
            Phân tách ba tầng dữ liệu: <strong>OBSERVED</strong> (Thực tế ghi nhận),{" "}
            <strong>HYPOTHESIS</strong> (Giả định mô hình), và <strong>FORECAST</strong> (Mục tiêu dự phóng).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={loadData}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm font-semibold text-foreground hover:bg-muted disabled:opacity-50"
          >
            <RefreshCcw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Làm mới
          </button>
        </div>
      </div>

      {/* Anti-Abuse Integrity Banner */}
      <div
        data-testid="anti-abuse-status"
        className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-sm"
      >
        <div className="flex items-center gap-3">
          <ShieldCheck className="h-5 w-5 text-emerald-600 shrink-0" />
          <div>
            <span className="font-semibold text-emerald-800 dark:text-emerald-400">
              Kiểm định phân tầng sự thật (Anti-Abuse Invariant):
            </span>{" "}
            <span className="text-emerald-700 dark:text-emerald-300">
              Mục tiêu dự phóng 1,100 lượt không bao giờ được tính vào số lượt hoàn thành thực tế.
            </span>
          </div>
        </div>
        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/20 px-2.5 py-0.5 text-xs font-medium text-emerald-700 dark:text-emerald-300">
          <CheckCircle2 className="h-3.5 w-3.5" /> BẢO VỆ TUYỆT ĐỐI
        </span>
      </div>

      {/* Filter Toolbar */}
      <div className="rounded-xl border border-border bg-card p-4 flex flex-wrap items-center gap-4 text-sm">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Filter className="h-4 w-4" />
          <span className="font-medium">Bộ lọc:</span>
        </div>
        <div className="flex items-center gap-2">
          <label htmlFor="channel-select" className="text-xs text-muted-foreground">Kênh:</label>
          <select
            id="channel-select"
            value={channelFilter}
            onChange={(e) => setChannelFilter(e.target.value)}
            className="rounded-lg border border-border bg-background px-3 py-1.5 text-sm text-foreground focus:ring-1 focus:ring-primary"
          >
            <option value="">Tất cả kênh</option>
            <option value="email">Email</option>
            <option value="phone">Điện thoại</option>
            <option value="zalo">Zalo</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label htmlFor="cohort-input" className="text-xs text-muted-foreground">Cohort:</label>
          <input
            id="cohort-input"
            type="text"
            placeholder="e.g. 2026-W44"
            value={cohortFilter}
            onChange={(e) => setCohortFilter(e.target.value)}
            className="rounded-lg border border-border bg-background px-3 py-1.5 text-sm text-foreground focus:ring-1 focus:ring-primary w-36"
          />
        </div>
      </div>

      {/* Tier Switcher Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-border pb-2">
        <button
          type="button"
          onClick={() => setActiveTab("observed")}
          className={`px-4 py-2 text-sm font-semibold rounded-lg transition-colors inline-flex items-center gap-2 ${
            activeTab === "observed"
              ? "bg-primary text-primary-foreground shadow-sm"
              : "text-muted-foreground hover:bg-muted hover:text-foreground"
          }`}
        >
          <Layers className="h-4 w-4" />
          1. OBSERVED (Thực tế ghi nhận)
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("hypothesis")}
          className={`px-4 py-2 text-sm font-semibold rounded-lg transition-colors inline-flex items-center gap-2 ${
            activeTab === "hypothesis"
              ? "bg-primary text-primary-foreground shadow-sm"
              : "text-muted-foreground hover:bg-muted hover:text-foreground"
          }`}
        >
          <BarChart3 className="h-4 w-4" />
          2. HYPOTHESIS (Giả thuyết mô hình)
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("forecast")}
          className={`px-4 py-2 text-sm font-semibold rounded-lg transition-colors inline-flex items-center gap-2 ${
            activeTab === "forecast"
              ? "bg-primary text-primary-foreground shadow-sm"
              : "text-muted-foreground hover:bg-muted hover:text-foreground"
          }`}
        >
          <Sparkles className="h-4 w-4" />
          3. FORECAST (Mục tiêu dự phóng)
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("audit")}
          className={`px-4 py-2 text-sm font-semibold rounded-lg transition-colors inline-flex items-center gap-2 ${
            activeTab === "audit"
              ? "bg-primary text-primary-foreground shadow-sm"
              : "text-muted-foreground hover:bg-muted hover:text-foreground"
          }`}
        >
          <ShieldCheck className="h-4 w-4" />
          4. TRUTH AUDIT (Đối soát phân tầng)
        </button>
      </div>

      {loading && !data ? (
        <div className="p-12 text-center text-muted-foreground space-y-3">
          <RefreshCcw className="h-6 w-6 animate-spin mx-auto text-primary" />
          <p>Đang tải dữ liệu phễu chuyển đổi phân tầng...</p>
        </div>
      ) : error ? (
        <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-6 text-destructive text-sm flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold">Lỗi tải dữ liệu</div>
            <div className="mt-1">{error}</div>
            <button
              type="button"
              onClick={loadData}
              className="mt-3 rounded-lg bg-destructive px-3 py-1.5 text-xs font-semibold text-destructive-foreground hover:bg-destructive/90"
            >
              Thử lại
            </button>
          </div>
        </div>
      ) : !data ? null : (
        <>
          {/* TAB 1: OBSERVED ACTUALS */}
          {activeTab === "observed" && (
            <div className="space-y-6">
              {/* Summary KPIs */}
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-6">
                <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
                  <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                    <Users className="h-3.5 w-3.5" />
                    <span>Visitors</span>
                  </div>
                  <div
                    data-testid="observed-visitors-count"
                    className="mt-2 text-2xl font-display font-bold text-foreground"
                  >
                    {data.observed.stages[0]?.count ?? 0}
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">Khách truy cập số liệu thật</div>
                </div>

                <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
                  <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                    <BookOpen className="h-3.5 w-3.5" />
                    <span>Source Reads</span>
                  </div>
                  <div
                    data-testid="observed-source-reads-count"
                    className="mt-2 text-2xl font-display font-bold text-foreground"
                  >
                    {data.observed.stages[1]?.count ?? 0}
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">Đọc sử liệu &gt;60s</div>
                </div>

                <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
                  <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                    <MessageSquare className="h-3.5 w-3.5" />
                    <span>Inquiries</span>
                  </div>
                  <div
                    data-testid="observed-inquiries-count"
                    className="mt-2 text-2xl font-display font-bold text-foreground"
                  >
                    {data.observed.stages[2]?.count ?? 0}
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">Phiếu yêu cầu đặt chỗ</div>
                </div>

                <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
                  <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                    <CalendarCheck className="h-3.5 w-3.5" />
                    <span>Confirmed</span>
                  </div>
                  <div
                    data-testid="observed-confirmed-count"
                    className="mt-2 text-2xl font-display font-bold text-foreground"
                  >
                    {data.observed.stages[3]?.count ?? 0}
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">Nghệ nhân xác nhận</div>
                </div>

                <div className="rounded-xl border border-border bg-card p-4 shadow-sm border-l-4 border-l-primary">
                  <div className="flex items-center gap-1.5 text-xs font-medium text-primary">
                    <Award className="h-3.5 w-3.5" />
                    <span>Completed</span>
                  </div>
                  <div
                    data-testid="observed-completed-count"
                    className="mt-2 text-2xl font-display font-bold text-foreground"
                  >
                    {data.observed.total_completed_experiences}
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">Trải nghiệm thực tế hoàn tất</div>
                </div>

                <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
                  <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                    <TrendingUp className="h-3.5 w-3.5" />
                    <span>Overall Conversion</span>
                  </div>
                  <div
                    data-testid="observed-overall-conversion"
                    className="mt-2 text-2xl font-display font-bold text-foreground"
                  >
                    {data.observed.overall_conversion_pct.toFixed(2)}%
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">Visitor → Completed</div>
                </div>
              </div>

              {/* 5-Stage Funnel Visual Progress */}
              <div className="rounded-xl border border-border bg-card p-6 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-display font-semibold text-foreground">
                    5-Stage Customer Conversion Funnel (OBSERVED ACTUALS)
                  </h2>
                  <span className="text-xs font-mono rounded bg-muted px-2 py-1 text-muted-foreground">
                    Tier: OBSERVED
                  </span>
                </div>
                <p className="text-sm text-muted-foreground">
                  Số liệu chuyển đổi từng bước thực tế từ nhật ký telemetry và bảng <code>rbpc_inquiries</code>.
                </p>

                <div className="space-y-4 pt-2">
                  {data.observed.stages.map((stg, idx) => (
                    <div key={stg.stage} className="space-y-1.5">
                      <div className="flex flex-wrap items-center justify-between text-sm">
                        <div className="font-semibold text-foreground flex items-center gap-2">
                          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary">
                            {idx + 1}
                          </span>
                          {stg.display_name}
                        </div>
                        <div className="flex items-center gap-4 text-xs font-mono">
                          <span className="text-foreground font-bold text-sm">{stg.count.toLocaleString()}</span>
                          <span className="text-muted-foreground">
                            Chuyển đổi từ bước trước:{" "}
                            <strong className="text-foreground">
                              {stg.conversion_from_previous_pct.toFixed(1)}%
                            </strong>
                          </span>
                        </div>
                      </div>
                      <div className="h-2.5 w-full rounded-full bg-muted overflow-hidden">
                        <div
                          className="h-full bg-primary transition-all duration-300"
                          style={{
                            width: `${Math.max(
                              stg.conversion_from_top_pct,
                              stg.count > 0 ? 4 : 0
                            )}%`,
                          }}
                        />
                      </div>
                      <div className="text-xs text-muted-foreground italic">
                        {stg.description} — <em>{stg.measurement_method}</em>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Quality Cohorts Table */}
              <div className="rounded-xl border border-border bg-card p-6 shadow-sm space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <h2 className="text-lg font-display font-semibold text-foreground">
                      Quality Cohorts Breakdown
                    </h2>
                    <p className="text-sm text-muted-foreground">
                      Phân tích chất lượng chuyển đổi theo kênh tiếp cận và làng nghề liên kết.
                    </p>
                  </div>
                  <span className="text-xs rounded bg-muted px-2.5 py-1 text-muted-foreground font-mono">
                    N={data.observed.quality_cohorts.length} Cohorts
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table
                    data-testid="quality-cohorts-table"
                    className="w-full text-left text-sm border-collapse"
                  >
                    <thead>
                      <tr className="border-b border-border bg-muted/40 text-xs uppercase text-muted-foreground font-semibold">
                        <th className="py-3 px-3">Cohort</th>
                        <th className="py-3 px-3">Phân loại</th>
                        <th className="py-3 px-3 text-right">Visitors</th>
                        <th className="py-3 px-3 text-right">Reads</th>
                        <th className="py-3 px-3 text-right">Inquiries</th>
                        <th className="py-3 px-3 text-right">Confirm</th>
                        <th className="py-3 px-3 text-right">Completed</th>
                        <th className="py-3 px-3 text-right">Inq → Conf %</th>
                        <th className="py-3 px-3 text-right">Conf → Comp %</th>
                        <th className="py-3 px-3 text-right">Nguồn chuẩn %</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {data.observed.quality_cohorts.map((c) => (
                        <tr key={c.cohort_id} className="hover:bg-muted/30 transition-colors">
                          <td className="py-3 px-3 font-medium text-foreground">{c.cohort_name}</td>
                          <td className="py-3 px-3 text-xs text-muted-foreground capitalize font-mono">
                            {c.cohort_type}
                          </td>
                          <td className="py-3 px-3 text-right font-mono">{c.visitor_count}</td>
                          <td className="py-3 px-3 text-right font-mono">{c.source_read_count}</td>
                          <td className="py-3 px-3 text-right font-mono font-semibold">{c.inquiry_count}</td>
                          <td className="py-3 px-3 text-right font-mono">{c.confirm_count}</td>
                          <td className="py-3 px-3 text-right font-mono font-bold text-primary">
                            {c.completed_count}
                          </td>
                          <td className="py-3 px-3 text-right font-mono">
                            {c.inquiry_to_confirm_pct.toFixed(1)}%
                          </td>
                          <td className="py-3 px-3 text-right font-mono">
                            {c.confirm_to_completed_pct.toFixed(1)}%
                          </td>
                          <td className="py-3 px-3 text-right font-mono text-emerald-600 font-semibold">
                            {c.source_grounding_score_pct.toFixed(0)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: HYPOTHESIS BENCHMARKS */}
          {activeTab === "hypothesis" && (
            <div className="space-y-6">
              <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-5 text-sm space-y-2">
                <div className="flex items-center gap-2 font-semibold text-amber-800 dark:text-amber-400">
                  <AlertTriangle className="h-4 w-4" />
                  Khung Giả Thuyết Mô Hình (HYPOTHESIS TIER)
                </div>
                <p className="text-amber-700 dark:text-amber-300">
                  {data.hypothesis.epistemic_disclaimer}
                </p>
              </div>

              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
                  <div className="text-xs uppercase text-muted-foreground font-semibold">
                    Độ Sâu Đọc Sử Liệu (B)
                  </div>
                  <div className="mt-2 text-3xl font-display font-bold text-foreground">
                    {data.hypothesis.benchmark_assumptions.story_engagement_rate_pct}%
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    Khách tương tác sâu &gt;60s với tư liệu
                  </div>
                </div>

                <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
                  <div className="text-xs uppercase text-muted-foreground font-semibold">
                    Tỷ Lệ Yêu Cầu (C)
                  </div>
                  <div className="mt-2 text-3xl font-display font-bold text-foreground">
                    {data.hypothesis.benchmark_assumptions.inquiry_conversion_rate_pct}%
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    Người đọc gửi phiếu đặt chỗ
                  </div>
                </div>

                <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
                  <div className="text-xs uppercase text-muted-foreground font-semibold">
                    Nghệ Nhân Nhận Lượt (D)
                  </div>
                  <div className="mt-2 text-3xl font-display font-bold text-foreground">
                    {data.hypothesis.benchmark_assumptions.partner_acceptance_rate_pct}%
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    Xác nhận chuẩn bị lò nung / vật liệu
                  </div>
                </div>

                <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
                  <div className="text-xs uppercase text-muted-foreground font-semibold">
                    Hoàn Tất Tham Gia (E)
                  </div>
                  <div className="mt-2 text-3xl font-display font-bold text-foreground">
                    {data.hypothesis.benchmark_assumptions.experience_completion_rate_pct}%
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    Khách có mặt và hoàn tất (11.11% hủy/vắng)
                  </div>
                </div>
              </div>

              {/* Modeled Monthly Funnel Simulation */}
              <div className="rounded-xl border border-border bg-card p-6 shadow-sm space-y-4">
                <h2 className="text-lg font-display font-semibold text-foreground">
                  Mô phỏng Phễu Tháng Tiêu Chuẩn (1,500 Lượt Tiếp Cận)
                </h2>
                <div className="grid gap-3 sm:grid-cols-5">
                  <div className="rounded-lg border border-border bg-muted/40 p-4 text-center">
                    <div className="text-xs text-muted-foreground">Visitors (A)</div>
                    <div className="mt-2 text-xl font-bold font-mono">
                      {data.hypothesis.modeled_monthly_funnel.visitors}
                    </div>
                  </div>
                  <div className="rounded-lg border border-border bg-muted/40 p-4 text-center">
                    <div className="text-xs text-muted-foreground">Engaged (A*B)</div>
                    <div className="mt-2 text-xl font-bold font-mono">
                      {data.hypothesis.modeled_monthly_funnel.engaged_story_readers}
                    </div>
                  </div>
                  <div className="rounded-lg border border-border bg-muted/40 p-4 text-center">
                    <div className="text-xs text-muted-foreground">Inquiries (A*B*C)</div>
                    <div className="mt-2 text-xl font-bold font-mono">
                      {data.hypothesis.modeled_monthly_funnel.qualified_inquiries}
                    </div>
                  </div>
                  <div className="rounded-lg border border-border bg-muted/40 p-4 text-center">
                    <div className="text-xs text-muted-foreground">Confirmed (D)</div>
                    <div className="mt-2 text-xl font-bold font-mono">
                      {data.hypothesis.modeled_monthly_funnel.confirmed_bookings}
                    </div>
                  </div>
                  <div className="rounded-lg border border-border bg-muted/40 p-4 text-center border-l-2 border-l-primary">
                    <div className="text-xs text-primary font-semibold">Completed (E)</div>
                    <div className="mt-2 text-xl font-bold font-mono text-primary">
                      {data.hypothesis.modeled_monthly_funnel.completed_experiences}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: FORECAST PROJECTIONS */}
          {activeTab === "forecast" && (
            <div className="space-y-6">
              <div
                data-testid="forecast-quarantine-box"
                className="rounded-xl border border-purple-500/30 bg-purple-500/10 p-6 space-y-4"
              >
                <div className="flex items-center gap-2 text-purple-800 dark:text-purple-300 font-bold text-base">
                  <Sparkles className="h-5 w-5" />
                  Khu Vực Cách Ly Dự Phóng (FORECAST QUARANTINE TIER)
                </div>
                <p className="text-sm text-purple-700 dark:text-purple-300">
                  {data.forecast.epistemic_disclaimer}
                </p>
                <div className="rounded-lg bg-background/80 p-3 text-xs text-muted-foreground font-mono">
                  {data.forecast.negative_abuse_guardrail}
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
                  <div className="text-xs uppercase text-muted-foreground font-semibold">
                    Mục Tiêu Năm 1 (SOM)
                  </div>
                  <div className="mt-2 text-3xl font-display font-bold text-foreground">
                    {data.forecast.projected_annual_bookings.toLocaleString()}
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    Lượt trải nghiệm mục tiêu (22 khách/xưởng/tháng)
                  </div>
                </div>

                <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
                  <div className="text-xs uppercase text-muted-foreground font-semibold">
                    Dự Phóng GMV (GBV)
                  </div>
                  <div className="mt-2 text-2xl font-display font-bold text-foreground">
                    {(data.forecast.projected_annual_gmv_vnd / 1_000_000).toFixed(0)}M VND
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    Tổng giá trị giao dịch dịch vụ di sản
                  </div>
                </div>

                <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
                  <div className="text-xs uppercase text-muted-foreground font-semibold">
                    Nghệ Nhân Giữ Lại (90%)
                  </div>
                  <div className="mt-2 text-2xl font-display font-bold text-emerald-600">
                    {(data.forecast.projected_artisan_retained_vnd / 1_000_000).toFixed(0)}M VND
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    Bảo vệ sinh kế gia đình nghề truyền thống
                  </div>
                </div>

                <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
                  <div className="text-xs uppercase text-muted-foreground font-semibold">
                    Doanh Thu Nền Tảng (10%)
                  </div>
                  <div className="mt-2 text-2xl font-display font-bold text-foreground">
                    {(data.forecast.projected_platform_net_revenue_vnd / 1_000_000).toFixed(0)}M VND
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    Phí vận hành chỉ thu khi khách hoàn tất
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: TRUTH AUDIT COMPARISON */}
          {activeTab === "audit" && (
            <div className="space-y-6">
              <div className="rounded-xl border border-border bg-card p-6 shadow-sm space-y-4">
                <h2 className="text-lg font-display font-semibold text-foreground">
                  Đối Soát Phân Tầng Sự Thật: OBSERVED vs FORECAST
                </h2>
                <p className="text-sm text-muted-foreground">
                  So sánh trực diện giữa số liệu hoàn thành thực tế và con số dự phóng 1,100 của đề án.
                </p>

                <div className="grid gap-4 md:grid-cols-2">
                  {/* Left: Real Observed */}
                  <div className="rounded-xl border border-emerald-500/40 bg-emerald-500/5 p-5 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold text-emerald-800 dark:text-emerald-400">
                        THỰC TẾ ĐÃ HOÀN THÀNH (OBSERVED)
                      </span>
                      <span className="text-xs rounded bg-emerald-500/20 px-2 py-0.5 text-emerald-700 font-mono">
                        Database Actuals
                      </span>
                    </div>
                    <div className="text-4xl font-display font-bold text-foreground">
                      {data.observed.total_completed_experiences}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Tổng hợp duy nhất từ các yêu cầu đặt chỗ có trạng thái <code>state == &apos;closed&apos;</code> trong cơ sở dữ liệu PostgreSQL. Khi không có giao dịch thật, giá trị luôn nghiêm ngặt bằng 0.
                    </p>
                  </div>

                  {/* Right: Forecast */}
                  <div className="rounded-xl border border-purple-500/40 bg-purple-500/5 p-5 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold text-purple-800 dark:text-purple-400">
                        MỤC TIÊU DỰ PHÓNG ĐỀ ÁN (FORECAST)
                      </span>
                      <span className="text-xs rounded bg-purple-500/20 px-2 py-0.5 text-purple-700 font-mono">
                        SOM Year 1
                      </span>
                    </div>
                    <div className="text-4xl font-display font-bold text-purple-700 dark:text-purple-300">
                      {data.forecast.projected_annual_bookings.toLocaleString()}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Mục tiêu công suất SOM năm 1 cho 5 xưởng đối tác trong tài liệu <code>DOC-RBPC-FIN-001 §2.3.3</code>. Được cách ly trong hồ sơ đề án, không bao giờ xuất hiện trong tầng hoàn tất thực tế.
                    </p>
                  </div>
                </div>

                {/* Audit Checklist Table */}
                <div className="rounded-xl border border-border p-4 bg-muted/20 space-y-3">
                  <div className="text-sm font-semibold text-foreground">
                    Tiêu chí kiểm định an toàn dữ liệu
                  </div>
                  <div className="space-y-2 text-xs">
                    <div className="flex items-center justify-between py-1.5 border-b border-border">
                      <span className="text-muted-foreground">
                        Con số 1,100 dự phóng có rò rỉ vào số lượt hoàn thành thực tế không?
                      </span>
                      <span className="font-semibold text-emerald-600 flex items-center gap-1">
                        <CheckCircle2 className="h-3.5 w-3.5" /> Tuyệt đối KHÔNG (False)
                      </span>
                    </div>
                    <div className="flex items-center justify-between py-1.5 border-b border-border">
                      <span className="text-muted-foreground">
                        Cơ sở dữ liệu trống có hiển thị 0 thay vì số liệu giả lập không?
                      </span>
                      <span className="font-semibold text-emerald-600 flex items-center gap-1">
                        <CheckCircle2 className="h-3.5 w-3.5" /> Đúng, nghiêm ngặt 0 (True)
                      </span>
                    </div>
                    <div className="flex items-center justify-between py-1.5 border-b border-border">
                      <span className="text-muted-foreground">
                        Yêu cầu &apos;new&apos;, &apos;contacted&apos;, &apos;confirmed&apos; có bị tính nhầm thành &apos;completed&apos; không?
                      </span>
                      <span className="font-semibold text-emerald-600 flex items-center gap-1">
                        <CheckCircle2 className="h-3.5 w-3.5" /> Không, chỉ &apos;closed&apos; mới được tính (True)
                      </span>
                    </div>
                    <div className="flex items-center justify-between py-1.5">
                      <span className="text-muted-foreground">
                        Tỷ lệ chia sẻ doanh thu cho nghệ nhân được bảo đảm ở mức nào?
                      </span>
                      <span className="font-semibold text-emerald-600 flex items-center gap-1">
                        <CheckCircle2 className="h-3.5 w-3.5" /> 90.0% doanh thu trải nghiệm
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </main>
  );
}
