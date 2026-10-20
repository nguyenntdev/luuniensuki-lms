"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Lock, ShieldAlert, Sparkles } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

export default function AnnotateAdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const status = useAuthStore((s) => s.status);
  const user = useAuthStore((s) => s.user);

  const isStaffOrAdmin =
    Boolean(user) &&
    ["admin", "super_admin", "staff", "editor", "reviewer"].includes(
      user?.role || "",
    );

  // If unauthenticated or checked
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

  if (status === "unauth" || !user) {
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
            Studio Biên tập Bản đồ Không ảnh Đại Nội Huế yêu cầu quyền biên soạn nội dung. Vui lòng đăng nhập với tài khoản Quản trị viên hoặc Cán bộ chuyên môn.
          </p>
          <div className="pt-2">
            <Button asChild className="w-full text-xs font-semibold">
              <Link href="/login?returnUrl=/admin/dai-noi/annotate">
                Đăng nhập ngay
              </Link>
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!isStaffOrAdmin) {
    return (
      <div className="flex min-h-[80vh] w-full items-center justify-center p-6 bg-background">
        <div className="max-w-md w-full p-8 rounded-3xl bg-card border border-border shadow-2xl text-center space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-destructive/10 border border-destructive/20 flex items-center justify-center text-destructive mx-auto">
            <ShieldAlert className="w-7 h-7" />
          </div>
          <h2 className="text-xl font-bold font-serif text-foreground">
            Từ chối quyền truy cập (403)
          </h2>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Tài khoản hiện tại ({user.email}) chưa được phân quyền biên tập bản đồ. Cần có vai trò Staff hoặc Admin để truy cập công cụ này.
          </p>
          <div className="pt-2">
            <Button asChild variant="outline" className="w-full text-xs font-semibold">
              <Link href="/dai-noi">
                Trở về Bản đồ công khai
              </Link>
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
