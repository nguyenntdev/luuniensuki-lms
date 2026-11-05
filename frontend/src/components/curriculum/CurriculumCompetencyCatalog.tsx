"use client";

import React, { useState, useMemo } from "react";
import {
  BookOpen,
  CheckCircle,
  AlertTriangle,
  Flag,
  Edit3,
  ShieldAlert,
  Filter,
  Layers,
  ChevronDown,
  X,
  Send,
  Save,
} from "lucide-react";
import type {
  CurriculumCompetency,
  CurriculumCompetencyRelicMapping,
  CompetencyFlagReason,
  FlagMappingInput,
  EditMappingInput,
} from "@/types/curriculum";

export interface CurriculumCompetencyCatalogProps {
  competencies: CurriculumCompetency[];
  initialMappings: CurriculumCompetencyRelicMapping[];
  userRole?: string; // "teacher", "admin", "learner", "guest"
  onFlagMapping?: (mappingId: string, input: FlagMappingInput) => Promise<void>;
  onEditMapping?: (mappingId: string, input: EditMappingInput) => Promise<void>;
  className?: string;
}

const GRADE_BAND_OPTIONS = [
  { value: "ALL", label: "Tất cả các khối lớp (6–12)" },
  { value: "GRADE_6_7", label: "Lớp 6–7 (THCS Đầu cấp)" },
  { value: "GRADE_8_9", label: "Lớp 8–9 (THCS Cuối cấp)" },
  { value: "GRADE_10_12", label: "Lớp 10–12 (THPT Chuyên sâu)" },
];

const FLAG_REASONS: { value: CompetencyFlagReason; label: string }[] = [
  { value: "inaccurate_grade_level", label: "Sai lệch phân phối khối lớp / Độ khó không phù hợp" },
  { value: "misaligned_competency", label: "Không chuẩn hóa theo 4 năng lực GDPT 2018" },
  { value: "historical_inaccuracy", label: "Sai lệch sự kiện / Thư tịch cổ hoặc hiện vật" },
  { value: "pedagogical_concern", label: "Hoạt động học tập thiếu tính sư phạm hoặc thiếu nguồn chứng cứ" },
  { value: "other", label: "Lý do học thuật khác" },
];

export const CurriculumCompetencyCatalog: React.FC<CurriculumCompetencyCatalogProps> = ({
  competencies,
  initialMappings,
  userRole = "guest",
  onFlagMapping,
  onEditMapping,
  className = "",
}) => {
  const [mappings, setMappings] = useState<CurriculumCompetencyRelicMapping[]>(initialMappings);
  const [selectedGradeBand, setSelectedGradeBand] = useState<string>("ALL");
  const [selectedDomain, setSelectedDomain] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Modals / forms state
  const [flaggingMappingId, setFlaggingMappingId] = useState<string | null>(null);
  const [flagReason, setFlagReason] = useState<CompetencyFlagReason>("inaccurate_grade_level");
  const [flagCommentary, setFlagCommentary] = useState<string>("");
  const [flagSubmitting, setFlagSubmitting] = useState(false);
  const [flagError, setFlagError] = useState<string | null>(null);

  const [editingMappingId, setEditingMappingId] = useState<string | null>(null);
  const [editMinGrade, setEditMinGrade] = useState<number>(6);
  const [editMaxGrade, setEditMaxGrade] = useState<number>(12);
  const [editActivity, setEditActivity] = useState<string>("");
  const [editEvidence, setEditEvidence] = useState<string>("");
  const [editSubmitting, setEditSubmitting] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  const isTeacherOrStaff = userRole === "teacher" || userRole === "admin" || userRole === "super_admin";

  // Filter mappings
  const filteredMappings = useMemo(() => {
    return mappings.filter((m) => {
      if (selectedGradeBand !== "ALL" && m.grade_band !== selectedGradeBand) {
        return false;
      }
      if (selectedDomain !== "ALL" && m.competency_domain !== selectedDomain) {
        return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const relic = (m.relic_urn_slug || "").toLowerCase();
        const act = m.learning_activity_vi.toLowerCase();
        const code = (m.competency_code || "").toLowerCase();
        if (!relic.includes(q) && !act.includes(q) && !code.includes(q)) {
          return false;
        }
      }
      return true;
    });
  }, [mappings, selectedGradeBand, selectedDomain, searchQuery]);

  const handleOpenFlagModal = (mapping: CurriculumCompetencyRelicMapping) => {
    setFlaggingMappingId(mapping.id);
    setFlagReason("inaccurate_grade_level");
    setFlagCommentary("");
    setFlagError(null);
  };

  const handleSubmitFlag = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!flaggingMappingId) return;
    if (flagCommentary.trim().length < 5) {
      setFlagError("Ý kiến nhận xét phải có ít nhất 5 ký tự");
      return;
    }

    try {
      setFlagSubmitting(true);
      setFlagError(null);
      if (onFlagMapping) {
        await onFlagMapping(flaggingMappingId, {
          reason: flagReason,
          commentary: flagCommentary.trim(),
        });
      }

      // Optimistic update
      setMappings((prev) =>
        prev.map((m) => {
          if (m.id === flaggingMappingId) {
            return {
              ...m,
              status: "flagged",
              is_reviewed: false,
              flag_count: m.flag_count + 1,
              review_warning: `Cảnh báo: Ánh xạ bị giáo viên gắn cờ cảnh báo: ${flagReason}`,
            };
          }
          return m;
        })
      );
      setFlaggingMappingId(null);
    } catch (err: unknown) {
      setFlagError(err instanceof Error ? err.message : "Không thể gửi cảnh báo");
    } finally {
      setFlagSubmitting(false);
    }
  };

  const handleOpenEditModal = (mapping: CurriculumCompetencyRelicMapping) => {
    setEditingMappingId(mapping.id);
    setEditMinGrade(mapping.min_grade);
    setEditMaxGrade(mapping.max_grade);
    setEditActivity(mapping.learning_activity_vi);
    setEditEvidence(mapping.evidence_requirement_vi);
    setEditError(null);
  };

  const handleSubmitEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingMappingId) return;

    if (editMinGrade < 6 || editMaxGrade > 12 || editMinGrade > editMaxGrade) {
      setEditError("Khối lớp không hợp lệ (Phải từ lớp 6 đến lớp 12 và lớp tối thiểu ≤ tối đa)");
      return;
    }
    if (editActivity.trim().length < 3 || editEvidence.trim().length < 3) {
      setEditError("Hoạt động học tập và yêu cầu chứng cứ không được để trống");
      return;
    }

    try {
      setEditSubmitting(true);
      setEditError(null);
      if (onEditMapping) {
        await onEditMapping(editingMappingId, {
          min_grade: editMinGrade,
          max_grade: editMaxGrade,
          learning_activity_vi: editActivity.trim(),
          evidence_requirement_vi: editEvidence.trim(),
        });
      }

      // Optimistic update
      setMappings((prev) =>
        prev.map((m) => {
          if (m.id === editingMappingId) {
            return {
              ...m,
              min_grade: editMinGrade,
              max_grade: editMaxGrade,
              learning_activity_vi: editActivity.trim(),
              evidence_requirement_vi: editEvidence.trim(),
              is_reviewed: false,
              review_warning: "Cảnh báo: Ánh xạ năng lực chưa được thẩm định chuyên môn bởi giáo viên cốt cán",
            };
          }
          return m;
        })
      );
      setEditingMappingId(null);
    } catch (err: unknown) {
      setEditError(err instanceof Error ? err.message : "Không thể cập nhật ánh xạ");
    } finally {
      setEditSubmitting(false);
    }
  };

  return (
    <div className={`space-y-6 ${className}`} data-testid="curriculum-competency-catalog">
      {/* Catalog Header */}
      <div className="bg-amber-950/40 border border-amber-900/60 rounded-xl p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-amber-500 font-semibold text-sm uppercase tracking-wider mb-1">
              <BookOpen className="w-4 h-4" />
              <span>Chương trình Giáo dục Phổ thông 2018 (Môn Lịch sử)</span>
            </div>
            <h1 className="text-2xl font-bold text-amber-100">
              Danh mục Năng lực Lịch sử & Ánh xạ Di sản Cửu Đỉnh
            </h1>
            <p className="text-sm text-neutral-300 mt-1 max-w-2xl">
              Chuẩn hóa 4 năng lực cốt lõi: Tìm hiểu Lịch sử, Khảo chứng Sử liệu, Đồng cảm Lịch sử, và
              Giao tiếp Trình bày. Ánh xạ trực tiếp từ Khối 6 đến Khối 12 đối chiếu 9 Đỉnh hoàng gia.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`px-3 py-1.5 rounded-full text-xs font-semibold ${
                isTeacherOrStaff
                  ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                  : "bg-neutral-800 text-neutral-400 border border-neutral-700"
              }`}
            >
              {isTeacherOrStaff ? "Chế độ Giáo viên / Biên tập viên" : "Chế độ Khách xem"}
            </span>
          </div>
        </div>

        {/* Standard 4 Competencies Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
          {competencies.map((comp) => (
            <div
              key={comp.id}
              className="bg-neutral-900/80 border border-amber-900/40 rounded-lg p-4 space-y-2"
              data-testid={`competency-card-${comp.code}`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-amber-500 font-bold">{comp.code}</span>
                <span className="text-[11px] px-2 py-0.5 rounded bg-neutral-800 text-neutral-300">
                  {comp.domain}
                </span>
              </div>
              <h3 className="font-semibold text-amber-200 text-sm">{comp.name_vi}</h3>
              <p className="text-xs text-neutral-400 line-clamp-3">{comp.description_vi}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
        <div className="flex flex-wrap gap-2 items-center">
          <div className="flex items-center gap-1.5 bg-neutral-900 border border-neutral-800 rounded-lg px-3 py-2 text-sm text-neutral-300">
            <Filter className="w-4 h-4 text-amber-500" />
            <select
              aria-label="Lọc theo khối lớp"
              value={selectedGradeBand}
              onChange={(e) => setSelectedGradeBand(e.target.value)}
              className="bg-transparent text-sm text-neutral-200 focus:outline-none cursor-pointer"
            >
              {GRADE_BAND_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value} className="bg-neutral-900 text-neutral-200">
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5 bg-neutral-900 border border-neutral-800 rounded-lg px-3 py-2 text-sm text-neutral-300">
            <Layers className="w-4 h-4 text-amber-500" />
            <select
              aria-label="Lọc theo miền năng lực"
              value={selectedDomain}
              onChange={(e) => setSelectedDomain(e.target.value)}
              className="bg-transparent text-sm text-neutral-200 focus:outline-none cursor-pointer"
            >
              <option value="ALL" className="bg-neutral-900 text-neutral-200">
                Tất cả 4 năng lực
              </option>
              <option value="historical_literacy" className="bg-neutral-900 text-neutral-200">
                Tìm hiểu lịch sử
              </option>
              <option value="source_criticism" className="bg-neutral-900 text-neutral-200">
                Khảo chứng sử liệu
              </option>
              <option value="historical_empathy" className="bg-neutral-900 text-neutral-200">
                Đồng cảm lịch sử
              </option>
              <option value="historical_communication" className="bg-neutral-900 text-neutral-200">
                Giao tiếp lịch sử
              </option>
            </select>
          </div>
        </div>

        <div className="w-full sm:w-72">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Tìm theo đỉnh, họa tiết, hoạt động..."
            className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-3 py-2 text-sm text-neutral-200 placeholder-neutral-500 focus:outline-none focus:border-amber-600"
          />
        </div>
      </div>

      {/* Relic Mappings List */}
      <div className="space-y-4">
        {filteredMappings.length === 0 ? (
          <div className="p-8 text-center bg-neutral-900/40 border border-neutral-800 rounded-xl text-neutral-400">
            Không tìm thấy ánh xạ năng lực phù hợp với bộ lọc.
          </div>
        ) : (
          filteredMappings.map((m) => (
            <div
              key={m.id}
              className={`border rounded-xl p-5 transition-colors ${
                m.status === "flagged"
                  ? "bg-red-950/20 border-red-800/60"
                  : !m.is_reviewed
                  ? "bg-amber-950/20 border-amber-800/60"
                  : "bg-neutral-900/60 border-neutral-800"
              }`}
              data-testid={`mapping-card-${m.id}`}
            >
              {/* Review Warnings Banner */}
              {(!m.is_reviewed || m.status === "flagged") && m.review_warning && (
                <div
                  className={`mb-4 px-3.5 py-2.5 rounded-lg flex items-start gap-2.5 text-xs font-medium ${
                    m.status === "flagged"
                      ? "bg-red-900/30 text-red-300 border border-red-800/50"
                      : "bg-amber-900/30 text-amber-300 border border-amber-800/50"
                  }`}
                  data-testid={`review-warning-banner-${m.id}`}
                >
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <span className="font-semibold block">Cảnh báo thẩm định năng lực:</span>
                    {m.review_warning}
                  </div>
                </div>
              )}

              {/* Main Mapping Details */}
              <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                <div className="space-y-2 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-900/60">
                      {m.competency_code || "NĂNG LỰC"}
                    </span>
                    <span className="text-xs px-2.5 py-0.5 rounded-full font-semibold bg-neutral-800 text-neutral-300 border border-neutral-700">
                      Lớp {m.min_grade}–{m.max_grade} ({m.grade_band})
                    </span>
                    {m.relic_urn_slug && (
                      <span className="text-xs px-2.5 py-0.5 rounded-full bg-amber-900/30 text-amber-300 border border-amber-800/40">
                        Đỉnh: {m.relic_urn_slug}
                      </span>
                    )}
                    {m.status === "verified" ? (
                      <span className="text-xs px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 flex items-center gap-1 border border-emerald-900">
                        <CheckCircle className="w-3 h-3" /> Đã thẩm định
                      </span>
                    ) : m.status === "flagged" ? (
                      <span className="text-xs px-2 py-0.5 rounded bg-red-950 text-red-400 flex items-center gap-1 border border-red-900">
                        <ShieldAlert className="w-3 h-3" /> Bị gắn cờ sai lệch ({m.flag_count})
                      </span>
                    ) : (
                      <span className="text-xs px-2 py-0.5 rounded bg-amber-950 text-amber-400 flex items-center gap-1 border border-amber-900">
                        <AlertTriangle className="w-3 h-3" /> Chưa duyệt
                      </span>
                    )}
                  </div>

                  <div>
                    <h4 className="text-sm font-semibold text-neutral-200">Hoạt động học tập:</h4>
                    <p className="text-sm text-neutral-300 mt-0.5">{m.learning_activity_vi}</p>
                  </div>

                  <div>
                    <h4 className="text-xs font-semibold text-neutral-400">Yêu cầu chứng cứ sử liệu:</h4>
                    <p className="text-xs text-neutral-400 mt-0.5">{m.evidence_requirement_vi}</p>
                  </div>
                </div>

                {/* Teacher Actions */}
                {isTeacherOrStaff && (
                  <div className="flex sm:flex-col items-center gap-2 shrink-0">
                    <button
                      type="button"
                      onClick={() => handleOpenEditModal(m)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-xs font-medium text-neutral-200 transition-colors border border-neutral-700"
                      data-testid={`btn-edit-mapping-${m.id}`}
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                      <span>Chỉnh sửa</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => handleOpenFlagModal(m)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-950/60 hover:bg-red-900/60 text-xs font-medium text-red-300 transition-colors border border-red-800/60"
                      data-testid={`btn-flag-mapping-${m.id}`}
                    >
                      <Flag className="w-3.5 h-3.5" />
                      <span>Gắn cờ sai lệch</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Flagging Modal */}
      {flaggingMappingId && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
          data-testid="flag-mapping-modal"
        >
          <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6 max-w-lg w-full space-y-4 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-neutral-800">
              <div className="flex items-center gap-2 text-red-400 font-semibold text-sm">
                <Flag className="w-4 h-4" />
                <span>Báo cáo sai lệch ánh xạ năng lực</span>
              </div>
              <button
                type="button"
                onClick={() => setFlaggingMappingId(null)}
                className="text-neutral-400 hover:text-neutral-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {flagError && (
              <div className="p-3 bg-red-950/60 border border-red-800 text-red-300 text-xs rounded-lg">
                {flagError}
              </div>
            )}

            <form onSubmit={handleSubmitFlag} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-neutral-300 mb-1.5">
                  Lý do gắn cờ cảnh báo:
                </label>
                <select
                  value={flagReason}
                  onChange={(e) => setFlagReason(e.target.value as CompetencyFlagReason)}
                  className="w-full bg-neutral-950 border border-neutral-800 rounded-lg p-2.5 text-sm text-neutral-200 focus:outline-none focus:border-red-600"
                  data-testid="flag-reason-select"
                >
                  {FLAG_REASONS.map((r) => (
                    <option key={r.value} value={r.value}>
                      {r.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-neutral-300 mb-1.5">
                  Nhận xét chuyên môn của giáo viên (tối thiểu 5 ký tự):
                </label>
                <textarea
                  rows={3}
                  value={flagCommentary}
                  onChange={(e) => setFlagCommentary(e.target.value)}
                  placeholder="Nêu rõ điểm sai lệch về khối lớp, ngữ liệu lịch sử hoặc phương pháp tiếp cận..."
                  className="w-full bg-neutral-950 border border-neutral-800 rounded-lg p-2.5 text-sm text-neutral-200 focus:outline-none focus:border-red-600"
                  data-testid="flag-commentary-input"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setFlaggingMappingId(null)}
                  className="px-4 py-2 rounded-lg bg-neutral-800 text-xs font-medium text-neutral-300 hover:bg-neutral-700"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={flagSubmitting}
                  className="px-4 py-2 rounded-lg bg-red-700 hover:bg-red-600 text-xs font-medium text-white flex items-center gap-1.5 disabled:opacity-50"
                  data-testid="btn-submit-flag"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{flagSubmitting ? "Đang gửi..." : "Xác nhận gắn cờ"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Teacher Edit Modal */}
      {editingMappingId && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
          data-testid="edit-mapping-modal"
        >
          <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6 max-w-lg w-full space-y-4 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-neutral-800">
              <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm">
                <Edit3 className="w-4 h-4" />
                <span>Chỉnh sửa ánh xạ năng lực di sản</span>
              </div>
              <button
                type="button"
                onClick={() => setEditingMappingId(null)}
                className="text-neutral-400 hover:text-neutral-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {editError && (
              <div className="p-3 bg-red-950/60 border border-red-800 text-red-300 text-xs rounded-lg">
                {editError}
              </div>
            )}

            <form onSubmit={handleSubmitEdit} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-neutral-300 mb-1">Từ lớp:</label>
                  <input
                    type="number"
                    min={6}
                    max={12}
                    value={editMinGrade}
                    onChange={(e) => setEditMinGrade(parseInt(e.target.value) || 6)}
                    className="w-full bg-neutral-950 border border-neutral-800 rounded-lg p-2.5 text-sm text-neutral-200"
                    data-testid="edit-min-grade-input"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-neutral-300 mb-1">Đến lớp:</label>
                  <input
                    type="number"
                    min={6}
                    max={12}
                    value={editMaxGrade}
                    onChange={(e) => setEditMaxGrade(parseInt(e.target.value) || 12)}
                    className="w-full bg-neutral-950 border border-neutral-800 rounded-lg p-2.5 text-sm text-neutral-200"
                    data-testid="edit-max-grade-input"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-neutral-300 mb-1">
                  Hoạt động học tập:
                </label>
                <textarea
                  rows={3}
                  value={editActivity}
                  onChange={(e) => setEditActivity(e.target.value)}
                  className="w-full bg-neutral-950 border border-neutral-800 rounded-lg p-2.5 text-sm text-neutral-200"
                  data-testid="edit-activity-input"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-neutral-300 mb-1">
                  Yêu cầu chứng cứ sử liệu:
                </label>
                <textarea
                  rows={2}
                  value={editEvidence}
                  onChange={(e) => setEditEvidence(e.target.value)}
                  className="w-full bg-neutral-950 border border-neutral-800 rounded-lg p-2.5 text-sm text-neutral-200"
                  data-testid="edit-evidence-input"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setEditingMappingId(null)}
                  className="px-4 py-2 rounded-lg bg-neutral-800 text-xs font-medium text-neutral-300 hover:bg-neutral-700"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={editSubmitting}
                  className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-xs font-medium text-neutral-950 font-bold flex items-center gap-1.5 disabled:opacity-50"
                  data-testid="btn-submit-edit"
                >
                  <Save className="w-3.5 h-3.5" />
                  <span>{editSubmitting ? "Đang lưu..." : "Lưu thay đổi"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default CurriculumCompetencyCatalog;
