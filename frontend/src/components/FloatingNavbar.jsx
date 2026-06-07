"use client";

import { useEffect, useRef, useState } from "react";
import {
  BookOpen,
  Brain,
  Compass,
  Globe,
  Home,
  LogOut,
  Menu,
  Moon,
  Search,
  Shield,
  Sparkles,
  Sun,
  Trophy,
  User,
  Users,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuthStore } from "../stores/authStore";

function cn(...classes) {
  return classes.filter(Boolean).join(" ");
}

const primaryNav = [
  { icon: Home, label: "Học tập", href: "/dashboard" },
  { icon: Compass, label: "Khám phá", href: "/explore" },
  { icon: Brain, label: "Ôn tập", href: "/practice" },
  { icon: Sparkles, label: "Giáo viên AI", href: "/ai" },
  { icon: User, label: "Cá nhân", href: "/profile" },
];

const moreNav = [
  { icon: BookOpen, label: "Bộ sưu tập", href: "/collection" },
  { icon: Globe, label: "Tham quan 360°", href: "/vr360" },
  { icon: Users, label: "Bạn học", href: "/friends" },
  { icon: Trophy, label: "Thành tích", href: "/achievements" },
  { icon: Compass, label: "Hành trình", href: "/quests" },
];

function isItemActive(pathname, href) {
  return pathname === href || pathname.startsWith(`${href}/`);
}

function NavLink({ item, active, onClick, compact = false }) {
  const Icon = item.icon;
  return (
    <Link
      href={item.href}
      onClick={onClick}
      className={cn(
        compact
          ? "flex min-w-0 flex-1 flex-col items-center gap-1 rounded-lg px-1.5 py-1.5 text-[10px] font-semibold leading-tight"
          : "inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm font-semibold",
        active
          ? "bg-primary text-primary-foreground shadow-[0_10px_24px_-18px_hsl(var(--primary)/0.75)]"
          : "text-muted-foreground hover:bg-secondary hover:text-foreground",
      )}
    >
      <Icon className={compact ? "h-5 w-5" : "h-4 w-4"} />
      <span className="truncate">{item.label}</span>
    </Link>
  );
}

function Dropdown({ label, icon: Icon, active, open, setOpen, children }) {
  const ref = useRef(null);

  useEffect(() => {
    function close(event) {
      if (ref.current && !ref.current.contains(event.target)) setOpen(false);
    }
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [setOpen]);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className={cn(
          "inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold transition",
          active || open
            ? "bg-secondary text-foreground"
            : "text-muted-foreground hover:bg-secondary hover:text-foreground",
        )}
        aria-haspopup="menu"
        aria-expanded={open}
      >
        <Icon className="h-4 w-4" />
        {label}
      </button>

      {open ? (
        <div className="absolute right-0 top-full mt-2 w-56 rounded-lg border border-border bg-popover p-1.5 shadow-[0_18px_44px_-26px_rgba(0,0,0,0.85)]">
          {children}
        </div>
      ) : null}
    </div>
  );
}

export default function FloatingNavbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const [userOpen, setUserOpen] = useState(false);
  const [theme, setTheme] = useState("dark");

  const pathname = usePathname();
  const status = useAuthStore((s) => s.status);
  const user = useAuthStore((s) => s.user);
  const fetchMe = useAuthStore((s) => s.fetchMe);
  const logout = useAuthStore((s) => s.logout);

  const isAuthPage = pathname === "/login" || pathname === "/register";
  const isQuizPage = /^\/motif\/[^/]+\/quiz/.test(pathname);
  const isExamPage = /^\/urns\/[^/]+\/exam/.test(pathname);
  const isStaff = ["teacher", "admin", "super_admin"].includes(user?.role);
  const userDisplayName = user?.display_name || user?.email || "Tài khoản";
  const userInitial = userDisplayName.trim().charAt(0).toUpperCase();
  const allMoreItems = isStaff
    ? [...moreNav, { icon: Shield, label: "Quản trị", href: "/admin" }]
    : moreNav;

  useEffect(() => {
    if (status === "authed" && !user) fetchMe();
  }, [status, user, fetchMe]);

  useEffect(() => {
    setMobileOpen(false);
    setMoreOpen(false);
    setUserOpen(false);
  }, [pathname]);

  useEffect(() => {
    document.body.style.overflow = mobileOpen ? "hidden" : "unset";
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [mobileOpen]);

  useEffect(() => {
    const currentTheme = window.__getLuuniensukiTheme?.() || "dark";
    setTheme(currentTheme);
  }, []);

  function toggleTheme() {
    const nextTheme = theme === "dark" ? "light" : "dark";
    setTheme(nextTheme);
    window.__setLuuniensukiTheme?.(nextTheme);
  }

  if (isAuthPage || isQuizPage || isExamPage) return null;

  const moreActive = allMoreItems.some((item) => isItemActive(pathname, item.href));

  return (
    <>
      <nav className="fixed left-0 right-0 top-0 z-50 hidden border-b border-border/70 bg-background/96 backdrop-blur-xl md:block">
        <div className="mx-auto flex h-14 max-w-[1280px] items-center gap-3 px-4">
          <Link href="/" className="flex min-w-[150px] items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-xs font-bold text-primary-foreground">
              LN
            </span>
            <span className="min-w-0">
              <span className="block truncate text-sm font-bold text-foreground">
                Lưu Niên Sử Kí
              </span>
            </span>
          </Link>

          <div className="flex min-w-0 flex-1 items-center justify-center gap-1 rounded-lg border border-border/70 bg-secondary/35 p-1">
            {primaryNav.map((item) => (
              <NavLink key={item.href} item={item} active={isItemActive(pathname, item.href)} />
            ))}
          </div>

          <div className="flex shrink-0 items-center gap-1">
            <button
              type="button"
              onClick={() => window.dispatchEvent(new Event("open-command-palette"))}
              className="inline-flex h-9 items-center gap-2 rounded-lg border border-border/70 bg-secondary/40 px-3 text-xs font-medium text-muted-foreground hover:bg-secondary hover:text-foreground"
              aria-label="Tìm kiếm nhanh"
              title="Tìm kiếm nhanh (⌘K)"
            >
              <Search className="h-4 w-4" />
              <span className="hidden lg:inline">Tìm kiếm</span>
              <kbd className="hidden rounded border border-border px-1 text-[10px] lg:inline">⌘K</kbd>
            </button>
            <button
              type="button"
              onClick={toggleTheme}
              className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground hover:bg-secondary hover:text-foreground"
              aria-label={theme === "dark" ? "Bật giao diện sáng" : "Bật giao diện tối"}
            >
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>

            <Dropdown
              label="Khác"
              icon={Menu}
              active={moreActive}
              open={moreOpen}
              setOpen={setMoreOpen}
            >
              {allMoreItems.map((item) => {
                const ItemIcon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="flex items-center gap-2 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-secondary hover:text-foreground"
                  >
                    <ItemIcon className="h-4 w-4 text-primary" />
                    {item.label}
                  </Link>
                );
              })}
            </Dropdown>

            {status === "authed" ? (
              <Dropdown
                label={userDisplayName}
                icon={User}
                active={isItemActive(pathname, "/profile")}
                open={userOpen}
                setOpen={setUserOpen}
              >
                <div className="px-3 py-2">
                  <p className="truncate text-sm font-semibold text-foreground">{userDisplayName}</p>
                  {user?.email ? (
                    <p className="truncate text-xs text-muted-foreground">{user.email}</p>
                  ) : null}
                </div>
                <div className="my-1 border-t border-border" />
                <Link
                  href="/profile"
                  className="flex items-center gap-2 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-secondary hover:text-foreground"
                >
                  <User className="h-4 w-4 text-primary" />
                  Hồ sơ
                </Link>
                <button
                  type="button"
                  onClick={() => logout()}
                  className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm text-muted-foreground hover:bg-secondary hover:text-foreground"
                >
                  <LogOut className="h-4 w-4 text-primary" />
                  Đăng xuất
                </button>
              </Dropdown>
            ) : (
              <Link
                href="/login"
                className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
              >
                Đăng nhập
              </Link>
            )}
          </div>
        </div>
      </nav>

      <nav className="fixed bottom-3 left-1/2 z-40 w-full max-w-md -translate-x-1/2 px-3 md:hidden">
        <div className="flex items-center gap-1 rounded-xl border border-border bg-background/94 p-1.5 shadow-[0_18px_44px_-28px_rgba(0,0,0,0.9)] backdrop-blur-xl">
          {primaryNav.slice(0, 4).map((item) => (
            <NavLink
              key={item.href}
              item={item}
              compact
              active={isItemActive(pathname, item.href)}
              onClick={() => setMobileOpen(false)}
            />
          ))}
          <button
            type="button"
            onClick={() => setMobileOpen((prev) => !prev)}
            className="flex min-w-0 flex-1 flex-col items-center gap-1 rounded-lg px-2 py-1.5 text-[11px] font-semibold text-muted-foreground hover:bg-secondary hover:text-foreground"
            aria-label="Mở menu"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            <span>Khác</span>
          </button>
        </div>
      </nav>

      {mobileOpen ? (
        <button
          type="button"
          className="fixed inset-0 z-40 bg-background/72 backdrop-blur-sm md:hidden"
          onClick={() => setMobileOpen(false)}
          aria-label="Đóng menu"
        />
      ) : null}

      <div
        className={cn(
          "fixed bottom-0 left-0 right-0 z-50 md:hidden",
          "transition duration-200",
          mobileOpen ? "translate-y-0 opacity-100" : "pointer-events-none translate-y-full opacity-0",
        )}
      >
        <div className="max-h-[76vh] overflow-y-auto rounded-t-xl border-t border-border bg-popover p-4 shadow-[0_-18px_48px_-28px_rgba(0,0,0,0.9)]">
          {status === "authed" ? (
            <div className="mb-4 flex items-center justify-between gap-3 rounded-lg border border-border bg-secondary/55 p-3">
              <div className="flex min-w-0 items-center gap-3">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-primary text-sm font-bold text-primary-foreground">
                  {user?.avatar_url ? (
                    <img src={user.avatar_url} alt={userDisplayName} className="h-full w-full object-cover" />
                  ) : (
                    userInitial
                  )}
                </span>
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-foreground">{userDisplayName}</p>
                  {user?.email ? <p className="truncate text-xs text-muted-foreground">{user.email}</p> : null}
                </div>
              </div>
              <button
                type="button"
                onClick={() => logout()}
                className="rounded-lg border border-border px-3 py-2 text-xs font-semibold text-muted-foreground"
              >
                Đăng xuất
              </button>
            </div>
          ) : null}

          <div className="grid grid-cols-2 gap-2">
            {[primaryNav[4], ...allMoreItems].map((item) => (
              <NavLink
                key={item.href}
                item={item}
                active={isItemActive(pathname, item.href)}
                onClick={() => setMobileOpen(false)}
              />
            ))}
          </div>

          <button
            type="button"
            onClick={toggleTheme}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg border border-border px-4 py-3 text-sm font-semibold text-foreground hover:bg-secondary"
          >
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            {theme === "dark" ? "Giao diện sáng" : "Giao diện tối"}
          </button>

          {status !== "authed" ? (
            <Link
              href="/login"
              onClick={() => setMobileOpen(false)}
              className="mt-4 flex w-full items-center justify-center rounded-lg bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground"
            >
              Đăng nhập
            </Link>
          ) : null}
        </div>
      </div>
    </>
  );
}
