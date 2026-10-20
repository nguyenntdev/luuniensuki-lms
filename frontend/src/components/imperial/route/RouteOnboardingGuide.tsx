"use client";

import React, { useState, useEffect } from "react";
import {
  Compass,
  Footprints,
  Laptop,
  CheckCircle2,
  Sparkles,
  BookOpen,
  Eye,
  Award,
  Stamp,
  HelpCircle,
  X,
  ArrowRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const ONBOARDING_DISMISSED_KEY = "luuniensuki_route_onboarding_dismissed";

interface RouteOnboardingGuideProps {
  isOpen: boolean;
  onClose: () => void;
  trailTitle?: string;
}

export function RouteOnboardingGuide({
  isOpen,
  onClose,
  trailTitle = "Trục Dũng Đạo & Quyền Lực Hoàng Triều",
}: RouteOnboardingGuideProps) {
  const [activeStep, setActiveStep] = useState(0);

  const steps = [
    {
      step: 1,
      title: "Định vị trạm dừng trên Bản đồ không ảnh",
      subtitle: "Quan sát trục không gian Thần đạo Nam - Bắc",
      icon: Compass,
      color: "text-amber-500",
      bgColor: "bg-amber-500/15",
      content:
        "Bắt đầu từ Ngọ Môn tiến dần vào Tử Cấm Thành. Hãy quan sát tọa độ UV chuẩn hóa và ranh giới phong thủy giữa hồ Thái Dịch, sân Đại Triều Nghi và các cổng thành để cảm nhận trật tự tôn ti vương triều.",
      tip: "Mẹo: Bạn có thể bấm 'Mở bản đồ lớn' để tương tác với toàn bộ 16 di tích Hoàng Thành.",
    },
    {
      step: 2,
      title: "Khảo sát Hiện trạng & Cấu kiện kiến trúc",
      subtitle: "Xem ảnh thực địa độ nét cao & Điểm khảo cứu",
      icon: Eye,
      color: "text-sky-500",
      bgColor: "bg-sky-500/15",
      content:
        "Mỗi trạm dừng có kho ảnh thực địa đã kiểm duyệt. Bấm nút 'Khám phá điểm cấu kiện' để xem giải thích các bộ phận kiến trúc (ví dụ: 5 vòm cửa Ngọ Môn, mái hoàng lưu ly Điện Thái Hòa). Nếu di tích bị phá hủy (như Điện Cần Chánh năm 1947), hệ thống sẽ nêu rõ nguyên nhân lịch sử.",
      tip: "Mẹo: Bấm trực tiếp vào ảnh để mở cửa sổ phóng to toàn màn hình.",
    },
    {
      step: 3,
      title: "Đối chiếu Sử liệu chính thống triều Nguyễn",
      subtitle: "Đọc trích đoạn Đại Nam Thực Lục & Hội Điển Sự Lệ",
      icon: BookOpen,
      color: "text-emerald-500",
      bgColor: "bg-emerald-500/15",
      content:
        "Đọc các văn bản chính sử được Quốc Sử Quán triều Nguyễn ghi chép. Chú ý các chi tiết về niên đại khởi dựng, quy thức phân luồng ra vào và quy định thứ bậc quan văn võ.",
      tip: "Mẹo: Mọi trích dẫn sử liệu đều có thể dùng làm bằng chứng (Evidence) cho bài Exit Ticket.",
    },
    {
      step: 4,
      title: "Đúc kết Mệnh đề M-E-E & Đóng Dấu Triện Son",
      subtitle: "Mệnh đề - Bằng chứng - Giới hạn kiểm chứng",
      icon: Award,
      color: "text-red-600 dark:text-red-400",
      bgColor: "bg-red-500/15",
      content:
        "Hoàn thành nhiệm vụ suy luận sư phạm bằng cách điền câu trả lời M-E-E. Khi nộp bài thành công, con dấu Ấn Triện Son Hoàng Triều của di tích sẽ tự động được dập vào Hộ Chiếu Di Sản của bạn!",
      tip: "Mẹo: Thu thập đủ dấu triện các trạm sẽ mở khóa Chứng Nhận Vinh Danh Di Sản Hoàng Thành.",
    },
  ];

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl p-6 sm:p-8">
        <DialogHeader className="space-y-2 text-left">
          <div className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <Sparkles className="h-4 w-4" />
            </span>
            <span className="text-xs font-bold uppercase tracking-wider text-primary">
              Quy trình học tập di sản số
            </span>
          </div>

          <DialogTitle className="font-serif text-xl sm:text-2xl font-bold text-foreground">
            Hướng dẫn khảo sát lộ trình: {trailTitle}
          </DialogTitle>
          <DialogDescription className="text-xs text-muted-foreground leading-relaxed">
            Dành cho học sinh và người học lần đầu trải nghiệm học lịch sử theo phương pháp đọc không gian & truy chứng tư liệu.
          </DialogDescription>
        </DialogHeader>

        {/* Stepper Navigation Pills */}
        <div className="grid grid-cols-4 gap-2 pt-2">
          {steps.map((s, idx) => {
            const Icon = s.icon;
            const isCurrent = idx === activeStep;
            return (
              <button
                key={s.step}
                type="button"
                onClick={() => setActiveStep(idx)}
                className={`flex flex-col items-center p-2.5 rounded-xl border text-center transition-all ${
                  isCurrent
                    ? "border-primary bg-primary/10 shadow-xs ring-1 ring-primary/40"
                    : "border-border/60 bg-secondary/30 hover:bg-secondary text-muted-foreground"
                }`}
              >
                <div
                  className={`flex h-8 w-8 items-center justify-center rounded-full mb-1 ${
                    isCurrent ? "bg-primary text-primary-foreground font-bold" : s.bgColor
                  }`}
                >
                  <Icon className={`h-4 w-4 ${isCurrent ? "" : s.color}`} />
                </div>
                <span className="text-[11px] font-bold line-clamp-1">
                  Bước {s.step}
                </span>
                <span className="text-[9px] text-muted-foreground hidden sm:block truncate w-full">
                  {s.title.slice(0, 15)}...
                </span>
              </button>
            );
          })}
        </div>

        {/* Active Step Content Card */}
        {(() => {
          const current = steps[activeStep];
          const CurrentIcon = current.icon;
          return (
            <div className="rounded-2xl border border-border/80 bg-card p-5 space-y-3.5 mt-2 animate-in fade-in duration-200">
              <div className="flex items-start gap-3.5">
                <div
                  className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl ${current.bgColor} ${current.color}`}
                >
                  <CurrentIcon className="h-6 w-6" />
                </div>
                <div>
                  <span className="text-[10px] font-mono text-muted-foreground uppercase font-semibold">
                    Chặng {current.step} / 4
                  </span>
                  <h3 className="font-serif text-base sm:text-lg font-bold text-foreground">
                    {current.title}
                  </h3>
                  <p className="text-xs font-serif italic text-primary font-medium">
                    {current.subtitle}
                  </p>
                </div>
              </div>

              <p className="text-xs sm:text-sm text-foreground/90 leading-relaxed">
                {current.content}
              </p>

              <div className="rounded-xl bg-secondary/50 border border-border/60 p-3 text-xs text-muted-foreground">
                <strong className="text-foreground">{current.tip}</strong>
              </div>
            </div>
          );
        })()}

        {/* Footer Navigation */}
        <div className="flex items-center justify-between pt-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onClose}
            className="text-xs"
          >
            Đóng hướng dẫn
          </Button>

          <div className="flex items-center gap-2">
            {activeStep > 0 && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setActiveStep((p) => p - 1)}
                className="text-xs"
              >
                Quay lại
              </Button>
            )}

            {activeStep < steps.length - 1 ? (
              <Button
                type="button"
                size="sm"
                onClick={() => setActiveStep((p) => p + 1)}
                className="text-xs gap-1.5 bg-primary text-primary-foreground"
              >
                <span>Bước kế tiếp</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            ) : (
              <Button
                type="button"
                size="sm"
                onClick={onClose}
                className="text-xs gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>Bắt đầu khảo sát ngay</span>
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
