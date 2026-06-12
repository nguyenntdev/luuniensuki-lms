"use client";

/**
 * EmptyState — a small, consistent empty/zero-data placeholder used across
 * pages. Optional icon, title, description, and a single action (Link or button).
 */

import * as React from "react";
import Link from "next/link";

export interface EmptyStateProps {
  icon?: React.ComponentType<{ className?: string }>;
  title?: React.ReactNode;
  description?: React.ReactNode;
  actionHref?: string;
  actionLabel?: React.ReactNode;
  onAction?: () => void;
}

export default function EmptyState({
  icon: Icon,
  title,
  description,
  actionHref,
  actionLabel,
  onAction,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border/70 bg-card/45 px-6 py-12 text-center">
      {Icon ? (
        <span className="mb-3 grid h-12 w-12 place-items-center rounded-2xl bg-secondary/60 text-muted-foreground">
          <Icon className="h-6 w-6" />
        </span>
      ) : null}
      {title ? (
        <h3 className="font-display text-base font-semibold text-foreground">
          {title}
        </h3>
      ) : null}
      {description ? (
        <p className="mt-1 max-w-md text-sm text-muted-foreground">
          {description}
        </p>
      ) : null}
      {actionHref && actionLabel ? (
        <Link
          href={actionHref}
          className="mt-4 inline-flex items-center rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
        >
          {actionLabel}
        </Link>
      ) : onAction && actionLabel ? (
        <button
          type="button"
          onClick={onAction}
          className="mt-4 inline-flex items-center rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
        >
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}
