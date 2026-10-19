"use client";

import React, { useState, useEffect, useCallback, useId } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Compass,
  Users,
  Sparkles,
  GraduationCap,
  Info,
  Menu,
  X,
  Globe,
  Search,
  LogIn,
  Layers,
  MapPin,
  ChevronRight,
  BookOpen,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { getRbpcCopy, type RbpcLocale } from "@/lib/rbpc/copy";
import { useAuthStore } from "@/stores/authStore";
import { isShellRoute } from "@/lib/shellRoutes";
import { cn } from "@/lib/utils";

/**
 * 5-Link Navigation Item Definition
 * Conforms strictly to Master Spec & Wireframe:
 * 1. Khám phá (/explore)
 * 2. Nghệ nhân (/people)
 * 3. Trải nghiệm (/experiences)
 * 4. Học tập (/learn)
 * 5. Về dự án (/about)
 */
export interface RbpcNavItem {
  id: string;
  href: string;
  labelVi: string;
  labelEn: string;
  icon: LucideIcon;
  descriptionVi: string;
  descriptionEn: string;
}

export const RBPC_NAV_ITEMS: RbpcNavItem[] = [
  {
    id: "explore",
    href: "/explore",
    labelVi: "Khám phá",
    labelEn: "Discover",
    icon: Compass,
    descriptionVi: "14 cấu phần di sản UNESCO & danh thắng Cố đô Huế",
    descriptionEn: "14 UNESCO World Heritage components & historic sites",
  },
  {
    id: "people",
    href: "/people",
    labelVi: "Nghệ nhân",
    labelEn: "Makers",
    icon: Users,
    descriptionVi: "Nghệ nhân làng nghề & người gìn giữ di sản sống",
    descriptionEn: "Living master artisans & cultural tradition bearers",
  },
  {
    id: "experiences",
    href: "/experiences",
    labelVi: "Trải nghiệm",
    labelEn: "Experiences",
    icon: Sparkles,
    descriptionVi: "Workshop thủ công & kết nối thực địa cùng xưởng nghề",
    descriptionEn: "Curated craft workshops & authentic artisan encounters",
  },
  {
    id: "learn",
    href: "/learn",
    labelVi: "Học tập",
    labelEn: "Learn",
    icon: GraduationCap,
    descriptionVi: "Góc học tập & lộ trình khảo cứu có dẫn chứng sử liệu",
    descriptionEn: "Pedagogical pathways & source-grounded learning modules",
  },
  {
    id: "about",
    href: "/about",
    labelVi: "Về dự án",
    labelEn: "About",
    icon: Info,
    descriptionVi: "Phương pháp nghiên cứu, đạo đức dữ liệu & đội ngũ RBPC 2026",
    descriptionEn: "Methodology, epistemic ethics & competition team",
  },
];

export interface RbpcHeaderProps {
  currentLocale?: RbpcLocale;
  onLocaleChange?: (next: RbpcLocale) => void;
  className?: string;
}

export default function RbpcHeader({
  currentLocale: initialLocale,
  onLocaleChange,
  className,
}: RbpcHeaderProps) {
  const pathname = usePathname();
  const authStatus = useAuthStore((s) => s.status);
  const isAuthed = authStatus === "authed";

  const [locale, setLocale] = useState<RbpcLocale>(initialLocale || "vi");
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const drawerId = useId();

  // Sync locale with localStorage & document cookies
  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = window.localStorage.getItem("rbpc_locale") as RbpcLocale | null;
    if (stored === "vi" || stored === "en") {
      setLocale(stored);
    }
  }, []);

  const handleSwitchLocale = useCallback(
    (targetLocale: RbpcLocale) => {
      setLocale(targetLocale);
      if (typeof window !== "undefined") {
        window.localStorage.setItem("rbpc_locale", targetLocale);
        document.cookie = `NEXT_LOCALE=${targetLocale}; path=/; max-age=31536000; SameSite=Lax`;
        window.dispatchEvent(
          new CustomEvent("rbpc_locale_changed", { detail: targetLocale })
        );
      }
      onLocaleChange?.(targetLocale);
    },
    [onLocaleChange]
  );

  const toggleLanguage = useCallback(() => {
    const nextLocale: RbpcLocale = locale === "vi" ? "en" : "vi";
    handleSwitchLocale(nextLocale);
  }, [locale, handleSwitchLocale]);

  // Lock body scroll when mobile drawer is open
  useEffect(() => {
    if (typeof document === "undefined") return;
    if (isDrawerOpen) {
      const originalStyle = window.getComputedStyle(document.body).overflow;
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = originalStyle;
      };
    }
  }, [isDrawerOpen]);

  // Close drawer on path change
  useEffect(() => {
    setIsDrawerOpen(false);
  }, [pathname]);

  // Close drawer on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isDrawerOpen) {
        setIsDrawerOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isDrawerOpen]);

  if (!isShellRoute(pathname)) {
    return null;
  }

  const copy = getRbpcCopy(locale);

  const isRouteActive = (href: string) => {
    if (!pathname) return false;
    if (href === "/") return pathname === "/";
    return pathname === href || pathname.startsWith(`${href}/`);
  };

  return (
    <>
      {/* Skip Link for Keyboard Accessibility (WCAG 2.4.1) */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-primary-foreground focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-ring"
      >
        {copy.nav.skipToContent}
      </a>

      {/* Main Sticky Header (Zero heavy backdrop-blur) */}
      <header
        className={cn(
          "sticky top-0 z-40 w-full border-b border-border/80 bg-background/98 transition-colors",
          className
        )}
      >
        <div className="pt-[env(safe-area-inset-top)]">
          <div className="mx-auto flex h-14 w-full max-w-[94rem] items-center justify-between gap-3 px-4 sm:px-6 lg:px-8">
            {/* Brand Display: LƯU NIÊN with Strapline */}
            <div className="flex shrink-0 items-center gap-3">
              <Link
                href="/"
                className="group flex items-center gap-2.5 rounded-lg py-1 pr-2 transition-opacity focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                aria-label={`${copy.brand.name} — ${copy.brand.heroExplanation}`}
              >
                {/* Brand Monogram Badge */}
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-primary/30 bg-primary/10 font-serif text-base font-bold text-primary shadow-sm transition-transform group-hover:scale-105">
                  LN
                </span>

                {/* Brand Title & Strapline */}
                <div className="flex flex-col leading-tight">
                  <span className="font-serif text-base font-bold tracking-[0.03em] text-foreground sm:text-lg">
                    {copy.brand.name}
                  </span>
                  <span className="text-[10px] font-semibold tracking-[0.14em] text-primary uppercase">
                    {locale === "vi" ? "DI SẢN SỐNG" : "LIVING HERITAGE"}
                  </span>
                </div>
              </Link>
            </div>

            {/* Desktop Unified 5-Link Navigation (≥1024px) */}
            <nav
              aria-label="Điều hướng chính LƯU NIÊN"
              className="hidden lg:flex min-w-0 flex-1 items-center justify-center gap-1 xl:gap-2"
            >
              {RBPC_NAV_ITEMS.map((item) => {
                const active = isRouteActive(item.href);
                const label = locale === "vi" ? item.labelVi : item.labelEn;
                const Icon = item.icon;

                return (
                  <Link
                    key={item.id}
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "group relative flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
                      active
                        ? "bg-primary/10 text-primary font-semibold"
                        : "text-muted-foreground hover:bg-secondary/70 hover:text-foreground"
                    )}
                  >
                    <Icon
                      className={cn(
                        "h-4 w-4 transition-colors",
                        active ? "text-primary" : "text-muted-foreground/80 group-hover:text-foreground"
                      )}
                      aria-hidden="true"
                    />
                    <span>{label}</span>
                    {active && (
                      <span className="absolute bottom-0 left-3 right-3 h-0.5 rounded-full bg-primary" />
                    )}
                  </Link>
                );
              })}
            </nav>

            {/* Desktop Right Actions: Search, Language Switcher, Account */}
            <div className="hidden lg:flex shrink-0 items-center gap-2">
              {/* Search Trigger */}
              <Link
                href="/explore?focus=search"
                className="inline-flex h-9 items-center gap-2 rounded-lg border border-border/80 bg-background/80 px-3 text-xs text-muted-foreground transition-colors hover:border-border hover:bg-secondary/60 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                aria-label={locale === "vi" ? "Tìm kiếm di sản Cố đô Huế" : "Search Huế heritage"}
              >
                <Search className="h-3.5 w-3.5" aria-hidden="true" />
                <span className="hidden xl:inline">
                  {locale === "vi" ? "Tìm kiếm..." : "Search..."}
                </span>
                <kbd className="hidden xl:inline rounded border border-border/60 bg-muted/60 px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                  ⌘K
                </kbd>
              </Link>

              {/* Language Switcher Button (VI / EN) */}
              <button
                type="button"
                onClick={toggleLanguage}
                className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-border/80 bg-background/80 px-2.5 text-xs font-medium text-foreground transition-colors hover:bg-secondary/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                aria-label={
                  locale === "vi"
                    ? "Chuyển sang Tiếng Anh (English)"
                    : "Switch to Vietnamese (Tiếng Việt)"
                }
              >
                <Globe className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
                <span className="font-semibold">{locale === "vi" ? "VI" : "EN"}</span>
                <span className="text-[10px] text-muted-foreground">
                  / {locale === "vi" ? "EN" : "VI"}
                </span>
              </button>

              {/* Auth / Action CTA (Single Unambiguous Action) */}
              {isAuthed ? (
                <Link
                  href="/dashboard"
                  className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-primary/30 bg-primary/10 px-3 text-xs font-semibold text-primary transition-colors hover:bg-primary/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                >
                  <BookOpen className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>{locale === "vi" ? "Học của tôi" : "My Learning"}</span>
                </Link>
              ) : (
                <Link
                  href="/login"
                  className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-primary px-3 text-xs font-semibold text-primary-foreground shadow-sm transition-colors hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                >
                  <LogIn className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>{locale === "vi" ? "Đăng nhập" : "Sign In"}</span>
                </Link>
              )}
            </div>

            {/* Mobile / Tablet Actions: Search + Menu Trigger (<1024px) */}
            <div className="flex lg:hidden items-center gap-1.5">
              {/* Quick Search Button */}
              <Link
                href="/explore?focus=search"
                className="inline-flex h-10 w-10 items-center justify-center rounded-lg text-muted-foreground hover:bg-secondary/70 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                aria-label={locale === "vi" ? "Tìm kiếm di sản" : "Search heritage"}
              >
                <Search className="h-5 w-5" aria-hidden="true" />
              </Link>

              {/* Quick Language Toggle */}
              <button
                type="button"
                onClick={toggleLanguage}
                className="inline-flex h-10 px-2.5 items-center justify-center rounded-lg border border-border/80 text-xs font-semibold text-foreground hover:bg-secondary/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                aria-label={
                  locale === "vi"
                    ? "Chuyển sang Tiếng Anh (English)"
                    : "Switch to Vietnamese (Tiếng Việt)"
                }
              >
                {locale.toUpperCase()}
              </button>

              {/* Hamburger Toggle Button (Min 44x44px touch target) */}
              <button
                type="button"
                onClick={() => setIsDrawerOpen((prev) => !prev)}
                aria-expanded={isDrawerOpen}
                aria-controls={drawerId}
                aria-label={isDrawerOpen ? copy.nav.closeMenu : copy.nav.menuToggle}
                className="inline-flex min-h-[44px] min-w-[44px] items-center justify-center rounded-lg text-foreground hover:bg-secondary/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              >
                {isDrawerOpen ? (
                  <X className="h-6 w-6 text-foreground" aria-hidden="true" />
                ) : (
                  <Menu className="h-6 w-6 text-foreground" aria-hidden="true" />
                )}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Clean Single Mobile Disclosure Drawer */}
      {isDrawerOpen && (
        <div
          id={drawerId}
          role="dialog"
          aria-modal="true"
          aria-label={copy.brand.fullName}
          className="fixed inset-0 z-50 flex lg:hidden"
        >
          {/* Dim Overlay (Zero heavy backdrop-blur) */}
          <div
            onClick={() => setIsDrawerOpen(false)}
            aria-hidden="true"
            className="fixed inset-0 bg-black/60 transition-opacity"
          />

          {/* Slide-in Panel from Right */}
          <div className="relative ml-auto flex h-full w-full max-w-sm flex-col border-l border-border bg-background shadow-2xl transition-transform">
            {/* Drawer Header */}
            <div className="flex h-16 items-center justify-between border-b border-border px-5">
              <div className="flex items-center gap-2.5">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg border border-primary/30 bg-primary/10 font-serif text-sm font-bold text-primary">
                  LN
                </span>
                <div className="flex flex-col leading-tight">
                  <span className="font-serif text-base font-bold text-foreground">
                    {copy.brand.name}
                  </span>
                  <span className="text-[10px] font-semibold tracking-wider text-primary uppercase">
                    {locale === "vi" ? "DI SẢN SỐNG" : "LIVING HERITAGE"}
                  </span>
                </div>
              </div>

              {/* Drawer Close Button (Min 44x44px touch target) */}
              <button
                type="button"
                onClick={() => setIsDrawerOpen(false)}
                aria-label={copy.nav.closeMenu}
                className="inline-flex min-h-[44px] min-w-[44px] items-center justify-center rounded-lg text-muted-foreground hover:bg-secondary hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              >
                <X className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>

            {/* Drawer Body Scroll Area */}
            <div className="flex-1 overflow-y-auto px-5 py-6">
              {/* Section 1: Unified 5-Link Navigation */}
              <div className="space-y-1">
                <p className="px-2 pb-2 text-[11px] font-semibold tracking-widest text-muted-foreground uppercase">
                  {locale === "vi" ? "Điều hướng chính" : "Main Navigation"}
                </p>

                {RBPC_NAV_ITEMS.map((item) => {
                  const active = isRouteActive(item.href);
                  const label = locale === "vi" ? item.labelVi : item.labelEn;
                  const desc = locale === "vi" ? item.descriptionVi : item.descriptionEn;
                  const Icon = item.icon;

                  return (
                    <Link
                      key={item.id}
                      href={item.href}
                      onClick={() => setIsDrawerOpen(false)}
                      aria-current={active ? "page" : undefined}
                      className={cn(
                        "group flex items-start gap-3 rounded-xl p-3 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
                        active
                          ? "bg-primary/10 text-primary font-semibold"
                          : "text-foreground hover:bg-secondary/60"
                      )}
                    >
                      <span
                        className={cn(
                          "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border transition-colors",
                          active
                            ? "border-primary/40 bg-primary/20 text-primary"
                            : "border-border/60 bg-muted/40 text-muted-foreground group-hover:text-foreground"
                        )}
                      >
                        <Icon className="h-4 w-4" aria-hidden="true" />
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-semibold">{label}</span>
                          <ChevronRight
                            className={cn(
                              "h-4 w-4 transition-transform",
                              active
                                ? "text-primary translate-x-0.5"
                                : "text-muted-foreground/60 group-hover:translate-x-0.5"
                            )}
                            aria-hidden="true"
                          />
                        </div>
                        <p className="text-xs text-muted-foreground line-clamp-1 mt-0.5">
                          {desc}
                        </p>
                      </div>
                    </Link>
                  );
                })}
              </div>

              {/* Section 2: Special Collections & Maps */}
              <div className="mt-6 border-t border-border/80 pt-6 space-y-1">
                <p className="px-2 pb-2 text-[11px] font-semibold tracking-widest text-muted-foreground uppercase">
                  {locale === "vi" ? "Bộ sưu tập đặc biệt" : "Special Collections"}
                </p>

                <Link
                  href="/cuu-dinh"
                  onClick={() => setIsDrawerOpen(false)}
                  className="flex items-center gap-3 rounded-xl p-3 text-foreground transition-colors hover:bg-secondary/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                >
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-border/60 bg-muted/40 text-muted-foreground">
                    <Layers className="h-4 w-4" aria-hidden="true" />
                  </span>
                  <div className="flex-1">
                    <div className="text-sm font-medium">Cửu Đỉnh & 162 Phù điêu</div>
                    <div className="text-xs text-muted-foreground">
                      {locale === "vi" ? "Di sản tư liệu ký ức thế giới" : "UNESCO Memory of the World"}
                    </div>
                  </div>
                </Link>

                <Link
                  href="/explore?view=map"
                  onClick={() => setIsDrawerOpen(false)}
                  className="flex items-center gap-3 rounded-xl p-3 text-foreground transition-colors hover:bg-secondary/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                >
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-border/60 bg-muted/40 text-muted-foreground">
                    <MapPin className="h-4 w-4" aria-hidden="true" />
                  </span>
                  <div className="flex-1">
                    <div className="text-sm font-medium">
                      {locale === "vi" ? "Bản đồ di tích Huế" : "Huế Heritage Map"}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {locale === "vi" ? "Không gian địa lý & toạ độ thực địa" : "Geographic GIS & field points"}
                    </div>
                  </div>
                </Link>
              </div>

              {/* Section 3: Language Preference Selector */}
              <div className="mt-6 border-t border-border/80 pt-6">
                <p className="px-2 pb-3 text-[11px] font-semibold tracking-widest text-muted-foreground uppercase">
                  {locale === "vi" ? "Ngôn ngữ hiển thị" : "Display Language"}
                </p>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => handleSwitchLocale("vi")}
                    className={cn(
                      "flex min-h-[44px] items-center justify-center gap-2 rounded-lg border px-3 py-2 text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
                      locale === "vi"
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-border bg-background text-muted-foreground hover:bg-secondary"
                    )}
                  >
                    <span>Tiếng Việt</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleSwitchLocale("en")}
                    className={cn(
                      "flex min-h-[44px] items-center justify-center gap-2 rounded-lg border px-3 py-2 text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
                      locale === "en"
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-border bg-background text-muted-foreground hover:bg-secondary"
                    )}
                  >
                    <span>English</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Drawer Footer: Auth Action */}
            <div className="border-t border-border bg-muted/30 p-5">
              {isAuthed ? (
                <Link
                  href="/dashboard"
                  onClick={() => setIsDrawerOpen(false)}
                  className="flex min-h-[44px] w-full items-center justify-center gap-2 rounded-xl border border-primary/40 bg-primary/10 px-4 py-2.5 text-sm font-semibold text-primary shadow-xs transition-colors hover:bg-primary/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                >
                  <BookOpen className="h-4 w-4" aria-hidden="true" />
                  <span>{locale === "vi" ? "Vào bàn học của tôi" : "Go to My Dashboard"}</span>
                </Link>
              ) : (
                <div className="flex flex-col gap-2">
                  <Link
                    href="/login"
                    onClick={() => setIsDrawerOpen(false)}
                    className="flex min-h-[44px] w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground shadow-sm transition-colors hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    <LogIn className="h-4 w-4" aria-hidden="true" />
                    <span>{locale === "vi" ? "Đăng nhập tài khoản" : "Sign In to Account"}</span>
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
