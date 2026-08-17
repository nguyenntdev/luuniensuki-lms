"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  ArrowRight,
  Boxes,
  BookOpen,
  Crown,
  Landmark,
  Map as MapIcon,
  Sparkles,
} from "lucide-react";

import { listHistoryEntities } from "@/lib/api";
import { asEntityList } from "@/lib/history";
import Skeleton from "@/components/Skeleton";
import EntityCard from "@/components/history/EntityCard";
import SectionHeading from "@/components/history/SectionHeading";
import VerificationNote from "@/components/history/VerificationNote";
import EpistemicLabel from "@/components/history/EpistemicLabel";

const INTERPRETATIONS = [
  {
    label: "Diễn giải / Interpretation",
    tone: "interpretation",
    text:
      "Nhiều nhà nghiên cứu xem Cửu Đỉnh như một 'bản đồ quốc gia' bằng đồng: việc chọn khắc các địa danh, sản vật và cảnh trí lên đỉnh vừa ghi nhận lãnh thổ, vừa khẳng định quyền lực và tầm nhìn của vương triều.",
  },
  {
    label: "Ghi chép / truyền thống",
    tone: "traditional",
    text:
      "Theo ghi chép truyền thống, vua Minh Mạng đích thân duyệt danh sách các hình tượng trước khi cho khắc, và việc hoàn thành Cửu Đỉnh được coi là một trong những sự kiện lớn của triều đình.",
  },
  {
    label: "Chưa chắc chắn / Uncertain",
    tone: "uncertain",
    text:
      "Chi tiết chính xác về số lần sửa đổi bản vẽ, chất lượng đồng và quy trình đúc hiện chưa được xác nhận đầy đủ qua nguồn — các con số cụ thể sẽ được cập nhật khi đối chiếu xong sử liệu.",
  },
];

export default function CuuDinhLanding() {
  const [urns, setUrns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    document.title = "Cửu Đỉnh — Lưu Niên Sử Kí";
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await listHistoryEntities({ entityType: "urn", limit: 20 });
        if (!cancelled) setUrns(asEntityList(res));
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
      {/* Definition & location */}
      <section className="heritage-hero p-6 md:p-10">
        <div className="relative max-w-4xl">
          <div className="heritage-chip">
            <Sparkles className="h-4 w-4" aria-hidden="true" />
            Di sản triều Nguyễn
          </div>
          <h1 className="mt-5 font-display text-4xl font-bold leading-tight text-foreground md:text-6xl">
            Cửu Đỉnh
            <span className="block text-gradient-bronze text-2xl md:text-3xl">
              Chín chiếc đỉnh đồng tại Thế Miếu
            </span>
          </h1>
          <p className="mt-6 text-base leading-7 text-muted-foreground md:text-lg">
            Cửu Đỉnh là chín chiếc đỉnh bằng đồng đặt tại Thế Miếu, bên trong
            Hoàng thành Huế. Được đúc trong giai đoạn 1835–1837 dưới triều Minh
            Mạng, mỗi chiếc đỉnh mang nhiều phù điêu khắc nổi về cảnh trí, địa
            danh, sinh vật và vật dụng của đất nước — tạo thành một bộ sưu tập
            hình ảnh được xem như bách khoa thư bằng đồng.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/atlas"
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
            >
              Khám phá 162 hình đúc
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
            <Link
              href="/urns/cao-dinh"
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-secondary/60 px-5 py-2.5 text-sm font-semibold text-foreground transition hover:border-primary/40 hover:bg-secondary"
            >
              <Boxes className="h-4 w-4 text-primary" aria-hidden="true" />
              Xem mô hình 3D
            </Link>
          </div>

          <div className="mt-8 flex flex-wrap gap-6 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-2">
              <Crown className="h-4 w-4 text-primary" aria-hidden="true" />
              Đúc 1835–1837 · triều Minh Mạng
            </span>
            <span className="inline-flex items-center gap-2">
              <Landmark className="h-4 w-4 text-primary" aria-hidden="true" />
              Thế Miếu · Hoàng thành Huế
            </span>
            <span className="inline-flex items-center gap-2">
              <MapIcon className="h-4 w-4 text-primary" aria-hidden="true" />
              162 hình tượng khắc nổi
            </span>
          </div>
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
          Không tải được dữ liệu đỉnh: {error}
        </div>
      ) : null}

      {/* Casting / commissioning context */}
      <section className="mt-10">
        <div className="heritage-surface p-6 md:p-8">
          <div className="relative grid gap-6 lg:grid-cols-2">
            <div className="max-w-3xl">
              <SectionHeading
                kicker="Bối cảnh chế tác"
                title="Một công trình đúc đồng lớn của triều Nguyễn"
                lead="Cửu Đỉnh được đặt trong giai đoạn 1835–1837, dưới triều vua Minh Mạng. Đây là một trong những dự án đúc đồng quy mô lớn của triều đình, đặt tại Thế Miếu — nơi thờ các vua triều Nguyễn."
              />
              <div className="mt-5 space-y-3 text-sm leading-7 text-muted-foreground">
                <p>
                  Mỗi chiếc đỉnh tương ứng với một nhóm chủ đề riêng, và toàn bộ
                  bộ đỉnh ghi lại nhiều địa danh cùng sản vật trên khắp lãnh thổ
                  đương thời.
                </p>
                <p>
                  Chi tiết về quy trình đúc, số lần chỉnh sửa bản vẽ và nguồn
                  đồng sẽ được bổ sung khi các nguồn tương ứng được kiểm chứng.
                </p>
              </div>
            </div>

            <div className="grid gap-3">
              <div className="rounded-lg border border-border bg-card/60 p-5">
                <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                  <Boxes className="h-4 w-4 text-primary" aria-hidden="true" />
                  9 đỉnh đồng
                </div>
                <p className="mt-2 text-sm text-muted-foreground">
                  Mỗi đỉnh mang 17 phù điêu (theo số liệu hiện có), tạo thành bộ
                  sưu tập 162 hình tượng.
                </p>
              </div>
              <div className="rounded-lg border border-border bg-card/60 p-5">
                <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                  <BookOpen className="h-4 w-4 text-primary" aria-hidden="true" />
                  Quan hệ với kho phù điêu
                </div>
                <p className="mt-2 text-sm text-muted-foreground">
                  Mỗi phù điêu là một mục tra cứu độc lập trong{" "}
                  <Link
                    href="/atlas"
                    className="font-medium text-primary hover:underline"
                  >
                    Atlas
                  </Link>{" "}
                  — gắn với đỉnh của nó, vị trí trên thân đỉnh và các nguồn sử
                  liệu liên quan.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Overview of all nine urns */}
      <section className="mt-10">
        <SectionHeading
          kicker="Chín chiếc đỉnh"
          title="Tổng quan chín chiếc đỉnh"
          lead="Danh sách dưới đây được nạp trực tiếp từ máy chủ lịch sử. Mở từng đỉnh để xem tóm tắt, các phù điêu và nguồn sử liệu."
        />
        {loading ? (
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(9)].map((_, i) => (
              <div key={i} className="heritage-card p-5">
                <Skeleton className="h-6 w-2/3" />
                <Skeleton className="mt-3 h-4 w-full" />
                <Skeleton className="mt-2 h-4 w-3/4" />
              </div>
            ))}
          </div>
        ) : urns.length > 0 ? (
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {urns.map((urn) => (
              <EntityCard
                key={urn.slug || urn.id}
                entity={urn}
                href={`/cuu-dinh/${urn.slug}`}
              />
            ))}
          </div>
        ) : (
          <div className="mt-6 rounded-lg border border-dashed border-border/70 bg-card/45 px-6 py-10 text-center text-sm text-muted-foreground">
            Chưa có dữ liệu đỉnh nào được nạp từ máy chủ lịch sử. Vui lòng quay
            lại sau.
          </div>
        )}
      </section>

      {/* Historical interpretations with epistemic labels */}
      <section className="mt-10">
        <SectionHeading
          kicker="Đọc Cửu Đỉnh"
          title="Một số cách đọc và diễn giải"
          lead="Các diễn giải dưới đây được dán nhãn theo mức độ kiểm chứng nguồn. Chúng thể hiện cách nhìn của nhiều người đọc khác nhau — không phải kết luận cuối cùng."
        />
        <div className="mt-6 grid gap-4 lg:grid-cols-3">
          {INTERPRETATIONS.map((item) => (
            <article
              key={item.label}
              className="flex flex-col gap-3 rounded-lg border border-border bg-card/60 p-5"
            >
              <EpistemicLabel
                info={{ label: item.label, tone: item.tone }}
                className="self-start"
              />
              <p className="text-sm leading-7 text-muted-foreground">
                {item.text}
              </p>
            </article>
          ))}
        </div>
      </section>

      {/* 3D exploration entry */}
      <section className="mt-10">
        <div className="heritage-hero flex flex-col items-center gap-5 p-6 text-center md:p-9">
          <h2 className="font-display text-2xl font-bold tracking-tight text-foreground md:text-3xl">
            Ngắm Cửu Đỉnh trong không gian 3D
          </h2>
          <p className="max-w-2xl text-sm leading-7 text-muted-foreground md:text-base">
            Mở trình xem 3D để xoay quanh đỉnh, phóng to và tìm hiểu vị trí các
            phù điêu trên thân đỉnh.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link
              href="/urns/cao-dinh"
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
            >
              <Boxes className="h-4 w-4" aria-hidden="true" />
              Xem Cửu Đỉnh 3D
            </Link>
            <Link
              href="/atlas"
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-secondary/60 px-5 py-2.5 text-sm font-semibold text-foreground transition hover:border-primary/40 hover:bg-secondary"
            >
              Mở Atlas
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}