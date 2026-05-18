"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { completeLesson, getMotifDetail, logAnalyticsEvent } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";
import { useMotifStore } from "@/stores/motifStore";

const CATEGORY_LABELS = {
  linh_thu: "Linh Thú",
  dong_vat: "Động Vật",
  thao_moc: "Thảo Mộc",
  dia_ly: "Địa Lý",
  nong_nghiep: "Nông Nghiệp",
  vo_bi: "Võ Bị",
  giao_thuong: "Giao Thương",
  thien_van: "Thiên Văn",
  kien_truc: "Kiến Trúc",
};

const RARITY_LABELS = {
  common: "Phổ Thông",
  uncommon: "Không Phổ Biến",
  rare: "Hiếm",
  epic: "Sử Thi",
  legendary: "Huyền Thoại",
};

const STATUS_LABELS = {
  discovered: "Đã Khám Phá",
  learned: "Đã Học",
  mastered: "Đã Thành Thạo",
  hidden: "Đã Khóa",
};

export default function MotifLessonPage() {
  const params = useParams();
  const motifId = useMemo(
    () => (typeof params?.motifId === "string" ? params.motifId : ""),
    [params],
  );

  const status = useAuthStore((s) => s.status);
  const fetchMe = useAuthStore((s) => s.fetchMe);
  const progressByMotifId = useMotifStore((s) => s.progressByMotifId);

  const [motif, setMotif] = useState(null);
  const [loading, setLoading] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);

  const mediaItems = useMemo(() => {
    const raw = motif?.lesson?.additional_images;
    if (!Array.isArray(raw)) return [];
    return raw
      .map((item, idx) => {
        if (typeof item === "string") {
          return {
            src: item,
            alt: `${motif?.name || "Hình ảnh"} ${idx + 1}`,
            caption: null,
          };
        }
        if (item && typeof item === "object") {
          const src =
            item.url || item.src || item.image_url || item.image || "";
          if (!src) return null;
          return {
            src,
            alt:
              item.alt ||
              item.caption ||
              `${motif?.name || "Hình ảnh"} ${idx + 1}`,
            caption: item.caption || item.title || null,
          };
        }
        return null;
      })
      .filter(Boolean);
  }, [motif?.lesson?.additional_images, motif?.name]);

  function trackMediaEvent(type) {
    if (!motifId) return;
    logAnalyticsEvent({
      name: type,
      payload: {
        motif_id: motifId,
        urn_id: motif?.urn?.id || null,
        source: "client",
      },
      path: `/motif/${motifId}`,
    }).catch(() => null);
  }

  // Check if motif is discovered
  const motifProgress = progressByMotifId[motifId];
  const isDiscovered =
    motifProgress?.status && motifProgress.status !== "hidden";
  const aiHref = useMemo(() => {
    if (!motifId) return "/ai";
    const params = new URLSearchParams();
    params.set("motifId", motifId);
    if (motif?.urn?.slug) {
      params.set("urnSlug", motif.urn.slug);
    }
    return `/ai?${params.toString()}`;
  }, [motif?.urn?.slug, motifId]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!motifId) return;

      // Redirect if not discovered
      if (!isDiscovered) {
        setError(
          "Bạn chưa khám phá họa tiết này. Hãy khám phá trên mô hình 3D trước!",
        );
        return;
      }

      setLoading(true);
      setError(null);
      try {
        const res = await getMotifDetail(motifId);
        if (!cancelled) setMotif(res);
      } catch (err) {
        if (!cancelled)
          setError(err instanceof Error ? err.message : String(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [motifId, isDiscovered]);

  async function handleCompleteLesson() {
    if (status !== "authed") return;
    if (!motifId) return;
    setCompleting(true);
    setNotice(null);
    setError(null);
    try {
      const res = await completeLesson({ motifId });
      const statusLabel = STATUS_LABELS[res.status] || res.status;
      setNotice(`Đã lưu: ${statusLabel}, +${res.xp_awarded} XP`);
      useMotifStore.getState().applyProgressUpdate({
        motifId,
        status: res.status,
        xpAwarded: res.xp_awarded,
        totalXp: res.total_xp,
      });
      await fetchMe();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setCompleting(false);
    }
  }

  return (
    <main className="site-shell">
      {!isDiscovered ? (
        <div className="rounded-lg border border-border bg-card p-6">
          <h1 className="text-xl font-display font-semibold text-foreground">
            Họa tiết đã khóa
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Bạn cần khám phá họa tiết trên mô hình 3D trước khi mở bài học.
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <Link
              href="/dashboard"
              className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
            >
              Về bảng học tập
            </Link>
            <Link
              href="/explore"
              className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-muted"
            >
              Khám phá Cửu Đỉnh
            </Link>
          </div>
        </div>
      ) : null}

      {isDiscovered ? (
        <>
          <div className="flex flex-wrap items-end justify-between gap-4 mb-8">
            <div>
              <h1 className="text-3xl font-display font-bold text-foreground tracking-tight">
                Bài học họa tiết
              </h1>
              <p className="mt-1 text-sm text-muted-foreground">
                Đọc, sau đó đánh dấu đã học để mở khóa phần trắc nghiệm.
              </p>
            </div>
          </div>

          {loading ? (
            <div className="mt-6 text-sm text-muted-foreground animate-pulse">
              Đang Tải Nội Dung…
            </div>
          ) : null}
          {error ? (
            <div className="mt-6 rounded-lg bg-destructive/10 p-4 text-sm text-destructive border border-destructive/20">
              {error}
            </div>
          ) : null}
          {notice ? (
            <div className="mt-6 rounded-lg bg-success/10 p-4 text-sm text-success border border-success/20">
              {notice}
            </div>
          ) : null}

          {motif ? (
            <div className="space-y-8">
              {/* Header Card */}
              <div className="rounded-lg border border-border bg-card p-6 shadow-lg">
                <div className="flex flex-wrap items-start justify-between gap-6">
                  <div className="min-w-0 flex-1">
                    <div className="text-xs font-bold uppercase tracking-wider text-primary">
                      {motif.urn?.name}
                    </div>
                    <h2 className="mt-2 text-3xl font-display font-bold text-foreground leading-tight">
                      {motif.name}
                    </h2>
                    {motif.name_en ? (
                      <div className="mt-1 text-lg text-muted-foreground font-medium">
                        {motif.name_en}
                      </div>
                    ) : null}

                    <div className="mt-4 flex flex-wrap items-center gap-3">
                      <span className="inline-flex items-center rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground border border-border">
                        {CATEGORY_LABELS[motif.category] || motif.category}
                      </span>
                      <span
                        className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium border ${
                          motif.rarity === "legendary"
                            ? "bg-bronze/10 text-bronze border-bronze/20"
                            : motif.rarity === "epic"
                              ? "bg-primary/10 text-primary border-primary/20"
                              : motif.rarity === "rare"
                                ? "bg-info/10 text-info border-info/20"
                                : "bg-muted/50 text-muted-foreground border-border"
                        }`}
                      >
                        {RARITY_LABELS[motif.rarity] || motif.rarity}
                      </span>
                      <span className="inline-flex items-center rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary border border-primary/20">
                        Trắc Nghiệm:{" "}
                        <span className="font-display tabular-nums">
                          {motif.quiz_question_count ?? 0}
                        </span>{" "}
                        Câu
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
                    <Link
                      href={aiHref}
                      className="inline-flex justify-center items-center rounded-lg border border-primary/40 bg-primary/10 px-5 py-2.5 text-sm font-semibold text-primary shadow-sm hover:bg-primary/15 transition-colors"
                    >
                      Hỏi AI
                    </Link>
                    <Link
                      href={`/motif/${motif.id}/quiz`}
                      className="inline-flex justify-center items-center rounded-lg border border-border bg-card px-5 py-2.5 text-sm font-semibold text-muted-foreground shadow-sm hover:bg-muted hover:text-foreground transition-colors"
                    >
                      Làm Trắc Nghiệm
                    </Link>
                    <button
                      onClick={handleCompleteLesson}
                      disabled={status !== "authed" || completing}
                      className={[
                        "inline-flex justify-center items-center rounded-lg px-5 py-2.5 text-sm font-semibold text-primary-foreground shadow-sm transition-all",
                        status !== "authed" || completing
                          ? "bg-muted cursor-not-allowed text-muted-foreground"
                          : "bg-primary hover:bg-primary/90 hover:shadow-lg",
                      ].join(" ")}
                    >
                      {status === "authed"
                        ? completing
                          ? "Đang Lưu…"
                          : "Hoàn Thành Bài Học"
                        : "Đăng nhập để lưu"}
                    </button>
                  </div>
                </div>

                {motif.thumbnail_url ? (
                  <div className="mt-8 aspect-video w-full overflow-hidden rounded-lg bg-muted border border-border">
                    <img
                      src={motif.thumbnail_url}
                      alt={motif.name}
                      className="h-full w-full object-cover"
                    />
                  </div>
                ) : null}
              </div>

              {/* Lesson Content */}
              <div className="grid gap-6">
                {/* Main Lesson Text */}
                <div className="rounded-lg border border-border bg-card p-6 md:p-8">
                  <div className="flex items-center justify-between gap-3 mb-4">
                    <h3 className="text-xl font-display font-bold text-foreground">
                      Bài Học
                    </h3>
                    {motif.lesson?.is_ai_generated ? (
                      <span className="rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-700">
                        AI hỗ trợ
                      </span>
                    ) : null}
                  </div>
                  <div className="prose prose-primary prose-sm sm:prose-base max-w-none text-muted-foreground leading-relaxed">
                    {motif.lesson?.description ||
                      motif.lesson?.intro_text ||
                      "Chưa có nội dung bài học."}
                  </div>
                </div>

                {(motif.lesson?.audio_narration_url ||
                  motif.lesson?.video_url) && (
                  <div className="rounded-lg border border-border bg-card p-6 md:p-8 space-y-4">
                    <h3 className="text-lg font-display font-bold text-foreground">
                      Nội dung đa phương tiện
                    </h3>
                    {motif.lesson?.audio_narration_url && (
                      <div className="space-y-2">
                        <div className="text-sm font-medium text-muted-foreground">
                          Nghe thuyết minh
                        </div>
                        <audio
                          controls
                          onPlay={() => trackMediaEvent("lesson_audio_play")}
                          className="w-full"
                          src={motif.lesson.audio_narration_url}
                        />
                      </div>
                    )}
                    {motif.lesson?.video_url && (
                      <div className="space-y-2">
                        <div className="text-sm font-medium text-muted-foreground">
                          Xem video
                        </div>
                        <video
                          controls
                          onPlay={() => trackMediaEvent("lesson_video_play")}
                          className="w-full rounded-lg border border-border bg-black"
                          src={motif.lesson.video_url}
                        />
                      </div>
                    )}
                  </div>
                )}

                {mediaItems.length > 0 && (
                  <div className="rounded-lg border border-border bg-card p-6 md:p-8">
                    <h3 className="text-lg font-display font-bold text-foreground mb-4">
                      Hình ảnh bổ sung
                    </h3>
                    <div className="grid gap-4 sm:grid-cols-2">
                      {mediaItems.map((item, idx) => (
                        <figure
                          key={`${item.src}-${idx}`}
                          className="overflow-hidden rounded-lg border border-border bg-muted"
                        >
                          <img
                            src={item.src}
                            alt={item.alt}
                            className="h-48 w-full object-cover"
                          />
                          {item.caption ? (
                            <figcaption className="px-3 py-2 text-xs text-muted-foreground">
                              {item.caption}
                            </figcaption>
                          ) : null}
                        </figure>
                      ))}
                    </div>
                  </div>
                )}

                {/* Historical Context */}
                {motif.lesson?.historical_context && (
                  <div className="rounded-lg border border-border bg-card p-6 md:p-8 relative overflow-hidden">
                    <div className="flex items-start gap-4">
                      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-bronze/10 flex items-center justify-center text-xl">
                        📖
                      </div>
                      <div>
                        <h4 className="text-lg font-display font-bold text-foreground mb-2">
                          Bối Cảnh Lịch Sử
                        </h4>
                        <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
                          {motif.lesson.historical_context}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Symbolism */}
                {motif.lesson?.symbolism && (
                  <div className="rounded-lg border border-primary/20 bg-primary/5 p-6 md:p-8">
                    <div className="flex items-start gap-4">
                      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-xl">
                        🔮
                      </div>
                      <div>
                        <h4 className="text-lg font-display font-bold text-primary mb-2">
                          Ý Nghĩa Biểu Tượng
                        </h4>
                        <p className="text-sm sm:text-base text-primary/80 leading-relaxed">
                          {motif.lesson.symbolism}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Fun Fact */}
                {motif.lesson?.fun_fact && (
                  <div className="rounded-lg border-2 border-bronze/30 bg-bronze/5 p-6 md:p-8">
                    <div className="flex items-start gap-4">
                      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-bronze/10 flex items-center justify-center text-xl">
                        ⭐
                      </div>
                      <div>
                        <h4 className="text-lg font-display font-bold text-bronze mb-2">
                          Điều Thú Vị
                        </h4>
                        <p className="text-sm sm:text-base text-bronze/80 font-medium leading-relaxed">
                          {motif.lesson.fun_fact}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </>
      ) : null}
    </main>
  );
}
