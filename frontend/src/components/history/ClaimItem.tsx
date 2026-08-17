"use client";

import { FileText } from "lucide-react";
import { cn } from "@/lib/utils";
import EpistemicLabel from "@/components/history/EpistemicLabel";
import {
  claimEpistemic,
  claimText,
  claimTypeLabel,
  verificationStatusLabel,
  type HistoryClaim,
} from "@/lib/history";

export default function ClaimItem({
  claim,
  className,
}: {
  claim: HistoryClaim;
  className?: string;
}) {
  const text = claimText(claim);
  const epistemic = claimEpistemic(claim);

  return (
    <article
      className={cn(
        "rounded-lg border border-border bg-card/60 px-5 py-4",
        className,
      )}
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className="inline-flex items-center gap-1.5 rounded-md bg-muted/70 px-2 py-0.5 text-[11px] font-semibold text-muted-foreground uppercase tracking-wide">
          <FileText className="h-3 w-3" aria-hidden="true" />
          {claimTypeLabel(claim.claim_type)}
        </span>
        <EpistemicLabel info={epistemic} />
        {claim.verification_status ? (
          <span className="text-[11px] text-muted-foreground">
            {verificationStatusLabel(claim.verification_status)}
          </span>
        ) : null}
      </div>

      {text ? (
        <p className="mt-3 text-sm leading-7 text-foreground/90">{text}</p>
      ) : (
        <p className="mt-3 text-sm italic leading-7 text-muted-foreground">
          Chưa có nội dung chi tiết cho nhận định này.
        </p>
      )}

      {claim.confidence != null && claim.confidence !== "" ? (
        <p className="mt-2 text-[11px] text-muted-foreground">
          Độ tin cậy: <span className="font-medium">{String(claim.confidence)}</span>
        </p>
      ) : null}
    </article>
  );
}