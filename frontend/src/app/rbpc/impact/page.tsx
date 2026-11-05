"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Sparkles,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  Award,
  Users,
  Compass,
  Building2,
  ChevronRight,
  RefreshCw,
  AlertCircle,
  HelpCircle,
  CheckCircle2,
  Coins,
  BookOpen,
} from "lucide-react";
import type { RbpcImpactMetricsOut, RbpcLocale } from "@/types/rbpc";
import { getRbpcCopy } from "@/lib/rbpc/copy";
import { cn } from "@/lib/utils";
import { setPageMeta } from "@/lib/seo";
import { fetchImpactMetricsApi } from "@/lib/rbpc/inquiries";
import { RbpcCard } from "@/components/rbpc/RbpcCard";
import { RbpcButton } from "@/components/rbpc/RbpcButton";

export default function RbpcImpactDashboardPage({
  initialMetrics = null,
}: {
  initialMetrics?: RbpcImpactMetricsOut | null;
} = {}) {
  const [metrics, setMetrics] = useState<RbpcImpactMetricsOut | null>(initialMetrics);
  const [isLoading, setIsLoading] = useState<boolean>(!initialMetrics);
  const [error, setError] = useState<string | null>(null);
  const [locale, setLocale] = useState<RbpcLocale>("vi");

  const copy = getRbpcCopy(locale);

  useEffect(() => {
    setPageMeta({
      title:
        locale === "vi"
          ? "Bảng Tác Động Cộng Đồng — LƯU NIÊN RBPC 2026"
          : "Public Community Impact Dashboard — LUU NIEN RBPC 2026",
      description:
        locale === "vi"
          ? "Minh bạch số liệu tác động thực tế từ sự kiện hoàn tất và chi trả nghệ nhân, phân tách rõ ràng với dự phóng."
          : "Transparent real-world community impact metrics from completed experiences and artisan payouts, separated from forward projections.",
      path: "/rbpc/impact",
    });
  }, [locale]);

  const loadMetrics = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchImpactMetricsApi();
      setMetrics(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Không thể tải số liệu tác động";
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!initialMetrics) {
      loadMetrics();
    }
  }, [initialMetrics]);

  const formatVnd = (val: number | null | undefined): string => {
    if (val === null || val === undefined) return "0 ₫";
    return new Intl.NumberFormat("vi-VN", {
      style: "currency",
      currency: "VND",
      maximumFractionDigits: 0,
    }).format(val);
  };

  const observed = metrics?.observed_metrics;
  const projected = metrics?.projected_metrics;

  return (
    <div className="rbpc-theme min-h-screen bg-[var(--rbpc-bg)] text-[var(--rbpc-ink)] py-8 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-8">
        {/* Navigation Breadcrumb Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[var(--rbpc-divider-subtle)] pb-4">
          <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-xs text-[var(--rbpc-muted)]">
            <Link
              href="/explore"
              className="hover:text-[var(--rbpc-primary)] flex items-center gap-1 transition-colors"
            >
              <Compass className="h-3.5 w-3.5" aria-hidden="true" />
              <span>{copy.nav.discover}</span>
            </Link>
            <ChevronRight className="h-3 w-3" aria-hidden="true" />
            <Link
              href="/rbpc/inquiries"
              className="hover:text-[var(--rbpc-primary)] transition-colors"
            >
              {locale === "vi" ? "Yêu cầu trải nghiệm" : "Inquiries"}
            </Link>
            <ChevronRight className="h-3 w-3" aria-hidden="true" />
            <span className="font-semibold text-[var(--rbpc-ink)]">
              {locale === "vi" ? "Bảng tác động thực tế" : "Impact Dashboard"}
            </span>
          </nav>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setLocale(locale === "vi" ? "en" : "vi")}
              className="inline-flex items-center gap-1.5 rounded-full border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] px-3 py-1 text-xs font-semibold text-[var(--rbpc-ink)] hover:border-[var(--rbpc-primary-border)] transition-colors"
              aria-label="Toggle language"
            >
              <span>{locale === "vi" ? "English" : "Tiếng Việt"}</span>
            </button>
            <button
              type="button"
              onClick={loadMetrics}
              disabled={isLoading}
              className="inline-flex items-center gap-1.5 rounded-full border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] px-3 py-1 text-xs font-semibold text-[var(--rbpc-ink)] hover:border-[var(--rbpc-primary-border)] disabled:opacity-50 transition-colors"
              title={locale === "vi" ? "Làm mới số liệu" : "Refresh metrics"}
            >
              <RefreshCw className={cn("h-3.5 w-3.5", isLoading && "animate-spin text-[var(--rbpc-primary)]")} />
              <span>{locale === "vi" ? "Làm mới" : "Refresh"}</span>
            </button>
            <Link
              href="/rbpc/partner"
              className="inline-flex items-center gap-1.5 rounded-full border border-[var(--rbpc-primary-border)] bg-[var(--rbpc-primary-subtle)] px-3 py-1 text-xs font-semibold text-[var(--rbpc-primary)] hover:bg-[var(--rbpc-primary)] hover:text-white transition-all"
            >
              <span>{copy.nav.partnerInbox}</span>
              <ArrowRight className="h-3 w-3" aria-hidden="true" />
            </Link>
          </div>
        </div>

        {/* Header Title */}
        <div className="space-y-3">
          <div className="inline-flex items-center gap-2 rounded-full border border-[var(--rbpc-primary-border)] bg-[var(--rbpc-primary-subtle)] px-3 py-1 text-xs font-semibold text-[var(--rbpc-primary)]">
            <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
            <span>
              {locale === "vi"
                ? "Minh bạch số liệu thực tế — Không tạo số ảo hay thổi phồng quy mô"
                : "Real-world Observed Metrics — Zero Synthetic Counts or Inflated Pitch Numbers"}
            </span>
          </div>

          <h1 className="font-serif text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-[var(--rbpc-ink)]">
            {locale === "vi"
              ? "Bảng Tác Động Thực Tế & Đối Soát Minh Bạch"
              : "Public Community Impact & Transparency Dashboard"}
          </h1>
          <p className="max-w-3xl text-sm sm:text-base text-[var(--rbpc-muted)] leading-relaxed">
            {locale === "vi"
              ? "Toàn bộ số liệu thực tế được tổng hợp trực tiếp từ cơ sở dữ liệu xác thực (trải nghiệm hoàn tất, thanh toán thực tế cho nghệ nhân, bảo trợ hiện vật đã ký kết). Dự phóng kinh doanh được tách biệt thành vùng riêng."
              : "All observed metrics are aggregated directly from verified database events (completed inquiries, settled artisan payouts, signed corporate in-kind sponsorship). Forward commercial projections are clearly quarantined in a separate section."}
          </p>
        </div>

        {/* Error State */}
        {error && (
          <div
            role="alert"
            className="flex items-start gap-3 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-800 dark:text-red-200"
          >
            <AlertCircle className="h-5 w-5 shrink-0 mt-0.5 text-red-600" aria-hidden="true" />
            <div>
              <p className="font-semibold">
                {locale === "vi" ? "Không thể tải số liệu tác động" : "Failed to load impact metrics"}
              </p>
              <p className="mt-1 text-xs opacity-90">{error}</p>
              <button
                type="button"
                onClick={loadMetrics}
                className="mt-2 inline-flex items-center gap-1 rounded bg-red-600 text-white px-2.5 py-1 text-xs font-medium hover:bg-red-700 transition"
              >
                {locale === "vi" ? "Thử lại" : "Retry"}
              </button>
            </div>
          </div>
        )}

        {/* Loading Skeleton */}
        {isLoading && !metrics && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
            {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
              <div key={i} className="h-32 rounded-lg border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-4" />
            ))}
          </div>
        )}

        {/* Section 1: Real Database-Observed Statistics */}
        {observed && (
          <section aria-labelledby="observed-metrics-heading" className="space-y-4">
            <div className="flex items-center justify-between border-b border-[var(--rbpc-divider-subtle)] pb-2">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-emerald-600" aria-hidden="true" />
                <h2 id="observed-metrics-heading" className="text-lg font-bold text-[var(--rbpc-ink)]">
                  {locale === "vi"
                    ? "1. Số Liệu Thực Tế Ghi Nhận (Database-Observed)"
                    : "1. Verified Observed Platform Metrics"}
                </h2>
              </div>
              <span className="text-xs text-[var(--rbpc-muted)]">
                {locale === "vi" ? "Nguồn dữ liệu: Cơ sở dữ liệu thật" : "Source: Live database events"}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Completed Experiences */}
              <RbpcCard className="p-5 flex flex-col justify-between">
                <div>
                  <span className="text-xs font-medium text-[var(--rbpc-muted)] uppercase tracking-wider">
                    {locale === "vi" ? "Trải nghiệm hoàn tất" : "Completed Experiences"}
                  </span>
                  <div
                    data-testid="completed-experiences-count"
                    className="mt-2 text-3xl font-extrabold text-[var(--rbpc-ink)]"
                  >
                    {observed.completed_experiences_count}
                  </div>
                </div>
                <p className="mt-3 text-xs text-[var(--rbpc-muted)]">
                  {locale === "vi"
                    ? "Tổng số lượt trải nghiệm văn hóa đã hoàn tất (trạng thái closed)."
                    : "Total verified completed cultural visits with closed status."}
                </p>
              </RbpcCard>

              {/* Artisan Net Payout */}
              <RbpcCard className="p-5 flex flex-col justify-between border-emerald-500/40 bg-emerald-50/30 dark:bg-emerald-950/20">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-emerald-800 dark:text-emerald-300 uppercase tracking-wider">
                      {locale === "vi" ? "Chi trả thực tế nghệ nhân" : "Settled Artisan Payouts"}
                    </span>
                    <Coins className="h-4 w-4 text-emerald-600" aria-hidden="true" />
                  </div>
                  <div
                    data-testid="artisan-payout-settled"
                    className="mt-2 text-3xl font-extrabold text-emerald-700 dark:text-emerald-400"
                  >
                    {formatVnd(observed.artisan_payout_vnd_settled)}
                  </div>
                </div>
                <p className="mt-3 text-xs text-emerald-800/80 dark:text-emerald-300/80">
                  {locale === "vi"
                    ? "Doanh thu thực tế đã đối soát qua sổ cái và chi trả trực tiếp cho nghệ nhân."
                    : "Actual verified payout distributed directly to artisans after compliance approval."}
                </p>
              </RbpcCard>

              {/* In-Kind Sponsorship */}
              <RbpcCard className="p-5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-[var(--rbpc-muted)] uppercase tracking-wider">
                      {locale === "vi" ? "Bảo trợ hiện vật xác thực" : "Verified In-Kind Sponsorship"}
                    </span>
                    <Award className="h-4 w-4 text-[var(--rbpc-primary)]" aria-hidden="true" />
                  </div>
                  <div
                    data-testid="sponsor-support-verified"
                    className="mt-2 text-2xl font-bold text-[var(--rbpc-primary)]"
                  >
                    {formatVnd(observed.sponsor_support_vnd_verified)}
                  </div>
                </div>
                <p className="mt-3 text-xs text-[var(--rbpc-muted)]">
                  {locale === "vi"
                    ? "Tài trợ hạ tầng VPS và tín dụng AI có hợp đồng ký kết (BNIX + Phổ Tuệ)."
                    : "Signed infrastructure and AI compute subsidy (BNIX + Pho Tue agreement)."}
                </p>
              </RbpcCard>

              {/* Total Inquiries */}
              <RbpcCard className="p-5 flex flex-col justify-between">
                <div>
                  <span className="text-xs font-medium text-[var(--rbpc-muted)] uppercase tracking-wider">
                    {locale === "vi" ? "Yêu cầu trải nghiệm tiếp nhận" : "Total Inquiries Logged"}
                  </span>
                  <div
                    data-testid="total-inquiries-count"
                    className="mt-2 text-3xl font-extrabold text-[var(--rbpc-ink)]"
                  >
                    {observed.total_inquiries_received}
                  </div>
                </div>
                <p className="mt-3 text-xs text-[var(--rbpc-muted)]">
                  {locale === "vi"
                    ? "Tổng lượt khách gửi yêu cầu đặt lịch trải nghiệm qua hệ thống."
                    : "Total visitor booking inquiries registered."}
                </p>
              </RbpcCard>

              {/* Consented Creators */}
              <RbpcCard className="p-5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-[var(--rbpc-muted)] uppercase tracking-wider">
                      {locale === "vi" ? "Nghệ nhân có chấp thuận" : "Consented Artisans"}
                    </span>
                    <Users className="h-4 w-4 text-[var(--rbpc-muted)]" aria-hidden="true" />
                  </div>
                  <div
                    data-testid="consented-creators-count"
                    className="mt-2 text-3xl font-extrabold text-[var(--rbpc-ink)]"
                  >
                    {observed.consented_creators_count}
                  </div>
                </div>
                <p className="mt-3 text-xs text-[var(--rbpc-muted)]">
                  {locale === "vi"
                    ? "Nghệ nhân truyền thống có văn bản chấp thuận sử dụng hình ảnh và thông tin."
                    : "Traditional makers with verified written consent on file."}
                </p>
              </RbpcCard>

              {/* Active Workshop Experiences */}
              <RbpcCard className="p-5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-[var(--rbpc-muted)] uppercase tracking-wider">
                      {locale === "vi" ? "Workshop đang mở nhận lịch" : "Active Experiences"}
                    </span>
                    <Building2 className="h-4 w-4 text-[var(--rbpc-muted)]" aria-hidden="true" />
                  </div>
                  <div
                    data-testid="active-experiences-count"
                    className="mt-2 text-3xl font-extrabold text-[var(--rbpc-ink)]"
                  >
                    {observed.active_experiences_count}
                  </div>
                </div>
                <p className="mt-3 text-xs text-[var(--rbpc-muted)]">
                  {locale === "vi"
                    ? "Danh mục trải nghiệm văn hóa ở chế độ tiếp nhận yêu cầu (inquiry-only)."
                    : "Experiences published under honest inquiry-only booking mode."}
                </p>
              </RbpcCard>

              {/* Published Stories */}
              <RbpcCard className="p-5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-[var(--rbpc-muted)] uppercase tracking-wider">
                      {locale === "vi" ? "Hành trình di sản xuất bản" : "Published Stories"}
                    </span>
                    <BookOpen className="h-4 w-4 text-[var(--rbpc-muted)]" aria-hidden="true" />
                  </div>
                  <div
                    data-testid="published-stories-count"
                    className="mt-2 text-3xl font-extrabold text-[var(--rbpc-ink)]"
                  >
                    {observed.published_stories_count}
                  </div>
                </div>
                <p className="mt-3 text-xs text-[var(--rbpc-muted)]">
                  {locale === "vi"
                    ? "Hành trình văn hóa được biên soạn với trích dẫn tư liệu chuẩn xác."
                    : "Editorial narratives linked to verified archival citations."}
                </p>
              </RbpcCard>

              {/* Verified Sources */}
              <RbpcCard className="p-5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-[var(--rbpc-muted)] uppercase tracking-wider">
                      {locale === "vi" ? "Trích dẫn khảo cứu xác thực" : "Verified Citations"}
                    </span>
                    <ShieldCheck className="h-4 w-4 text-[var(--rbpc-muted)]" aria-hidden="true" />
                  </div>
                  <div
                    data-testid="verified-citations-count"
                    className="mt-2 text-3xl font-extrabold text-[var(--rbpc-ink)]"
                  >
                    {observed.verified_source_citations_count}
                  </div>
                </div>
                <p className="mt-3 text-xs text-[var(--rbpc-muted)]">
                  {locale === "vi"
                    ? "Luận điểm lịch sử được kiểm chứng qua tư liệu gốc và UNESCO."
                    : "Historical claims corroborated by primary archives."}
                </p>
              </RbpcCard>
            </div>
          </section>
        )}

        {/* Section 2: Forward Commercial Projections (Explicitly Separated & Quarantined) */}
        {projected && (
          <section aria-labelledby="projected-metrics-heading" className="space-y-4 pt-4">
            <div className="flex items-center justify-between border-b border-amber-500/30 pb-2">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-amber-600" aria-hidden="true" />
                <h2 id="projected-metrics-heading" className="text-lg font-bold text-amber-900 dark:text-amber-200">
                  {locale === "vi"
                    ? "2. Số Liệu Dự Phóng Mô Hình Kinh Doanh (Forward Projections — Phân Tách Rõ)"
                    : "2. Forward Commercial Hypotheses & Projections (Clearly Separated)"}
                </h2>
              </div>
              <span className="inline-flex items-center gap-1 rounded-full border border-amber-500/40 bg-amber-500/10 px-2.5 py-0.5 text-xs font-semibold text-amber-800 dark:text-amber-300">
                <HelpCircle className="h-3 w-3" />
                {locale === "vi" ? "Giả định nghiên cứu RBPC 2026" : "Hypothetical RBPC Model"}
              </span>
            </div>

            {/* Projection Basis Banner */}
            <div
              data-testid="projection-basis-disclaimer"
              className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 text-xs text-amber-900 dark:text-amber-200"
            >
              <div className="font-semibold mb-1">
                {locale === "vi"
                  ? "Cảnh báo phương pháp luận (Epistemic Disclaimers):"
                  : "Methodological Transparency Notice:"}
              </div>
              <p>{projected.projection_basis}</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <RbpcCard className="p-5 border-amber-500/30 bg-amber-50/20 dark:bg-amber-950/10">
                <span className="text-xs font-medium text-amber-900/80 dark:text-amber-300/80 uppercase tracking-wider">
                  {locale === "vi" ? "Dự phóng nhu cầu tháng (Giả định)" : "Estimated Monthly Inquiries (Projected)"}
                </span>
                <div
                  data-testid="projected-monthly-demand"
                  className="mt-2 text-3xl font-extrabold text-amber-800 dark:text-amber-400"
                >
                  {projected.estimated_monthly_demand !== null && projected.estimated_monthly_demand !== undefined
                    ? `~${projected.estimated_monthly_demand} yêu cầu/tháng`
                    : "—"}
                </div>
                <p className="mt-3 text-xs text-[var(--rbpc-muted)]">
                  {locale === "vi"
                    ? "Dự phóng lượng khách có nhu cầu tham gia workshop văn hóa Huế trong giai đoạn mở rộng pilot."
                    : "Estimated monthly qualified inquiries based on pilot conversion benchmarks."}
                </p>
              </RbpcCard>

              <RbpcCard className="p-5 border-amber-500/30 bg-amber-50/20 dark:bg-amber-950/10">
                <span className="text-xs font-medium text-amber-900/80 dark:text-amber-300/80 uppercase tracking-wider">
                  {locale === "vi" ? "Dự phóng giá trị tạo cho địa phương" : "Projected Local Value Addition"}
                </span>
                <div
                  data-testid="projected-local-value"
                  className="mt-2 text-3xl font-extrabold text-amber-800 dark:text-amber-400"
                >
                  {formatVnd(projected.projected_local_value_addition_vnd)}
                </div>
                <p className="mt-3 text-xs text-[var(--rbpc-muted)]">
                  {locale === "vi"
                    ? "Giá trị gia tăng kinh tế kỳ vọng chuyển trực tiếp đến các gia đình nghệ nhân khi vận hành toàn diện."
                    : "Estimated annual economic value retained by craft communities under the SOM plan."}
                </p>
              </RbpcCard>
            </div>
          </section>
        )}

        {/* Integrity Notice Footer */}
        <div className="rounded-xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-6 text-xs text-[var(--rbpc-muted)] space-y-2">
          <div className="font-semibold text-[var(--rbpc-ink)] flex items-center gap-1.5">
            <ShieldCheck className="h-4 w-4 text-emerald-600" />
            <span>
              {locale === "vi"
                ? "Cam kết liêm chính số liệu LƯU NIÊN"
                : "LUU NIEN Data Integrity & Verification Commitment"}
            </span>
          </div>
          <p>
            {locale === "vi"
              ? "Trong trường hợp cơ sở dữ liệu trống hoặc đang triển khai mới, bảng tác động hiển thị chính xác 0 và không đưa ra bất kỳ con số tổng hợp ảo nào. Chúng tôi tuyệt đối không sử dụng dữ liệu tiếp thị để ngụy tạo thành tích."
              : "When the database is empty or freshly initialized, the dashboard strictly renders 0 and never outputs fabricated pitch numbers. We do not conflate pitch hypotheses with actual transactions."}
          </p>
          <div className="pt-2 flex flex-wrap gap-4 text-[var(--rbpc-primary)] font-medium">
            <Link href="/rbpc/inquiries" className="hover:underline flex items-center gap-1">
              <span>{locale === "vi" ? "Gửi yêu cầu trải nghiệm" : "Submit Experience Inquiry"}</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
            <Link href="/rbpc/partner" className="hover:underline flex items-center gap-1">
              <span>{locale === "vi" ? "Cổng điều phối đối tác" : "Partner Operations Console"}</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
            <Link href="/explore" className="hover:underline flex items-center gap-1">
              <span>{locale === "vi" ? "Khám phá di sản Huế" : "Explore Huế Heritage"}</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
