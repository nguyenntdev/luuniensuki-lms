"use client";

import React from "react";
import { CheckCircle2, Lock } from "lucide-react";
import type { ZoneSealBreakdown } from "@/lib/imperial/certificate-utils";
import { cn } from "@/lib/utils";

export interface ZoneScoreBreakdownProps {
  zones: ZoneSealBreakdown[];
  totalScore: number;
  totalSeals: number;
  unlockedCount: number;
  className?: string;
  compact?: boolean;
}

/**
 * 4 Spatial Zones Seal & Score Breakdown Component.
 * Displays seal collection progress across:
 * 1. Trục trung tâm (Central Ceremonial Axis)
 * 2. Không gian thờ tự (Ancestral Worship Space)
 * 3. Tử Cấm Thành (Purple Forbidden City)
 * 4. Không gian sinh hoạt (Royal Living and Gardens)
 */
export function ZoneScoreBreakdown({
  zones,
  totalScore,
  totalSeals,
  unlockedCount,
  className,
  compact = false,
}: ZoneScoreBreakdownProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-[#C68A2C]/35 bg-[#FAF6EC]/85 p-3 sm:p-4 text-left shadow-sm print:bg-white/80 print:border-[#A62B2B]/40",
        className,
      )}
    >
      {/* Header with summary count and score */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#C68A2C]/25 pb-2.5">
        <div className="flex items-center gap-2">
          <span className="font-serif text-xs sm:text-sm font-bold text-[#A62B2B] uppercase tracking-wider">
            Kết quả Khảo cứu 4 Cụm Không gian
          </span>
          <span className="rounded-full bg-[#A62B2B]/10 px-2 py-0.5 text-[10px] font-bold text-[#A62B2B] border border-[#A62B2B]/20">
            {unlockedCount}/{totalSeals} Ấn triện
          </span>
        </div>

        <div className="flex items-center gap-1.5 text-xs text-[#2A241D] font-mono">
          <span className="text-[11px] text-[#675C4E]">Tổng điểm di sản:</span>
          <strong className="text-sm font-bold text-[#C68A2C]">{totalScore} XP</strong>
        </div>
      </div>

      {/* 4 Zone Cards Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5 pt-3">
        {zones.map((zone) => {
          const isComplete = zone.isCompleted;
          const ratio = `${zone.unlockedCount}/${zone.totalCount}`;

          const zoneSealBadge = {
            "central-ceremonial-axis": { motif: "Kim Bảo", name: "Hoàng Đế Chi Bảo" },
            "ancestral-worship-space": { motif: "Ngự Tỷ", name: "Tôn Miếu Ngự Tỷ" },
            "purple-forbidden-city": { motif: "Kim Bảo", name: "Ngự Tiền Chi Bảo" },
            "royal-living-gardens": { motif: "Ngự Tỷ", name: "Diên Thọ Ngự Tỷ" },
          }[zone.zoneSlug];

          return (
            <div
              key={zone.zoneSlug}
              className={cn(
                "rounded-lg p-2.5 border transition-all text-xs flex flex-col justify-between",
                isComplete
                  ? "border-[#2F6F55]/40 bg-[#2F6F55]/[0.06] text-[#2A241D]"
                  : "border-[#D8C7A5] bg-white/60 text-[#2A241D]",
              )}
            >
              <div>
                <div className="flex items-center justify-between gap-1 mb-1">
                  <span className="font-serif font-bold text-[11px] sm:text-xs truncate text-[#2A241D]">
                    {zone.zoneTitleVi}
                  </span>
                  {isComplete ? (
                    <div className="flex items-center gap-1 shrink-0">
                      <span className="text-[9px] font-serif font-bold text-amber-800 dark:text-amber-300 bg-amber-500/15 border border-amber-500/30 px-1 rounded">
                        {zoneSealBadge?.motif}
                      </span>
                      <CheckCircle2 className="size-3.5 text-[#2F6F55]" />
                    </div>
                  ) : (
                    <span className="text-[10px] font-mono font-semibold text-[#675C4E]">
                      {ratio}
                    </span>
                  )}
                </div>

                <div className="text-[10px] text-[#675C4E] font-serif italic mb-1.5 line-clamp-1">
                  {zone.zoneTitleHanNom}
                </div>
              </div>

              {isComplete && zoneSealBadge && (
                <div className="text-[9px] font-serif font-semibold text-[#A62B2B] truncate mb-1">
                  ❖ {zoneSealBadge.name}
                </div>
              )}

              {/* Mini Stamp Pill Representation */}
              {!compact && (
                <div className="flex flex-wrap gap-1 pt-1 border-t border-[#D8C7A5]/40">
                  {zone.seals.map((seal) => (
                    <span
                      key={seal.slug}
                      title={`${seal.name} — ${seal.sealTitle} (${seal.isUnlocked ? "Đã đóng dấu" : "Chưa hoàn thành"})`}
                      className={cn(
                        "size-4 rounded-[2px] flex items-center justify-center font-serif text-[8px] font-bold border transition-colors",
                        seal.isUnlocked
                          ? "bg-[#A62B2B] text-white border-[#A62B2B]"
                          : "bg-black/5 text-muted-foreground/40 border-black/10",
                      )}
                    >
                      {seal.isUnlocked ? "✓" : "·"}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default ZoneScoreBreakdown;
