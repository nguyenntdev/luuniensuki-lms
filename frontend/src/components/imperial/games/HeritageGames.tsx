"use client";

import React, { useState, useEffect, useMemo } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  Award,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  Compass,
  Crosshair,
  HelpCircle,
  History,
  Layers,
  Lightbulb,
  Link as LinkIcon,
  MapPin,
  RefreshCw,
  RotateCcw,
  Scroll,
  ShieldCheck,
  Sparkles,
  Trophy,
  Volume2,
  VolumeX,
  XCircle,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import type { GameQuestion, GameSubmitResult, ImperialClue } from "@/lib/imperial/v51-types";
import { fetchGameQuestions, submitGameAnswer, fetchClues } from "@/lib/imperial/v51-api";
import {
  playGameSuccessSound,
  playGameErrorSound,
  playGameHintSound,
  playGameClickSound,
  playGameVictorySound,
} from "@/lib/imperial/game-audio";
import { TimelineSequenceGame } from "./TimelineSequenceGame";
import { ImperialCipherGame } from "./ImperialCipherGame";
import { HeritageDetectiveWidget } from "@/components/imperial/detective/HeritageDetectiveWidget";
import { cn } from "@/lib/utils";

export type PrimaryGameType = "quiz" | "detective" | "timeline" | "cipher";
export type QuizSubMode = "all" | "multiple_choice" | "matching" | "hotspot_identify";

export interface HeritageGamesProps {
  initialQuestions?: GameQuestion[];
  siteSlug?: string;
  onGameComplete?: (totalScore: number) => void;
  className?: string;
  defaultGameCategory?: PrimaryGameType;
}

interface MatchingPairItem {
  id: string;
  left: string;
  right: string;
}

export function HeritageGames({
  initialQuestions,
  siteSlug,
  onGameComplete,
  className,
  defaultGameCategory = "quiz",
}: HeritageGamesProps) {
  // Top-Level Active Game Tab
  const [activeGameType, setActiveGameType] = useState<PrimaryGameType>(defaultGameCategory);

  // Sound Engine Toggle
  const [soundEnabled, setSoundEnabled] = useState<boolean>(true);

  // Shared XP Counter
  const [totalScore, setTotalScore] = useState<number>(0);

  // 1. Quizzes State
  const [questions, setQuestions] = useState<GameQuestion[]>(initialQuestions || []);
  const [loadingQuestions, setLoadingQuestions] = useState<boolean>(!initialQuestions || initialQuestions.length === 0);
  const [selectedQuizMode, setSelectedQuizMode] = useState<QuizSubMode>("all");
  const [currentQuizIndex, setCurrentQuizIndex] = useState<number>(0);
  const [isQuizHintRevealed, setIsQuizHintRevealed] = useState<boolean>(false);

  // Deep Comprehension State
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [submittedResult, setSubmittedResult] = useState<GameSubmitResult | null>(null);

  // Matching Challenge State
  const [selectedLeft, setSelectedLeft] = useState<number | null>(null);
  const [selectedRight, setSelectedRight] = useState<number | null>(null);
  const [matchedPairs, setMatchedPairs] = useState<Record<number, number>>({});
  const [matchingValidated, setMatchingValidated] = useState<boolean>(false);

  // Hotspot Identify State
  const [selectedHotspotIndex, setSelectedHotspotIndex] = useState<number | null>(null);
  const [hotspotSubmitted, setHotspotSubmitted] = useState<boolean>(false);

  // 2. Detective Clues State
  const [clues, setClues] = useState<ImperialClue[]>([]);
  const [loadingClues, setLoadingClues] = useState<boolean>(true);
  const [selectedClueIndex, setSelectedClueIndex] = useState<number>(0);
  const [solvedClueIds, setSolvedClueIds] = useState<string[]>([]);

  // Load Questions
  useEffect(() => {
    let mounted = true;
    async function load() {
      if (initialQuestions && initialQuestions.length > 0) return;
      try {
        setLoadingQuestions(true);
        const data = await fetchGameQuestions(siteSlug);
        if (mounted) {
          setQuestions(data);
        }
      } catch (err) {
        console.error("Failed to fetch game questions:", err);
      } finally {
        if (mounted) setLoadingQuestions(false);
      }
    }
    load();
    return () => {
      mounted = false;
    };
  }, [initialQuestions, siteSlug]);

  // Load Detective Clues
  useEffect(() => {
    let mounted = true;
    async function loadClues() {
      try {
        setLoadingClues(true);
        const data = await fetchClues();
        if (mounted) {
          if (siteSlug) {
            const filtered = data.filter((c) => c.target_slug === siteSlug);
            setClues(filtered.length > 0 ? filtered : data);
          } else {
            setClues(data);
          }
        }
      } catch (err) {
        console.error("Failed to fetch clues for game arena:", err);
      } finally {
        if (mounted) setLoadingClues(false);
      }
    }
    loadClues();
    return () => {
      mounted = false;
    };
  }, [siteSlug]);

  // Filter questions by quiz sub-mode
  const filteredQuestions = useMemo(() => {
    if (selectedQuizMode === "all") return questions;
    return questions.filter((q) => q.question_type === selectedQuizMode);
  }, [questions, selectedQuizMode]);

  const activeQuestion = filteredQuestions[currentQuizIndex] || filteredQuestions[0];
  const activeClue = clues[selectedClueIndex] || clues[0];

  // Reset internal item states when changing question
  const handleSelectQuestion = (idx: number) => {
    setCurrentQuizIndex(idx);
    setSelectedOption(null);
    setSubmittedResult(null);
    setSelectedLeft(null);
    setSelectedRight(null);
    setMatchedPairs({});
    setMatchingValidated(false);
    setSelectedHotspotIndex(null);
    setHotspotSubmitted(false);
    setIsQuizHintRevealed(false);
    if (soundEnabled) playGameClickSound();
  };

  const handleScoreAdd = (points: number) => {
    setTotalScore((prev) => {
      const next = prev + points;
      if (onGameComplete) onGameComplete(next);
      return next;
    });
  };

  // --- Handlers for Mode 1: Multiple Choice (Hiểu Sâu) ---
  const handleSubmitMultipleChoice = async () => {
    if (selectedOption === null || !activeQuestion) return;
    try {
      const res = await submitGameAnswer(activeQuestion.id, selectedOption);
      setSubmittedResult(res);
      if (res.correct) {
        if (soundEnabled) playGameSuccessSound();
        handleScoreAdd(res.score_delta || 50);
      } else {
        if (soundEnabled) playGameErrorSound();
      }
    } catch {
      const correctIdx = activeQuestion.answer_key
        ? parseInt(activeQuestion.answer_key, 10)
        : 1;
      const isCorrect = selectedOption === correctIdx;
      const res: GameSubmitResult = {
        correct: isCorrect,
        correct_index: correctIdx,
        explanation:
          activeQuestion.explanation_why ||
          "Dữ liệu lịch sử đã được đối chiếu theo chính sử triều Nguyễn.",
        score_delta: isCorrect ? 50 : 0,
      };
      setSubmittedResult(res);
      if (isCorrect) {
        if (soundEnabled) playGameSuccessSound();
        handleScoreAdd(50);
      } else {
        if (soundEnabled) playGameErrorSound();
      }
    }
  };

  // --- Handlers for Mode 2: Matching Challenge ---
  const matchingData = useMemo(() => {
    if (!activeQuestion || activeQuestion.question_type !== "matching") return null;
    const pairs: MatchingPairItem[] = (activeQuestion.options || []).map((opt, i) => {
      const parts = opt.split("<->");
      return {
        id: `pair-${i}`,
        left: parts[0]?.trim() || `Yếu tố ${i + 1}`,
        right: parts[1]?.trim() || `Ý nghĩa ${i + 1}`,
      };
    });
    // Deterministic shuffle of right items to test learner pairing
    const rightShuffled = [...pairs].map((p, i) => ({ text: p.right, originalIdx: i }));
    if (pairs.length > 2) {
      const temp = rightShuffled[0];
      rightShuffled[0] = rightShuffled[1];
      rightShuffled[1] = temp;
    }
    return { pairs, rightShuffled };
  }, [activeQuestion]);

  const handlePairSelection = (leftIdx: number, rightIdx: number) => {
    if (soundEnabled) playGameClickSound();
    setMatchedPairs((prev) => ({
      ...prev,
      [leftIdx]: rightIdx,
    }));
    setSelectedLeft(null);
    setSelectedRight(null);
  };

  const handleValidateMatching = () => {
    if (!matchingData) return;
    setMatchingValidated(true);
    let correctCount = 0;
    matchingData.pairs.forEach((_, leftIdx) => {
      const chosenRightIdx = matchedPairs[leftIdx];
      if (chosenRightIdx !== undefined) {
        const originalIdx = matchingData.rightShuffled[chosenRightIdx]?.originalIdx;
        if (originalIdx === leftIdx) {
          correctCount++;
        }
      }
    });
    const isAllCorrect = correctCount === matchingData.pairs.length;
    if (isAllCorrect) {
      if (soundEnabled) playGameSuccessSound();
      handleScoreAdd(60);
    } else {
      if (soundEnabled) playGameErrorSound();
    }
  };

  // --- Handlers for Mode 3: Hotspot Identify Challenge ---
  const handleSelectHotspotOption = (idx: number) => {
    if (hotspotSubmitted) return;
    if (soundEnabled) playGameClickSound();
    setSelectedHotspotIndex(idx);
  };

  const handleSubmitHotspot = () => {
    if (selectedHotspotIndex === null || !activeQuestion) return;
    setHotspotSubmitted(true);
    const correctIdx = activeQuestion.answer_key
      ? parseInt(activeQuestion.answer_key, 10)
      : 0;
    if (selectedHotspotIndex === correctIdx) {
      if (soundEnabled) playGameSuccessSound();
      handleScoreAdd(50);
    } else {
      if (soundEnabled) playGameErrorSound();
    }
  };

  const handleNextQuestion = () => {
    if (currentQuizIndex < filteredQuestions.length - 1) {
      handleSelectQuestion(currentQuizIndex + 1);
    } else {
      if (soundEnabled) playGameVictorySound();
    }
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* 4 Primary Game Mode Selector Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border/80 pb-3">
        <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
          <Button
            variant={activeGameType === "quiz" ? "default" : "outline"}
            size="sm"
            onClick={() => {
              setActiveGameType("quiz");
              if (soundEnabled) playGameClickSound();
            }}
            className="text-xs h-9 gap-1.5 font-semibold px-3 touch-manipulation"
          >
            <BookOpen className="size-3.5" />
            <span>Trắc nghiệm di sản</span>
          </Button>

          <Button
            variant={activeGameType === "detective" ? "default" : "outline"}
            size="sm"
            onClick={() => {
              setActiveGameType("detective");
              if (soundEnabled) playGameClickSound();
            }}
            className="text-xs h-9 gap-1.5 font-semibold px-3 touch-manipulation"
          >
            <Compass className="size-3.5" />
            <span>Thám tử cổ vật</span>
          </Button>

          <Button
            variant={activeGameType === "timeline" ? "default" : "outline"}
            size="sm"
            onClick={() => {
              setActiveGameType("timeline");
              if (soundEnabled) playGameClickSound();
            }}
            className="text-xs h-9 gap-1.5 font-semibold px-3 touch-manipulation"
          >
            <History className="size-3.5" />
            <span>Sắp xếp niên biểu</span>
          </Button>

          <Button
            variant={activeGameType === "cipher" ? "default" : "outline"}
            size="sm"
            onClick={() => {
              setActiveGameType("cipher");
              if (soundEnabled) playGameClickSound();
            }}
            className="text-xs h-9 gap-1.5 font-semibold px-3 touch-manipulation"
          >
            <Scroll className="size-3.5" />
            <span>Giải mã mật mã</span>
          </Button>
        </div>

        {/* Global Sound & Score Bar */}
        <div className="flex items-center justify-between sm:justify-end gap-2.5">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSoundEnabled((prev) => !prev)}
            className="size-8 text-muted-foreground hover:text-foreground"
            title={soundEnabled ? "Tắt âm thanh hiệu ứng" : "Bật âm thanh hiệu ứng"}
          >
            {soundEnabled ? <Volume2 className="size-4" /> : <VolumeX className="size-4" />}
          </Button>

          <Badge className="bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/30 text-xs font-semibold gap-1.5 py-1 px-3">
            <Trophy className="size-3.5 text-amber-500" />
            <span>Điểm tích lũy: {totalScore} XP</span>
          </Badge>
        </div>
      </div>

      {/* ==================================================================== */}
      {/* TAB 1: TRẮC NGHIỆM DI SẢN (QUIZZES & SPATIAL HOTSPOTS)               */}
      {/* ==================================================================== */}
      {activeGameType === "quiz" && (
        <div className="space-y-6">
          {/* Quiz Sub-mode Filter */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-1.5">
              <Button
                variant={selectedQuizMode === "all" ? "default" : "outline"}
                size="sm"
                onClick={() => {
                  setSelectedQuizMode("all");
                  handleSelectQuestion(0);
                }}
                className="text-xs h-8"
              >
                Tất cả ({questions.length})
              </Button>
              <Button
                variant={selectedQuizMode === "multiple_choice" ? "default" : "outline"}
                size="sm"
                onClick={() => {
                  setSelectedQuizMode("multiple_choice");
                  handleSelectQuestion(0);
                }}
                className="text-xs h-8 gap-1.5"
              >
                <BookOpen className="size-3" />
                <span>Trắc nghiệm hiểu sâu</span>
              </Button>
              <Button
                variant={selectedQuizMode === "matching" ? "default" : "outline"}
                size="sm"
                onClick={() => {
                  setSelectedQuizMode("matching");
                  handleSelectQuestion(0);
                }}
                className="text-xs h-8 gap-1.5"
              >
                <LinkIcon className="size-3" />
                <span>Ghép chi tiết - Ý nghĩa</span>
              </Button>
              <Button
                variant={selectedQuizMode === "hotspot_identify" ? "default" : "outline"}
                size="sm"
                onClick={() => {
                  setSelectedQuizMode("hotspot_identify");
                  handleSelectQuestion(0);
                }}
                className="text-xs h-8 gap-1.5"
              >
                <Crosshair className="size-3" />
                <span>Định vị chi tiết</span>
              </Button>
            </div>

            <span className="text-xs text-muted-foreground font-medium">
              Câu {currentQuizIndex + 1}/{filteredQuestions.length || 1}
            </span>
          </div>

          {loadingQuestions ? (
            <div className="p-8 text-center text-muted-foreground flex flex-col items-center gap-3">
              <RefreshCw className="size-6 animate-spin text-primary" />
              <span className="text-sm">Đang tải câu hỏi tương tác Đại Nội Huế...</span>
            </div>
          ) : filteredQuestions.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground border rounded-2xl bg-card">
              <Sparkles className="size-8 mx-auto mb-2 text-primary/60" />
              <p className="text-sm">Chưa có câu hỏi tương tác nào trong danh mục này.</p>
            </div>
          ) : activeQuestion ? (
            <Card className="border border-border/80 shadow-lg bg-card/95 overflow-hidden">
              <div className="px-5 py-3 border-b border-border/60 bg-muted/30 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-xs font-semibold uppercase tracking-wider">
                    {activeQuestion.question_type === "multiple_choice"
                      ? "Hiểu sâu (Vì sao)"
                      : activeQuestion.question_type === "matching"
                      ? "Ghép nối biểu tượng"
                      : "Định vị không gian"}
                  </Badge>
                  {activeQuestion.site_slug && (
                    <span className="text-xs text-muted-foreground font-serif">
                      Di tích: <strong className="text-foreground capitalize">{activeQuestion.site_slug.replace(/-/g, " ")}</strong>
                    </span>
                  )}
                </div>

                <Badge variant="secondary" className="text-[11px] font-bold">
                  +{activeQuestion.points || 50} XP
                </Badge>
              </div>

              <CardContent className="p-5 sm:p-7 space-y-6">
                <div className="space-y-2">
                  <h3 className="font-serif font-bold text-lg sm:text-xl text-foreground leading-snug">
                    {activeQuestion.prompt}
                  </h3>
                </div>

                {/* Sub-mode 1: Multiple Choice */}
                {activeQuestion.question_type === "multiple_choice" && (
                  <div className="space-y-4">
                    <div className="space-y-2.5">
                      {(activeQuestion.options || []).map((opt, idx) => {
                        const isSelected = selectedOption === idx;
                        const isResultShown = submittedResult !== null;
                        const isCorrect = submittedResult?.correct_index === idx;
                        const isWrongSelected = isResultShown && isSelected && !submittedResult.correct;

                        return (
                          <button
                            key={idx}
                            disabled={isResultShown}
                            onClick={() => {
                              setSelectedOption(idx);
                              if (soundEnabled) playGameClickSound();
                            }}
                            className={cn(
                              "w-full text-left p-3.5 sm:p-4 rounded-xl border text-xs sm:text-sm transition-all flex items-start gap-3 touch-manipulation min-h-[44px]",
                              isSelected && !isResultShown
                                ? "border-primary bg-primary/10 shadow-sm font-medium"
                                : "border-border/60 hover:bg-muted/30 bg-background",
                              isResultShown && isCorrect
                                ? "border-emerald-500 bg-emerald-500/10 text-emerald-950 dark:text-emerald-200 font-semibold"
                                : "",
                              isWrongSelected
                                ? "border-rose-500 bg-rose-500/10 text-rose-950 dark:text-rose-200"
                                : "",
                            )}
                          >
                            <span
                              className={cn(
                                "flex size-6 shrink-0 items-center justify-center rounded-full text-xs font-bold border",
                                isSelected && !isResultShown
                                  ? "bg-primary text-primary-foreground border-primary"
                                  : "border-border bg-muted/50 text-muted-foreground",
                                isResultShown && isCorrect
                                  ? "bg-emerald-600 text-white border-emerald-600"
                                  : "",
                                isWrongSelected
                                  ? "bg-rose-600 text-white border-rose-600"
                                  : "",
                              )}
                            >
                              {String.fromCharCode(65 + idx)}
                            </span>
                            <span className="flex-1 leading-relaxed">{opt}</span>
                          </button>
                        );
                      })}
                    </div>

                    {/* Hint Box for Multiple Choice */}
                    {isQuizHintRevealed && (
                      <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-3 text-xs text-amber-950 dark:text-amber-200 flex items-start gap-2 animate-in fade-in">
                        <Lightbulb className="size-4 text-amber-500 shrink-0 mt-0.5" />
                        <span>
                          <strong>Gợi ý sư phạm:</strong> Hãy liên hệ với quy chế cung đình triều Nguyễn và điển lễ Nho giáo về trật tự đế vương và âm dương ngũ hành.
                        </span>
                      </div>
                    )}

                    {!submittedResult && (
                      <div className="flex items-center justify-between pt-2 border-t border-border/50">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setIsQuizHintRevealed(true);
                            if (soundEnabled) playGameHintSound();
                          }}
                          disabled={isQuizHintRevealed}
                          className="text-xs h-8 gap-1.5 border-dashed"
                        >
                          <HelpCircle className="size-3.5 text-amber-500" />
                          <span>{isQuizHintRevealed ? "Đã mở gợi ý" : "Gợi ý lịch sử"}</span>
                        </Button>

                        <Button
                          onClick={handleSubmitMultipleChoice}
                          disabled={selectedOption === null}
                          className="gap-2 bg-primary text-primary-foreground font-semibold px-5 h-9 text-xs"
                        >
                          <span>Kiểm tra câu trả lời</span>
                          <ChevronRight className="size-4" />
                        </Button>
                      </div>
                    )}
                  </div>
                )}

                {/* Sub-mode 2: Matching Challenge */}
                {activeQuestion.question_type === "matching" && matchingData && (
                  <div className="space-y-5">
                    <p className="text-xs text-muted-foreground italic">
                      💡 Nhấp vào một chi tiết cột bên trái, sau đó nhấp vào ý nghĩa biểu tượng tương ứng ở cột bên phải để nối cặp.
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Left Column */}
                      <div className="space-y-2">
                        <span className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground block">
                          Chi tiết / Họa tiết mỹ thuật:
                        </span>
                        {matchingData.pairs.map((p, lIdx) => {
                          const isPaired = matchedPairs[lIdx] !== undefined;
                          const isSelected = selectedLeft === lIdx;
                          return (
                            <button
                              key={lIdx}
                              disabled={matchingValidated}
                              onClick={() => {
                                setSelectedLeft(lIdx);
                                if (soundEnabled) playGameClickSound();
                                if (selectedRight !== null) {
                                  handlePairSelection(lIdx, selectedRight);
                                }
                              }}
                              className={cn(
                                "w-full text-left p-3.5 rounded-xl border text-xs sm:text-sm transition-all flex items-center justify-between gap-2 touch-manipulation min-h-[44px]",
                                isSelected
                                  ? "border-primary bg-primary/10 ring-2 ring-primary/40 font-semibold text-primary"
                                  : isPaired
                                  ? "border-emerald-500/60 bg-emerald-500/5 text-foreground font-medium"
                                  : "border-border/70 hover:bg-muted/40 bg-background",
                              )}
                            >
                              <span>{p.left}</span>
                              {isPaired && (
                                <Badge variant="outline" className="text-[10px] bg-background">
                                  Đã ghép
                                </Badge>
                              )}
                            </button>
                          );
                        })}
                      </div>

                      {/* Right Column */}
                      <div className="space-y-2">
                        <span className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground block">
                          Ý nghĩa biểu tượng lịch sử:
                        </span>
                        {matchingData.rightShuffled.map((item, rIdx) => {
                          const isPaired = Object.values(matchedPairs).includes(rIdx);
                          const isSelected = selectedRight === rIdx;
                          return (
                            <button
                              key={rIdx}
                              disabled={matchingValidated}
                              onClick={() => {
                                setSelectedRight(rIdx);
                                if (soundEnabled) playGameClickSound();
                                if (selectedLeft !== null) {
                                  handlePairSelection(selectedLeft, rIdx);
                                }
                              }}
                              className={cn(
                                "w-full text-left p-3.5 rounded-xl border text-xs sm:text-sm transition-all flex items-center justify-between gap-2 touch-manipulation min-h-[44px]",
                                isSelected
                                  ? "border-primary bg-primary/10 ring-2 ring-primary/40 font-semibold text-primary"
                                  : isPaired
                                  ? "border-emerald-500/60 bg-emerald-500/5 text-foreground font-medium"
                                  : "border-border/70 hover:bg-muted/40 bg-background",
                              )}
                            >
                              <span className="line-clamp-2">{item.text}</span>
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    {!matchingValidated && (
                      <div className="flex items-center justify-between pt-2 border-t border-border/50">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setMatchedPairs({});
                            setSelectedLeft(null);
                            setSelectedRight(null);
                            if (soundEnabled) playGameClickSound();
                          }}
                          className="text-xs text-muted-foreground"
                        >
                          <RotateCcw className="size-3.5 mr-1" />
                          Làm lại ghép đôi
                        </Button>

                        <Button
                          onClick={handleValidateMatching}
                          disabled={Object.keys(matchedPairs).length !== matchingData.pairs.length}
                          className="gap-2 bg-primary text-primary-foreground font-semibold text-xs h-9"
                        >
                          <span>Xác nhận kết quả ghép</span>
                          <ChevronRight className="size-4" />
                        </Button>
                      </div>
                    )}
                  </div>
                )}

                {/* Sub-mode 3: Hotspot Identify */}
                {activeQuestion.question_type === "hotspot_identify" && (
                  <div className="space-y-4">
                    <p className="text-xs text-muted-foreground italic">
                      💡 Nhấp vào vùng mô tả phù hợp nhất với vị trí cấu kiện kiến trúc trên công trình:
                    </p>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {(activeQuestion.options || []).map((opt, idx) => {
                        const isSelected = selectedHotspotIndex === idx;
                        const isCorrect =
                          hotspotSubmitted &&
                          idx === (activeQuestion.answer_key ? parseInt(activeQuestion.answer_key, 10) : 0);
                        const isWrong = hotspotSubmitted && isSelected && !isCorrect;

                        return (
                          <button
                            key={idx}
                            disabled={hotspotSubmitted}
                            onClick={() => handleSelectHotspotOption(idx)}
                            className={cn(
                              "p-4 rounded-xl border text-left text-xs sm:text-sm transition-all flex items-start gap-3 touch-manipulation min-h-[48px]",
                              isSelected && !hotspotSubmitted
                                ? "border-primary bg-primary/10 font-semibold ring-2 ring-primary/30"
                                : "border-border/60 hover:bg-muted/30 bg-background",
                              isCorrect
                                ? "border-emerald-500 bg-emerald-500/10 text-emerald-950 dark:text-emerald-200 font-semibold"
                                : "",
                              isWrong ? "border-rose-500 bg-rose-500/10 text-rose-950 dark:text-rose-200" : "",
                            )}
                          >
                            <Crosshair className="size-4 text-primary shrink-0 mt-0.5" />
                            <span className="leading-relaxed">{opt}</span>
                          </button>
                        );
                      })}
                    </div>

                    {!hotspotSubmitted && (
                      <div className="flex justify-end pt-2 border-t border-border/50">
                        <Button
                          onClick={handleSubmitHotspot}
                          disabled={selectedHotspotIndex === null}
                          className="gap-2 bg-primary text-primary-foreground font-semibold text-xs h-9"
                        >
                          <span>Xác nhận vị trí</span>
                          <ChevronRight className="size-4" />
                        </Button>
                      </div>
                    )}
                  </div>
                )}

                {/* Immediate Pedagogical Feedback */}
                {(submittedResult || matchingValidated || hotspotSubmitted) && (
                  <div className="rounded-2xl border border-primary/20 bg-primary/5 p-4 sm:p-5 space-y-3 animate-in fade-in slide-in-from-top-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Sparkles className="size-4 text-primary" />
                        <span className="font-serif font-bold text-sm text-foreground">
                          Giải Thích Sư Phạm & Chứng Cứ Lịch Sử:
                        </span>
                      </div>

                      <Badge className="bg-emerald-600 text-white text-xs font-semibold">
                        Đã hoàn thành thử thách
                      </Badge>
                    </div>

                    <p className="text-xs sm:text-sm text-foreground/90 leading-relaxed font-serif">
                      {submittedResult?.explanation || activeQuestion.explanation_why}
                    </p>

                    {activeQuestion.source_citation && (
                      <div className="rounded-lg border border-border/60 bg-background/80 p-2.5 text-xs text-muted-foreground flex items-start gap-2">
                        <BookOpen className="size-3.5 text-primary shrink-0 mt-0.5" />
                        <span>
                          <strong>Nguồn chính sử đối chiếu:</strong> {activeQuestion.source_citation}
                        </span>
                      </div>
                    )}

                    <div className="flex justify-end pt-2 border-t border-border/50">
                      <Button
                        onClick={handleNextQuestion}
                        className="gap-2 bg-primary text-primary-foreground font-semibold text-xs h-9"
                      >
                        <span>
                          {currentQuizIndex < filteredQuestions.length - 1
                            ? "Thử thách tiếp theo"
                            : "Hoàn tất danh mục này"}
                        </span>
                        <ChevronRight className="size-4" />
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ) : null}
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 2: THÁM TỬ CỔ VẬT (HERITAGE DETECTIVE RIDDLES)                   */}
      {/* ==================================================================== */}
      {activeGameType === "detective" && (
        <div className="space-y-6">
          <div className="space-y-2">
            <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider block">
              Hồ sơ câu đố thám tử di sản đang mở:
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
              {clues.map((c, idx) => {
                const isSelected = idx === selectedClueIndex;
                const isSolved = solvedClueIds.includes(c.id);
                return (
                  <button
                    key={c.id}
                    onClick={() => {
                      setSelectedClueIndex(idx);
                      if (soundEnabled) playGameClickSound();
                    }}
                    className={cn(
                      "text-left p-3 rounded-xl border text-xs transition-all flex items-start justify-between gap-2 touch-manipulation min-h-[50px]",
                      isSelected
                        ? "border-primary bg-primary/10 font-semibold text-primary shadow-xs ring-1 ring-primary/40"
                        : "border-border/60 hover:bg-muted/40 text-foreground bg-card",
                    )}
                  >
                    <div className="space-y-0.5 truncate">
                      <span className="block truncate font-medium">
                        {idx + 1}. {c.title}
                      </span>
                      <span className="text-[10px] text-muted-foreground block">
                        Độ khó: {c.difficulty || "Cơ bản"} • +{c.points || 50} XP
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

          {activeClue ? (
            <HeritageDetectiveWidget
              key={activeClue.id}
              clue={activeClue}
              currentSiteSlug={siteSlug}
              onClueSolved={(clueId, pts) => {
                setSolvedClueIds((prev) => (prev.includes(clueId) ? prev : [...prev, clueId]));
                handleScoreAdd(pts);
              }}
            />
          ) : (
            <div className="p-8 text-center text-muted-foreground border rounded-2xl bg-card">
              Đang tải danh sách câu đố thám tử...
            </div>
          )}
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 3: SẮP XẾP NIÊN BIỂU (TIMELINE SEQUENCE GAME)                     */}
      {/* ==================================================================== */}
      {activeGameType === "timeline" && (
        <TimelineSequenceGame onComplete={handleScoreAdd} />
      )}

      {/* ==================================================================== */}
      {/* TAB 4: GIẢI MÃ MẬT MÃ CUNG ĐÌNH (IMPERIAL CIPHER GAME)              */}
      {/* ==================================================================== */}
      {activeGameType === "cipher" && (
        <ImperialCipherGame onComplete={handleScoreAdd} />
      )}
    </div>
  );
}
