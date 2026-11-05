"use client";

import React, { useState } from "react";
import {
  AlertCircle,
  Award,
  BookOpen,
  Check,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock,
  Copy,
  Download,
  ExternalLink,
  FileCheck2,
  FileText,
  GraduationCap,
  HelpCircle,
  Layers,
  LifeBuoy,
  MessageSquare,
  RotateCcw,
  Send,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Video,
  X,
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

export interface TeacherOnboardingSupportModalProps {
  isOpen: boolean;
  onClose: () => void;
  isVerified?: boolean;
  schoolName?: string;
  onCloneTemplate?: (templateId: string) => void;
}

export type CenterTab = "tour" | "sample_templates" | "support_tickets" | "training_resources";

interface TourStepItem {
  id: string;
  title: string;
  category: string;
  summary: string;
  actionGuide: string;
  regulatoryNote: string;
}

const TOUR_STEPS: TourStepItem[] = [
  {
    id: "welcome",
    title: "1. Định hướng Sư phạm & Khám phá Cửu Đỉnh Huế",
    category: "Khởi động & Bối cảnh",
    summary:
      "Chào mừng thầy cô đến với Hệ thống LMS Di sản Cửu Đỉnh Đại Nội Huế. Nền tảng được thiết kế hỗ trợ giáo viên THCS và THPT triển khai dạy học tích hợp di sản theo phương pháp nêu vấn đề (Inquiry-based Learning).",
    actionGuide:
      "Làm quen với giao diện Bản đồ thực địa, Thao tác khảo sát dập nổi 2D băng thông thấp và tương tác mô hình 3D số hóa 9 đỉnh đồng triều Nguyễn.",
    regulatoryNote: "Chương trình Giáo dục Phổ thông 2018 — Hoạt động trải nghiệm & Giáo dục địa phương.",
  },
  {
    id: "curriculum",
    title: "2. Chuẩn Kế hoạch bài dạy 45 phút theo Công văn 5512/BGDĐT",
    category: "Khung bài dạy chính khóa",
    summary:
      "Mỗi bài học thực địa được cấu trúc chuẩn hóa qua 4 pha nối tiếp: Khởi động (5m), Khảo sát tư liệu (15m), Thảo luận giải quyết vấn đề (15m), và Đánh giá kết thúc / Vé ra cửa (10m).",
    actionGuide:
      "Sử dụng công cụ 'Soạn giáo án 45 phút' trong Bảng giáo viên để xuất hồ sơ bài dạy và phiếu học tập in A4 cho học sinh.",
    regulatoryNote: "Quy định cấu trúc kế hoạch bài dạy theo Công văn 5512/BGDĐT của Bộ GD&ĐT.",
  },
  {
    id: "sample_templates",
    title: "3. Khai thác Mẫu Giáo án Tham khảo (SAMPLE TEMPLATE)",
    category: "Học liệu mẫu",
    summary:
      "Hệ thống cung cấp các mẫu bài giảng tham khảo đã được hội đồng chuyên môn thẩm định. Các mẫu này được gắn nhãn [SAMPLE TEMPLATE] và disclaimer rõ ràng để giáo viên tham khảo và sao chép.",
    actionGuide:
      "Chuyển sang tab 'Mẫu Giáo Án Tham Khảo' để xem chi tiết mẫu Cao Đỉnh, Minh Đỉnh và sao chép thành bản thảo cá nhân.",
    regulatoryNote: "Mẫu giáo án phục vụ mục đích tập huấn nội bộ, không thay thế hồ sơ thực địa được duyệt của nhà trường.",
  },
  {
    id: "privacy",
    title: "4. Bảo vệ Dữ liệu Học sinh & Chấp thuận của Phụ huynh",
    category: "An toàn thông tin & Pháp lý",
    summary:
      "Hệ thống tuân thủ nghiêm ngặt Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân. Học sinh dưới 16 tuổi cần có sự đồng thuận của phụ huynh (Guardian Consent) trước khi ghi nhận dữ liệu đánh giá thực địa.",
    actionGuide:
      "Chỉ tài khoản giáo viên đã được nhà trường xác thực mới được truy cập dữ liệu PII học sinh thật và bảng điểm trực tiếp. Tài khoản dùng thử (Demo) chỉ xem dữ liệu mẫu ẩn danh.",
    regulatoryNote: "Nghị định 13/2023/NĐ-CP — Điều 20: Xử lý dữ liệu cá nhân của trẻ em.",
  },
  {
    id: "rubric",
    title: "5. Đánh giá Năng lực Tư duy Lịch sử theo Rubric S1-S4",
    category: "Đo lường & Đánh giá",
    summary:
      "Chấm điểm bài nộp của học sinh theo 4 tiêu chí năng lực lịch sử cốt lõi: S1 (Không gian - Hiện vật), S2 (Thời gian - Bối cảnh), S3 (Sử liệu - Khai thác tư liệu), và S4 (Lập luận - Đánh giá).",
    actionGuide:
      "Chấm điểm trực tiếp bằng thang điểm 0-3 cho từng tiêu chí, xem biểu đồ Radar cá nhân hóa và xuất bảng điểm UTF-8 BOM Excel.",
    regulatoryNote: "Thang đo chuẩn hóa năng lực tìm hiểu lịch sử theo khung đánh giá GDPT 2018.",
  },
];

interface SampleTemplateCard {
  id: string;
  title: string;
  topic: string;
  targetGrade: string;
  duration: string;
  variant: string;
  disclaimer: string;
}

const SAMPLE_TEMPLATES_DATA: SampleTemplateCard[] = [
  {
    id: "sample-cao-dinh-dragon-45min",
    title: "Mẫu Giáo án 45 phút: Khảo sát hình tượng Rồng trên Cao Đỉnh (CV 5512)",
    topic: "Ý nghĩa biểu tượng vương quyền thời Nguyễn & Khắc họa trên Cửu Đỉnh",
    targetGrade: "Lớp 10 THPT",
    duration: "45 phút",
    variant: "2D Dập nổi băng thông thấp",
    disclaimer:
      "SAMPLE TEMPLATE - Mẫu giáo án tham khảo phục vụ tập huấn giáo viên, không thay thế hồ sơ thực địa chính thức.",
  },
  {
    id: "sample-minh-dinh-maritime-45min",
    title: "Mẫu Chuyên đề: Biển đảo & Hàng hải qua hình tượng Đông Hải trên Minh Đỉnh",
    topic: "Chủ quyền lãnh thổ biển đảo và kinh tế hàng hải thời Nguyễn qua Cửu Đỉnh",
    targetGrade: "Lớp 11 THPT",
    duration: "45 phút",
    variant: "Mô hình 3D số hóa & Bản dập",
    disclaimer:
      "SAMPLE TEMPLATE - Mẫu giáo án tham khảo phục vụ tập huấn giáo viên, không thay thế hồ sơ thực địa chính thức.",
  },
  {
    id: "sample-flora-fauna-nhan-thuan-dinh-45min",
    title: "Mẫu Tiết thực địa: So sánh hệ động thực vật trên Nhân Đỉnh và Thuần Đỉnh",
    topic: "Sản vật địa phương và bức tranh sinh thái Đại Nam thế kỷ XIX",
    targetGrade: "Lớp 8 THCS",
    duration: "45 phút",
    variant: "2D Dập nổi thực địa",
    disclaimer:
      "SAMPLE TEMPLATE - Mẫu giáo án tham khảo phục vụ tập huấn giáo viên, không thay thế hồ sơ thực địa chính thức.",
  },
];

interface SupportTicketMock {
  id: string;
  code: string;
  subject: string;
  category: string;
  priority: string;
  status: "open" | "in_progress" | "resolved";
  createdAt: string;
  message: string;
  latestResponse?: string;
}

const INITIAL_MOCK_TICKETS: SupportTicketMock[] = [
  {
    id: "tkt-01",
    code: "TKT-202611-8A1",
    subject: "Yêu cầu cấp mã xác thực trường học THPT Chuyên Quốc Học Huế",
    category: "Xác thực trường học",
    priority: "high",
    status: "in_progress",
    createdAt: "2026-11-04T10:15:00Z",
    message: "Kính gửi BQT, tôi là giáo viên Sử tổ THPT, cần xác thực tài khoản để truy cập sổ điểm lớp 10A1.",
    latestResponse: "Ban Quản Trị đã tiếp nhận hồ sơ giới thiệu từ Ban Giám Hiệu và đang đối soát danh sách.",
  },
  {
    id: "tkt-02",
    code: "TKT-202611-3C9",
    subject: "Hướng dẫn cấu hình phiếu học tập in A4 khi máy in trường không hỗ trợ màu",
    category: "Kỹ thuật / In ấn",
    priority: "normal",
    status: "resolved",
    createdAt: "2026-11-02T14:30:00Z",
    message: "Hệ thống có hỗ trợ chế độ tương phản cao đơn sắc (Grayscale) cho bản dập nổi không?",
    latestResponse: "Hệ thống đã hỗ trợ chế độ Grayscale độ tương phản cao 300 DPI tối ưu cho in máy photocopy.",
  },
];

export default function TeacherOnboardingSupportModal({
  isOpen,
  onClose,
  isVerified = true,
  schoolName = "Trường THPT Chuyên Quốc Học Huế",
  onCloneTemplate,
}: TeacherOnboardingSupportModalProps) {
  const [activeTab, setActiveTab] = useState<CenterTab>("tour");
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<string[]>(["welcome"]);

  // Ticket Form State
  const [ticketSubject, setTicketSubject] = useState("");
  const [ticketCategory, setTicketCategory] = useState("pedagogical_guidance");
  const [ticketPriority, setTicketPriority] = useState("normal");
  const [ticketMessage, setTicketMessage] = useState("");
  const [ticketsList, setTicketsList] = useState<SupportTicketMock[]>(INITIAL_MOCK_TICKETS);
  const [ticketSuccessMessage, setTicketSuccessMessage] = useState<string | null>(null);
  const [clonedSuccessMessage, setClonedSuccessMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const currentStep = TOUR_STEPS[currentStepIndex];
  const isCurrentStepDone = completedSteps.includes(currentStep.id);

  const handleNextStep = () => {
    if (!completedSteps.includes(currentStep.id)) {
      setCompletedSteps((prev) => [...prev, currentStep.id]);
    }
    if (currentStepIndex < TOUR_STEPS.length - 1) {
      setCurrentStepIndex(currentStepIndex + 1);
    }
  };

  const handlePrevStep = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(currentStepIndex - 1);
    }
  };

  const handleToggleCurrentStep = () => {
    if (isCurrentStepDone) {
      setCompletedSteps((prev) => prev.filter((s) => s !== currentStep.id));
    } else {
      setCompletedSteps((prev) => [...prev, currentStep.id]);
    }
  };

  const handleResetTour = () => {
    setCompletedSteps([]);
    setCurrentStepIndex(0);
  };

  const handleSubmitTicket = (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticketSubject.trim() || !ticketMessage.trim()) return;

    const newTicket: SupportTicketMock = {
      id: `tkt-${Date.now()}`,
      code: `TKT-${new Date().getFullYear()}${String(new Date().getMonth() + 1).padStart(2, "0")}-${Math.random().toString(36).substring(2, 5).toUpperCase()}`,
      subject: ticketSubject.trim(),
      category: ticketCategory,
      priority: ticketPriority,
      status: "open",
      createdAt: new Date().toISOString(),
      message: ticketMessage.trim(),
    };

    setTicketsList([newTicket, ...ticketsList]);
    setTicketSubject("");
    setTicketMessage("");
    setTicketSuccessMessage(`Đã gửi yêu cầu hỗ trợ mã [${newTicket.code}]. Đội ngũ chuyên gia sẽ phản hồi trong 24h.`);
    setTimeout(() => setTicketSuccessMessage(null), 5000);
  };

  const handleClone = (tmplId: string, title: string) => {
    if (onCloneTemplate) {
      onCloneTemplate(tmplId);
    }
    setClonedSuccessMessage(`Đã tạo bản sao mẫu: "${title}". Bạn có thể chỉnh sửa trong Kế hoạch bài dạy.`);
    setTimeout(() => setClonedSuccessMessage(null), 4000);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto bg-stone-900 border-amber-800 text-stone-100 p-0 shadow-2xl">
        <DialogHeader className="p-6 pb-4 border-b border-stone-800 bg-stone-950/80 sticky top-0 z-20">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-amber-900/40 border border-amber-600/50 flex items-center justify-center text-amber-400">
                <GraduationCap className="w-5 h-5" />
              </div>
              <div>
                <DialogTitle className="text-xl font-bold text-amber-200">
                  Trung Tâm Hỗ Trợ & Tập Huấn Giáo Viên
                </DialogTitle>
                <DialogDescription className="text-xs text-stone-400">
                  Cẩm nang sư phạm, giáo án mẫu [SAMPLE TEMPLATE], tài liệu tập huấn và kênh hỗ trợ trực tiếp
                </DialogDescription>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {isVerified ? (
                <Badge className="bg-emerald-950 text-emerald-300 border-emerald-600 flex items-center gap-1.5 text-xs py-1 px-2.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  Đã xác thực ({schoolName})
                </Badge>
              ) : (
                <Badge className="bg-amber-950 text-amber-300 border-amber-600 flex items-center gap-1.5 text-xs py-1 px-2.5 animate-pulse">
                  <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
                  Chế độ Dùng thử (Demo)
                </Badge>
              )}
            </div>
          </div>

          {/* Verification Warning Alert if Unverified */}
          {!isVerified && (
            <div className="mt-3 p-3 bg-amber-950/70 border border-amber-600/60 rounded-lg flex items-start gap-2.5 text-amber-200 text-xs">
              <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div className="flex-1">
                <span className="font-semibold text-amber-300">Cảnh báo An toàn Thông tin (Nghị định 13/2023/NĐ-CP):</span>{" "}
                Tài khoản giáo viên chưa được nhà trường xác thực. Chế độ dùng thử (Demo Mode) đang kích hoạt: Thầy cô chỉ có thể xem học liệu và học sinh mẫu ẩn danh. Vui lòng gửi yêu cầu xác thực tại tab Trợ giúp để mở khóa dữ liệu thật.
              </div>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setActiveTab("support_tickets");
                  setTicketCategory("account_verification");
                  setTicketSubject(`Yêu cầu xác thực tài khoản giáo viên: ${schoolName}`);
                }}
                className="text-xs border-amber-500 text-amber-300 hover:bg-amber-900/60 shrink-0"
              >
                Gửi yêu cầu xác thực
              </Button>
            </div>
          )}

          {/* Navigation Tabs */}
          <div className="flex items-center gap-1 mt-4 border-b border-stone-800 -mb-4">
            <button
              onClick={() => setActiveTab("tour")}
              className={cn(
                "px-3.5 py-2 text-xs font-semibold rounded-t-lg transition flex items-center gap-1.5 border-b-2",
                activeTab === "tour"
                  ? "border-amber-500 text-amber-300 bg-stone-800/60"
                  : "border-transparent text-stone-400 hover:text-stone-200 hover:bg-stone-800/30"
              )}
            >
              <Sparkles className="w-3.5 h-3.5" />
              Hướng Dẫn Onboarding ({completedSteps.length}/{TOUR_STEPS.length})
            </button>
            <button
              onClick={() => setActiveTab("sample_templates")}
              className={cn(
                "px-3.5 py-2 text-xs font-semibold rounded-t-lg transition flex items-center gap-1.5 border-b-2",
                activeTab === "sample_templates"
                  ? "border-amber-500 text-amber-300 bg-stone-800/60"
                  : "border-transparent text-stone-400 hover:text-stone-200 hover:bg-stone-800/30"
              )}
            >
              <BookOpen className="w-3.5 h-3.5" />
              Mẫu Giáo Án [SAMPLE TEMPLATE]
            </button>
            <button
              onClick={() => setActiveTab("support_tickets")}
              className={cn(
                "px-3.5 py-2 text-xs font-semibold rounded-t-lg transition flex items-center gap-1.5 border-b-2",
                activeTab === "support_tickets"
                  ? "border-amber-500 text-amber-300 bg-stone-800/60"
                  : "border-transparent text-stone-400 hover:text-stone-200 hover:bg-stone-800/30"
              )}
            >
              <LifeBuoy className="w-3.5 h-3.5" />
              Gửi Yêu Cầu Hỗ Trợ
            </button>
            <button
              onClick={() => setActiveTab("training_resources")}
              className={cn(
                "px-3.5 py-2 text-xs font-semibold rounded-t-lg transition flex items-center gap-1.5 border-b-2",
                activeTab === "training_resources"
                  ? "border-amber-500 text-amber-300 bg-stone-800/60"
                  : "border-transparent text-stone-400 hover:text-stone-200 hover:bg-stone-800/30"
              )}
            >
              <FileCheck2 className="w-3.5 h-3.5" />
              Tài Liệu Tập Huấn
            </button>
          </div>
        </DialogHeader>

        {/* Tab 1: Interactive Onboarding Tour */}
        {activeTab === "tour" && (
          <div className="p-6 space-y-6">
            {/* Progress tracker */}
            <div className="bg-stone-950 p-4 rounded-xl border border-stone-800">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-stone-400 font-medium">Tiến độ hoàn thành chuyến tham quan tập huấn:</span>
                <span className="text-xs font-bold text-amber-400">
                  {Math.round((completedSteps.length / TOUR_STEPS.length) * 100)}% ({completedSteps.length}/{TOUR_STEPS.length} bước)
                </span>
              </div>
              <div className="w-full h-2 bg-stone-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-amber-600 to-amber-400 transition-all duration-300"
                  style={{ width: `${(completedSteps.length / TOUR_STEPS.length) * 100}%` }}
                />
              </div>

              {/* Step pills */}
              <div className="grid grid-cols-5 gap-2 mt-3">
                {TOUR_STEPS.map((step, idx) => {
                  const isDone = completedSteps.includes(step.id);
                  const isCurrent = idx === currentStepIndex;
                  return (
                    <button
                      key={step.id}
                      onClick={() => setCurrentStepIndex(idx)}
                      className={cn(
                        "p-2 rounded-lg text-left text-xs transition border flex items-center justify-between",
                        isCurrent
                          ? "bg-amber-950/60 border-amber-500 text-amber-200 font-semibold"
                          : isDone
                          ? "bg-stone-900 border-emerald-800/60 text-emerald-300"
                          : "bg-stone-900 border-stone-800 text-stone-400 hover:bg-stone-800"
                      )}
                    >
                      <span className="truncate">Bước {idx + 1}</span>
                      {isDone ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                      ) : (
                        <span className="w-2 h-2 rounded-full bg-stone-700 shrink-0" />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Active Step Details */}
            <div className="bg-stone-950/70 border border-amber-900/50 rounded-xl p-6 space-y-4">
              <div className="flex items-center justify-between">
                <Badge className="bg-amber-950 text-amber-300 border-amber-700 text-xs">
                  {currentStep.category}
                </Badge>
                <button
                  onClick={handleToggleCurrentStep}
                  className={cn(
                    "text-xs px-3 py-1.5 rounded-lg border transition flex items-center gap-1.5",
                    isCurrentStepDone
                      ? "bg-emerald-950 border-emerald-600 text-emerald-300"
                      : "bg-stone-800 border-stone-700 text-stone-300 hover:border-amber-500"
                  )}
                >
                  <Check className="w-3.5 h-3.5" />
                  {isCurrentStepDone ? "Đã đánh dấu hoàn thành" : "Đánh dấu hoàn thành bước này"}
                </button>
              </div>

              <h3 className="text-lg font-bold text-amber-200">{currentStep.title}</h3>
              <p className="text-stone-300 text-sm leading-relaxed">{currentStep.summary}</p>

              <div className="p-3.5 bg-stone-900/80 border border-stone-800 rounded-lg space-y-1.5">
                <div className="text-xs font-semibold text-amber-400 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Hướng dẫn thao tác thực hành:
                </div>
                <div className="text-xs text-stone-300 pl-5">{currentStep.actionGuide}</div>
              </div>

              <div className="text-xs text-stone-400 italic flex items-center gap-1.5 border-t border-stone-800 pt-3">
                <FileText className="w-3.5 h-3.5 text-stone-500" />
                Căn cứ pháp lý & quy chuẩn: {currentStep.regulatoryNote}
              </div>
            </div>

            {/* Step Controls */}
            <div className="flex items-center justify-between border-t border-stone-800 pt-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleResetTour}
                className="text-xs text-stone-400 hover:text-stone-200 flex items-center gap-1.5"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Đặt lại toàn bộ hướng dẫn
              </Button>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handlePrevStep}
                  disabled={currentStepIndex === 0}
                  className="text-xs border-stone-700 text-stone-300"
                >
                  <ChevronLeft className="w-4 h-4 mr-1" />
                  Bước trước
                </Button>
                <Button
                  size="sm"
                  onClick={handleNextStep}
                  className="text-xs bg-amber-600 hover:bg-amber-500 text-stone-950 font-semibold"
                >
                  {currentStepIndex === TOUR_STEPS.length - 1 ? "Hoàn tất tập huấn" : "Bước tiếp theo"}
                  <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Sample Lesson Templates */}
        {activeTab === "sample_templates" && (
          <div className="p-6 space-y-6">
            {clonedSuccessMessage && (
              <div className="p-3 bg-emerald-950 border border-emerald-600 rounded-lg text-emerald-200 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                {clonedSuccessMessage}
              </div>
            )}

            <div className="bg-stone-950 p-4 rounded-xl border border-stone-800 space-y-2">
              <div className="flex items-center gap-2 text-amber-300 font-semibold text-sm">
                <BookOpen className="w-4 h-4 text-amber-400" />
                Kho Học Liệu Giáo Án Mẫu [SAMPLE TEMPLATE]
              </div>
              <p className="text-xs text-stone-400 leading-relaxed">
                Các mẫu giáo án dưới đây được thiết kế mẫu theo chuẩn Công văn 5512/BGDĐT, tích hợp tư liệu dập nổi 2D và mô hình 3D Cửu Đỉnh Huế. Thầy cô có thể xem trước nội dung hoặc sao chép thành bản thảo riêng để chỉnh sửa.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {SAMPLE_TEMPLATES_DATA.map((tmpl) => (
                <div
                  key={tmpl.id}
                  className="bg-stone-950 border border-stone-800 rounded-xl p-5 space-y-3.5 flex flex-col justify-between hover:border-amber-700/60 transition"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Badge className="bg-amber-950 text-amber-300 border-amber-600 text-xs font-bold">
                        SAMPLE TEMPLATE
                      </Badge>
                      <Badge variant="outline" className="border-stone-700 text-stone-300 text-xs">
                        {tmpl.targetGrade}
                      </Badge>
                    </div>

                    <h4 className="text-sm font-bold text-amber-200 leading-snug">{tmpl.title}</h4>
                    <p className="text-xs text-stone-400 line-clamp-2">{tmpl.topic}</p>

                    <div className="grid grid-cols-2 gap-2 text-xs text-stone-300 bg-stone-900/60 p-2.5 rounded-lg border border-stone-800/80">
                      <div>
                        <span className="text-stone-500">Thời lượng:</span> {tmpl.duration}
                      </div>
                      <div>
                        <span className="text-stone-500">Tư liệu:</span> {tmpl.variant}
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3 pt-2 border-t border-stone-800/80">
                    <div className="text-[11px] text-amber-400/90 italic bg-amber-950/40 p-2 rounded border border-amber-900/40">
                      {tmpl.disclaimer}
                    </div>

                    <div className="flex items-center justify-between gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleClone(tmpl.id, tmpl.title)}
                        className="w-full text-xs border-amber-600/70 text-amber-300 hover:bg-amber-900/40 flex items-center justify-center gap-1.5"
                      >
                        <Copy className="w-3.5 h-3.5" />
                        Sao chép bài giảng mẫu này
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 3: Support Tickets */}
        {activeTab === "support_tickets" && (
          <div className="p-6 space-y-6">
            {ticketSuccessMessage && (
              <div className="p-3 bg-emerald-950 border border-emerald-600 rounded-lg text-emerald-200 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                {ticketSuccessMessage}
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Submission Form */}
              <div className="lg:col-span-6 bg-stone-950 p-5 rounded-xl border border-stone-800 space-y-4">
                <div className="text-sm font-bold text-amber-200 flex items-center gap-2">
                  <LifeBuoy className="w-4 h-4 text-amber-400" />
                  Gửi Yêu Cầu Hỗ Trợ Mới
                </div>
                <form onSubmit={handleSubmitTicket} className="space-y-3.5">
                  <div>
                    <label className="text-xs text-stone-400 block mb-1">Tiêu đề yêu cầu *</label>
                    <Input
                      value={ticketSubject}
                      onChange={(e) => setTicketSubject(e.target.value)}
                      placeholder="VD: Cần hỗ trợ cấp mã liên kết trường THPT..."
                      className="bg-stone-900 border-stone-700 text-stone-100 text-xs"
                      required
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs text-stone-400 block mb-1">Danh mục *</label>
                      <select
                        value={ticketCategory}
                        onChange={(e) => setTicketCategory(e.target.value)}
                        className="w-full bg-stone-900 border border-stone-700 rounded-md p-2 text-xs text-stone-200"
                      >
                        <option value="pedagogical_guidance">Hướng dẫn sư phạm</option>
                        <option value="curriculum_alignment">Chuẩn GDPT 2018 / CV 5512</option>
                        <option value="account_verification">Xác thực tài khoản trường học</option>
                        <option value="technical_issue">Sự cố kỹ thuật / WebGL</option>
                        <option value="rubric_scoring">Chấm điểm Rubric S1-S4</option>
                        <option value="student_privacy">Quyền riêng tư học sinh</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-xs text-stone-400 block mb-1">Mức độ ưu tiên</label>
                      <select
                        value={ticketPriority}
                        onChange={(e) => setTicketPriority(e.target.value)}
                        className="w-full bg-stone-900 border border-stone-700 rounded-md p-2 text-xs text-stone-200"
                      >
                        <option value="low">Thấp</option>
                        <option value="normal">Bình thường</option>
                        <option value="high">Cao</option>
                        <option value="urgent">Khẩn cấp</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="text-xs text-stone-400 block mb-1">Nội dung chi tiết *</label>
                    <textarea
                      value={ticketMessage}
                      onChange={(e) => setTicketMessage(e.target.value)}
                      rows={4}
                      placeholder="Mô tả cụ thể khó khăn hoặc câu hỏi của thầy cô để tổ chuyên môn hỗ trợ kịp thời..."
                      className="w-full bg-stone-900 border border-stone-700 rounded-md p-2.5 text-xs text-stone-100 placeholder:text-stone-500 focus:outline-none focus:border-amber-500"
                      required
                    />
                  </div>

                  <Button
                    type="submit"
                    className="w-full bg-amber-600 hover:bg-amber-500 text-stone-950 font-bold text-xs flex items-center justify-center gap-1.5"
                  >
                    <Send className="w-3.5 h-3.5" />
                    Gửi yêu cầu hỗ trợ ngay
                  </Button>
                </form>
              </div>

              {/* Submitted Tickets Tracker */}
              <div className="lg:col-span-6 bg-stone-950 p-5 rounded-xl border border-stone-800 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-stone-200 flex items-center gap-1.5">
                    <MessageSquare className="w-4 h-4 text-amber-400" />
                    Lịch sử yêu cầu đã gửi ({ticketsList.length})
                  </span>
                  <Badge variant="outline" className="border-stone-700 text-stone-400 text-[11px]">
                    SLA: Phản hồi trong 24h
                  </Badge>
                </div>

                <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1">
                  {ticketsList.map((tkt) => (
                    <div
                      key={tkt.id}
                      className="p-3.5 bg-stone-900/80 border border-stone-800 rounded-lg space-y-2 text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-bold text-amber-400">{tkt.code}</span>
                        <Badge
                          className={cn(
                            "text-[10px] py-0.5 px-2 font-semibold",
                            tkt.status === "resolved"
                              ? "bg-emerald-950 text-emerald-300 border-emerald-600"
                              : tkt.status === "in_progress"
                              ? "bg-amber-950 text-amber-300 border-amber-600"
                              : "bg-blue-950 text-blue-300 border-blue-600"
                          )}
                        >
                          {tkt.status === "resolved"
                            ? "Đã giải quyết"
                            : tkt.status === "in_progress"
                            ? "Đang xử lý"
                            : "Tiếp nhận"}
                        </Badge>
                      </div>

                      <div className="font-semibold text-stone-200">{tkt.subject}</div>
                      <p className="text-stone-400 line-clamp-2 text-[11px]">{tkt.message}</p>

                      {tkt.latestResponse && (
                        <div className="p-2 bg-stone-950/70 border-l-2 border-amber-500 rounded text-[11px] text-amber-200 mt-2">
                          <span className="font-semibold text-amber-400">Phản hồi BQT:</span> {tkt.latestResponse}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 4: Teacher Training Resources */}
        {activeTab === "training_resources" && (
          <div className="p-6 space-y-6">
            <div className="bg-stone-950 p-4 rounded-xl border border-stone-800 space-y-2">
              <div className="flex items-center gap-2 text-amber-300 font-semibold text-sm">
                <FileCheck2 className="w-4 h-4 text-amber-400" />
                Kho Tài Liệu Tập Huấn & Phát Triển Năng Lực Chuyên Môn
              </div>
              <p className="text-xs text-stone-400 leading-relaxed">
                Tài liệu hướng dẫn, video mẫu và cẩm nang quy chuẩn được biên soạn bởi Ban Cố Vấn Sử Học và Trung Tâm Bảo Tồn Di Tích Cố Đô Huế.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-stone-950 border border-stone-800 rounded-xl space-y-3">
                <div className="flex items-center justify-between">
                  <Badge className="bg-amber-950 text-amber-300 border-amber-700 text-xs">
                    Công văn 5512/BGDĐT
                  </Badge>
                  <span className="text-xs text-stone-500 flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" /> 30 phút
                  </span>
                </div>
                <h4 className="text-sm font-bold text-amber-200">
                  Cẩm nang Thiết kế Bài dạy 45 phút Di sản Cửu Đỉnh
                </h4>
                <p className="text-xs text-stone-400">
                  Hướng dẫn chi tiết xây dựng 4 pha dạy học nêu vấn đề, ma trận năng lực và bộ câu hỏi kích hoạt tư duy lịch sử.
                </p>
                <div className="flex items-center justify-between pt-2 border-t border-stone-800">
                  <span className="text-xs text-emerald-400 font-semibold">Tài liệu bắt buộc</span>
                  <Button size="sm" variant="ghost" className="text-xs text-amber-400 hover:text-amber-300 p-0 h-auto">
                    <Download className="w-3.5 h-3.5 mr-1" /> Tải cẩm nang PDF
                  </Button>
                </div>
              </div>

              <div className="p-4 bg-stone-950 border border-stone-800 rounded-xl space-y-3">
                <div className="flex items-center justify-between">
                  <Badge className="bg-emerald-950 text-emerald-300 border-emerald-700 text-xs">
                    Đánh giá Rubric S1-S4
                  </Badge>
                  <span className="text-xs text-stone-500 flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" /> 25 phút
                  </span>
                </div>
                <h4 className="text-sm font-bold text-amber-200">
                  Quy trình Chấm điểm Rubric & Hiệu chuẩn Hai Giám Khảo
                </h4>
                <p className="text-xs text-stone-400">
                  Chuẩn hóa thang điểm 0-3 cho 4 tiêu chí; đối soát độ lệch đánh giá và phương pháp xử lý khi điểm chênh lệch &gt; 15%.
                </p>
                <div className="flex items-center justify-between pt-2 border-t border-stone-800">
                  <span className="text-xs text-emerald-400 font-semibold">Tài liệu bắt buộc</span>
                  <Button size="sm" variant="ghost" className="text-xs text-amber-400 hover:text-amber-300 p-0 h-auto">
                    <Download className="w-3.5 h-3.5 mr-1" /> Tải quy trình PDF
                  </Button>
                </div>
              </div>

              <div className="p-4 bg-stone-950 border border-stone-800 rounded-xl space-y-3">
                <div className="flex items-center justify-between">
                  <Badge className="bg-blue-950 text-blue-300 border-blue-700 text-xs">
                    Nghị định 13/2023/NĐ-CP
                  </Badge>
                  <span className="text-xs text-stone-500 flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" /> 20 phút
                  </span>
                </div>
                <h4 className="text-sm font-bold text-amber-200">
                  Bảo vệ Dữ liệu Cá nhân Học sinh & Đạo đức Nghiên cứu
                </h4>
                <p className="text-xs text-stone-400">
                  Checklist kiểm tra biểu mẫu phụ huynh đồng thuận, quy tắc khử định danh và thời hạn lưu trữ hồ sơ thực địa.
                </p>
                <div className="flex items-center justify-between pt-2 border-t border-stone-800">
                  <span className="text-xs text-emerald-400 font-semibold">Tài liệu bắt buộc</span>
                  <Button size="sm" variant="ghost" className="text-xs text-amber-400 hover:text-amber-300 p-0 h-auto">
                    <Download className="w-3.5 h-3.5 mr-1" /> Tải sổ tay PDF
                  </Button>
                </div>
              </div>

              <div className="p-4 bg-stone-950 border border-stone-800 rounded-xl space-y-3">
                <div className="flex items-center justify-between">
                  <Badge className="bg-purple-950 text-purple-300 border-purple-700 text-xs">
                    Kỹ thuật & Phương tiện
                  </Badge>
                  <span className="text-xs text-stone-500 flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" /> 20 phút
                  </span>
                </div>
                <h4 className="text-sm font-bold text-amber-200">
                  Bộ Tư Liệu Dập Nổi 2D & Tối Ưu Băng Thông Thấp
                </h4>
                <p className="text-xs text-stone-400">
                  Khai thác 162 bản dập nổi hoa văn chất lượng cao phục vụ in ấn phiếu bài tập khi thiết bị học sinh không có Internet.
                </p>
                <div className="flex items-center justify-between pt-2 border-t border-stone-800">
                  <span className="text-xs text-stone-400">Tài liệu tham khảo</span>
                  <Button size="sm" variant="ghost" className="text-xs text-amber-400 hover:text-amber-300 p-0 h-auto">
                    <Download className="w-3.5 h-3.5 mr-1" /> Tải bộ tư liệu ZIP
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}

        <DialogFooter className="p-4 border-t border-stone-800 bg-stone-950/80 flex items-center justify-between">
          <div className="text-xs text-stone-500">
            Hỗ trợ giáo viên: hotro@histolab.icu | Hotline chuyên môn: (0234) 3822 532
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={onClose}
            className="text-xs border-stone-700 text-stone-300 hover:bg-stone-800"
          >
            Đóng
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
