import * as React from "react";
import Link from "next/link";
import { ChevronRightIcon } from "lucide-react";

import { cn } from "@/lib/utils";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

function Breadcrumb({
  items,
  className,
  ...props
}: React.ComponentProps<"nav"> & { items: BreadcrumbItem[] }) {
  return (
    <nav
      aria-label="Đường dẫn trang"
      className={cn(
        "flex items-center text-sm text-muted-foreground",
        className,
      )}
      {...props}
    >
      <ol className="flex flex-wrap items-center gap-1.5">
        {items.map((item, idx) => {
          const isLast = idx === items.length - 1;
          return (
            <li key={`${item.label}-${idx}`} className="flex items-center gap-1.5">
              {item.href && !isLast ? (
                <Link
                  href={item.href}
                  className="transition-colors hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 focus-visible:outline-none"
                >
                  {item.label}
                </Link>
              ) : (
                <span
                  aria-current={isLast ? "page" : undefined}
                  className={cn(isLast && "font-medium text-foreground")}
                >
                  {item.label}
                </span>
              )}
              {!isLast ? (
                <ChevronRightIcon
                  className="h-3.5 w-3.5 text-muted-foreground/60"
                  aria-hidden="true"
                />
              ) : null}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

export { Breadcrumb };