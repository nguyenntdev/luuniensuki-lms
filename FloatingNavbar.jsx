"use client";

import { useEffect, useRef, useState } from "react";
import {
  Menu,
  X,
  Globe,
  ChevronDown,
  Eye,
  Trophy,
  BookOpen,
  Sparkles,
  User,
  Map,
  Shield,
  Users,
  Brain,
  Home,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuthStore } from "../stores/authStore";

function cn(...classes) {
  return classes.filter(Boolean).join(" ");
}

const Button = ({ className, size, children, ...props }) => {
  const baseStyles =
    "inline-flex items-center justify-center whitespace-nowrap rounded-full border border-primary/35 text-sm font-semibold ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50";
  const variants = {
    default:
      "bg-gradient-to-br from-primary via-amber-500 to-bronze text-primary-foreground shadow-[0_10px_26px_-18px_hsl(var(--primary)/0.7)] hover:brightness-110",
    sm: "h-9 px-3",
  };

  return (
    <button
      className={cn(
        baseStyles,
        variants.default,
        size === "sm" && variants.sm,
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
};

const languages = [
  { code: "vi", nativeName: "Tiếng Việt" },
  { code: "en", nativeName: "English" },
];

const translations = {
  vi: {
    "nav.dashboard": "Học tập",
    "nav.explore": "Khám phá",
    "nav.quests": "Hành trình",
    "nav.collection": "Bộ sưu tập",
    "nav.practice": "Ôn tập",
    "nav.ai": "AI giáo viên",
    "nav.friends": "Bạn bè",
    "nav.achievements": "Thành tích",
    "nav.profile": "Hồ sơ",
    "nav.admin": "Giáo viên",
    "nav.leaderboard": "Bảng hạng",
    "nav.leagues": "Liên đoàn",
    "nav.menu": "Mục lục",
    "nav.logout": "Đăng xuất",
    "nav.start": "Tiếp tục học",
  },
  en: {
    "nav.dashboard": "Học tập",
    "nav.explore": "Khám phá",
    "nav.quests": "Hành trình",
    "nav.collection": "Bộ sưu tập",
    "nav.practice": "Ôn tập",
    "nav.ai": "AI giáo viên",
    "nav.friends": "Bạn bè",
    "nav.achievements": "Thành tích",
    "nav.profile": "Hồ sơ",
    "nav.admin": "Giáo viên",
    "nav.leaderboard": "Bảng hạng",
    "nav.leagues": "Liên đoàn",
    "nav.menu": "Mục lục",
    "nav.logout": "Đăng xuất",
    "nav.start": "Tiếp tục học",
  },
};

function NavIconLink({ item, onClick, active, compact }) {
  const Icon = item.icon;
  const base = compact
    ? "w-full flex flex-col items-center gap-1 px-2 py-1.5 rounded-2xl transition-all"
    : "inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-full border transition-all";

  const activeClasses = compact
    ? "text-primary border border-primary/50 bg-primary/10 shadow-[0_8px_18px_rgba(0,0,0,0.28)]"
    : "border-primary/45 bg-primary/15 text-primary shadow-[inset_0_1px_0_hsl(43_30%_92%_/_0.08)]";

  const idleClasses = compact
    ? "text-muted-foreground hover:text-primary"
    : "border-transparent text-stone-300/88 hover:border-primary/25 hover:bg-primary/10 hover:text-primary";

  return (
    <Link href={item.link} className={compact ? "flex-1 min-w-0" : "shrink-0"} onClick={onClick}>
      <span className={`${base} ${active ? activeClasses : idleClasses}`}>
        <Icon className={compact ? "h-5 w-5" : "h-4 w-4"} />
        <span className={compact ? "truncate text-[11px] font-medium" : "whitespace-nowrap text-xs font-medium"}>
          {item.label}
        </span>
      </span>
    </Link>
  );
}

export default function FloatingNavbar() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isLangDropdownOpen, setIsLangDropdownOpen] = useState(false);
  const [isUserDropdownOpen, setIsUserDropdownOpen] = useState(false);
  const [isMoreDropdownOpen, setIsMoreDropdownOpen] = useState(false);
  const [lang, setLang] = useState("vi");

  const pathname = usePathname();
  const isAuthPage = pathname === "/login" || pathname === "/register";
  const isQuizPage = /^\/motif\/[^/]+\/quiz/.test(pathname);
  const isExamPage = /^\/urns\/[^/]+\/exam/.test(pathname);

  const langDropdownRef = useRef(null);
  const userDropdownRef = useRef(null);
  const moreDropdownRef = useRef(null);

  const status = useAuthStore((s) => s.status);
  const user = useAuthStore((s) => s.user);
  const fetchMe = useAuthStore((s) => s.fetchMe);
  const logout = useAuthStore((s) => s.logout);

  const userDisplayName = user?.display_name || user?.email || "User";
  const userInitial = (userDisplayName || "U").trim().charAt(0).toUpperCase();
  const isStaff = ["teacher", "admin", "super_admin"].includes(user?.role);

  const t = (key) => translations[lang][key] || key;
  const isActive = (href) => pathname === href || pathname.startsWith(`${href}/`);

  const coreNavItems = [
    { icon: Home, label: t("nav.dashboard"), link: "/dashboard" },
    { icon: Eye, label: t("nav.explore"), link: "/explore" },
    { icon: Brain, label: t("nav.practice"), link: "/practice" },
    { icon: BookOpen, label: t("nav.collection"), link: "/collection" },
    { icon: Sparkles, label: t("nav.ai"), link: "/ai" },
    { icon: Map, label: t("nav.quests"), link: "/quests" },
  ];

  const secondaryNavItems = [
    { icon: Users, label: t("nav.friends"), link: "/friends" },
    { icon: Trophy, label: t("nav.achievements"), link: "/achievements" },
    { icon: Trophy, label: t("nav.leaderboard"), link: "/leaderboard" },
    { icon: Trophy, label: t("nav.leagues"), link: "/leagues" },
    { icon: User, label: t("nav.profile"), link: "/profile" },
  ];

  if (isStaff) {
    secondaryNavItems.push({
      icon: Shield,
      label: t("nav.admin"),
      link: "/admin",
    });
  }

  const mobileCoreNavItems = coreNavItems.slice(0, 4);

  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isMobileMenuOpen]);

  useEffect(() => {
    if (status === "authed" && !user) fetchMe();
  }, [status, user, fetchMe]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        langDropdownRef.current &&
        !langDropdownRef.current.contains(event.target)
      ) {
        setIsLangDropdownOpen(false);
      }
      if (
        userDropdownRef.current &&
        !userDropdownRef.current.contains(event.target)
      ) {
        setIsUserDropdownOpen(false);
      }
      if (
        moreDropdownRef.current &&
        !moreDropdownRef.current.contains(event.target)
      ) {
        setIsMoreDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    setIsMobileMenuOpen(false);
    setIsLangDropdownOpen(false);
    setIsUserDropdownOpen(false);
    setIsMoreDropdownOpen(false);
  }, [pathname]);

  if (isAuthPage || isQuizPage || isExamPage) return null;

  return (
    <>
      <nav className="fixed left-0 right-0 top-3 z-50 hidden px-4 md:block">
        <div className="mx-auto flex max-w-7xl items-center gap-3 rounded-[1.75rem] border border-primary/20 bg-[#090604]/90 px-3 py-2 shadow-[0_16px_46px_-28px_rgba(0,0,0,0.92)] ring-1 ring-white/5 backdrop-blur-xl">
          <Link
            href="/"
            className="group flex min-w-[178px] shrink-0 items-center gap-3 rounded-2xl px-2 py-1.5 transition hover:bg-primary/10"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-2xl border border-primary/25 bg-primary/10 font-serif text-base font-bold text-primary shadow-[inset_0_1px_0_hsl(43_30%_92%_/_0.08)]">
              LN
            </span>
            <span>
            <span className="block font-serif text-sm font-semibold leading-none tracking-tight text-gradient-bronze">
              Lưu Niên Sử Kí
            </span>
            <span className="mt-0.5 block text-[10px] font-medium uppercase tracking-[0.18em] text-muted-foreground group-hover:text-primary/80">
              Cửu Đỉnh
            </span>
            </span>
          </Link>

          <div className="flex min-w-0 flex-1 items-center justify-center gap-0.5 overflow-x-auto scrollbar-hide rounded-full border border-primary/10 bg-background/25 px-1.5 py-1">
            {coreNavItems.map((item) => (
              <NavIconLink
                key={item.link}
                item={item}
                active={isActive(item.link)}
              />
            ))}
          </div>

          <div className="flex shrink-0 items-center gap-1.5">
            <div className="relative" ref={moreDropdownRef}>
              <button
                onClick={() => {
                  setIsMoreDropdownOpen((prev) => !prev);
                  setIsLangDropdownOpen(false);
                  setIsUserDropdownOpen(false);
                }}
                className="inline-flex items-center gap-1 rounded-full border border-transparent px-2.5 py-1.5 text-stone-300 transition-all hover:border-primary/25 hover:bg-primary/10 hover:text-primary"
                type="button"
                aria-haspopup="menu"
                aria-expanded={isMoreDropdownOpen}
              >
                <Menu className="h-4 w-4" />
                <span className="text-xs font-semibold">{t("nav.menu")}</span>
                <ChevronDown
                  className={`h-3 w-3 transition-transform ${isMoreDropdownOpen ? "rotate-180" : "rotate-0"}`}
                />
              </button>
              {isMoreDropdownOpen && (
                <div className="absolute right-0 top-full mt-3 min-w-[230px] rounded-2xl border border-primary/20 bg-[#090604]/96 p-1.5 shadow-[0_18px_46px_-30px_rgba(0,0,0,0.9)] ring-1 ring-white/5 backdrop-blur-xl">
                  {secondaryNavItems.map((item) => {
                    const Icon = item.icon;
                    return (
                      <Link key={item.link} href={item.link}>
                        <span className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-stone-300 transition-colors hover:bg-primary/10 hover:text-primary">
                          <Icon className="h-4 w-4 text-primary" />
                          <span>{item.label}</span>
                        </span>
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>

            {status === "authed" && (
              <div className="relative" ref={userDropdownRef}>
                <button
                  onClick={() => {
                    setIsUserDropdownOpen((prev) => !prev);
                    setIsLangDropdownOpen(false);
                    setIsMoreDropdownOpen(false);
                  }}
                  className="inline-flex items-center gap-1 rounded-full border border-transparent px-2 py-1.5 text-stone-300 transition-all hover:border-primary/25 hover:bg-primary/10 hover:text-primary"
                  type="button"
                  aria-haspopup="menu"
                  aria-expanded={isUserDropdownOpen}
                >
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center overflow-hidden rounded-full border border-primary/28 bg-primary/10">
                    {user?.avatar_url ? (
                      <img
                        src={user.avatar_url}
                        alt={userDisplayName}
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <span className="text-[11px] font-bold text-primary">
                        {userInitial}
                      </span>
                    )}
                  </span>
                  <span className="max-w-[120px] truncate text-xs font-semibold">
                    {userDisplayName}
                  </span>
                  <ChevronDown
                    className={`h-3 w-3 transition-transform ${isUserDropdownOpen ? "rotate-180" : "rotate-0"}`}
                  />
                </button>
                {isUserDropdownOpen && (
                  <div className="absolute right-0 top-full mt-3 min-w-[220px] rounded-2xl border border-primary/20 bg-[#090604]/96 p-1.5 shadow-[0_18px_46px_-30px_rgba(0,0,0,0.9)] ring-1 ring-white/5 backdrop-blur-xl">
                    <div className="px-3 py-2">
                      <p className="truncate text-sm font-semibold text-foreground">
                        {userDisplayName}
                      </p>
                      {user?.email ? (
                        <p className="truncate text-xs text-muted-foreground">
                          {user.email}
                        </p>
                      ) : null}
                    </div>
                    <div className="my-1 border-t border-primary/15" />
                    <button
                      onClick={() => {
                        logout();
                        setIsUserDropdownOpen(false);
                      }}
                      className="w-full rounded-xl px-3 py-2 text-left text-sm text-stone-300 transition-colors hover:bg-primary/10 hover:text-primary"
                      type="button"
                    >
                      {t("nav.logout")}
                    </button>
                  </div>
                )}
              </div>
            )}

            <div className="relative" ref={langDropdownRef}>
              <button
                onClick={() => {
                  setIsLangDropdownOpen((prev) => !prev);
                  setIsUserDropdownOpen(false);
                  setIsMoreDropdownOpen(false);
                }}
                className="inline-flex items-center gap-1 rounded-full border border-transparent px-2 py-1.5 text-stone-300 transition-all hover:border-primary/25 hover:bg-primary/10 hover:text-primary"
                type="button"
                aria-haspopup="listbox"
                aria-expanded={isLangDropdownOpen}
              >
                <Globe className="h-4 w-4" />
                <span className="text-xs font-semibold uppercase">{lang}</span>
                <ChevronDown
                  className={`h-3 w-3 transition-transform ${isLangDropdownOpen ? "rotate-180" : "rotate-0"}`}
                />
              </button>
              {isLangDropdownOpen && (
                <div className="absolute right-0 top-full mt-3 min-w-[150px] rounded-2xl border border-primary/20 bg-[#090604]/96 p-1.5 shadow-[0_18px_46px_-30px_rgba(0,0,0,0.9)] ring-1 ring-white/5 backdrop-blur-xl">
                  {languages.map((language) => (
                    <button
                      key={language.code}
                      onClick={() => {
                        setLang(language.code);
                        setIsLangDropdownOpen(false);
                      }}
                      className={`flex w-full items-center justify-between rounded-xl px-3 py-2 text-left text-sm transition-colors hover:bg-primary/10 ${
                        lang === language.code
                          ? "font-medium text-primary"
                          : "text-foreground/80"
                      }`}
                      type="button"
                    >
                      <span>{language.nativeName}</span>
                      {lang === language.code ? (
                        <span className="text-primary">*</span>
                      ) : null}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <Link href="/dashboard" className="shrink-0">
              <Button
                size="sm"
                className="whitespace-nowrap px-3 py-1 text-xs"
              >
                {t("nav.start")}
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      <nav className="fixed bottom-3 left-1/2 z-30 w-full max-w-md -translate-x-1/2 px-3 md:hidden">
        <div className="flex items-center gap-1 rounded-full border border-primary/20 bg-[#090604]/94 px-2 py-1.5 shadow-[0_14px_38px_-24px_rgba(0,0,0,0.9)] ring-1 ring-white/5 backdrop-blur-xl">
          {mobileCoreNavItems.map((item) => (
            <NavIconLink
              key={item.link}
              item={item}
              compact
              active={isActive(item.link)}
              onClick={() => setIsMobileMenuOpen(false)}
            />
          ))}

          <button
            onClick={() => setIsMobileMenuOpen((prev) => !prev)}
            className="flex flex-col items-center gap-1 rounded-2xl px-2 py-1.5 text-muted-foreground transition-colors hover:text-primary"
            aria-label="Mở mục lục"
            type="button"
          >
            {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            <span className="text-[11px] font-medium">{t("nav.menu")}</span>
          </button>
        </div>
      </nav>

      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-background/78 backdrop-blur-sm md:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      <div
        className={`fixed bottom-0 left-0 right-0 z-50 transition-all duration-300 md:hidden ${
          isMobileMenuOpen
            ? "translate-y-0 opacity-100"
            : "pointer-events-none translate-y-full opacity-0"
        }`}
        role="navigation"
        aria-label="Điều hướng di động"
      >
        <div className="max-h-[72vh] space-y-5 overflow-y-auto rounded-t-[2rem] border-t border-primary/20 bg-[#090604]/97 p-5 shadow-[0_-18px_54px_-34px_rgba(0,0,0,0.92)] ring-1 ring-white/5 backdrop-blur-xl">
          {status === "authed" ? (
            <div className="flex items-center justify-between gap-3 rounded-2xl border border-primary/20 bg-secondary/45 px-4 py-3">
              <div className="flex min-w-0 items-center gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-full border border-primary/28 bg-primary/10">
                  {user?.avatar_url ? (
                    <img
                      src={user.avatar_url}
                      alt={userDisplayName}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <span className="text-sm font-bold text-primary">
                      {userInitial}
                    </span>
                  )}
                </div>
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-foreground">
                    {userDisplayName}
                  </p>
                  {user?.email ? (
                    <p className="truncate text-xs text-muted-foreground">
                      {user.email}
                    </p>
                  ) : null}
                </div>
              </div>
              <button
                onClick={() => {
                  logout();
                  setIsMobileMenuOpen(false);
                }}
                className="rounded-xl border border-primary/20 bg-primary/10 px-3 py-2 text-xs font-semibold text-primary transition-colors hover:bg-primary/15"
                type="button"
              >
                {t("nav.logout")}
              </button>
            </div>
          ) : null}

          <div>
            <p className="mb-3 text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              Lối tắt
            </p>
            <div className="grid grid-cols-2 gap-2">
              {[...coreNavItems, ...secondaryNavItems].map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.link}
                    href={item.link}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`flex items-center gap-2 rounded-xl border px-3 py-2 text-xs font-medium transition-colors ${
                      isActive(item.link)
                        ? "border-primary/50 bg-primary/10 text-primary"
                        : "border-border/60 bg-secondary/30 text-foreground/80 hover:border-primary/30 hover:bg-primary/10 hover:text-primary"
                    }`}
                  >
                    <Icon className="h-4 w-4 text-primary" />
                    <span className="truncate">{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>

          <div>
            <p className="mb-3 text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              Ngôn ngữ
            </p>
            <div className="grid grid-cols-4 gap-2">
              {languages.map((language) => (
                <button
                  key={language.code}
                  onClick={() => setLang(language.code)}
                  className={`rounded-xl py-2.5 text-xs font-semibold transition-colors ${
                    lang === language.code
                      ? "border border-primary/30 bg-primary text-primary-foreground"
                      : "border border-border/60 bg-secondary/45 text-foreground/70 hover:bg-primary/10"
                  }`}
                  type="button"
                >
                  {language.code.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <Link
            href="/dashboard"
            className="block"
            onClick={() => setIsMobileMenuOpen(false)}
          >
            <Button className="w-full">
              {t("nav.start")}
            </Button>
          </Link>
        </div>
      </div>
    </>
  );
}
