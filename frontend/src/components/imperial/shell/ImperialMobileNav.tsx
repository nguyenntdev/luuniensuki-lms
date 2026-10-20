"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  MapIcon,
  RouteIcon,
  TrophyIcon,
  StampIcon,
  UserIcon,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";
import { usePassportProgress } from "@/lib/imperial/passport-storage";

interface ImperialBottomNavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  badgeCount?: boolean;
}

const DAI_NOI_BOTTOM_NAV: ImperialBottomNavItem[] = [
  { label: "Bản đồ", href: "/dai-noi", icon: MapIcon },
  { label: "Hành trình", href: "/dai-noi/tuyen-duong", icon: RouteIcon },
  { label: "Trò chơi", href: "/dai-noi/tro-choi", icon: TrophyIcon },
  { label: "Hộ chiếu", href: "/dai-noi/ho-chieu", icon: StampIcon, badgeCount: true },
  { label: "Cá nhân", href: "/profile", icon: UserIcon },
];

function isItemActive(pathname: string | null, href: string): boolean {
  if (!pathname) return false;
  if (href === "/dai-noi") {
    return pathname === "/dai-noi" || pathname === "/dai-noi/";
  }
  if (href === "/dai-noi/tuyen-duong") {
    return (
      pathname === "/dai-noi/tuyen-duong" ||
      pathname.startsWith("/dai-noi/tuyen-duong/") ||
      pathname.startsWith("/dai-noi/hanh-trinh/")
    );
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

export default function ImperialMobileNav() {
  const pathname = usePathname();
  const { unlockedCount, isLoaded } = usePassportProgress();

  return (
    <nav
      aria-label="Điều hướng di động Đại Nội Huế"
      className="fixed inset-x-0 bottom-0 z-40 border-t border-[#D4AF37]/40 bg-[#4A0E0E]/95 backdrop-blur-xl text-[#FDF8EE] shadow-lg md:hidden"
    >
      <div className="flex items-stretch justify-around px-1 pb-[env(safe-area-inset-bottom)]">
        {DAI_NOI_BOTTOM_NAV.map((item) => {
          const active = isItemActive(pathname, item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "relative flex min-w-0 flex-1 flex-col items-center gap-0.5 rounded-lg px-1 py-2 text-[10px] font-semibold transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
                active
                  ? "text-[#D4AF37] font-bold"
                  : "text-[#FDF8EE]/70 hover:bg-white/10 hover:text-white",
              )}
            >
              <div className="relative">
                <Icon
                  className={cn("h-5 w-5", active && "stroke-[2.25]")}
                  aria-hidden="true"
                />
                {item.badgeCount && isLoaded && unlockedCount > 0 ? (
                  <span
                    className="absolute -top-1 -right-2.5 flex h-3.5 min-w-3.5 items-center justify-center rounded-full bg-primary px-1 text-[9px] font-bold text-primary-foreground shadow-xs"
                    aria-hidden="true"
                  >
                    {unlockedCount}
                  </span>
                ) : null}
              </div>
              <span className="truncate">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
