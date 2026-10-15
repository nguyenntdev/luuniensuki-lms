"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  CompassIcon,
  GraduationCapIcon,
  HomeIcon,
  LayoutGridIcon,
  UserIcon,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { isShellRoute } from "@/lib/shellRoutes";
import { cn } from "@/lib/utils";

import GlobalSearch from "./GlobalSearch";
import MobileDrawer from "./MobileDrawer";
import ThemeToggle from "./ThemeToggle";
import { MenuIcon } from "lucide-react";

interface BottomNavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

const BOTTOM_NAV: BottomNavItem[] = [
  { label: "Trang chủ", href: "/", icon: HomeIcon },
  { label: "Atlas", href: "/atlas", icon: LayoutGridIcon },
  { label: "Khám phá", href: "/explore", icon: CompassIcon },
  { label: "Học", href: "/practice", icon: GraduationCapIcon },
  { label: "Cá nhân", href: "/profile", icon: UserIcon },
];

function isActive(pathname: string | null, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || (pathname?.startsWith(`${href}/`) ?? false);
}

export default function MobileNavigation() {
  const pathname = usePathname();

  if (!isShellRoute(pathname)) return null;

  return (
    <>
      <div className="sticky top-0 z-40 border-b border-border/70 bg-background/90 backdrop-blur-xl md:hidden">
        <div className="flex h-14 items-center gap-2 px-4 pt-[env(safe-area-inset-top)]">
          <Link
            href="/"
            className="flex min-w-0 items-center gap-2 rounded-md focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
            aria-label="Lưu Niên Sử Kí — Trang chủ"
          >
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-primary/30 bg-primary/10 font-serif text-sm font-bold text-primary">
              LN
            </span>
            <span className="min-w-0 truncate font-serif text-base font-bold tracking-[0.02em] text-foreground">
              Lưu Niên Sử Kí
            </span>
          </Link>
          <div className="ml-auto flex items-center gap-1">
            <GlobalSearch />
            <ThemeToggle />
            <MobileDrawer
              trigger={
                <button
                  type="button"
                  className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
                  aria-label="Mở danh mục menu"
                >
                  <MenuIcon className="h-5 w-5" aria-hidden="true" />
                </button>
              }
            />
          </div>
        </div>
      </div>

      <nav
        aria-label="Điều hướng chính"
        className="fixed inset-x-0 bottom-0 z-40 border-t border-border/70 bg-background/92 backdrop-blur-xl md:hidden"
      >
        <div className="flex items-stretch justify-around px-1 pb-[env(safe-area-inset-bottom)]">
          {BOTTOM_NAV.map((item) => {
            const active = isActive(pathname, item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex min-w-0 flex-1 flex-col items-center gap-0.5 rounded-lg px-1 py-2 text-[10px] font-semibold transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
                  active
                    ? "text-primary"
                    : "text-muted-foreground hover:bg-secondary hover:text-foreground",
                )}
              >
                <Icon
                  className={cn("h-5 w-5", active && "stroke-[2.25]")}
                  aria-hidden="true"
                />
                <span className="truncate">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </>
  );
}