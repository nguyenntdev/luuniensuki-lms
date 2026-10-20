"use client";

import { useState } from "react";
import {
  BookMarked,
  Scroll,
  ShieldCheck,
  AlertTriangle,
  HelpCircle,
  Quote,
  Check,
  Copy,
  ExternalLink,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ClaimEvidence } from "@/lib/imperial/map-types";

interface ClaimsEvidenceListProps {
  claims: ClaimEvidence[];
  monumentName: string;
}

export function getEpistemicBadge(status: "verified" | "probable" | "disputed") {
  switch (status) {
    case "verified":
      return {
        label: "Đã xác thực (Chính sử)",
        icon: ShieldCheck,
        className: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-500/30",
      };
    case "probable":
      return {
        label: "Khả tín cao (Tư liệu thứ cấp)",
        icon: HelpCircle,
        className: "bg-sky-500/15 text-sky-700 dark:text-sky-400 border-sky-500/30",
      };
    case "disputed":
      return {
        label: "Còn ý kiến khác nhau",
        icon: AlertTriangle,
        className: "bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/30",
      };
  }
}

export default function ClaimsEvidenceList({
  claims,
  monumentName,
}: ClaimsEvidenceListProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  if (!claims || claims.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
        Đang đồng bộ hóa cơ sở dữ liệu luận điểm và nguồn sơ cấp cho công trình này.
      </div>
    );
  }

  const handleCopyCitation = (claim: ClaimEvidence) => {
    const text = `[Trích nguồn] ${claim.source_title}${claim.volume_or_chapter ? `, ${claim.volume_or_chapter}` : ""}: "${claim.citation || claim.assertion_vi}" (${claim.archival_unit || "Lưu trữ Quốc Sử Quán"})`;
    navigator.clipboard.writeText(text);
    setCopiedId(claim.id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <section aria-labelledby="claims-heading" className="space-y-6">
      <div className="flex items-center justify-between border-b border-border/70 pb-3">
        <div className="flex items-center gap-2.5">
          <BookMarked className="h-5 w-5 text-primary" />
          <h2 id="claims-heading" className="font-display text-xl font-bold tracking-tight text-foreground md:text-2xl">
            Luận điểm lịch sử & Nguồn tư liệu gốc
          </h2>
        </div>
        <span className="text-xs text-muted-foreground font-medium">
          {claims.length} luận điểm có chứng cứ
        </span>
      </div>

      <p className="text-sm text-muted-foreground leading-relaxed">
        Các khẳng định học thuật được truy nguyên từ chính văn các bộ quốc sử triều Nguyễn như{" "}
        <em>Đại Nam Thực Lục</em>, <em>Khâm Định Đại Nam Hội Điển Sự Lệ</em> và <em>Đại Nam Nhất Thống Chí</em>.
      </p>

      {/* Claims and Evidence Cards */}
      <div className="space-y-4">
        {claims.map((claim) => {
          const badge = getEpistemicBadge(claim.epistemic_status);
          const BadgeIcon = badge.icon;
          const isCopied = copiedId === claim.id;

          return (
            <div
              key={claim.id}
              className="rounded-xl border border-border/80 bg-card p-5 shadow-sm space-y-4 transition-all hover:border-primary/40 hover:shadow"
            >
              {/* Header: Title & Epistemic Status */}
              <div className="flex flex-wrap items-start justify-between gap-2 border-b border-border/50 pb-3">
                <div className="space-y-1 max-w-2xl">
                  <span className="text-[11px] font-mono uppercase tracking-wider text-primary font-semibold">
                    Luận điểm khoa học
                  </span>
                  <h3 className="font-display text-base font-bold text-foreground">
                    {claim.claim_title}
                  </h3>
                </div>

                <span
                  className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${badge.className}`}
                >
                  <BadgeIcon className="h-3.5 w-3.5" />
                  {badge.label}
                </span>
              </div>

              {/* Assertion Statement */}
              <div className="rounded-lg bg-secondary/30 p-3.5 text-sm text-foreground/90 leading-relaxed">
                <strong>Khẳng định:</strong> {claim.assertion_vi}
              </div>

              {/* Primary Source Citation Box */}
              <div className="relative rounded-lg border-l-4 border-primary bg-primary/5 p-4 text-xs space-y-2">
                <div className="flex items-center justify-between text-primary font-semibold">
                  <div className="flex items-center gap-1.5">
                    <Scroll className="h-4 w-4 shrink-0" />
                    <span>
                      {claim.source_title}
                      {claim.volume_or_chapter && ` • ${claim.volume_or_chapter}`}
                    </span>
                  </div>

                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 text-[11px] gap-1 text-primary hover:text-primary"
                    onClick={() => handleCopyCitation(claim)}
                    title="Sao chép trích dẫn sử liệu để làm bài tập"
                  >
                    {isCopied ? (
                      <>
                        <Check className="h-3 w-3 text-emerald-600" />
                        Đã chép
                      </>
                    ) : (
                      <>
                        <Copy className="h-3 w-3" />
                        Chép trích dẫn
                      </>
                    )}
                  </Button>
                </div>

                {claim.citation && (
                  <p className="text-foreground/85 italic leading-relaxed pl-2 border-l border-primary/20">
                    &ldquo;{claim.citation}&rdquo;
                  </p>
                )}

                <div className="flex flex-wrap items-center justify-between text-[11px] text-muted-foreground pt-1">
                  <span>
                    <strong>Cơ quan biên soạn / Lưu trữ:</strong>{" "}
                    {claim.archival_unit || "Quốc Sử Quán triều Nguyễn"}
                  </span>
                  {claim.notes && (
                    <span className="italic text-foreground/70">
                      Ghi chú: {claim.notes}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
