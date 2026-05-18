"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useAuthStore } from "@/stores/authStore";
import XpBoostIndicator from "./dashboard/XpBoostIndicator";

const NAV_LINKS = [
  { href: "/explore", label: "Khám phá" },
  { href: "/practice", label: "Ôn tập" },
  { href: "/collection", label: "Bộ sưu tập" },
  { href: "/ai", label: "Giáo viên AI" },
  { href: "/achievements", label: "Thành tích" },
];

export default function Navbar() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  const isActive = (path) => pathname === path;

  return (
    <nav className="border-b border-border bg-card">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 justify-between">
          <div className="flex">
            <div className="flex flex-shrink-0 items-center">
              <Link
                href="/"
                className="text-xl font-serif font-bold text-primary"
              >
                Lưu Niên Sử Kí
              </Link>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              {NAV_LINKS.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`inline-flex items-center border-b-2 px-1 pt-1 text-sm font-medium ${
                    isActive(link.href)
                      ? "border-primary text-foreground"
                      : "border-transparent text-muted-foreground hover:border-border hover:text-foreground"
                  }`}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </div>

          <div className="hidden sm:ml-6 sm:flex sm:items-center">
            {user ? (
              <div className="relative ml-3 flex items-center gap-4">
                <XpBoostIndicator size="sm" />
                <Link
                  href="/profile"
                  className={`text-sm font-medium ${isActive("/profile") ? "text-primary" : "text-muted-foreground hover:text-foreground"}`}
                >
                  {user.display_name}
                </Link>
                <button
                  onClick={() => logout()}
                  className="rounded-md bg-muted px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-muted/80"
                >
                  Đăng xuất
                </button>
              </div>
            ) : (
              <Link
                href="/login"
                className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
              >
                Đăng nhập
              </Link>
            )}
          </div>

          <div className="-mr-2 flex items-center sm:hidden">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="inline-flex items-center justify-center rounded-md p-2 text-muted-foreground hover:bg-muted hover:text-foreground focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary"
            >
              <span className="sr-only">Mở menu</span>
              {/* Menu Icon */}
              {!isOpen ? (
                <svg
                  className="h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth="1.5"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
                  />
                </svg>
              ) : (
                /* Close Icon */
                <svg
                  className="h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth="1.5"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {isOpen && (
        <div className="sm:hidden">
          <div className="space-y-1 pb-3 pt-2">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setIsOpen(false)}
                className={`block border-l-4 py-2 pl-3 pr-4 text-base font-medium ${
                  isActive(link.href)
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-transparent text-muted-foreground hover:border-border hover:bg-muted hover:text-foreground"
                }`}
              >
                {link.label}
              </Link>
            ))}
          </div>
          <div className="border-t border-border pb-3 pt-4">
            {user ? (
              <div className="space-y-1">
                <div className="px-4 py-2">
                  <div className="text-base font-medium text-foreground">
                    {user.display_name}
                  </div>
                  <div className="text-sm font-medium text-muted-foreground">
                    {user.email}
                  </div>
                </div>
                <Link
                  href="/profile"
                  onClick={() => setIsOpen(false)}
                  className="block px-4 py-2 text-base font-medium text-muted-foreground hover:bg-muted hover:text-foreground"
                >
                  Hồ sơ
                </Link>
                <button
                  onClick={() => {
                    logout();
                    setIsOpen(false);
                  }}
                  className="block w-full px-4 py-2 text-left text-base font-medium text-muted-foreground hover:bg-muted hover:text-foreground"
                >
                  Đăng xuất
                </button>
              </div>
            ) : (
              <div className="mt-3 space-y-1 px-4">
                <Link
                  href="/login"
                  onClick={() => setIsOpen(false)}
                  className="block rounded-md bg-primary px-4 py-2 text-center text-base font-medium text-primary-foreground hover:bg-primary/90"
                >
                  Đăng nhập
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
