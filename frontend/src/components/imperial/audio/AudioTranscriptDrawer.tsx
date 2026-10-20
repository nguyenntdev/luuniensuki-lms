"use client";

import React, { useEffect, useRef } from "react";
import {
  Bell,
  FileText,
  Headphones,
  Music,
  RotateCcw,
  Sparkles,
  Volume2,
  X,
} from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { useAudioPlayerStore } from "@/stores/imperialAudioStore";
import { formatAudioTime } from "@/lib/imperial/audio-api";
import { playThienMuBellSound, playNhaNhacChime } from "@/lib/imperial/seal-audio";
import type { TimedTranscriptCue } from "@/lib/imperial/audio-types";

export interface AudioTranscriptDrawerProps {
  className?: string;
}

export function AudioTranscriptDrawer({ className }: AudioTranscriptDrawerProps) {
  const currentTrack = useAudioPlayerStore((s) => s.currentTrack);
  const currentTime = useAudioPlayerStore((s) => s.currentTime);
  const isPlaying = useAudioPlayerStore((s) => s.isPlaying);
  const isDrawerOpen = useAudioPlayerStore((s) => s.isDrawerOpen);
  const setDrawerOpen = useAudioPlayerStore((s) => s.setDrawerOpen);
  const seekTo = useAudioPlayerStore((s) => s.seekTo);
  const activeCueId = useAudioPlayerStore((s) => s.activeCueId);

  const activeCueRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll the active transcript cue into comfortable view
  useEffect(() => {
    if (isDrawerOpen && activeCueRef.current) {
      activeCueRef.current.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });
    }
  }, [activeCueId, isDrawerOpen]);

  if (!currentTrack) return null;

  const transcript = currentTrack.transcript || [];

  return (
    <Sheet open={isDrawerOpen} onOpenChange={setDrawerOpen}>
      <SheetContent
        side="right"
        className={cn(
          "w-full sm:max-w-md md:max-w-lg bg-card/95 backdrop-blur-2xl border-l border-border/80 p-0 flex flex-col shadow-2xl z-[60]",
          className,
        )}
      >
        {/* Header */}
        <SheetHeader className="p-5 pb-3 border-b border-border/60 bg-secondary/30">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/15 text-primary border border-primary/20">
                <FileText className="w-4 h-4" />
              </span>
              <div>
                <Badge
                  variant="outline"
                  className="bg-primary/10 text-primary border-primary/30 text-[10px] px-2 py-0 h-4 font-mono uppercase tracking-wider"
                >
                  Lời thoại chính âm
                </Badge>
                <SheetTitle className="text-base font-serif font-bold text-foreground line-clamp-1 mt-0.5">
                  {currentTrack.siteNameVi}
                  {currentTrack.siteNameHanNom && (
                    <span className="font-serif text-amber-500 text-sm ml-1.5 font-normal">
                      {currentTrack.siteNameHanNom}
                    </span>
                  )}
                </SheetTitle>
              </div>
            </div>
          </div>
          <SheetDescription className="text-xs text-muted-foreground mt-1 line-clamp-2">
            {currentTrack.titleVi} — {currentTrack.narrator || "Giọng đọc Thừa Thiên Huế chuẩn truyền cảm"}
          </SheetDescription>
        </SheetHeader>

        {/* Status / Quick Tip & Soundscape Triggers */}
        <div className="px-5 py-2.5 bg-amber-500/10 border-b border-amber-500/20 flex items-center justify-between text-xs text-amber-300 gap-2 flex-wrap">
          <span className="flex items-center gap-1.5 min-w-0 truncate">
            <Sparkles className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            Nhấn câu để chuyển nhanh
          </span>
          <div className="flex items-center gap-2 shrink-0">
            {/* Quick soundscape triggers */}
            <button
              type="button"
              onClick={() => playThienMuBellSound({ volume: 0.8 })}
              className="inline-flex items-center gap-1 rounded bg-amber-500/20 hover:bg-amber-500/30 px-2 py-0.5 text-[11px] font-medium text-amber-300 transition-colors"
              title="Ngân vang tiếng chuông chùa Thiên Mụ"
            >
              <Bell className="w-3 h-3 text-amber-400" />
              <span>Chuông Thiên Mụ</span>
            </button>
            <button
              type="button"
              onClick={() => playNhaNhacChime({ volume: 0.75 })}
              className="inline-flex items-center gap-1 rounded bg-primary/20 hover:bg-primary/30 px-2 py-0.5 text-[11px] font-medium text-primary transition-colors"
              title="Âm vang Nhã nhạc cung đình Huế"
            >
              <Music className="w-3 h-3 text-primary" />
              <span>Nhã nhạc</span>
            </button>
            <span className="font-mono text-[11px] text-amber-400 font-semibold pl-1">
              {formatAudioTime(currentTime)} / {formatAudioTime(currentTrack.duration)}
            </span>
          </div>
        </div>

        {/* Scrollable Transcript Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-3.5 scroll-smooth">
          {transcript.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center text-muted-foreground space-y-2">
              <Headphones className="w-8 h-8 opacity-40 animate-pulse" />
              <p className="text-sm">Chưa có văn bản đồng bộ cho di tích này.</p>
            </div>
          ) : (
            transcript.map((cue: TimedTranscriptCue, idx: number) => {
              const isActive =
                activeCueId === cue.id ||
                (currentTime >= cue.startTime && currentTime < cue.endTime);

              return (
                <div
                  key={cue.id || idx}
                  ref={isActive ? activeCueRef : null}
                  onClick={() => seekTo(cue.startTime)}
                  className={cn(
                    "group relative p-3.5 rounded-xl border transition-all duration-200 cursor-pointer text-left select-none",
                    isActive
                      ? "bg-primary/10 border-primary/40 shadow-sm ring-1 ring-primary/30"
                      : "bg-card/60 hover:bg-secondary/60 border-border/40 hover:border-border",
                  )}
                >
                  {/* Top line: Timestamp & Section Title */}
                  <div className="flex items-center justify-between text-[11px] mb-1.5 gap-2">
                    <div className="flex items-center gap-1.5">
                      <span
                        className={cn(
                          "font-mono px-1.5 py-0.5 rounded text-[10px] font-semibold transition-colors",
                          isActive
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted text-muted-foreground group-hover:bg-primary/20 group-hover:text-primary",
                        )}
                      >
                        {formatAudioTime(cue.startTime)}
                      </span>
                      {cue.sectionTitle && (
                        <span
                          className={cn(
                            "font-semibold line-clamp-1",
                            isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground",
                          )}
                        >
                          {cue.sectionTitle}
                        </span>
                      )}
                    </div>

                    {isActive && (
                      <span className="flex items-center gap-1 text-[10px] text-primary font-medium shrink-0 animate-pulse">
                        <Volume2 className="w-3 h-3" />
                        Đang phát
                      </span>
                    )}
                  </div>

                  {/* Cue Paragraph */}
                  <p
                    className={cn(
                      "text-sm leading-relaxed transition-colors",
                      isActive
                        ? "text-foreground font-medium"
                        : "text-foreground/80 group-hover:text-foreground",
                    )}
                  >
                    {cue.textVi}
                  </p>

                  {/* English subtitled text if available */}
                  {cue.textEn && (
                    <p className="mt-1 text-xs text-muted-foreground/90 italic border-l-2 border-primary/30 pl-2">
                      {cue.textEn}
                    </p>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Footer info */}
        <div className="p-4 border-t border-border/60 bg-secondary/20 flex items-center justify-between text-xs text-muted-foreground">
          <span className="truncate">
            {currentTrack.historicalPeriod || "Triều Nguyễn"}
          </span>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => seekTo(0)}
            className="text-xs h-8 px-2.5 text-muted-foreground hover:text-foreground flex items-center gap-1"
          >
            <RotateCcw className="w-3 h-3" />
            Nghe lại từ đầu
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
