"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuthStore } from "@/stores/authStore";
import { isShellRoute } from "@/lib/shellRoutes";
import { cn } from "@/lib/utils";

import GlobalSearch from "./GlobalSearch";
import UserMenu from "./UserMenu";

const PRIMARY_NAV = [
  { label: "Cửu Đỉnh", href: "/cuu-dinh" },
  { label: "Atlas 162", href: "/atlas" },
  { label: "Khám phá", href: "/explore" },
  { label: "Nguồn", href: "/sources" },
];

function isActive(pathname: string | null, href: string): boolean {
  return pathname === href || (pathname?.startsWith(`${href}/`) ?? false);
}

export default function GlobalHeader() {
  const pathname = usePathname();
  const status = useAuthStore((s) => s.status);
  const isAuthed = status === "authed";

  if (!isShellRoute(pathname)) return null;

  return (
    <header className="sticky top-0 z-40 hidden border-b border-border/70 bg-background/90 backdrop-blur-xl md:block">
      <div className="pt-[env(safe-area-inset-top)]">
        <div className="mx-auto flex h-14 w-full max-w-[94rem] items-center gap-4 px-4 lg:px-8">
          <Link
            href="/"
            className="flex shrink-0 items-center gap-2.5 rounded-md focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
            aria-label="Lưu Niên Sử Kí — Trang chủ"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-primary/30 bg-primary/10 font-serif text-base font-bold text-primary">
              LN
            </span>
            <span className="flex flex-col leading-tight">
              <span className="font-serif text-lg font-bold tracking-[0.02em] text-foreground">
                Lưu Niên Sử Kí
              </span>
              <span className="text-[10px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
                Cửu Đỉnh · Atlas
              </span>
            </span>
          </Link>

          <nav
            aria-label="Điều hướng chính"
            className="flex min-w-0 flex-1 items-center justify-center gap-1"
          >
            {PRIMARY_NAV.map((item) => {
              const active = isActive(pathname, item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "rounded-md px-3 py-1.5 text-sm font-medium transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
                    active
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:bg-secondary hover:text-foreground",
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="flex shrink-0 items-center gap-2">
            <GlobalSearch />
            {isAuthed ? (
              <>
                <Link
                  href="/dashboard"
                  className="inline-flex h-9 items-center rounded-lg border border-primary/30 bg-primary/10 px-3.5 text-xs font-semibold text-primary transition-colors hover:bg-primary/15 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
                >
                  Học của tôi
                </Link>
                <UserMenu />
              </>
            ) : (
              <>
                <Link
                  href="/practice"
                  className="inline-flex h-9 items-center rounded-lg bg-primary px-3.5 text-xs font-semibold text-primary-foreground transition-colors hover:brightness-110 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:outline-none"
                >
                  Bắt đầu học
                </Link>
                <Link
                  href="/login"
                  className="inline-flex h-9 items-center rounded-lg border border-border/70 px-3.5 text-xs font-semibold text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
                >
                  Đăng nhập
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}