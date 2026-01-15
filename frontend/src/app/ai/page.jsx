"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";

import {
  aiCoach,
  aiDiagnostic,
  aiExplain,
  aiFeedback,
  aiFlashcards,
  aiQa,
  aiReviewPlan,
  aiSummary,
  aiTutor,
} from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

const LEVEL_OPTIONS = [
  { value: "beginner", label: "Cơ bản" },
  { value: "intermediate", label: "Trung bình" },
  { value: "advanced", label: "Nâng cao" },
];

const EXPLAIN_LEVELS = [
  { value: "child", label: "12 tuổi" },
  { value: "teen", label: "18 tuổi" },
  { value: "expert", label: "Chuyên gia" },
];

function formatSources(citations = []) {
  if (!Array.isArray(citations) || citations.length === 0) return null;
  return citations.map((source) => ({
    id: `${source.index}-${source.source_id || "source"}`,
    title: source.title || `Nguồn ${source.index}`,
    snippet: source.snippet || "",
    type: source.source_type || "source",
  }));
}

function formatAiPayload(payload) {
  if (!payload) return "";
  if (Array.isArray(payload)) {
    return payload.map((item) => `• ${String(item)}`).join("\n");
  }
  if (typeof payload === "object") {
    if (payload.summary || payload.key_points) {
      const points = Array.isArray(payload.key_points)
        ? payload.key_points.map((item) => `• ${item}`).join("\n")
        : "";
      return [
        payload.summary ? `Tóm tắt: ${payload.summary}` : "",
        points ? `Điểm chính:\n${points}` : "",
      ]
        .filter(Boolean)
        .join("\n\n");
    }
    if (Array.isArray(payload.cards)) {
      return `Flashcards:\n${payload.cards
        .map((card) => {
          if (card && typeof card === "object") {
            return `• ${card.front || card.question || "Thẻ"} → ${
              card.back || card.answer || ""
            }`;
          }
          return `• ${String(card)}`;
        })
        .join("\n")}`;
    }
    if (Array.isArray(payload.questions)) {
      return `Câu hỏi chẩn đoán:\n${payload.questions
        .map((q) => `• ${q.question_text || q.question || q}`)
        .join("\n")}`;
    }
    if (payload.message || payload.weekly_plan) {
      const plan = Array.isArray(payload.weekly_plan)
        ? payload.weekly_plan.map((item) => `• ${item}`).join("\n")
        : "";
      return [payload.message || "", plan ? `Kế hoạch tuần:\n${plan}` : ""]
        .filter(Boolean)
        .join("\n\n");
    }
    return JSON.stringify(payload, null, 2);
  }
  return String(payload);
}

function normalizeAiContent(content) {
  if (content == null) return "";
  if (typeof content === "string") {
    const trimmed = content.trim();
    if (!trimmed) return "";
    if (
      (trimmed.startsWith("{") && trimmed.endsWith("}")) ||
      (trimmed.startsWith("[") && trimmed.endsWith("]"))
    ) {
      try {
        const parsed = JSON.parse(trimmed);
        return formatAiPayload(parsed);
      } catch {
        return content;
      }
    }
    return content;
  }
  return formatAiPayload(content);
}

function normalizeAiError(err) {
  const message = err instanceof Error ? err.message : String(err);
  if (
    message.includes("502") ||
    message.toLowerCase().includes("deepseek") ||
    message.toLowerCase().includes("ai")
  ) {
    return "AI đang bận, thử lại sau nhé.";
  }
  return message;
}

export default function AiHubPage() {
  const status = useAuthStore((s) => s.status);
  const searchParams = useSearchParams();
  const initialMotifId = searchParams.get("motifId") || "";
  const initialUrnSlug = searchParams.get("urnSlug") || "";

  const [mode, setMode] = useState("tutor");
  const [level, setLevel] = useState("beginner");
  const [messages, setMessages] = useState([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Chào bạn! Mình là AI Tutor. Hãy hỏi về bài học, quiz hoặc nhờ tóm tắt nội dung nhé.",
      sources: [],
    },
  ]);
  const [input, setInput] = useState("");
  const [motifId, setMotifId] = useState(initialMotifId);
  const [urnSlug, setUrnSlug] = useState(initialUrnSlug);
  const [explainText, setExplainText] = useState("");
  const [explainLevel, setExplainLevel] = useState("teen");
  const [feedbackQuestion, setFeedbackQuestion] = useState("");
  const [feedbackCorrect, setFeedbackCorrect] = useState("");
  const [feedbackAnswer, setFeedbackAnswer] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState(null);

  const contextPayload = useMemo(() => {
    const payload = {};
    if (motifId.trim()) payload.motif_id = motifId.trim();
    if (urnSlug.trim()) payload.urn_slug = urnSlug.trim();
    return Object.keys(payload).length ? payload : undefined;
  }, [motifId, urnSlug]);

  function buildHistory() {
    const history = messages
      .filter((msg) => msg.role === "user" || msg.role === "assistant")
      .slice(-6)
      .map((msg) => ({ role: msg.role, content: msg.content }));
    return history;
  }

  function appendMessage(role, content, citations) {
    setMessages((prev) => [
      ...prev,
      {
        id: `${role}-${Date.now()}-${Math.random().toString(16).slice(2)}`,
        role,
        content: normalizeAiContent(content),
        sources: formatSources(citations) || [],
      },
    ]);
  }

  async function handleSend() {
    const text = input.trim();
    if (!text || isSending) return;
    if (status !== "authed") {
      setError("Hãy đăng nhập để sử dụng AI Tutor.");
      return;
    }

    setError(null);
    const history = buildHistory();
    appendMessage("user", text);
    setInput("");
    setIsSending(true);

    try {
      if (mode === "tutor") {
        const res = await aiTutor({
          message: text,
          history,
          context: contextPayload,
          level,
        });
        appendMessage(
          "assistant",
          res.answer || "AI chưa trả lời.",
          res.citations,
        );
      } else {
        const res = await aiQa({
          question: text,
          context: contextPayload,
          limit: 6,
        });
        appendMessage(
          "assistant",
          res.answer || "AI chưa trả lời.",
          res.citations,
        );
      }
    } catch (err) {
      setError(normalizeAiError(err));
      appendMessage("assistant", "AI đang bận, thử lại sau nhé.");
    } finally {
      setIsSending(false);
    }
  }

  async function runAction(handler, fallbackMessage) {
    if (isSending) return;
    if (status !== "authed") {
      setError("Hãy đăng nhập để sử dụng AI.");
      return;
    }
    setError(null);
    setIsSending(true);
    try {
      const content = await handler();
      appendMessage("assistant", content || fallbackMessage);
    } catch (err) {
      setError(normalizeAiError(err));
      appendMessage("assistant", fallbackMessage);
    } finally {
      setIsSending(false);
    }
  }

  function handleSummary() {
    runAction(async () => {
      const res = await aiSummary({
        motifId: motifId.trim() || undefined,
        urnSlug: urnSlug.trim() || undefined,
      });
      const keyPoints = Array.isArray(res.key_points) ? res.key_points : [];
      return [
        `Tóm tắt: ${res.summary}`,
        keyPoints.length
          ? `Điểm chính:\n${keyPoints.map((item) => `• ${item}`).join("\n")}`
          : "",
      ]
        .filter(Boolean)
        .join("\n\n");
    }, "Chưa thể tóm tắt, thử lại nhé.");
  }

  function handleFlashcards() {
    runAction(async () => {
      const res = await aiFlashcards({
        motifId: motifId.trim() || undefined,
        topic: motifId.trim() || urnSlug.trim() ? undefined : "Cửu Đỉnh",
        count: 6,
        level,
      });
      const cards = Array.isArray(res.cards) ? res.cards : [];
      if (!cards.length) return "Chưa có flashcards.";
      return `Flashcards:\n${cards
        .map((card) => {
          if (card && typeof card === "object") {
            const front = card.front ?? card.question ?? "Thẻ";
            const back = card.back ?? card.answer ?? "";
            return `• ${front} → ${back}`;
          }
          return `• ${String(card)}`;
        })
        .join("\n")}`;
    }, "Không tạo được flashcards lúc này.");
  }

  function handleExplain() {
    if (!explainText.trim()) {
      setError("Nhập nội dung cần giải thích trước nhé.");
      return;
    }
    runAction(async () => {
      const res = await aiExplain({
        text: explainText.trim(),
        level: explainLevel,
      });
      setExplainText("");
      return res.explanation || "AI chưa có phản hồi.";
    }, "Không thể giải thích lúc này.");
  }

  function handleCoach() {
    runAction(async () => {
      const res = await aiCoach({});
      const plan = Array.isArray(res.weekly_plan) ? res.weekly_plan : [];
      return [
        res.message || "Coach đã sẵn sàng giúp bạn.",
        plan.length
          ? `Kế hoạch tuần:\n${plan.map((item) => `• ${item}`).join("\n")}`
          : "",
      ]
        .filter(Boolean)
        .join("\n\n");
    }, "Không thể tạo coach plan lúc này.");
  }

  function handleReviewPlan() {
    runAction(async () => {
      const res = await aiReviewPlan();
      const items = Array.isArray(res.items) ? res.items : [];
      if (!items.length) return "Chưa có kế hoạch ôn tập.";
      return `Lộ trình ôn tập:\n${items
        .map(
          (item) =>
            `• ${item.motif_name || "Họa tiết"} (còn ${item.due_in_days} ngày)`,
        )
        .join("\n")}`;
    }, "Không thể tạo kế hoạch ôn tập.");
  }

  function handleDiagnostic() {
    runAction(async () => {
      const res = await aiDiagnostic({
        urnSlug: urnSlug.trim() || undefined,
        count: 6,
        level,
      });
      const questions = Array.isArray(res.questions) ? res.questions : [];
      if (!questions.length) return "Chưa có câu hỏi chẩn đoán.";
      return `Câu hỏi chẩn đoán:\n${questions
        .map((q) => `• ${q.question_text || q}`)
        .join("\n")}`;
    }, "Không thể tạo bài chẩn đoán.");
  }

  function handleFeedback() {
    if (
      !feedbackQuestion.trim() ||
      !feedbackCorrect.trim() ||
      !feedbackAnswer.trim()
    ) {
      setError("Nhập đủ câu hỏi, đáp án đúng và câu trả lời của bạn.");
      return;
    }
    runAction(async () => {
      const res = await aiFeedback({
        question: feedbackQuestion.trim(),
        correctAnswer: feedbackCorrect.trim(),
        userAnswer: feedbackAnswer.trim(),
        context: contextPayload,
      });
      setFeedbackQuestion("");
      setFeedbackCorrect("");
      setFeedbackAnswer("");
      return [
        res.is_correct === true ? "Kết quả: Đúng ✅" : "Kết quả: Chưa đúng ❌",
        res.explanation ? `Giải thích: ${res.explanation}` : "",
        res.next_step ? `Gợi ý tiếp theo: ${res.next_step}` : "",
      ]
        .filter(Boolean)
        .join("\n\n");
    }, "Chưa tạo được phản hồi.");
  }

  const isAuthed = status === "authed";

  return (
    <main className="mx-auto max-w-6xl px-6 py-10 pb-28">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-display font-bold text-foreground">
            AI Tutor Hub
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Trợ giảng AI theo ngữ cảnh bài học, quiz và kho tri thức nội bộ.
          </p>
        </div>
        <Link
          href="/explore"
          className="rounded-lg border border-border px-4 py-2 text-sm font-semibold text-foreground hover:bg-muted"
        >
          Quay lại khám phá
        </Link>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="flex flex-col rounded-3xl border border-border bg-card p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-xs font-semibold uppercase tracking-wider text-primary">
                {mode === "tutor" ? "Tutor mode" : "Q&A mode"}
              </div>
              <div className="text-lg font-display font-semibold text-foreground">
                {mode === "tutor"
                  ? "Chat theo bài học & quiz"
                  : "Hỏi đáp theo tài liệu nội bộ"}
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setMode("tutor")}
                className={[
                  "rounded-full border px-3 py-1 text-xs font-semibold",
                  mode === "tutor"
                    ? "border-primary bg-primary/15 text-primary"
                    : "border-border text-muted-foreground hover:bg-muted",
                ].join(" ")}
              >
                Tutor
              </button>
              <button
                type="button"
                onClick={() => setMode("qa")}
                className={[
                  "rounded-full border px-3 py-1 text-xs font-semibold",
                  mode === "qa"
                    ? "border-primary bg-primary/15 text-primary"
                    : "border-border text-muted-foreground hover:bg-muted",
                ].join(" ")}
              >
                Q&A
              </button>
              <select
                value={level}
                onChange={(e) => setLevel(e.target.value)}
                disabled={mode !== "tutor"}
                className="rounded-full border border-border bg-background px-3 py-1 text-xs font-semibold text-foreground disabled:opacity-60"
              >
                {LEVEL_OPTIONS.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {error ? (
            <div className="mt-4 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive">
              {error}
            </div>
          ) : null}

          <div className="mt-5 flex-1 space-y-4 overflow-y-auto pr-1">
            {messages.map((message) => (
              <div
                key={message.id}
                className={[
                  "rounded-2xl border p-4 text-sm",
                  message.role === "user"
                    ? "ml-auto border-primary/40 bg-primary/10 text-foreground"
                    : "border-border bg-muted/50 text-foreground",
                ].join(" ")}
              >
                <div className="text-xs uppercase tracking-wider text-muted-foreground">
                  {message.role === "user" ? "Bạn" : "AI Tutor"}
                </div>
                <div className="mt-2 whitespace-pre-line leading-relaxed">
                  {message.content}
                </div>
                {message.sources?.length ? (
                  <div className="mt-3 space-y-2 rounded-xl border border-border bg-background/60 p-3 text-xs text-muted-foreground">
                    <div className="font-semibold text-foreground">
                      Nguồn tham khảo
                    </div>
                    {message.sources.map((source) => (
                      <div key={source.id}>
                        <div className="font-medium text-foreground">
                          {source.title}
                        </div>
                        {source.snippet ? (
                          <div className="mt-1 text-xs">{source.snippet}</div>
                        ) : null}
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            ))}
            {isSending ? (
              <div className="rounded-2xl border border-border bg-muted/40 p-4 text-xs text-muted-foreground">
                AI đang trả lời...
              </div>
            ) : null}
          </div>

          <div className="mt-5 border-t border-border pt-4">
            <div className="flex flex-col gap-3 sm:flex-row">
              <textarea
                rows={2}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Nhập câu hỏi cho AI Tutor..."
                className="flex-1 rounded-xl border border-border bg-background px-3 py-2 text-sm text-foreground"
              />
              <button
                type="button"
                disabled={!isAuthed || isSending}
                onClick={handleSend}
                className="rounded-xl bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
              >
                Gửi
              </button>
            </div>
            {!isAuthed ? (
              <p className="mt-2 text-xs text-muted-foreground">
                Vui lòng đăng nhập để dùng AI.
              </p>
            ) : null}
          </div>
        </section>

        <aside className="space-y-6">
          <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-foreground">
              Ngữ cảnh bài học
            </h3>
            <p className="mt-1 text-xs text-muted-foreground">
              Liên kết AI với họa tiết hoặc Cửu Đỉnh để trả lời chính xác hơn.
            </p>
            <div className="mt-4 space-y-3">
              <input
                type="text"
                value={motifId}
                onChange={(e) => setMotifId(e.target.value)}
                placeholder="Motif ID"
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
              />
              <input
                type="text"
                value={urnSlug}
                onChange={(e) => setUrnSlug(e.target.value)}
                placeholder="Urn slug"
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
              />
              <div className="text-xs text-muted-foreground">
                Gợi ý: mở từ bài học/quiz sẽ tự điền sẵn.
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-foreground">
              Hành động nhanh
            </h3>
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={handleSummary}
                className="rounded-full border border-border px-3 py-1 text-xs font-semibold text-foreground hover:bg-muted"
              >
                Tóm tắt
              </button>
              <button
                type="button"
                onClick={handleFlashcards}
                className="rounded-full border border-border px-3 py-1 text-xs font-semibold text-foreground hover:bg-muted"
              >
                Flashcards
              </button>
              <button
                type="button"
                onClick={handleCoach}
                className="rounded-full border border-border px-3 py-1 text-xs font-semibold text-foreground hover:bg-muted"
              >
                Coach
              </button>
              <button
                type="button"
                onClick={handleReviewPlan}
                className="rounded-full border border-border px-3 py-1 text-xs font-semibold text-foreground hover:bg-muted"
              >
                Ôn tập
              </button>
              <button
                type="button"
                onClick={handleDiagnostic}
                className="rounded-full border border-border px-3 py-1 text-xs font-semibold text-foreground hover:bg-muted"
              >
                Chẩn đoán
              </button>
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-foreground">
              Giải thích theo cấp độ
            </h3>
            <textarea
              rows={3}
              value={explainText}
              onChange={(e) => setExplainText(e.target.value)}
              placeholder="Nhập nội dung cần giải thích..."
              className="mt-3 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
            />
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <select
                value={explainLevel}
                onChange={(e) => setExplainLevel(e.target.value)}
                className="rounded-lg border border-border bg-background px-3 py-2 text-xs font-semibold text-foreground"
              >
                {EXPLAIN_LEVELS.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={handleExplain}
                className="rounded-lg bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90"
              >
                Giải thích
              </button>
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-foreground">
              Phản hồi bài làm
            </h3>
            <div className="mt-3 space-y-3">
              <input
                type="text"
                value={feedbackQuestion}
                onChange={(e) => setFeedbackQuestion(e.target.value)}
                placeholder="Câu hỏi"
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
              />
              <input
                type="text"
                value={feedbackCorrect}
                onChange={(e) => setFeedbackCorrect(e.target.value)}
                placeholder="Đáp án đúng"
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
              />
              <input
                type="text"
                value={feedbackAnswer}
                onChange={(e) => setFeedbackAnswer(e.target.value)}
                placeholder="Câu trả lời của bạn"
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
              />
              <button
                type="button"
                onClick={handleFeedback}
                className="rounded-lg bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90"
              >
                Nhận phản hồi
              </button>
            </div>
          </div>
        </aside>
      </div>
    </main>
  );
}
