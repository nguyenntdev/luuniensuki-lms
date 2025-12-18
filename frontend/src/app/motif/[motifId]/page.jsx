"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { completeLesson, getMotifDetail } from "@/lib/api";
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
  const router = useRouter();
  const motifId = useMemo(() => (typeof params?.motifId === "string" ? params.motifId : ""), [params]);

  const token = useAuthStore((s) => s.accessToken);
  const fetchMe = useAuthStore((s) => s.fetchMe);
  const progressByMotifId = useMotifStore((s) => s.progressByMotifId);

  const [motif, setMotif] = useState(null);
  const [loading, setLoading] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);

  // Check if motif is discovered
  const motifProgress = progressByMotifId[motifId];
  const isDiscovered = motifProgress?.status && motifProgress.status !== "hidden";

  useEffect(() => {
    if (token) fetchMe();
  }, [token, fetchMe]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!motifId) return;

      // Redirect if not discovered
      if (!isDiscovered) {
        setError("Bạn chưa khám phá họa tiết này. Hãy khám phá trên mô hình 3D trước!");
        setTimeout(() => {
          router.push("/explore");
        }, 2000);
        return;
      }

      setLoading(true);
      setError(null);
      try {
        const res = await getMotifDetail(motifId);
        if (!cancelled) setMotif(res);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [motifId, isDiscovered, router]);

  async function handleCompleteLesson() {
    if (!token) return;
    if (!motifId) return;
    setCompleting(true);
    setNotice(null);
    setError(null);
    try {
      const res = await completeLesson({ token, motifId });
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
    <main className="mx-auto max-w-4xl px-6 py-10 pb-24">
      <div className="flex flex-wrap items-end justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-display font-bold text-foreground tracking-tight">Bài Học Họa Tiết</h1>
          <p className="mt-1 text-sm text-muted-foreground">Đọc, sau đó đánh dấu đã học để mở khóa phần trắc nghiệm.</p>
        </div>
      </div>

      {loading ? <div className="mt-6 text-sm text-muted-foreground animate-pulse">Đang Tải Nội Dung…</div> : null}
      {error ? <div className="mt-6 rounded-lg bg-destructive/10 p-4 text-sm text-destructive border border-destructive/20">{error}</div> : null}
      {notice ? <div className="mt-6 rounded-lg bg-success/10 p-4 text-sm text-success border border-success/20">{notice}</div> : null}

      {motif ? (
        <div className="space-y-8">
          {/* Header Card */}
          <div className="rounded-3xl border border-border bg-card p-6 shadow-lg">
            <div className="flex flex-wrap items-start justify-between gap-6">
              <div className="min-w-0 flex-1">
                <div className="text-xs font-bold uppercase tracking-wider text-primary">{motif.urn?.name}</div>
                <h2 className="mt-2 text-3xl font-display font-bold text-foreground leading-tight">{motif.name}</h2>
                {motif.name_en ? <div className="mt-1 text-lg text-muted-foreground font-medium">{motif.name_en}</div> : null}
                
                <div className="mt-4 flex flex-wrap items-center gap-3">
                  <span className="inline-flex items-center rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground border border-border">
                    {CATEGORY_LABELS[motif.category] || motif.category}
                  </span>
                  <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium border ${
                    motif.rarity === 'legendary' ? 'bg-bronze/10 text-bronze border-bronze/20' :
                    motif.rarity === 'epic' ? 'bg-primary/10 text-primary border-primary/20' :
                    motif.rarity === 'rare' ? 'bg-info/10 text-info border-info/20' :
                    'bg-muted/50 text-muted-foreground border-border'
                  }`}>
                    {RARITY_LABELS[motif.rarity] || motif.rarity}
                  </span>
                  <span className="inline-flex items-center rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary border border-primary/20">
                    Trắc Nghiệm: <span className="font-display tabular-nums">{motif.quiz_question_count ?? 0}</span> Câu
                  </span>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
                <Link
                  href={`/motif/${motif.id}/quiz`}
                  className="inline-flex justify-center items-center rounded-xl border border-border bg-card px-5 py-2.5 text-sm font-semibold text-muted-foreground shadow-sm hover:bg-muted hover:text-foreground transition-colors"
                >
                  Làm Trắc Nghiệm
                </Link>
                <button
                  onClick={handleCompleteLesson}
                  disabled={!token || completing}
                  className={[
                    "inline-flex justify-center items-center rounded-xl px-5 py-2.5 text-sm font-semibold text-primary-foreground shadow-sm transition-all",
                    !token || completing 
                      ? "bg-muted cursor-not-allowed text-muted-foreground" 
                      : "bg-primary hover:bg-primary/90 hover:shadow-lg",
                  ].join(" ")}
                >
                  {token ? (completing ? "Đang Lưu…" : "Hoàn Thành Bài Học") : "Đăng Nhập Để Lưu"}
                </button>
              </div>
            </div>

            {motif.thumbnail_url ? (
              <div className="mt-8 aspect-video w-full overflow-hidden rounded-2xl bg-muted border border-border">
                <img src={motif.thumbnail_url} alt={motif.name} className="h-full w-full object-cover" />
              </div>
            ) : null}
          </div>

          {/* Lesson Content */}
          <div className="grid gap-6">
            
            {/* Main Lesson Text */}
            <div className="rounded-2xl border border-border bg-card p-6 md:p-8">
              <h3 className="text-xl font-display font-bold text-foreground mb-4">Bài Học</h3>
              <div className="prose prose-primary prose-sm sm:prose-base max-w-none text-muted-foreground leading-relaxed">
                {motif.lesson?.description || motif.lesson?.intro_text || "Chưa có nội dung bài học."}
              </div>
            </div>

            {/* Historical Context */}
            {motif.lesson?.historical_context && (
              <div className="rounded-2xl border border-border bg-card p-6 md:p-8 relative overflow-hidden">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-bronze/10 flex items-center justify-center text-xl">
                    📖
                  </div>
                  <div>
                    <h4 className="text-lg font-display font-bold text-foreground mb-2">Bối Cảnh Lịch Sử</h4>
                    <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
                      {motif.lesson.historical_context}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Symbolism */}
            {motif.lesson?.symbolism && (
              <div className="rounded-2xl border border-primary/20 bg-primary/5 p-6 md:p-8">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-xl">
                    🔮
                  </div>
                  <div>
                    <h4 className="text-lg font-display font-bold text-primary mb-2">Ý Nghĩa Biểu Tượng</h4>
                    <p className="text-sm sm:text-base text-primary/80 leading-relaxed">
                      {motif.lesson.symbolism}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Fun Fact */}
            {motif.lesson?.fun_fact && (
              <div className="rounded-2xl border-2 border-bronze/30 bg-bronze/5 p-6 md:p-8">
                 <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-bronze/10 flex items-center justify-center text-xl">
                    ⭐
                  </div>
                  <div>
                    <h4 className="text-lg font-display font-bold text-bronze mb-2">Điều Thú Vị</h4>
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
    </main>
  );
}
