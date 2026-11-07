"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  ShieldAlert,
  Key,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Activity,
  Send,
  Sparkles,
  School,
  Building2,
  ArrowRight,
  ListChecks,
  Check,
  LifeBuoy,
} from "lucide-react";

interface ValidationResult {
  is_valid: boolean;
  status: string;
  message: string;
  invitation_code?: string;
  pilot_name?: string;
  target_role?: string;
  organization_name?: string;
  expires_at?: string;
}

interface ActivationData {
  id: string;
  role_type: string;
  organization_name: string;
  status: string;
  current_step: string;
  completed_steps: string[];
  compliance_accepted: boolean;
  pilot_name?: string;
}

interface HealthData {
  health_score: number;
  health_status: string;
  login_count: number;
  actions_count: number;
  last_action_name?: string;
}

export default function PilotOnboardingPortal() {
  const [tokenInput, setTokenInput] = useState("");
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [complianceAccepted, setComplianceAccepted] = useState(false);

  const [activating, setActivating] = useState(false);
  const [activation, setActivation] = useState<ActivationData | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [health, setHealth] = useState<HealthData | null>(null);
  const [activeTab, setActiveTab] = useState<"checklist" | "health" | "support">("checklist");

  // Support ticket form
  const [supportSubject, setSupportSubject] = useState("");
  const [supportCategory, setSupportCategory] = useState("onboarding_help");
  const [supportMessage, setSupportMessage] = useState("");
  const [supportSubmitted, setSupportSubmitted] = useState(false);

  // Check for existing activation on mount
  useEffect(() => {
    async function fetchMyActivation() {
      try {
        const res = await fetch("/api/v1/pilot/my-activation");
        if (res.ok) {
          const data = await res.json();
          setActivation(data);
          fetchHealth();
        }
      } catch (err) {
        // Not activated yet or unauthenticated
      }
    }
    fetchMyActivation();
  }, []);

  async function fetchHealth() {
    try {
      const res = await fetch("/api/v1/pilot/health");
      if (res.ok) {
        const data = await res.json();
        setHealth(data);
      }
    } catch (err) {
      // Telemetry not available
    }
  }

  async function handleValidateToken(e: React.FormEvent) {
    e.preventDefault();
    if (!tokenInput.trim()) return;

    setValidating(true);
    setErrorMsg(null);
    setValidationResult(null);

    try {
      const res = await fetch("/api/v1/pilot/invitations/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: tokenInput.trim() }),
      });
      const data = await res.json();
      setValidationResult(data);
      if (!data.is_valid) {
        setErrorMsg(data.message || "Mã thư mời không hợp lệ.");
      }
    } catch (err) {
      setErrorMsg("Không thể kết nối đến máy chủ xác thực thư mời.");
    } finally {
      setValidating(false);
    }
  }

  async function handleActivate() {
    if (!tokenInput.trim() || !complianceAccepted) return;

    setActivating(true);
    setErrorMsg(null);

    try {
      const res = await fetch("/api/v1/pilot/activate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token: tokenInput.trim(),
          compliance_accepted: complianceAccepted,
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || errData.error?.message || "Kích hoạt thất bại.");
      }

      const data = await res.json();
      setActivation(data);
      fetchHealth();
    } catch (err: any) {
      setErrorMsg(err.message || "Đã xảy ra lỗi khi kích hoạt thử nghiệm.");
    } finally {
      setActivating(false);
    }
  }

  async function handleCompleteStep(stepKey: string) {
    try {
      const res = await fetch("/api/v1/pilot/onboarding/step", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: stepKey, completed: true }),
      });
      if (res.ok) {
        const data = await res.json();
        setActivation(data);
        fetchHealth();
      }
    } catch (err) {
      // Step sync error
    }
  }

  async function handleCreateSupport(e: React.FormEvent) {
    e.preventDefault();
    if (!supportSubject || !supportMessage) return;

    try {
      const res = await fetch("/api/v1/pilot/support", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          category: supportCategory,
          priority: "normal",
          subject: supportSubject,
          message: supportMessage,
        }),
      });
      if (res.ok) {
        setSupportSubmitted(true);
        setSupportSubject("");
        setSupportMessage("");
      }
    } catch (err) {
      // Ticket submission error
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-12 font-sans">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <header className="border-b border-slate-800 pb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm uppercase tracking-wider">
              <Sparkles className="w-4 h-4" />
              <span>Cổng Thử Nghiệm Thí Điểm (Pilot Onboarding)</span>
            </div>
            <h1 className="text-3xl font-bold mt-1 text-white">
              Kích Hoạt & Đồng Hành Pilot Dự Án Lưu Niên
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Dành riêng cho đối tác giáo dục THPT/THCS và các cơ sở làng nghề di sản được cấp quyền.
            </p>
          </div>
          {activation && (
            <div className="flex items-center gap-3 bg-slate-900 border border-slate-800 px-4 py-2 rounded-lg">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              <div>
                <div className="text-xs text-slate-400">Đơn vị tham gia</div>
                <div className="text-sm font-medium text-white">{activation.organization_name}</div>
              </div>
            </div>
          )}
        </header>

        {/* Phase 1: Invitation Token Gate (if not activated) */}
        {!activation ? (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 space-y-6">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-amber-500/10 text-amber-400 rounded-lg">
                <Key className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-white">Xác Thực Mã Mời Thử Nghiệm</h2>
                <p className="text-slate-400 text-sm mt-1">
                  Chương trình thử nghiệm thí điểm có kiểm soát chất lượng và cam kết tuân thủ quy chuẩn đạo đức nghiên cứu. Vui lòng nhập mã token từ thư mời chính thức.
                </p>
              </div>
            </div>

            <form onSubmit={handleValidateToken} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Mã Token Thư Mời (Invitation Secret Token)
                </label>
                <div className="flex gap-3">
                  <input
                    type="text"
                    value={tokenInput}
                    onChange={(e) => setTokenInput(e.target.value)}
                    placeholder="ln_pilot_..."
                    className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white font-mono text-sm focus:outline-none focus:border-amber-500"
                  />
                  <button
                    type="submit"
                    disabled={validating || !tokenInput.trim()}
                    className="bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white px-5 py-2 rounded-lg font-medium text-sm transition"
                  >
                    {validating ? "Đang kiểm tra..." : "Kiểm tra mã"}
                  </button>
                </div>
              </div>
            </form>

            {errorMsg && (
              <div className="flex items-center gap-2 p-4 bg-red-950/40 border border-red-800 rounded-lg text-red-200 text-sm">
                <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
                <span>{errorMsg}</span>
              </div>
            )}

            {validationResult && validationResult.is_valid && (
              <div className="space-y-4 border border-emerald-900/60 bg-emerald-950/20 rounded-xl p-6">
                <div className="flex items-center gap-2 text-emerald-400 font-semibold">
                  <CheckCircle2 className="w-5 h-5" />
                  <span>Thư mời hợp lệ: {validationResult.pilot_name}</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-slate-300">
                  <div>
                    <span className="text-slate-500">Đơn vị: </span>
                    <strong className="text-white">{validationResult.organization_name}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500">Vai trò cấp quyền: </span>
                    <strong className="text-white">
                      {validationResult.target_role === "school_teacher"
                        ? "Giáo viên trường học"
                        : "Nghệ nhân / Đối tác di sản"}
                    </strong>
                  </div>
                </div>

                <div className="border-t border-slate-800 pt-4 space-y-3">
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={complianceAccepted}
                      onChange={(e) => setComplianceAccepted(e.target.checked)}
                      className="mt-1 rounded bg-slate-950 border-slate-700 text-amber-500 focus:ring-0"
                    />
                    <span className="text-xs text-slate-300">
                      Tôi xác nhận đã đọc, hiểu và đồng ý tuân thủ Khung Đạo đức Nghiên cứu Thí điểm &amp; Nghị định 13/2023/NĐ-CP về Bảo vệ dữ liệu cá nhân học sinh / nghệ nhân.
                    </span>
                  </label>

                  <button
                    onClick={handleActivate}
                    disabled={activating || !complianceAccepted}
                    className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-medium py-3 rounded-lg flex items-center justify-center gap-2 transition"
                  >
                    {activating ? "Đang kích hoạt..." : "Xác nhận & Kích Hoạt Quyền Thử Nghiệm"}
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Phase 2: Active Pilot Management Dashboard */
          <div className="space-y-6">
            {/* Tabs */}
            <div className="flex border-b border-slate-800 gap-4">
              <button
                onClick={() => setActiveTab("checklist")}
                className={`pb-3 text-sm font-medium border-b-2 flex items-center gap-2 transition ${
                  activeTab === "checklist"
                    ? "border-amber-500 text-amber-400"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                <ListChecks className="w-4 h-4" />
                Lộ Trình Kích Hoạt ({activation.completed_steps.length} bước)
              </button>
              <button
                onClick={() => setActiveTab("health")}
                className={`pb-3 text-sm font-medium border-b-2 flex items-center gap-2 transition ${
                  activeTab === "health"
                    ? "border-amber-500 text-amber-400"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                <Activity className="w-4 h-4" />
                Sức Khỏe Sử Dụng &amp; Telemetry
              </button>
              <button
                onClick={() => setActiveTab("support")}
                className={`pb-3 text-sm font-medium border-b-2 flex items-center gap-2 transition ${
                  activeTab === "support"
                    ? "border-amber-500 text-amber-400"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                <LifeBuoy className="w-4 h-4" />
                Hỗ Trợ &amp; Góp Ý Chuyên Môn
              </button>
            </div>

            {/* Tab 1: Checklist */}
            {activeTab === "checklist" && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
                <h3 className="text-lg font-semibold text-white">
                  Danh Mục Khởi Động Pilot ({activation.role_type === "school_teacher" ? "Giáo viên" : "Đối tác"})
                </h3>
                <p className="text-slate-400 text-sm">
                  Hoàn thành các bước để làm quen với hệ thống và đủ điều kiện nhận chứng nhận hoàn thành đợt thí điểm.
                </p>

                <div className="space-y-3 mt-4">
                  {[
                    { key: "welcome", label: "1. Định hướng tổng quan nền tảng & mục tiêu thí điểm" },
                    { key: "curriculum_alignment", label: "2. Khảo sát tư liệu Cửu Đỉnh & ánh xạ chuẩn CT GDPT 2018" },
                    { key: "interactive_lesson_wizard", label: "3. Soạn bài dạy 45 phút theo Công văn 5512/BGDĐT" },
                    { key: "printable_kit_review", label: "4. Kiểm thử bộ học liệu in dập nổi 2D băng thông thấp" },
                    { key: "first_class_roster", label: "5. Thiết lập danh sách học sinh & gửi mã tham gia" },
                    { key: "rubric_grading_practice", label: "6. Thử nghiệm chấm rubric lịch sử theo khung S1-S4" },
                    { key: "activation_complete", label: "7. Hoàn tất kích hoạt toàn diện đợt pilot" },
                  ].map((step) => {
                    const isDone = activation.completed_steps.includes(step.key);
                    return (
                      <div
                        key={step.key}
                        className={`flex items-center justify-between p-4 rounded-lg border transition ${
                          isDone
                            ? "bg-emerald-950/20 border-emerald-900/60 text-slate-200"
                            : "bg-slate-950 border-slate-800 text-slate-400"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <div
                            className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                              isDone
                                ? "bg-emerald-500 text-slate-950"
                                : "bg-slate-800 text-slate-400"
                            }`}
                          >
                            {isDone ? <Check className="w-4 h-4" /> : "•"}
                          </div>
                          <span className={`text-sm ${isDone ? "text-white font-medium" : ""}`}>
                            {step.label}
                          </span>
                        </div>
                        {!isDone && (
                          <button
                            onClick={() => handleCompleteStep(step.key)}
                            className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded transition"
                          >
                            Đánh dấu hoàn thành
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Tab 2: Health & Telemetry */}
            {activeTab === "health" && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-white">Chỉ Số Sức Khỏe Tham Gia (Usage Health)</h3>
                  <p className="text-slate-400 text-sm">
                    Đo lường mức độ tương tác thực tế nhằm đảm bảo chất lượng mẫu thử nghiệm khoa học, không tạo số ảo.
                  </p>
                </div>

                {health ? (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-slate-950 border border-slate-800 p-4 rounded-lg">
                      <div className="text-xs text-slate-500">Điểm Sức Khỏe (Health Score)</div>
                      <div className="text-2xl font-bold text-emerald-400 mt-1">
                        {health.health_score.toFixed(0)} / 100
                      </div>
                      <div className="text-xs text-slate-400 mt-1 capitalize">
                        Trạng thái: {health.health_status}
                      </div>
                    </div>
                    <div className="bg-slate-950 border border-slate-800 p-4 rounded-lg">
                      <div className="text-xs text-slate-500">Số Thao Tác Đã Thực Hiện</div>
                      <div className="text-2xl font-bold text-white mt-1">
                        {health.actions_count}
                      </div>
                      <div className="text-xs text-slate-400 mt-1">Hành động tương tác</div>
                    </div>
                    <div className="bg-slate-950 border border-slate-800 p-4 rounded-lg">
                      <div className="text-xs text-slate-500">Thao Tác Gần Nhất</div>
                      <div className="text-sm font-medium text-amber-300 mt-2 truncate">
                        {health.last_action_name || "N/A"}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-sm text-slate-400">Đang tải số liệu sức khỏe pilot...</div>
                )}
              </div>
            )}

            {/* Tab 3: Dedicated Support */}
            {activeTab === "support" && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-white">Hỗ Trợ Kỹ Thuật &amp; Phản Hồi Chuyên Môn</h3>
                  <p className="text-slate-400 text-sm">
                    Gửi yêu cầu trực tiếp đến đội ngũ vận hành pilot. Cam kết phản hồi theo chuẩn SLA trong vòng 24 giờ.
                  </p>
                </div>

                {supportSubmitted ? (
                  <div className="p-4 bg-emerald-950/40 border border-emerald-800 rounded-lg text-emerald-200 text-sm flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                      <span>Yêu cầu của bạn đã được ghi nhận vào hệ thống quản lý vé thử nghiệm.</span>
                    </div>
                    <button
                      onClick={() => setSupportSubmitted(false)}
                      className="text-xs underline text-emerald-400"
                    >
                      Gửi thêm yêu cầu
                    </button>
                  </div>
                ) : (
                  <form onSubmit={handleCreateSupport} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-1">Danh Mục</label>
                      <select
                        value={supportCategory}
                        onChange={(e) => setSupportCategory(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white text-sm"
                      >
                        <option value="onboarding_help">Trợ giúp kích hoạt &amp; onboarding</option>
                        <option value="feature_feedback">Góp ý tính năng bài giảng &amp; rubric</option>
                        <option value="data_privacy">Thắc mắc bảo mật &amp; dữ liệu học sinh</option>
                        <option value="bug_report">Báo cáo lỗi kỹ thuật</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-1">Tiêu Đề</label>
                      <input
                        type="text"
                        value={supportSubject}
                        onChange={(e) => setSupportSubject(e.target.value)}
                        placeholder="Tóm tắt yêu cầu cần hỗ trợ..."
                        className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white text-sm"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-1">Nội Dung Chi Tiết</label>
                      <textarea
                        value={supportMessage}
                        onChange={(e) => setSupportMessage(e.target.value)}
                        rows={4}
                        placeholder="Mô tả cụ thể khó khăn hoặc góp ý..."
                        className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white text-sm"
                        required
                      />
                    </div>

                    <button
                      type="submit"
                      className="bg-amber-600 hover:bg-amber-500 text-white font-medium px-5 py-2 rounded-lg text-sm transition flex items-center gap-2"
                    >
                      <Send className="w-4 h-4" />
                      Gửi Yêu Cầu Hỗ Trợ
                    </button>
                  </form>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
