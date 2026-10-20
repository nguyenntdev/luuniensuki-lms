"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  BookOpen,
  BookmarkCheck,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  FileText,
  GraduationCap,
  HelpCircle,
  Lightbulb,
  PlusCircle,
  Send,
  Sparkles,
  UserCheck,
} from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { saveStudentSubmission } from "@/lib/imperial/submissions-api";
import { unlockSeal, showSealCelebrationToast } from "@/lib/imperial/passport-storage";
import type { StudentSubmission } from "@/lib/imperial/map-types";

interface StudentSubmissionModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  monumentSlug: string;
  monumentName: string;
  trailSlug?: string;
  trailTitle?: string;
  taskPrompt: string;
  expectedEvidence?: string;
  uncertaintyPrompt?: string;
  availableSources?: Array<{ title: string; citation?: string }>;
  onSuccess?: (submission: StudentSubmission) => void;
}

export default function StudentSubmissionModal({
  open,
  onOpenChange,
  monumentSlug,
  monumentName,
  trailSlug,
  trailTitle,
  taskPrompt,
  expectedEvidence,
  uncertaintyPrompt,
  availableSources = [],
  onSuccess,
}: StudentSubmissionModalProps) {
  const user = useAuthStore((s) => s.user);

  // Form states
  const [studentName, setStudentName] = useState(
    user?.display_name || user?.username || "Nguyễn Văn An",
  );
  const [studentClass, setStudentClass] = useState("Lớp 11 Sử — THPT Chuyên Quốc Học");
  const [claimText, setClaimText] = useState("");
  const [evidenceText, setEvidenceText] = useState("");
  const [selectedCitations, setSelectedCitations] = useState<string[]>([]);
  const [explanationText, setExplanationText] = useState("");
  const [uncertaintyNotes, setUncertaintyNotes] = useState("");

  const [showRubrics, setShowRubrics] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [submittedData, setSubmittedData] = useState<StudentSubmission | null>(null);

  const handleAddCitation = (title: string, citation?: string) => {
    const textToAdd = citation ? `${title} (${citation})` : title;
    if (!selectedCitations.includes(textToAdd)) {
      setSelectedCitations((prev) => [...prev, textToAdd]);
      if (!evidenceText.includes(title)) {
        setEvidenceText((prev) => (prev ? `${prev}\n- Trích dẫn: ${textToAdd}` : `- Trích dẫn: ${textToAdd}`));
      }
    }
  };

  const handleRemoveCitation = (cit: string) => {
    setSelectedCitations((prev) => prev.filter((c) => c !== cit));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!claimText.trim() || !evidenceText.trim() || !explanationText.trim()) {
      alert("Vui lòng điền đủ 3 phần: Mệnh đề (M), Bằng chứng (E) và Diễn giải logic (E) để hoàn thành bài nộp!");
      return;
    }

    const created = saveStudentSubmission({
      monument_slug: monumentSlug,
      monument_name_vi: monumentName,
      trail_slug: trailSlug,
      trail_title: trailTitle,
      student_id: user?.id || `anon-${Date.now()}`,
      student_name: studentName.trim() || "Học sinh ẩn danh",
      student_class: studentClass.trim() || "Học sinh THPT",
      student_avatar: user?.avatar_url || `https://api.dicebear.com/7.x/bottts/svg?seed=${encodeURIComponent(studentName)}`,
      claim: claimText.trim(),
      evidence: evidenceText.trim(),
      evidence_citations: selectedCitations.length > 0 ? selectedCitations : ["Khảo sát trực quan thực địa và sử liệu"],
      explanation: explanationText.trim(),
      notes: uncertaintyNotes.trim() || undefined,
    });

    // Automatically trigger royal seal unlock and celebratory notification toast
    try {
      unlockSeal(monumentSlug, "Khảo sát tư liệu M-E-E");
      showSealCelebrationToast(monumentSlug, monumentName);
    } catch (err) {
      console.warn("Could not unlock passport seal:", err);
    }

    setSubmittedData(created);
    setIsSubmitted(true);
    if (onSuccess) {
      onSuccess(created);
    }
  };

  const handleReset = () => {
    setIsSubmitted(false);
    setClaimText("");
    setEvidenceText("");
    setExplanationText("");
    setSelectedCitations([]);
    setUncertaintyNotes("");
    setSubmittedData(null);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-2xl p-0 gap-0 border-border/80 bg-card">
        {/* Header */}
        <div className="border-b border-border/70 p-6 pb-4 bg-secondary/20">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-primary">
            <GraduationCap className="h-4 w-4" />
            <span>Nộp bài nghiên cứu lịch sử theo mô hình M-E-E</span>
          </div>
          <DialogTitle className="mt-1 font-serif text-xl font-bold tracking-tight text-foreground md:text-2xl">
            Phiếu Khảo Sát: {monumentName}
          </DialogTitle>
          <DialogDescription className="mt-1 text-xs text-muted-foreground">
            {trailTitle ? `Thuộc tuyến học: ${trailTitle}` : "Khảo sát tư liệu và hiện trường Đại Nội Huế"}
          </DialogDescription>
        </div>

        {isSubmitted && submittedData ? (
          <div className="p-8 text-center space-y-6">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="h-9 w-9 animate-in zoom-in-75 duration-300" />
            </div>

            <div className="space-y-2 max-w-lg mx-auto">
              <div className="flex flex-wrap items-center justify-center gap-2">
                <Badge className="bg-amber-500/15 text-amber-700 dark:text-amber-400 border border-amber-500/30 gap-1.5 py-1 px-3">
                  <Sparkles className="h-3.5 w-3.5" />
                  <span>+50 XP Hoàn thành khảo sát lịch sử</span>
                </Badge>
                <Badge className="bg-red-700/15 text-red-700 dark:text-red-400 border border-red-700/30 gap-1.5 py-1 px-3">
                  <span className="font-serif font-black">印</span>
                  <span>Đã đóng Dấu Triện Hoàng Gia</span>
                </Badge>
              </div>
              <h3 className="font-serif text-2xl font-bold text-foreground">
                {typeof navigator !== "undefined" && !navigator.onLine
                  ? "Đã lưu vào bộ nhớ ngoại tuyến!"
                  : "Đã nộp bài khảo sát thành công!"}
              </h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                {typeof navigator !== "undefined" && !navigator.onLine
                  ? "Bài làm của em đã được lưu an toàn trong IndexedDB của thiết bị và sẽ tự động chuyển lên bảng giáo viên ngay khi kết nối lại mạng."
                  : "Bài làm của em đã được chuyển đến Bảng Đánh Giá Giáo Viên. Giáo viên phụ trách bộ môn Lịch sử sẽ đối chiếu theo Rubric S1-S4 để nhận xét và cho điểm."}
              </p>
            </div>

            {/* Submission preview recap */}
            <div className="rounded-xl border border-border/70 bg-secondary/30 p-4 text-left text-xs space-y-3">
              <div className="flex justify-between items-center border-b border-border/50 pb-2 text-muted-foreground">
                <span className="font-medium">Người nộp: <strong>{submittedData.student_name}</strong> ({submittedData.student_class})</span>
                <span className="text-[11px] font-mono">Mã: {submittedData.id}</span>
              </div>
              <div>
                <span className="font-bold text-primary">[M] Mệnh đề:</span>
                <p className="mt-0.5 text-foreground leading-relaxed">{submittedData.claim}</p>
              </div>
              <div>
                <span className="font-bold text-primary">[E] Bằng chứng sử liệu:</span>
                <p className="mt-0.5 text-foreground leading-relaxed whitespace-pre-line">{submittedData.evidence}</p>
              </div>
              <div>
                <span className="font-bold text-primary">[E] Diễn giải logic:</span>
                <p className="mt-0.5 text-foreground leading-relaxed">{submittedData.explanation}</p>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
              <Button onClick={handleReset} className="font-semibold text-xs h-9">
                Đóng & Tiếp tục học
              </Button>
              <Link href="/dai-noi/ho-chieu">
                <Button
                  variant="outline"
                  className="border-[#d4af37] text-amber-800 dark:text-amber-300 hover:bg-amber-500/10 font-semibold text-xs h-9 gap-1.5"
                >
                  <BookOpen className="size-3.5 text-amber-600" />
                  <span>Mở Hộ Chiếu Di Sản</span>
                </Button>
              </Link>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-6 space-y-5">
            {/* Task Prompt Overview */}
            <div className="rounded-xl border border-primary/20 bg-primary/5 p-4 space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold text-primary">
                <Lightbulb className="h-4 w-4" />
                <span>Nhiệm vụ khảo sát cần giải quyết:</span>
              </div>
              <p className="text-sm font-semibold leading-relaxed text-foreground">
                {taskPrompt}
              </p>
              {expectedEvidence && (
                <div className="text-xs text-muted-foreground pt-1 border-t border-primary/10">
                  <strong>Chứng cứ yêu cầu:</strong> {expectedEvidence}
                </div>
              )}
            </div>

            {/* Student Info inputs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                  <UserCheck className="h-3.5 w-3.5 text-muted-foreground" />
                  Họ và tên học sinh: <span className="text-destructive">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={studentName}
                  onChange={(e) => setStudentName(e.target.value)}
                  placeholder="Ví dụ: Trần Văn Nam"
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-xs focus:border-primary focus:outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                  <GraduationCap className="h-3.5 w-3.5 text-muted-foreground" />
                  Lớp / Trường học: <span className="text-destructive">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={studentClass}
                  onChange={(e) => setStudentClass(e.target.value)}
                  placeholder="Ví dụ: 11 Sử — THPT Chuyên Quốc Học"
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-xs focus:border-primary focus:outline-none"
                />
              </div>
            </div>

            {/* Step 1: Claim [M] */}
            <div className="space-y-1.5 rounded-xl border border-border/80 bg-background p-3.5 shadow-xs">
              <div className="flex items-center justify-between">
                <label htmlFor="modal-claim" className="text-xs font-bold text-foreground flex items-center gap-1.5">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/20 text-[11px] font-bold text-primary">M</span>
                  <span>Mệnh đề / Khẳng định của em (Claim):</span>
                  <span className="text-destructive">*</span>
                </label>
                <span className="text-[10px] text-muted-foreground">Trả lời trực tiếp câu hỏi khảo sát</span>
              </div>
              <textarea
                id="modal-claim"
                rows={2}
                required
                value={claimText}
                onChange={(e) => setClaimText(e.target.value)}
                placeholder={`Em kết luận rằng ${monumentName} được thiết kế nhằm khẳng định...`}
                className="w-full rounded-md border border-border/80 bg-secondary/15 px-3 py-2 text-xs placeholder:text-muted-foreground/60 focus:border-primary focus:bg-background focus:outline-none"
              />
            </div>

            {/* Step 2: Evidence [E] */}
            <div className="space-y-2 rounded-xl border border-border/80 bg-background p-3.5 shadow-xs">
              <div className="flex items-center justify-between">
                <label htmlFor="modal-evidence" className="text-xs font-bold text-foreground flex items-center gap-1.5">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/20 text-[11px] font-bold text-primary">E</span>
                  <span>Bằng chứng sử liệu & Quan sát thực địa (Evidence):</span>
                  <span className="text-destructive">*</span>
                </label>
                <span className="text-[10px] text-muted-foreground">Trích dẫn chính sử hoặc chi tiết kiến trúc</span>
              </div>

              {/* Quick source insertion tags */}
              {availableSources.length > 0 && (
                <div className="rounded-lg bg-secondary/40 p-2.5 space-y-1.5 border border-border/60">
                  <span className="text-[11px] font-semibold text-muted-foreground flex items-center gap-1">
                    <FileText className="h-3.5 w-3.5 text-primary" />
                    Chạm để chèn nhanh tư liệu đã kiểm chứng của công trình:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {availableSources.map((src, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => handleAddCitation(src.title, src.citation)}
                        className="inline-flex items-center gap-1 rounded-md border border-primary/30 bg-primary/10 px-2 py-1 text-[11px] font-medium text-primary hover:bg-primary/20 transition-colors"
                      >
                        <PlusCircle className="h-3 w-3" />
                        <span>{src.title}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Selected citations chips */}
              {selectedCitations.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {selectedCitations.map((cit, idx) => (
                    <Badge
                      key={idx}
                      variant="secondary"
                      className="gap-1 text-[11px] bg-secondary border border-border font-normal py-0.5"
                    >
                      <span className="truncate max-w-xs">{cit}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveCitation(cit)}
                        className="hover:text-destructive font-bold ml-1"
                        title="Xóa nguồn này"
                      >
                        ×
                      </button>
                    </Badge>
                  ))}
                </div>
              )}

              <textarea
                id="modal-evidence"
                rows={3}
                required
                value={evidenceText}
                onChange={(e) => setEvidenceText(e.target.value)}
                placeholder="Trích dẫn đoạn văn bản (Đại Nam Thực Lục, Hội Điển...) hoặc số liệu quan sát (kích thước, số cột, lối cửa, chất liệu đá/ngói)..."
                className="w-full rounded-md border border-border/80 bg-secondary/15 px-3 py-2 text-xs placeholder:text-muted-foreground/60 focus:border-primary focus:bg-background focus:outline-none font-sans"
              />
            </div>

            {/* Step 3: Explanation [E] */}
            <div className="space-y-1.5 rounded-xl border border-border/80 bg-background p-3.5 shadow-xs">
              <div className="flex items-center justify-between">
                <label htmlFor="modal-explanation" className="text-xs font-bold text-foreground flex items-center gap-1.5">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/20 text-[11px] font-bold text-primary">E</span>
                  <span>Diễn giải logic nối Bằng chứng với Mệnh đề (Explanation):</span>
                  <span className="text-destructive">*</span>
                </label>
                <span className="text-[10px] text-muted-foreground">Vì sao bằng chứng chứng minh được mệnh đề?</span>
              </div>
              <textarea
                id="modal-explanation"
                rows={3}
                required
                value={explanationText}
                onChange={(e) => setExplanationText(e.target.value)}
                placeholder="Giải thích mối liên hệ nhân quả, tư tưởng chính trị hoặc bối cảnh lịch sử chi phối..."
                className="w-full rounded-md border border-border/80 bg-secondary/15 px-3 py-2 text-xs placeholder:text-muted-foreground/60 focus:border-primary focus:bg-background focus:outline-none"
              />
            </div>

            {/* Optional: Critical Thinking / Uncertainty notes */}
            {uncertaintyPrompt && (
              <div className="space-y-1.5 rounded-xl border border-amber-500/30 bg-amber-500/5 p-3.5 text-xs">
                <div className="flex items-center gap-1.5 text-amber-800 dark:text-amber-300 font-bold">
                  <HelpCircle className="h-4 w-4" />
                  <span>Tư duy phản biện & Nghi vấn sử liệu (Không bắt buộc):</span>
                </div>
                <p className="text-muted-foreground text-[11px] leading-relaxed">
                  {uncertaintyPrompt}
                </p>
                <input
                  type="text"
                  value={uncertaintyNotes}
                  onChange={(e) => setUncertaintyNotes(e.target.value)}
                  placeholder="Điều em thấy còn hoài nghi hoặc cần đối chiếu thêm qua khảo cổ học..."
                  className="w-full rounded-md border border-border/80 bg-background px-3 py-1.5 text-xs focus:border-primary focus:outline-none"
                />
              </div>
            )}

            {/* Rubrics Self-Check Accordion */}
            <div className="rounded-xl border border-border/80 bg-secondary/20 overflow-hidden">
              <button
                type="button"
                onClick={() => setShowRubrics(!showRubrics)}
                className="w-full flex items-center justify-between p-3 text-xs font-semibold text-foreground hover:bg-secondary/40 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <BookmarkCheck className="h-4 w-4 text-primary" />
                  <span>Tự đối chiếu tiêu chí Rubric S1 - S4 trước khi nộp bài</span>
                </div>
                {showRubrics ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </button>

              {showRubrics && (
                <div className="p-3.5 pt-0 grid grid-cols-1 gap-2 sm:grid-cols-2 text-xs border-t border-border/60">
                  <div className="p-2.5 rounded-lg bg-background border border-border/60">
                    <span className="font-bold text-primary">S1 • Năng lực Không gian (0-3đ)</span>
                    <p className="text-[11px] text-muted-foreground mt-0.5">Xác định đúng vị trí trục Thần đạo, phân tầng không gian và phương hướng.</p>
                  </div>
                  <div className="p-2.5 rounded-lg bg-background border border-border/60">
                    <span className="font-bold text-primary">S2 • Năng lực Thời gian (0-3đ)</span>
                    <p className="text-[11px] text-muted-foreground mt-0.5">Xác định đúng mốc xây dựng, biến chuyển triều đại và phục hồi di sản.</p>
                  </div>
                  <div className="p-2.5 rounded-lg bg-background border border-border/60">
                    <span className="font-bold text-primary">S3 • Năng lực Sử liệu (0-3đ)</span>
                    <p className="text-[11px] text-muted-foreground mt-0.5">Trích dẫn chính xác tên tài liệu, điều luật hoặc tư liệu ảnh đối chứng.</p>
                  </div>
                  <div className="p-2.5 rounded-lg bg-background border border-border/60">
                    <span className="font-bold text-primary">S4 • Năng lực Lập luận (0-3đ)</span>
                    <p className="text-[11px] text-muted-foreground mt-0.5">Lập luận sắc bén theo M-E-E, logic mạch lạc, có tư duy phản biện.</p>
                  </div>
                </div>
              )}
            </div>

            <DialogFooter className="gap-2 sm:gap-0 pt-2 border-t border-border/60">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => onOpenChange(false)}
              >
                Hủy bỏ
              </Button>
              <Button type="submit" size="sm" className="gap-2 font-semibold">
                <Send className="h-4 w-4" />
                Nộp bài cho Giáo viên
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
