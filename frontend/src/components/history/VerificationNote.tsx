"use client";

import { Info } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Honest epistemic disclaimer shown on pages whose interpretations are still
 * under source verification. Never alarmist; required for public_unverified
 * legacy content per spec 22.3.
 */
export default function VerificationNote({
  className,
  compact = false,
}: {
  className?: string;
  compact?: boolean;
}) {
  return (
    <aside
      aria-label="Ghi chú về kiểm chứng nguồn"
      className={cn(
        "flex items-start gap-3 rounded-lg border border-border/70 bg-secondary/50 px-4 text-sm leading-6 text-muted-foreground",
        compact ? "py-3" : "py-4",
        className,
      )}
    >
      <Info
        className="mt-0.5 h-4 w-4 shrink-0 text-primary"
        aria-hidden="true"
      />
      <p>
        Một số diễn giải trên trang này đang trong quá trình kiểm chứng nguồn.
        Các thông tin chưa được xác nhận được dán nhãn rõ ràng.
      </p>
    </aside>
  );
}