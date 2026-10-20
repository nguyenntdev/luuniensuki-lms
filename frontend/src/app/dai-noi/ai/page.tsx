"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import {
  Bot,
  Sparkles,
  Send,
  BookOpen,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  ShieldAlert,
  ChevronRight,
  ArrowLeft,
  Compass,
  FileText,
  RotateCcw,
  Info,
} from "lucide-react";
import ImperialHeader from "@/components/imperial/shell/ImperialHeader";
import { Button } from "@/components/ui/button";
import {
  askImperialAiTutor,
  type ImperialAiMessage,
  SUGGESTED_INQUIRY_PROMPTS,
} from "@/lib/imperial/ai-assistant";
import { FALLBACK_SITES } from "@/lib/imperial/fallback-data";
import { cn } from "@/lib/utils";

export default function ImperialAiInquiryPage() {
  const [selectedSiteSlug, setSelectedSiteSlug] = useState<string>("");
  const [inputQuery, setInputQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<ImperialAiMessage[]>([
    {
      id: "init_system",
      role: "assistant",
      content:
        "Chào mừng bạn đến với **Không gian Truy vấn Lịch sử AI — Đại Nội Huế**.\n\nHệ thống được khóa phạm vi chuyên sâu theo đề tài: chỉ phản hồi các vấn đề về quy hoạch kiến trúc, đời sống triều đình và các tư liệu chính sử triều Nguyễn đã kiểm chứng. Mọi câu hỏi ngoài phạm vi sẽ được từ chối sư phạm rõ ràng.",
      timestamp: Date.now(),
      suggestedQuestions: SUGGESTED_INQUIRY_PROMPTS,
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

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
        context_monument_slug: selectedSiteSlug || undefined,
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

  const handleResetConversation = () => {
    setMessages([
      {
        id: `reset_${Date.now()}`,
        role: "assistant",
        content:
          "Phiên làm việc đã được làm mới. Mời bạn chọn di tích hoặc nhập câu hỏi truy chứng lịch sử Đại Nội Huế.",
        timestamp: Date.now(),
        suggestedQuestions: SUGGESTED_INQUIRY_PROMPTS,
      },
    ]);
  };

  const selectedSite = FALLBACK_SITES.find((s) => s.slug === selectedSiteSlug);

  return (
    <div className="min-h-screen bg-background flex flex-col selection:bg-primary/20 selection:text-primary">
      {/* Universal Imperial Top Navigation */}
      <ImperialHeader />

      <main className="flex-1 flex flex-col max-w-5xl w-full mx-auto px-4 py-6 sm:px-6">
        {/* Navigation & Breadcrumb */}
        <div className="flex items-center justify-between gap-4 pb-4 border-b border-border/70">
          <div className="flex items-center gap-3">
            <Link href="/dai-noi">
              <Button variant="ghost" size="sm" className="gap-1.5 text-xs text-muted-foreground hover:text-foreground">
                <ArrowLeft className="size-3.5" />
                Về bản đồ
              </Button>
            </Link>
            <div className="h-4 w-px bg-border/80" />
            <div className="flex items-center gap-2">
              <div className="size-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center">
                <Bot className="size-4 text-primary" />
              </div>
              <div>
                <h1 className="font-serif font-bold text-base text-foreground leading-tight">
                  Truy vấn Lịch sử AI Đại Nội
                </h1>
                <p className="text-[11px] text-muted-foreground">
                  Trợ lý đối chiếu tư liệu chính sử có số quyển & phân định mức độ xác thực
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleResetConversation}
              className="text-xs gap-1.5 border-border/80"
              title="Làm mới hội thoại"
            >
              <RotateCcw className="size-3.5" />
              Làm mới
            </Button>
          </div>
        </div>

        {/* Monument Context Selector */}
        <div className="py-3 flex flex-wrap items-center gap-2.5 bg-secondary/30 px-3.5 rounded-xl mt-3 border border-border/60">
          <span className="text-xs font-semibold text-muted-foreground shrink-0">
            Khung ngữ cảnh di tích:
          </span>
          <select
            value={selectedSiteSlug}
            onChange={(e) => setSelectedSiteSlug(e.target.value)}
            className="bg-card border border-border/80 rounded-lg px-2.5 py-1 text-xs font-medium text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="">-- Toàn bộ Đại Nội (16 công trình) --</option>
            {FALLBACK_SITES.map((site) => (
              <option key={site.slug} value={site.slug}>
                {site.name_vi} ({site.zone_slug})
              </option>
            ))}
          </select>

          {selectedSite && (
            <span className="text-[11px] text-primary font-medium">
              Niên đại: {selectedSite.construction_year || "thế kỷ XIX"} ({selectedSite.reign || "Triều Nguyễn"})
            </span>
          )}
        </div>

        {/* Chat Feed */}
        <div className="flex-1 overflow-y-auto my-4 space-y-5 pr-1">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={cn(
                "flex flex-col gap-2 max-w-3xl",
                msg.role === "user" ? "ml-auto items-end" : "mr-auto items-start",
              )}
            >
              {msg.role === "user" && (
                <div className="px-4 py-2.5 rounded-2xl rounded-tr-sm bg-primary text-primary-foreground text-sm font-medium shadow-md">
                  {msg.content}
                </div>
              )}

              {msg.role === "assistant" && (
                <div className="w-full space-y-3">
                  {/* Scope Refusal Visual Card */}
                  {msg.isScopeRefusal ? (
                    <div className="p-4 rounded-2xl border border-rose-300 dark:border-rose-900 bg-rose-50/90 dark:bg-rose-950/40 text-foreground space-y-2.5 shadow-sm">
                      <div className="flex items-center gap-2 text-rose-700 dark:text-rose-400 font-bold text-xs uppercase tracking-wide">
                        <ShieldAlert className="size-4 shrink-0" />
                        <span>Giới hạn phạm vi sư phạm</span>
                      </div>
                      <p className="text-sm font-semibold text-rose-950 dark:text-rose-200">
                        {msg.content}
                      </p>
                      {msg.refusalReason && (
                        <p className="text-xs text-muted-foreground leading-relaxed">
                          {msg.refusalReason}
                        </p>
                      )}
                    </div>
                  ) : (
                    /* Grounded Pedagogical Structured Response */
                    <div className="space-y-3">
                      {/* 1. Inquiry Explanation */}
                      <div className="p-4 rounded-2xl rounded-tl-sm bg-card border border-border/80 shadow-sm space-y-2 text-sm leading-relaxed">
                        <div className="flex items-center gap-1.5 font-serif font-bold text-xs text-primary">
                          <BookOpen className="size-4" />
                          <span>1. Lời giải thích gợi mở tư duy</span>
                        </div>
                        <p className="text-foreground/90 whitespace-pre-wrap">
                          {msg.structuredResponse?.explanation || msg.content}
                        </p>
                      </div>

                      {/* 2. Official Citations with Volume/Page */}
                      {msg.structuredResponse?.citations && msg.structuredResponse.citations.length > 0 && (
                        <div className="p-4 rounded-2xl border border-amber-500/30 bg-amber-500/5 space-y-2 text-xs">
                          <div className="flex items-center gap-2 font-bold text-amber-700 dark:text-amber-400">
                            <CheckCircle2 className="size-4" />
                            <span>2. Trích dẫn sử liệu chính thức</span>
                          </div>
                          <div className="space-y-2 divide-y divide-border/50">
                            {msg.structuredResponse.citations.map((cite, cIdx) => (
                              <div key={cIdx} className="pt-2 first:pt-0">
                                <div className="font-semibold text-foreground text-xs flex items-center justify-between">
                                  <span>{cite.source_title}</span>
                                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-800 dark:text-amber-300">
                                    {cite.volume_or_chapter}
                                  </span>
                                </div>
                                <blockquote className="mt-1 pl-3 border-l-2 border-amber-500/50 text-xs italic text-muted-foreground">
                                  &ldquo;{cite.citation}&rdquo;
                                </blockquote>
                                {cite.archival_unit && (
                                  <p className="mt-1 text-[10px] text-muted-foreground">
                                    Đơn vị lưu trữ: {cite.archival_unit}
                                  </p>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* 3. Epistemic Certainty vs Needs Verification */}
                      {msg.structuredResponse?.certainty_vs_verification && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                          <div className="p-3.5 rounded-xl border border-emerald-500/30 bg-emerald-500/5 space-y-1.5">
                            <div className="flex items-center gap-1.5 font-bold text-emerald-700 dark:text-emerald-400">
                              <CheckCircle2 className="size-3.5" />
                              <span>Điều chắc chắn (Đã xác minh)</span>
                            </div>
                            <p className="text-muted-foreground leading-relaxed">
                              {msg.structuredResponse.certainty_vs_verification.certain}
                            </p>
                          </div>

                          <div className="p-3.5 rounded-xl border border-sky-500/30 bg-sky-500/5 space-y-1.5">
                            <div className="flex items-center gap-1.5 font-bold text-sky-700 dark:text-sky-400">
                              <HelpCircle className="size-3.5" />
                              <span>Điều cần kiểm chứng thêm</span>
                            </div>
                            <p className="text-muted-foreground leading-relaxed">
                              {msg.structuredResponse.certainty_vs_verification.needs_verification}
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Suggested Follow-up Questions */}
                  {msg.suggestedQuestions && msg.suggestedQuestions.length > 0 && (
                    <div className="p-3 rounded-xl bg-secondary/30 border border-border/50 space-y-1.5">
                      <span className="text-[10px] uppercase font-bold tracking-wider text-muted-foreground">
                        Gợi ý câu hỏi đào sâu tư liệu:
                      </span>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                        {msg.suggestedQuestions.map((q, qIdx) => (
                          <button
                            key={qIdx}
                            type="button"
                            onClick={() => handleSendMessage(q)}
                            className="text-left text-xs p-2 rounded-lg bg-card hover:bg-secondary text-foreground/80 hover:text-foreground border border-border/60 transition-colors flex items-center justify-between group"
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
            <div className="flex items-center gap-2.5 p-3.5 rounded-2xl bg-card border border-border/80 text-xs text-muted-foreground max-w-md">
              <Sparkles className="size-4 text-primary animate-spin" />
              <span>Đang tra cứu tư liệu chính sử và kiểm chứng phạm vi...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="pt-2 border-t border-border/70 space-y-2">
          {/* Quick Prompts Bar */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar text-xs">
            <span className="text-[10px] uppercase font-bold text-muted-foreground shrink-0 flex items-center gap-1">
              <Sparkles className="size-3 text-primary" />
              Mẫu:
            </span>
            {SUGGESTED_INQUIRY_PROMPTS.map((prompt, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSendMessage(prompt)}
                className="whitespace-nowrap px-3 py-1 rounded-full text-xs font-medium bg-secondary/70 hover:bg-secondary text-muted-foreground hover:text-foreground border border-border/60 transition-colors shrink-0"
              >
                {prompt}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <input
              ref={inputRef}
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSendMessage()}
              placeholder={
                selectedSite
                  ? `Đặt câu hỏi về ${selectedSite.name_vi} (ví dụ: 'Vì sao công trình được xây dựng?')...`
                  : "Đặt câu hỏi về không gian, quy hoạch hoặc sử liệu Đại Nội Huế..."
              }
              className="flex-1 bg-card border border-border/80 rounded-xl px-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary shadow-sm"
            />
            <Button
              type="button"
              disabled={!inputQuery.trim() || loading}
              onClick={() => handleSendMessage()}
              className="h-10 px-5 rounded-xl bg-primary text-primary-foreground font-semibold shadow-md gap-2"
            >
              <span>Gửi</span>
              <Send className="size-4" />
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}
