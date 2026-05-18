"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import {
  aiCoach,
  aiDiagnostic,
  aiExplain,
  aiFeedback,
  aiFlashcards,
  aiQa,
  aiQaStream,
  aiReviewPlan,
  aiSummary,
  aiTutor,
  aiTutorStream,
  getUrns,
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

const QUICK_PROMPTS = [
  "Tóm tắt bài học này thành 3 ý dễ nhớ.",
  "Đặt cho tôi 5 câu hỏi ôn tập có đáp án.",
  "Giải thích biểu tượng di sản này bằng tiếng Việt dễ hiểu.",
];

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const SIMPLE_SLUG_PATTERN = /^[a-z0-9-]+$/;

function normalizeTextForMatch(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase();
}

function hasFollowUpCue(content) {
  const normalized = normalizeTextForMatch(content);
  return (
    normalized.includes("goi y hoc tiep") ||
    normalized.includes("goi y tiep theo")
  );
}

function makeGuidanceActions({
  content,
  sources = [],
  motifId = "",
  urnSlug = "",
  urnLookup = null,
} = {}) {
  if (!hasFollowUpCue(content)) return null;

  const actions = [];
  const references = [];
  const seenActionHref = new Set();
  const seenReferenceKey = new Set();

  const addAction = ({ label, href, description }) => {
    if (!href || seenActionHref.has(href)) return;
    seenActionHref.add(href);
    actions.push({
      id: `action-${actions.length + 1}-${href}`,
      label,
      href,
      description,
    });
  };

  const addReference = ({ title, href, description }) => {
    const key = `${title || ""}::${href || ""}`;
    if (!title || seenReferenceKey.has(key)) return;
    seenReferenceKey.add(key);
    references.push({
      id: `ref-${references.length + 1}-${key}`,
      title,
      href,
      description: description || "",
    });
  };

  const lookupHasData = Boolean(
    urnLookup &&
      (Object.keys(urnLookup.byId || {}).length ||
        Object.keys(urnLookup.byName || {}).length ||
        Object.keys(urnLookup.bySlug || {}).length)
  );
  const resolveUrnSlugFromAny = (candidate = "") => {
    const raw = String(candidate || "").trim();
    if (!raw) return null;
    if (!lookupHasData) {
      return SIMPLE_SLUG_PATTERN.test(raw) ? raw : null;
    }

    if (SIMPLE_SLUG_PATTERN.test(raw) && urnLookup.bySlug?.[raw]) {
      return raw;
    }
    if (UUID_PATTERN.test(raw) && urnLookup.byId?.[raw]) {
      return urnLookup.byId[raw];
    }

    const byName = urnLookup.byName?.[normalizeTextForMatch(raw)];
    return byName || null;
  };
  const resolveUrnSlugFromSources = () => {
    for (const source of sources) {
      const sourceType = String(source.type || "").toLowerCase();
      if (sourceType !== "urn" && sourceType !== "context") continue;
      const fromId = resolveUrnSlugFromAny(source.sourceId);
      if (fromId) return fromId;
      const fromTitle = resolveUrnSlugFromAny(source.title);
      if (fromTitle) return fromTitle;
    }
    return null;
  };

  const motifFromContext = String(motifId || "").trim();
  const resolvedUrnSlug =
    resolveUrnSlugFromAny(urnSlug) || resolveUrnSlugFromSources();

  if (motifFromContext) {
    const encoded = encodeURIComponent(motifFromContext);
    addAction({
      label: "Vào bài học họa tiết này",
      href: `/motif/${encoded}`,
      description: "Mở bài học chi tiết để học tiếp theo ngữ cảnh hiện tại.",
    });
    addAction({
      label: "Làm trắc nghiệm họa tiết",
      href: `/motif/${encoded}/quiz`,
      description: "Kiểm tra nhanh mức độ nắm bài ngay sau khi học.",
    });
  }

  if (resolvedUrnSlug) {
    const encoded = encodeURIComponent(resolvedUrnSlug);
    addAction({
      label: "Quay lại không gian 3D",
      href: `/urns/${encoded}`,
      description: "Khám phá trực tiếp trên mô hình 3D của đỉnh.",
    });
    addAction({
      label: "Làm bài kiểm tra đỉnh",
      href: `/urns/${encoded}/exam`,
      description: "Ôn tổng hợp kiến thức của cả đỉnh.",
    });

    const urnName =
      (lookupHasData &&
        urnLookup.bySlug?.[resolvedUrnSlug] &&
        urnLookup.bySlug?.[resolvedUrnSlug] !== true &&
        urnLookup.bySlug?.[resolvedUrnSlug]) ||
      resolvedUrnSlug;
    addReference({
      title: `Hồ sơ đỉnh ${urnName}`,
      href: `/urns/${encoded}`,
      description: "Tổng hợp bối cảnh và hành trình học theo đỉnh.",
    });
  }

  for (const source of sources) {
    const sourceId = String(source.sourceId || "").trim();
    const sourceType = String(source.type || "").toLowerCase();
    const title = source.title || "Nguồn nội bộ";
    const snippet = source.snippet || "";

    if (sourceType === "motif" && sourceId && UUID_PATTERN.test(sourceId)) {
      const encoded = encodeURIComponent(sourceId);
      addAction({
        label: `Học tiếp: ${title}`,
        href: `/motif/${encoded}`,
        description: "Mở ngay bài học liên quan trực tiếp tới câu trả lời.",
      });
      addReference({
        title,
        href: `/motif/${encoded}`,
        description: snippet,
      });
      continue;
    }

    if (
      (sourceType === "context" || sourceType === "urn") &&
      (sourceId || title)
    ) {
      const resolvedFromSource =
        resolveUrnSlugFromAny(sourceId) || resolveUrnSlugFromAny(title);
      if (resolvedFromSource) {
        const encoded = encodeURIComponent(resolvedFromSource);
        addAction({
          label: `Mở hành trình ${title}`,
          href: `/urns/${encoded}`,
          description: "Đi thẳng vào hành trình học theo đỉnh tương ứng.",
        });
        addReference({
          title,
          href: `/urns/${encoded}`,
          description: snippet,
        });
      } else {
        addReference({
          title,
          href: null,
          description: snippet || "Nội dung liên quan để học tiếp.",
        });
      }
      continue;
    }

    if (!sourceId || sourceType === "rag") {
      addReference({
        title,
        href: null,
        description: snippet || "Tài liệu nội bộ liên quan cho phần học tiếp.",
      });
    }
  }

  addAction({
    label: "Khám phá thêm bài học",
    href: "/explore",
    description: "Chọn chủ đề gần nhất để học tiếp ngay.",
  });

  const topActions = actions.slice(0, 3);
  const topReferences = references.slice(0, 4);

  if (!topActions.length && !topReferences.length) return null;
  return {
    actions: topActions,
    references: topReferences,
  };
}

function formatSources(citations = []) {
  if (!Array.isArray(citations) || citations.length === 0) return null;
  return citations.map((source) => ({
    id: `${source.index}-${source.source_id || "source"}`,
    sourceId: source.source_id || null,
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
  if (err == null) {
    return "AI đang bận, thử lại sau nhé.";
  }
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
  const [urnLookup, setUrnLookup] = useState({
    byId: {},
    byName: {},
    bySlug: {},
  });

  const [mode, setMode] = useState("tutor");
  const [level, setLevel] = useState("beginner");
  const [messages, setMessages] = useState([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Chào bạn. Hỏi ngắn điều đang vướng, mình sẽ trả lời rõ ý và gợi ý bước học tiếp.",
      sources: [],
      guidance: null,
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

  useEffect(() => {
    if (status !== "authed") return undefined;
    let cancelled = false;
    async function loadUrnLookup() {
      try {
        const res = await getUrns();
        if (cancelled) return;
        const items = Array.isArray(res)
          ? res
          : Array.isArray(res?.items)
            ? res.items
            : [];
        const byId = {};
        const byName = {};
        const bySlug = {};
        for (const item of items) {
          const id = String(item?.id || "").trim();
          const slug = String(item?.slug || "").trim();
          const name = String(item?.name || "").trim();
          if (!slug) continue;
          bySlug[slug] = name || true;
          if (id) byId[id] = slug;
          if (name) byName[normalizeTextForMatch(name)] = slug;
        }
        setUrnLookup({ byId, byName, bySlug });
      } catch {
        if (!cancelled) {
          setUrnLookup({ byId: {}, byName: {}, bySlug: {} });
        }
      }
    }
    loadUrnLookup();
    return () => {
      cancelled = true;
    };
  }, [status]);

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

  function appendMessage(role, content, citations, guidanceContext = {}) {
    const normalizedContent = normalizeAiContent(content);
    const normalizedSources = formatSources(citations) || [];
    const guidance =
      role === "assistant"
        ? makeGuidanceActions({
            content: normalizedContent,
            sources: normalizedSources,
            motifId: guidanceContext.motifId,
            urnSlug: guidanceContext.urnSlug,
            urnLookup,
          })
        : null;

    setMessages((prev) => [
      ...prev,
      {
        id: `${role}-${Date.now()}-${Math.random().toString(16).slice(2)}`,
        role,
        content: normalizedContent,
        sources: normalizedSources,
        guidance,
        isStreaming: false,
      },
    ]);
  }

  function appendStreamingMessage(role) {
    const msgId = `${role}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    setMessages((prev) => [
      ...prev,
      {
        id: msgId,
        role,
        content: "",
        sources: [],
        guidance: null,
        isStreaming: true,
      },
    ]);
    return msgId;
  }

  function updateStreamingMessage(msgId, content) {
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === msgId ? { ...msg, content } : msg
      )
    );
  }

  function finalizeStreamingMessage(
    msgId,
    content,
    citations,
    guidanceContext = {},
  ) {
    const normalizedContent = normalizeAiContent(content);
    const normalizedSources = formatSources(citations) || [];
    const guidance = makeGuidanceActions({
      content: normalizedContent,
      sources: normalizedSources,
      motifId: guidanceContext.motifId,
      urnSlug: guidanceContext.urnSlug,
      urnLookup,
    });

    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === msgId
          ? {
              ...msg,
              content: normalizedContent,
              sources: normalizedSources,
              guidance,
              isStreaming: false,
            }
          : msg
      )
    );
  }

  async function handleSend() {
    const text = input.trim();
    if (!text || isSending) return;
    if (status !== "authed") {
      setError("Hãy đăng nhập để sử dụng Giáo viên AI.");
      return;
    }

    setError(null);
    const history = buildHistory();
    const guidanceContext = {
      motifId: motifId.trim(),
      urnSlug: urnSlug.trim(),
    };
    appendMessage("user", text);
    setInput("");
    setIsSending(true);

    const streamingMsgId = appendStreamingMessage("assistant");
    let accumulatedContent = "";

    try {
      if (mode === "tutor") {
        await aiTutorStream({
          message: text,
          history,
          context: contextPayload,
          level,
          onChunk: (chunk) => {
            accumulatedContent += chunk;
            updateStreamingMessage(streamingMsgId, accumulatedContent);
          },
          onDone: (fullResponse, citations) => {
            finalizeStreamingMessage(
              streamingMsgId,
              fullResponse || accumulatedContent || "AI chưa trả lời.",
              citations,
              guidanceContext
            );
          },
          onError: (error) => {
            setError(normalizeAiError(error));
            finalizeStreamingMessage(
              streamingMsgId,
              "AI đang bận, thử lại sau nhé.",
              null
            );
          },
        });
      } else {
        await aiQaStream({
          question: text,
          context: contextPayload,
          limit: 6,
          onChunk: (chunk) => {
            accumulatedContent += chunk;
            updateStreamingMessage(streamingMsgId, accumulatedContent);
          },
          onDone: (fullResponse, citations) => {
            finalizeStreamingMessage(
              streamingMsgId,
              fullResponse || accumulatedContent || "AI chưa trả lời.",
              citations,
              guidanceContext
            );
          },
          onError: (error) => {
            setError(normalizeAiError(error));
            finalizeStreamingMessage(
              streamingMsgId,
              "AI đang bận, thử lại sau nhé.",
              null
            );
          },
        });
      }
    } catch (err) {
      setError(normalizeAiError(err));
      finalizeStreamingMessage(
        streamingMsgId,
        "AI đang bận, thử lại sau nhé.",
        null
      );
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
      appendMessage("assistant", content || fallbackMessage, null, {
        motifId: motifId.trim(),
        urnSlug: urnSlug.trim(),
      });
    } catch (err) {
      setError(normalizeAiError(err));
      appendMessage("assistant", fallbackMessage, null, {
        motifId: motifId.trim(),
        urnSlug: urnSlug.trim(),
      });
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
        res.is_correct === true ? "Kết quả: Đúng" : "Kết quả: Chưa đúng",
        res.explanation ? `Giải thích: ${res.explanation}` : "",
        res.next_step ? `Gợi ý tiếp theo: ${res.next_step}` : "",
      ]
        .filter(Boolean)
        .join("\n\n");
    }, "Chưa tạo được phản hồi.");
  }

  const isAuthed = status === "authed";

  return (
    <main className="site-shell flex flex-col">
      <section className="heritage-hero p-5 md:p-7">
      <div className="relative flex flex-wrap items-center justify-between gap-4">
        <div className="max-w-3xl">
          <div className="heritage-chip">Giáo viên AI</div>
          <h1 className="mt-3 text-3xl font-display font-bold text-foreground md:text-4xl">
            Hỏi Giáo viên AI
          </h1>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            Một ô hỏi chính. Câu trả lời ngắn, có nguồn khi cần, kèm bước học tiếp.
          </p>
        </div>
        <Link
          href="/explore"
          className="rounded-lg border border-border bg-secondary/60 px-4 py-2 text-sm font-semibold text-foreground hover:border-primary/35 hover:bg-secondary"
        >
          Mở thư viện
        </Link>
      </div>
      </section>

      <div className="mt-5 flex flex-1 flex-col gap-4">
        <section className="heritage-surface flex min-h-0 flex-col p-4 md:p-6">
          <div className="relative flex min-h-0 flex-1 flex-col">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="text-xs font-semibold uppercase tracking-wider text-primary">
                {mode === "tutor" ? "Dạy bài" : "Tra cứu"}
              </div>
              <div className="text-xl font-display font-semibold text-foreground">
                {mode === "tutor"
                  ? "Bạn hỏi, AI trả lời"
                  : "Hỏi theo tài liệu"}
              </div>
              <p className="mt-1 max-w-2xl text-xs leading-relaxed text-muted-foreground">
                Nhập một câu hỏi rõ. Công cụ phụ nằm bên dưới, chỉ mở khi cần.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setMode("tutor")}
                className={[
                  "rounded-lg border px-3 py-1 text-xs font-semibold",
                  mode === "tutor"
                    ? "border-primary bg-primary/15 text-primary"
                    : "border-border/70 text-muted-foreground hover:bg-primary/10",
                ].join(" ")}
              >
                Dạy bài
              </button>
              <button
                type="button"
                onClick={() => setMode("qa")}
                className={[
                  "rounded-lg border px-3 py-1 text-xs font-semibold",
                  mode === "qa"
                    ? "border-primary bg-primary/15 text-primary"
                    : "border-border/70 text-muted-foreground hover:bg-primary/10",
                ].join(" ")}
              >
                Tra cứu
              </button>
              <select
                value={level}
                onChange={(e) => setLevel(e.target.value)}
                disabled={mode !== "tutor"}
                className="rounded-lg border border-border/70 bg-background/60 px-3 py-1 text-xs font-semibold text-foreground disabled:opacity-60"
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

          <div className="mt-5 min-h-[360px] max-h-[58vh] flex-1 space-y-4 overflow-y-auto rounded-lg border border-border/60 bg-background/25 p-3 pr-1">
            {messages.map((message) => (
              <div
                key={message.id}
                className={[
                  "max-w-[92%] rounded-lg border p-4 text-sm shadow-sm",
                  message.role === "user"
                    ? "ml-auto border-primary/40 bg-primary/15 text-foreground"
                    : "mr-auto border-border/70 bg-secondary/45 text-foreground",
                ].join(" ")}
              >
                <div className="text-xs uppercase tracking-wider text-muted-foreground">
                  {message.role === "user" ? "Bạn" : "Giáo viên AI"}
                </div>
                <div className="mt-2 whitespace-pre-line break-words leading-relaxed">
                  {message.content}
                  {message.isStreaming && (
                    <span className="ml-1 text-xs font-medium text-primary">đang viết...</span>
                  )}
                </div>
                {message.sources?.length ? (
                  <div className="mt-3 space-y-2 rounded-lg border border-border/70 bg-background/60 p-3 text-xs text-muted-foreground">
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
                {message.guidance &&
                (message.guidance.actions?.length ||
                  message.guidance.references?.length) ? (
                  <div className="mt-3 space-y-3 rounded-lg border border-primary/25 bg-primary/5 p-3">
                    {message.guidance.actions?.length ? (
                      <div>
                        <div className="text-xs font-semibold uppercase tracking-wider text-primary">
                          Hành động tiếp theo
                        </div>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {message.guidance.actions.map((action) => (
                            <Link
                              key={action.id}
                              href={action.href}
                              className="rounded-full border border-primary/30 bg-background/60 px-3 py-1.5 text-xs font-semibold text-primary hover:bg-primary/10"
                            >
                              {action.label}
                            </Link>
                          ))}
                        </div>
                      </div>
                    ) : null}
                    {message.guidance.references?.length ? (
                      <div className="space-y-2 rounded-lg border border-border/70 bg-background/70 p-3 text-xs text-muted-foreground">
                        <div className="font-semibold text-foreground">
                          Nguồn tham khảo thêm
                        </div>
                        {message.guidance.references.map((reference) => (
                          <div key={reference.id}>
                            {reference.href ? (
                              <Link
                                href={reference.href}
                                className="font-medium text-primary hover:underline"
                              >
                                {reference.title}
                              </Link>
                            ) : (
                              <div className="font-medium text-foreground">
                                {reference.title}
                              </div>
                            )}
                            {reference.description ? (
                              <div className="mt-0.5">{reference.description}</div>
                            ) : null}
                          </div>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </div>
            ))}
            {isSending && messages.length > 0 && !messages[messages.length - 1].isStreaming ? (
              <div className="rounded-lg border border-border/70 bg-secondary/40 p-4 text-xs text-muted-foreground">
                AI đang trả lời...
              </div>
            ) : null}
          </div>

          <div className="mt-5 rounded-lg border border-border/70 bg-background/45 p-3">
            <div className="mb-3 flex flex-wrap gap-2">
              {QUICK_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => setInput(prompt)}
                  disabled={isSending}
                  className="rounded-full border border-primary/20 bg-primary/5 px-3 py-1.5 text-xs font-semibold text-primary hover:bg-primary/10 disabled:opacity-50"
                >
                  {prompt}
                </button>
              ))}
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <textarea
                rows={2}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Hỏi điều bạn đang vướng..."
                className="flex-1 resize-none rounded-lg border border-border/70 bg-background/70 px-3 py-2 text-sm leading-relaxed text-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
              />
              <button
                type="button"
                disabled={!isAuthed || isSending || !input.trim()}
                onClick={handleSend}
                className="min-h-11 rounded-lg border border-primary/35 bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground hover:brightness-110 disabled:opacity-60"
              >
                {isSending ? "Đang gửi..." : "Gửi"}
              </button>
            </div>
            {!isAuthed ? (
              <p className="mt-2 text-xs text-muted-foreground">
                Vui lòng đăng nhập để dùng AI.
              </p>
            ) : null}
          </div>
          </div>
        </section>

        <details className="heritage-surface p-4">
          <summary className="cursor-pointer select-none text-sm font-semibold text-foreground">
            Công cụ phụ và ngữ cảnh
            <span className="ml-2 text-xs font-normal text-muted-foreground">
              tóm tắt, thẻ nhớ, chấm bài
            </span>
          </summary>
        <aside className="mt-4 grid gap-4 lg:grid-cols-2 xl:grid-cols-4">
          <div className="heritage-card p-5">
            <div className="relative">
            <h3 className="text-sm font-semibold text-foreground">
              Ngữ cảnh
            </h3>
            <p className="mt-1 text-xs text-muted-foreground">
              Điền khi muốn AI bám sát một bài học.
            </p>
            <div className="mt-4 space-y-3">
              <label className="block space-y-1">
                <span className="text-xs font-medium text-muted-foreground">Mã họa tiết</span>
                <input
                  type="text"
                  value={motifId}
                  onChange={(e) => setMotifId(e.target.value)}
                  placeholder="Ví dụ: motif UUID"
                  className="w-full rounded-lg border border-border/70 bg-background/60 px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
              </label>
              <label className="block space-y-1">
                <span className="text-xs font-medium text-muted-foreground">Slug Cửu Đỉnh</span>
                <input
                  type="text"
                  value={urnSlug}
                  onChange={(e) => setUrnSlug(e.target.value)}
                  placeholder="Ví dụ: cao-dinh"
                  className="w-full rounded-lg border border-border/70 bg-background/60 px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
              </label>
              <div className="text-xs text-muted-foreground">
                Mở từ bài học thường tự điền sẵn.
              </div>
            </div>
          </div>
          </div>

          <div className="heritage-card p-5">
            <div className="relative">
            <h3 className="text-sm font-semibold text-foreground">
              Tạo nhanh
            </h3>
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={handleSummary}
                className="rounded-full border border-primary/25 bg-background/45 px-3 py-1 text-xs font-semibold text-foreground hover:bg-primary/10 hover:text-primary"
              >
                Tóm tắt
              </button>
              <button
                type="button"
                onClick={handleFlashcards}
                className="rounded-full border border-primary/25 bg-background/45 px-3 py-1 text-xs font-semibold text-foreground hover:bg-primary/10 hover:text-primary"
              >
                Thẻ nhớ
              </button>
              <button
                type="button"
                onClick={handleCoach}
                className="rounded-full border border-primary/25 bg-background/45 px-3 py-1 text-xs font-semibold text-foreground hover:bg-primary/10 hover:text-primary"
              >
                Huấn luyện
              </button>
              <button
                type="button"
                onClick={handleReviewPlan}
                className="rounded-full border border-primary/25 bg-background/45 px-3 py-1 text-xs font-semibold text-foreground hover:bg-primary/10 hover:text-primary"
              >
                Ôn tập
              </button>
              <button
                type="button"
                onClick={handleDiagnostic}
                className="rounded-full border border-primary/25 bg-background/45 px-3 py-1 text-xs font-semibold text-foreground hover:bg-primary/10 hover:text-primary"
              >
                Chẩn đoán
              </button>
            </div>
          </div>
          </div>

          <div className="heritage-card p-5">
            <div className="relative">
            <h3 className="text-sm font-semibold text-foreground">
              Giải thích
            </h3>
            <label className="mt-3 block space-y-1">
              <span className="text-xs font-medium text-muted-foreground">Nội dung</span>
            <textarea
              rows={3}
              value={explainText}
              onChange={(e) => setExplainText(e.target.value)}
              placeholder="Nhập nội dung cần giải thích..."
              className="w-full rounded-lg border border-border/70 bg-background/60 px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
            </label>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <select
                value={explainLevel}
                onChange={(e) => setExplainLevel(e.target.value)}
                className="rounded-lg border border-border/70 bg-background/60 px-3 py-2 text-xs font-semibold text-foreground"
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
                disabled={isSending || !explainText.trim()}
                className="rounded-lg border border-primary/35 bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground hover:brightness-110 disabled:opacity-60"
              >
                Giải thích
              </button>
            </div>
          </div>
          </div>

          <div className="heritage-card p-5">
            <div className="relative">
            <h3 className="text-sm font-semibold text-foreground">
              Chấm nhanh
            </h3>
            <div className="mt-3 space-y-3">
              <label className="block space-y-1">
                <span className="text-xs font-medium text-muted-foreground">Câu hỏi</span>
                <input
                  type="text"
                  value={feedbackQuestion}
                  onChange={(e) => setFeedbackQuestion(e.target.value)}
                  placeholder="Nhập câu hỏi cần chấm"
                  className="w-full rounded-lg border border-border/70 bg-background/60 px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
              </label>
              <label className="block space-y-1">
                <span className="text-xs font-medium text-muted-foreground">Đáp án đúng</span>
                <input
                  type="text"
                  value={feedbackCorrect}
                  onChange={(e) => setFeedbackCorrect(e.target.value)}
                  placeholder="Nhập đáp án chuẩn"
                  className="w-full rounded-lg border border-border/70 bg-background/60 px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
              </label>
              <label className="block space-y-1">
                <span className="text-xs font-medium text-muted-foreground">Bài làm của bạn</span>
                <input
                  type="text"
                  value={feedbackAnswer}
                  onChange={(e) => setFeedbackAnswer(e.target.value)}
                  placeholder="Nhập câu trả lời cần nhận xét"
                  className="w-full rounded-lg border border-border/70 bg-background/60 px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
              </label>
              <button
                type="button"
                onClick={handleFeedback}
                disabled={
                  isSending ||
                  !feedbackQuestion.trim() ||
                  !feedbackCorrect.trim() ||
                  !feedbackAnswer.trim()
                }
                className="rounded-lg border border-primary/35 bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground hover:brightness-110 disabled:opacity-60"
              >
                Chấm bài
              </button>
            </div>
          </div>
          </div>
        </aside>
        </details>
      </div>
    </main>
  );
}
