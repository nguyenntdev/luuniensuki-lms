"use client";

import React, { useState } from "react";
import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  FileText,
  HelpCircle,
  KeyRound,
  Lightbulb,
  RotateCcw,
  Scroll,
  Sparkles,
  Trophy,
  Volume2,
  VolumeX,
  XCircle,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  CIPHER_CHALLENGES,
  verifyCipherSubmission,
  type CipherChallenge,
} from "@/lib/imperial/games-data";
import {
  playGameSuccessSound,
  playGameErrorSound,
  playGameHintSound,
  playGameClickSound,
  playGameVictorySound,
} from "@/lib/imperial/game-audio";
import { cn } from "@/lib/utils";

export interface ImperialCipherGameProps {
  onComplete?: (score: number) => void;
  className?: string;
}

export function ImperialCipherGame({
  onComplete,
  className,
}: ImperialCipherGameProps) {
  const [activeChallengeIndex, setActiveChallengeIndex] = useState<number>(0);
  const activeChallenge = CIPHER_CHALLENGES[activeChallengeIndex] || CIPHER_CHALLENGES[0];

  const [selectedTokens, setSelectedTokens] = useState<string[]>([]);
  const [availableTokens, setAvailableTokens] = useState<string[]>([
    ...activeChallenge.scrambled_tokens,
  ]);
  const [revealedHintIndex, setRevealedHintIndex] = useState<number>(0);
  const [validationResult, setValidationResult] = useState<{
    validated: boolean;
    isCorrect: boolean;
    scoreAwarded: number;
    feedback: string;
  } | null>(null);

  const [soundEnabled, setSoundEnabled] = useState<boolean>(true);

  // Switch challenge
  const handleSelectChallenge = (index: number) => {
    setActiveChallengeIndex(index);
    const targetChallenge = CIPHER_CHALLENGES[index] || CIPHER_CHALLENGES[0];
    setSelectedTokens([]);
    setAvailableTokens([...targetChallenge.scrambled_tokens]);
    setRevealedHintIndex(0);
    setValidationResult(null);
    if (soundEnabled) playGameClickSound();
  };

  // Add token from pool into decoded slots
  const handlePickToken = (token: string, tokenIndex: number) => {
    if (validationResult?.isCorrect) return;
    if (soundEnabled) playGameClickSound();

    setSelectedTokens((prev) => [...prev, token]);
    setAvailableTokens((prev) => prev.filter((_, idx) => idx !== tokenIndex));
    setValidationResult(null);
  };

  // Return token from decoded slots back to pool
  const handleReturnToken = (token: string, tokenIndex: number) => {
    if (validationResult?.isCorrect) return;
    if (soundEnabled) playGameClickSound();

    setSelectedTokens((prev) => prev.filter((_, idx) => idx !== tokenIndex));
    setAvailableTokens((prev) => [...prev, token]);
    setValidationResult(null);
  };

  // Reset to original pool
  const handleReset = () => {
    setSelectedTokens([]);
    setAvailableTokens([...activeChallenge.scrambled_tokens]);
    setValidationResult(null);
    if (soundEnabled) playGameClickSound();
  };

  // Progressive hint reveal
  const handleRevealHint = () => {
    if (revealedHintIndex < activeChallenge.hint_steps.length) {
      setRevealedHintIndex((prev) => prev + 1);
      if (soundEnabled) playGameHintSound();
    }
  };

  // Submit and verify solution
  const handleVerify = () => {
    const result = verifyCipherSubmission(activeChallenge, selectedTokens);

    setValidationResult({
      validated: true,
      isCorrect: result.isCorrect,
      scoreAwarded: result.scoreAwarded,
      feedback: result.feedback,
    });

    if (result.isCorrect) {
      if (soundEnabled) playGameSuccessSound();
      if (onComplete) {
        onComplete(result.scoreAwarded);
      }
    } else {
      if (soundEnabled) playGameErrorSound();
    }
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border/60 pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Badge className="bg-purple-500/15 text-purple-700 dark:text-purple-300 border-purple-500/30 text-xs font-semibold gap-1.5 py-0.5 px-2.5">
              <Scroll className="size-3.5" />
              <span>Năng Lực S3 & S4 — Giải Mã Mật Mã Cung Đình</span>
            </Badge>
            <Badge variant="outline" className="text-xs">
              +{activeChallenge.points} XP
            </Badge>
          </div>
          <h3 className="font-serif font-bold text-lg sm:text-xl text-foreground">
            {activeChallenge.title}
          </h3>
          <p className="text-xs sm:text-sm text-muted-foreground">
            {activeChallenge.subtitle} • {activeChallenge.monument_name}
          </p>
        </div>

        {/* Audio Toggle & Progress */}
        <div className="flex items-center gap-2 shrink-0">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSoundEnabled((prev) => !prev)}
            className="size-8 text-muted-foreground hover:text-foreground"
            title={soundEnabled ? "Tắt âm thanh hiệu ứng" : "Bật âm thanh hiệu ứng"}
          >
            {soundEnabled ? <Volume2 className="size-4" /> : <VolumeX className="size-4" />}
          </Button>

          <span className="text-xs text-muted-foreground font-medium">
            Mật thư {activeChallengeIndex + 1}/{CIPHER_CHALLENGES.length}
          </span>
        </div>
      </div>

      {/* Challenge Navigation Tabs */}
      <div className="flex flex-wrap gap-2">
        {CIPHER_CHALLENGES.map((ch, idx) => (
          <Button
            key={ch.id}
            variant={idx === activeChallengeIndex ? "default" : "outline"}
            size="sm"
            onClick={() => handleSelectChallenge(idx)}
            className="text-xs h-8 gap-1.5"
          >
            <KeyRound className="size-3" />
            <span>Mật mã {idx + 1}: {ch.title.split("'")[1] || ch.title.split(" ")[2]}</span>
          </Button>
        ))}
      </div>

      {/* Main Parchment Cipher Card */}
      <Card className="border border-amber-500/30 shadow-lg bg-gradient-to-b from-card via-card to-amber-500/5 overflow-hidden">
        <CardHeader className="bg-muted/30 p-4 sm:p-5 border-b border-border/60">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-primary text-xs font-semibold">
              <BookOpen className="size-4" />
              <span>Bối cảnh di sản & Sử ký triều Nguyễn:</span>
            </div>
            <p className="text-xs sm:text-sm text-foreground/90 font-serif leading-relaxed italic border-l-2 border-primary/50 pl-3 py-0.5 bg-background/50 rounded-r-md">
              &ldquo;{activeChallenge.background_story}&rdquo;
            </p>
          </div>
        </CardHeader>

        <CardContent className="p-4 sm:p-6 space-y-6">
          {/* Challenge Prompt */}
          <div className="space-y-1">
            <h4 className="font-serif font-bold text-sm sm:text-base text-foreground flex items-center gap-2">
              <KeyRound className="size-4 text-amber-500 shrink-0" />
              <span>{activeChallenge.clue_prompt}</span>
            </h4>
          </div>

          {/* Decoding Output Area (Target Slots) */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span className="font-semibold uppercase tracking-wider text-[11px]">
                Khu vực giải mã mật thư:
              </span>
              <span>
                Đã đặt: {selectedTokens.length}/{activeChallenge.solution_tokens.length} mảnh ghép
              </span>
            </div>

            <div className="min-h-[72px] sm:min-h-[80px] p-3 rounded-2xl border-2 border-dashed border-amber-500/40 bg-background/60 flex flex-wrap items-center gap-2">
              {selectedTokens.length === 0 ? (
                <div className="w-full text-center py-3 text-xs text-muted-foreground/80 italic">
                  Chạm vào các thẻ từ khóa bên dưới để ghép vào mật thư hoàng cung...
                </div>
              ) : (
                selectedTokens.map((token, tIdx) => (
                  <button
                    key={tIdx}
                    disabled={validationResult?.isCorrect}
                    onClick={() => handleReturnToken(token, tIdx)}
                    className={cn(
                      "px-3.5 py-2 rounded-xl text-xs sm:text-sm font-serif font-semibold border transition-all flex items-center gap-1.5 shadow-sm active:scale-95 touch-manipulation min-h-[44px]",
                      validationResult?.isCorrect
                        ? "bg-emerald-600 text-white border-emerald-600 cursor-default"
                        : "bg-amber-500/15 border-amber-500/40 text-amber-950 dark:text-amber-200 hover:bg-rose-500/15 hover:border-rose-500/40 hover:text-rose-600",
                    )}
                    title="Chạm để gỡ khỏi mật thư"
                  >
                    <span>{token}</span>
                    {!validationResult?.isCorrect && (
                      <span className="text-[10px] opacity-60">×</span>
                    )}
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Available Word Bank (Source Tokens) */}
          {availableTokens.length > 0 && !validationResult?.isCorrect && (
            <div className="space-y-2">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground block">
                Kho từ khóa ngự chế & Mảnh ghép mật mã (Chạm để chọn):
              </span>
              <div className="flex flex-wrap gap-2.5">
                {availableTokens.map((token, idx) => (
                  <button
                    key={idx}
                    onClick={() => handlePickToken(token, idx)}
                    className="px-4 py-2.5 rounded-xl border border-border/80 bg-background hover:bg-primary/10 hover:border-primary/60 text-foreground font-serif font-medium text-xs sm:text-sm shadow-xs transition-all active:scale-95 touch-manipulation min-h-[44px]"
                  >
                    {token}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Progressive Hint Box */}
          {revealedHintIndex > 0 && (
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-3.5 space-y-2 animate-in fade-in">
              <span className="text-[11px] font-bold text-amber-700 dark:text-amber-300 uppercase tracking-wider block">
                Gợi ý văn tự ({revealedHintIndex}/{activeChallenge.hint_steps.length}):
              </span>
              <div className="space-y-1.5">
                {activeChallenge.hint_steps.slice(0, revealedHintIndex).map((hint, hIdx) => (
                  <div key={hIdx} className="text-xs text-amber-950 dark:text-amber-200 flex items-start gap-2">
                    <Lightbulb className="size-3.5 text-amber-500 shrink-0 mt-0.5" />
                    <span>{hint}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Action Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-border/60">
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRevealHint}
                disabled={revealedHintIndex >= activeChallenge.hint_steps.length || validationResult?.isCorrect}
                className="text-xs h-9 gap-1.5 border-dashed"
              >
                <HelpCircle className="size-3.5 text-amber-500" />
                <span>
                  {revealedHintIndex >= activeChallenge.hint_steps.length
                    ? "Đã mở hết gợi ý"
                    : `Gợi ý văn tự (${revealedHintIndex}/${activeChallenge.hint_steps.length})`}
                </span>
              </Button>

              {!validationResult?.isCorrect && selectedTokens.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleReset}
                  className="text-xs h-9 text-muted-foreground gap-1"
                >
                  <RotateCcw className="size-3" />
                  <span>Xếp lại</span>
                </Button>
              )}
            </div>

            {!validationResult?.isCorrect ? (
              <Button
                onClick={handleVerify}
                disabled={selectedTokens.length === 0}
                className="gap-2 bg-primary text-primary-foreground font-semibold text-xs h-9 px-5 shadow-sm"
              >
                <span>Giải mã mật thư</span>
                <KeyRound className="size-3.5" />
              </Button>
            ) : (
              <Button
                onClick={() => {
                  if (activeChallengeIndex < CIPHER_CHALLENGES.length - 1) {
                    handleSelectChallenge(activeChallengeIndex + 1);
                  } else {
                    if (soundEnabled) playGameVictorySound();
                  }
                }}
                className="gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs h-9 px-5 shadow-sm"
              >
                <span>
                  {activeChallengeIndex < CIPHER_CHALLENGES.length - 1
                    ? "Mật thư tiếp theo"
                    : "Hoàn tất giải mã cung đình"}
                </span>
                <ArrowRight className="size-4" />
              </Button>
            )}
          </div>

          {/* Result Feedback Banner */}
          {validationResult && (
            <div
              className={cn(
                "rounded-2xl border p-4 sm:p-5 space-y-3 animate-in fade-in slide-in-from-top-2",
                validationResult.isCorrect
                  ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-950 dark:text-emerald-200"
                  : "border-amber-500/40 bg-amber-500/10 text-amber-950 dark:text-amber-200",
              )}
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  {validationResult.isCorrect ? (
                    <Sparkles className="size-5 text-emerald-600 dark:text-emerald-400 shrink-0" />
                  ) : (
                    <XCircle className="size-5 text-amber-600 shrink-0" />
                  )}
                  <span className="font-serif font-bold text-sm sm:text-base">
                    {validationResult.isCorrect
                      ? "Mật mã cung đình đã được giải mã chính xác!"
                      : "Mật mã chưa trùng khớp với điển lệ triều Nguyễn"}
                  </span>
                </div>

                {validationResult.isCorrect && (
                  <Badge className="bg-emerald-600 text-white font-bold text-xs">
                    +{validationResult.scoreAwarded} XP
                  </Badge>
                )}
              </div>

              <p className="text-xs sm:text-sm leading-relaxed">
                {validationResult.feedback}
              </p>

              {validationResult.isCorrect && (
                <div className="space-y-2 pt-2 border-t border-emerald-500/30">
                  <div className="text-xs font-serif leading-relaxed opacity-95">
                    <strong>Ý nghĩa văn hiến & Điển tích:</strong> {activeChallenge.explanation}
                  </div>

                  <div className="rounded-lg border border-border/60 bg-background/80 p-2 text-[11px] text-muted-foreground flex items-center gap-2">
                    <BookOpen className="size-3 text-primary shrink-0" />
                    <span>
                      <strong>Nguồn chính sử đối chiếu:</strong> {activeChallenge.source_citation}
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
