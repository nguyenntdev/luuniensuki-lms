"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  ArrowRight,
  BookOpen,
  Bot,
  Boxes,
  Compass,
  Landmark,
  Layers,
  Library,
  Map as MapIcon,
  Network,
  ScrollText,
  Sparkles,
  UserRound,
} from "lucide-react";

import { useAuthStore } from "@/stores/authStore";
import { listHistoryEntities } from "@/lib/api";
import {
  asEntityList,
  entityName,
  KNOWN_URNS,
  listTotal,
  reliefNumberFromSlug,
  urnNameFromSlug,
  urnSlugFromReliefSlug,
} from "@/lib/history";
import { setPageMeta } from "@/lib/seo";
import { cn } from "@/lib/utils";
import Skeleton from "@/components/Skeleton";
import EntityCard from "@/components/history/EntityCard";
import SectionHeading from "@/components/history/SectionHeading";
import VerificationNote from "@/components/history/VerificationNote";
import EpistemicLabel from "@/components/history/EpistemicLabel";

const RELIEF_PREVIEW_COUNT = 8;

function PrimaryLink({ href, children }) {
  return (
    <Link
      href={href}
      className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background"
    >
      {children}
    </Link>
  );
}

function SecondaryLink({ href, icon: Icon, children }) {
  return (
    <Link
      href={href}
      className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-border bg-secondary/60 px-5 py-2.5 text-sm font-semibold text-foreground transition hover:border-primary/40 hover:bg-secondary focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background"
    >
      {Icon ? <Icon className="h-4 w-4 text-primary" aria-hidden="true" /> : null}
      {children}
    </Link>
  );
}

function TertiaryLink({ href, icon: Icon, children }) {
  return (
    <Link
      href={href}
      className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg px-3 text-sm font-semibold text-muted-foreground underline decoration-border underline-offset-4 transition hover:text-foreground hover:decoration-primary focus-visible:ring-2 focus-visible:ring-primary"
    >
      {Icon ? <Icon className="h-4 w-4" aria-hidden="true" /> : null}
      {children}
    </Link>
  );
}

function HeroStat({ value, label }) {
  return (
    <div className="heritage-stat px-3 py-3">
      <div className="font-display text-xl font-semibold tabular-nums text-foreground">
        {value}
      </div>
      <div className="mt-0.5 text-xs leading-5 text-muted-foreground">
        {label}
      </div>
    </div>
  );
}

// Stylized bronze-rimmed urn silhouette used as a static, SSR-renderable
// poster motif. Decorative only; links wrapping it carry the real labels.
function UrnShape({ className }) {
  return (
    <div aria-hidden="true" className={cn("relative", className)}>
      <div className="absolute -top-[0.35em] left-1/2 h-[0.8em] w-[118%] -translate-x-1/2 rounded-t-full border border-bronze-accent/40 bg-paper-elevated" />
      <div className="absolute inset-x-0 bottom-0 top-[0.45em] rounded-t-[46%] rounded-b-md border border-bronze-accent/35 bg-paper-elevated" />
      <div className="absolute left-1/2 top-[42%] h-[46%] w-[46%] -translate-x-1/2 rounded-full border border-bronze-accent/25" />
    </div>
  );
}

function UrnGlyph({ slug, nameVi }) {
  const label = `Mở trang ${nameVi}`;
  return (
    <Link
      href={`/cuu-dinh/${slug}`}
      aria-label={label}
      title={label}
      className="group flex w-[2.7rem] flex-col items-center gap-1.5 rounded-md outline-none focus-visible:ring-2 focus-visible:ring-primary"
    >
      <UrnShape className="h-10 w-8 transition group-hover:border-bronze-accent/70" />
      <span className="w-full truncate text-center text-[0.55rem] text-muted-foreground transition group-hover:text-foreground">
        {nameVi.split(" ")[0]}
      </span>
    </Link>
  );
}

function PosterPanel() {
  return (
    <div
      className="heritage-surface relative overflow-hidden p-6"
      aria-label="Hình minh họa: chín chiếc đỉnh đồng"
    >
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-12 -top-12 h-52 w-52 rounded-full border border-bronze-accent/20"
      >
        <div className="absolute inset-6 rounded-full border border-bronze-accent/15" />
      </div>
      <div className="relative flex items-center gap-2 text-[0.65rem] font-bold uppercase tracking-[0.16em] text-bronze-accent">
        <Landmark className="h-3.5 w-3.5" aria-hidden="true" />
        Thế Miếu · Hoàng thành Huế
      </div>
      <div className="relative mt-5 flex flex-wrap justify-between gap-x-1 gap-y-4 pb-1">
        {KNOWN_URNS.map((urn) => (
          <UrnGlyph key={urn.slug} slug={urn.slug} nameVi={urn.nameVi} />
        ))}
      </div>
      <div className="relative mt-5 flex flex-wrap items-center justify-between gap-2 border-t border-border/60 pt-4 text-[0.7rem] text-muted-foreground">
        <span>Chín chiếc đỉnh đồng · đúc 1835–1837</span>
        <span className="inline-flex items-center gap-1.5 text-bronze-accent">
          <Boxes className="h-3.5 w-3.5" aria-hidden="true" />
          162 hình đúc khắc nổi
        </span>
      </div>
    </div>
  );
}

function ExploreTeaser({ icon: Icon, title, lead, href, cta }) {
  return (
    <Link
      href={href}
      className="focus-card group flex flex-col gap-4 p-6 outline-none transition duration-200 hover:border-primary/40 focus-visible:ring-2 focus-visible:ring-primary"
    >
      <span className="flex h-11 w-11 items-center justify-center rounded-lg border border-bronze-accent/25 bg-bronze-accent/10 text-bronze-accent">
        <Icon className="h-5 w-5" aria-hidden="true" />
      </span>
      <div>
        <h3 className="font-display text-lg font-semibold text-foreground">
          {title}
        </h3>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">{lead}</p>
      </div>
      <span className="mt-auto inline-flex items-center gap-1.5 text-sm font-medium text-primary">
        {cta}
        <ArrowRight
          className="h-4 w-4 transition group-hover:translate-x-0.5"
          aria-hidden="true"
        />
      </span>
    </Link>
  );
}

function ReliefPlate({ relief }) {
  const name = entityName(relief);
  const urnSlug = relief.urn_slug || urnSlugFromReliefSlug(relief.slug);
  const num = reliefNumberFromSlug(relief.slug);
  const thumb = relief.thumbnail_url;
  return (
    <Link
      href={`/atlas/${urnSlug}/${relief.slug}`}
      className="group flex flex-col overflow-hidden rounded-lg border border-border/70 bg-card/60 outline-none transition duration-200 hover:border-primary/40 focus-visible:ring-2 focus-visible:ring-primary"
    >
      <div className="relative aspect-[4/3] overflow-hidden bg-muted/60">
        {thumb ? (
          <img
            src={thumb}
            alt={name}
            loading="lazy"
            decoding="async"
            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.03]"
          />
        ) : (
          <div className="flex h-full w-full flex-col items-center justify-center gap-1 text-muted-foreground">
            <span className="font-serif text-2xl text-bronze-accent">
              {num ? `#${num}` : "·"}
            </span>
            <span className="text-[0.6rem] uppercase tracking-wide">
              {urnNameFromSlug(urnSlug)}
            </span>
          </div>
        )}
        {num ? (
          <span className="absolute left-2 top-2 rounded-md bg-ink/80 px-1.5 py-0.5 text-[0.6rem] font-bold tabular-nums text-paper">
            {num}
          </span>
        ) : null}
      </div>
      <div className="flex-1 p-3">
        <p className="line-clamp-1 text-xs font-medium text-foreground">
          {name}
        </p>
        <p className="mt-1 text-[0.65rem] text-muted-foreground">
          {urnNameFromSlug(urnSlug)}
        </p>
      </div>
    </Link>
  );
}

const EPISTEMIC_CONCEPTS = [
  {
    info: { label: "Được nguồn xác nhận", tone: "documented" },
    text: "Nhận định dựa trên nguồn đã được đối chiếu và xác nhận bởi biên tập hoặc chuyên gia.",
  },
  {
    info: { label: "Diễn giải", tone: "interpretation" },
    text: "Cách đọc, cách giải thích của nhà nghiên cứu về ý nghĩa một hình tượng — được dán nhãn để phân biệt với sự kiện đã xác thực.",
  },
  {
    info: { label: "Chưa chắc chắn", tone: "uncertain" },
    text: "Chi tiết chưa được xác nhận đầy đủ qua sử liệu hiện có; nội dung sẽ được cập nhật khi đối chiếu xong nguồn.",
  },
];

export default function HomePage() {
  const status = useAuthStore((s) => s.status);
  const [urns, setUrns] = useState([]);
  const [reliefs, setReliefs] = useState([]);
  const [reliefTotal, setReliefTotal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setPageMeta({
      title: "Lưu Niên Sử Kí — Cửu Đỉnh, bách khoa thư bằng đồng của triều Nguyễn",
      description:
        "Chín chiếc đỉnh đồng tại Thế Miếu, Hoàng thành Huế, với 162 hình đúc khắc nổi — tra cứu, đối chiếu nguồn sử liệu và học di sản, mở cho tất cả mọi người.",
      path: "/",
    });
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [urnRes, reliefRes] = await Promise.all([
          listHistoryEntities({ entityType: "urn", limit: 20 }),
          listHistoryEntities({
            entityType: "relief",
            limit: RELIEF_PREVIEW_COUNT,
          }),
        ]);
        if (cancelled) return;
        setUrns(asEntityList(urnRes));
        setReliefs(asEntityList(reliefRes));
        setReliefTotal(listTotal(reliefRes));
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

  const isAuthed = status === "authed";

  return (
    <main className="site-shell">
      {/* 1 · Hero */}
      <section className="heritage-hero p-6 md:p-10" aria-labelledby="home-hero-title">
        <div className="relative grid gap-9 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
          <div>
            <p className="page-kicker inline-flex items-center gap-2 rounded-full border border-border/60 bg-secondary/50 px-3 py-1.5">
              <Landmark className="h-3.5 w-3.5 text-bronze-accent" aria-hidden="true" />
              Triều Nguyễn · Đúc 1835–1837
            </p>
            <h1
              id="home-hero-title"
              className="mt-4 font-serif text-4xl font-bold tracking-tight text-foreground text-balance md:text-6xl"
            >
              Cửu Đỉnh
            </h1>
            <p className="mt-3 font-serif text-xl italic text-bronze-accent md:text-2xl">
              Bách khoa thư bằng đồng của một vương triều
            </p>
            <p className="mt-5 max-w-xl text-base leading-7 text-muted-foreground text-pretty md:text-lg">
              Chín chiếc đỉnh đồng đặt tại Thế Miếu, trong Hoàng thành Huế, được
              đúc dưới triều Minh Mạng. Trên thân đỉnh khắc nổi 162 hình tượng về
              núi sông, muôn thú, cây cỏ, vũ khí và biển đảo của đất nước. Lưu
              Niên Sử Kí là nơi tra cứu và học di sản này — mọi nhận định đều gắn
              với nguồn sử liệu và mở cho tất cả mọi người, không cần đăng nhập.
            </p>

            <div className="mt-7 flex flex-wrap items-center gap-3">
              <PrimaryLink href="/atlas">
                Khám phá 162 hình đúc
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </PrimaryLink>
              <SecondaryLink href="/urns/cao-dinh" icon={Boxes}>
                Xem Cửu Đỉnh 3D
              </SecondaryLink>
              <TertiaryLink href="/practice" icon={BookOpen}>
                Bắt đầu học
              </TertiaryLink>
            </div>

            <div className="mt-8 grid max-w-md grid-cols-3 gap-2">
              <HeroStat value="9" label="đỉnh đồng tại Thế Miếu" />
              <HeroStat value={reliefTotal ?? 162} label="hình đúc khắc nổi" />
              <HeroStat value="Có nguồn" label="dữ liệu gắn sử liệu công khai" />
            </div>
          </div>

          <PosterPanel />
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
          Không tải được dữ liệu lịch sử: {error}
        </div>
      ) : null}

      {/* 2 · Nine-urn gallery (museum objects, not progress cards) */}
      <section className="mt-12" aria-labelledby="nine-urns-heading">
        <div id="nine-urns-heading">
          <SectionHeading
            kicker="Chín chiếc đỉnh"
            title="Chín chiếc đỉnh — chín nhóm hình tượng"
            lead="Mỗi chiếc đỉnh là một hiện vật riêng, mang một nhóm hình tượng về đất nước. Mở từng đỉnh để xem tóm tắt, các phù điêu và nguồn sử liệu liên quan."
          />
        </div>
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

      {/* 3 · Atlas of 162 — visual preview grid */}
      <section className="mt-12" aria-labelledby="atlas-heading">
        <div className="heritage-surface p-6 md:p-8">
          <div id="atlas-heading">
            <SectionHeading
              kicker="Atlas"
              title="162 hình đúc — bộ sưu tập toàn bộ phù điêu"
              lead="Toàn bộ hình tượng khắc nổi trên chín chiếc đỉnh đồng: tìm theo tên, lọc theo đỉnh, và mở từng phù điêu để xem mô tả, vị trí trên thân đỉnh và nguồn sử liệu."
            />
          </div>

          {loading ? (
            <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
              {[...Array(RELIEF_PREVIEW_COUNT)].map((_, i) => (
                <div
                  key={i}
                  className="overflow-hidden rounded-lg border border-border/70 bg-card/60"
                >
                  <Skeleton className="aspect-[4/3] w-full" />
                  <div className="p-3">
                    <Skeleton className="h-3 w-3/4" />
                    <Skeleton className="mt-2 h-2.5 w-1/2" />
                  </div>
                </div>
              ))}
            </div>
          ) : reliefs.length > 0 ? (
            <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
              {reliefs.map((relief) => (
                <ReliefPlate key={relief.slug || relief.id} relief={relief} />
              ))}
            </div>
          ) : (
            <div className="mt-6 rounded-lg border border-dashed border-border/70 bg-card/45 px-6 py-8 text-center text-sm text-muted-foreground">
              Chưa có dữ liệu phù điêu nào được nạp từ máy chủ lịch sử.
            </div>
          )}

          <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-border/60 pt-5">
            <p className="flex items-center gap-2 text-sm text-muted-foreground">
              <Layers className="h-4 w-4 text-bronze-accent" aria-hidden="true" />
              {reliefTotal ?? 162} hình đúc · tìm kiếm và lọc theo đỉnh, trạng
              thái
            </p>
            <PrimaryLink href="/atlas">
              Mở Atlas
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </PrimaryLink>
          </div>
        </div>
      </section>

      {/* 4 · Explore by space / time / story / connections */}
      <section className="mt-12" aria-labelledby="explore-heading">
        <div id="explore-heading">
          <SectionHeading
            kicker="Khám phá"
            title="Từ bản đồ đến dòng thời gian"
            lead="Di sản có nhiều lối vào: không gian, thời gian, câu chuyện và mạng lưới liên kết giữa các thực thể."
          />
        </div>
        <div className="section-grid mt-6 grid-cols-1 sm:grid-cols-2 xl:grid-cols-4">
          <ExploreTeaser
            icon={MapIcon}
            title="Bản đồ địa danh"
            lead="Từ Trường Sơn đến biển đảo phía Đông — các địa danh được chọn khắc lên đỉnh nói lên cách vương triều hình dung lãnh thổ."
            href="/map"
            cta="Xem bản đồ"
          />
          <ExploreTeaser
            icon={ScrollText}
            title="Dòng thời gian"
            lead="Bối cảnh triều Nguyễn từ 1802 đến 1945: sự kiện, con người và hoàn cảnh quanh việc đúc Cửu Đỉnh."
            href="/timeline"
            cta="Theo dòng thời gian"
          />
          <ExploreTeaser
            icon={BookOpen}
            title="Câu chuyện"
            lead="Những bài viết dài về Cửu Đỉnh: bối cảnh chế tác, ý nghĩa biểu tượng và cách các thế hệ đọc lại bộ đỉnh."
            href="/stories"
            cta="Đọc câu chuyện"
          />
          <ExploreTeaser
            icon={Network}
            title="Mạng lưới liên kết"
            lead="Đỉnh, phù điêu, địa danh, nhân vật và nguồn sử liệu được nối với nhau thành một mạng tra cứu mở."
            href="/explore/connections"
            cta="Khám phá liên kết"
          />
        </div>
      </section>

      {/* 5 · 3D as a historical instrument */}
      <section className="mt-12" aria-labelledby="td-heading">
        <div className="heritage-surface p-6 md:p-8">
          <div className="grid gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
            <div>
              <div id="td-heading">
                <SectionHeading
                  kicker="Trải nghiệm 3D"
                  title="Cửu Đỉnh trong không gian ba chiều"
                  lead="3D ở đây là một công cụ lịch sử: xoay quanh thân đỉnh, phóng to từng phù điêu, và đối chiếu hình tượng với vị trí thực trên hiện vật. Bắt đầu với Cao Đỉnh — mô hình đã được dựng để khám phá chi tiết khắc nổi."
                />
              </div>
              <div className="mt-6 flex flex-wrap gap-3">
                <SecondaryLink href="/urns/cao-dinh" icon={Boxes}>
                  Mở trình xem Cửu Đỉnh 3D
                </SecondaryLink>
                <TertiaryLink href="/cuu-dinh">
                  Về trang Cửu Đỉnh
                </TertiaryLink>
              </div>
            </div>
            <div
              className="relative flex items-center justify-center overflow-hidden rounded-lg border border-border/70 bg-secondary/40 p-8"
              role="img"
              aria-label="Minh họa: cửa sổ trình xem 3D chiếc đỉnh đồng Cao Đỉnh"
            >
              <div
                aria-hidden="true"
                className="pointer-events-none absolute -left-12 -top-12 h-44 w-44 rounded-full border border-bronze-accent/20"
              >
                <div className="absolute inset-6 rounded-full border border-bronze-accent/15" />
              </div>
              <div aria-hidden="true" className="relative">
                <UrnShape className="mx-auto h-48 w-36" />
                <div className="mt-4 flex items-center justify-center gap-2 text-[0.65rem] font-bold uppercase tracking-[0.16em] text-bronze-accent">
                  <Boxes className="h-3.5 w-3.5" aria-hidden="true" />
                  Cao Đỉnh · CAO-DINH-v1.glb
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 6 · Evidence & source credibility */}
      <section className="mt-12" aria-labelledby="evidence-heading">
        <div className="heritage-surface p-6 md:p-8">
          <div className="grid gap-8 lg:grid-cols-[1fr_1.1fr]">
            <div>
              <div id="evidence-heading">
                <SectionHeading
                  kicker="Nguồn sử liệu"
                  title="Mọi nhận định đều gắn với nguồn"
                  lead="Mỗi khẳng định trên nền tảng được nối với một nguồn cụ thể — sách, châu bản, văn khắc hay công trình nghiên cứu. Cách đọc nào chưa được xác nhận đều được dán nhãn rõ ràng, để bạn tự đánh giá."
                />
              </div>
              <div className="mt-5">
                <VerificationNote compact />
              </div>
              <div className="mt-5">
                <PrimaryLink href="/sources">
                  <Library className="h-4 w-4" aria-hidden="true" />
                  Thư viện nguồn
                </PrimaryLink>
              </div>
            </div>
            <div className="grid content-start gap-3">
              {EPISTEMIC_CONCEPTS.map((item) => (
                <article
                  key={item.info.label}
                  className="flex flex-col gap-2.5 rounded-lg border border-border/70 bg-card/60 p-5"
                >
                  <EpistemicLabel info={item.info} className="self-start" />
                  <p className="text-sm leading-6 text-muted-foreground">
                    {item.text}
                  </p>
                </article>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* 7 · Contextual History Tutor preview */}
      <section className="mt-12" aria-labelledby="tutor-heading">
        <div className="focus-card p-6 md:p-8">
          <div className="grid gap-6 md:grid-cols-[auto_1fr_auto] md:items-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-lg border border-bronze-accent/25 bg-bronze-accent/10 text-bronze-accent">
              <Bot className="h-6 w-6" aria-hidden="true" />
            </span>
            <div>
              <div id="tutor-heading">
                <SectionHeading
                  as="h3"
                  kicker="Trợ giảng lịch sử"
                  title="Hỏi về Cửu Đỉnh, trả lời có nguồn"
                  lead="Trợ giảng AI trả lời dựa trên kho nguồn sử liệu của nền tảng, kèm trích dẫn để bạn tự kiểm chứng — không phải trả lời chung chung."
                />
              </div>
            </div>
            <div className="flex md:justify-end">
              <SecondaryLink href="/ai" icon={Sparkles}>
                Mở trợ giảng lịch sử
              </SecondaryLink>
            </div>
          </div>
        </div>
      </section>

      {/* 8 · Optional learning layer CTA */}
      <section className="mt-12" aria-labelledby="learn-heading">
        <div className="heritage-hero flex flex-col items-center gap-5 p-6 text-center md:p-9">
          <h2
            id="learn-heading"
            className="font-display text-2xl font-bold tracking-tight text-foreground md:text-3xl"
          >
            Bắt đầu học Cửu Đỉnh
          </h2>
          <p className="max-w-2xl text-sm leading-7 text-muted-foreground md:text-base">
            Sau khi đọc hiểu một phù điêu, củng cố bằng bài tập ngắn. Tài khoản
            miễn phí giúp bạn lưu tiến độ và bộ sưu tập của riêng mình.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <PrimaryLink href="/practice">
              <Compass className="h-4 w-4" aria-hidden="true" />
              Vào luyện tập
            </PrimaryLink>
            <SecondaryLink
              href={isAuthed ? "/dashboard" : "/login"}
              icon={UserRound}
            >
              {isAuthed ? "Vào bảng học tập" : "Tạo tài khoản / Đăng nhập"}
            </SecondaryLink>
          </div>
        </div>
      </section>
    </main>
  );
}