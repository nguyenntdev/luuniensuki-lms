"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Compass,
  Users,
  Sparkles,
  GraduationCap,
  Info,
  ShieldCheck,
  BookOpen,
  Award,
  ExternalLink,
  Mail,
  HeartHandshake,
  CheckCircle2,
  FileText,
  Building2,
  Layers,
} from "lucide-react";
import { getRbpcCopy, type RbpcLocale } from "@/lib/rbpc/copy";
import { isShellRoute } from "@/lib/shellRoutes";
import { cn } from "@/lib/utils";

export interface RbpcFooterProps {
  currentLocale?: RbpcLocale;
  className?: string;
}

export default function RbpcFooter({
  currentLocale: initialLocale,
  className,
}: RbpcFooterProps) {
  const pathname = usePathname();
  const [locale, setLocale] = useState<RbpcLocale>(initialLocale || "vi");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = window.localStorage.getItem("rbpc_locale") as RbpcLocale | null;
    if (stored === "vi" || stored === "en") {
      setLocale(stored);
    }

    const onLocaleChange = (e: Event) => {
      const customEvent = e as CustomEvent<RbpcLocale>;
      if (customEvent.detail) {
        setLocale(customEvent.detail);
      }
    };

    window.addEventListener("rbpc_locale_changed", onLocaleChange);
    return () => window.removeEventListener("rbpc_locale_changed", onLocaleChange);
  }, []);

  if (!isShellRoute(pathname)) {
    return null;
  }

  const copy = getRbpcCopy(locale);

  return (
    <footer
      className={cn(
        "border-t border-border/80 bg-paper/60 dark:bg-card/40 transition-colors",
        className
      )}
      aria-label="Chân trang LƯU NIÊN"
    >
      <div className="mx-auto w-full max-w-[94rem] px-4 py-16 sm:px-6 lg:px-8">
        {/* Top Section: Brand Statement & Primary Pillars */}
        <div className="grid gap-12 lg:grid-cols-12">
          {/* Brand & Editorial Mission (5 Cols) */}
          <div className="lg:col-span-5">
            <Link
              href="/"
              className="inline-flex items-center gap-3 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              aria-label={`${copy.brand.name} — Trang chủ`}
            >
              <span className="flex h-10 w-10 items-center justify-center rounded-xl border border-primary/30 bg-primary/10 font-serif text-lg font-bold text-primary shadow-xs">
                LN
              </span>
              <div className="flex flex-col leading-tight">
                <span className="font-serif text-xl font-bold tracking-wide text-foreground">
                  {copy.brand.name}
                </span>
                <span className="text-[11px] font-semibold tracking-widest text-primary uppercase">
                  {locale === "vi" ? "CẦU NỐI DI SẢN SỐNG" : "THE LIVING HERITAGE BRIDGE"}
                </span>
              </div>
            </Link>

            {/* Working Strapline */}
            <p className="mt-4 font-serif text-base italic text-foreground/90 sm:text-lg">
              &ldquo;{copy.brand.strapline}&rdquo;
            </p>

            {/* Subheadline & Mission */}
            <p className="mt-3 max-w-lg text-sm leading-relaxed text-muted-foreground">
              {copy.brand.subheadline}
            </p>

            {/* Quick Epistemic Pill Rail */}
            <div className="mt-6 flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-xs font-medium text-primary">
                <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
                <span>
                  {locale === "vi" ? "100% Khảo cứu có nguồn" : "100% Source-Backed"}
                </span>
              </span>
              <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-700/20 bg-amber-500/5 px-3 py-1 text-xs font-medium text-amber-800 dark:text-amber-400">
                <HeartHandshake className="h-3.5 w-3.5" aria-hidden="true" />
                <span>
                  {locale === "vi" ? "Đồng thuận nghệ nhân" : "Artisan Consented"}
                </span>
              </span>
              <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-700/20 bg-emerald-500/5 px-3 py-1 text-xs font-medium text-emerald-800 dark:text-emerald-400">
                <Award className="h-3.5 w-3.5" aria-hidden="true" />
                <span>
                  {locale === "vi" ? "UNESCO Ref. 678" : "UNESCO Inscribed Ref 678"}
                </span>
              </span>
            </div>
          </div>

          {/* Navigation Columns (7 Cols) */}
          <div className="grid grid-cols-2 gap-8 sm:grid-cols-3 lg:col-span-7">
            {/* Column 1: Khám phá & Di sản */}
            <div>
              <h2 className="text-xs font-bold tracking-widest text-foreground uppercase">
                {locale === "vi" ? "Khám phá di sản" : "Explore Heritage"}
              </h2>
              <ul className="mt-4 space-y-2.5 text-sm">
                <li>
                  <Link
                    href="/explore"
                    className="text-muted-foreground transition-colors hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    {locale === "vi" ? "Danh mục toàn diện" : "Full Catalogue"}
                  </Link>
                </li>
                <li>
                  <Link
                    href="/explore?category=imperial_architecture"
                    className="text-muted-foreground transition-colors hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    {locale === "vi" ? "Kiến trúc Cung đình" : "Imperial Architecture"}
                  </Link>
                </li>
                <li>
                  <Link
                    href="/explore?category=royal_tomb"
                    className="text-muted-foreground transition-colors hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    {locale === "vi" ? "Lăng tẩm Hoàng gia" : "Royal Tombs"}
                  </Link>
                </li>
                <li>
                  <Link
                    href="/explore?category=craft_living_culture"
                    className="text-muted-foreground transition-colors hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    {locale === "vi" ? "Làng nghề di sản sống" : "Living Craft Villages"}
                  </Link>
                </li>
                <li>
                  <Link
                    href="/cuu-dinh"
                    className="text-muted-foreground transition-colors hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    {locale === "vi" ? "Cửu Đỉnh & 162 Phù điêu" : "Nine Dynastic Urns"}
                  </Link>
                </li>
                <li>
                  <Link
                    href="/explore?view=map"
                    className="text-muted-foreground transition-colors hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    {locale === "vi" ? "Bản đồ di tích tương tác" : "Interactive Heritage Map"}
                  </Link>
                </li>
              </ul>
            </div>

            {/* Column 2: Nghệ nhân & Trải nghiệm */}
            <div>
              <h2 className="text-xs font-bold tracking-widest text-foreground uppercase">
                {locale === "vi" ? "Nghệ nhân & Trải nghiệm" : "Makers & Experience"}
              </h2>
              <ul className="mt-4 space-y-2.5 text-sm">
                <li>
                  <Link
                    href="/people"
                    className="text-muted-foreground transition-colors hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    {locale === "vi" ? "Gặp người làm nghề" : "Meet the Makers"}
                  </Link>
                </li>
                <li>
                  <Link
                    href="/experiences"
                    className="text-muted-foreground transition-colors hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    {locale === "vi" ? "Workshop văn hóa thực tế" : "Cultural Workshops"}
                  </Link>
                </li>
                <li>
                  <Link
                    href="/partner-inbox"
                    className="text-muted-foreground transition-colors hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    {locale === "vi" ? "Hộp thư điều phối đối tác" : "Partner Inbox"}
                  </Link>
                </li>
                <li>
                  <Link
                    href="/about#how-it-works"
                    className="text-muted-foreground transition-colors hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    {locale === "vi" ? "Cách thức hoạt động" : "How It Works"}
                  </Link>
                </li>
                <li>
                  <Link
                    href="/about#consent"
                    className="text-muted-foreground transition-colors hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    {locale === "vi" ? "Văn bản đồng thuận nghệ nhân" : "Artisan Consent Policy"}
                  </Link>
                </li>
              </ul>
            </div>

            {/* Column 3: Học tập & Minh bạch */}
            <div className="col-span-2 sm:col-span-1">
              <h2 className="text-xs font-bold tracking-widest text-foreground uppercase">
                {locale === "vi" ? "Học tập & Minh bạch" : "Learn & Trust"}
              </h2>
              <ul className="mt-4 space-y-2.5 text-sm">
                <li>
                  <Link
                    href="/learn"
                    className="text-muted-foreground transition-colors hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    {locale === "vi" ? "Góc học tập & Lộ trình" : "Learning Pathways"}
                  </Link>
                </li>
                <li>
                  <Link
                    href="/sources"
                    className="text-muted-foreground transition-colors hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    {locale === "vi" ? "Thư mục nguồn sử liệu" : "Archival Sources"}
                  </Link>
                </li>
                <li>
                  <Link
                    href="/about"
                    className="text-muted-foreground transition-colors hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    {locale === "vi" ? "Về dự án LƯU NIÊN" : "About Project"}
                  </Link>
                </li>
                <li>
                  <Link
                    href="/about#epistemic"
                    className="text-muted-foreground transition-colors hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    {locale === "vi" ? "Khung thang đo độ xác thực" : "Epistemic Framework"}
                  </Link>
                </li>
                <li>
                  <Link
                    href="/about#privacy"
                    className="text-muted-foreground transition-colors hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    {locale === "vi" ? "Cam kết bảo vệ dữ liệu" : "Data Privacy Pledge"}
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Middle Section: UNESCO Attribution & RBPC Provenance Notice */}
        <div className="mt-12 grid gap-6 rounded-2xl border border-border/80 bg-background/60 p-6 sm:p-8 lg:grid-cols-3">
          {/* Card 1: UNESCO World Heritage Attribution */}
          <div className="flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 text-primary font-serif font-bold text-sm">
                <Award className="h-4 w-4 shrink-0" aria-hidden="true" />
                <span>
                  {locale === "vi"
                    ? "Đối chiếu Di sản UNESCO (Mã số 678)"
                    : "UNESCO World Heritage Attribution (Ref. 678)"}
                </span>
              </div>
              <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                {copy.brand.unescoDisclaimer}
              </p>
            </div>
            <a
              href="https://whc.unesco.org/en/list/678"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 inline-flex items-center gap-1.5 text-xs font-semibold text-primary hover:underline"
            >
              <span>{locale === "vi" ? "Xem hồ sơ UNESCO chính thức" : "View Official UNESCO Dossier"}</span>
              <ExternalLink className="h-3 w-3" aria-hidden="true" />
            </a>
          </div>

          {/* Card 2: Academic Citation & Epistemic Honesty */}
          <div className="flex flex-col justify-between border-t border-border/60 pt-6 lg:border-t-0 lg:border-l lg:pt-0 lg:pl-6">
            <div>
              <div className="flex items-center gap-2 text-foreground font-serif font-bold text-sm">
                <BookOpen className="h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
                <span>
                  {locale === "vi" ? "Chính sách trích dẫn sử liệu" : "Citation & Academic Policy"}
                </span>
              </div>
              <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                {copy.brand.citationPolicy}
              </p>
            </div>
            <Link
              href="/sources"
              className="mt-4 inline-flex items-center gap-1.5 text-xs font-semibold text-primary hover:underline"
            >
              <span>{locale === "vi" ? "Tra cứu danh mục thư tịch" : "Browse Bibliographic Archive"}</span>
              <ExternalLink className="h-3 w-3" aria-hidden="true" />
            </Link>
          </div>

          {/* Card 3: RBPC 2026 Provenance & Ethics */}
          <div className="flex flex-col justify-between border-t border-border/60 pt-6 lg:border-t-0 lg:border-l lg:pt-0 lg:pl-6">
            <div>
              <div className="flex items-center gap-2 text-foreground font-serif font-bold text-sm">
                <Building2 className="h-4 w-4 shrink-0 text-amber-700 dark:text-amber-400" aria-hidden="true" />
                <span>
                  {locale === "vi"
                    ? "Sáng kiến dự thi RBPC 2026"
                    : "RMIT Business Plan Competition 2026"}
                </span>
              </div>
              <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                {locale === "vi"
                  ? "Dự án LƯU NIÊN tham dự RMIT Business Plan Competition 2026 với chủ đề 'AI and Humanity: Building What's Next'. Sáng kiến phi thương mại kết nối tư liệu lịch sử có nguồn với con người thực hành di sản sống."
                  : "Developed for RMIT Business Plan Competition 2026 under 'AI and Humanity: Building What's Next'. A non-commercial initiative bridging verified scholarship with living heritage practitioners."}
              </p>
            </div>
            <div className="mt-4 text-[11px] text-muted-foreground/80">
              {locale === "vi"
                ? "Không mô phỏng thanh toán tức thì · Không lưu trữ cookie theo dõi"
                : "No instant checkout simulation · Zero behavioral tracking cookies"}
            </div>
          </div>
        </div>

        {/* Partner Organizations & Institutional Links */}
        <div className="mt-10 flex flex-wrap items-center justify-between gap-4 border-t border-border/60 pt-6 text-xs text-muted-foreground">
          <div className="flex flex-wrap items-center gap-4 sm:gap-6">
            <span className="font-semibold text-foreground">
              {locale === "vi" ? "Tổ chức & Đối tác tham khảo:" : "Institutional References & Partners:"}
            </span>
            <a
              href="http://hueworldheritage.org.vn"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-foreground hover:underline"
            >
              Trung tâm BTDT Cố đô Huế (HMCC)
            </a>
            <a
              href="http://vicas.org.vn"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-foreground hover:underline"
            >
              Viện VHNT Quốc gia Việt Nam (VICAS)
            </a>
            <a
              href="https://whc.unesco.org"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-foreground hover:underline"
            >
              UNESCO WHC
            </a>
            <a
              href="https://www.rmit.edu.vn"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-foreground hover:underline"
            >
              RMIT Vietnam
            </a>
          </div>

          <div className="flex items-center gap-2">
            <Mail className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
            <a
              href="mailto:contact@histolab.icu"
              className="font-mono text-xs hover:text-foreground hover:underline"
            >
              contact@histolab.icu
            </a>
          </div>
        </div>

        {/* Bottom Bar: Copyright & Epistemic Statement */}
        <div className="mt-8 flex flex-col gap-3 border-t border-border/80 pt-6 sm:flex-row sm:items-center sm:justify-between text-xs text-muted-foreground">
          <p>
            © 2026 {copy.brand.name} Team.{" "}
            {locale === "vi"
              ? "Bản quyền nội dung nghiên cứu và bảo tồn di sản."
              : "All rights reserved. Living heritage research and cultural preservation."}
          </p>

          <p className="max-w-md text-right text-[11px] text-muted-foreground/80">
            {locale === "vi"
              ? "Mọi chân dung nghệ nhân và câu chuyện xưởng nghề được công bố dựa trên văn bản đồng thuận có chữ ký."
              : "All artisan portraits and workshop narratives are published strictly upon signed, written consent."}
          </p>
        </div>
      </div>
    </footer>
  );
}
