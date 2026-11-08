"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  MapIcon,
  RouteIcon,
  TrophyIcon,
  StampIcon,
  UserIcon,
  Menu,
  Palette,
  Maximize2,
  Globe,
  FileText,
  Camera,
  Printer,
  Award,
  ShieldCheck,
  ChevronRight,
  Compass,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";
import { usePassportProgress } from "@/lib/imperial/passport-storage";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";

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

interface DrawerMenuSection {
  title: string;
  items: Array<{
    label: string;
    description: string;
    href: string;
    icon: LucideIcon;
    badge?: string;
  }>;
}

const DRAWER_SECTIONS: DrawerMenuSection[] = [
  {
    title: "Không gian di sản & Học tập",
    items: [
      {
        label: "Bản đồ không ảnh di sản",
        description: "Bản đồ không ảnh trực giao 4096x3072",
        href: "/dai-noi",
        icon: MapIcon,
      },
      {
        label: "Bản đồ vệ tinh toàn màn hình",
        description: "Google Maps vệ tinh & định vị WGS84",
        href: "/dai-noi/map",
        icon: Globe,
        badge: "Vệ tinh",
      },
      {
        label: "Mỹ thuật cung đình",
        description: "Khảm sành sứ, Pháp lam, Đúc đồng, Sơn thếp",
        href: "/dai-noi/my-thuat",
        icon: Palette,
        badge: "5 Chuyên đề",
      },
      {
        label: "Tuyến đường di sản",
        description: "5 lộ trình khám phá chuyên đề theo trục",
        href: "/dai-noi/tuyen-duong",
        icon: RouteIcon,
      },
      {
        label: "Hộ chiếu di sản số",
        description: "Đóng 16 dấu ấn triện hoàng gia khi khảo sát",
        href: "/dai-noi/ho-chieu",
        icon: StampIcon,
      },
    ],
  },
  {
    title: "Sử liệu & Nghiên cứu",
    items: [
      {
        label: "Mục lục nguồn tư liệu",
        description: "Đại Nam Thực Lục, Hội Điển Sự Lệ, ảnh EFEO",
        href: "/dai-noi/nguon",
        icon: FileText,
      },
      {
        label: "Kho ảnh tư liệu thế kỷ 20",
        description: "27 tư liệu thị giác Cố đô phục chế số",
        href: "/dai-noi/thu-vien-anh",
        icon: Camera,
      },
      {
        label: "Phiếu in học tập & Ngoại tuyến",
        description: "Xuất A4 phiếu điền dã di sản & PWA",
        href: "/dai-noi/offline",
        icon: Printer,
      },
      {
        label: "Chứng nhận hoàng triều",
        description: "Xuất chứng chỉ di sản mộc son vinh danh",
        href: "/dai-noi/chung-nhan",
        icon: Award,
      },
      {
        label: "Bảng quản lý giáo viên",
        description: "Giao nhiệm vụ & chấm Rubric S1–S4",
        href: "/dai-noi/giao-vien",
        icon: ShieldCheck,
      },
    ],
  },
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
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <>
      <nav
        aria-label="Điều hướng di động Đại Nội Huế"
        className="fixed inset-x-0 bottom-0 z-40 border-t border-[#D4AF37]/40 bg-[#4A0E0E]/95 backdrop-blur-xl text-[#FDF8EE] shadow-lg md:hidden"
      >
        {/* Floating Quick Explore Drawer Trigger Pill */}
        <div className="absolute right-3 -top-9 pointer-events-auto">
          <button
            type="button"
            onClick={() => setDrawerOpen(true)}
            aria-label="Mở danh mục di tích Đại Nội Huế"
            className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#5C1010]/95 border border-[#D4AF37]/60 text-[#FDF8EE] text-[10px] font-semibold shadow-lg backdrop-blur-md hover:bg-[#8E2323] transition-colors"
          >
            <Menu className="w-3 h-3 text-[#D4AF37]" />
            <span>Mở rộng</span>
          </button>
        </div>

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

      {/* Slide-Up Mobile Navigation Drawer */}
      <Sheet open={drawerOpen} onOpenChange={setDrawerOpen}>
        <SheetContent
          side="bottom"
          className="bg-card/95 backdrop-blur-2xl border-t border-border/80 p-5 shadow-2xl max-h-[85vh] rounded-t-3xl overflow-y-auto no-scrollbar text-foreground"
        >
          {/* Touch Drag Indicator */}
          <div className="mx-auto w-12 h-1.5 rounded-full bg-muted-foreground/30 mb-3 shrink-0" />

          <SheetHeader className="text-left pb-3 border-b border-border/60">
            <SheetTitle className="text-xl font-bold font-serif text-foreground flex items-center gap-2">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg border border-[#D4AF37]/60 bg-[#8E2323] font-serif text-xs font-black text-white">
                LN
              </span>
              <span>Đại Nội Huế — Menu di sản số</span>
            </SheetTitle>
            <SheetDescription className="text-xs text-muted-foreground">
              Toàn bộ không gian học tập, mỹ thuật, nguồn sử liệu và tiện ích
            </SheetDescription>
          </SheetHeader>

          <div className="py-4 space-y-6">
            {DRAWER_SECTIONS.map((section) => (
              <div key={section.title} className="space-y-2">
                <h4 className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground px-1">
                  {section.title}
                </h4>
                <div className="grid grid-cols-1 gap-1.5">
                  {section.items.map((item) => {
                    const active = isItemActive(pathname, item.href);
                    const Icon = item.icon;
                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        onClick={() => setDrawerOpen(false)}
                        className={cn(
                          "flex items-center justify-between p-3 rounded-2xl transition-all border",
                          active
                            ? "bg-primary/10 border-primary/30 text-primary font-semibold"
                            : "bg-secondary/40 hover:bg-secondary border-border/50 text-foreground",
                        )}
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <div
                            className={cn(
                              "w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border",
                              active
                                ? "bg-primary text-primary-foreground border-primary"
                                : "bg-card text-muted-foreground border-border/60",
                            )}
                          >
                            <Icon className="w-4 h-4" />
                          </div>
                          <div className="min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-bold truncate">
                                {item.label}
                              </span>
                              {item.badge && (
                                <span className="px-1.5 py-0.2 rounded-full text-[9px] font-semibold bg-amber-500/10 text-amber-500 border border-amber-500/20">
                                  {item.badge}
                                </span>
                              )}
                            </div>
                            <p className="text-[11px] text-muted-foreground truncate">
                              {item.description}
                            </p>
                          </div>
                        </div>

                        <ChevronRight className="w-4 h-4 text-muted-foreground/60 shrink-0 ml-2" />
                      </Link>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </SheetContent>
      </Sheet>
    </>
  );
}
