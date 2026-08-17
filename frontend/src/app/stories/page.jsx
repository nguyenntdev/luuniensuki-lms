"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { BookOpen, Feather, Star } from "lucide-react";

import { listHistoryStories } from "@/lib/api";
import { asStoryList } from "@/lib/history";
import Skeleton from "@/components/Skeleton";
import VerificationNote from "@/components/history/VerificationNote";
import EpistemicLabel from "@/components/history/EpistemicLabel";
import { Badge } from "@/components/ui/badge";
import { setPageMeta } from "@/lib/seo";

export default function StoriesPage() {
  const [stories, setStories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setPageMeta({
      title: "Truyện sử — Lưu Niên Sử Kí",
      description: "Những câu chuyện lịch sử được dựng từ thực thể, nguồn và bằng chứng về Cửu Đỉnh.",
      path: "/stories",
    });
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await listHistoryStories();
        if (cancelled) return;
        setStories(asStoryList(res));
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
  }, []);

  return (
    <main className="site-shell">
      <section className="heritage-hero p-6 md:p-9">
        <div className="relative max-w-4xl">
          <div className="heritage-chip">
            <Feather className="h-4 w-4" aria-hidden="true" />
            Truyện sử
          </div>
          <h1 className="mt-5 font-display text-3xl font-bold tracking-tight text-foreground md:text-5xl">
            Những câu chuyện trên đồng
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground md:text-lg">
            Các bài viết được dựng từ từng khối nội dung: trích dẫn nguồn, điểm
            nhấn phù điêu, bản đồ, dòng thời gian và câu hỏi suy ngẫm. Chúng tôi
            không bịa thêm thông tin — điều gì chưa kiểm chứng sẽ được dán nhãn
            rõ ràng.
          </p>
        </div>
      </section>

      <div className="mt-5">
        <VerificationNote />
      </div>

      {error ? (
        <div
          role="alert"
          className="mt-5 rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive"
        >
          Không tải được danh sách truyện: {error}
        </div>
      ) : null}

      {loading ? (
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="heritage-card p-5">
              <Skeleton className="h-6 w-2/3" />
              <Skeleton className="mt-4 h-4 w-full" />
              <Skeleton className="mt-2 h-4 w-4/5" />
            </div>
          ))}
        </div>
      ) : stories.length > 0 ? (
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {stories.map((story) => (
            <Link
              key={String(story.id)}
              href={`/stories/${story.slug}`}
              className="heritage-card group flex flex-col gap-3 p-5 outline-none transition duration-200 hover:border-primary/40 focus-visible:ring-2 focus-visible:ring-primary"
            >
              <div className="flex items-start justify-between gap-3">
                <h2 className="font-display text-lg font-semibold text-foreground">
                  {story.title_vi || `Truyện #${story.slug || story.id}`}
                </h2>
                {story.featured ? (
                  <Star
                    className="h-4 w-4 shrink-0 fill-warning text-warning"
                    aria-label="Truyện nổi bật"
                  />
                ) : null}
              </div>
              {story.summary_vi ? (
                <p className="line-clamp-3 text-sm leading-6 text-muted-foreground">
                  {story.summary_vi}
                </p>
              ) : null}
              <div className="mt-auto flex flex-wrap items-center gap-2">
                <Badge variant="outline">
                  <BookOpen className="mr-1 h-3.5 w-3.5" aria-hidden="true" />
                  Truyện sử
                </Badge>
                <EpistemicLabel
                  info={{
                    label:
                      story.publication_status === "unreviewed"
                        ? "Chưa kiểm chứng"
                        : "Đã kiểm chứng",
                    tone:
                      story.publication_status === "unreviewed"
                        ? "unreviewed"
                        : "documented",
                  }}
                />
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="mt-6">
          <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border/70 bg-card/45 px-6 py-14 text-center">
            <Feather
              className="mb-3 h-8 w-8 text-muted-foreground"
              aria-hidden="true"
            />
            <h2 className="font-display text-base font-semibold text-foreground">
              Chưa có truyện nào
            </h2>
            <p className="mt-1 max-w-md text-sm text-muted-foreground">
              Các bài viết đang được biên tập. Khi một truyện được xuất bản, nó
              sẽ xuất hiện tại đây.
            </p>
          </div>
        </div>
      )}
    </main>
  );
}
