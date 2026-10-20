"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  CompassIcon,
  BookOpenIcon,
  FileTextIcon,
  LogOutIcon,
  UserIcon,
  GraduationCapIcon,
  MapPinIcon,
  ShieldCheckIcon,
  RouteIcon,
  TrophyIcon,
  AwardIcon,
  StampIcon,
  ChevronDownIcon,
  PrinterIcon,
  CameraIcon,
} from "lucide-react";

import { useAuthStore } from "@/stores/authStore";
import { usePassportProgress } from "@/lib/imperial/passport-storage";
import { cn } from "@/lib/utils";
import ThemeToggle from "@/components/shell/ThemeToggle";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface NavItem {
  label: string;
  href: string;
  icon: typeof CompassIcon;
}

const IMPERIAL_NAV: NavItem[] = [
  { label: "Khám phá", href: "/dai-noi", icon: CompassIcon },
  { label: "Tuyến học", href: "/dai-noi/tuyen-duong", icon: RouteIcon },
  { label: "Trò chơi", href: "/dai-noi/tro-choi", icon: TrophyIcon },
  { label: "Hộ chiếu di sản", href: "/dai-noi/ho-chieu", icon: StampIcon },
  { label: "Học tập", href: "/dai-noi/hoc-tap", icon: GraduationCapIcon },
];

function isRouteActive(pathname: string | null, href: string): boolean {
  if (!pathname) return false;
  if (href === "/dai-noi") {
    return pathname === "/dai-noi" || pathname === "/dai-noi/";
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

export default function ImperialHeader() {
  const pathname = usePathname();
  const status = useAuthStore((s) => s.status);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const { unlockedCount, totalSeals } = usePassportProgress();

  const isAuthed = status === "authed" && Boolean(user);
  const displayName = user?.display_name || user?.username || user?.email || "Người học";
  const initial = displayName.trim().charAt(0).toUpperCase() || "H";
  const isAdmin = user?.role === "admin" || user?.role === "staff";

  const isUtilityActive =
    pathname === "/dai-noi/thu-vien-anh" ||
    pathname?.startsWith("/dai-noi/thu-vien-anh/") ||
    pathname === "/dai-noi/chung-nhan" ||
    pathname?.startsWith("/dai-noi/chung-nhan/") ||
    pathname === "/dai-noi/offline" ||
    pathname?.startsWith("/dai-noi/offline/") ||
    pathname === "/dai-noi/giao-vien" ||
    pathname?.startsWith("/dai-noi/giao-vien/") ||
    pathname === "/dai-noi/nguon" ||
    pathname?.startsWith("/dai-noi/nguon/");

  return (
    <header className="sticky top-0 z-40 w-full border-b border-[#D4AF37]/40 bg-[#5C1010]/95 text-[#FDF8EE] backdrop-blur-xl shadow-md">
      <div className="pt-[env(safe-area-inset-top)]">
        <div className="mx-auto flex h-14 w-full max-w-[94rem] items-center justify-between gap-3 px-4 lg:px-8">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <Link
              href="/dai-noi"
              className="flex shrink-0 items-center gap-2.5 rounded-md focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
              aria-label="Lưu Niên — Đại Nội Huế — Trang chủ"
            >
              <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-[#D4AF37]/60 bg-[#8E2323] font-serif text-base font-black text-[#FDF8EE] shadow-sm">
                LN
              </span>
              <span className="flex flex-col leading-tight">
                <span className="font-serif text-lg font-bold tracking-[0.02em] text-[#FDF8EE]">
                  Lưu Niên — Đại Nội Huế
                </span>
                <span className="text-[10px] font-medium tracking-[0.16em] text-[#D4AF37] uppercase">
                  Bản đồ di sản số
                </span>
              </span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <nav
            aria-label="Điều hướng Đại Nội Huế"
            className="hidden min-w-0 items-center justify-center gap-1 md:flex"
          >
            {IMPERIAL_NAV.map((item) => {
              const active = isRouteActive(pathname, item.href);
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
                    active
                      ? "bg-[#8E2323] text-white border border-[#D4AF37]/40 shadow-xs"
                      : "text-[#FDF8EE]/80 hover:bg-white/10 hover:text-white",
                  )}
                >
                  <Icon className="h-4 w-4 text-[#D4AF37]" aria-hidden="true" />
                  <span>{item.label}</span>
                </Link>
              );
            })}

            {/* Secondary Utilities Dropdown (Chứng nhận, Phiếu in, Nguồn, Giáo viên) */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  type="button"
                  className={cn(
                    "flex items-center gap-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
                    isUtilityActive
                      ? "bg-[#8E2323] text-white border border-[#D4AF37]/40 shadow-xs"
                      : "text-[#FDF8EE]/80 hover:bg-white/10 hover:text-white",
                  )}
                  aria-label="Menu tài liệu & tiện ích di sản"
                >
                  <span>Tiện ích</span>
                  <ChevronDownIcon className="h-3.5 w-3.5 opacity-70 text-[#D4AF37]" aria-hidden="true" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-60">
                <DropdownMenuItem asChild>
                  <Link href="/dai-noi/thu-vien-anh" className="flex items-center gap-2.5 cursor-pointer">
                    <CameraIcon className="h-4 w-4 text-primary shrink-0" aria-hidden="true" />
                    <div className="flex flex-col">
                      <span className="font-medium text-foreground">Kho ảnh di sản</span>
                      <span className="text-[11px] text-muted-foreground">27 tư liệu thị giác Cố đô</span>
                    </div>
                  </Link>
                </DropdownMenuItem>

                <DropdownMenuItem asChild>
                  <Link href="/dai-noi/chung-nhan" className="flex items-center gap-2.5 cursor-pointer">
                    <AwardIcon className="h-4 w-4 text-amber-500 shrink-0" aria-hidden="true" />
                    <div className="flex flex-col">
                      <span className="font-medium text-foreground">Chứng nhận di sản</span>
                      <span className="text-[11px] text-muted-foreground">Mộc son & vinh danh</span>
                    </div>
                  </Link>
                </DropdownMenuItem>

                <DropdownMenuItem asChild>
                  <Link href="/dai-noi/offline" className="flex items-center gap-2.5 cursor-pointer">
                    <PrinterIcon className="h-4 w-4 text-emerald-600 dark:text-emerald-400 shrink-0" aria-hidden="true" />
                    <div className="flex flex-col">
                      <span className="font-medium text-foreground">Phiếu in & Ngoại tuyến</span>
                      <span className="text-[11px] text-muted-foreground">Xuất A4 chuẩn & PWA</span>
                    </div>
                  </Link>
                </DropdownMenuItem>

                <DropdownMenuSeparator />

                <DropdownMenuItem asChild>
                  <Link href="/dai-noi/giao-vien" className="flex items-center gap-2.5 cursor-pointer">
                    <ShieldCheckIcon className="h-4 w-4 text-blue-500 shrink-0" aria-hidden="true" />
                    <div className="flex flex-col">
                      <span className="font-medium text-foreground">Bảng giáo viên</span>
                      <span className="text-[11px] text-muted-foreground">Chấm điểm Rubric S1–S4</span>
                    </div>
                  </Link>
                </DropdownMenuItem>

                <DropdownMenuItem asChild>
                  <Link href="/dai-noi/nguon" className="flex items-center gap-2.5 cursor-pointer">
                    <FileTextIcon className="h-4 w-4 text-muted-foreground shrink-0" aria-hidden="true" />
                    <div className="flex flex-col">
                      <span className="font-medium text-foreground">Nguồn tư liệu</span>
                      <span className="text-[11px] text-muted-foreground">ĐNTL & Hội Điển Sự Lệ</span>
                    </div>
                  </Link>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </nav>

          {/* User Badge & Actions */}
          <div className="flex shrink-0 items-center gap-2.5">
            {/* Unlocked Seal Count Badge */}
            <Link
              href="/dai-noi/ho-chieu"
              className={cn(
                "flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold transition-all focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
                pathname === "/dai-noi/ho-chieu"
                  ? "border-primary bg-primary text-primary-foreground shadow-xs"
                  : "border-primary/40 bg-primary/10 text-primary hover:border-primary/70 hover:bg-primary/20",
              )}
              aria-label={`Hộ chiếu di sản: Đã đóng ${unlockedCount} trên tổng số ${totalSeals} ấn triện hoàng gia`}
              title={`Hộ chiếu di sản: ${unlockedCount}/${totalSeals} ấn triện hoàng gia`}
            >
              <StampIcon className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
              <span className="tabular-nums font-bold">
                {unlockedCount}/{totalSeals}
              </span>
              <span className="hidden xl:inline text-[11px] font-medium opacity-85">
                Ấn triện
              </span>
            </Link>

            <ThemeToggle />

            {status === "checking" ? (
              <div className="h-9 w-20 animate-pulse rounded-full bg-secondary/50" />
            ) : isAuthed ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button
                    type="button"
                    className="flex h-9 items-center gap-2 rounded-full border border-border/70 bg-secondary/40 p-1 pr-2.5 transition-colors hover:bg-secondary focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
                    aria-label={`Mở menu tài khoản · ${displayName}`}
                  >
                    <Avatar className="size-7">
                      {user?.avatar_url ? (
                        <AvatarImage src={user.avatar_url} alt={displayName} />
                      ) : null}
                      <AvatarFallback>{initial}</AvatarFallback>
                    </Avatar>
                    <span className="max-w-28 truncate text-xs font-semibold text-foreground">
                      {displayName}
                    </span>
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" sideOffset={8} className="w-60">
                  <DropdownMenuLabel className="font-normal">
                    <p className="truncate text-sm font-medium text-foreground">
                      {displayName}
                    </p>
                    {user?.email ? (
                      <p className="truncate text-xs text-muted-foreground">
                        {user.email}
                      </p>
                    ) : null}
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />

                  <DropdownMenuItem asChild>
                    <Link href="/dai-noi">
                      <MapPinIcon className="mr-2 h-4 w-4" aria-hidden="true" />
                      Bản đồ Đại Nội
                    </Link>
                  </DropdownMenuItem>

                  <DropdownMenuItem asChild>
                    <Link href="/dai-noi/ho-chieu">
                      <StampIcon className="mr-2 h-4 w-4 text-primary" aria-hidden="true" />
                      <span>Hộ chiếu di sản</span>
                      <span className="ml-auto text-xs font-bold text-primary">
                        {unlockedCount}/{totalSeals}
                      </span>
                    </Link>
                  </DropdownMenuItem>

                  <DropdownMenuItem asChild>
                    <Link href="/dai-noi/chung-nhan">
                      <AwardIcon className="mr-2 h-4 w-4 text-amber-500" aria-hidden="true" />
                      <span>Chứng nhận vinh danh</span>
                    </Link>
                  </DropdownMenuItem>

                  <DropdownMenuItem asChild>
                    <Link href="/dai-noi/offline">
                      <PrinterIcon className="mr-2 h-4 w-4 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
                      <span>Phiếu in & Ngoại tuyến</span>
                    </Link>
                  </DropdownMenuItem>

                  <DropdownMenuItem asChild>
                    <Link href="/dai-noi/hoc-tap">
                      <GraduationCapIcon className="mr-2 h-4 w-4" aria-hidden="true" />
                      Học tập & Nhiệm vụ
                    </Link>
                  </DropdownMenuItem>

                  <DropdownMenuItem asChild>
                    <Link href="/dai-noi/tuyen-duong">
                      <RouteIcon className="mr-2 h-4 w-4" aria-hidden="true" />
                      Tuyến đường khảo sát
                    </Link>
                  </DropdownMenuItem>

                  <DropdownMenuItem asChild>
                    <Link href="/dai-noi/giao-vien">
                      <ShieldCheckIcon className="mr-2 h-4 w-4" aria-hidden="true" />
                      Bảng đánh giá Giáo viên
                    </Link>
                  </DropdownMenuItem>

                  <DropdownMenuItem asChild>
                    <Link href="/profile">
                      <UserIcon className="mr-2 h-4 w-4" aria-hidden="true" />
                      Hồ sơ cá nhân
                    </Link>
                  </DropdownMenuItem>

                  {isAdmin ? (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem asChild>
                        <Link href="/admin/dai-noi/annotate">
                          <ShieldCheckIcon className="mr-2 h-4 w-4 text-primary" aria-hidden="true" />
                          <span className="font-medium text-primary">Biên tập bản đồ (Studio)</span>
                        </Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem asChild>
                        <Link href="/admin/dai-noi/chi-tiet-my-thuat">
                          <BookOpenIcon className="mr-2 h-4 w-4 text-primary" aria-hidden="true" />
                          <span className="font-medium text-primary">Biên tập mỹ thuật (Studio)</span>
                        </Link>
                      </DropdownMenuItem>
                    </>
                  ) : null}

                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={() => logout()}
                    className="text-destructive focus:bg-destructive/10 focus:text-destructive"
                  >
                    <LogOutIcon className="mr-2 h-4 w-4" aria-hidden="true" />
                    Đăng xuất
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <Link
                href={`/login?returnUrl=${encodeURIComponent(pathname || "/dai-noi")}`}
                className="inline-flex h-9 items-center justify-center rounded-lg bg-primary px-3.5 text-xs font-semibold text-primary-foreground transition-colors hover:bg-primary/90 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
              >
                Đăng nhập
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
