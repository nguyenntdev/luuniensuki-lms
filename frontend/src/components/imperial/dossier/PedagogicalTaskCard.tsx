"use client";

import { useState } from "react";
import {
  GraduationCap,
  Sparkles,
  Send,
  CheckCircle2,
  AlertCircle,
  FileText,
  ChevronDown,
  ChevronUp,
  BookmarkCheck,
  HelpCircle,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { PedagogicalTask, RubricGuidelines } from "@/lib/imperial/map-types";
import StudentSubmissionModal from "./StudentSubmissionModal";
import { saveStudentSubmission } from "@/lib/imperial/submissions-api";
import { useAuthStore } from "@/stores/authStore";

interface PedagogicalTaskCardProps {
  task: PedagogicalTask;
  rubrics: RubricGuidelines;
  monumentName: string;
  monumentSlug?: string;
  availableSources?: Array<{ title: string; citation?: string }>;
}

export default function PedagogicalTaskCard({
  task,
  rubrics,
  monumentName,
  monumentSlug = "di-tich",
  availableSources = [],
}: PedagogicalTaskCardProps) {
  const user = useAuthStore((s) => s.user);
  const [claimText, setClaimText] = useState("");
  const [evidenceText, setEvidenceText] = useState("");
  const [explanationText, setExplanationText] = useState("");
  const [showRubrics, setShowRubrics] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!claimText.trim() || !evidenceText.trim() || !explanationText.trim()) {
      alert("Vui lòng điền đủ 3 phần: Mệnh đề (M), Bằng chứng (E) và Diễn giải (E) để hoàn thành bài tập!");
      return;
    }

    saveStudentSubmission({
      monument_slug: monumentSlug,
      monument_name_vi: monumentName,
      student_id: user?.id || `anon-${Date.now()}`,
      student_name: user?.display_name || user?.username || "Học sinh khảo sát",
      student_class: "Học sinh THPT",
      student_avatar: user?.avatar_url || undefined,
      claim: claimText.trim(),
      evidence: evidenceText.trim(),
      evidence_citations: ["Khảo sát trực tiếp hồ sơ di tích"],
      explanation: explanationText.trim(),
    });

    setIsSubmitted(true);
  };

  return (
    <section aria-labelledby="task-heading" className="space-y-6">
      <div className="flex items-center justify-between border-b border-border/70 pb-3">
        <div className="flex items-center gap-2.5">
          <GraduationCap className="h-5 w-5 text-primary" />
          <h2 id="task-heading" className="font-display text-xl font-bold tracking-tight text-foreground md:text-2xl">
            Nhiệm vụ học tập: &ldquo;Em kết luận gì?&rdquo;
          </h2>
        </div>
        <Badge variant="outline" className="text-xs font-semibold">
          Quy trình M-E-E • Tiêu chí S1-S4
        </Badge>
      </div>

      <div className="rounded-2xl border-2 border-primary/40 bg-card p-6 md:p-8 shadow-sm space-y-6">
        {/* Task Prompt Box */}
        <div className="rounded-xl border border-primary/30 bg-primary/5 p-5 space-y-3">
          <div className="flex items-center gap-2 text-primary font-bold text-xs uppercase tracking-wide">
            <Sparkles className="h-4 w-4 shrink-0" />
            <span>Đề bài khảo sát: {task.title || monumentName}</span>
          </div>

          <p className="font-display text-base font-bold leading-relaxed text-foreground md:text-lg">
            {task.task_prompt}
          </p>

          {task.expected_evidence && (
            <div className="text-xs text-muted-foreground pt-1 border-t border-primary/15">
              <strong>Yêu cầu chứng cứ:</strong> {task.expected_evidence}
            </div>
          )}

          {task.uncertainty_prompt && (
            <div className="rounded-lg bg-amber-500/10 border border-amber-500/20 p-2.5 text-xs text-amber-800 dark:text-amber-300 flex items-start gap-2">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <div>
                <strong>Tư duy phản biện:</strong> {task.uncertainty_prompt}
              </div>
            </div>
          )}
        </div>

        {/* Rubrics Toggle Drawer */}
        <div className="rounded-xl border border-border/80 bg-secondary/30 overflow-hidden">
          <button
            type="button"
            onClick={() => setShowRubrics(!showRubrics)}
            className="w-full flex items-center justify-between p-4 text-xs font-semibold text-foreground hover:bg-secondary/60 transition-colors"
          >
            <div className="flex items-center gap-2">
              <BookmarkCheck className="h-4 w-4 text-primary" />
              <span>Hướng dẫn chấm & Tiêu chuẩn đánh giá (Rubric S1 - S4)</span>
            </div>
            {showRubrics ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>

          {showRubrics && (
            <div className="p-4 pt-0 grid grid-cols-1 gap-3 sm:grid-cols-2 border-t border-border/60">
              <div className="rounded-lg bg-background p-3 text-xs space-y-1 border border-border/50">
                <div className="font-bold text-primary flex items-center gap-1">
                  <span>S1 • Không gian (Spatial)</span>
                </div>
                <p className="text-muted-foreground leading-relaxed">{rubrics.S1_spatial}</p>
              </div>

              <div className="rounded-lg bg-background p-3 text-xs space-y-1 border border-border/50">
                <div className="font-bold text-primary flex items-center gap-1">
                  <span>S2 • Thời gian (Temporal)</span>
                </div>
                <p className="text-muted-foreground leading-relaxed">{rubrics.S2_temporal}</p>
              </div>

              <div className="rounded-lg bg-background p-3 text-xs space-y-1 border border-border/50">
                <div className="font-bold text-primary flex items-center gap-1">
                  <span>S3 • Chứng cứ (Evidence)</span>
                </div>
                <p className="text-muted-foreground leading-relaxed">{rubrics.S3_evidence}</p>
              </div>

              <div className="rounded-lg bg-background p-3 text-xs space-y-1 border border-border/50">
                <div className="font-bold text-primary flex items-center gap-1">
                  <span>S4 • Lập luận (Argument)</span>
                </div>
                <p className="text-muted-foreground leading-relaxed">{rubrics.S4_argument}</p>
              </div>
            </div>
          )}
        </div>

        {/* Student Inquiry Response Form (M-E-E Model) */}
        {isSubmitted ? (
          <div className="rounded-xl border border-emerald-500/40 bg-emerald-500/10 p-6 text-center space-y-3">
            <CheckCircle2 className="mx-auto h-10 w-10 text-emerald-600 dark:text-emerald-400" />
            <h3 className="font-display text-lg font-bold text-emerald-800 dark:text-emerald-300">
              Đã ghi nhận câu trả lời khảo sát!
            </h3>
            <p className="text-xs text-muted-foreground max-w-md mx-auto">
              Bài làm của em theo cấu trúc M-E-E đã được lưu tạm. Em có thể đối chiếu với Rubric S1-S4 hoặc nộp cho giáo viên trong tiết học lịch sử.
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsSubmitted(false)}
              className="mt-2 text-xs"
            >
              Chỉnh sửa bài làm
            </Button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label htmlFor="claim-input" className="text-xs font-bold text-foreground flex items-center gap-1">
                <span>[M] — Mệnh đề / Khẳng định của em (Claim):</span>
                <span className="text-destructive">*</span>
              </label>
              <textarea
                id="claim-input"
                rows={2}
                required
                value={claimText}
                onChange={(e) => setClaimText(e.target.value)}
                placeholder={`Ví dụ: Em kết luận rằng ${monumentName} được quy hoạch nhằm...`}
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground/60 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>

            <div className="space-y-1.5">
              <label htmlFor="evidence-input" className="text-xs font-bold text-foreground flex items-center gap-1">
                <span>[E] — Bằng chứng cụ thể trích từ sử liệu hoặc bản đồ (Evidence):</span>
                <span className="text-destructive">*</span>
              </label>
              <textarea
                id="evidence-input"
                rows={2}
                required
                value={evidenceText}
                onChange={(e) => setEvidenceText(e.target.value)}
                placeholder="Trích dẫn văn bản Đại Nam Thực Lục / Khâm Định Hội Điển hoặc quan sát 5 cửa / 2 tầng sân..."
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground/60 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>

            <div className="space-y-1.5">
              <label htmlFor="explanation-input" className="text-xs font-bold text-foreground flex items-center gap-1">
                <span>[E] — Diễn giải logic nối bằng chứng với mệnh đề (Explanation):</span>
                <span className="text-destructive">*</span>
              </label>
              <textarea
                id="explanation-input"
                rows={3}
                required
                value={explanationText}
                onChange={(e) => setExplanationText(e.target.value)}
                placeholder="Giải thích vì sao bằng chứng trên lại chứng minh được trật tự quyền lực hoặc chức năng di tích..."
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground/60 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setIsModalOpen(true)}
                className="gap-2 text-xs font-semibold border-primary/40 text-primary hover:bg-primary/10"
              >
                <FileText className="h-4 w-4" />
                Mở phiếu nộp chuyên sâu & Trích dẫn
              </Button>
              <Button type="submit" className="gap-2 font-semibold">
                <Send className="h-4 w-4" />
                Hoàn thành kết luận
              </Button>
            </div>
          </form>
        )}
      </div>

      <StudentSubmissionModal
        open={isModalOpen}
        onOpenChange={setIsModalOpen}
        monumentSlug={monumentSlug}
        monumentName={monumentName}
        taskPrompt={task.task_prompt}
        expectedEvidence={task.expected_evidence}
        uncertaintyPrompt={task.uncertainty_prompt}
        availableSources={availableSources}
        onSuccess={() => setIsSubmitted(true)}
      />
    </section>
  );
}
