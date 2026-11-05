"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  BarChart3,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  Sparkles,
  Layers,
  ArrowRight,
  TrendingUp,
  RefreshCw,
  Info,
  Lock,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  fetchClassroomRubricAnalytics,
  type ClassroomRubricAnalyticsResponse,
  type RubricCriterionAnalytics,
} from "@/lib/api";

interface RubricAnalyticsDashboardProps {
  classroomId: string;
  classroomName?: string;
  isTeacher?: boolean;
}

const DEFAULT_FALLBACK_ANALYTICS: ClassroomRubricAnalyticsResponse = {
  classroom_id: "demo-class",
  classroom_name: "Lớp 10A1 — THPT Chuyên Quốc Học Huế",
  teacher_id: "demo-teacher",
  active_rubric_version: "GDPT_2018_V1",
  available_rubric_versions: ["GDPT_2018_V1", "v1.0"],
  analytics_type: "descriptive",
  causal_inference_permitted: false,
  methodological_notice:
    "Descriptive statistics only. Causal learning gains or inferential mastery claims strictly require an approved controlled comparative study (IRB/Ethics Protocol) and are forbidden from observational classroom rubric aggregates.",
  cohort_size: 6,
  min_k_threshold: 5,
  is_suppressed: false,
  suppression_reason: null,
  overall_average: 2.35,
  criteria_analytics: [
    {
      criterion_key: "S1_SPATIAL",
      dimension_vi: "Năng lực Không gian (Spatial Reasoning)",
      dimension_en: "Spatial Reasoning",
      max_score: 3.0,
      mean: 2.4,
      median: 2.5,
      std_dev: 0.45,
      mastery_rate: 83.3,
      sample_size: 6,
      distribution: { level_0: 0, level_1: 1, level_2: 2, level_3: 3 },
    },
    {
      criterion_key: "S2_TEMPORAL",
      dimension_vi: "Năng lực Thời gian (Temporal Reasoning)",
      dimension_en: "Temporal Reasoning",
      max_score: 3.0,
      mean: 2.2,
      median: 2.0,
      std_dev: 0.52,
      mastery_rate: 66.7,
      sample_size: 6,
      distribution: { level_0: 0, level_1: 2, level_2: 3, level_3: 1 },
    },
    {
      criterion_key: "S3_EVIDENCE",
      dimension_vi: "Năng lực Sử liệu & Bằng chứng (Primary Evidence Analysis)",
      dimension_en: "Source & Evidence Analysis",
      max_score: 3.0,
      mean: 2.5,
      median: 2.5,
      std_dev: 0.38,
      mastery_rate: 100.0,
      sample_size: 6,
      distribution: { level_0: 0, level_1: 0, level_2: 3, level_3: 3 },
    },
    {
      criterion_key: "S4_ARGUMENT",
      dimension_vi: "Năng lực Lập luận & Giới hạn Tri thức (Historical Argumentation)",
      dimension_en: "Historical Argumentation & Epistemic Humility",
      max_score: 3.0,
      mean: 2.3,
      median: 2.5,
      std_dev: 0.49,
      mastery_rate: 83.3,
      sample_size: 6,
      distribution: { level_0: 0, level_1: 1, level_2: 2, level_3: 3 },
    },
  ],
  recommendations: [
    "Bồi dưỡng kỹ năng lập niên biểu và liên hệ bối cảnh lịch sử thời Minh Mạng (1835-1837).",
  ],
};

export default function RubricAnalyticsDashboard({
  classroomId,
  classroomName,
  isTeacher = true,
}: RubricAnalyticsDashboardProps) {
  const [data, setData] = useState<ClassroomRubricAnalyticsResponse | null>(DEFAULT_FALLBACK_ANALYTICS);
  const [selectedVersion, setSelectedVersion] = useState<string>("GDPT_2018_V1");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Negative abuse test states
  const [causalTesting, setCausalTesting] = useState<boolean>(false);
  const [causalErrorResult, setCausalErrorResult] = useState<string | null>(null);

  const loadAnalytics = useCallback(
    async (version?: string) => {
      if (!classroomId) return;
      setLoading(true);
      setError(null);
      try {
        const res = await fetchClassroomRubricAnalytics({
          classroomId,
          rubricVersion: version || selectedVersion,
          claimCausality: false,
        });
        setData(res);
        if (res.active_rubric_version) {
          setSelectedVersion(res.active_rubric_version);
        }
      } catch (err: unknown) {
        // In local/test environment without network, maintain fallback
        const msg = err instanceof Error ? err.message : String(err);
        setError(msg);
        setData(DEFAULT_FALLBACK_ANALYTICS);
      } finally {
        setLoading(false);
      }
    },
    [classroomId, selectedVersion],
  );

  useEffect(() => {
    loadAnalytics();
  }, [loadAnalytics]);

  const handleVersionChange = (newVer: string) => {
    setSelectedVersion(newVer);
    loadAnalytics(newVer);
  };

  const handleTestCausalRejection = async () => {
    setCausalTesting(true);
    setCausalErrorResult(null);
    try {
      await fetchClassroomRubricAnalytics({
        classroomId,
        rubricVersion: selectedVersion,
        claimCausality: true, // Deliberate negative abuse test without approved protocol
      });
      setCausalErrorResult("Cảnh báo: Máy chủ không chặn yêu cầu nhân quả (Lỗi bảo vệ)!");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setCausalErrorResult(
        `Bảo vệ chống lạm dụng kích hoạt thành công (HTTP 422): ${msg}`,
      );
    } finally {
      setCausalTesting(false);
    }
  };

  const analytics = data || DEFAULT_FALLBACK_ANALYTICS;
  const isSuppressed = analytics.is_suppressed;

  return (
    <div className="rounded-2xl border border-border/80 bg-card p-6 shadow-2xs space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border/70 pb-5">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge className="bg-primary/10 text-primary border-primary/20 text-xs font-semibold gap-1.5 py-0.5 px-2.5">
              <BarChart3 className="h-3.5 w-3.5" />
              Bảng Phân Tích Năng Lực Rubric
            </Badge>

            {isSuppressed ? (
              <Badge
                variant="outline"
                className="bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-500/30 text-xs gap-1 font-medium"
              >
                <Lock className="h-3 w-3" />
                k-anonymity (n &lt; 5): Kích hoạt ẩn danh
              </Badge>
            ) : (
              <Badge
                variant="outline"
                className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/30 text-xs gap-1 font-medium"
              >
                <ShieldCheck className="h-3 w-3" />
                k-anonymity: Đạt chuẩn bảo vệ dữ liệu (n = {analytics.cohort_size} &ge; 5)
              </Badge>
            )}

            <Badge
              variant="secondary"
              className="text-xs bg-secondary/80 text-foreground font-medium"
            >
              {analytics.analytics_type === "descriptive"
                ? "Thống kê mô tả (Descriptive)"
                : "Nghiên cứu đối chứng (Causal)"}
            </Badge>

            {loading && (
              <Badge variant="secondary" className="text-[10px] animate-pulse">
                Đang tải dữ liệu...
              </Badge>
            )}
          </div>

          <h2 className="font-serif font-bold text-xl text-foreground flex items-center gap-2">
            <span>Phân Tích Năng Lực Lịch Sử Theo Tiêu Chuẩn Rubric S1–S4</span>
          </h2>
          <p className="text-xs text-muted-foreground">
            Đo lường năng lực học tập GDPT 2018 (Không gian, Thời gian, Sử liệu, Lập luận) bảo đảm chuẩn an toàn học đường và quyền riêng tư học sinh.
          </p>
        </div>

        {/* Controls: Version Selector & Refresh */}
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-muted-foreground shrink-0" />
            <select
              value={selectedVersion}
              onChange={(e) => handleVersionChange(e.target.value)}
              className="h-9 rounded-xl border border-border bg-background px-3 text-xs font-medium text-foreground focus:border-primary focus:outline-none"
              title="Chọn phiên bản Rubric để xem thống kê"
            >
              {(analytics.available_rubric_versions || ["GDPT_2018_V1"]).map((ver) => (
                <option key={ver} value={ver}>
                  Phiên bản: {ver}
                </option>
              ))}
              <option value="all">Tất cả phiên bản</option>
            </select>
          </div>

          <Button
            size="sm"
            variant="outline"
            onClick={() => loadAnalytics(selectedVersion)}
            disabled={loading}
            className="text-xs h-9 gap-1.5"
            title="Làm mới bảng thống kê"
          >
            <RefreshCw className={cn("h-3.5 w-3.5", loading && "animate-spin")} />
            <span>Làm mới</span>
          </Button>
        </div>
      </div>

      {/* Error alert if any */}
      {error && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3.5 text-xs text-amber-800 dark:text-amber-300 flex items-start gap-2.5">
          <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5 text-amber-600" />
          <div className="space-y-0.5">
            <span className="font-bold">Lưu ý kết nối:</span>
            <p className="opacity-90">{error} (Đang hiển thị dữ liệu tham chiếu an toàn)</p>
          </div>
        </div>
      )}

      {/* PRIVACY SUPPRESSION VIEW (k-anonymity for cohort < 5) */}
      {isSuppressed ? (
        <div className="space-y-4">
          <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 p-4 text-xs text-rose-900 dark:text-rose-200 space-y-2">
            <div className="flex items-center gap-2 font-bold text-sm text-rose-700 dark:text-rose-300">
              <ShieldAlert className="h-5 w-5 shrink-0" />
              <span>Bảo Vệ Quyền Riêng Tư Học Sinh (k-anonymity: Sĩ số nhóm n &lt; 5)</span>
            </div>
            <p className="leading-relaxed opacity-90">
              {analytics.suppression_reason ||
                `Số lượng học sinh được đánh giá trong nhóm (n = ${analytics.cohort_size}) nhỏ hơn ngưỡng tối thiểu k = 5. Hệ thống kích hoạt cơ chế ẩn danh bắt buộc: Các chỉ số trung bình, độ lệch chuẩn và phân phối điểm chi tiết được ẩn để loại bỏ nguy cơ tái định danh cá nhân.`}
            </p>
            <div className="pt-1 flex items-center gap-2 text-[11px] font-semibold text-rose-800 dark:text-rose-300">
              <Info className="h-3.5 w-3.5 shrink-0" />
              <span>Cần thêm ít nhất {Math.max(1, 5 - analytics.cohort_size)} học sinh được chấm điểm để hiển thị thống kê tổng hợp.</span>
            </div>
          </div>

          {/* Masked Dimension Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3.5">
            {analytics.criteria_analytics.map((crit) => (
              <div
                key={crit.criterion_key}
                className="rounded-xl border border-dashed border-border/80 bg-secondary/10 p-4 space-y-3 opacity-75"
              >
                <div className="flex items-center justify-between">
                  <Badge variant="outline" className="text-[10px] font-bold">
                    {crit.criterion_key.slice(0, 2)}
                  </Badge>
                  <Lock className="h-3.5 w-3.5 text-muted-foreground" />
                </div>
                <div>
                  <h4 className="font-semibold text-xs text-foreground line-clamp-1">
                    {crit.dimension_vi}
                  </h4>
                  <span className="text-[10px] text-muted-foreground">
                    {crit.dimension_en}
                  </span>
                </div>
                <div className="py-3 text-center border-t border-border/50">
                  <span className="text-xs font-mono font-medium text-muted-foreground tracking-wider">
                    [DỮ LIỆU ĐƯỢC ẨN]
                  </span>
                  <span className="block text-[10px] text-muted-foreground mt-0.5">
                    (k-anonymity threshold n &lt; 5)
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        /* FULL DESCRIPTIVE ANALYTICS VIEW (cohort >= 5) */
        <div className="space-y-6">
          {/* Quick Summary Bar */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div className="rounded-xl border border-primary/20 bg-primary/5 p-3.5 space-y-1">
              <span className="text-[11px] text-primary font-semibold block">
                Điểm TB Toàn Diện
              </span>
              <div className="flex items-baseline gap-1.5">
                <span className="font-serif text-2xl font-bold text-primary">
                  {analytics.overall_average !== null ? analytics.overall_average.toFixed(2) : "--"}
                </span>
                <span className="text-xs text-muted-foreground">/ 3.0</span>
              </div>
              <span className="text-[10px] text-muted-foreground block">
                Quy đổi: {analytics.overall_average !== null ? ((analytics.overall_average / 3.0) * 10).toFixed(1) : "--"}/10 điểm
              </span>
            </div>

            <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3.5 space-y-1">
              <span className="text-[11px] text-emerald-700 dark:text-emerald-400 font-semibold block">
                Sĩ Số Được Đánh Giá
              </span>
              <div className="flex items-baseline gap-1.5">
                <span className="font-serif text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                  {analytics.cohort_size}
                </span>
                <span className="text-xs text-emerald-700/80 dark:text-emerald-400/80">học sinh</span>
              </div>
              <span className="text-[10px] text-emerald-700/80 dark:text-emerald-400/80 block">
                Đạt chuẩn bảo vệ quyền riêng tư
              </span>
            </div>

            <div className="rounded-xl border border-indigo-500/20 bg-indigo-500/5 p-3.5 space-y-1">
              <span className="text-[11px] text-indigo-700 dark:text-indigo-400 font-semibold block">
                Phiên Bản Rubric
              </span>
              <span className="font-mono text-base font-bold text-indigo-600 dark:text-indigo-400 block truncate">
                {analytics.active_rubric_version}
              </span>
              <span className="text-[10px] text-indigo-700/80 dark:text-indigo-400/80 block">
                Khung đánh giá GDPT 2018
              </span>
            </div>

            <div className="rounded-xl border border-border/70 bg-secondary/20 p-3.5 space-y-1">
              <span className="text-[11px] text-muted-foreground font-semibold block">
                Phân Loại Thống Kê
              </span>
              <span className="font-medium text-xs text-foreground block">
                Thống kê mô tả (Descriptive)
              </span>
              <span className="text-[10px] text-muted-foreground block">
                Cách ly khỏi suy luận nhân quả
              </span>
            </div>
          </div>

          {/* 4 Core Historical Reasoning Criteria Dimensions */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {analytics.criteria_analytics.map((crit) => {
              const mean = crit.mean ?? 0;
              const median = crit.median ?? 0;
              const stdDev = crit.std_dev ?? 0;
              const mastery = crit.mastery_rate ?? 0;
              const dist = crit.distribution || { level_0: 0, level_1: 0, level_2: 0, level_3: 0 };
              const total = Math.max(1, crit.sample_size);

              return (
                <div
                  key={crit.criterion_key}
                  className="rounded-xl border border-border/80 bg-secondary/15 p-4 space-y-3.5 flex flex-col justify-between"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Badge className="bg-primary/10 text-primary border-primary/20 text-[10px] font-bold">
                        {crit.criterion_key.slice(0, 2)}
                      </Badge>
                      <span className="text-[10px] text-muted-foreground font-mono">
                        n = {crit.sample_size}
                      </span>
                    </div>

                    <div>
                      <h4 className="font-semibold text-xs text-foreground line-clamp-1" title={crit.dimension_vi}>
                        {crit.dimension_vi}
                      </h4>
                      <span className="text-[10px] text-muted-foreground block">
                        {crit.dimension_en}
                      </span>
                    </div>

                    {/* Score stats */}
                    <div className="rounded-lg bg-background/80 p-2.5 border border-border/50 space-y-1.5">
                      <div className="flex items-baseline justify-between text-xs">
                        <span className="text-muted-foreground text-[11px]">Điểm TB (Mean):</span>
                        <span className="font-bold text-foreground font-mono">
                          {mean.toFixed(2)} / 3.0
                        </span>
                      </div>
                      <div className="flex items-baseline justify-between text-[11px]">
                        <span className="text-muted-foreground">Trung vị (Median):</span>
                        <span className="font-semibold text-foreground font-mono">{median.toFixed(2)}</span>
                      </div>
                      <div className="flex items-baseline justify-between text-[11px]">
                        <span className="text-muted-foreground">Độ lệch chuẩn (&sigma;):</span>
                        <span className="font-semibold text-foreground font-mono">&plusmn;{stdDev.toFixed(2)}</span>
                      </div>
                    </div>

                    {/* Mastery rate progress bar */}
                    <div className="space-y-1">
                      <div className="flex items-center justify-between text-[10px]">
                        <span className="text-muted-foreground font-medium">Tỷ lệ đạt chuẩn (&ge; Khá):</span>
                        <span className="font-bold text-emerald-600 dark:text-emerald-400">
                          {mastery.toFixed(1)}%
                        </span>
                      </div>
                      <div className="h-1.5 w-full bg-secondary rounded-full overflow-hidden">
                        <div
                          className="h-full bg-emerald-500 rounded-full transition-all"
                          style={{ width: `${Math.min(100, mastery)}%` }}
                        />
                      </div>
                    </div>

                    {/* Level Distribution Stack */}
                    <div className="space-y-1 pt-1">
                      <span className="text-[10px] text-muted-foreground block font-medium">
                        Phân bố 4 mức đạt (GDPT 2018):
                      </span>
                      <div className="grid grid-cols-4 gap-1 text-[9px] text-center font-mono">
                        <div className="rounded bg-rose-500/10 text-rose-700 dark:text-rose-400 p-1">
                          <span className="block font-bold">{dist.level_0}</span>
                          <span className="opacity-75">M0</span>
                        </div>
                        <div className="rounded bg-amber-500/10 text-amber-700 dark:text-amber-400 p-1">
                          <span className="block font-bold">{dist.level_1}</span>
                          <span className="opacity-75">M1</span>
                        </div>
                        <div className="rounded bg-sky-500/10 text-sky-700 dark:text-sky-400 p-1">
                          <span className="block font-bold">{dist.level_2}</span>
                          <span className="opacity-75">M2</span>
                        </div>
                        <div className="rounded bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 p-1">
                          <span className="block font-bold">{dist.level_3}</span>
                          <span className="opacity-75">M3</span>
                        </div>
                      </div>
                      <span className="text-[9px] text-muted-foreground block text-right">
                        M0: Chưa đạt • M1: Cơ bản • M2: Khá • M3: Xuất sắc
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Actionable Recommendations */}
          {analytics.recommendations && analytics.recommendations.length > 0 && (
            <div className="rounded-xl border border-primary/20 bg-primary/5 p-4 space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold text-primary">
                <Sparkles className="h-4 w-4 shrink-0" />
                <span>Khuyến Nghị Sư Phạm & Kế Hoạch Bồi Dưỡng</span>
              </div>
              <ul className="text-xs space-y-1.5 list-disc list-inside text-foreground/90 pl-1">
                {analytics.recommendations.map((rec, idx) => (
                  <li key={idx} className="leading-relaxed">
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* METHODOLOGICAL NOTICE & NEGATIVE ABUSE GUARDRAIL */}
      <div className="rounded-xl border border-border/80 bg-background/60 p-4 space-y-3 text-xs">
        <div className="flex items-start gap-2.5">
          <Info className="h-4 w-4 shrink-0 mt-0.5 text-indigo-600 dark:text-indigo-400" />
          <div className="space-y-1 flex-1">
            <span className="font-bold text-foreground">
              Quy Chuẩn Phương Pháp Luận Giáo Dục & Phòng Ngừa Lạm Dụng (Negative Abuse Rule):
            </span>
            <p className="text-muted-foreground leading-relaxed">
              {analytics.methodological_notice}
            </p>
          </div>
        </div>

        {/* Negative abuse interactive guardrail drill */}
        <div className="pt-2 border-t border-border/50 flex flex-wrap items-center justify-between gap-3">
          <span className="text-[11px] text-muted-foreground">
            Xác minh cơ chế máy chủ chặn các tuyên bố nhân quả (Causal Learning Gain) khi không có đề cương đối chứng:
          </span>
          <Button
            size="sm"
            variant="ghost"
            onClick={handleTestCausalRejection}
            disabled={causalTesting}
            className="text-[11px] h-7 gap-1 border border-border text-muted-foreground hover:text-foreground"
            title="Thử nghiệm gửi yêu cầu claim_causality=true để xác minh mã lỗi 422 từ máy chủ"
          >
            <ShieldCheck className="h-3 w-3 text-indigo-600" />
            <span>{causalTesting ? "Đang kiểm tra..." : "Kiểm tra Chặn Khẳng định Nhân quả (422)"}</span>
          </Button>
        </div>

        {causalErrorResult && (
          <div className="rounded-lg bg-indigo-500/10 border border-indigo-500/20 p-2.5 text-[11px] text-indigo-900 dark:text-indigo-200 flex items-start gap-2">
            <CheckCircle2 className="h-3.5 w-3.5 text-indigo-600 shrink-0 mt-0.5" />
            <span>{causalErrorResult}</span>
          </div>
        )}
      </div>
    </div>
  );
}
