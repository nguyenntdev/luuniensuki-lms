"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import {
  Bot,
  Sparkles,
  X,
  Send,
  BookOpen,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  Maximize2,
  ChevronRight,
  ShieldAlert,
  ArrowRight,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  askImperialAiTutor,
  type ImperialAiMessage,
  SUGGESTED_INQUIRY_PROMPTS,
} from "@/lib/imperial/ai-assistant";
import { cn } from "@/lib/utils";

interface ImperialAiAssistantProps {
  contextMonumentSlug?: string;
  contextMonumentName?: string;
  className?: string;
  defaultOpen?: boolean;
}

export default function ImperialAiAssistant({
  contextMonumentSlug,
  contextMonumentName,
  className,
  defaultOpen = false,
}: ImperialAiAssistantProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const [inputQuery, setInputQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<ImperialAiMessage[]>([
    {
      id: "welcome_msg",
      role: "assistant",
      content: contextMonumentName
        ? `Xin chào! Tôi là Trợ lý Lịch sử Đại Nội Huế. Bạn đang tìm hiểu về di tích **${contextMonumentName}**. Hãy đặt câu hỏi hoặc chọn một gợi ý bên dưới để tra cứu sử liệu chính thức.`
        : "Xin chào! Tôi là Trợ lý Lịch sử Đại Nội Huế. Tôi có thể hỗ trợ bạn giải mã quy hoạch không gian, đối chiếu sử liệu chính thức và phân tích vai trò các di tích Hoàng Thành - Tử Cấm Thành.",
      timestamp: Date.now(),
      suggestedQuestions: contextMonumentName
        ? [
            `Ý nghĩa quy hoạch của ${contextMonumentName} là gì?`,
            `Sử liệu nào ghi chép về việc xây dựng ${contextMonumentName}?`,
            `Điều chắc chắn vs điều cần kiểm chứng tại ${contextMonumentName}?`,
          ]
        : SUGGESTED_INQUIRY_PROMPTS.slice(0, 3),
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto scroll to latest message
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen]);

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputQuery).trim();
    if (!query || loading) return;

    const userMessage: ImperialAiMessage = {
      id: `usr_${Date.now()}`,
      role: "user",
      content: query,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputQuery("");
    setLoading(true);

    try {
      const assistantMessage = await askImperialAiTutor({
        query,
        context_monument_slug: contextMonumentSlug,
      });
      setMessages((prev) => [...prev, assistantMessage]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          role: "assistant",
          content: "Đã có gián đoạn kết nối. Vui lòng thử lại với một câu hỏi lịch sử khác.",
          timestamp: Date.now(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className={cn("fixed bottom-5 right-5 z-40 print:hidden", className)}>
      {/* Floating Toggle Button */}
      {!isOpen && (
        <Button
          type="button"
          onClick={() => {
            setIsOpen(true);
            setTimeout(() => inputRef.current?.focus(), 150);
          }}
          className="relative h-13 px-4.5 rounded-full bg-primary hover:bg-primary/90 text-primary-foreground shadow-2xl flex items-center gap-2.5 transition-all duration-300 hover:scale-105 group border border-amber-300/30"
          aria-label="Mở Trợ lý Lịch sử AI Đại Nội"
        >
          <div className="relative flex items-center justify-center size-8 rounded-full bg-amber-500/20 group-hover:rotate-12 transition-transform">
            <Bot className="size-5 text-amber-200" />
            <span className="absolute -top-0.5 -right-0.5 flex size-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full size-2.5 bg-amber-500"></span>
            </span>
          </div>
          <div className="flex flex-col text-left">
            <span className="text-xs font-bold font-serif tracking-wide leading-none text-white">
              Trợ lý Lịch sử AI
            </span>
            <span className="text-[10px] text-amber-200 font-medium">
              {contextMonumentName ? `Hỏi về ${contextMonumentName}` : "Hỏi đáp & Đối chiếu sử liệu"}
            </span>
          </div>
        </Button>
      )}

      {/* Main Floating Assistant Window */}
      {isOpen && (
        <div
          role="region"
          aria-label="Cửa sổ Trợ lý Lịch sử AI Đại Nội Huế"
          className="flex flex-col w-[92vw] sm:w-[440px] h-[580px] max-h-[85vh] bg-card/95 backdrop-blur-xl border border-border/80 rounded-2xl shadow-2xl overflow-hidden transition-all duration-300 animate-in fade-in zoom-in-95"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 bg-secondary/60 border-b border-border/70">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="size-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0">
                <Sparkles className="size-4 text-primary" />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-1.5">
                  <h3 className="font-serif font-bold text-sm text-foreground truncate">
                    Trợ lý Lịch sử Đại Nội
                  </h3>
                  <span className="text-[10px] font-semibold px-1.5 py-0.2 rounded bg-amber-500/15 text-amber-700 dark:text-amber-400 border border-amber-500/30 shrink-0">
                    Sử liệu chuẩn
                  </span>
                </div>
                <p className="text-[11px] text-muted-foreground truncate">
                  {contextMonumentName ? `Đang khảo cứu: ${contextMonumentName}` : "Học tập dựa trên chứng cứ"}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <Link
                href="/dai-noi/ai"
                className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
                title="Mở toàn màn hình"
                aria-label="Mở trang hỏi đáp AI toàn màn hình"
              >
                <Maximize2 className="size-4" />
              </Link>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
                aria-label="Đóng trợ lý"
              >
                <X className="size-4" />
              </button>
            </div>
          </div>

          {/* Messages Feed */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 text-sm">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={cn(
                  "flex flex-col gap-1.5 max-w-[92%]",
                  msg.role === "user" ? "ml-auto items-end" : "mr-auto items-start",
                )}
              >
                {/* User Message Bubble */}
                {msg.role === "user" && (
                  <div className="px-3.5 py-2 rounded-2xl rounded-tr-sm bg-primary text-primary-foreground text-xs sm:text-sm font-medium shadow-sm">
                    {msg.content}
                  </div>
                )}

                {/* Assistant Message Bubble */}
                {msg.role === "assistant" && (
                  <div className="space-y-3 w-full">
                    {/* Scope Refusal Card */}
                    {msg.isScopeRefusal ? (
                      <div className="p-3.5 rounded-xl border border-rose-300/60 dark:border-rose-900/60 bg-rose-50/80 dark:bg-rose-950/40 text-foreground space-y-2">
                        <div className="flex items-start gap-2 text-rose-700 dark:text-rose-400 font-semibold text-xs">
                          <ShieldAlert className="size-4 shrink-0 mt-0.5" />
                          <span>Giới hạn phạm vi đề tài</span>
                        </div>
                        <p className="text-xs text-rose-950 dark:text-rose-200 font-medium leading-relaxed">
                          {msg.content}
                        </p>
                        {msg.refusalReason && (
                          <p className="text-[11px] text-muted-foreground leading-normal">
                            {msg.refusalReason}
                          </p>
                        )}
                      </div>
                    ) : (
                      /* Grounded 3-Part Structured Response */
                      <div className="space-y-2.5">
                        {/* Part 1: Inquiry-oriented explanation */}
                        <div className="p-3.5 rounded-2xl rounded-tl-sm bg-secondary/80 border border-border/70 text-xs sm:text-sm leading-relaxed text-foreground shadow-sm">
                          <div className="flex items-center gap-1.5 font-serif font-bold text-xs text-primary mb-1">
                            <BookOpen className="size-3.5" />
                            <span>Lời giải thích gợi mở</span>
                          </div>
                          <p className="text-foreground/90 whitespace-pre-wrap">
                            {msg.structuredResponse?.explanation || msg.content}
                          </p>
                        </div>

                        {/* Part 2: Primary Source Citations */}
                        {msg.structuredResponse?.citations && msg.structuredResponse.citations.length > 0 && (
                          <div className="p-3 rounded-xl border border-amber-500/30 bg-amber-500/5 text-xs space-y-1.5">
                            <div className="flex items-center gap-1.5 font-semibold text-[11px] text-amber-700 dark:text-amber-400">
                              <CheckCircle2 className="size-3.5" />
                              <span>Trích dẫn sử liệu chính thức</span>
                            </div>
                            <div className="space-y-1.5 divide-y divide-border/40">
                              {msg.structuredResponse.citations.map((cite, cIdx) => (
                                <div key={cIdx} className="pt-1.5 first:pt-0">
                                  <div className="font-semibold text-foreground text-[11px]">
                                    {cite.source_title}{" "}
                                    <span className="text-muted-foreground font-normal">
                                      ({cite.volume_or_chapter})
                                    </span>
                                  </div>
                                  <blockquote className="mt-0.5 pl-2 border-l-2 border-amber-500/40 text-[11px] italic text-muted-foreground">
                                    &ldquo;{cite.citation}&rdquo;
                                  </blockquote>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Part 3: Epistemic Certainty vs Needs Verification */}
                        {msg.structuredResponse?.certainty_vs_verification && (
                          <div className="grid grid-cols-1 gap-2 text-[11px]">
                            {/* Certainty */}
                            <div className="p-2.5 rounded-lg border border-emerald-500/30 bg-emerald-500/5 space-y-1">
                              <div className="flex items-center gap-1 font-semibold text-emerald-700 dark:text-emerald-400">
                                <CheckCircle2 className="size-3" />
                                <span>Điều chắc chắn (Sử liệu xác nhận)</span>
                              </div>
                              <p className="text-muted-foreground leading-normal">
                                {msg.structuredResponse.certainty_vs_verification.certain}
                              </p>
                            </div>

                            {/* Needs verification */}
                            <div className="p-2.5 rounded-lg border border-sky-500/30 bg-sky-500/5 space-y-1">
                              <div className="flex items-center gap-1 font-semibold text-sky-700 dark:text-sky-400">
                                <HelpCircle className="size-3" />
                                <span>Điều cần kiểm chứng thêm</span>
                              </div>
                              <p className="text-muted-foreground leading-normal">
                                {msg.structuredResponse.certainty_vs_verification.needs_verification}
                              </p>
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Suggested Followup Prompts */}
                    {msg.suggestedQuestions && msg.suggestedQuestions.length > 0 && (
                      <div className="space-y-1.5 pt-1">
                        <span className="text-[10px] uppercase font-semibold tracking-wider text-muted-foreground">
                          Gợi ý câu hỏi đào sâu:
                        </span>
                        <div className="flex flex-col gap-1">
                          {msg.suggestedQuestions.map((q, qIdx) => (
                            <button
                              key={qIdx}
                              type="button"
                              onClick={() => handleSendMessage(q)}
                              className="text-left text-xs p-2 rounded-lg bg-secondary/50 hover:bg-secondary text-foreground/80 hover:text-foreground border border-border/50 transition-colors flex items-center justify-between group"
                            >
                              <span className="truncate">{q}</span>
                              <ChevronRight className="size-3 text-muted-foreground group-hover:text-primary shrink-0 ml-1" />
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex items-center gap-2 p-3 rounded-xl bg-secondary/40 border border-border/40 text-xs text-muted-foreground">
                <Sparkles className="size-3.5 text-primary animate-spin" />
                <span>Đang tra cứu tư liệu chính sử và kiểm chứng phạm vi...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Quick Inquiry Suggested Prompt Pills */}
          <div className="px-3 py-1.5 bg-secondary/30 border-t border-border/50 overflow-x-auto flex gap-1.5 no-scrollbar">
            {SUGGESTED_INQUIRY_PROMPTS.slice(0, 3).map((prompt, pIdx) => (
              <button
                key={pIdx}
                type="button"
                onClick={() => handleSendMessage(prompt)}
                className="whitespace-nowrap px-2.5 py-1 rounded-full text-[11px] font-medium bg-card hover:bg-secondary text-muted-foreground hover:text-foreground border border-border/60 transition-colors shrink-0"
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Input Footer */}
          <div className="p-3 bg-card border-t border-border/70 flex items-center gap-2">
            <input
              ref={inputRef}
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                contextMonumentName
                  ? `Hỏi về sử liệu của ${contextMonumentName}...`
                  : "Đặt câu hỏi về không gian Đại Nội Huế..."
              }
              className="flex-1 bg-secondary/60 border border-border/70 rounded-xl px-3.5 py-2 text-xs sm:text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
            <Button
              type="button"
              size="sm"
              disabled={!inputQuery.trim() || loading}
              onClick={() => handleSendMessage()}
              className="h-9 w-9 p-0 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 shrink-0"
              aria-label="Gửi câu hỏi"
            >
              <Send className="size-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
