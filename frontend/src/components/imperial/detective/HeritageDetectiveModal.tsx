"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Compass,
  Search,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  X,
  MapPin,
  ExternalLink,
  Award,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ImperialClue } from "@/lib/imperial/v51-types";
import { fetchClues } from "@/lib/imperial/v51-api";
import { HeritageDetectiveWidget } from "./HeritageDetectiveWidget";

interface HeritageDetectiveModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  currentSiteSlug?: string;
  currentSiteId?: string;
  onClueSolved?: (clueId: string, pointsAwarded: number) => void;
}

export function HeritageDetectiveModal({
  open,
  onOpenChange,
  currentSiteSlug,
  currentSiteId,
  onClueSolved,
}: HeritageDetectiveModalProps) {
  const [clues, setClues] = useState<ImperialClue[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeClueIndex, setActiveClueIndex] = useState<number>(0);
  const [solvedClueIds, setSolvedClueIds] = useState<string[]>([]);

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        setLoading(true);
        const data = await fetchClues();
        if (mounted) {
          setClues(data);
        }
      } catch (err) {
        console.error("Failed to fetch clues for modal:", err);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    if (open) {
      load();
    }
    return () => {
      mounted = false;
    };
  }, [open]);

  const handleSolved = (clueId: string, points: number) => {
    setSolvedClueIds((prev) => (prev.includes(clueId) ? prev : [...prev, clueId]));
    if (onClueSolved) {
      onClueSolved(clueId, points);
    }
  };

  const activeClue = clues[activeClueIndex] || clues[0];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto p-0 gap-0 border-border/80 bg-background/95 backdrop-blur-xl">
        <DialogHeader className="p-5 pb-3 border-b border-border/60">
          <div className="flex items-center gap-2">
            <Badge className="bg-primary/10 text-primary border-primary/20 text-xs font-semibold gap-1.5 py-0.5 px-2.5">
              <Compass className="size-3.5" />
              <span>Hồ Sơ Mật Vụ Lịch Sử</span>
            </Badge>
            <Badge variant="outline" className="text-xs text-muted-foreground">
              Đã giải: {solvedClueIds.length}/{clues.length}
            </Badge>
          </div>
          <DialogTitle className="font-serif text-xl sm:text-2xl text-foreground mt-1">
            Thám Tử Di Sản Đại Nội Huế
          </DialogTitle>
          <DialogDescription className="text-xs sm:text-sm text-muted-foreground">
            Giải mã các câu đố lịch sử dựa trên các chi tiết kiến trúc, hoa văn và trích dẫn chính sử triều Nguyễn.
          </DialogDescription>
        </DialogHeader>

        <div className="p-5 space-y-5">
          {/* Clue selector list */}
          <div className="space-y-2">
            <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider block">
              Danh sách câu đố đang mở:
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {clues.map((c, idx) => {
                const isSelected = idx === activeClueIndex;
                const isSolved = solvedClueIds.includes(c.id);
                return (
                  <button
                    key={c.id}
                    onClick={() => setActiveClueIndex(idx)}
                    className={`text-left p-2.5 rounded-xl border text-xs transition-all flex items-start justify-between gap-2 ${
                      isSelected
                        ? "border-primary bg-primary/10 font-semibold text-primary shadow-sm"
                        : "border-border/60 hover:bg-muted/40 text-foreground"
                    }`}
                  >
                    <div className="space-y-0.5 truncate">
                      <span className="block truncate font-medium">
                        {idx + 1}. {c.title}
                      </span>
                      <span className="text-[10px] text-muted-foreground block">
                        Độ khó: {c.difficulty || "Cơ bản"} • +{c.points || 30} XP
                      </span>
                    </div>
                    {isSolved && (
                      <CheckCircle2 className="size-4 text-emerald-500 shrink-0 mt-0.5" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Active Clue Widget */}
          {activeClue && (
            <div className="pt-2">
              <HeritageDetectiveWidget
                key={activeClue.id}
                clue={activeClue}
                currentSiteSlug={currentSiteSlug}
                currentSiteId={currentSiteId}
                onClueSolved={handleSolved}
              />
            </div>
          )}

          {/* Educational Note */}
          <div className="rounded-xl border border-border/50 bg-muted/20 p-3 text-[11px] text-muted-foreground flex items-center justify-between gap-2">
            <span>
              💡 Học sinh có thể đọc sử liệu và quan sát bản đồ không ảnh để thu thập manh mối trước khi xác nhận đáp án.
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onOpenChange(false)}
              className="h-7 text-xs"
            >
              Đóng
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
