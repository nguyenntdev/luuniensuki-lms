"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpen,
  ChevronDown,
  Compass,
  GitCompare,
  History,
  Layers,
  Library,
  Map,
  Network,
  RotateCw,
  Route,
  Sparkles,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";

interface HeritageLink {
  title: string;
  description: string;
  href: string;
  icon: LucideIcon;
  badge?: string;
}

const FEATURED_LINKS: HeritageLink[] = [
  {
    title: "Cửu Đỉnh",
    description: "9 đỉnh đồng báu vật biểu trưng vương triều & giang sơn",
    href: "/cuu-dinh",
    icon: Sparkles,
    badge: "Báu vật",
  },
  {
    title: "Atlas 162",
    description: "162 phù điêu khảo chứng Hán-Nôm đa giác độ",
    href: "/atlas",
    icon: Layers,
    badge: "162 bản khắc",
  },
];

const TOOLS_LINKS: HeritageLink[] = [
  {
    title: "Bản đồ",
    description: "Địa lý & cương giới Đại Nam trên các đỉnh",
    href: "/map",
    icon: Map,
  },
  {
    title: "Dòng thời gian",
    description: "Biên niên sử kiện & quy trình đúc đỉnh 1835",
    href: "/timeline",
    icon: History,
  },
  {
    title: "Câu chuyện",
    description: "Điển tích, ngụ ý biểu tượng & giai thoại lịch sử",
    href: "/stories",
    icon: BookOpen,
  },
  {
    title: "Lộ trình",
    description: "Chủ đề khám phá dẫn dắt theo tuyến tri thức",
    href: "/trails",
    icon: Route,
  },
  {
    title: "So sánh",
    description: "Đối chiếu họa tiết, hình thái và quy cách đỉnh",
    href: "/compare",
    icon: GitCompare,
  },
  {
    title: "360° VR",
    description: "Tham quan không gian thực tế ảo Thế Miếu",
    href: "/vr360",
    icon: RotateCw,
  },
];

const SECONDARY_LINKS: HeritageLink[] = [
  {
    title: "Nguồn sử liệu",
    description: "Thực lục, Điển lệ, Khâm định & thư tịch gốc",
    href: "/sources",
    icon: Library,
  },
  {
    title: "Mạng lưới tri thức",
    description: "Đồ thị liên kết thực thể, địa danh & niên đại",
    href: "/explore/connections",
    icon: Network,
  },
];

const ALL_HERITAGE_HREFS = [
  ...FEATURED_LINKS,
  ...TOOLS_LINKS,
  ...SECONDARY_LINKS,
].map((item) => item.href);

function isHeritageActive(pathname: string | null): boolean {
  if (!pathname) return false;
  return ALL_HERITAGE_HREFS.some(
    (href) => pathname === href || pathname.startsWith(`${href}/`),
  );
}

export default function HeritageMegaMenu() {
  const pathname = usePathname();
  const active = isHeritageActive(pathname);

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          aria-expanded={undefined}
          className={cn(
            "group inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
            active
              ? "bg-primary/10 text-primary"
              : "text-muted-foreground hover:bg-secondary hover:text-foreground",
          )}
        >
          <Compass className="h-4 w-4" aria-hidden="true" />
          <span>Di sản văn hóa</span>
          <ChevronDown
            className="h-3.5 w-3.5 opacity-60 transition-transform duration-200 group-data-[state=open]:rotate-180"
            aria-hidden="true"
          />
        </button>
      </PopoverTrigger>

      <PopoverContent
        align="start"
        sideOffset={12}
        className="w-[92vw] max-w-4xl p-6 shadow-xl"
      >
        <div className="grid gap-6 md:grid-cols-12">
          {/* Featured Section */}
          <div className="space-y-3 md:col-span-4 md:border-r md:border-border/70 md:pr-6">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-semibold tracking-wider text-muted-foreground uppercase">
                Tiêu điểm di sản
              </span>
            </div>
            <div className="space-y-2">
              {FEATURED_LINKS.map((item) => {
                const Icon = item.icon;
                const isItemActive =
                  pathname === item.href ||
                  (pathname?.startsWith(`${item.href}/`) ?? false);

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "group block rounded-xl border p-3.5 transition-all duration-200 hover:border-primary/40 hover:bg-primary/5 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
                      isItemActive
                        ? "border-primary/40 bg-primary/10"
                        : "border-border/70 bg-card/60",
                    )}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2 font-serif text-base font-bold text-foreground group-hover:text-primary">
                        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                          <Icon className="h-4 w-4" aria-hidden="true" />
                        </span>
                        <span>{item.title}</span>
                      </div>
                      {item.badge && (
                        <span className="rounded-full bg-primary/15 px-2 py-0.5 text-[10px] font-semibold text-primary">
                          {item.badge}
                        </span>
                      )}
                    </div>
                    <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                      {item.description}
                    </p>
                  </Link>
                );
              })}
            </div>
          </div>

          {/* Tools & Experience Section */}
          <div className="space-y-3 md:col-span-8">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold tracking-wider text-muted-foreground uppercase">
                Công cụ & Trải nghiệm
              </span>
              <Link
                href="/explore"
                className="text-xs font-medium text-primary hover:underline"
              >
                Tất cả không gian →
              </Link>
            </div>

            <div className="grid gap-2.5 sm:grid-cols-2">
              {TOOLS_LINKS.map((item) => {
                const Icon = item.icon;
                const isItemActive =
                  pathname === item.href ||
                  (pathname?.startsWith(`${item.href}/`) ?? false);

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "group flex items-start gap-3 rounded-lg p-2.5 transition-colors hover:bg-secondary focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
                      isItemActive && "bg-secondary/80",
                    )}
                  >
                    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-border/70 bg-background text-muted-foreground transition-colors group-hover:border-primary/40 group-hover:bg-primary/10 group-hover:text-primary">
                      <Icon className="h-4 w-4" aria-hidden="true" />
                    </span>
                    <div className="min-w-0">
                      <div className="text-sm font-semibold text-foreground group-hover:text-primary">
                        {item.title}
                      </div>
                      <div className="line-clamp-1 text-xs text-muted-foreground">
                        {item.description}
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>

            {/* Secondary Section */}
            <div className="border-t border-border/70 pt-3">
              <span className="text-[11px] font-semibold tracking-wider text-muted-foreground uppercase">
                Khảo chứng & Nghiên cứu
              </span>
              <div className="mt-2 grid gap-2.5 sm:grid-cols-2">
                {SECONDARY_LINKS.map((item) => {
                  const Icon = item.icon;
                  const isItemActive =
                    pathname === item.href ||
                    (pathname?.startsWith(`${item.href}/`) ?? false);

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={cn(
                        "group flex items-start gap-3 rounded-lg p-2.5 transition-colors hover:bg-secondary focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
                        isItemActive && "bg-secondary/80",
                      )}
                    >
                      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-border/70 bg-background text-muted-foreground transition-colors group-hover:border-primary/40 group-hover:bg-primary/10 group-hover:text-primary">
                        <Icon className="h-4 w-4" aria-hidden="true" />
                      </span>
                      <div className="min-w-0">
                        <div className="text-sm font-semibold text-foreground group-hover:text-primary">
                          {item.title}
                        </div>
                        <div className="line-clamp-1 text-xs text-muted-foreground">
                          {item.description}
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
