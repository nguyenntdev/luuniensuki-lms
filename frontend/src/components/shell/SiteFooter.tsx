"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { isShellRoute } from "@/lib/shellRoutes";

const PRIMARY_NAV = [
  { label: "Cửu Đỉnh", href: "/cuu-dinh" },
  { label: "Atlas 162", href: "/atlas" },
  { label: "Khám phá", href: "/explore" },
  { label: "Nguồn", href: "/sources" },
];

const EXPLORE_NAV = [
  { label: "Bản đồ", href: "/map" },
  { label: "Dòng thời gian", href: "/timeline" },
  { label: "Câu chuyện", href: "/stories" },
  { label: "Mạng lưới", href: "/explore/connections" },
  { label: "So sánh", href: "/compare" },
  { label: "360°", href: "/vr360" },
];

function FooterLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="text-sm text-muted-foreground transition-colors hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
    >
      {children}
    </Link>
  );
}

export default function SiteFooter() {
  const pathname = usePathname();

  if (!isShellRoute(pathname)) return null;

  return (
    <footer className="border-t border-border bg-paper">
      <div className="mx-auto w-full max-w-[94rem] px-4 py-12 lg:px-8">
        <div className="grid gap-10 md:grid-cols-2 lg:grid-cols-4">
          <div className="lg:col-span-2">
            <Link
              href="/"
              className="inline-flex items-center gap-2.5 rounded-md focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
              aria-label="Lưu Niên Sử Kí — Trang chủ"
            >
              <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-primary/30 bg-primary/10 font-serif text-base font-bold text-primary">
                LN
              </span>
              <span className="font-serif text-xl font-bold tracking-[0.02em] text-foreground">
                Lưu Niên Sử Kí
              </span>
            </Link>
            <p className="mt-4 max-w-md text-sm leading-relaxed text-muted-foreground">
              Bảo tàng số tương tác về chín chiếc đỉnh đồng triều Nguyễn — di sản
              Cửu Đỉnh tại Hoàng thành Huế. Khám phá 162 phù điêu qua không gian,
              thời gian, tư liệu và nguồn sử liệu được ghi chú rõ ràng.
            </p>
          </div>

          <div>
            <h2 className="text-xs font-semibold tracking-[0.18em] text-foreground uppercase">
              Khám phá
            </h2>
            <ul className="mt-4 space-y-2.5">
              {PRIMARY_NAV.map((item) => (
                <li key={item.href}>
                  <FooterLink href={item.href}>{item.label}</FooterLink>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h2 className="text-xs font-semibold tracking-[0.18em] text-foreground uppercase">
              Không gian di sản
            </h2>
            <ul className="mt-4 space-y-2.5">
              {EXPLORE_NAV.map((item) => (
                <li key={item.href}>
                  <FooterLink href={item.href}>{item.label}</FooterLink>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-12 flex flex-col gap-4 border-t border-border/70 pt-6 sm:flex-row sm:items-center sm:justify-between">
          <FooterLink href="/sources">Về nguồn tư liệu</FooterLink>
          <p className="max-w-xl text-xs leading-relaxed text-muted-foreground">
            Một số diễn giải đang trong quá trình kiểm chứng nguồn.
          </p>
        </div>
      </div>
    </footer>
  );
}