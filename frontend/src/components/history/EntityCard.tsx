"use client";

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  entityName,
  publicationStatusLabel,
  reliefNumberFromSlug,
  reliefThumbnailUrl,
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
  const num = reliefNumberFromSlug(entity.slug);
  const hanNom = entity.name_han_nom || entity.han_nom;
  const thumb = entity.thumbnail_url || reliefThumbnailUrl(entity.slug);

  return (
    <Link
      href={href}
      prefetch={false}
      className={cn(
        "heritage-card focus-card group flex flex-col overflow-hidden rounded-2xl border border-border/70 bg-card/70 p-4 transition-all duration-300 hover:-translate-y-1.5 hover:border-primary/50 hover:shadow-xl focus-visible:ring-2 focus-visible:ring-primary [content-visibility:auto] [contain-intrinsic-size:1px_300px]",
        className,
      )}
    >
      <div className="relative aspect-[16/10] w-full overflow-hidden rounded-xl bg-black mb-3.5">
        <img
          src={thumb}
          alt={name}
          loading="lazy"
          decoding="async"
          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent z-10" />

        {num ? (
          <span className="absolute left-2.5 top-2.5 z-20 rounded-md bg-black/80 px-2 py-0.5 text-[10px] font-bold text-white backdrop-blur-sm">
            #{num}
          </span>
        ) : null}

        {hanNom ? (
          <span className="absolute bottom-2.5 right-2.5 z-20 rounded-md bg-background/90 px-2 py-0.5 font-serif text-xs font-bold text-primary backdrop-blur-sm shadow-sm">
            {hanNom}
          </span>
        ) : null}
      </div>

      <div className="relative flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-display text-base font-bold text-foreground group-hover:text-primary transition-colors">
              {name}
            </span>
            {badge ? (
              <span className="rounded-md bg-primary/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-primary ring-1 ring-primary/30">
                {badge}
              </span>
            ) : null}
          </div>
          {entity.name_en ? (
            <div className="mt-0.5 truncate text-xs text-muted-foreground">
              {entity.name_en}
            </div>
          ) : null}
        </div>
        <ArrowUpRight
          className="h-4 w-4 shrink-0 text-muted-foreground transition group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-primary"
          aria-hidden="true"
        />
      </div>

      <div className="flex-1 mt-2">
        <p className="line-clamp-2 text-xs leading-relaxed text-muted-foreground">
          {summary || (
            <span className="italic">
              Chưa có phần tóm tắt — nội dung đang được soạn thảo.
            </span>
          )}
        </p>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-border/50 pt-3 text-[11px] text-muted-foreground">
        {entity.entity_type === "relief" ? (
          <span className="rounded-md border border-border/60 bg-secondary/60 px-2 py-0.5">
            {urnNameFromSlug(entity.urn_slug || entity.slug)}
          </span>
        ) : null}
        {pubLabel ? (
          <span className="rounded-md border border-border/60 bg-secondary/60 px-2 py-0.5">
            {pubLabel}
          </span>
        ) : null}
      </div>
    </Link>
  );
}