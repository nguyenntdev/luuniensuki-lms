"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Users,
  BookOpen,
  Plus,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  MessageSquare,
  Link2,
  MoveRight,
  ShieldCheck,
  ChevronRight,
  Send,
  HelpCircle,
  FileText,
  Clock,
  Layers,
  Sparkles,
} from "lucide-react";
import { RbpcCard, RbpcCardHeader } from "@/components/rbpc/RbpcCard";
import { RbpcButton } from "@/components/rbpc/RbpcButton";
import type { RbpcLocale } from "@/types/rbpc";

export interface ComparativeLink {
  id: string;
  source_id_a: string;
  source_title_a: string;
  source_id_b?: string | null;
  source_title_b?: string | null;
  claim_id?: string | null;
  claim_title?: string | null;
  relation_type: "supports" | "refutes" | "corroborates" | "contrasts" | "qualifies";
  rationale: string;
  created_by_user_id: string;
  created_by_name: string;
  created_at: string;
}

export interface TeacherInlineFeedback {
  id: string;
  target_type: "card" | "comparison" | "hypothesis" | "synthesis" | "board";
  target_id?: string | null;
  teacher_id: string;
  teacher_name: string;
  comment: string;
  created_at: string;
  resolved: boolean;
}

export interface EvidenceBoardCard {
  id: string;
  source_id: string;
  source_title: string;
  author?: string | null;
  locator: string;
  excerpt: string;
  claim_id?: string | null;
  claim_title?: string | null;
  support_type: "supports" | "refutes" | "inconclusive" | "disputed";
  board_column: "supporting" | "refuting" | "synthesis" | "unresolved";
  position: number;
  linked_evidence_id?: string | null;
  comparison_notes?: string | null;
  inline_feedback: TeacherInlineFeedback[];
  interpretation_note: string;
  contributed_by_user_id: string;
  contributed_by_name: string;
  contributed_at: string;
}

export interface EvidenceBoardData {
  group_id: string;
  group_name: string;
  activity_id: string;
  activity_title: string;
  hypothesis: string;
  synthesis_argument: string;
  epistemic_rating: string;
  status: "draft" | "submitted" | "approved" | "revision_requested";
  privacy_mode: "private_group" | "class_visible";
  revision_cycle: number;
  version: number;
  columns: Array<"supporting" | "refuting" | "synthesis" | "unresolved">;
  cards: EvidenceBoardCard[];
  comparative_links: ComparativeLink[];
  inline_feedback: TeacherInlineFeedback[];
  revision_history: Array<{
    cycle: number;
    action: string;
    actor_id: string;
    actor_name: string;
    notes?: string;
    timestamp: string;
  }>;
  teacher_feedback?: string | null;
  score?: number | null;
  rubric_evaluation?: Record<string, any>;
  updated_at: string;
}

interface EvidenceBoardProps {
  groupId: string;
  locale?: RbpcLocale;
  isTeacher?: boolean;
}

const COLUMN_CONFIG: Record<
  "supporting" | "refuting" | "synthesis" | "unresolved",
  { titleVi: string; titleEn: string; color: string; badge: string }
> = {
  supporting: {
    titleVi: "Bằng chứng ủng hộ (Supports)",
    titleEn: "Supporting Evidence",
    color: "border-emerald-600/40 bg-emerald-500/5",
    badge: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
  },
  refuting: {
    titleVi: "Bằng chứng phản bác (Refutes)",
    titleEn: "Refuting Evidence",
    color: "border-rose-600/40 bg-rose-500/5",
    badge: "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300",
  },
  synthesis: {
    titleVi: "Tổng hợp luận điểm (Synthesis)",
    titleEn: "Synthesis Arguments",
    color: "border-amber-600/40 bg-amber-500/5",
    badge: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  },
  unresolved: {
    titleVi: "Còn tranh biện (Unresolved)",
    titleEn: "Unresolved / Inconclusive",
    color: "border-slate-500/40 bg-slate-500/5",
    badge: "bg-slate-100 text-slate-800 dark:bg-slate-900 dark:text-slate-300",
  },
};

export function EvidenceBoard({
  groupId,
  locale = "vi",
  isTeacher = false,
}: EvidenceBoardProps) {
  const [board, setBoard] = useState<EvidenceBoardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"columns" | "comparisons" | "revisions">("columns");

  // New Card Form
  const [showAddCard, setShowAddCard] = useState(false);
  const [cardSourceId, setCardSourceId] = useState("");
  const [cardLocator, setCardLocator] = useState("");
  const [cardExcerpt, setCardExcerpt] = useState("");
  const [cardNote, setCardNote] = useState("");
  const [cardSupportType, setCardSupportType] = useState<"supports" | "refutes" | "inconclusive" | "disputed">("supports");
  const [cardColumn, setCardColumn] = useState<"supporting" | "refuting" | "synthesis" | "unresolved">("supporting");

  // New Comparative Link Form
  const [showAddComparison, setShowAddComparison] = useState(false);
  const [compSourceA, setCompSourceA] = useState("");
  const [compSourceB, setCompSourceB] = useState("");
  const [compRelation, setCompRelation] = useState<"supports" | "refutes" | "corroborates" | "contrasts" | "qualifies">("corroborates");
  const [compRationale, setCompRationale] = useState("");

  // Teacher Inline Feedback Form
  const [selectedTargetCard, setSelectedTargetCard] = useState<EvidenceBoardCard | null>(null);
  const [inlineComment, setInlineComment] = useState("");

  // Teacher Request Revision Form
  const [showRevModal, setShowRevModal] = useState(false);
  const [teacherRevFeedback, setTeacherRevFeedback] = useState("");
  const [teacherRevScore, setTeacherRevScore] = useState<number | undefined>(undefined);

  // Student Resubmit Form
  const [showResubmitModal, setShowResubmitModal] = useState(false);
  const [studentResubmitNotes, setStudentResubmitNotes] = useState("");

  // Load board data
  const loadBoard = useCallback(async () => {
    if (!groupId) return;
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`/api/v1/history/inquiry/groups/${groupId}/board`);
      if (res.ok) {
        const data: EvidenceBoardData = await res.json();
        setBoard(data);
      } else if (res.status === 403) {
        setError(
          locale === "vi"
            ? "Bảng bằng chứng này thuộc về nhóm khác. Bạn không có quyền truy cập hoặc chỉnh sửa (403 Forbidden)."
            : "Access denied: Students outside this group cannot access or edit this evidence board (403 Forbidden)."
        );
      } else {
        const errJson = await res.json();
        setError(errJson?.error?.message || "Failed to load evidence board");
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [groupId, locale]);

  useEffect(() => {
    loadBoard();
  }, [loadBoard]);

  // Handle Add Card
  const handleAddCard = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!groupId || !cardSourceId.trim()) return;
    try {
      setError(null);
      const res = await fetch(`/api/v1/history/inquiry/groups/${groupId}/board/cards`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_id: cardSourceId.trim(),
          locator: cardLocator.trim(),
          excerpt: cardExcerpt.trim(),
          support_type: cardSupportType,
          board_column: cardColumn,
          interpretation_note: cardNote.trim(),
        }),
      });
      if (res.ok) {
        setShowAddCard(false);
        setCardSourceId("");
        setCardLocator("");
        setCardExcerpt("");
        setCardNote("");
        await loadBoard();
      } else {
        const err = await res.json();
        setError(err?.error?.message || "Failed to add card");
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  // Handle Move / Update Card Column
  const handleMoveCard = async (cardId: string, newCol: "supporting" | "refuting" | "synthesis" | "unresolved") => {
    if (!groupId) return;
    try {
      const res = await fetch(`/api/v1/history/inquiry/groups/${groupId}/board/cards/${cardId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ board_column: newCol }),
      });
      if (res.ok) {
        await loadBoard();
      } else {
        const err = await res.json();
        setError(err?.error?.message || "Failed to update card column");
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  // Handle Delete Card
  const handleDeleteCard = async (cardId: string) => {
    if (!groupId) return;
    try {
      const res = await fetch(`/api/v1/history/inquiry/groups/${groupId}/board/cards/${cardId}`, {
        method: "DELETE",
      });
      if (res.ok) {
        await loadBoard();
      } else {
        const err = await res.json();
        setError(err?.error?.message || "Failed to remove card");
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  // Handle Add Comparative Link
  const handleAddComparison = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!groupId || !compSourceA.trim()) return;
    try {
      setError(null);
      const res = await fetch(`/api/v1/history/inquiry/groups/${groupId}/board/comparisons`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_id_a: compSourceA.trim(),
          source_id_b: compSourceB.trim() || undefined,
          relation_type: compRelation,
          rationale: compRationale.trim(),
        }),
      });
      if (res.ok) {
        setShowAddComparison(false);
        setCompSourceA("");
        setCompSourceB("");
        setCompRationale("");
        await loadBoard();
      } else {
        const err = await res.json();
        setError(err?.error?.message || "Failed to add comparison");
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  // Handle Teacher Inline Feedback
  const handleAddInlineFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!groupId || !selectedTargetCard || !inlineComment.trim()) return;
    try {
      setError(null);
      const res = await fetch(`/api/v1/history/inquiry/groups/${groupId}/board/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_type: "card",
          target_id: selectedTargetCard.id,
          comment: inlineComment.trim(),
        }),
      });
      if (res.ok) {
        setSelectedTargetCard(null);
        setInlineComment("");
        await loadBoard();
      } else {
        const err = await res.json();
        setError(err?.error?.message || "Failed to post teacher feedback");
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  // Handle Teacher Request Revision
  const handleRequestRevision = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!groupId || !teacherRevFeedback.trim()) return;
    try {
      setError(null);
      const res = await fetch(`/api/v1/history/inquiry/groups/${groupId}/board/request-revision`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          teacher_feedback: teacherRevFeedback.trim(),
          score: teacherRevScore,
        }),
      });
      if (res.ok) {
        setShowRevModal(false);
        setTeacherRevFeedback("");
        await loadBoard();
      } else {
        const err = await res.json();
        setError(err?.error?.message || "Failed to request revision");
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  // Handle Student Resubmit
  const handleResubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!groupId) return;
    try {
      setError(null);
      const res = await fetch(`/api/v1/history/inquiry/groups/${groupId}/board/resubmit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          revision_notes: studentResubmitNotes.trim(),
        }),
      });
      if (res.ok) {
        setShowResubmitModal(false);
        setStudentResubmitNotes("");
        await loadBoard();
      } else {
        const err = await res.json();
        setError(err?.error?.message || "Failed to resubmit board");
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8 text-xs text-[var(--rbpc-muted)]">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-[var(--rbpc-primary)] border-t-transparent mr-2" />
        <span>{locale === "vi" ? "Đang tải bảng bằng chứng..." : "Loading evidence board..."}</span>
      </div>
    );
  }

  if (error && !board) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-xs text-red-800 space-y-2">
        <div className="flex items-center gap-2 font-bold text-sm">
          <AlertTriangle className="h-4 w-4" />
          <span>{locale === "vi" ? "Lỗi truy cập bảng khảo cứu" : "Access Error"}</span>
        </div>
        <p>{error}</p>
      </div>
    );
  }

  if (!board) return null;

  const isLocked = board.status === "submitted" || board.status === "approved";

  return (
    <div className="space-y-6">
      {/* Board Top Header Banner */}
      <RbpcCard elevation="surface" padding="responsive" className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--rbpc-divider-subtle)] pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-[var(--rbpc-primary)] uppercase tracking-wider">
                {locale === "vi" ? "Bảng Bằng Chứng Khảo Cứu" : "Comparative Evidence Board"}
              </span>
              <span className="text-xs text-[var(--rbpc-muted)]">•</span>
              <span className="font-semibold text-xs text-[var(--rbpc-ink)]">
                {board.group_name}
              </span>
              <span className="text-xs text-[var(--rbpc-muted)]">•</span>
              <span className="font-mono text-xs text-[var(--rbpc-muted)]">
                {locale === "vi" ? `Chu kỳ sửa đổi #${board.revision_cycle}` : `Revision Cycle #${board.revision_cycle}`}
              </span>
            </div>
            <h3 className="font-serif text-lg sm:text-xl font-bold text-[var(--rbpc-ink)]">
              {board.activity_title}
            </h3>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${
                board.status === "approved"
                  ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                  : board.status === "submitted"
                  ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                  : board.status === "revision_requested"
                  ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
                  : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
              }`}
            >
              {board.status === "approved"
                ? "Đã duyệt"
                : board.status === "submitted"
                ? "Đang chờ chấm"
                : board.status === "revision_requested"
                ? "Yêu cầu chỉnh sửa"
                : "Bản nháp đang mở"}
            </span>

            {/* Teacher action: Request revision */}
            {isTeacher && board.status === "submitted" && (
              <RbpcButton
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => setShowRevModal(true)}
              >
                <RotateCcw className="h-3.5 w-3.5 mr-1" />
                <span>{locale === "vi" ? "Yêu cầu sửa đổi" : "Request Revision"}</span>
              </RbpcButton>
            )}

            {/* Student action: Resubmit after revision */}
            {!isTeacher && board.status === "revision_requested" && (
              <RbpcButton
                type="button"
                variant="primary"
                size="sm"
                onClick={() => setShowResubmitModal(true)}
              >
                <Send className="h-3.5 w-3.5 mr-1" />
                <span>{locale === "vi" ? "Nộp lại bản sửa đổi" : "Resubmit Revision"}</span>
              </RbpcButton>
            )}
          </div>
        </div>

        {/* Hypothesis & Synthesis Summary Strip */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="rounded-lg bg-[var(--rbpc-surface-subtle)] p-3 space-y-1">
            <span className="font-semibold text-[var(--rbpc-primary)] block">
              {locale === "vi" ? "Giả thuyết khảo cứu:" : "Hypothesis:"}
            </span>
            <p className="text-[var(--rbpc-ink-subtle)] leading-relaxed italic">
              &ldquo;{board.hypothesis || (locale === "vi" ? "Chưa thiết lập giả thuyết" : "No hypothesis set")}&rdquo;
            </p>
          </div>
          <div className="rounded-lg bg-[var(--rbpc-surface-subtle)] p-3 space-y-1">
            <span className="font-semibold text-[var(--rbpc-highlight)] block">
              {locale === "vi" ? "Luận điểm tổng hợp:" : "Synthesis Argument:"}
            </span>
            <p className="text-[var(--rbpc-ink-subtle)] leading-relaxed line-clamp-2">
              {board.synthesis_argument || (locale === "vi" ? "Chưa có luận điểm tổng hợp" : "No synthesis yet")}
            </p>
          </div>
        </div>

        {/* Tabs Bar */}
        <div className="flex items-center justify-between border-t border-[var(--rbpc-divider-subtle)] pt-3">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setActiveTab("columns")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                activeTab === "columns"
                  ? "bg-[var(--rbpc-primary)] text-white"
                  : "text-[var(--rbpc-muted)] hover:text-[var(--rbpc-ink)]"
              }`}
            >
              {locale === "vi" ? `Cột bằng chứng (${board.cards.length})` : `Columns (${board.cards.length})`}
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("comparisons")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                activeTab === "comparisons"
                  ? "bg-[var(--rbpc-primary)] text-white"
                  : "text-[var(--rbpc-muted)] hover:text-[var(--rbpc-ink)]"
              }`}
            >
              {locale === "vi" ? `Liên kết đối chiếu (${board.comparative_links.length})` : `Comparative Links (${board.comparative_links.length})`}
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("revisions")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                activeTab === "revisions"
                  ? "bg-[var(--rbpc-primary)] text-white"
                  : "text-[var(--rbpc-muted)] hover:text-[var(--rbpc-ink)]"
              }`}
            >
              {locale === "vi" ? `Lịch sử chu kỳ (${board.revision_history.length})` : `Revisions (${board.revision_history.length})`}
            </button>
          </div>

          {!isLocked && !isTeacher && activeTab === "columns" && (
            <RbpcButton
              type="button"
              variant="primary"
              size="sm"
              onClick={() => setShowAddCard(!showAddCard)}
            >
              <Plus className="h-3.5 w-3.5 mr-1" />
              <span>{locale === "vi" ? "Thêm thẻ bằng chứng" : "Add Evidence Card"}</span>
            </RbpcButton>
          )}

          {!isLocked && !isTeacher && activeTab === "comparisons" && (
            <RbpcButton
              type="button"
              variant="primary"
              size="sm"
              onClick={() => setShowAddComparison(!showAddComparison)}
            >
              <Link2 className="h-3.5 w-3.5 mr-1" />
              <span>{locale === "vi" ? "Thêm liên kết đối chiếu" : "Add Link"}</span>
            </RbpcButton>
          )}
        </div>
      </RbpcCard>

      {/* Add Card Form Drawer */}
      {showAddCard && (
        <form
          onSubmit={handleAddCard}
          className="rounded-xl border border-[var(--rbpc-primary-border)] bg-[var(--rbpc-surface)] p-4 space-y-3 shadow-md"
        >
          <div className="flex items-center justify-between border-b border-[var(--rbpc-divider-subtle)] pb-2">
            <h4 className="font-serif text-xs font-bold text-[var(--rbpc-primary)]">
              {locale === "vi" ? "Thêm Thẻ Bằng Chứng Mới" : "New Evidence Card"}
            </h4>
            <button
              type="button"
              onClick={() => setShowAddCard(false)}
              className="text-xs text-[var(--rbpc-muted)] hover:text-[var(--rbpc-ink)]"
            >
              ✕
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="space-y-1">
              <label htmlFor="card-src" className="block text-[11px] font-semibold text-[var(--rbpc-ink)]">
                Source UUID:
              </label>
              <input
                id="card-src"
                required
                type="text"
                placeholder="UUID tư liệu chính sử..."
                value={cardSourceId}
                onChange={(e) => setCardSourceId(e.target.value)}
                className="w-full rounded border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-2 text-xs font-mono text-[var(--rbpc-ink)]"
              />
            </div>
            <div className="space-y-1">
              <label htmlFor="card-loc" className="block text-[11px] font-semibold text-[var(--rbpc-ink)]">
                {locale === "vi" ? "Định vị tư liệu:" : "Locator:"}
              </label>
              <input
                id="card-loc"
                required
                type="text"
                placeholder="Quyển, tờ, trang..."
                value={cardLocator}
                onChange={(e) => setCardLocator(e.target.value)}
                className="w-full rounded border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-2 text-xs text-[var(--rbpc-ink)]"
              />
            </div>
            <div className="space-y-1">
              <label htmlFor="card-col" className="block text-[11px] font-semibold text-[var(--rbpc-ink)]">
                {locale === "vi" ? "Cột phân loại:" : "Target Column:"}
              </label>
              <select
                id="card-col"
                value={cardColumn}
                onChange={(e) => {
                  const col = e.target.value as any;
                  setCardColumn(col);
                  if (col === "supporting") setCardSupportType("supports");
                  else if (col === "refuting") setCardSupportType("refutes");
                  else setCardSupportType("inconclusive");
                }}
                className="w-full rounded border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-2 text-xs text-[var(--rbpc-ink)]"
              >
                <option value="supporting">{locale === "vi" ? "Ủng hộ (Supports)" : "Supporting"}</option>
                <option value="refuting">{locale === "vi" ? "Phản bác (Refutes)" : "Refuting"}</option>
                <option value="synthesis">{locale === "vi" ? "Tổng hợp (Synthesis)" : "Synthesis"}</option>
                <option value="unresolved">{locale === "vi" ? "Tranh biện (Unresolved)" : "Unresolved"}</option>
              </select>
            </div>
          </div>

          <div className="space-y-1">
            <label htmlFor="card-exc" className="block text-[11px] font-semibold text-[var(--rbpc-ink)]">
              {locale === "vi" ? "Trích dẫn nguyên văn sử liệu:" : "Excerpt:"}
            </label>
            <textarea
              id="card-exc"
              required
              rows={2}
              placeholder="Nguyên văn chỉ dụ hoặc sử liệu..."
              value={cardExcerpt}
              onChange={(e) => setCardExcerpt(e.target.value)}
              className="w-full rounded border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-2 text-xs text-[var(--rbpc-ink)]"
            />
          </div>

          <div className="space-y-1">
            <label htmlFor="card-note" className="block text-[11px] font-semibold text-[var(--rbpc-ink)]">
              {locale === "vi" ? "Diễn giải & Suy luận lịch sử của nhóm:" : "Interpretation Note:"}
            </label>
            <textarea
              id="card-note"
              required
              rows={2}
              placeholder="Giải thích vì sao nguồn tư liệu này ủng hộ hoặc bác bỏ giả thuyết..."
              value={cardNote}
              onChange={(e) => setCardNote(e.target.value)}
              className="w-full rounded border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-2 text-xs text-[var(--rbpc-ink)]"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-1">
            <RbpcButton type="button" variant="secondary" size="sm" onClick={() => setShowAddCard(false)}>
              <span>{locale === "vi" ? "Hủy" : "Cancel"}</span>
            </RbpcButton>
            <RbpcButton type="submit" variant="primary" size="sm">
              <span>{locale === "vi" ? "Thêm vào bảng" : "Add to Board"}</span>
            </RbpcButton>
          </div>
        </form>
      )}

      {/* Add Comparative Link Drawer */}
      {showAddComparison && (
        <form
          onSubmit={handleAddComparison}
          className="rounded-xl border border-amber-600/40 bg-[var(--rbpc-surface)] p-4 space-y-3 shadow-md"
        >
          <div className="flex items-center justify-between border-b border-[var(--rbpc-divider-subtle)] pb-2">
            <h4 className="font-serif text-xs font-bold text-amber-700 dark:text-amber-400">
              {locale === "vi" ? "Thiết Lập Liên Kết Đối Chiếu Tư Liệu" : "New Comparative Source Link"}
            </h4>
            <button
              type="button"
              onClick={() => setShowAddComparison(false)}
              className="text-xs text-[var(--rbpc-muted)] hover:text-[var(--rbpc-ink)]"
            >
              ✕
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="space-y-1">
              <label htmlFor="comp-src-a" className="block text-[11px] font-semibold text-[var(--rbpc-ink)]">
                Source A UUID:
              </label>
              <input
                id="comp-src-a"
                required
                type="text"
                placeholder="UUID tư liệu A..."
                value={compSourceA}
                onChange={(e) => setCompSourceA(e.target.value)}
                className="w-full rounded border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-2 text-xs font-mono text-[var(--rbpc-ink)]"
              />
            </div>
            <div className="space-y-1">
              <label htmlFor="comp-src-b" className="block text-[11px] font-semibold text-[var(--rbpc-ink)]">
                Source B UUID (optional):
              </label>
              <input
                id="comp-src-b"
                type="text"
                placeholder="UUID tư liệu B..."
                value={compSourceB}
                onChange={(e) => setCompSourceB(e.target.value)}
                className="w-full rounded border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-2 text-xs font-mono text-[var(--rbpc-ink)]"
              />
            </div>
            <div className="space-y-1">
              <label htmlFor="comp-rel" className="block text-[11px] font-semibold text-[var(--rbpc-ink)]">
                {locale === "vi" ? "Mối quan hệ đối chiếu:" : "Relationship Type:"}
              </label>
              <select
                id="comp-rel"
                value={compRelation}
                onChange={(e) => setCompRelation(e.target.value as any)}
                className="w-full rounded border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-2 text-xs text-[var(--rbpc-ink)]"
              >
                <option value="corroborates">{locale === "vi" ? "Cùng chứng minh (Corroborates)" : "Corroborates"}</option>
                <option value="contrasts">{locale === "vi" ? "Mâu thuẫn / Đối nghịch (Contrasts)" : "Contrasts"}</option>
                <option value="supports">{locale === "vi" ? "Ủng hộ luận điểm (Supports)" : "Supports"}</option>
                <option value="refutes">{locale === "vi" ? "Bác bỏ luận điểm (Refutes)" : "Refutes"}</option>
                <option value="qualifies">{locale === "vi" ? "Bổ sung / Giới hạn (Qualifies)" : "Qualifies"}</option>
              </select>
            </div>
          </div>

          <div className="space-y-1">
            <label htmlFor="comp-rat" className="block text-[11px] font-semibold text-[var(--rbpc-ink)]">
              {locale === "vi" ? "Lý giải sự đối chiếu giữa hai nguồn:" : "Comparative Rationale:"}
            </label>
            <textarea
              id="comp-rat"
              required
              rows={2}
              placeholder="Chỉ rõ điểm tương đồng hoặc dị biệt giữa 2 sử liệu..."
              value={compRationale}
              onChange={(e) => setCompRationale(e.target.value)}
              className="w-full rounded border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-2 text-xs text-[var(--rbpc-ink)]"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-1">
            <RbpcButton type="button" variant="secondary" size="sm" onClick={() => setShowAddComparison(false)}>
              <span>{locale === "vi" ? "Hủy" : "Cancel"}</span>
            </RbpcButton>
            <RbpcButton type="submit" variant="primary" size="sm">
              <span>{locale === "vi" ? "Tạo liên kết" : "Create Link"}</span>
            </RbpcButton>
          </div>
        </form>
      )}

      {/* 4-Column Evidence Board View */}
      {activeTab === "columns" && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {(["supporting", "refuting", "synthesis", "unresolved"] as const).map((colKey) => {
            const colCfg = COLUMN_CONFIG[colKey];
            const colCards = board.cards.filter((c) => c.board_column === colKey);
            return (
              <div
                key={colKey}
                className={`rounded-xl border ${colCfg.color} p-3 space-y-3 flex flex-col min-h-[420px]`}
              >
                <div className="flex items-center justify-between border-b border-[var(--rbpc-divider-subtle)] pb-2">
                  <h4 className="font-serif text-xs font-bold text-[var(--rbpc-ink)]">
                    {locale === "vi" ? colCfg.titleVi : colCfg.titleEn}
                  </h4>
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${colCfg.badge}`}>
                    {colCards.length}
                  </span>
                </div>

                <div className="space-y-2 flex-1 overflow-y-auto">
                  {colCards.length > 0 ? (
                    colCards.map((card) => (
                      <div
                        key={card.id}
                        className="rounded-lg border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-3 space-y-2 shadow-xs hover:border-[var(--rbpc-primary-border)] transition-colors"
                      >
                        <div className="flex items-start justify-between gap-1">
                          <span className="font-serif text-xs font-bold text-[var(--rbpc-ink)] line-clamp-1">
                            {card.source_title}
                          </span>
                          {!isLocked && !isTeacher && (
                            <button
                              type="button"
                              onClick={() => handleDeleteCard(card.id)}
                              className="text-red-500 hover:text-red-700 p-0.5"
                              title="Delete card"
                            >
                              <Trash2 className="h-3 w-3" />
                            </button>
                          )}
                        </div>

                        <span className="font-mono text-[10px] text-[var(--rbpc-primary)] block">
                          {card.locator}
                        </span>

                        <blockquote className="border-l-2 border-[var(--rbpc-primary)] pl-2 text-[11px] italic text-[var(--rbpc-ink-subtle)] line-clamp-3">
                          &ldquo;{card.excerpt}&rdquo;
                        </blockquote>

                        <p className="text-[11px] text-[var(--rbpc-ink)] leading-snug">
                          {card.interpretation_note}
                        </p>

                        {/* Inline feedback badge / trigger */}
                        <div className="flex items-center justify-between text-[10px] pt-1 border-t border-[var(--rbpc-divider-subtle)]">
                          <span className="text-[var(--rbpc-muted)]">
                            {card.contributed_by_name}
                          </span>
                          {isTeacher ? (
                            <button
                              type="button"
                              onClick={() => setSelectedTargetCard(card)}
                              className="text-[var(--rbpc-primary)] hover:underline inline-flex items-center gap-0.5"
                            >
                              <MessageSquare className="h-3 w-3" />
                              <span>{locale === "vi" ? "Góp ý" : "Comment"}</span>
                            </button>
                          ) : card.inline_feedback?.length > 0 ? (
                            <span className="text-amber-700 dark:text-amber-400 font-semibold inline-flex items-center gap-0.5">
                              <MessageSquare className="h-3 w-3" />
                              <span>{card.inline_feedback.length}</span>
                            </span>
                          ) : null}
                        </div>

                        {/* Render inline feedback annotations */}
                        {card.inline_feedback?.map((fb) => (
                          <div
                            key={fb.id}
                            className="rounded bg-amber-500/10 border border-amber-600/30 p-2 text-[10px] text-amber-900 dark:text-amber-200 space-y-0.5"
                          >
                            <span className="font-bold block">
                              {fb.teacher_name} ({locale === "vi" ? "Giáo viên" : "Teacher"}):
                            </span>
                            <p>{fb.comment}</p>
                          </div>
                        ))}

                        {/* Card movement helper controls */}
                        {!isLocked && !isTeacher && (
                          <div className="flex items-center justify-between pt-1 border-t border-[var(--rbpc-divider-subtle)] text-[10px]">
                            <span className="text-[var(--rbpc-muted)]">
                              {locale === "vi" ? "Chuyển cột:" : "Move to:"}
                            </span>
                            <div className="flex items-center gap-1">
                              {colKey !== "supporting" && (
                                <button
                                  type="button"
                                  onClick={() => handleMoveCard(card.id, "supporting")}
                                  className="px-1 py-0.5 rounded bg-emerald-100 text-emerald-800 text-[9px]"
                                >
                                  +Ủng hộ
                                </button>
                              )}
                              {colKey !== "refuting" && (
                                <button
                                  type="button"
                                  onClick={() => handleMoveCard(card.id, "refuting")}
                                  className="px-1 py-0.5 rounded bg-rose-100 text-rose-800 text-[9px]"
                                >
                                  +Phản bác
                                </button>
                              )}
                              {colKey !== "synthesis" && (
                                <button
                                  type="button"
                                  onClick={() => handleMoveCard(card.id, "synthesis")}
                                  className="px-1 py-0.5 rounded bg-amber-100 text-amber-800 text-[9px]"
                                >
                                  +Tổng hợp
                                </button>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="rounded-lg border border-dashed border-[var(--rbpc-divider)] p-4 text-center text-[10px] text-[var(--rbpc-muted)]">
                      {locale === "vi" ? "Chưa có thẻ trong cột này" : "Empty column"}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Comparisons Tab View */}
      {activeTab === "comparisons" && (
        <div className="space-y-3">
          {board.comparative_links.length > 0 ? (
            board.comparative_links.map((link) => (
              <RbpcCard key={link.id} elevation="surface" padding="responsive" className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-serif text-xs font-bold text-[var(--rbpc-ink)]">
                      {link.source_title_a}
                    </span>
                    <MoveRight className="h-3.5 w-3.5 text-[var(--rbpc-muted)]" />
                    <span className="font-serif text-xs font-bold text-[var(--rbpc-ink)]">
                      {link.source_title_b || (locale === "vi" ? "Luận điểm" : "Hypothesis")}
                    </span>
                  </div>
                  <span className="rounded-full px-2 py-0.5 text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">
                    {link.relation_type}
                  </span>
                </div>
                <p className="text-xs text-[var(--rbpc-ink-subtle)] leading-relaxed">
                  {link.rationale}
                </p>
                <div className="flex items-center justify-between text-[10px] text-[var(--rbpc-muted)] pt-1 border-t border-[var(--rbpc-divider-subtle)]">
                  <span>{locale === "vi" ? "Người tạo:" : "Author:"} {link.created_by_name}</span>
                  <span>{new Date(link.created_at).toLocaleDateString(locale === "vi" ? "vi-VN" : "en-US")}</span>
                </div>
              </RbpcCard>
            ))
          ) : (
            <div className="rounded-xl border border-dashed border-[var(--rbpc-divider)] p-8 text-center text-xs text-[var(--rbpc-muted)]">
              {locale === "vi"
                ? "Chưa có liên kết so sánh đối chiếu giữa các nguồn sử liệu."
                : "No comparative source links created yet."}
            </div>
          )}
        </div>
      )}

      {/* Revisions Tab View */}
      {activeTab === "revisions" && (
        <div className="space-y-3">
          {board.revision_history.length > 0 ? (
            board.revision_history.map((rev, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 p-3 rounded-lg border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] text-xs"
              >
                <div className="h-7 w-7 rounded-full bg-[var(--rbpc-primary-subtle)] text-[var(--rbpc-primary)] font-mono font-bold flex items-center justify-center shrink-0">
                  {rev.cycle}
                </div>
                <div className="flex-1 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-[var(--rbpc-ink)]">
                      {rev.action} — {rev.actor_name}
                    </span>
                    <span className="text-[10px] text-[var(--rbpc-muted)]">
                      {new Date(rev.timestamp).toLocaleString(locale === "vi" ? "vi-VN" : "en-US")}
                    </span>
                  </div>
                  {rev.notes && (
                    <p className="text-[var(--rbpc-ink-subtle)] leading-relaxed">
                      {rev.notes}
                    </p>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="rounded-xl border border-dashed border-[var(--rbpc-divider)] p-8 text-center text-xs text-[var(--rbpc-muted)]">
              {locale === "vi" ? "Chưa có lịch sử chu kỳ sửa đổi." : "No revision history recorded."}
            </div>
          )}
        </div>
      )}

      {/* Teacher Inline Feedback Modal */}
      {selectedTargetCard && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs"
          onClick={() => setSelectedTargetCard(null)}
        >
          <div
            className="w-full max-w-md rounded-xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-6 space-y-4 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-[var(--rbpc-divider-subtle)] pb-2">
              <h4 className="font-serif text-sm font-bold text-[var(--rbpc-ink)]">
                {locale === "vi" ? "Góp Ý Sư Phạm Thẻ Bằng Chứng" : "Teacher Inline Feedback"}
              </h4>
              <button
                type="button"
                onClick={() => setSelectedTargetCard(null)}
                className="text-xs text-[var(--rbpc-muted)] hover:text-[var(--rbpc-ink)]"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-[var(--rbpc-ink-subtle)]">
              {locale === "vi" ? "Góp ý trên tư liệu:" : "Commenting on:"}{" "}
              <strong>{selectedTargetCard.source_title}</strong>
            </p>

            <form onSubmit={handleAddInlineFeedback} className="space-y-3">
              <textarea
                required
                rows={3}
                placeholder={
                  locale === "vi"
                    ? "Nhập nhận xét sư phạm, yêu cầu đối chiếu thêm hoặc câu hỏi gợi ý..."
                    : "Enter pedagogical feedback or guided inquiry questions..."
                }
                value={inlineComment}
                onChange={(e) => setInlineComment(e.target.value)}
                className="w-full rounded border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-2.5 text-xs text-[var(--rbpc-ink)]"
              />
              <div className="flex items-center justify-end gap-2">
                <RbpcButton type="button" variant="secondary" size="sm" onClick={() => setSelectedTargetCard(null)}>
                  <span>{locale === "vi" ? "Hủy" : "Cancel"}</span>
                </RbpcButton>
                <RbpcButton type="submit" variant="primary" size="sm">
                  <span>{locale === "vi" ? "Gửi góp ý" : "Submit Feedback"}</span>
                </RbpcButton>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Teacher Request Revision Modal */}
      {showRevModal && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs"
          onClick={() => setShowRevModal(false)}
        >
          <div
            className="w-full max-w-md rounded-xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-6 space-y-4 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h4 className="font-serif text-sm font-bold text-[var(--rbpc-ink)]">
              {locale === "vi" ? "Yêu Cầu Chỉnh Sửa & Khởi Động Chu Kỳ Mới" : "Request Revision Cycle"}
            </h4>
            <p className="text-xs text-[var(--rbpc-ink-subtle)]">
              {locale === "vi"
                ? "Bảng bằng chứng sẽ được mở khóa lại để nhóm học sinh tiếp tục bổ sung tư liệu và lập luận."
                : "The evidence board will be unlocked for the student group to address your comments."}
            </p>

            <form onSubmit={handleRequestRevision} className="space-y-3">
              <div className="space-y-1">
                <label htmlFor="rev-feedback" className="block text-xs font-semibold text-[var(--rbpc-ink)]">
                  {locale === "vi" ? "Yêu cầu chỉnh sửa chính:" : "Revision Requirements:"}
                </label>
                <textarea
                  id="rev-feedback"
                  required
                  rows={4}
                  placeholder="Ghi rõ nhóm cần bổ sung nguồn sử liệu nào hoặc làm rõ mâu thuẫn gì..."
                  value={teacherRevFeedback}
                  onChange={(e) => setTeacherRevFeedback(e.target.value)}
                  className="w-full rounded border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-2.5 text-xs text-[var(--rbpc-ink)]"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <RbpcButton type="button" variant="secondary" size="sm" onClick={() => setShowRevModal(false)}>
                  <span>{locale === "vi" ? "Hủy" : "Cancel"}</span>
                </RbpcButton>
                <RbpcButton type="submit" variant="primary" size="sm">
                  <span>{locale === "vi" ? "Xác nhận yêu cầu" : "Confirm Request"}</span>
                </RbpcButton>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Student Resubmit Modal */}
      {showResubmitModal && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs"
          onClick={() => setShowResubmitModal(false)}
        >
          <div
            className="w-full max-w-md rounded-xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-6 space-y-4 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h4 className="font-serif text-sm font-bold text-[var(--rbpc-ink)]">
              {locale === "vi" ? "Nộp Lại Bản Khảo Cứu Đã Chỉnh Sửa" : "Resubmit Revised Evidence Board"}
            </h4>
            <p className="text-xs text-[var(--rbpc-ink-subtle)]">
              {locale === "vi"
                ? "Nộp lại bài cho giáo viên sau khi nhóm đã hoàn thành các góp ý sửa đổi."
                : "Submit the updated evidence board to the teacher for evaluation."}
            </p>

            <form onSubmit={handleResubmit} className="space-y-3">
              <div className="space-y-1">
                <label htmlFor="resubmit-notes" className="block text-xs font-semibold text-[var(--rbpc-ink)]">
                  {locale === "vi" ? "Ghi chú những điểm đã sửa đổi:" : "Notes on Changes Made:"}
                </label>
                <textarea
                  id="resubmit-notes"
                  rows={3}
                  placeholder="Nhóm đã bổ sung thêm nguồn Thực Lục và phân loại lại bằng chứng..."
                  value={studentResubmitNotes}
                  onChange={(e) => setStudentResubmitNotes(e.target.value)}
                  className="w-full rounded border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-2.5 text-xs text-[var(--rbpc-ink)]"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <RbpcButton type="button" variant="secondary" size="sm" onClick={() => setShowResubmitModal(false)}>
                  <span>{locale === "vi" ? "Hủy" : "Cancel"}</span>
                </RbpcButton>
                <RbpcButton type="submit" variant="primary" size="sm">
                  <span>{locale === "vi" ? "Xác nhận nộp" : "Confirm Resubmit"}</span>
                </RbpcButton>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
