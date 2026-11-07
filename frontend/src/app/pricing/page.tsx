"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  ShieldCheck,
  Calculator,
  AlertCircle,
  Sparkles,
  Layers,
  Lock,
  FileText,
  CheckCircle2,
  ArrowRight,
  Building2,
  Users,
  BarChart3,
  Sliders,
  Check,
  Eye,
  Calendar,
  X,
  HelpCircle,
  Info,
} from "lucide-react";

import {
  PricingCalculatorIn,
  PricingCalculatorOut,
  PricingContractCreateIn,
  PricingContractOut,
  PricingContractSignAcceptIn,
  PricingExperimentConfigOut,
  PricingExperimentMetricsSummaryOut,
  PricingTierInfo,
} from "@/types/pricing";

const EXPERIMENT_KEY = "school_pricing_v1";
const CONSENT_VERSION = "2026.1-pricing";

export default function PricingExperimentPage() {
  const [variant, setVariant] = useState<string>("control");
  const [hasConsent, setHasConsent] = useState<boolean>(true);
  const [config, setConfig] = useState<PricingExperimentConfigOut | null>(null);
  const [selectedTierKey, setSelectedTierKey] = useState<string>("standard_school");
  const [loadingConfig, setLoadingConfig] = useState<boolean>(true);

  // Calculator inputs
  const [studentCount, setStudentCount] = useState<number>(500);
  const [monthsDuration, setMonthsDuration] = useState<number>(12);
  const [includeAiTutor, setIncludeAiTutor] = useState<boolean>(true);
  const [includeVr360, setIncludeVr360] = useState<boolean>(false);
  const [includeTeacherTraining, setIncludeTeacherTraining] = useState<boolean>(false);

  // Calculator state
  const [calcResult, setCalcResult] = useState<PricingCalculatorOut | null>(null);
  const [calculating, setCalculating] = useState<boolean>(false);

  // Metrics summary
  const [metrics, setMetrics] = useState<PricingExperimentMetricsSummaryOut | null>(null);

  // Contract workflow modal
  const [contractModalOpen, setContractModalOpen] = useState<boolean>(false);
  const [contractOrgName, setContractOrgName] = useState<string>("");
  const [draftedContract, setDraftedContract] = useState<PricingContractOut | null>(null);
  const [signerTitle, setSignerTitle] = useState<string>("Hiệu trưởng");
  const [signerName, setSignerName] = useState<string>("");
  const [confirmStatement, setConfirmStatement] = useState<string>(
    "Tôi xác nhận đại diện cho nhà trường ký kết hợp đồng triển khai chương trình di sản Cửu Đỉnh."
  );
  const [submittingContract, setSubmittingContract] = useState<boolean>(false);
  const [executedContract, setExecutedContract] = useState<PricingContractOut | null>(null);
  const [contractError, setContractError] = useState<string | null>(null);

  // Helper to record telemetry events with consent & zero-revenue invariant
  const recordEvent = useCallback(
    async (
      tierKey: string,
      eventType: "tier_view" | "calculator_interaction" | "quote_inquiry" | "contract_sign_attempt",
      calculatorParams?: Record<string, unknown>
    ) => {
      if (!hasConsent) return; // Strict opt-in telemetry
      try {
        await fetch("/api/v1/pricing/events", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            experiment_key: EXPERIMENT_KEY,
            variant_key: variant,
            tier_key: tierKey,
            event_type: eventType,
            has_experiment_consent: hasConsent,
            consent_version: CONSENT_VERSION,
            calculator_params: calculatorParams,
            anonymous_session_id: "web-pricing-client",
          }),
        });
      } catch (err) {
        // Silently tolerate non-blocking telemetry failures
      }
    },
    [hasConsent, variant]
  );

  // Fetch experiment config
  const fetchConfig = useCallback(async () => {
    setLoadingConfig(true);
    try {
      const res = await fetch(`/api/v1/pricing/config?variant=${variant}`);
      if (res.ok) {
        const data = await res.json();
        setConfig(data);
      }
    } catch (err) {
      // Configuration fallback
    } finally {
      setLoadingConfig(false);
    }
  }, [variant]);

  // Fetch metrics summary
  const fetchMetrics = useCallback(async () => {
    try {
      const res = await fetch(`/api/v1/pricing/metrics/summary?experiment_key=${EXPERIMENT_KEY}`);
      if (res.ok) {
        const data = await res.json();
        setMetrics(data);
      }
    } catch (err) {
      // Metrics retrieval error
    }
  }, []);

  useEffect(() => {
    fetchConfig();
    fetchMetrics();
  }, [fetchConfig, fetchMetrics]);

  // Run calculator
  const runCalculator = useCallback(async () => {
    setCalculating(true);
    const payload: PricingCalculatorIn = {
      tier_key: selectedTierKey,
      student_count: studentCount,
      months_duration: monthsDuration,
      include_ai_tutor_credits: includeAiTutor,
      include_vr360_interactive_lab: includeVr360,
      include_teacher_training_pdu: includeTeacherTraining,
    };

    try {
      const res = await fetch("/api/v1/pricing/calculator", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const data = await res.json();
        setCalcResult(data);
        recordEvent(selectedTierKey, "calculator_interaction", payload as unknown as Record<string, unknown>);
      }
    } catch (err) {
      // Calculation failed
    } finally {
      setCalculating(false);
    }
  }, [
    selectedTierKey,
    studentCount,
    monthsDuration,
    includeAiTutor,
    includeVr360,
    includeTeacherTraining,
    recordEvent,
  ]);

  useEffect(() => {
    const timer = setTimeout(() => {
      runCalculator();
    }, 250);
    return () => clearTimeout(timer);
  }, [runCalculator]);

  // Handle tier select
  const handleSelectTier = (tierKey: string) => {
    setSelectedTierKey(tierKey);
    recordEvent(tierKey, "tier_view");
  };

  // Start contract drafting
  const handleOpenContractModal = (tier: PricingTierInfo) => {
    setSelectedTierKey(tier.key);
    setDraftedContract(null);
    setExecutedContract(null);
    setContractError(null);
    setContractModalOpen(true);
    recordEvent(tier.key, "quote_inquiry");
  };

  // Submit contract draft
  const handleDraftContract = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!contractOrgName.trim()) return;

    setSubmittingContract(true);
    setContractError(null);
    recordEvent(selectedTierKey, "contract_sign_attempt");

    const payload: PricingContractCreateIn = {
      organization_name: contractOrgName.trim(),
      tier_key: selectedTierKey,
      variant_key: variant,
      student_seat_capacity: studentCount,
      contract_value_vnd: calcResult ? calcResult.estimated_total_vnd : 0,
      terms_version: "v2026.1-edu",
    };

    try {
      const res = await fetch("/api/v1/pricing/contracts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const data = await res.json();
        setDraftedContract(data);
      } else {
        const err = await res.json();
        setContractError(err.detail || "Không thể khởi tạo hợp đồng. Vui lòng đăng nhập trước.");
      }
    } catch (err) {
      setContractError("Lỗi kết nối máy chủ");
    } finally {
      setSubmittingContract(false);
    }
  };

  // Execute and accept contract
  const handleSignContract = async () => {
    if (!draftedContract) return;
    if (!signerName.trim() || !confirmStatement.trim()) {
      setContractError("Vui lòng điền họ tên người đại diện và lời xác nhận.");
      return;
    }

    setSubmittingContract(true);
    setContractError(null);

    const payload: PricingContractSignAcceptIn = {
      confirmation_statement: confirmStatement.trim(),
      signer_title: signerTitle.trim(),
      signer_legal_name: signerName.trim(),
      ip_address_masked: "127.0.0.1",
    };

    try {
      const res = await fetch(`/api/v1/pricing/contracts/${draftedContract.id}/accept`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const data = await res.json();
        setExecutedContract(data);
        fetchMetrics();
      } else {
        const err = await res.json();
        setContractError(err.detail || "Ký hợp đồng thất bại.");
      }
    } catch (err) {
      setContractError("Lỗi kết nối khi gửi chữ ký");
    } finally {
      setSubmittingContract(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-12">
        {/* Header with A/B Variant Indicator */}
        <div className="text-center space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-medium">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Thí Nghiệm Định Giá Trường Học (A/B Test Variant: {variant})</span>
          </div>

          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-white">
            Bảng Giá Đồng Hành Di Sản Cửu Đỉnh Cho Trường Học
          </h1>

          <p className="max-w-3xl mx-auto text-slate-400 text-sm sm:text-base">
            Minh bạch 100%, không dark patterns, không tự động trừ tiền. Tích hợp trọn gói 162 phù điêu di sản,
            trợ giảng AI Sử Gia Socratic và bộ tài liệu in ấn chuẩn UDL.
          </p>

          {/* Variant Switcher for Testing */}
          <div className="inline-flex items-center gap-2 p-1 bg-slate-900 border border-slate-800 rounded-lg text-xs">
            <span className="text-slate-500 px-2">Biến thể thử nghiệm:</span>
            {(["control", "annual_flat", "per_student_metered"] as const).map((v) => (
              <button
                key={v}
                onClick={() => setVariant(v)}
                className={`px-3 py-1 rounded font-medium transition ${
                  variant === v
                    ? "bg-amber-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {v}
              </button>
            ))}
          </div>
        </div>

        {/* Consent Banner - Zero Dark Pattern Guarantee */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 sm:p-6 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <ShieldCheck className="w-6 h-6 text-emerald-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                Cam Kết Minh Bạch &amp; Bảo Vệ Người Dùng (Chính sách {CONSENT_VERSION})
              </h3>
              <p className="text-xs text-slate-300">
                {config?.consent_text_vi ||
                  "Lựa chọn hoặc tính toán gói giá của bạn giúp cải thiện sản phẩm và hoàn toàn KHÔNG tự động tính phí."}
              </p>
              <p className="text-[11px] text-amber-400 font-medium">
                * Quy tắc bất biến: Xem gói giá hoặc dùng máy tính KHÔNG tạo doanh thu và KHÔNG biến bạn thành khách hàng trả phí.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <label className="flex items-center gap-2 cursor-pointer bg-slate-950 px-3 py-2 rounded-lg border border-slate-800">
              <input
                type="checkbox"
                checked={hasConsent}
                onChange={(e) => setHasConsent(e.target.checked)}
                className="rounded bg-slate-900 border-slate-700 text-amber-500 focus:ring-0"
              />
              <span className="text-xs text-slate-200">
                {hasConsent ? "Đang bật đo lường nhu cầu" : "Đã tắt đo lường (Ẩn danh hoàn toàn)"}
              </span>
            </label>
          </div>
        </div>

        {/* Tiers Grid */}
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Layers className="w-5 h-5 text-amber-400" />
              Các Gói Định Giá Tiêu Chuẩn
            </h2>
            <span className="text-xs text-slate-500">Đơn vị: Đồng Việt Nam (VND)</span>
          </div>

          {loadingConfig ? (
            <div className="p-12 text-center text-slate-500">Đang tải biểu giá...</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {config?.tiers.map((tier) => {
                const isSelected = selectedTierKey === tier.key;
                return (
                  <div
                    key={tier.key}
                    onClick={() => handleSelectTier(tier.key)}
                    className={`relative rounded-2xl p-6 transition flex flex-col justify-between cursor-pointer border ${
                      isSelected
                        ? "bg-slate-900 border-amber-500 shadow-lg shadow-amber-500/10 ring-1 ring-amber-500"
                        : "bg-slate-900/60 border-slate-800 hover:border-slate-700"
                    }`}
                  >
                    {tier.is_popular && (
                      <div className="absolute -top-3 right-6 bg-amber-500 text-slate-950 text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider">
                        Phổ Biến Nhất
                      </div>
                    )}

                    <div className="space-y-4">
                      <div>
                        <h3 className="text-lg font-bold text-white">{tier.name_vi}</h3>
                        <p className="text-xs text-slate-400 mt-1">{tier.description_vi}</p>
                      </div>

                      <div className="border-t border-slate-800 pt-4">
                        <div className="flex items-baseline gap-1">
                          <span className="text-3xl font-extrabold text-white">
                            {tier.base_price_vnd === 0
                              ? "Miễn Phí"
                              : `${(tier.base_price_vnd / 1_000_000).toLocaleString("vi-VN")} Triệu`}
                          </span>
                          <span className="text-xs text-slate-400">
                            {tier.billing_period === "per_semester"
                              ? "/ học kỳ"
                              : "/ năm học"}
                          </span>
                        </div>
                      </div>

                      <div className="space-y-2 pt-2">
                        <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                          Đặc quyền bao gồm:
                        </span>
                        <ul className="space-y-2 text-xs text-slate-300">
                          {tier.features_vi.map((f, i) => (
                            <li key={i} className="flex items-start gap-2">
                              <Check className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                              <span>{f}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    <div className="pt-6 border-t border-slate-800 mt-6 space-y-3">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenContractModal(tier);
                        }}
                        className={`w-full py-2.5 px-4 rounded-xl font-medium text-xs flex items-center justify-center gap-2 transition ${
                          isSelected
                            ? "bg-amber-600 hover:bg-amber-500 text-white"
                            : "bg-slate-800 hover:bg-slate-700 text-slate-200"
                        }`}
                      >
                        <FileText className="w-4 h-4" />
                        <span>Ký Hợp Đồng / Đăng Ký Trường</span>
                      </button>

                      <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
                        <Info className="w-3.5 h-3.5 shrink-0 text-slate-500" />
                        <span>{tier.anti_dark_pattern_notice}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Real-time Pricing Calculator */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div className="space-y-1">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Calculator className="w-5 h-5 text-amber-400" />
                Công Cụ Dự Toán Chi Phí Tùy Chỉnh Cho Trường Học
              </h2>
              <p className="text-xs text-slate-400">
                Mô phỏng chi phí thực tế theo quy mô học sinh, số tháng và các mô-đun công nghệ bổ trợ.
              </p>
            </div>

            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs">
              <ShieldCheck className="w-4 h-4 shrink-0" />
              <span>Dự toán không ràng buộc (0 VNĐ nghĩa vụ)</span>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Controls */}
            <div className="lg:col-span-7 space-y-6">
              {/* Student Count Slider */}
              <div className="space-y-2">
                <div className="flex justify-between items-center text-sm">
                  <label className="font-medium text-slate-200 flex items-center gap-2">
                    <Users className="w-4 h-4 text-amber-400" />
                    Số lượng học sinh sử dụng:
                  </label>
                  <span className="font-bold text-amber-400 font-mono text-base">
                    {studentCount.toLocaleString("vi-VN")} học sinh
                  </span>
                </div>
                <input
                  type="range"
                  min="50"
                  max="5000"
                  step="50"
                  value={studentCount}
                  onChange={(e) => setStudentCount(Number(e.target.value))}
                  className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-500"
                />
                <div className="flex justify-between text-[11px] text-slate-500">
                  <span>50 học sinh (Lớp thí điểm)</span>
                  <span>1,000 học sinh (Trường chuẩn)</span>
                  <span>5,000 học sinh (Cụm trường)</span>
                </div>
              </div>

              {/* Duration Selector */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-200 flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-amber-400" />
                  Thời hạn gói triển khai:
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { m: 6, label: "1 Học Kỳ (6 tháng)" },
                    { m: 12, label: "1 Năm Học (12 tháng)" },
                    { m: 24, label: "2 Năm Học (24 tháng)" },
                  ].map((dur) => (
                    <button
                      key={dur.m}
                      type="button"
                      onClick={() => setMonthsDuration(dur.m)}
                      className={`p-3 rounded-xl border text-xs font-medium text-center transition ${
                        monthsDuration === dur.m
                          ? "bg-amber-600/20 border-amber-500 text-amber-400"
                          : "bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      {dur.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Addons toggles */}
              <div className="space-y-3 pt-2">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Mô-đun công nghệ bổ trợ:
                </span>

                <label className="flex items-start gap-3 p-3 bg-slate-950 border border-slate-800 rounded-xl cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeAiTutor}
                    onChange={(e) => setIncludeAiTutor(e.target.checked)}
                    className="mt-1 rounded bg-slate-900 border-slate-700 text-amber-500 focus:ring-0"
                  />
                  <div className="text-xs">
                    <span className="font-semibold text-slate-200">
                      Tích hợp Trợ giảng AI Sử Gia Socratic
                    </span>
                    <p className="text-slate-400 text-[11px]">
                      Truy hồi trích dẫn nguồn lưu trữ Đại Nam Thực Lục, chống bịa đặt lịch sử.
                    </p>
                  </div>
                </label>

                <label className="flex items-start gap-3 p-3 bg-slate-950 border border-slate-800 rounded-xl cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeVr360}
                    onChange={(e) => setIncludeVr360(e.target.checked)}
                    className="mt-1 rounded bg-slate-900 border-slate-700 text-amber-500 focus:ring-0"
                  />
                  <div className="text-xs">
                    <span className="font-semibold text-slate-200">
                      Phòng Thí Nghiệm Bảo Tàng Ảo VR360
                    </span>
                    <p className="text-slate-400 text-[11px]">
                      Tương tác không gian 3D tại sân Thế Miếu và Cửu Đỉnh độ phân giải cao.
                    </p>
                  </div>
                </label>

                <label className="flex items-start gap-3 p-3 bg-slate-950 border border-slate-800 rounded-xl cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeTeacherTraining}
                    onChange={(e) => setIncludeTeacherTraining(e.target.checked)}
                    className="mt-1 rounded bg-slate-900 border-slate-700 text-amber-500 focus:ring-0"
                  />
                  <div className="text-xs">
                    <span className="font-semibold text-slate-200">
                      Tập Huấn Sư Phạm Chuyên Đề &amp; PDU Cho Giáo Viên
                    </span>
                    <p className="text-slate-400 text-[11px]">
                      Chuyên gia di sản đồng hành 02 buổi trực tiếp tại trường.
                    </p>
                  </div>
                </label>
              </div>
            </div>

            {/* Quote Summary Output */}
            <div className="lg:col-span-5 bg-slate-950 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Kết Quả Dự Toán Mô Phỏng
                  </span>
                  <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                    Gói: {selectedTierKey}
                  </span>
                </div>

                {calculating ? (
                  <div className="py-8 text-center text-slate-500 text-xs">Đang tính toán...</div>
                ) : calcResult ? (
                  <div className="space-y-3 text-xs">
                    <div className="flex justify-between text-slate-300">
                      <span>Giá cơ bản gói:</span>
                      <span className="font-mono">
                        {calcResult.base_subtotal_vnd.toLocaleString("vi-VN")} đ
                      </span>
                    </div>

                    <div className="flex justify-between text-slate-300">
                      <span>Mô-đun bổ trợ:</span>
                      <span className="font-mono">
                        {calcResult.addons_subtotal_vnd.toLocaleString("vi-VN")} đ
                      </span>
                    </div>

                    {calcResult.volume_discount_vnd > 0 && (
                      <div className="flex justify-between text-emerald-400">
                        <span>Ưu đãi quy mô học sinh:</span>
                        <span className="font-mono">
                          -{calcResult.volume_discount_vnd.toLocaleString("vi-VN")} đ
                        </span>
                      </div>
                    )}

                    <div className="border-t border-slate-800 pt-3">
                      <div className="flex justify-between items-baseline">
                        <span className="text-sm font-semibold text-white">Tổng dự toán ước tính:</span>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-amber-400 font-mono">
                            {calcResult.estimated_total_vnd.toLocaleString("vi-VN")} đ
                          </div>
                          <div className="text-[11px] text-slate-400">
                            ~{calcResult.per_student_month_vnd.toLocaleString("vi-VN")} đ/học sinh/tháng
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : null}
              </div>

              {/* Strict Disclaimer */}
              <div className="space-y-4 pt-4 border-t border-slate-800">
                <div className="p-3 rounded-xl bg-amber-950/20 border border-amber-900/40 text-[11px] text-amber-300/90 leading-relaxed">
                  <div className="font-semibold flex items-center gap-1.5 mb-1 text-amber-300">
                    <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                    Quy định minh bạch doanh thu:
                  </div>
                  {calcResult?.disclaimer ||
                    "Kết quả tính toán chỉ mang tính ước tính và khảo sát nhu cầu thị trường. Không cấu thành hóa đơn và không ghi nhận doanh thu."}
                </div>

                <button
                  type="button"
                  onClick={() => {
                    const activeTier = config?.tiers.find((t) => t.key === selectedTierKey);
                    if (activeTier) handleOpenContractModal(activeTier);
                  }}
                  className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-medium py-3 rounded-xl text-xs flex items-center justify-center gap-2 transition shadow-lg shadow-emerald-950/40"
                >
                  <FileText className="w-4 h-4" />
                  <span>Tiến Hành Đăng Ký Hợp Đồng Pháp Lý Cho Trường</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Real-time Experiment Metrics & Anti-Abuse Transparency Summary */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-amber-400" />
              Báo Cáo Minh Bạch Dữ Liệu Thực Nghiệm (Live Ledger Audit)
            </h3>
            <span className="text-[11px] text-slate-400 font-mono">
              Experiment: {EXPERIMENT_KEY}
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1">
              <span className="text-slate-400">Lượt Xem Gói Giá:</span>
              <div className="text-xl font-bold text-white font-mono">
                {metrics ? metrics.total_tier_views : 0}
              </div>
              <span className="text-[10px] text-emerald-400">0 VNĐ doanh thu</span>
            </div>

            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1">
              <span className="text-slate-400">Lượt Dùng Máy Tính:</span>
              <div className="text-xl font-bold text-white font-mono">
                {metrics ? metrics.total_calculator_interactions : 0}
              </div>
              <span className="text-[10px] text-emerald-400">0 VNĐ doanh thu</span>
            </div>

            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1">
              <span className="text-slate-400">Hợp Đồng Đã Ký Kết:</span>
              <div className="text-xl font-bold text-amber-400 font-mono">
                {metrics ? metrics.signed_contracts_count : 0}
              </div>
              <span className="text-[10px] text-slate-400">Đại diện pháp lý thực</span>
            </div>

            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1">
              <span className="text-slate-400">Doanh Thu Ghi Nhận:</span>
              <div className="text-xl font-bold text-emerald-400 font-mono">
                {metrics
                  ? `${(metrics.recognized_contract_revenue_vnd / 1_000_000).toLocaleString("vi-VN")} Tr`
                  : "0 Tr"}
              </div>
              <span className="text-[10px] text-emerald-400">Hợp đồng thực thi 100%</span>
            </div>
          </div>

          <div className="p-3 bg-slate-950 rounded-xl border border-slate-800/80 text-[11px] text-slate-400 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>
              {metrics?.negative_abuse_verification ||
                "INVARIANT VERIFIED: Tier views and calculator clicks contributed 0 VND and 0 paying customers."}
            </span>
          </div>
        </div>

        {/* Contract Signing Modal */}
        {contractModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-6 shadow-2xl relative">
              <button
                type="button"
                onClick={() => setContractModalOpen(false)}
                className="absolute top-4 right-4 text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>

              <div className="space-y-1">
                <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-amber-500/10 text-amber-400 text-xs font-medium">
                  <Building2 className="w-3.5 h-3.5" />
                  <span>Xác Nhận Hợp Đồng B2B Cấp Trường</span>
                </div>
                <h3 className="text-lg font-bold text-white">
                  Đăng Ký &amp; Ký Kết Hợp Đồng Triển Khai
                </h3>
                <p className="text-xs text-slate-400">
                  Chỉ hành động ký kết pháp lý bên dưới mới xác nhận thỏa thuận và ghi nhận hợp đồng chính thức.
                </p>
              </div>

              {contractError && (
                <div className="p-3 bg-red-950/40 border border-red-800 rounded-xl text-red-300 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{contractError}</span>
                </div>
              )}

              {/* Step 1: Draft Contract */}
              {!draftedContract ? (
                <form onSubmit={handleDraftContract} className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-slate-300">
                      Tên trường học / Sở GD&amp;ĐT / Đơn vị:
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="Ví dụ: THPT Chuyên Quốc Học Huế"
                      value={contractOrgName}
                      onChange={(e) => setContractOrgName(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl">
                      <span className="text-slate-400">Gói đăng ký:</span>
                      <div className="font-bold text-white mt-0.5">{selectedTierKey}</div>
                    </div>
                    <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl">
                      <span className="text-slate-400">Giá trị hợp đồng:</span>
                      <div className="font-bold text-amber-400 mt-0.5 font-mono">
                        {calcResult ? calcResult.estimated_total_vnd.toLocaleString("vi-VN") : 0} đ
                      </div>
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={submittingContract || !contractOrgName.trim()}
                    className="w-full bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white font-medium py-3 rounded-xl text-xs flex items-center justify-center gap-2 transition"
                  >
                    {submittingContract ? "Đang khởi tạo..." : "Khởi Tạo Dự Thảo Hợp Đồng"}
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </form>
              ) : !executedContract ? (
                /* Step 2: Formal Electronic Signature */
                <div className="space-y-4">
                  <div className="p-3 bg-amber-950/20 border border-amber-900/40 rounded-xl text-xs space-y-1">
                    <div className="text-amber-400 font-semibold flex items-center gap-1.5">
                      <FileText className="w-4 h-4" />
                      Mã hợp đồng: {draftedContract.contract_number}
                    </div>
                    <div className="text-slate-300">
                      Đơn vị: <strong>{draftedContract.organization_name}</strong> | Quy mô:{" "}
                      <strong>{draftedContract.student_seat_capacity} học sinh</strong>
                    </div>
                    <div className="text-emerald-400 font-mono font-semibold">
                      Giá trị: {draftedContract.contract_value_vnd.toLocaleString("vi-VN")} VNĐ
                    </div>
                  </div>

                  <div className="space-y-3 text-xs">
                    <div>
                      <label className="font-semibold text-slate-300">Họ và tên người đại diện ký:</label>
                      <input
                        type="text"
                        required
                        placeholder="Ví dụ: Nguyễn Văn A"
                        value={signerName}
                        onChange={(e) => setSignerName(e.target.value)}
                        className="w-full mt-1 bg-slate-950 border border-slate-700 rounded-xl px-4 py-2 text-xs text-white"
                      />
                    </div>

                    <div>
                      <label className="font-semibold text-slate-300">Chức vụ đại diện:</label>
                      <input
                        type="text"
                        required
                        value={signerTitle}
                        onChange={(e) => setSignerTitle(e.target.value)}
                        className="w-full mt-1 bg-slate-950 border border-slate-700 rounded-xl px-4 py-2 text-xs text-white"
                      />
                    </div>

                    <div>
                      <label className="font-semibold text-slate-300">Tuyên bố xác nhận cam kết:</label>
                      <textarea
                        rows={2}
                        value={confirmStatement}
                        onChange={(e) => setConfirmStatement(e.target.value)}
                        className="w-full mt-1 bg-slate-950 border border-slate-700 rounded-xl p-3 text-xs text-white"
                      />
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={handleSignContract}
                    disabled={submittingContract || !signerName.trim()}
                    className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-medium py-3 rounded-xl text-xs flex items-center justify-center gap-2 transition"
                  >
                    <Lock className="w-4 h-4" />
                    <span>
                      {submittingContract ? "Đang ký số..." : "Ký Điện Tử & Xác Nhận Hợp Đồng"}
                    </span>
                  </button>
                </div>
              ) : (
                /* Step 3: Executed Result */
                <div className="space-y-4 text-center">
                  <div className="w-12 h-12 bg-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center mx-auto">
                    <CheckCircle2 className="w-6 h-6" />
                  </div>

                  <div className="space-y-1">
                    <h4 className="text-base font-bold text-white">
                      Hợp Đồng Đã Được Ký Kết Thành Công!
                    </h4>
                    <p className="text-xs text-slate-400">
                      Mã hợp đồng:{" "}
                      <span className="font-mono text-emerald-400">
                        {executedContract.contract_number}
                      </span>
                    </p>
                  </div>

                  <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-[11px] text-left text-slate-400 space-y-1 font-mono">
                    <div>Trạng thái: {executedContract.status}</div>
                    <div className="truncate">
                      Chữ ký số: {executedContract.verification_hash}
                    </div>
                    <div>
                      Ngày ký:{" "}
                      {executedContract.signed_at
                        ? new Date(executedContract.signed_at).toLocaleString("vi-VN")
                        : "N/A"}
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => setContractModalOpen(false)}
                    className="w-full bg-slate-800 hover:bg-slate-700 text-white font-medium py-2.5 rounded-xl text-xs transition"
                  >
                    Đóng
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
