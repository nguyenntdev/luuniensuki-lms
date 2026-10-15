"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Award,
  BookOpen,
  Bot,
  Flame,
  FolderHeart,
  Globe,
  GraduationCap,
  History,
  Layers,
  Library,
  LogIn,
  LogOut,
  Map,
  Network,
  RotateCw,
  Route,
  ShieldCheck,
  Sparkles,
  Users,
  User,
  GitCompare,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { useAuthStore } from "@/stores/authStore";
import { cn } from "@/lib/utils";
import ThemeToggle from "./ThemeToggle";

interface NavEntry {
  title: string;
  href: string;
  icon: LucideIcon;
  description?: string;
  badge?: string;
}

interface NavSection {
  title: string;
  items: NavEntry[];
  staffOnly?: boolean;
}

const NAV_SECTIONS: NavSection[] = [
  {
    title: "Di sản văn hóa",
    items: [
      {
        title: "Cửu Đỉnh",
        href: "/cuu-dinh",
        icon: Sparkles,
        description: "9 đỉnh đồng báu vật hoàng triều",
      },
      {
        title: "Atlas 162",
        href: "/atlas",
        icon: Layers,
        description: "162 phù điêu khảo chứng Hán-Nôm",
      },
      {
        title: "Bản đồ",
        href: "/map",
        icon: Map,
        description: "Địa lý & cương vực Cửu Đỉnh",
      },
      {
        title: "Dòng thời gian",
        href: "/timeline",
        icon: History,
        description: "Biên niên lịch sử & niên biểu",
      },
      {
        title: "Câu chuyện",
        href: "/stories",
        icon: BookOpen,
        description: "Điển tích và giai thoại di sản",
      },
      {
        title: "Lộ trình khám phá",
        href: "/trails",
        icon: Route,
        description: "Tuyến tham quan theo chủ đề",
      },
      {
        title: "So sánh đối chiếu",
        href: "/compare",
        icon: GitCompare,
        description: "Đối chiếu họa tiết và quy cách",
      },
      {
        title: "360° VR",
        href: "/vr360",
        icon: RotateCw,
        description: "Thực tế ảo không gian Thế Miếu",
      },
      {
        title: "Nguồn sử liệu",
        href: "/sources",
        icon: Library,
        description: "Thư tịch gốc & văn bản Hán-Nôm",
      },
      {
        title: "Mạng lưới tri thức",
        href: "/explore/connections",
        icon: Network,
        description: "Đồ thị liên kết thực thể lịch sử",
      },
    ],
  },
  {
    title: "Học tập & Rèn luyện",
    items: [
      {
        title: "Không gian học tập",
        href: "/dashboard",
        icon: GraduationCap,
        description: "Tổng quan tiến độ và nhiệm vụ",
      },
      {
        title: "Ôn tập thông minh",
        href: "/practice",
        icon: Flame,
        description: "Ôn luyện lặp lại ngắt quãng (FSRS)",
      },
      {
        title: "Hành trình di sản",
        href: "/quests",
        icon: Route,
        description: "Nhiệm vụ & thử thách hàng ngày",
      },
      {
        title: "Giáo viên AI",
        href: "/ai",
        icon: Bot,
        description: "Trợ lý giải đáp lịch sử có trích dẫn",
      },
    ],
  },
  {
    title: "Cộng đồng",
    items: [
      {
        title: "Bạn đồng hành",
        href: "/friends",
        icon: Users,
        description: "Kết nối bạn bè cùng sở thích",
      },
      {
        title: "Bảng vinh danh",
        href: "/achievements",
        icon: Award,
        description: "Bảng xếp hạng & huy hiệu danh giá",
      },
    ],
  },
  {
    title: "Khu vực cá nhân",
    items: [
      {
        title: "Hồ sơ & Tiến trình",
        href: "/profile",
        icon: User,
        description: "Thông tin cá nhân & cấp bậc",
      },
      {
        title: "Bộ sưu tập đã lưu",
        href: "/collection",
        icon: FolderHeart,
        description: "Họa tiết & tư liệu đã đánh dấu",
      },
    ],
  },
  {
    title: "Khu vực quản trị",
    staffOnly: true,
    items: [
      {
        title: "Bảng điều khiển quản trị",
        href: "/admin",
        icon: ShieldCheck,
        description: "Duyệt nguồn, biên tập & kiểm soát",
      },
    ],
  },
];

const ROLE_LABELS: Record<string, string> = {
  admin: "Quản trị viên",
  super_admin: "Tổng quản trị",
  teacher: "Giáo viên / Biên tập",
  learner: "Học viên",
  guest: "Khách viếng thăm",
};

interface MobileDrawerProps {
  trigger?: React.ReactNode;
}

export default function MobileDrawer({ trigger }: MobileDrawerProps) {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  const user = useAuthStore((s) => s.user);
  const status = useAuthStore((s) => s.status);
  const logout = useAuthStore((s) => s.logout);
  const [lang, setLang] = useState<"vi" | "en">("vi");

  const isAuthed = status === "authed";
  const role = user?.role ?? "guest";
  const isStaff = ["teacher", "admin", "super_admin"].includes(role);

  const displayName = user?.display_name || user?.email || "Khách viếng thăm";
  const initial = displayName.trim().charAt(0).toUpperCase() || "K";
  const roleBadge = ROLE_LABELS[role] || (isAuthed ? "Thành viên" : "Khách viếng thăm");

  const visibleSections = NAV_SECTIONS.filter((sec) => !sec.staffOnly || isStaff);

  function toggleLanguage() {
    setLang((prev) => (prev === "vi" ? "en" : "vi"));
  }

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      {trigger ? (
        <SheetTrigger asChild>{trigger}</SheetTrigger>
      ) : null}

      <SheetContent
        side="left"
        className="flex h-full w-[85vw] max-w-sm flex-col gap-0 p-0"
      >
        {/* Header with user avatar, name, role badge or guest CTA */}
        <SheetHeader className="border-b border-border/70 p-4 pb-4">
          <SheetTitle className="sr-only">Menu điều hướng chính</SheetTitle>

          {isAuthed ? (
            <div className="flex items-center gap-3">
              <Avatar className="size-11 border border-border">
                {user?.avatar_url ? (
                  <AvatarImage src={user.avatar_url} alt={displayName} />
                ) : null}
                <AvatarFallback className="bg-primary/10 font-serif font-bold text-primary">
                  {initial}
                </AvatarFallback>
              </Avatar>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-foreground">
                  {displayName}
                </p>
                {user?.email && (
                  <p className="truncate text-xs text-muted-foreground">
                    {user.email}
                  </p>
                )}
                <span className="mt-1 inline-flex items-center rounded-md bg-secondary px-2 py-0.5 text-[10px] font-semibold text-secondary-foreground">
                  {roleBadge}
                </span>
              </div>
            </div>
          ) : (
            <div className="space-y-2.5">
              <div className="flex items-center gap-2.5">
                <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-primary/30 bg-primary/10 font-serif text-sm font-bold text-primary">
                  LN
                </span>
                <div>
                  <p className="font-serif text-base font-bold text-foreground">
                    Lưu Niên Sử Kí
                  </p>
                  <p className="text-[10px] text-muted-foreground">
                    Di sản Cửu Đỉnh · Triều Nguyễn
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 pt-1">
                <Link
                  href="/login"
                  onClick={() => setOpen(false)}
                  className="flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-primary py-2 text-xs font-semibold text-primary-foreground transition-colors hover:brightness-110 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
                >
                  <LogIn className="h-3.5 w-3.5" aria-hidden="true" />
                  Đăng nhập
                </Link>
                <Link
                  href="/practice"
                  onClick={() => setOpen(false)}
                  className="flex flex-1 items-center justify-center rounded-lg border border-border/70 py-2 text-xs font-semibold text-foreground transition-colors hover:bg-secondary focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
                >
                  Bắt đầu học
                </Link>
              </div>
            </div>
          )}
        </SheetHeader>

        {/* 5 Categorized sections */}
        <div className="flex-1 overflow-y-auto px-3 py-3">
          <div className="space-y-4">
            {visibleSections.map((section) => (
              <div key={section.title} className="space-y-1">
                <div className="px-2 py-1 text-[11px] font-semibold tracking-wider text-muted-foreground uppercase">
                  {section.title}
                </div>
                <div className="space-y-0.5">
                  {section.items.map((item) => {
                    const Icon = item.icon;
                    const isActive =
                      pathname === item.href ||
                      (pathname?.startsWith(`${item.href}/`) ?? false);

                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        onClick={() => setOpen(false)}
                        className={cn(
                          "flex items-center gap-3 rounded-lg px-2.5 py-2 transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
                          isActive
                            ? "bg-primary/10 text-primary font-medium"
                            : "text-muted-foreground hover:bg-secondary hover:text-foreground",
                        )}
                      >
                        <Icon
                          className={cn(
                            "h-4 w-4 shrink-0",
                            isActive ? "text-primary" : "text-muted-foreground",
                          )}
                          aria-hidden="true"
                        />
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-xs font-semibold">
                            {item.title}
                          </div>
                          {item.description && (
                            <div className="line-clamp-1 text-[10px] text-muted-foreground">
                              {item.description}
                            </div>
                          )}
                        </div>
                      </Link>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer with language, theme toggle, and logout button */}
        <div className="border-t border-border/70 bg-card/40 p-3">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={toggleLanguage}
                className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-border/70 bg-background px-2.5 text-xs font-semibold text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
                aria-label={`Chuyển đổi ngôn ngữ. Hiện tại: ${lang.toUpperCase()}`}
              >
                <Globe className="h-3.5 w-3.5" aria-hidden="true" />
                <span>{lang === "vi" ? "VI" : "EN"}</span>
              </button>
              <ThemeToggle className="h-8 w-8" />
            </div>

            {isAuthed ? (
              <button
                type="button"
                onClick={() => {
                  setOpen(false);
                  logout();
                }}
                className="inline-flex h-8 items-center gap-1.5 rounded-lg px-2.5 text-xs font-semibold text-destructive transition-colors hover:bg-destructive/10 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
              >
                <LogOut className="h-3.5 w-3.5" aria-hidden="true" />
                <span>Đăng xuất</span>
              </button>
            ) : null}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
