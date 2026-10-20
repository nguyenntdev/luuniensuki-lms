"use client";

import React from "react";
import Link from "next/link";
import { Lock, Sparkles } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

export default function ArtDetailStudioLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const status = useAuthStore((s) => s.status);
  const user = useAuthStore((s) => s.user);

  const isStaffOrAdmin =
    Boolean(user) &&
    ["admin", "super_admin", "staff", "editor", "reviewer"].includes(
      user?.role || "",
    );

  if (status === "checking") {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-stone-950 p-6">
        <div className="space-y-4 w-full max-w-md text-center">
          <Skeleton className="h-10 w-48 mx-auto rounded-xl bg-stone-800" />
          <Skeleton className="h-4 w-72 mx-auto rounded-lg bg-stone-800" />
          <Skeleton className="h-48 w-full rounded-2xl bg-stone-900" />
        </div>
      </div>
    );
  }

  // Allow in non-production or for staff/admin
  if (process.env.NODE_ENV === "production" && (status === "unauth" || !user || !isStaffOrAdmin)) {
    return (
      <div className="flex min-h-[80vh] w-full items-center justify-center p-6 bg-background">
        <div className="max-w-md w-full p-8 rounded-3xl bg-card border border-border shadow-2xl text-center space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary mx-auto">
            <Lock className="w-7 h-7" />
          </div>
          <h2 className="text-xl font-bold font-serif text-foreground">
            Yêu cầu xác thực tài khoản
          </h2>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Studio Biên tập Chi tiết Mỹ thuật & Manh mối Điểm ghim yêu cầu quyền biên tập viên di sản. Vui lòng đăng nhập với tài khoản Quản trị viên hoặc Cán bộ chuyên môn.
          </p>
          <div className="pt-2 flex justify-center gap-3">
            <Link href="/login">
              <Button size="sm">Đăng nhập ngay</Button>
            </Link>
            <Link href="/dai-noi">
              <Button variant="outline" size="sm">Về Đại Nội</Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
