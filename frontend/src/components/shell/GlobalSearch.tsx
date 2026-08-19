"use client";

import { useEffect, useRef, useState } from "react";
import type { KeyboardEvent as ReactKeyboardEvent } from "react";
import { useRouter } from "next/navigation";
import { CornerDownLeftIcon, Loader2Icon, SearchIcon } from "lucide-react";

import { searchHistory } from "@/lib/api";
import {
  asSearchItems,
  urnNameFromSlug,
  urnSlugFromReliefSlug,
  type HistorySearchItem,
} from "@/lib/history";
import { cn } from "@/lib/utils";

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

interface SearchResult {
  id: string;
  label: string;
  hint: string;
  href: string;
}

function toResult(item: HistorySearchItem): SearchResult {
  const slug = String(item.slug || "");
  const urn = urnSlugFromReliefSlug(slug);
  const type = String(item.entity_type || "").toLowerCase();
  const label = item.name_vi || item.name_en || slug || "Kết quả tìm kiếm";
  if (type === "urn") {
    return {
      id: `urn-${item.id ?? slug}`,
      label,
      hint: "Đỉnh đồng · Cửu Đỉnh",
      href: `/cuu-dinh/${slug}`,
    };
  }
  if (type === "relief") {
    return {
      id: `relief-${item.id ?? slug}`,
      label,
      hint: `Phù điêu · ${urnNameFromSlug(urn)}`,
      href: `/atlas/${urn}/${slug}`,
    };
  }
  if (type === "source") {
    return {
      id: `source-${item.id ?? slug}`,
      label,
      hint: "Nguồn sử liệu",
      href: `/sources/${item.id}`,
    };
  }
  return {
    id: `entity-${item.id ?? slug}`,
    label,
    hint: "Thực thể lịch sử",
    href: `/explore/connections?entity=${encodeURIComponent(slug)}`,
  };
}

export default function GlobalSearch() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    const timer = window.setTimeout(() => {
      const q = query.trim();
      if (!q) {
        if (!cancelled) {
          setResults([]);
          setLoading(false);
        }
        return;
      }
      setLoading(true);
      searchHistory(q, 10)
        .then((res) => {
          if (cancelled) return;
          const items = asSearchItems(res)
            .map(toResult)
            .slice(0, 8);
          setResults(items);
          setActive(0);
        })
        .catch(() => {
          if (!cancelled) setResults([]);
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    }, 250);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [open, query]);

  useEffect(() => {
    if (!open) return;
    const el = listRef.current?.querySelector(`[data-idx="${active}"]`);
    el?.scrollIntoView({ block: "nearest" });
  }, [active, open]);

  useEffect(() => {
    if (!open) return;
    setQuery("");
    setResults([]);
    setActive(0);
    setLoading(false);
  }, [open]);

  function go(result: SearchResult | undefined) {
    if (!result) return;
    setOpen(false);
    router.push(result.href);
  }

  function onInputKey(e: ReactKeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((a) => Math.min(a + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((a) => Math.max(a - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      go(results[active]);
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="inline-flex h-9 items-center gap-2 rounded-lg border border-border/70 bg-secondary/40 px-3 text-xs font-medium text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
        aria-label="Tìm kiếm toàn di sản"
        title="Tìm kiếm toàn di sản"
      >
        <SearchIcon className="h-4 w-4 shrink-0" aria-hidden="true" />
        <span className="hidden lg:inline">Tìm kiếm</span>
        <kbd className="hidden rounded border border-border px-1 font-sans text-[10px] lg:inline">
          ⌘K
        </kbd>
      </button>

      <DialogContent className="gap-0 overflow-hidden p-0 sm:max-w-lg">
        <DialogHeader className="border-b border-border px-4 py-3">
          <DialogTitle className="sr-only">Tìm kiếm toàn di sản</DialogTitle>
          <div className="flex items-center gap-3">
            <SearchIcon className="h-5 w-5 shrink-0 text-muted-foreground" aria-hidden="true" />
            <Input
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setActive(0);
              }}
              onKeyDown={onInputKey}
              autoFocus
              placeholder="Tìm đỉnh, phù điêu, nguồn… (vd: cao đỉnh)"
              aria-label="Từ khóa tìm kiếm"
              className="h-9 border-0 bg-transparent px-0 shadow-none focus-visible:ring-0 focus-visible:bg-transparent"
            />
            {loading ? (
              <Loader2Icon className="h-4 w-4 shrink-0 animate-spin text-muted-foreground" aria-hidden="true" />
            ) : null}
            <kbd className="hidden rounded border border-border px-1.5 py-0.5 text-[10px] text-muted-foreground sm:inline">
              ESC
            </kbd>
          </div>
        </DialogHeader>

        <div ref={listRef} className="max-h-[52vh] overflow-y-auto py-2">
          {query.trim() === "" ? (
            <p className="px-4 py-8 text-center text-sm text-muted-foreground">
              Nhập từ khóa để tìm đỉnh, phù điêu, nguồn sử liệu và thực thể lịch sử.
            </p>
          ) : results.length === 0 && !loading ? (
            <p className="px-4 py-8 text-center text-sm text-muted-foreground">
              Không tìm thấy kết quả cho “{query}”.
            </p>
          ) : (
            results.map((result, idx) => {
              const isActive = idx === active;
              return (
                <button
                  key={result.id}
                  type="button"
                  data-idx={idx}
                  onMouseEnter={() => setActive(idx)}
                  onClick={() => go(result)}
                  className={cn(
                    "flex w-full items-center gap-3 px-4 py-2.5 text-left transition-colors",
                    isActive
                      ? "bg-primary/12 text-foreground"
                      : "text-muted-foreground hover:bg-secondary/60",
                  )}
                >
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium text-foreground">
                      {result.label}
                    </span>
                    <span className="block truncate text-xs text-muted-foreground">
                      {result.hint}
                    </span>
                  </span>
                  {isActive ? (
                    <CornerDownLeftIcon className="h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
                  ) : null}
                </button>
              );
            })
          )}
        </div>

        <div className="flex items-center justify-between border-t border-border px-4 py-2 text-[11px] text-muted-foreground">
          <span>↑↓ di chuyển · ↵ mở · ESC đóng</span>
          <span>⌘K / Ctrl+K</span>
        </div>
      </DialogContent>
    </Dialog>
  );
}