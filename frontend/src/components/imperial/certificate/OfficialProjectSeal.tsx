"use client";

import React from "react";
import { cn } from "@/lib/utils";

export interface OfficialProjectSealProps {
  className?: string;
  size?: "sm" | "md" | "lg";
}

/**
 * Official Project Seal of Luu Nien — Hue Imperial City
 * Authentic Vietnamese Imperial cinnabar ink seal (Ấn triện mộc son thẩm định).
 * Text: "LƯU NIÊN ĐẠI NỘI CHI BẢO — THẨM ĐỊNH DI SẢN"
 */
export function OfficialProjectSeal({
  className,
  size = "md",
}: OfficialProjectSealProps) {
  const sizeClasses = {
    sm: "size-20 sm:size-24",
    md: "size-24 sm:size-28 md:size-32",
    lg: "size-32 sm:size-36 md:size-40",
  }[size];

  return (
    <div
      className={cn(
        "relative select-none transition-transform hover:scale-105",
        "flex flex-col items-center justify-center text-center",
        sizeClasses,
        className,
      )}
      aria-label="Dấu mộc son thẩm định của Ban Quản lý Di sản Lưu Niên Đại Nội Huế"
    >
      <div
        className={cn(
          "w-full h-full rounded-md border-[3px] border-[#A62B2B] bg-[#A62B2B]/[0.06] p-1.5",
          "shadow-[0_0_1px_1px_rgba(166,43,43,0.3)] rotate-[-2.5deg]",
          "flex flex-col items-center justify-between",
          "relative overflow-hidden print:bg-transparent",
        )}
      >
        {/* Inner double border rail */}
        <div className="absolute inset-1 border border-[#A62B2B]/80 rounded-[3px] pointer-events-none" />

        {/* 4 Tiny Corner Triện Accents */}
        <span className="absolute top-1 left-1 size-1.5 border-t border-l border-[#A62B2B]" />
        <span className="absolute top-1 right-1 size-1.5 border-t border-r border-[#A62B2B]" />
        <span className="absolute bottom-1 left-1 size-1.5 border-b border-l border-[#A62B2B]" />
        <span className="absolute bottom-1 right-1 size-1.5 border-b border-r border-[#A62B2B]" />

        {/* Top Arc Inscription */}
        <div className="pt-0.5 text-[8px] sm:text-[9px] font-serif font-black tracking-[0.2em] text-[#A62B2B] uppercase">
          LƯU NIÊN SỬ KÝ
        </div>

        {/* Central Seal Inscription (Hán Nôm + Quốc ngữ) */}
        <div className="flex flex-col items-center justify-center my-auto leading-none">
          <span className="font-serif font-black text-base sm:text-lg md:text-xl text-[#A62B2B] tracking-[0.15em]">
            ĐẠI NỘI
          </span>
          <span className="font-serif text-[10px] sm:text-xs font-extrabold text-[#A62B2B] tracking-[0.3em] uppercase pt-0.5">
            CHI BẢO
          </span>
          <span className="text-[7px] text-[#A62B2B]/75 font-mono tracking-widest pt-0.5">
            ★ THẨM ĐỊNH ★
          </span>
        </div>

        {/* Bottom Arc Inscription */}
        <div className="pb-0.5 text-[7px] sm:text-[8px] font-serif font-bold tracking-[0.14em] text-[#A62B2B] uppercase border-t border-[#A62B2B]/40 w-full text-center">
          HOÀNG THÀNH HUẾ
        </div>
      </div>
    </div>
  );
}

export default OfficialProjectSeal;
