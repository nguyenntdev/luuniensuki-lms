"use client";

import { useEffect, useRef, useState } from "react";
import {
  Menu,
  X,
  Globe,
  ChevronUp,
  Eye,
  Trophy,
  BookOpen,
  Sparkles,
  User,
  Map,
  Shield,
  Users,
  Brain,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuthStore } from "../stores/authStore";

function cn(...classes) {
  return classes.filter(Boolean).join(" ");
}

const Button = ({ className, size, children, ...props }) => {
  const baseStyles =
    "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50";
  const variants = {
    default: "bg-primary text-primary-foreground hover:bg-primary/90",
    sm: "h-9 rounded-md px-3",
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
    "nav.dashboard": "Learning Hub",
    "nav.explore": "Khám Phá",
    "nav.quests": "Hành Trình",
    "nav.collection": "Bộ Sưu Tập",
    "nav.practice": "Ôn Tập",
    "nav.ai": "AI Tutor",
    "nav.friends": "Bạn Bè",
    "nav.achievements": "Thành Tích",
    "nav.profile": "Hồ Sơ",
    "nav.admin": "Teacher Hub",
    "nav.leaderboard": "Bảng Hạng",
    "nav.leagues": "Leagues",
    "nav.menu": "Menu",
    "nav.logout": "Đăng xuất",
    "nav.start": "Tiếp Tục Học",
  },
  en: {
    "nav.dashboard": "Learning Hub",
    "nav.explore": "Explore",
    "nav.quests": "Quests",
    "nav.collection": "Collection",
    "nav.practice": "Practice",
    "nav.ai": "AI Tutor",
    "nav.friends": "Friends",
    "nav.achievements": "Achievements",
    "nav.profile": "Profile",
    "nav.admin": "Teacher Hub",
    "nav.leaderboard": "Leaderboard",
    "nav.leagues": "Leagues",
    "nav.menu": "Menu",
    "nav.logout": "Logout",
    "nav.start": "Continue Learning",
  },
};

function NavIconLink({ item, onClick, active, compact }) {
  const Icon = item.icon;
  const base = compact
    ? "w-full flex flex-col items-center gap-1 px-2 py-1.5 rounded-2xl transition-colors"
    : "inline-flex items-center gap-1.5 px-2 py-1.5 rounded-full transition-colors";

  const activeClasses = compact
    ? "text-primary border border-primary/50 bg-primary/10 shadow-[0_6px_14px_rgba(0,0,0,0.2)]"
    : "text-foreground bg-primary/20 border border-primary/40";

  const idleClasses = compact
    ? "text-primary/80 hover:text-primary"
    : "text-primary hover:text-foreground hover:bg-primary/20";

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
    { icon: Eye, label: t("nav.explore"), link: "/explore" },
    { icon: Brain, label: t("nav.practice"), link: "/practice" },
    { icon: BookOpen, label: t("nav.collection"), link: "/collection" },
  ];

  const secondaryNavItems = [
    { icon: Sparkles, label: t("nav.ai"), link: "/ai" },
    { icon: Map, label: t("nav.quests"), link: "/quests" },
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

  const mobileCoreNavItems = coreNavItems.slice(0, 3);

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
      <nav className="fixed bottom-4 left-1/2 z-50 hidden max-w-[95vw] -translate-x-1/2 md:flex">
        <div className="flex items-center gap-2 rounded-full border border-border/60 bg-background/90 px-3 py-2 shadow-[0_12px_35px_rgba(0,0,0,0.35)] backdrop-blur-xl">
          <Link
            href="/"
            className="shrink-0 border-r border-border/50 pr-2 font-serif text-sm font-semibold tracking-tight text-foreground/90"
          >
            Lưu Niên Sử Kí
          </Link>

          <div className="flex items-center gap-0.5 overflow-x-auto scrollbar-hide">
            {coreNavItems.map((item) => (
              <NavIconLink
                key={item.link}
                item={item}
                active={isActive(item.link)}
              />
            ))}
          </div>

          <div className="flex shrink-0 items-center gap-1.5 border-l border-border/50 pl-2">
            <div className="relative" ref={moreDropdownRef}>
              <button
                onClick={() => {
                  setIsMoreDropdownOpen((prev) => !prev);
                  setIsLangDropdownOpen(false);
                  setIsUserDropdownOpen(false);
                }}
                className="inline-flex items-center gap-1 rounded-full px-2 py-1.5 text-primary transition-colors hover:bg-primary/10"
                type="button"
                aria-haspopup="menu"
                aria-expanded={isMoreDropdownOpen}
              >
                <Menu className="h-4 w-4" />
                <span className="text-xs font-semibold">{t("nav.menu")}</span>
                <ChevronUp
                  className={`h-3 w-3 transition-transform ${isMoreDropdownOpen ? "rotate-180" : "rotate-0"}`}
                />
              </button>
              {isMoreDropdownOpen && (
                <div className="absolute bottom-full right-0 mb-2 min-w-[220px] rounded-xl border border-border bg-background/95 py-1 shadow-lg backdrop-blur-lg">
                  {secondaryNavItems.map((item) => {
                    const Icon = item.icon;
                    return (
                      <Link key={item.link} href={item.link}>
                        <span className="flex items-center gap-2 px-3 py-2 text-sm text-foreground/80 transition-colors hover:bg-primary/10">
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
                  className="inline-flex items-center gap-1 rounded-full px-2 py-1.5 text-primary transition-colors hover:bg-primary/10"
                  type="button"
                  aria-haspopup="menu"
                  aria-expanded={isUserDropdownOpen}
                >
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center overflow-hidden rounded-full border border-border/60 bg-primary/10">
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
                  <ChevronUp
                    className={`h-3 w-3 transition-transform ${isUserDropdownOpen ? "rotate-180" : "rotate-0"}`}
                  />
                </button>
                {isUserDropdownOpen && (
                  <div className="absolute bottom-full right-0 mb-2 min-w-[180px] rounded-xl border border-border bg-background/95 py-1 shadow-lg backdrop-blur-lg">
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
                    <div className="my-1 border-t border-border/60" />
                    <button
                      onClick={() => {
                        logout();
                        setIsUserDropdownOpen(false);
                      }}
                      className="w-full px-3 py-2 text-left text-sm text-foreground/80 transition-colors hover:bg-primary/10"
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
                className="inline-flex items-center gap-1 rounded-full px-2 py-1.5 text-primary transition-colors hover:bg-primary/10"
                type="button"
                aria-haspopup="listbox"
                aria-expanded={isLangDropdownOpen}
              >
                <Globe className="h-4 w-4" />
                <span className="text-xs font-semibold uppercase">{lang}</span>
                <ChevronUp
                  className={`h-3 w-3 transition-transform ${isLangDropdownOpen ? "rotate-180" : "rotate-0"}`}
                />
              </button>
              {isLangDropdownOpen && (
                <div className="absolute bottom-full right-0 mb-2 min-w-[140px] rounded-xl border border-border bg-background/95 py-1 shadow-lg backdrop-blur-lg">
                  {languages.map((language) => (
                    <button
                      key={language.code}
                      onClick={() => {
                        setLang(language.code);
                        setIsLangDropdownOpen(false);
                      }}
                      className={`flex w-full items-center justify-between px-3 py-2 text-left text-sm transition-colors hover:bg-primary/10 ${
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
                className="whitespace-nowrap rounded-full bg-primary px-3 py-1 text-xs hover:bg-primary/90 hover:shadow-lg hover:shadow-primary/20"
              >
                {t("nav.start")}
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      <nav className="fixed bottom-3 left-1/2 z-30 w-full max-w-md -translate-x-1/2 px-3 md:hidden">
        <div className="flex items-center gap-1 rounded-full border border-border bg-background/95 px-2 py-1.5 shadow-[0_10px_30px_rgba(0,0,0,0.35)] backdrop-blur-lg">
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
            className="flex flex-col items-center gap-1 px-2 py-1.5 text-primary/80 transition-colors hover:text-primary"
            aria-label="More options"
            type="button"
          >
            {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            <span className="text-[11px] font-medium">{t("nav.menu")}</span>
          </button>
        </div>
      </nav>

      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-background/75 backdrop-blur-sm md:hidden"
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
        aria-label="Mobile navigation"
      >
        <div className="max-h-[70vh] space-y-5 overflow-y-auto rounded-t-3xl border-t border-border bg-background/95 p-5 shadow-2xl backdrop-blur-xl">
          {status === "authed" ? (
            <div className="flex items-center justify-between gap-3 rounded-2xl border border-border/60 bg-background/60 px-4 py-3">
              <div className="flex min-w-0 items-center gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-full border border-border/60 bg-primary/10">
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
                className="rounded-xl bg-muted/50 px-3 py-2 text-xs font-semibold text-foreground/80 transition-colors hover:bg-primary/10"
                type="button"
              >
                {t("nav.logout")}
              </button>
            </div>
          ) : null}

          <div>
            <p className="mb-3 text-xs text-muted-foreground">Quick links</p>
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
                        : "border-border/60 text-foreground/80 hover:bg-primary/10"
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
            <p className="mb-3 text-xs text-muted-foreground">Language</p>
            <div className="grid grid-cols-4 gap-2">
              {languages.map((language) => (
                <button
                  key={language.code}
                  onClick={() => setLang(language.code)}
                  className={`rounded-xl py-2.5 text-xs font-semibold transition-colors ${
                    lang === language.code
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted/50 text-foreground/70 hover:bg-primary/10"
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
            <Button className="w-full bg-primary hover:bg-primary/90">
              {t("nav.start")}
            </Button>
          </Link>
        </div>
      </div>
    </>
  );
}
