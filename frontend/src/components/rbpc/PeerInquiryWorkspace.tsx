"use client";

import React, { useState, useEffect } from "react";
import {
  Users,
  BookOpen,
  Send,
  Plus,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  Lock,
  Unlock,
  ShieldCheck,
  Award,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { RbpcCard, RbpcCardHeader } from "@/components/rbpc/RbpcCard";
import { RbpcButton } from "@/components/rbpc/RbpcButton";
import { EpistemicBadge } from "@/components/rbpc/EpistemicBadge";
import type { RbpcLocale } from "@/types/rbpc";

export interface InquiryEvidenceItem {
  id: string;
  source_id: string;
  source_title: string;
  author?: string | null;
  locator: string;
  excerpt: string;
  claim_id?: string | null;
  claim_title?: string | null;
  support_type: string;
  interpretation_note: string;
  contributed_by_user_id: string;
  contributed_by_name: string;
  contributed_at: string;
}

export interface InquirySubmission {
  id: string;
  group_id: string;
  activity_id: string;
  hypothesis: string;
  synthesis_argument: string;
  epistemic_rating: string;
  evidence_items: InquiryEvidenceItem[];
  status: "draft" | "submitted" | "approved" | "revision_requested";
  privacy_mode: "private_group" | "class_visible";
  submitted_at?: string | null;
  submitted_by_id?: string | null;
  teacher_feedback?: string | null;
  score?: number | null;
  version: number;
}

export interface InquiryGroupMember {
  id: string;
  user_id: string;
  display_name?: string | null;
  username?: string | null;
  role: "leader" | "contributor";
  joined_at: string;
}

export interface InquiryGroup {
  id: string;
  activity_id: string;
  classroom_id?: string | null;
  name: string;
  created_by_id: string;
  members: InquiryGroupMember[];
  submission_status?: string | null;
  score?: number | null;
  created_at: string;
}

export interface InquiryActivity {
  id: string;
  classroom_id?: string | null;
  title: string;
  description: string;
  guiding_questions: string[];
  suggested_source_ids: string[];
  suggested_claim_ids: string[];
  is_active: boolean;
}

interface PeerInquiryWorkspaceProps {
  locale?: RbpcLocale;
  activityId?: string;
}

export function PeerInquiryWorkspace({
  locale = "vi",
  activityId,
}: PeerInquiryWorkspaceProps) {
  const [activities, setActivities] = useState<InquiryActivity[]>([]);
  const [selectedActivity, setSelectedActivity] = useState<InquiryActivity | null>(null);
  const [groups, setGroups] = useState<InquiryGroup[]>([]);
  const [activeGroup, setActiveGroup] = useState<InquiryGroup | null>(null);
  const [submission, setSubmission] = useState<InquirySubmission | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Form states
  const [hypothesis, setHypothesis] = useState("");
  const [synthesisArgument, setSynthesisArgument] = useState("");
  const [epistemicRating, setEpistemicRating] = useState("dang_khao_cuu");
  const [privacyMode, setPrivacyMode] = useState<"private_group" | "class_visible">("private_group");

  // New evidence form
  const [newSourceId, setNewSourceId] = useState("");
  const [newLocator, setNewLocator] = useState("");
  const [newExcerpt, setNewExcerpt] = useState("");
  const [newNote, setNewNote] = useState("");
  const [showAddEvidence, setShowAddEvidence] = useState(false);

  // Fetch activities on load
  useEffect(() => {
    async function loadActivities() {
      try {
        setLoading(true);
        const res = await fetch("/api/v1/history/inquiry/activities");
        if (res.ok) {
          const data: InquiryActivity[] = await res.json();
          setActivities(data);
          if (activityId) {
            const found = data.find((a) => a.id === activityId);
            if (found) setSelectedActivity(found);
          } else if (data.length > 0) {
            setSelectedActivity(data[0]);
          }
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    loadActivities();
  }, [activityId]);

  // Load groups when activity selected
  useEffect(() => {
    if (!selectedActivity) return;
    const currentActivityId = selectedActivity.id;
    async function loadGroups() {
      try {
        const res = await fetch(`/api/v1/history/inquiry/activities/${currentActivityId}/groups`);
        if (res.ok) {
          const grps: InquiryGroup[] = await res.json();
          setGroups(grps);
          setActiveGroup((prev) => (prev ? prev : grps.length > 0 ? grps[0] : null));
        }
      } catch (err: any) {
        console.error("Failed to load inquiry groups:", err);
      }
    }
    loadGroups();
  }, [selectedActivity]);

  // Load submission when active group selected
  useEffect(() => {
    if (!activeGroup) {
      setSubmission(null);
      return;
    }
    const currentGroupId = activeGroup.id;
    async function loadSubmission() {
      try {
        setError(null);
        const res = await fetch(`/api/v1/history/inquiry/groups/${currentGroupId}/submission`);
        if (res.ok) {
          const sub: InquirySubmission = await res.json();
          setSubmission(sub);
          setHypothesis(sub.hypothesis || "");
          setSynthesisArgument(sub.synthesis_argument || "");
          setEpistemicRating(sub.epistemic_rating || "dang_khao_cuu");
          setPrivacyMode(sub.privacy_mode || "private_group");
        } else if (res.status === 403) {
          setError(
            locale === "vi"
              ? "Bản thảo nghiên cứu này được bảo mật riêng cho thành viên nhóm và giáo viên phụ trách."
              : "This inquiry draft is private to group members and the classroom teacher."
          );
          setSubmission(null);
        }
      } catch (err: any) {
        setError(err.message);
      }
    }
    loadSubmission();
  }, [activeGroup, locale]);

  // Save draft
  const handleSaveDraft = async () => {
    if (!activeGroup) return;
    try {
      setError(null);
      setSaveSuccess(false);
      const res = await fetch(`/api/v1/history/inquiry/groups/${activeGroup.id}/submission`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          hypothesis,
          synthesis_argument: synthesisArgument,
          epistemic_rating: epistemicRating,
          privacy_mode: privacyMode,
        }),
      });
      if (res.ok) {
        const updated: InquirySubmission = await res.json();
        setSubmission(updated);
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 3000);
      } else {
        const errJson = await res.json();
        setError(errJson?.error?.message || "Failed to update submission");
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  // Add evidence
  const handleAddEvidence = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeGroup) return;
    try {
      setError(null);
      const res = await fetch(`/api/v1/history/inquiry/groups/${activeGroup.id}/evidence`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_id: newSourceId,
          locator: newLocator,
          excerpt: newExcerpt,
          interpretation_note: newNote,
          support_type: "supports",
        }),
      });
      if (res.ok) {
        setShowAddEvidence(false);
        setNewSourceId("");
        setNewLocator("");
        setNewExcerpt("");
        setNewNote("");
        // Reload submission
        const subRes = await fetch(`/api/v1/history/inquiry/groups/${activeGroup.id}/submission`);
        if (subRes.ok) {
          const sub = await subRes.json();
          setSubmission(sub);
        }
      } else {
        const errJson = await res.json();
        setError(errJson?.error?.message || "Failed to add evidence");
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  // Remove evidence
  const handleRemoveEvidence = async (evidenceId: string) => {
    if (!activeGroup) return;
    try {
      setError(null);
      const res = await fetch(
        `/api/v1/history/inquiry/groups/${activeGroup.id}/evidence/${evidenceId}`,
        { method: "DELETE" }
      );
      if (res.ok) {
        const sub: InquirySubmission = await res.json();
        setSubmission(sub);
      } else {
        const errJson = await res.json();
        setError(errJson?.error?.message || "Failed to remove evidence");
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  // Submit inquiry
  const handleSubmitInquiry = async () => {
    if (!activeGroup) return;
    try {
      setError(null);
      const res = await fetch(`/api/v1/history/inquiry/groups/${activeGroup.id}/submit`, {
        method: "POST",
      });
      if (res.ok) {
        const sub: InquirySubmission = await res.json();
        setSubmission(sub);
      } else {
        const errJson = await res.json();
        setError(errJson?.error?.message || "Failed to submit inquiry");
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Activity selector banner */}
      <RbpcCard elevation="surface" padding="responsive" className="space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[var(--rbpc-divider-subtle)] pb-4">
          <div className="flex items-center gap-2">
            <Users className="h-5 w-5 text-[var(--rbpc-primary)]" aria-hidden="true" />
            <h2 className="font-serif text-lg sm:text-xl font-bold text-[var(--rbpc-ink)]">
              {locale === "vi"
                ? "Không Gian Khảo Cứu Lịch Sử Nhóm (Peer Historical Inquiry)"
                : "Collaborative Historical Inquiry Workspace"}
            </h2>
          </div>
          {activities.length > 1 && (
            <select
              aria-label={locale === "vi" ? "Chọn chuyên đề khảo cứu" : "Select inquiry topic"}
              className="rounded-lg border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] px-3 py-1.5 text-xs text-[var(--rbpc-ink)]"
              value={selectedActivity?.id || ""}
              onChange={(e) => {
                const a = activities.find((act) => act.id === e.target.value);
                if (a) setSelectedActivity(a);
              }}
            >
              {activities.map((act) => (
                <option key={act.id} value={act.id}>
                  {act.title}
                </option>
              ))}
            </select>
          )}
        </div>

        {selectedActivity && (
          <div className="space-y-2">
            <h3 className="font-serif text-base font-semibold text-[var(--rbpc-ink)]">
              {selectedActivity.title}
            </h3>
            <p className="text-xs text-[var(--rbpc-ink-subtle)] leading-relaxed">
              {selectedActivity.description}
            </p>
            {selectedActivity.guiding_questions?.length > 0 && (
              <div className="mt-3 rounded-lg bg-[var(--rbpc-surface-subtle)] p-3 text-xs">
                <span className="font-semibold text-[var(--rbpc-primary)] block mb-1">
                  {locale === "vi" ? "Câu hỏi định hướng:" : "Guiding Questions:"}
                </span>
                <ul className="list-disc list-inside space-y-1 text-[var(--rbpc-ink-subtle)]">
                  {selectedActivity.guiding_questions.map((q, idx) => (
                    <li key={idx}>{q}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </RbpcCard>

      {/* Error / Alert notification */}
      {error && (
        <div
          role="alert"
          className="rounded-xl border border-red-200 bg-red-50 p-4 text-xs text-red-800 flex items-start gap-2"
        >
          <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      {/* Group selector tabs */}
      {groups.length > 0 && (
        <div className="flex items-center gap-2 overflow-x-auto pb-2">
          {groups.map((grp) => (
            <button
              key={grp.id}
              type="button"
              onClick={() => setActiveGroup(grp)}
              className={`rounded-lg px-3.5 py-1.5 text-xs font-semibold whitespace-nowrap transition-colors ${
                activeGroup?.id === grp.id
                  ? "bg-[var(--rbpc-primary)] text-white"
                  : "bg-[var(--rbpc-surface)] text-[var(--rbpc-ink-subtle)] border border-[var(--rbpc-divider)] hover:border-[var(--rbpc-primary-border)]"
              }`}
            >
              {grp.name} ({grp.members?.length || 0} TV)
            </button>
          ))}
        </div>
      )}

      {/* Main Collaborative Workspace */}
      {activeGroup && submission && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left 2 Cols: Synthesis & Evidence */}
          <div className="lg:col-span-2 space-y-6">
            <RbpcCard elevation="surface" padding="responsive" className="space-y-4">
              <div className="flex items-center justify-between border-b border-[var(--rbpc-divider-subtle)] pb-3">
                <div className="flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-[var(--rbpc-primary)]" aria-hidden="true" />
                  <h4 className="font-serif text-sm sm:text-base font-bold text-[var(--rbpc-ink)]">
                    {locale === "vi"
                      ? "Tổng Hợp Luận Điểm Lịch Sử Của Nhóm"
                      : "Group Synthesis & Historical Argument"}
                  </h4>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                      submission.status === "approved"
                        ? "bg-emerald-100 text-emerald-800"
                        : submission.status === "submitted"
                        ? "bg-amber-100 text-amber-800"
                        : submission.status === "revision_requested"
                        ? "bg-rose-100 text-rose-800"
                        : "bg-slate-100 text-slate-700"
                    }`}
                  >
                    {submission.status === "approved"
                      ? "Đã duyệt"
                      : submission.status === "submitted"
                      ? "Đã nộp"
                      : submission.status === "revision_requested"
                      ? "Cần chỉnh sửa"
                      : "Bản nháp"}
                  </span>
                  <span className="text-[11px] font-mono text-[var(--rbpc-muted)]">
                    v{submission.version}
                  </span>
                </div>
              </div>

              {/* Hypothesis input */}
              <div className="space-y-1.5">
                <label
                  htmlFor="inquiry-hypothesis"
                  className="block text-xs font-semibold text-[var(--rbpc-ink)]"
                >
                  {locale === "vi"
                    ? "Giả thuyết khảo cứu (Hypothesis):"
                    : "Research Hypothesis:"}
                </label>
                <textarea
                  id="inquiry-hypothesis"
                  rows={2}
                  disabled={submission.status === "submitted" || submission.status === "approved"}
                  value={hypothesis}
                  onChange={(e) => setHypothesis(e.target.value)}
                  placeholder={
                    locale === "vi"
                      ? "Nêu luận điểm hoặc câu trả lời dự kiến cho đề tài..."
                      : "State your central historical hypothesis..."
                  }
                  className="w-full rounded-lg border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-2.5 text-xs text-[var(--rbpc-ink)] focus:outline-none focus:ring-2 focus:ring-[var(--rbpc-focus)] disabled:opacity-60"
                />
              </div>

              {/* Synthesis argument input */}
              <div className="space-y-1.5">
                <label
                  htmlFor="inquiry-synthesis"
                  className="block text-xs font-semibold text-[var(--rbpc-ink)]"
                >
                  {locale === "vi"
                    ? "Lập luận tổng hợp & Đối chiếu nguồn sử liệu:"
                    : "Synthesis Argument & Source Corroboration:"}
                </label>
                <textarea
                  id="inquiry-synthesis"
                  rows={5}
                  disabled={submission.status === "submitted" || submission.status === "approved"}
                  value={synthesisArgument}
                  onChange={(e) => setSynthesisArgument(e.target.value)}
                  placeholder={
                    locale === "vi"
                      ? "Trình bày sự đối chiếu giữa các nguồn sử liệu thành văn (Đại Nam Thực Lục, Hội Điển...) và hiện vật..."
                      : "Corroborate primary text sources with artefacts and secondary interpretations..."
                  }
                  className="w-full rounded-lg border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-2.5 text-xs text-[var(--rbpc-ink)] focus:outline-none focus:ring-2 focus:ring-[var(--rbpc-focus)] disabled:opacity-60"
                />
              </div>

              {/* Epistemic rating and privacy controls */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div className="space-y-1">
                  <label
                    htmlFor="epistemic-select"
                    className="block text-xs font-semibold text-[var(--rbpc-ink)]"
                  >
                    {locale === "vi" ? "Độ tin cậy nhận thức:" : "Epistemic Certainty:"}
                  </label>
                  <select
                    id="epistemic-select"
                    disabled={submission.status === "submitted" || submission.status === "approved"}
                    value={epistemicRating}
                    onChange={(e) => setEpistemicRating(e.target.value)}
                    className="w-full rounded-lg border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-2 text-xs text-[var(--rbpc-ink)] focus:outline-none focus:ring-2 focus:ring-[var(--rbpc-focus)] disabled:opacity-60"
                  >
                    <option value="dang_khao_cuu">
                      {locale === "vi" ? "Đang khảo cứu (Cần dẫn chứng)" : "Under Investigation"}
                    </option>
                    <option value="su_lieu_xac_thuc">
                      {locale === "vi" ? "Sử liệu xác thực (Có sử liệu gốc)" : "Documented Fact"}
                    </option>
                    <option value="truyen_thuyet_dan_gian">
                      {locale === "vi" ? "Truyền thuyết dân gian (Dã sử)" : "Traditional / Oral"}
                    </option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label
                    htmlFor="privacy-select"
                    className="block text-xs font-semibold text-[var(--rbpc-ink)]"
                  >
                    {locale === "vi" ? "Chế độ hiển thị:" : "Privacy Isolation:"}
                  </label>
                  <select
                    id="privacy-select"
                    disabled={submission.status === "submitted" || submission.status === "approved"}
                    value={privacyMode}
                    onChange={(e) => setPrivacyMode(e.target.value as any)}
                    className="w-full rounded-lg border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-2 text-xs text-[var(--rbpc-ink)] focus:outline-none focus:ring-2 focus:ring-[var(--rbpc-focus)] disabled:opacity-60"
                  >
                    <option value="private_group">
                      {locale === "vi" ? "Chỉ trong nhóm & Giáo viên" : "Private (Group & Teacher Only)"}
                    </option>
                    <option value="class_visible">
                      {locale === "vi" ? "Chia sẻ cả lớp khi duyệt" : "Class Visible (When Approved)"}
                    </option>
                  </select>
                </div>
              </div>

              {/* Save & Submit Actions */}
              {submission.status !== "submitted" && submission.status !== "approved" && (
                <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-[var(--rbpc-divider-subtle)]">
                  <div className="flex items-center gap-2">
                    <RbpcButton
                      type="button"
                      variant="secondary"
                      size="sm"
                      onClick={handleSaveDraft}
                    >
                      <span>{locale === "vi" ? "Lưu bản nháp" : "Save Draft"}</span>
                    </RbpcButton>
                    {saveSuccess && (
                      <span className="text-xs text-emerald-600 flex items-center gap-1 font-medium">
                        <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
                        <span>{locale === "vi" ? "Đã lưu thành công" : "Saved"}</span>
                      </span>
                    )}
                  </div>

                  <RbpcButton
                    type="button"
                    variant="primary"
                    size="sm"
                    onClick={handleSubmitInquiry}
                    disabled={!hypothesis.trim() || !synthesisArgument.trim()}
                  >
                    <Send className="h-3.5 w-3.5 mr-1" aria-hidden="true" />
                    <span>{locale === "vi" ? "Nộp bài cho giáo viên" : "Submit Inquiry"}</span>
                  </RbpcButton>
                </div>
              )}
            </RbpcCard>

            {/* Evidence Synthesis List */}
            <RbpcCard elevation="surface" padding="responsive" className="space-y-4">
              <div className="flex items-center justify-between border-b border-[var(--rbpc-divider-subtle)] pb-3">
                <div>
                  <h4 className="font-serif text-sm sm:text-base font-bold text-[var(--rbpc-ink)]">
                    {locale === "vi"
                      ? `Bằng Chứng & Sử Liệu Nhóm Đã Tổng Hợp (${submission.evidence_items.length})`
                      : `Corroborated Evidence Citations (${submission.evidence_items.length})`}
                  </h4>
                  <p className="text-[11px] text-[var(--rbpc-muted)]">
                    {locale === "vi"
                      ? "Mỗi trích dẫn ghi rõ định vị (quyển, tờ), trích đoạn và thành viên đóng góp."
                      : "Citations linked to primary sources with member attribution."}
                  </p>
                </div>

                {submission.status !== "submitted" && submission.status !== "approved" && (
                  <RbpcButton
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={() => setShowAddEvidence(!showAddEvidence)}
                  >
                    <Plus className="h-3.5 w-3.5 mr-1" aria-hidden="true" />
                    <span>{locale === "vi" ? "Thêm sử liệu" : "Add Source"}</span>
                  </RbpcButton>
                )}
              </div>

              {/* Add evidence form modal / drawer */}
              {showAddEvidence && (
                <form
                  onSubmit={handleAddEvidence}
                  className="rounded-xl border border-[var(--rbpc-primary-border)] bg-[var(--rbpc-primary-subtle)] p-4 space-y-3"
                >
                  <h5 className="font-serif text-xs font-bold text-[var(--rbpc-primary)]">
                    {locale === "vi" ? "Bổ sung trích dẫn sử liệu" : "Add Primary Source Citation"}
                  </h5>

                  <div className="space-y-1">
                    <label
                      htmlFor="source-id-input"
                      className="block text-[11px] font-semibold text-[var(--rbpc-ink)]"
                    >
                      Source UUID:
                    </label>
                    <input
                      id="source-id-input"
                      type="text"
                      required
                      placeholder="e.g. 804d9be9-e4cc-442d-802a-ab9bc652a535"
                      value={newSourceId}
                      onChange={(e) => setNewSourceId(e.target.value)}
                      className="w-full rounded border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-2 text-xs font-mono text-[var(--rbpc-ink)]"
                    />
                  </div>

                  <div className="space-y-1">
                    <label
                      htmlFor="locator-input"
                      className="block text-[11px] font-semibold text-[var(--rbpc-ink)]"
                    >
                      {locale === "vi" ? "Định vị (Quyển, tờ, trang):" : "Locator (Volume, folio, page):"}
                    </label>
                    <input
                      id="locator-input"
                      type="text"
                      required
                      placeholder="Đệ nhị kỷ, quyển 154, tờ 12a"
                      value={newLocator}
                      onChange={(e) => setNewLocator(e.target.value)}
                      className="w-full rounded border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-2 text-xs text-[var(--rbpc-ink)]"
                    />
                  </div>

                  <div className="space-y-1">
                    <label
                      htmlFor="excerpt-input"
                      className="block text-[11px] font-semibold text-[var(--rbpc-ink)]"
                    >
                      {locale === "vi" ? "Đoạn văn sử liệu trích dẫn:" : "Source Excerpt:"}
                    </label>
                    <textarea
                      id="excerpt-input"
                      rows={2}
                      required
                      placeholder="Tháng 10 năm Ất Mùi, đúc chín đỉnh..."
                      value={newExcerpt}
                      onChange={(e) => setNewExcerpt(e.target.value)}
                      className="w-full rounded border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-2 text-xs text-[var(--rbpc-ink)]"
                    />
                  </div>

                  <div className="space-y-1">
                    <label
                      htmlFor="note-input"
                      className="block text-[11px] font-semibold text-[var(--rbpc-ink)]"
                    >
                      {locale === "vi" ? "Ghi chú phân tích & suy luận:" : "Interpretation Note:"}
                    </label>
                    <textarea
                      id="note-input"
                      rows={2}
                      required
                      placeholder="Tư liệu khẳng định mối quan hệ giữa quẻ Càn và vua Gia Long..."
                      value={newNote}
                      onChange={(e) => setNewNote(e.target.value)}
                      className="w-full rounded border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-2 text-xs text-[var(--rbpc-ink)]"
                    />
                  </div>

                  <div className="flex items-center justify-end gap-2 pt-2">
                    <RbpcButton
                      type="button"
                      variant="secondary"
                      size="sm"
                      onClick={() => setShowAddEvidence(false)}
                    >
                      <span>{locale === "vi" ? "Hủy" : "Cancel"}</span>
                    </RbpcButton>
                    <RbpcButton type="submit" variant="primary" size="sm">
                      <span>{locale === "vi" ? "Thêm vào nhóm" : "Add Citation"}</span>
                    </RbpcButton>
                  </div>
                </form>
              )}

              {/* Evidence cards */}
              {submission.evidence_items.length > 0 ? (
                <div className="space-y-3">
                  {submission.evidence_items.map((item) => (
                    <div
                      key={item.id}
                      className="rounded-xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-3.5 space-y-2 hover:border-[var(--rbpc-primary-border)] transition-colors"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <h6 className="font-serif text-xs font-bold text-[var(--rbpc-ink)]">
                            {item.source_title}
                          </h6>
                          <span className="text-[11px] font-mono text-[var(--rbpc-primary)] block">
                            {item.locator}
                          </span>
                        </div>
                        {submission.status !== "submitted" && submission.status !== "approved" && (
                          <button
                            type="button"
                            onClick={() => handleRemoveEvidence(item.id)}
                            className="text-red-500 hover:text-red-700 p-1"
                            title="Xóa trích dẫn"
                            aria-label="Remove citation"
                          >
                            <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                          </button>
                        )}
                      </div>

                      <blockquote className="border-l-2 border-[var(--rbpc-primary)] pl-2.5 text-xs italic text-[var(--rbpc-ink-subtle)] leading-relaxed">
                        &ldquo;{item.excerpt}&rdquo;
                      </blockquote>

                      <p className="text-xs text-[var(--rbpc-ink)] leading-relaxed">
                        <strong className="text-[11px] text-[var(--rbpc-muted)] block">
                          {locale === "vi" ? "Phân tích nhóm:" : "Group Interpretation:"}
                        </strong>
                        {item.interpretation_note}
                      </p>

                      <div className="flex items-center justify-between text-[10px] text-[var(--rbpc-muted)] pt-1 border-t border-[var(--rbpc-divider-subtle)]">
                        <span>Đóng góp bởi: <strong className="text-[var(--rbpc-ink)]">{item.contributed_by_name}</strong></span>
                        <span>{new Date(item.contributed_at).toLocaleDateString(locale === "vi" ? "vi-VN" : "en-US")}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-xl border border-dashed border-[var(--rbpc-divider)] p-6 text-center text-xs text-[var(--rbpc-muted)]">
                  {locale === "vi"
                    ? "Chưa có trích dẫn sử liệu nào. Nhóm cần bổ sung ít nhất 1 trích dẫn để nộp bài."
                    : "No primary evidence synthesized yet. Group must corroborate at least one source before submission."}
                </div>
              )}
            </RbpcCard>
          </div>

          {/* Right Col: Team Roster & Teacher Feedback */}
          <div className="space-y-6">
            {/* Group Members Roster */}
            <RbpcCard elevation="surface" padding="responsive" className="space-y-3">
              <div className="flex items-center gap-2 border-b border-[var(--rbpc-divider-subtle)] pb-2.5">
                <Users className="h-4 w-4 text-[var(--rbpc-primary)]" aria-hidden="true" />
                <h4 className="font-serif text-xs sm:text-sm font-bold text-[var(--rbpc-ink)]">
                  {locale === "vi" ? "Thành Viên Nhóm" : "Team Members"}
                </h4>
              </div>

              <div className="space-y-2">
                {activeGroup.members?.map((m) => (
                  <div
                    key={m.id}
                    className="flex items-center justify-between p-2 rounded-lg bg-[var(--rbpc-surface-subtle)] text-xs"
                  >
                    <div>
                      <span className="font-semibold text-[var(--rbpc-ink)] block">
                        {m.display_name || m.username || "Học sinh"}
                      </span>
                      <span className="text-[10px] text-[var(--rbpc-muted)]">
                        Tham gia: {new Date(m.joined_at).toLocaleDateString(locale === "vi" ? "vi-VN" : "en-US")}
                      </span>
                    </div>
                    <span
                      className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${
                        m.role === "leader"
                          ? "bg-amber-100 text-amber-800"
                          : "bg-slate-100 text-slate-700"
                      }`}
                    >
                      {m.role === "leader" ? "Trưởng nhóm" : "Thành viên"}
                    </span>
                  </div>
                ))}
              </div>
            </RbpcCard>

            {/* Teacher Moderation & Feedback */}
            <RbpcCard elevation="surface" padding="responsive" className="space-y-3">
              <div className="flex items-center gap-2 border-b border-[var(--rbpc-divider-subtle)] pb-2.5">
                <ShieldCheck className="h-4 w-4 text-[var(--rbpc-primary)]" aria-hidden="true" />
                <h4 className="font-serif text-xs sm:text-sm font-bold text-[var(--rbpc-ink)]">
                  {locale === "vi" ? "Nhận Xét Của Giáo Viên" : "Teacher Moderation"}
                </h4>
              </div>

              {submission.teacher_feedback ? (
                <div className="space-y-2 text-xs">
                  {submission.score !== null && submission.score !== undefined && (
                    <div className="flex items-center justify-between p-2 rounded-lg bg-emerald-50 border border-emerald-200">
                      <span className="font-semibold text-emerald-800">
                        {locale === "vi" ? "Điểm đánh giá:" : "Assessed Score:"}
                      </span>
                      <span className="font-mono text-sm font-bold text-emerald-900">
                        {submission.score}/100
                      </span>
                    </div>
                  )}

                  <div className="p-3 rounded-lg bg-[var(--rbpc-surface-subtle)] text-[var(--rbpc-ink)] space-y-1">
                    <span className="font-semibold text-[11px] text-[var(--rbpc-muted)] block">
                      {locale === "vi" ? "Góp ý sư phạm:" : "Pedagogical Feedback:"}
                    </span>
                    <p className="leading-relaxed">{submission.teacher_feedback}</p>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-[var(--rbpc-muted)] italic">
                  {locale === "vi"
                    ? "Chưa có nhận xét từ giáo viên phụ trách."
                    : "No teacher feedback recorded yet."}
                </p>
              )}
            </RbpcCard>
          </div>
        </div>
      )}
    </div>
  );
}
