"use client";

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  entityName,
  publicationStatusLabel,
  urnNameFromSlug,
  type HistoryEntity,
} from "@/lib/history";

function firstSentence(text: string | null | undefined): string {
  const t = String(text || "").trim();
  if (!t) return "";
  const idx = t.indexOf(".");
  return (idx > 0 ? t.slice(0, idx + 1) : t).trim();
}

export default function EntityCard({
  entity,
  href,
  badge,
  className,
}: {
  entity: HistoryEntity;
  href: string;
  badge?: string;
  className?: string;
}) {
  const name = entityName(entity);
  const summary = firstSentence(
    entity.summary_vi || entity.summary || entity.summary_en,
  );
  const pubLabel = publicationStatusLabel(entity.publication_status);

  return (
    <Link
      href={href}
      className={cn(
        "heritage-card group flex flex-col gap-4 p-5 outline-none transition duration-200 hover:border-primary/40 focus-visible:ring-2 focus-visible:ring-primary",
        className,
      )}
    >
      <div className="relative flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-display text-lg font-semibold text-foreground">
              {name}
            </span>
            {badge ? (
              <span className="rounded-md bg-primary/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-primary ring-1 ring-primary/30">
                {badge}
              </span>
            ) : null}
          </div>
          {entity.name_en ? (
            <div className="mt-1 truncate text-xs text-muted-foreground">
              {entity.name_en}
            </div>
          ) : null}
          {entity.slug ? (
            <div className="mt-1 text-[11px] text-muted-foreground/70">
              {entity.slug}
            </div>
          ) : null}
        </div>
        <ArrowUpRight
          className="h-4 w-4 shrink-0 text-muted-foreground transition group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-primary"
          aria-hidden="true"
        />
      </div>

      <div className="flex-1">
        <p className="line-clamp-3 text-sm leading-6 text-muted-foreground">
          {summary || (
            <span className="italic">
              Chưa có phần tóm tắt — nội dung đang được soạn thảo.
            </span>
          )}
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
        {entity.entity_type === "relief" ? (
          <span className="rounded-md border border-border/60 bg-background/70 px-2 py-0.5">
            {urnNameFromSlug(entity.urn_slug || entity.slug)}
          </span>
        ) : null}
        {pubLabel ? (
          <span className="rounded-md border border-border/60 bg-background/70 px-2 py-0.5">
            {pubLabel}
          </span>
        ) : null}
      </div>
    </Link>
  );
}