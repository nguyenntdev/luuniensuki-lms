"use client";

import React, { useState } from "react";
import {
  BookOpen,
  Calendar,
  CheckCircle2,
  Clock,
  Compass,
  Download,
  FileCheck2,
  FileText,
  GraduationCap,
  Layers,
  MapPin,
  Printer,
  Sparkles,
  ShieldCheck,
  ShieldAlert,
  AlertCircle,
  Eye,
  Check,
  ChevronRight,
  ChevronLeft,
  X,
  ExternalLink,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

export interface LessonWizardModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (plan: any) => void;
}

export type WizardPhase = "objectives" | "source" | "media" | "inquiry" | "assessment";

export default function LessonPlanWizardModal({
  isOpen,
  onClose,
  onSuccess,
}: LessonWizardModalProps) {
  const [currentPhase, setCurrentPhase] = useState<WizardPhase>("objectives");

  // Form State
  const [title, setTitle] = useState("Khảo sát hình tượng Rồng trên Cao Đỉnh");
  const [topic, setTopic] = useState("Ý nghĩa biểu tượng vương quyền thời Nguyễn");
  const [targetGrade, setTargetGrade] = useState("Lớp 10 THPT");
  const [durationMinutes, setDurationMinutes] = useState(45);
  const [curriculumFramework, setCurriculumFramework] = useState("CV 5512/BGDĐT");

  // Phase 2: Object & Sources
  const [selectedRelic, setSelectedRelic] = useState("cao-dinh-long");
  const [selectedUrn, setSelectedUrn] = useState("Cao Đỉnh (1835-1836)");
  const [sourceDaiNam, setSourceDaiNam] = useState(true);
  const [sourceHoiDien, setSourceHoiDien] = useState(true);
  const [claimStatus, setClaimStatus] = useState<"verified" | "unreviewed" | "disputed">("verified");

  // Phase 3: Media
  const [mediaVariant, setMediaVariant] = useState<"2d_rubbing" | "3d_model">("2d_rubbing");
  const [rubbingAsset, setRubbingAsset] = useState("/assets/ban-duc-noi/cao_dinh/long.jpg");

  // Phase 4: Inquiry Activities (4 Sequential Stations: 5m, 15m, 15m, 10m)
  const [act1Name, setAct1Name] = useState("Khởi động: Kích hoạt tri thức nền & quan sát bản dập");
  const [act2Name, setAct2Name] = useState("Khảo sát: Đối chiếu hiện vật với chép sử Đại Nam Thực Lục");
  const [act3Name, setAct3Name] = useState("Thảo luận: Phân tích tư tưởng độc lập tự chủ và quyền uy");
  const [act4Name, setAct4Name] = useState("Đánh giá: Vé ra cửa (Exit Ticket) & Tự lượng giá Rubric");

  // Phase 5: Assessment & Rubric
  const [rubricScale, setRubricScale] = useState("4 Mức độ (0-3: Chưa đạt, Đạt cơ sở, Khá, Xuất sắc)");
  const [exitTicketPrompt, setExitTicketPrompt] = useState(
    "Dựa trên hình ảnh bản dập và đoạn chép sử, em hãy viết 5-7 câu giải thích vì sao hình tượng Rồng trên Cao Đỉnh là biểu tượng vương quyền tối thượng.",
  );

  // Validation & Submission State
  const [isValidating, setIsValidating] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [publishSuccess, setPublishSuccess] = useState<any | null>(null);
  const [printPreviewOpen, setPrintPreviewOpen] = useState(false);

  const phases: Array<{ id: WizardPhase; label: string; number: number }> = [
    { id: "objectives", label: "Mục tiêu & Năng lực", number: 1 },
    { id: "source", label: "Hiện vật & Sử liệu", number: 2 },
    { id: "media", label: "Học liệu 2D/3D", number: 3 },
    { id: "inquiry", label: "Tiến trình 45 phút", number: 4 },
    { id: "assessment", label: "Đánh giá & Phiếu in", number: 5 },
  ];

  const handleNext = () => {
    const idx = phases.findIndex((p) => p.id === currentPhase);
    if (idx < phases.length - 1) {
      setCurrentPhase(phases[idx + 1].id);
      setValidationError(null);
    }
  };

  const handlePrev = () => {
    const idx = phases.findIndex((p) => p.id === currentPhase);
    if (idx > 0) {
      setCurrentPhase(phases[idx - 1].id);
      setValidationError(null);
    }
  };

  const handleValidateAndPublish = async () => {
    // Negative Abuse Enforcement: Reject unreviewed or disputed claims!
    if (claimStatus !== "verified") {
      setValidationError(
        "LỖI THẨM ĐỊNH LỊCH SỬ (HTTP 422 LESSON_PLAN_UNVERIFIED_CLAIMS): Bài học không thể xuất bản khi sử liệu hoặc luận điểm chưa được chuyên gia phê duyệt (trạng thái: unreviewed/disputed).",
      );
      return;
    }

    if (!sourceDaiNam && !sourceHoiDien) {
      setValidationError(
        "LỖI TƯ LIỆU: Bài học lịch sử 45 phút bắt buộc phải có ít nhất 1 nguồn sử liệu gốc (Đại Nam Thực Lục hoặc Hội Điển Sự Lệ).",
      );
      return;
    }

    setIsPublishing(true);
    setValidationError(null);

    try {
      // Mock / API call simulation payload
      const mockResult = {
        id: "plan-45m-" + Date.now(),
        title,
        topic,
        target_grade: targetGrade,
        duration_minutes: durationMinutes,
        curriculum_framework: curriculumFramework,
        media_variant: mediaVariant,
        status: "published",
        content_validation_status: "valid",
        published_at: new Date().toISOString(),
        printable_handout: {
          header: {
            title: "PHIẾU HỌC TẬP KHẢO CỨU DI SẢN (45 PHÚT)",
            framework: curriculumFramework,
            topic,
          },
          stations: [
            { name: act1Name, duration: "5 phút" },
            { name: act2Name, duration: "15 phút" },
            { name: act3Name, duration: "15 phút" },
            { name: act4Name, duration: "10 phút" },
          ],
          rubric_scale: rubricScale,
          exit_ticket: exitTicketPrompt,
          anti_abuse_seal: "SEAL_V5_APPROVED",
        },
      };

      setPublishSuccess(mockResult);
      if (onSuccess) onSuccess(mockResult);
    } catch (err: any) {
      setValidationError(err?.message || "Không thể xuất bản giáo án.");
    } finally {
      setIsPublishing(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-3xl p-0 gap-0 border-border/80 bg-background/95 backdrop-blur-xl">
        <DialogHeader className="p-5 pb-3 border-b border-border/60">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge className="bg-primary/10 text-primary border-primary/20 text-xs font-semibold gap-1 py-0.5 px-2.5">
                <Sparkles className="size-3.5" />
                <span>Wizard Sư Phạm 45 Phút (CV 5512/BGDĐT)</span>
              </Badge>
              <Badge variant="outline" className="text-[10px]">
                Thời lượng: 45 phút
              </Badge>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-7 w-7 p-0 rounded-full text-muted-foreground hover:text-foreground"
            >
              <X className="size-4" />
            </Button>
          </div>
          <DialogTitle className="font-serif text-xl text-foreground mt-2">
            Thiết Kế Giáo Án Di Sản 45 Phút Chuẩn Sư Phạm
          </DialogTitle>
          <DialogDescription className="text-xs text-muted-foreground">
            Quy trình 5 bước: Mục tiêu & Năng lực ➔ Hiện vật & Sử liệu ➔ Học liệu 2D/3D ➔ Tiến trình 4 hoạt động ➔ Đánh giá & Xuất phiếu in A4.
          </DialogDescription>

          {/* Stepper Navigation */}
          <div className="grid grid-cols-5 gap-1 pt-3">
            {phases.map((p) => {
              const isActive = p.id === currentPhase;
              const isPast =
                phases.findIndex((x) => x.id === currentPhase) >
                phases.findIndex((x) => x.id === p.id);

              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => {
                    setCurrentPhase(p.id);
                    setValidationError(null);
                  }}
                  className={cn(
                    "text-left p-2 rounded-lg border transition-all text-[11px]",
                    isActive
                      ? "border-primary bg-primary/10 text-primary font-semibold"
                      : isPast
                        ? "border-border/80 bg-muted/30 text-foreground"
                        : "border-transparent text-muted-foreground opacity-60",
                  )}
                >
                  <div className="flex items-center gap-1.5">
                    <span
                      className={cn(
                        "size-4 rounded-full flex items-center justify-center text-[10px] shrink-0",
                        isActive
                          ? "bg-primary text-primary-foreground font-bold"
                          : isPast
                            ? "bg-muted text-foreground"
                            : "bg-muted/50 text-muted-foreground",
                      )}
                    >
                      {isPast ? <Check className="size-2.5" /> : p.number}
                    </span>
                    <span className="truncate">{p.label}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </DialogHeader>

        {/* Validation Error Banner */}
        {validationError && (
          <div className="mx-5 mt-4 rounded-xl border border-rose-500/40 bg-rose-500/10 p-3 text-xs text-rose-800 dark:text-rose-300 flex items-start gap-2.5 animate-in fade-in">
            <ShieldAlert className="size-4 shrink-0 mt-0.5 text-rose-600 dark:text-rose-400" />
            <div className="space-y-0.5">
              <span className="font-bold">Cảnh Báo Thẩm Định Sử Liệu:</span>
              <p className="leading-relaxed opacity-90">{validationError}</p>
            </div>
          </div>
        )}

        {/* Success Modal / Banner */}
        {publishSuccess && (
          <div className="mx-5 mt-4 rounded-xl border border-emerald-500/40 bg-emerald-500/10 p-4 text-xs text-emerald-800 dark:text-emerald-300 flex flex-col gap-2 animate-in fade-in">
            <div className="flex items-center gap-2 font-bold text-sm">
              <ShieldCheck className="size-5 text-emerald-600 dark:text-emerald-400" />
              <span>Giáo Án Đã Xuất Bản Thành Công Chuẩn 45 Phút!</span>
            </div>
            <p className="opacity-90">
              Giáo án &ldquo;{publishSuccess.title}&rdquo; đã được khóa thẩm định cùng nguồn sử liệu chính thức. Phiếu học tập thực địa A4 đã sẵn sàng để in ấn và phát cho học sinh.
            </p>
            <div className="flex items-center gap-2 pt-1">
              <Button
                size="sm"
                variant="outline"
                onClick={() => setPrintPreviewOpen(true)}
                className="text-xs h-7 gap-1 border-emerald-500/30 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-500/10"
              >
                <Printer className="size-3" />
                <span>Xem Phiếu In A4 (Student Handout)</span>
              </Button>
            </div>
          </div>
        )}

        {/* Phase Content Body */}
        <div className="p-5 max-h-[55vh] overflow-y-auto space-y-4 text-xs">
          {/* PHASE 1: Objectives & Framework */}
          {currentPhase === "objectives" && (
            <div className="space-y-4 animate-in fade-in">
              <div className="space-y-1.5">
                <label className="font-bold text-foreground block">
                  Tiêu đề giáo án (45 phút):
                </label>
                <Input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Ví dụ: Chuyên đề khảo sát hình tượng Rồng trên Cao Đỉnh"
                  className="h-9 text-xs rounded-xl"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <label className="font-bold text-foreground block">
                  Chủ đề di sản trọng tâm:
                </label>
                <Input
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="Ví dụ: Ý nghĩa biểu tượng vương quyền và chủ quyền quốc gia thời Nguyễn"
                  className="h-9 text-xs rounded-xl"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-medium text-muted-foreground block">
                    Khối lớp áp dụng:
                  </label>
                  <Input
                    value={targetGrade}
                    onChange={(e) => setTargetGrade(e.target.value)}
                    className="h-8 text-xs font-mono"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-medium text-muted-foreground block">
                    Khung chương trình:
                  </label>
                  <Input
                    value={curriculumFramework}
                    onChange={(e) => setCurriculumFramework(e.target.value)}
                    className="h-8 text-xs font-mono"
                  />
                </div>
              </div>

              <div className="rounded-xl border border-border/70 bg-secondary/15 p-3 space-y-2">
                <span className="font-bold text-foreground block">
                  4 Năng lực lịch sử cốt lõi (S1 - S4):
                </span>
                <ul className="space-y-1.5 text-muted-foreground">
                  <li className="flex items-start gap-1.5">
                    <CheckCircle2 className="size-3.5 text-primary shrink-0 mt-0.5" />
                    <span><strong className="text-foreground">S1 (Không gian):</strong> Xác định vị trí phù điêu trên Cửu Đỉnh và không gian Kinh thành Huế.</span>
                  </li>
                  <li className="flex items-start gap-1.5">
                    <CheckCircle2 className="size-3.5 text-primary shrink-0 mt-0.5" />
                    <span><strong className="text-foreground">S2 (Thời gian):</strong> Niên đại đúc đỉnh (1835-1836) và các mốc lịch sử vương triều.</span>
                  </li>
                  <li className="flex items-start gap-1.5">
                    <CheckCircle2 className="size-3.5 text-primary shrink-0 mt-0.5" />
                    <span><strong className="text-foreground">S3 (Sử liệu):</strong> Trích dẫn đối chiếu Đại Nam Thực Lục Chính Biên & Khâm Định Hội Điển.</span>
                  </li>
                  <li className="flex items-start gap-1.5">
                    <CheckCircle2 className="size-3.5 text-primary shrink-0 mt-0.5" />
                    <span><strong className="text-foreground">S4 (Lập luận):</strong> Phân tích biểu tượng vương quyền, tính thống nhất của non sông.</span>
                  </li>
                </ul>
              </div>
            </div>
          )}

          {/* PHASE 2: Object & Sources */}
          {currentPhase === "source" && (
            <div className="space-y-4 animate-in fade-in">
              <div className="space-y-1.5">
                <label className="font-bold text-foreground block">
                  Đối tượng hiện vật bảo vật quốc gia liên kết:
                </label>
                <select
                  value={selectedRelic}
                  onChange={(e) => setSelectedRelic(e.target.value)}
                  className="w-full h-9 rounded-xl border border-input bg-background px-3 text-xs"
                >
                  <option value="cao-dinh-long">Long (Rồng) — Cao Đỉnh (1835-1836)</option>
                  <option value="nhan-dinh-hoa-mai">Hoa Mai — Nhân Đỉnh (1835-1836)</option>
                  <option value="chuong-dinh-phuong-hoang">Phượng Hoàng — Chương Đỉnh (1835-1836)</option>
                  <option value="anh-dinh-su-tu">Sư Tử — Anh Đỉnh (1835-1836)</option>
                </select>
              </div>

              <div className="space-y-2 rounded-xl border border-border/70 bg-secondary/15 p-3">
                <span className="font-bold text-foreground block">
                  Nguồn sử liệu chính thống liên kết:
                </span>
                <div className="space-y-2">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={sourceDaiNam}
                      onChange={(e) => setSourceDaiNam(e.target.checked)}
                      className="rounded border-border text-primary"
                    />
                    <span><strong>Đại Nam Thực Lục Chính Biên</strong> — Quốc sử quán triều Nguyễn (1848), Đệ nhị kỷ, quyển 154</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={sourceHoiDien}
                      onChange={(e) => setSourceHoiDien(e.target.checked)}
                      className="rounded border-border text-primary"
                    />
                    <span><strong>Khâm Định Đại Nam Hội Điển Sự Lệ</strong> — Nội các triều Nguyễn (1851), Quyển 214, Công bộ</span>
                  </label>
                </div>
              </div>

              {/* Epistemic / Verification Guardrail Setting */}
              <div className="space-y-2 rounded-xl border border-border/70 bg-muted/20 p-3">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-foreground">
                    Trạng thái thẩm định luận điểm lịch sử (Epistemic Status):
                  </span>
                  <Badge
                    variant="outline"
                    className={cn(
                      "text-[10px]",
                      claimStatus === "verified"
                        ? "text-emerald-600 border-emerald-500/30 bg-emerald-500/10"
                        : "text-amber-600 border-amber-500/30 bg-amber-500/10",
                    )}
                  >
                    {claimStatus === "verified" ? "Đã thẩm định (Verified)" : "Chưa kiểm chứng (Unreviewed)"}
                  </Badge>
                </div>
                <p className="text-[11px] text-muted-foreground">
                  Hệ thống thực thi nguyên tắc History-First: Bài học bắt buộc phải dựa trên chứng cứ đã thẩm định.
                </p>
                <div className="grid grid-cols-3 gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => {
                      setClaimStatus("verified");
                      setValidationError(null);
                    }}
                    className={cn(
                      "py-1.5 px-2 rounded-lg border text-center font-medium transition-all",
                      claimStatus === "verified"
                        ? "border-emerald-500 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 font-bold"
                        : "border-border text-muted-foreground hover:bg-muted",
                    )}
                  >
                    Thẩm định (Verified)
                  </button>
                  <button
                    type="button"
                    onClick={() => setClaimStatus("unreviewed")}
                    className={cn(
                      "py-1.5 px-2 rounded-lg border text-center font-medium transition-all",
                      claimStatus === "unreviewed"
                        ? "border-amber-500 bg-amber-500/10 text-amber-700 dark:text-amber-300 font-bold"
                        : "border-border text-muted-foreground hover:bg-muted",
                    )}
                  >
                    Chưa thẩm định (Unreviewed)
                  </button>
                  <button
                    type="button"
                    onClick={() => setClaimStatus("disputed")}
                    className={cn(
                      "py-1.5 px-2 rounded-lg border text-center font-medium transition-all",
                      claimStatus === "disputed"
                        ? "border-rose-500 bg-rose-500/10 text-rose-700 dark:text-rose-300 font-bold"
                        : "border-border text-muted-foreground hover:bg-muted",
                    )}
                  >
                    Đang tranh cãi (Disputed)
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* PHASE 3: Media (2D Rubbing vs 3D Model) */}
          {currentPhase === "media" && (
            <div className="space-y-4 animate-in fade-in">
              <div className="space-y-1.5">
                <label className="font-bold text-foreground block">
                  Định dạng học liệu trực quan:
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setMediaVariant("2d_rubbing")}
                    className={cn(
                      "p-3 rounded-xl border text-left space-y-1 transition-all",
                      mediaVariant === "2d_rubbing"
                        ? "border-primary bg-primary/10 text-primary font-bold shadow-2xs"
                        : "border-border text-muted-foreground hover:bg-muted",
                    )}
                  >
                    <div className="flex items-center gap-1.5 font-bold">
                      <FileText className="size-4" />
                      <span>Bản dập 2D (2D Rubbing)</span>
                    </div>
                    <p className="text-[11px] font-normal opacity-85">
                      Chuẩn ảnh đen trắng độ nét cao, tối ưu cho lớp học ngoại thành hoặc in ấn ra giấy A4.
                    </p>
                  </button>

                  <button
                    type="button"
                    onClick={() => setMediaVariant("3d_model")}
                    className={cn(
                      "p-3 rounded-xl border text-left space-y-1 transition-all",
                      mediaVariant === "3d_model"
                        ? "border-primary bg-primary/10 text-primary font-bold shadow-2xs"
                        : "border-border text-muted-foreground hover:bg-muted",
                    )}
                  >
                    <div className="flex items-center gap-1.5 font-bold">
                      <Layers className="size-4" />
                      <span>Mô hình 3D (Interactive GLB)</span>
                    </div>
                    <p className="text-[11px] font-normal opacity-85">
                      Tương tác xoay 360 độ, kiểm tra các tầng chạm khắc và toạ độ nổi trên thân đỉnh.
                    </p>
                  </button>
                </div>
              </div>

              <div className="rounded-xl border border-border/70 bg-secondary/15 p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-foreground">
                    Đường dẫn học liệu bản dập (2D Fallback):
                  </span>
                  <Badge variant="outline" className="text-[10px]">
                    100% Sẵn sàng ngoại tuyến
                  </Badge>
                </div>
                <Input
                  value={rubbingAsset}
                  onChange={(e) => setRubbingAsset(e.target.value)}
                  className="h-8 text-xs font-mono"
                />
                <p className="text-[11px] text-muted-foreground">
                  Đảm bảo học sinh không có thiết bị WebGL vẫn hoàn thành trọn vẹn mục tiêu bài học qua bản dập 2D.
                </p>
              </div>
            </div>
          )}

          {/* PHASE 4: 45-Minute Sequential Inquiry Flow */}
          {currentPhase === "inquiry" && (
            <div className="space-y-3 animate-in fade-in">
              <div className="flex items-center justify-between">
                <span className="font-bold text-foreground">
                  Tiến trình 4 hoạt động nối tiếp (Tổng 45 phút):
                </span>
                <Badge variant="secondary" className="text-[10px] font-mono">
                  5m + 15m + 15m + 10m = 45m
                </Badge>
              </div>

              {/* Station 1 */}
              <div className="rounded-xl border border-border/70 bg-card p-3 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-foreground flex items-center gap-1.5">
                    <Clock className="size-3.5 text-primary" />
                    <span>Hoạt động 1: Khởi động (5 phút)</span>
                  </span>
                  <Badge variant="outline" className="text-[10px]">5 phút</Badge>
                </div>
                <Input
                  value={act1Name}
                  onChange={(e) => setAct1Name(e.target.value)}
                  className="h-8 text-xs"
                />
              </div>

              {/* Station 2 */}
              <div className="rounded-xl border border-border/70 bg-card p-3 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-foreground flex items-center gap-1.5">
                    <Clock className="size-3.5 text-primary" />
                    <span>Hoạt động 2: Khảo sát hiện vật & sử liệu (15 phút)</span>
                  </span>
                  <Badge variant="outline" className="text-[10px]">15 phút</Badge>
                </div>
                <Input
                  value={act2Name}
                  onChange={(e) => setAct2Name(e.target.value)}
                  className="h-8 text-xs"
                />
              </div>

              {/* Station 3 */}
              <div className="rounded-xl border border-border/70 bg-card p-3 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-foreground flex items-center gap-1.5">
                    <Clock className="size-3.5 text-primary" />
                    <span>Hoạt động 3: Thảo luận sâu & lập luận (15 phút)</span>
                  </span>
                  <Badge variant="outline" className="text-[10px]">15 phút</Badge>
                </div>
                <Input
                  value={act3Name}
                  onChange={(e) => setAct3Name(e.target.value)}
                  className="h-8 text-xs"
                />
              </div>

              {/* Station 4 */}
              <div className="rounded-xl border border-border/70 bg-card p-3 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-foreground flex items-center gap-1.5">
                    <Clock className="size-3.5 text-primary" />
                    <span>Hoạt động 4: Đánh giá & Vé ra cửa (10 phút)</span>
                  </span>
                  <Badge variant="outline" className="text-[10px]">10 phút</Badge>
                </div>
                <Input
                  value={act4Name}
                  onChange={(e) => setAct4Name(e.target.value)}
                  className="h-8 text-xs"
                />
              </div>
            </div>
          )}

          {/* PHASE 5: Assessment & Printable Handout */}
          {currentPhase === "assessment" && (
            <div className="space-y-4 animate-in fade-in">
              <div className="space-y-1.5">
                <label className="font-bold text-foreground block">
                  Thang đo Rubric chuẩn hoá:
                </label>
                <Input
                  value={rubricScale}
                  onChange={(e) => setRubricScale(e.target.value)}
                  className="h-9 text-xs rounded-xl"
                />
              </div>

              <div className="space-y-1.5">
                <label className="font-bold text-foreground block">
                  Nội dung câu hỏi Vé ra cửa (Exit Ticket):
                </label>
                <textarea
                  value={exitTicketPrompt}
                  onChange={(e) => setExitTicketPrompt(e.target.value)}
                  rows={3}
                  className="w-full rounded-xl border border-input bg-background p-3 text-xs leading-relaxed focus:border-primary focus:outline-none"
                />
              </div>

              <div className="rounded-xl border border-border/70 bg-secondary/15 p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-foreground flex items-center gap-1.5">
                    <Printer className="size-4 text-primary" />
                    <span>Tạo Phiếu In Thực Địa A4 (Printable Handout):</span>
                  </span>
                  <Badge className="bg-primary/10 text-primary border-primary/20 text-[10px]">
                    Chuẩn in A4 2 trang
                  </Badge>
                </div>
                <p className="text-[11px] text-muted-foreground">
                  Hệ thống tự động đồng bộ tiêu đề, bảng đối chiếu sử liệu, 4 trạm hoạt động và phiếu tự lượng giá Rubric sang bản in A4 tiêu chuẩn.
                </p>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => setPrintPreviewOpen(true)}
                  className="text-xs h-7 gap-1 border-primary/30 text-primary font-medium"
                >
                  <Eye className="size-3" />
                  <span>Xem trước định dạng in ấn A4</span>
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer Controls */}
        <DialogFooter className="p-4 border-t border-border/60 flex items-center justify-between gap-2">
          <div>
            {currentPhase !== "objectives" && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={handlePrev}
                className="text-xs gap-1"
              >
                <ChevronLeft className="size-3.5" />
                <span>Quay lại</span>
              </Button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onClose}
              className="text-xs"
            >
              Đóng
            </Button>

            {currentPhase !== "assessment" ? (
              <Button
                type="button"
                size="sm"
                onClick={handleNext}
                className="text-xs bg-primary text-primary-foreground font-semibold px-4 gap-1"
              >
                <span>Tiếp theo</span>
                <ChevronRight className="size-3.5" />
              </Button>
            ) : (
              <Button
                type="button"
                size="sm"
                onClick={handleValidateAndPublish}
                disabled={isPublishing}
                className="text-xs bg-primary text-primary-foreground font-semibold px-4 gap-1.5 shadow-xs"
              >
                <ShieldCheck className="size-3.5" />
                <span>{isPublishing ? "Đang xuất bản..." : "Xuất Bản Giáo Án 45 Phút"}</span>
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>

      {/* Embedded Printable Handout A4 Preview Dialog */}
      {printPreviewOpen && (
        <Dialog open={printPreviewOpen} onOpenChange={setPrintPreviewOpen}>
          <DialogContent className="max-w-4xl p-6 bg-white text-zinc-900 border border-zinc-200 overflow-y-auto max-h-[85vh]">
            <DialogHeader className="border-b pb-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-serif font-bold text-lg text-zinc-900">
                    SỞ GIÁO DỤC VÀ ĐÀO TẠO THỪA THIÊN HUẾ
                  </h3>
                  <p className="text-xs text-zinc-600">TRƯỜNG THPT: ..............................................................</p>
                </div>
                <div className="text-right text-xs text-zinc-500 font-mono">
                  MÃ BÀI HỌC: CV5512-45M-CD
                </div>
              </div>
              <DialogTitle className="font-serif text-xl font-bold text-center mt-3 text-zinc-900 uppercase">
                PHIẾU HỌC TẬP KHẢO CỨU DI SẢN (45 PHÚT)
              </DialogTitle>
              <DialogDescription className="text-center text-xs text-zinc-700 italic">
                Chuyên đề: {title} — {selectedUrn}
              </DialogDescription>
            </DialogHeader>

            <div className="py-4 space-y-4 text-xs font-sans">
              <div className="grid grid-cols-2 gap-4 border p-3 rounded-md bg-zinc-50">
                <div>Họ và tên: ..............................................................</div>
                <div>Lớp: ......................... Nhóm: .........................</div>
              </div>

              {/* Stations */}
              <div className="space-y-3">
                <div className="border p-3 rounded-md">
                  <div className="font-bold text-zinc-900">{act1Name} (5 phút)</div>
                  <p className="text-zinc-600 italic">Quan sát phù điêu trên đỉnh và ghi chép 3 đặc điểm nổi bật:</p>
                  <div className="h-12 border-b border-dashed mt-2"></div>
                </div>

                <div className="border p-3 rounded-md">
                  <div className="font-bold text-zinc-900">{act2Name} (15 phút)</div>
                  <p className="text-zinc-600 italic">Đối chiếu lời chép sử trong Đại Nam Thực Lục Chính Biên với hình tượng hiện vật:</p>
                  <div className="h-16 border-b border-dashed mt-2"></div>
                </div>

                <div className="border p-3 rounded-md">
                  <div className="font-bold text-zinc-900">{act3Name} (15 phút)</div>
                  <p className="text-zinc-600 italic">Tổng hợp luận điểm nhóm về ý nghĩa biểu tượng quyền uy vương triều:</p>
                  <div className="h-16 border-b border-dashed mt-2"></div>
                </div>

                <div className="border p-3 rounded-md bg-zinc-50">
                  <div className="font-bold text-zinc-900">{act4Name} — Vé Ra Cửa (Exit Ticket) (10 phút)</div>
                  <p className="text-zinc-700 font-medium mt-1">{exitTicketPrompt}</p>
                  <div className="h-20 border-b border-dashed mt-2"></div>
                </div>
              </div>
            </div>

            <DialogFooter className="border-t pt-4 flex items-center justify-between">
              <span className="text-[11px] text-zinc-500 font-mono">SEAL_V5_APPROVED • In ấn 2 mặt A4</span>
              <Button size="sm" onClick={() => window.print()} className="gap-1.5 text-xs bg-zinc-900 text-white">
                <Printer className="size-3.5" />
                <span>In Phiếu Học Tập</span>
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </Dialog>
  );
}
