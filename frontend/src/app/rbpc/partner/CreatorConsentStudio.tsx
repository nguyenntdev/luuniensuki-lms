"use client";

import React, { useState, useEffect } from "react";
import {
  Mic,
  FileText,
  ShieldCheck,
  ShieldAlert,
  Clock,
  CheckCircle2,
  AlertTriangle,
  History,
  RotateCcw,
  Sparkles,
  Lock,
  Globe,
  Plus,
} from "lucide-react";
import { RbpcCard } from "@/components/rbpc/RbpcCard";
import { RbpcButton } from "@/components/rbpc/RbpcButton";
import { cn } from "@/lib/utils";

export type ConsentScope = "full_public" | "educational_only" | "preview_only" | "revoked";
export type RecordingStatus = "draft" | "submitted" | "consented" | "revoked" | "erased";

export interface TimedCue {
  time_sec: number;
  end_time_sec?: number | null;
  text: string;
  speaker?: string | null;
  section_title?: string | null;
}

export interface TranscriptVersion {
  id: string;
  version_number: number;
  transcript_text_vi: string;
  transcript_text_en?: string | null;
  timed_cues: TimedCue[];
  change_summary?: string | null;
  is_verified_by_artisan: boolean;
  artisan_verified_at?: string | null;
  created_at: string;
}

export interface OralHistoryRecording {
  id: string;
  creator_id: string;
  recording_code: string;
  title_vi: string;
  title_en?: string | null;
  audio_url?: string | null;
  audio_duration_seconds: number;
  cultural_context_vi: string;
  cultural_context_en?: string | null;
  recording_date?: string | null;
  recording_location?: string | null;
  interviewer_name?: string | null;
  epistemic_certainty: string;
  consent_scope: ConsentScope;
  status: RecordingStatus;
  consent_granted: boolean;
  consent_agreement_ref?: string | null;
  consent_notes?: string | null;
  revocation_reason?: string | null;
  current_version_number: number;
  latest_transcript?: TranscriptVersion | null;
}

interface CreatorConsentStudioProps {
  creatorId?: string;
  locale: "vi" | "en";
  isStaffOrPartner: boolean;
  onAlert?: (alert: { type: "success" | "error" | "info"; message: string }) => void;
}

const SAMPLE_RECORDINGS: OralHistoryRecording[] = [
  {
    id: "rec-phuong-duc-01",
    creator_id: "prov-phuong-duc-01",
    recording_code: "OH-PD-1923",
    title_vi: "Ký ức đúc Đại Hồng Chung và bí quyết đất sét sông Hương",
    title_en: "Great Temple Bell Casting Memories & Perfume River Clay Secrets",
    audio_url: "/assets/rbpc/audio/oh-pd-1923.webm",
    audio_duration_seconds: 195,
    cultural_context_vi: "Truyền thống phối trộn đất sét lòng sông Hương với tro trấu tạo khuôn đúc chuông vang xa.",
    recording_date: "2026-03-20",
    recording_location: "Xưởng Đúc Đồng Nguyễn Văn, Phường Đúc, TP. Huế",
    interviewer_name: "Nhà nghiên cứu Trần Đại",
    epistemic_certainty: "community_tradition",
    consent_scope: "full_public",
    status: "consented",
    consent_granted: true,
    consent_agreement_ref: "AGR-2026-PD-009",
    current_version_number: 2,
    latest_transcript: {
      id: "ver-02",
      version_number: 2,
      transcript_text_vi: "Tiếng chuông Cố Đô khác các vùng là nhờ phù sa sông Hương nén chặt, khi rót đồng không sinh bọt khí...",
      timed_cues: [
        { time_sec: 0, end_time_sec: 15.5, text: "Tiếng chuông Cố Đô khác các vùng là nhờ phù sa sông Hương...", speaker: "Nghệ nhân Sáng", section_title: "Bí quyết đất sông Hương" },
        { time_sec: 16, end_time_sec: 45, text: "Khi rót đồng nóng chảy 1100 độ, khuôn đất trấu giữ nhiệt từ từ...", speaker: "Nghệ nhân Sáng", section_title: "Kỹ thuật rót đồng" }
      ],
      change_summary: "Nghệ nhân hiệu đính thuật ngữ tro trấu và nhiệt độ",
      is_verified_by_artisan: true,
      artisan_verified_at: "2026-03-22T09:00:00Z",
      created_at: "2026-03-22T08:30:00Z"
    }
  }
];

export function CreatorConsentStudio({
  creatorId,
  locale,
  isStaffOrPartner,
  onAlert,
}: CreatorConsentStudioProps) {
  const [recordings, setRecordings] = useState<OralHistoryRecording[]>(SAMPLE_RECORDINGS);
  const [selectedRecording, setSelectedRecording] = useState<OralHistoryRecording | null>(
    SAMPLE_RECORDINGS[0] || null
  );
  const [isLoading, setIsLoading] = useState(false);
  const [isRevoking, setIsRevoking] = useState(false);
  const [revokeReason, setRevokeReason] = useState("");
  const [eraseData, setEraseData] = useState(false);

  // Per-use consent modification form state
  const [editScope, setEditScope] = useState<ConsentScope>("full_public");
  const [editNotes, setEditNotes] = useState("");

  // Version revision modal/drawer state
  const [isAddingVersion, setIsAddingVersion] = useState(false);
  const [newTranscriptVi, setNewTranscriptVi] = useState("");
  const [changeSummary, setChangeSummary] = useState("");
  const [verifyByArtisan, setVerifyByArtisan] = useState(true);

  // Sync state if selected changes
  useEffect(() => {
    if (selectedRecording) {
      setEditScope(selectedRecording.consent_scope);
      setEditNotes(selectedRecording.consent_notes || "");
    }
  }, [selectedRecording]);

  const handleUpdateConsent = async () => {
    if (!selectedRecording) return;
    setIsLoading(true);
    try {
      // Optimistic update
      const updated: OralHistoryRecording = {
        ...selectedRecording,
        consent_scope: editScope,
        consent_granted: editScope !== "revoked",
        status: editScope === "revoked" ? "revoked" : "consented",
        consent_notes: editNotes,
      };
      setRecordings((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
      setSelectedRecording(updated);

      onAlert?.({
        type: "success",
        message:
          locale === "vi"
            ? `Đã cập nhật phạm vi đồng thuận sang '${editScope}'.`
            : `Consent scope updated to '${editScope}'.`,
      });
    } catch (err) {
      onAlert?.({
        type: "error",
        message: err instanceof Error ? err.message : "Cập nhật đồng thuận thất bại.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRevokeConsent = async () => {
    if (!selectedRecording || !revokeReason.trim()) return;
    setIsLoading(true);
    try {
      // Optimistic update simulating fail-closed invalidation
      const updated: OralHistoryRecording = {
        ...selectedRecording,
        status: eraseData ? "erased" : "revoked",
        consent_scope: "revoked",
        consent_granted: false,
        revocation_reason: revokeReason,
        audio_url: eraseData ? null : selectedRecording.audio_url,
        latest_transcript: eraseData && selectedRecording.latest_transcript
          ? {
              ...selectedRecording.latest_transcript,
              transcript_text_vi: "[ERASED UNDER RIGHT-TO-ERASURE / DECREE 13/2023/ND-CP]",
              timed_cues: [],
            }
          : selectedRecording.latest_transcript,
      };

      setRecordings((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
      setSelectedRecording(updated);
      setIsRevoking(false);
      setRevokeReason("");

      onAlert?.({
        type: "info",
        message:
          locale === "vi"
            ? "Đã thu hồi đồng thuận ghi âm và phát lệnh hủy bộ nhớ đệm CDN / Cache công khai."
            : "Recording consent revoked. Invalidation dispatched to CDN and edge caches immediately.",
      });
    } catch (err) {
      onAlert?.({
        type: "error",
        message: err instanceof Error ? err.message : "Thu hồi thất bại.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddVersion = async () => {
    if (!selectedRecording || !newTranscriptVi.trim()) return;
    setIsLoading(true);
    try {
      const nextVerNum = selectedRecording.current_version_number + 1;
      const newVersion: TranscriptVersion = {
        id: `ver-${nextVerNum}`,
        version_number: nextVerNum,
        transcript_text_vi: newTranscriptVi.trim(),
        timed_cues: selectedRecording.latest_transcript?.timed_cues || [],
        change_summary: changeSummary.trim() || `Phiên bản hiệu đính v${nextVerNum}`,
        is_verified_by_artisan: verifyByArtisan,
        artisan_verified_at: verifyByArtisan ? new Date().toISOString() : null,
        created_at: new Date().toISOString(),
      };

      const updated: OralHistoryRecording = {
        ...selectedRecording,
        current_version_number: nextVerNum,
        latest_transcript: newVersion,
      };

      setRecordings((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
      setSelectedRecording(updated);
      setIsAddingVersion(false);
      setNewTranscriptVi("");
      setChangeSummary("");

      onAlert?.({
        type: "success",
        message:
          locale === "vi"
            ? `Đã lưu phiên bản văn bản số v${nextVerNum} có xác thực của nghệ nhân.`
            : `Transcript version v${nextVerNum} created and linked.`,
      });
    } catch (err) {
      onAlert?.({
        type: "error",
        message: err instanceof Error ? err.message : "Thêm phiên bản thất bại.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Studio Header Card */}
      <RbpcCard elevation="surface" padding="responsive" className="border-l-4 border-l-purple-600">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-purple-700 dark:text-purple-400">
              <Mic className="h-3.5 w-3.5" />
              <span>
                {locale === "vi"
                  ? "Xưởng Quản Trị Đồng Thuận & Lịch Sử Truyền Khẩu (Oral History Studio)"
                  : "Artisan Oral History Consent Studio & Cultural Memory"}
              </span>
            </div>
            <h2 className="font-serif text-xl sm:text-2xl font-bold text-[var(--rbpc-ink)]">
              {locale === "vi" ? "Bản Ghi Âm Thanh & Quyền Thu Hồi Nghệ Nhân" : "Audio Transcripts & Right-to-Erasure Studio"}
            </h2>
            <p className="text-xs sm:text-sm text-[var(--rbpc-ink-subtle)] max-w-2xl leading-relaxed">
              {locale === "vi"
                ? "Bảo toàn ngữ cảnh văn hóa phi vật thể, lịch sử phiên bản phụ đề và quyền kiểm soát dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP."
                : "Preserve intangible cultural context, timed bilingual transcripts, and full data sovereignty under Decree 13/2023/ND-CP."}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <RbpcButton
              variant="secondary"
              size="sm"
              onClick={() => setIsAddingVersion(true)}
              disabled={!selectedRecording || selectedRecording.status === "revoked" || selectedRecording.status === "erased"}
              className="inline-flex items-center gap-1 text-xs"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>{locale === "vi" ? "Thêm phiên bản lời thoại" : "New Transcript Version"}</span>
            </RbpcButton>
          </div>
        </div>
      </RbpcCard>

      {/* Main Studio Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Recordings List */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--rbpc-muted)]">
            {locale === "vi" ? "Danh sách bản ghi truyền khẩu" : "Oral History Recordings"} ({recordings.length})
          </h3>

          <div className="space-y-2">
            {recordings.map((rec) => {
              const isSelected = selectedRecording?.id === rec.id;
              const isRevoked = rec.status === "revoked" || rec.status === "erased";

              return (
                <button
                  key={rec.id}
                  type="button"
                  onClick={() => setSelectedRecording(rec)}
                  className={cn(
                    "w-full text-left p-3.5 rounded-xl border transition-all space-y-2",
                    isSelected
                      ? "border-purple-600 bg-purple-500/5 shadow-sm ring-1 ring-purple-600/30"
                      : "border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] hover:border-purple-300",
                    isRevoked && "opacity-60 bg-red-500/5 border-red-300"
                  )}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[11px] font-bold text-purple-700 dark:text-purple-400">
                      {rec.recording_code}
                    </span>
                    <span
                      className={cn(
                        "rounded-full px-2 py-0.5 text-[10px] font-bold",
                        rec.status === "consented" && "bg-emerald-500/10 text-emerald-800",
                        rec.status === "draft" && "bg-amber-500/10 text-amber-800",
                        rec.status === "revoked" && "bg-red-500/10 text-red-800",
                        rec.status === "erased" && "bg-gray-500/10 text-gray-800"
                      )}
                    >
                      {rec.status.toUpperCase()}
                    </span>
                  </div>

                  <p className="text-xs font-semibold text-[var(--rbpc-ink)] line-clamp-2">
                    {locale === "vi" ? rec.title_vi : rec.title_en || rec.title_vi}
                  </p>

                  <div className="flex items-center justify-between text-[11px] text-[var(--rbpc-muted)]">
                    <span className="inline-flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      <span>{Math.round(rec.audio_duration_seconds)}s</span>
                    </span>
                    <span className="font-mono text-[10px]">v{rec.current_version_number}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Center & Right: Selected Recording Detail & Consent Controls */}
        {selectedRecording ? (
          <div className="lg:col-span-2 space-y-6">
            {/* Recording Metadata & Cultural Context */}
            <RbpcCard elevation="surface" padding="responsive" className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2 border-b border-[var(--rbpc-divider)] pb-3">
                <div>
                  <span className="text-[10px] font-mono font-semibold uppercase text-purple-700">
                    {selectedRecording.recording_code} • {selectedRecording.recording_date || "2026"}
                  </span>
                  <h4 className="font-serif text-lg font-bold text-[var(--rbpc-ink)]">
                    {selectedRecording.title_vi}
                  </h4>
                  {selectedRecording.recording_location && (
                    <p className="text-xs text-[var(--rbpc-muted)]">
                      {selectedRecording.recording_location} {selectedRecording.interviewer_name ? `• Phỏng vấn: ${selectedRecording.interviewer_name}` : ""}
                    </p>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold",
                      selectedRecording.status === "consented" ? "bg-emerald-500/10 text-emerald-800" : "bg-red-500/10 text-red-800"
                    )}
                  >
                    {selectedRecording.status === "consented" ? (
                      <>
                        <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
                        <span>Đã có đồng thuận</span>
                      </>
                    ) : (
                      <>
                        <ShieldAlert className="h-3.5 w-3.5 text-red-600" />
                        <span>Đã thu hồi / Xóa</span>
                      </>
                    )}
                  </span>
                </div>
              </div>

              {/* Cultural Context Box */}
              <div className="rounded-xl bg-[var(--rbpc-surface-subtle)] p-3 text-xs space-y-1">
                <span className="font-semibold text-purple-700 uppercase tracking-wider text-[10px] block">
                  {locale === "vi" ? "Ngữ cảnh bảo tồn văn hóa & tri thức truyền khẩu:" : "Intangible Cultural Context & Living Tradition:"}
                </span>
                <p className="text-[var(--rbpc-ink)] leading-relaxed">
                  {selectedRecording.cultural_context_vi}
                </p>
              </div>

              {/* Latest Transcript Version & Cues */}
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold uppercase tracking-wider text-[var(--rbpc-muted)]">
                    {locale === "vi" ? "Nội dung phụ đề được lưu trữ" : "Active Transcript Body"} (v{selectedRecording.current_version_number})
                  </span>
                  {selectedRecording.latest_transcript?.is_verified_by_artisan && (
                    <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      <span>{locale === "vi" ? "Nghệ nhân đã kiểm duyệt" : "Artisan Verified"}</span>
                    </span>
                  )}
                </div>

                <div className="rounded-xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-3.5 font-mono text-xs text-[var(--rbpc-ink)] leading-relaxed">
                  {selectedRecording.latest_transcript?.transcript_text_vi || "Chưa có nội dung lời thoại."}
                </div>

                {/* Timed cues preview */}
                {selectedRecording.latest_transcript?.timed_cues && selectedRecording.latest_transcript.timed_cues.length > 0 && (
                  <div className="space-y-1.5">
                    <span className="text-[11px] font-semibold text-[var(--rbpc-muted)] block">
                      {locale === "vi" ? "Đoạn khớp thời gian (Timed Cues):" : "Synchronized Cues:"}
                    </span>
                    <div className="space-y-1 max-h-40 overflow-y-auto pr-1">
                      {selectedRecording.latest_transcript.timed_cues.map((cue, idx) => (
                        <div key={idx} className="flex items-baseline gap-2 text-[11px] p-1.5 rounded bg-[var(--rbpc-surface-subtle)]">
                          <span className="font-mono text-purple-700 font-bold shrink-0">
                            [{cue.time_sec}s - {cue.end_time_sec ?? cue.time_sec}s]
                          </span>
                          <span className="font-semibold text-[var(--rbpc-ink)] shrink-0">{cue.section_title || cue.speaker}:</span>
                          <span className="text-[var(--rbpc-ink-subtle)] truncate">{cue.text}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Consent Management Form */}
              <div className="border-t border-[var(--rbpc-divider)] pt-4 space-y-4">
                <h5 className="text-xs font-bold uppercase tracking-wider text-[var(--rbpc-ink)]">
                  {locale === "vi" ? "Quản lý phạm vi đồng thuận theo ngữ cảnh" : "Per-Use Media Consent Scope"}
                </h5>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-[var(--rbpc-muted)] mb-1">
                      {locale === "vi" ? "Phạm vi công bố:" : "Consent Scope:"}
                    </label>
                    <select
                      value={editScope}
                      onChange={(e) => setEditScope(e.target.value as ConsentScope)}
                      disabled={selectedRecording.status === "erased"}
                      className="w-full text-xs rounded-lg border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-2 text-[var(--rbpc-ink)]"
                    >
                      <option value="full_public">{locale === "vi" ? "Công khai toàn cầu (Full Public)" : "Full Public Streaming"}</option>
                      <option value="educational_only">{locale === "vi" ? "Chỉ mục đích giáo dục & trường học" : "Educational Only (LMS)"}</option>
                      <option value="preview_only">{locale === "vi" ? "Chỉ nghe thử giới hạn tại xưởng" : "Preview / On-site Only"}</option>
                      <option value="revoked">{locale === "vi" ? "Thu hồi quyền phát âm thanh" : "Revoked (Immediate Fail-Closed)"}</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-[var(--rbpc-muted)] mb-1">
                      {locale === "vi" ? "Ghi chú hợp đồng / văn bản:" : "Agreement Document Ref:"}
                    </label>
                    <input
                      type="text"
                      value={editNotes}
                      onChange={(e) => setEditNotes(e.target.value)}
                      placeholder="AGR-2026-..."
                      className="w-full text-xs rounded-lg border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-2 text-[var(--rbpc-ink)]"
                    />
                  </div>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                  <RbpcButton
                    variant="primary"
                    size="sm"
                    onClick={handleUpdateConsent}
                    disabled={isLoading || selectedRecording.status === "erased"}
                    className="text-xs"
                  >
                    <span>{locale === "vi" ? "Lưu thay đổi đồng thuận" : "Save Consent Policy"}</span>
                  </RbpcButton>

                  <button
                    type="button"
                    onClick={() => setIsRevoking(true)}
                    disabled={selectedRecording.status === "revoked" || selectedRecording.status === "erased"}
                    className="inline-flex items-center gap-1.5 text-xs text-red-600 hover:text-red-700 font-semibold disabled:opacity-50 transition-colors"
                  >
                    <AlertTriangle className="h-3.5 w-3.5" />
                    <span>{locale === "vi" ? "Thu hồi / Thực thi quyền được quên (Erasure)" : "Revoke / Right to Erasure"}</span>
                  </button>
                </div>
              </div>
            </RbpcCard>
          </div>
        ) : (
          <div className="lg:col-span-2 flex items-center justify-center p-12 text-center text-xs text-[var(--rbpc-muted)]">
            {locale === "vi" ? "Chọn một bản ghi truyền khẩu để xem chi tiết" : "Select an oral history recording"}
          </div>
        )}
      </div>

      {/* Revocation / Erasure Modal */}
      {isRevoking && selectedRecording && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl border border-red-200 dark:border-red-900 bg-[var(--rbpc-surface)] p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-2 text-red-600 font-bold">
              <ShieldAlert className="h-5 w-5" />
              <span>{locale === "vi" ? "Thu hồi quyền & Hủy bộ nhớ đệm CDN" : "Revoke Consent & Invalidate Caches"}</span>
            </div>

            <p className="text-xs text-[var(--rbpc-ink-subtle)] leading-relaxed">
              {locale === "vi"
                ? "Theo Nghị định 13/2023/NĐ-CP, việc thu hồi sẽ lập tức chặn phát công khai (HTTP 403), xóa tệp âm thanh khỏi bộ nhớ đệm máy chủ và phát thông điệp hủy CDN."
                : "Immediately stops public streaming (HTTP 403) and invalidates edge and CDN caches in compliance with Decree 13/2023/ND-CP."}
            </p>

            <div className="space-y-2">
              <label className="block text-xs font-semibold text-[var(--rbpc-ink)]">
                {locale === "vi" ? "Lý do thu hồi từ nghệ nhân:" : "Revocation reason from artisan:"}
              </label>
              <textarea
                value={revokeReason}
                onChange={(e) => setRevokeReason(e.target.value)}
                rows={3}
                placeholder={locale === "vi" ? "Nghệ nhân yêu cầu bảo mật bí quyết gia truyền..." : "Artisan requested voice withdrawal..."}
                className="w-full text-xs rounded-lg border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-2 text-[var(--rbpc-ink)]"
              />
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="erase-toggle"
                checked={eraseData}
                onChange={(e) => setEraseData(e.target.checked)}
                className="rounded border-[var(--rbpc-divider)]"
              />
              <label htmlFor="erase-toggle" className="text-xs font-medium text-red-700 dark:text-red-400">
                {locale === "vi" ? "Xóa trắng dữ liệu (Right-to-Erasure)" : "Hard scrub data (Right-to-Erasure)"}
              </label>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <RbpcButton variant="subtle" size="sm" onClick={() => setIsRevoking(false)}>
                <span>{locale === "vi" ? "Hủy bỏ" : "Cancel"}</span>
              </RbpcButton>
              <RbpcButton
                variant="primary"
                size="sm"
                onClick={handleRevokeConsent}
                disabled={!revokeReason.trim() || isLoading}
                className="bg-red-600 hover:bg-red-700 text-white"
              >
                <span>{locale === "vi" ? "Xác nhận thu hồi ngay" : "Confirm Revocation"}</span>
              </RbpcButton>
            </div>
          </div>
        </div>
      )}

      {/* New Transcript Version Modal */}
      {isAddingVersion && selectedRecording && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-2 font-serif text-lg font-bold text-[var(--rbpc-ink)]">
              <History className="h-5 w-5 text-purple-600" />
              <span>{locale === "vi" ? `Thêm phiên bản lời thoại v${selectedRecording.current_version_number + 1}` : `Add Transcript Version v${selectedRecording.current_version_number + 1}`}</span>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-[var(--rbpc-ink)] mb-1">
                  {locale === "vi" ? "Nội dung văn bản lời thoại mới:" : "New transcript text:"}
                </label>
                <textarea
                  value={newTranscriptVi}
                  onChange={(e) => setNewTranscriptVi(e.target.value)}
                  rows={4}
                  placeholder="Nhập nội dung đã được chuẩn hóa..."
                  className="w-full text-xs font-mono rounded-lg border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-2 text-[var(--rbpc-ink)]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[var(--rbpc-ink)] mb-1">
                  {locale === "vi" ? "Tóm tắt điểm thay đổi / đính chính:" : "Revision summary / corrections:"}
                </label>
                <input
                  type="text"
                  value={changeSummary}
                  onChange={(e) => setChangeSummary(e.target.value)}
                  placeholder="Hiệu đính tên công cụ đúc đồng cổ..."
                  className="w-full text-xs rounded-lg border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-2 text-[var(--rbpc-ink)]"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="artisan-verified-toggle"
                  checked={verifyByArtisan}
                  onChange={(e) => setVerifyByArtisan(e.target.checked)}
                  className="rounded border-[var(--rbpc-divider)]"
                />
                <label htmlFor="artisan-verified-toggle" className="text-xs font-medium text-purple-700 dark:text-purple-400">
                  {locale === "vi" ? "Đã đối chiếu và nhận được xác nhận từ nghệ nhân" : "Verified by artisan master"}
                </label>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <RbpcButton variant="subtle" size="sm" onClick={() => setIsAddingVersion(false)}>
                <span>{locale === "vi" ? "Đóng" : "Close"}</span>
              </RbpcButton>
              <RbpcButton
                variant="primary"
                size="sm"
                onClick={handleAddVersion}
                disabled={!newTranscriptVi.trim() || isLoading}
              >
                <span>{locale === "vi" ? "Lưu phiên bản mới" : "Save Version"}</span>
              </RbpcButton>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
