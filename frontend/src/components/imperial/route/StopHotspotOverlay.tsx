"use client";

import React, { useState } from "react";
import { Sparkles, Eye, Info, X } from "lucide-react";
import { cn } from "@/lib/utils";

export interface ArchitecturalHotspot {
  id: string;
  label: string;
  x: number; // percentage 0-100
  y: number; // percentage 0-100
  detailTitle: string;
  description: string;
  historicalCitation: string;
}

const ARCHITECTURAL_HOTSPOTS_MAP: Record<string, ArchitecturalHotspot[]> = {
  "ngo-mon": [
    {
      id: "hm-1",
      label: "Cửa Ngọ Môn (Lối giữa)",
      x: 50,
      y: 86,
      detailTitle: "Lối đi Ngự Đạo của Thiên Tử",
      description: "Cửa chính giữa xây bằng đá thanh, chỉ dành riêng cho Hoàng đế triều Nguyễn ngự hành khi xuất giá tuần du hoặc thiết lễ.",
      historicalCitation: "Đại Nam Thực Lục: 'Cửa giữa chỉ để mở mỗi khi loan giá xuất cung.'",
    },
    {
      id: "hm-2",
      label: "Lầu Ngũ Phụng",
      x: 50,
      y: 35,
      detailTitle: "Đài quan sát & Lễ đài truyền loa",
      description: "Tầng lầu hai tầng chồng diềm với 100 cột gỗ lim, chia 9 bộ mái tượng trưng trăm họ thái bình; nơi ban sóc (phát lịch) và truyền loa tiến sĩ.",
      historicalCitation: "Khâm Định Đại Nam Hội Điển Sự Lệ: 'Quy định các vị tân khoa tiến sĩ đứng bái mạng dưới lầu Ngũ Phụng.'",
    },
    {
      id: "hm-3",
      label: "Tả/Hữu Giáp Môn",
      x: 37,
      y: 86,
      detailTitle: "Cửa quan văn & quan võ",
      description: "Hai cửa hai bên cửa chính, lợp ngói thanh lưu ly, dành riêng cho các quan đại thần triều đình ra vào khi vào chầu.",
      historicalCitation: "Quy thức phân tầng đẳng cấp phong kiến triều Nguyễn.",
    },
    {
      id: "hm-4",
      label: "Tả/Hữu Dịch Môn",
      x: 18,
      y: 87,
      detailTitle: "Cửa cánh cung dành cho cấm binh",
      description: "Hai lối cửa khoét xuyên qua cánh gà thành đá chữ U, dành cho binh lính thị vệ và voi ngựa tùy tùng.",
      historicalCitation: "Hệ thống phân luồng kiểm soát an ninh Hoàng Thành.",
    },
  ],
  "dien-thai-hoa": [
    {
      id: "ht-1",
      label: "Mái ngói Hoàng lưu ly",
      x: 50,
      y: 22,
      detailTitle: "Ngói tráng men vàng Đế vương",
      description: "Toàn bộ mái chính điện lợp ngói hoàng lưu ly rực rỡ, biểu trưng quyền lực tối cao của hoàng triều dưới ánh mặt trời.",
      historicalCitation: "Quy chuẩn mái ngói hoàng gia triều Nguyễn.",
    },
    {
      id: "ht-2",
      label: "Bờ nóc Lưỡng long triều nhật",
      x: 50,
      y: 8,
      detailTitle: "Nghệ thuật đắp nổi sành sứ",
      description: "Hình tượng hai con rồng chầu mặt trời đắp nổi bằng vôi vữa trộn mật mía và ghép hàng ngàn mảnh sành sứ, pháp lam tinh xảo.",
      historicalCitation: "Mô típ rồng 5 móng độc quyền của thiên tử.",
    },
    {
      id: "ht-3",
      label: "Hệ thống liên ba 'Nhất thi nhất họa'",
      x: 50,
      y: 60,
      detailTitle: "Thơ văn ngự chế chạm khảm thếp vàng",
      description: "Dải liên ba chạy suốt chiều ngang tòa điện gồm hàng trăm ô hộc chạm khắc thơ văn chữ Hán của các vị hoàng đế ca ngợi nền thái bình độc lập.",
      historicalCitation: "Di sản Tư liệu Ký ức Thế giới UNESCO (2016).",
    },
    {
      id: "ht-4",
      label: "Thềm rồng đá Gia Long",
      x: 50,
      y: 88,
      detailTitle: "Bốn con rồng đá thanh nguyên bản năm 1805",
      description: "Bốn con rồng đá thanh uốn lượn theo bậc thềm chia sân Đại Triều Nghi với thềm điện Thái Hòa, tạo thế 'long trì ngự tọa'.",
      historicalCitation: "Điêu khắc đá cung đình đầu thế kỷ XIX.",
    },
  ],
};

interface StopHotspotOverlayProps {
  monumentSlug: string;
  isVisible: boolean;
  onToggleVisible: () => void;
}

export function StopHotspotOverlay({
  monumentSlug,
  isVisible,
  onToggleVisible,
}: StopHotspotOverlayProps) {
  const hotspots = ARCHITECTURAL_HOTSPOTS_MAP[monumentSlug] || [];
  const [selectedHotspot, setSelectedHotspot] = useState<ArchitecturalHotspot | null>(null);

  if (hotspots.length === 0) return null;

  return (
    <>
      {/* Toggle Hotspot Button */}
      <button
        type="button"
        onClick={onToggleVisible}
        className={cn(
          "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all shadow-md backdrop-blur-md border",
          isVisible
            ? "bg-amber-500 text-stone-950 border-amber-400 font-bold"
            : "bg-black/60 text-white border-white/20 hover:bg-black/80",
        )}
      >
        <Sparkles className="h-3.5 w-3.5" />
        <span>{isVisible ? "Ẩn điểm khảo cứu cấu kiện" : "Khám phá điểm cấu kiện kiến trúc"}</span>
        <span className="rounded-full bg-white/20 px-1.5 py-0.2 text-[10px] ml-0.5">
          {hotspots.length}
        </span>
      </button>

      {/* Render Hotspot Pins when enabled */}
      {isVisible && (
        <div className="absolute inset-0 pointer-events-none z-20">
          {hotspots.map((hp) => (
            <div
              key={hp.id}
              style={{ left: `${hp.x}%`, top: `${hp.y}%` }}
              className="absolute -translate-x-1/2 -translate-y-1/2 pointer-events-auto"
            >
              <button
                type="button"
                onClick={() => setSelectedHotspot(hp)}
                className="group relative flex items-center justify-center p-1 focus:outline-none"
                title={hp.label}
              >
                {/* Ping ring */}
                <span className="absolute h-7 w-7 rounded-full bg-amber-400/50 animate-ping pointer-events-none" />

                {/* Hotspot Center Icon */}
                <span className="relative flex h-6 w-6 items-center justify-center rounded-full bg-amber-500 border-2 border-white text-stone-950 shadow-lg text-[10px] font-black group-hover:scale-125 transition-transform">
                  +
                </span>

                {/* Hover Label */}
                <span className="absolute top-full mt-1 whitespace-nowrap rounded-md bg-black/85 px-2 py-0.5 text-[10px] font-bold text-white shadow opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                  {hp.label}
                </span>
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Active Hotspot Info Card Flyout */}
      {selectedHotspot && (
        <div
          role="dialog"
          aria-modal="true"
          className="absolute bottom-3 left-3 right-3 sm:left-auto sm:right-3 sm:max-w-xs z-30 rounded-2xl bg-card/95 border border-primary/40 p-4 shadow-xl backdrop-blur-md space-y-2 animate-in fade-in slide-in-from-bottom-2 duration-200"
        >
          <div className="flex items-start justify-between gap-2 border-b border-border/50 pb-2">
            <div>
              <span className="text-[10px] font-mono text-primary font-bold uppercase tracking-wider block">
                Cấu kiện khảo cứu
              </span>
              <h4 className="font-serif text-sm font-bold text-foreground">
                {selectedHotspot.detailTitle}
              </h4>
            </div>
            <button
              type="button"
              onClick={() => setSelectedHotspot(null)}
              className="rounded-full p-1 text-muted-foreground hover:bg-secondary hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <p className="text-xs text-muted-foreground leading-relaxed">
            {selectedHotspot.description}
          </p>

          <div className="rounded-lg bg-primary/5 border border-primary/20 p-2 text-[11px] italic text-primary/90 font-serif">
            {selectedHotspot.historicalCitation}
          </div>
        </div>
      )}
    </>
  );
}
