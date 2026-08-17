"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  ArrowRight,
  BookOpen,
  Compass,
  Landmark,
  Library,
  Map as MapIcon,
  ScrollText,
  Sparkles,
  UserRound,
} from "lucide-react";

import { useAuthStore } from "@/stores/authStore";
import { listHistoryEntities } from "@/lib/api";
import { asEntityList, listTotal } from "@/lib/history";
import Skeleton from "@/components/Skeleton";
import EntityCard from "@/components/history/EntityCard";
import SectionHeading from "@/components/history/SectionHeading";
import VerificationNote from "@/components/history/VerificationNote";

function PrimaryLink({ href, children }) {
  return (
    <Link
      href={href}
      className="inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
    >
      {children}
    </Link>
  );
}

function SecondaryLink({ href, icon: Icon, children }) {
  return (
    <Link
      href={href}
      className="inline-flex items-center justify-center gap-2 rounded-lg border border-border bg-secondary/60 px-5 py-2.5 text-sm font-semibold text-foreground transition hover:border-primary/40 hover:bg-secondary"
    >
      <Icon className="h-4 w-4 text-primary" aria-hidden="true" />
      {children}
    </Link>
  );
}

function HeroStat({ value, label }) {
  return (
    <div className="heritage-stat px-3 py-3">
      <div className="font-display text-xl font-semibold text-foreground">
        {value}
      </div>
      <div className="mt-0.5 text-xs text-muted-foreground">{label}</div>
    </div>
  );
}

function TeaserSection({ icon: Icon, title, lead, href, cta }) {
  return (
    <Link
      href={href}
      className="heritage-surface group flex flex-col gap-4 p-6 transition duration-200 hover:border-primary/40 focus-visible:ring-2 focus-visible:ring-primary md:p-7"
    >
      <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-primary/15 text-primary">
        <Icon className="h-6 w-6" aria-hidden="true" />
      </span>
      <div>
        <h3 className="font-display text-lg font-semibold text-foreground">
          {title}
        </h3>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">{lead}</p>
      </div>
      <span className="inline-flex items-center gap-1.5 text-sm font-medium text-primary">
        {cta}
        <ArrowRight
          className="h-4 w-4 transition group-hover:translate-x-0.5"
          aria-hidden="true"
        />
      </span>
    </Link>
  );
}

export default function HomePage() {
  const status = useAuthStore((s) => s.status);
  const [mounted, setMounted] = useState(false);
  const [urns, setUrns] = useState([]);
  const [reliefTotal, setReliefTotal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    document.title =
      "Lưu Niên Sử Kí — Cửu Đỉnh, bách khoa thư bằng đồng của triều Nguyễn";
  }, [mounted]);

  useEffect(() => {
    if (!mounted) return;
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [urnRes, reliefRes] = await Promise.all([
          listHistoryEntities({ entityType: "urn", limit: 20 }),
          listHistoryEntities({ entityType: "relief", limit: 1 }),
        ]);
        if (cancelled) return;
        setUrns(asEntityList(urnRes));
        const total = listTotal(reliefRes);
        setReliefTotal(total ?? asEntityList(reliefRes).length);
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
  }, [mounted]);

  if (!mounted) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <div className="text-muted-foreground">Đang tải...</div>
      </main>
    );
  }

  const isAuthed = status === "authed";

  return (
    <main className="site-shell">
      {/* (a) Hero */}
      <section className="heritage-hero p-6 md:p-10">
        <div className="relative">
          <div className="heritage-chip">
            <Sparkles className="h-4 w-4" aria-hidden="true" />
            Di sản triều Nguyễn · đúc 1835–1837
          </div>
          <h1 className="mt-5 font-display text-4xl font-bold tracking-tight text-foreground md:text-6xl">
            Cửu Đỉnh
          </h1>
          <p className="mt-3 font-display text-xl font-semibold text-gradient-bronze md:text-2xl">
            Bách khoa thư bằng đồng của một vương triều
          </p>
          <p className="mt-5 max-w-2xl text-base leading-7 text-muted-foreground md:text-lg">
            Chín chiếc đỉnh đồng đặt tại Thế Miếu trong Hoàng thành Huế, đúc dưới
            triều Minh Mạng, khắc nổi 162 hình tượng về đất nước: núi sông, muôn
            thú, cây cỏ, vũ khí và biển đảo. Lưu Niên Sử Kí là nơi tra cứu và học
            di sản này — mở cho tất cả mọi người, không cần đăng nhập.
          </p>

          <div className="mt-7 flex flex-wrap gap-3">
            <PrimaryLink href="/atlas">
              Khám phá 162 hình đúc
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </PrimaryLink>
            <SecondaryLink href="/cuu-dinh" icon={Landmark}>
              Xem Cửu Đỉnh 3D
            </SecondaryLink>
            <SecondaryLink
              href={isAuthed ? "/practice" : "/login"}
              icon={isAuthed ? BookOpen : UserRound}
            >
              {isAuthed ? "Bắt đầu học" : "Bắt đầu học / Đăng nhập"}
            </SecondaryLink>
          </div>

          <div className="mt-8 grid max-w-lg grid-cols-3 gap-2 text-xs">
            <HeroStat value={urns.length || "…"} label="đỉnh đồng" />
            <HeroStat
              value={reliefTotal ?? "…"}
              label="hình đúc (từ dữ liệu)"
            />
            <HeroStat value="Huế" label="Thế Miếu · Hoàng thành" />
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
          Không tải được dữ liệu lịch sử: {error}
        </div>
      ) : null}

      {/* (b) Interactive overview of the Nine Urns */}
      <section className="mt-10">
        <SectionHeading
          kicker="Chín chiếc đỉnh"
          title="Chín chiếc đỉnh, chín câu chuyện về đất nước"
          lead="Mỗi chiếc đỉnh mang một nhóm hình tượng riêng. Chọn một đỉnh để xem chi tiết và các phù điêu của nó."
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

      {/* (c) Atlas entry */}
      <section className="mt-10" aria-labelledby="atlas-heading">
        <div className="heritage-surface p-6 md:p-8">
          <div className="relative grid gap-6 lg:grid-cols-[1fr_auto]">
            <div className="max-w-3xl">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-primary">
                Atlas
              </p>
              <h2
                id="atlas-heading"
                className="mt-3 font-display text-2xl font-bold tracking-tight text-foreground md:text-3xl"
              >
                162 hình đúc — bộ sưu tập toàn bộ phù điêu
              </h2>
              <p className="mt-3 text-sm leading-7 text-muted-foreground md:text-base">
                Duyệt, tìm kiếm và lọc toàn bộ các hình tượng khắc nổi trên chín
                chiếc đỉnh theo đỉnh, trạng thái xuất bản và tên gọi.
              </p>
            </div>
            <div className="flex items-center lg:flex-col lg:justify-center">
              <PrimaryLink href="/atlas">
                Mở Atlas
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </PrimaryLink>
            </div>
          </div>
        </div>
      </section>

      {/* (d) Geographic teaser + (e) Timeline teaser */}
      <section className="mt-5 grid gap-4 lg:grid-cols-2">
        <TeaserSection
          icon={MapIcon}
          title="Địa lý trên đỉnh đồng"
          lead="Từ dãy Trường Sơn đến biển đảo phía Đông — những địa danh được chọn khắc lên đỉnh nói lên cách vương triều hình dung lãnh thổ."
          href="/map"
          cta="Xem bản đồ"
        />
        <TeaserSection
          icon={ScrollText}
          title="Dòng thời gian"
          lead="Bối cảnh triều Nguyễn từ 1802 đến 1945: những sự kiện, con người và hoàn cảnh quanh việc đúc Cửu Đỉnh."
          href="/timeline"
          cta="Theo dòng thời gian"
        />
      </section>

      {/* (f) Sources / credibility */}
      <section className="mt-5">
        <div className="heritage-surface p-6 md:p-8">
          <div className="relative grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="max-w-3xl">
              <SectionHeading
                kicker="Nguồn sử liệu"
                title="Mọi nhận định đều gắn với nguồn"
                lead="Thư viện nguồn công khai liệt kê các sách, châu bản, văn khắc và công trình nghiên cứu được dùng để viết nội dung. Các diễn giải chưa được xác nhận luôn được dán nhãn rõ ràng."
              />
              <div className="mt-5">
                <PrimaryLink href="/sources">
                  <Library className="h-4 w-4" aria-hidden="true" />
                  Thư viện nguồn
                </PrimaryLink>
              </div>
            </div>
            <div className="flex items-start">
              <VerificationNote compact />
            </div>
          </div>
        </div>
      </section>

      {/* (g) Learning CTA */}
      <section className="mt-5">
        <div className="heritage-hero flex flex-col items-center gap-5 p-6 text-center md:p-9">
          <h2 className="font-display text-2xl font-bold tracking-tight text-foreground md:text-3xl">
            Học sâu hơn với bài tập và trắc nghiệm
          </h2>
          <p className="max-w-2xl text-sm leading-7 text-muted-foreground md:text-base">
            Sau khi đọc hiểu một phù điêu, hãy củng cố bằng bài tập ngắn. Tài
            khoản miễn phí giúp bạn lưu tiến độ và bộ sưu tập của riêng mình.
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