"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import {
  Bell,
  ChevronDown,
  ChevronUp,
  FileText,
  Headphones,
  Maximize2,
  Minimize2,
  Music,
  Pause,
  Play,
  RotateCcw,
  RotateCw,
  Sparkles,
  Volume2,
  VolumeX,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { useAudioPlayerStore, getGlobalAudioElement } from "@/stores/imperialAudioStore";
import { formatAudioTime, findActiveCue } from "@/lib/imperial/audio-api";
import { playThienMuBellSound, playNhaNhacChime } from "@/lib/imperial/seal-audio";
import { AudioTranscriptDrawer } from "./AudioTranscriptDrawer";
import type { PlaybackRate } from "@/lib/imperial/audio-types";

export interface FloatingAudioPlayerProps {
  className?: string;
}

export function FloatingAudioPlayer({ className }: FloatingAudioPlayerProps) {
  const currentTrack = useAudioPlayerStore((s) => s.currentTrack);
  const isPlaying = useAudioPlayerStore((s) => s.isPlaying);
  const currentTime = useAudioPlayerStore((s) => s.currentTime);
  const duration = useAudioPlayerStore((s) => s.duration);
  const playbackRate = useAudioPlayerStore((s) => s.playbackRate);
  const volume = useAudioPlayerStore((s) => s.volume);
  const isMuted = useAudioPlayerStore((s) => s.isMuted);
  const isMinimized = useAudioPlayerStore((s) => s.isMinimized);
  const isDrawerOpen = useAudioPlayerStore((s) => s.isDrawerOpen);
  const activeCueId = useAudioPlayerStore((s) => s.activeCueId);

  const togglePlayPause = useAudioPlayerStore((s) => s.togglePlayPause);
  const seekTo = useAudioPlayerStore((s) => s.seekTo);
  const skipTime = useAudioPlayerStore((s) => s.skipTime);
  const setPlaybackRate = useAudioPlayerStore((s) => s.setPlaybackRate);
  const cyclePlaybackRate = useAudioPlayerStore((s) => s.cyclePlaybackRate);
  const toggleMute = useAudioPlayerStore((s) => s.toggleMute);
  const setVolume = useAudioPlayerStore((s) => s.setVolume);
  const toggleMinimized = useAudioPlayerStore((s) => s.toggleMinimized);
  const toggleDrawer = useAudioPlayerStore((s) => s.toggleDrawer);
  const closePlayer = useAudioPlayerStore((s) => s.closePlayer);
  const updateTime = useAudioPlayerStore((s) => s.updateTime);
  const setIsPlaying = useAudioPlayerStore((s) => s.setIsPlaying);

  const [showVolumeSlider, setShowVolumeSlider] = useState(false);
  const [showSpeedSelector, setShowSpeedSelector] = useState(false);
  const [isMounted, setIsMounted] = useState(false);
  const isDraggingSeekbar = useRef(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  // Sync with global HTMLAudioElement lifecycle & fallback playback simulation
  useEffect(() => {
    if (!currentTrack) return;

    const audio = getGlobalAudioElement();
    if (!audio) return;

    let simulationTimer: NodeJS.Timeout | null = null;

    const onTimeUpdate = () => {
      if (!isDraggingSeekbar.current && audio.duration) {
        updateTime(audio.currentTime, audio.duration);
      }
    };

    const onEnded = () => {
      setIsPlaying(false);
      updateTime(0, audio.duration || currentTrack.duration);
    };

    const onError = () => {
      // If the audio URL is not yet physically placed on the server,
      // simulate realistic playback progression so the user can experience
      // transcript sync, seekbar, and speed controls flawlessly.
      console.info("[AudioPlayer] Falling back to audio simulation loop for demonstration");
    };

    audio.addEventListener("timeupdate", onTimeUpdate);
    audio.addEventListener("ended", onEnded);
    audio.addEventListener("error", onError);

    // Fallback simulation timer if real audio source isn't advancing
    if (isPlaying) {
      simulationTimer = setInterval(() => {
        const state = useAudioPlayerStore.getState();
        if (!state.isPlaying || !state.currentTrack) return;
        const total = state.duration || state.currentTrack.duration || 120;
        const nextTime = state.currentTime + 0.5 * state.playbackRate;
        if (nextTime >= total) {
          state.seekTo(0);
          state.pause();
        } else {
          // If HTMLAudio is advancing on its own, it will supersede this via onTimeUpdate
          if (audio.paused || isNaN(audio.currentTime) || audio.currentTime === 0) {
            state.updateTime(nextTime, total);
          }
        }
      }, 500);
    }

    return () => {
      audio.removeEventListener("timeupdate", onTimeUpdate);
      audio.removeEventListener("ended", onEnded);
      audio.removeEventListener("error", onError);
      if (simulationTimer) clearInterval(simulationTimer);
    };
  }, [currentTrack, isPlaying, updateTime, setIsPlaying]);

  if (!isMounted || !currentTrack) {
    return null;
  }

  const activeCue = findActiveCue(currentTrack.transcript, currentTime);

  return (
    <TooltipProvider delayDuration={200}>
      <aside
        aria-label="Trình phát thuyết minh âm thanh di sản"
        className={cn(
          "fixed z-50 transition-all duration-300 ease-out",
          // Placement: Bottom-center or bottom-right
          "bottom-20 md:bottom-6 right-3 md:right-6 max-w-[calc(100vw-24px)]",
          isMinimized ? "w-auto" : "w-[390px] sm:w-[460px] md:w-[480px]",
          className,
        )}
      >
        {/* Minimized Pill View */}
        {isMinimized ? (
          <div className="flex items-center gap-2 rounded-full border border-primary/40 bg-card/95 p-1.5 pl-3 shadow-2xl backdrop-blur-xl ring-1 ring-primary/20 animate-in fade-in zoom-in-95">
            <button
              onClick={togglePlayPause}
              className="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-primary-foreground shadow hover:brightness-110 active:scale-95 transition-transform"
              title={isPlaying ? "Tạm dừng" : "Tiếp tục phát"}
              aria-label={isPlaying ? "Tạm dừng thuyết minh" : "Phát thuyết minh"}
            >
              {isPlaying ? (
                <Pause className="h-4 w-4 fill-current" />
              ) : (
                <Play className="h-4 w-4 fill-current ml-0.5" />
              )}
            </button>

            <button
              onClick={toggleMinimized}
              className="flex items-center gap-2 text-left pr-2 group"
              title="Phóng to bảng điều khiển thuyết minh"
            >
              <div className="flex flex-col max-w-[150px] sm:max-w-[200px]">
                <span className="text-xs font-semibold font-serif text-foreground truncate group-hover:text-primary transition-colors">
                  {currentTrack.siteNameVi}
                </span>
                <span className="font-mono text-[10px] text-muted-foreground">
                  {formatAudioTime(currentTime)} / {formatAudioTime(duration || currentTrack.duration)}
                </span>
              </div>
              <Maximize2 className="h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors ml-1" />
            </button>

            <Button
              size="icon"
              variant="ghost"
              onClick={closePlayer}
              className="h-7 w-7 rounded-full text-muted-foreground hover:text-foreground"
              title="Đóng trình phát"
            >
              <X className="h-3.5 w-3.5" />
            </Button>
          </div>
        ) : (
          /* Full Floating Player Card */
          <div className="rounded-2xl border border-border/80 bg-card/95 p-4 shadow-2xl backdrop-blur-2xl ring-1 ring-primary/20 flex flex-col gap-3 animate-in fade-in slide-in-from-bottom-3">
            {/* Top Bar: Title, Site, Actions */}
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-amber-500/20 via-primary/20 to-primary/30 border border-primary/30 text-primary shadow-inner">
                  <Headphones className={cn("h-5 w-5", isPlaying && "animate-pulse")} />
                  {isPlaying && (
                    <span className="absolute -top-1 -right-1 flex h-3 w-3">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                      <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500 border-2 border-card" />
                    </span>
                  )}
                </div>

                <div className="min-w-0">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <Badge
                      variant="outline"
                      className="bg-primary/10 text-primary border-primary/30 text-[9px] px-1.5 py-0 font-mono"
                    >
                      ÂM THANH DI SẢN
                    </Badge>
                    <Badge
                      variant="outline"
                      className="bg-amber-500/10 text-amber-500 border-amber-500/30 text-[9px] px-1.5 py-0 font-serif"
                    >
                      Giọng Huế truyền cảm
                    </Badge>
                    {currentTrack.historicalPeriod && (
                      <span className="text-[10px] text-muted-foreground truncate hidden sm:inline">
                        {currentTrack.historicalPeriod}
                      </span>
                    )}
                  </div>
                  <h3 className="font-serif font-bold text-sm text-foreground truncate mt-0.5">
                    {currentTrack.siteNameVi}
                    {currentTrack.siteNameHanNom && (
                      <span className="text-amber-500 text-xs ml-1.5 font-normal">
                        {currentTrack.siteNameHanNom}
                      </span>
                    )}
                  </h3>
                </div>
              </div>

              {/* Window controls */}
              <div className="flex items-center gap-1 shrink-0">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={toggleMinimized}
                      className="h-7 w-7 text-muted-foreground hover:text-foreground"
                    >
                      <Minimize2 className="h-3.5 w-3.5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="top">Thu nhỏ</TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={closePlayer}
                      className="h-7 w-7 text-muted-foreground hover:text-destructive"
                    >
                      <X className="h-3.5 w-3.5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="top">Đóng</TooltipContent>
                </Tooltip>
              </div>
            </div>

            {/* Realtime Synchronized Subtitle Snippet */}
            <div
              onClick={toggleDrawer}
              className="cursor-pointer group rounded-xl bg-secondary/50 hover:bg-secondary/70 border border-border/50 px-3 py-2 text-xs transition-colors flex items-center justify-between gap-2 select-none"
              title="Nhấn để mở toàn văn lời thoại đồng bộ"
            >
              <div className="flex items-center gap-2 min-w-0">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                  <FileText className="h-3 w-3" />
                </span>
                <p className="italic text-foreground/90 truncate text-[11px] sm:text-xs">
                  {activeCue ? `“${activeCue.textVi}”` : `Lời thuyết minh: ${currentTrack.titleVi}`}
                </p>
              </div>
              <span className="text-[10px] text-primary font-medium shrink-0 group-hover:underline">
                Xem lời thoại
              </span>
            </div>

            {/* Seekbar and Timestamps */}
            <div className="space-y-1">
              <div className="relative flex items-center group">
                <input
                  type="range"
                  min={0}
                  max={duration || currentTrack.duration || 120}
                  step={0.5}
                  value={currentTime}
                  onChange={(e) => {
                    const target = parseFloat(e.target.value);
                    seekTo(target);
                  }}
                  className="w-full h-1.5 bg-secondary group-hover:h-2.5 rounded-lg appearance-none cursor-pointer accent-primary transition-all duration-150 focus:outline-none"
                  aria-label="Thanh tiến trình âm thanh"
                />
              </div>

              <div className="flex items-center justify-between text-[11px] font-mono text-muted-foreground px-0.5">
                <span>{formatAudioTime(currentTime)}</span>
                <span>{formatAudioTime(duration || currentTrack.duration)}</span>
              </div>
            </div>

            {/* Bottom Controls Row: Rewind, Play/Pause, Forward, Speed, Volume, Transcript */}
            <div className="flex items-center justify-between pt-1">
              {/* Left group: Speed selector (0.75x, 1x, 1.25x, 1.5x), Volume & Soundscapes */}
              <div className="flex items-center gap-1.5">
                {/* Speed selector dropdown/cycler */}
                <div
                  className="relative flex items-center"
                  onMouseEnter={() => setShowSpeedSelector(true)}
                  onMouseLeave={() => setShowSpeedSelector(false)}
                >
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={cyclePlaybackRate}
                        className="h-8 px-2 text-xs font-mono font-bold text-foreground hover:bg-secondary border-border/70"
                        aria-label={`Tốc độ phát: ${playbackRate}x`}
                      >
                        {playbackRate}x
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="top">Tốc độ: {playbackRate}x (0.75x, 1x, 1.25x, 1.5x)</TooltipContent>
                  </Tooltip>

                  {showSpeedSelector && (
                    <div className="absolute left-0 bottom-9 bg-card border border-border/80 p-1 rounded-lg shadow-xl flex items-center gap-1 z-30 animate-in fade-in slide-in-from-bottom-1">
                      {([0.75, 1.0, 1.25, 1.5] as PlaybackRate[]).map((rate) => (
                        <button
                          key={rate}
                          type="button"
                          onClick={() => {
                            setPlaybackRate(rate);
                            setShowSpeedSelector(false);
                          }}
                          className={cn(
                            "px-1.5 py-0.5 text-[10px] font-mono rounded font-semibold transition-colors",
                            playbackRate === rate
                              ? "bg-primary text-primary-foreground"
                              : "hover:bg-secondary text-foreground",
                          )}
                        >
                          {rate}x
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Volume Control Popover / Hover */}
                <div
                  className="relative flex items-center"
                  onMouseEnter={() => setShowVolumeSlider(true)}
                  onMouseLeave={() => setShowVolumeSlider(false)}
                >
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={toggleMute}
                    className="h-8 w-8 text-muted-foreground hover:text-foreground"
                    title={isMuted ? "Bật âm" : "Tắt tiếng"}
                  >
                    {isMuted || volume === 0 ? (
                      <VolumeX className="h-4 w-4 text-destructive" />
                    ) : (
                      <Volume2 className="h-4 w-4" />
                    )}
                  </Button>

                  {showVolumeSlider && (
                    <div className="absolute left-8 bottom-0 bg-card border border-border/70 p-2 rounded-lg shadow-xl flex items-center w-24 z-20 animate-in fade-in slide-in-from-left-1">
                      <input
                        type="range"
                        min={0}
                        max={1}
                        step={0.05}
                        value={isMuted ? 0 : volume}
                        onChange={(e) => setVolume(parseFloat(e.target.value))}
                        className="w-full h-1 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary"
                        aria-label="Thanh âm lượng"
                      />
                    </div>
                  )}
                </div>

                {/* Soundscapes: Thien Mu Bell & Court Music Chimes */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => playThienMuBellSound({ volume: 0.8 })}
                      className="h-8 w-8 text-amber-500 hover:text-amber-400 hover:bg-amber-500/10"
                      aria-label="Tiếng chuông chùa Thiên Mụ"
                    >
                      <Bell className="h-3.5 w-3.5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="top">Âm vang tiếng chuông chùa Thiên Mụ</TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => playNhaNhacChime({ volume: 0.75 })}
                      className="h-8 w-8 text-primary hover:text-primary/80 hover:bg-primary/10"
                      aria-label="Nhã nhạc cung đình Huế"
                    >
                      <Music className="h-3.5 w-3.5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="top">Nhã nhạc cung đình âm vang (Biên Chung/Biên Khánh)</TooltipContent>
                </Tooltip>
              </div>

              {/* Center group: Skip -10s, Play/Pause, Skip +10s */}
              <div className="flex items-center gap-2">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => skipTime(-10)}
                      className="h-8 w-8 text-muted-foreground hover:text-foreground"
                      aria-label="Lùi 10 giây"
                    >
                      <RotateCcw className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="top">Lùi 10 giây</TooltipContent>
                </Tooltip>

                <Button
                  size="icon"
                  onClick={togglePlayPause}
                  className="h-10 w-10 rounded-full bg-gradient-to-r from-primary to-amber-600 text-primary-foreground shadow-lg hover:brightness-110 active:scale-95 transition-transform"
                  aria-label={isPlaying ? "Tạm dừng" : "Phát"}
                >
                  {isPlaying ? (
                    <Pause className="h-5 w-5 fill-current" />
                  ) : (
                    <Play className="h-5 w-5 fill-current ml-0.5" />
                  )}
                </Button>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => skipTime(10)}
                      className="h-8 w-8 text-muted-foreground hover:text-foreground"
                      aria-label="Tua tới 10 giây"
                    >
                      <RotateCw className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="top">Tua tới 10 giây</TooltipContent>
                </Tooltip>
              </div>

              {/* Right group: Open Transcript Drawer Button */}
              <Button
                size="sm"
                variant={isDrawerOpen ? "secondary" : "outline"}
                onClick={toggleDrawer}
                className={cn(
                  "h-8 px-2.5 text-xs font-medium flex items-center gap-1.5 transition-colors border-border/70",
                  isDrawerOpen && "bg-primary/20 text-primary border-primary/40",
                )}
              >
                <FileText className="h-3.5 w-3.5 text-primary" />
                <span className="hidden sm:inline">Xem Lời Thoại</span>
                <span className="sm:hidden">Lời thoại</span>
              </Button>
            </div>
          </div>
        )}
      </aside>

      {/* Transcript Drawer Overlay */}
      <AudioTranscriptDrawer />
    </TooltipProvider>
  );
}
