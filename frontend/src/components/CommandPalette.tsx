"use client";

/**
 * CommandPalette — global quick-launcher (⌘K / Ctrl+K, or "/").
 *
 * Lets users jump to any page or any đỉnh (urn) instantly with fuzzy,
 * accent-insensitive search and full keyboard navigation. Mounted globally in
 * the root layout. Lazily loads the urn list the first time it opens.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { KeyboardEvent as ReactKeyboardEvent } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  Compass,
  BookOpen,
  Clock,
  GraduationCap,
  Landmark,
  LayoutGrid,
  Library,
  Map,
  Mountain,
  CornerDownLeft,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { getUrns, searchHistory } from "@/lib/api";
import {
  asSearchItems,
  urnNameFromSlug,
  urnSlugFromReliefSlug,
  type HistorySearchItem,
} from "@/lib/history";

interface Command {
  id: string;
  label: string;
  hint: string;
  href: string;
  icon: LucideIcon;
}

interface UrnSummary {
  slug?: string;
  name?: string;
  motif_count?: number;
  [key: string]: unknown;
}

function deburr(s: unknown): string {
  return String(s || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLowerCase();
}

const PAGE_COMMANDS: Command[] = [
  { id: "p-cuu-dinh", label: "Cửu Đỉnh", hint: "Chín chiếc đỉnh đồng triều Nguyễn", href: "/cuu-dinh", icon: Landmark },
  { id: "p-atlas", label: "Atlas 162", hint: "Toàn bộ phù điêu theo không gian", href: "/atlas", icon: LayoutGrid },
  { id: "p-explore", label: "Khám phá", hint: "Trung tâm khám phá di sản", href: "/explore", icon: Compass },
  { id: "p-sources", label: "Nguồn", hint: "Kho tư liệu và nguồn sử liệu", href: "/sources", icon: Library },
  { id: "p-map", label: "Bản đồ", hint: "Định vị di sản theo không gian", href: "/map", icon: Map },
  { id: "p-timeline", label: "Dòng thời gian", hint: "Lịch sử triều Nguyễn theo niên đại", href: "/timeline", icon: Clock },
  { id: "p-stories", label: "Câu chuyện", hint: "Bài viết và hành trình di sản", href: "/stories", icon: BookOpen },
  { id: "p-dashboard", label: "Học của tôi", hint: "Bảng điều khiển người học", href: "/dashboard", icon: GraduationCap },
];

export default function CommandPalette() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const [urns, setUrns] = useState<UrnSummary[]>([]);
  const [urnsLoaded, setUrnsLoaded] = useState(false);
  const [historyResults, setHistoryResults] = useState<HistorySearchItem[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const searchTimerRef = useRef<number | null>(null);
  const lastSearchRef = useRef("");

  // Lazily load urns the first time the palette opens.
  useEffect(() => {
    if (!open || urnsLoaded) return;
    let cancelled = false;
    getUrns()
      .then((res) => {
        if (cancelled) return;
        const data = res as { urns?: UrnSummary[] } | UrnSummary[] | null;
        const list = Array.isArray(data) ? data : data?.urns || [];
        setUrns(list);
        setUrnsLoaded(true);
      })
      .catch(() => setUrnsLoaded(true));
    return () => {
      cancelled = true;
    };
  }, [open, urnsLoaded]);

  // Debounced history-entity search, surfaced as top results (spec 29).
  useEffect(() => {
    if (!open) return undefined;
    const q = query.trim();
    if (searchTimerRef.current) window.clearTimeout(searchTimerRef.current);
    if (!q) {
      setHistoryResults([]);
      lastSearchRef.current = "";
      return undefined;
    }
    if (q === lastSearchRef.current) return undefined;
    lastSearchRef.current = q;
    setHistoryResults([]);
    let cancelled = false;
    searchTimerRef.current = window.setTimeout(() => {
      searchHistory(q, 20)
        .then((res) => {
          if (!cancelled) setHistoryResults(asSearchItems(res));
        })
        .catch(() => {
          if (!cancelled) setHistoryResults([]);
        });
    }, 250);
    return () => {
      cancelled = true;
      if (searchTimerRef.current) window.clearTimeout(searchTimerRef.current);
    };
  }, [open, query]);

  // Global hotkeys: ⌘K / Ctrl+K toggles; "/" opens when not typing elsewhere.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const k = e.key?.toLowerCase();
      const target = e.target as HTMLElement | null;
      const inField =
        ["input", "textarea", "select"].includes(
          target?.tagName?.toLowerCase() ?? "",
        ) || target?.isContentEditable;
      if ((e.metaKey || e.ctrlKey) && k === "k") {
        e.preventDefault();
        setOpen((v) => !v);
      } else if (k === "/" && !inField && !open) {
        e.preventDefault();
        setOpen(true);
      } else if (k === "escape" && open) {
        setOpen(false);
      }
    }
    window.addEventListener("keydown", onKey);
    const openEvt = () => setOpen(true);
    window.addEventListener("open-command-palette", openEvt);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("open-command-palette", openEvt);
    };
  }, [open]);

  useEffect(() => {
    if (open) {
      setQuery("");
      setActive(0);
      // focus after the dialog paints
      const t = setTimeout(() => inputRef.current?.focus(), 30);
      return () => clearTimeout(t);
    }
    return undefined;
  }, [open]);

  const results = useMemo(() => {
    const urnCmds: Command[] = urns
      .filter((u) => u?.slug)
      .map((u) => ({
        id: `u-${u.slug}`,
        label: u.name || u.slug || "",
        hint: `Đỉnh · ${u.motif_count ?? 0} họa tiết`,
        href: `/urns/${u.slug}`,
        icon: Mountain,
      }));

    const historyCmds: Command[] = historyResults.map((item) => {
      const slug = item.slug || "";
      const urn = urnSlugFromReliefSlug(slug);
      const type = String(item.entity_type || "").toLowerCase();
      let href = "/timeline";
      let icon: LucideIcon = Clock;
      let hint = "Kết quả lịch sử";
      if (type === "urn") {
        href = `/cuu-dinh/${slug}`;
        icon = Landmark;
        hint = "Đỉnh đồng · Cửu Đỉnh";
      } else if (type === "relief") {
        href = `/atlas/${urn}/${slug}`;
        icon = BookOpen;
        hint = `Phù điêu · ${urnNameFromSlug(urn)}`;
      } else if (type === "source") {
        href = `/sources/${item.id}`;
        icon = Library;
        hint = "Nguồn sử liệu";
      } else if (slug) {
        href = `/atlas/${urn}/${slug}`;
        icon = BookOpen;
        hint = type || "Thực thể lịch sử";
      }
      return {
        id: `h-${item.id ?? slug}`,
        label: item.name_vi || item.name_en || slug || "Kết quả lịch sử",
        hint,
        href,
        icon,
      };
    });

    const all = [...historyCmds, ...PAGE_COMMANDS, ...urnCmds];
    const q = deburr(query.trim());
    if (!q) return all;
    return all.filter((c) => deburr(`${c.label} ${c.hint}`).includes(q));
  }, [urns, query, historyResults]);

  useEffect(() => {
    setActive((a) => Math.min(a, Math.max(0, results.length - 1)));
  }, [results.length]);

  const go = useCallback(
    (cmd: Command | undefined) => {
      if (!cmd) return;
      setOpen(false);
      router.push(cmd.href);
    },
    [router],
  );

  const onInputKey = (e: ReactKeyboardEvent<HTMLInputElement>) => {
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
  };

  // Keep the active row scrolled into view.
  useEffect(() => {
    const el = listRef.current?.querySelector(`[data-idx="${active}"]`);
    el?.scrollIntoView({ block: "nearest" });
  }, [active]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-start justify-center px-4 pt-[12vh]"
      role="dialog"
      aria-modal="true"
      aria-label="Bảng lệnh nhanh"
    >
      <div className="absolute inset-0 bg-background/70 backdrop-blur-sm" onClick={() => setOpen(false)} />
      <div className="relative w-full max-w-xl overflow-hidden rounded-2xl border border-border bg-card shadow-elegant">
        <div className="flex items-center gap-3 border-b border-border px-4 py-3">
          <Search className="h-5 w-5 shrink-0 text-muted-foreground" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setActive(0);
            }}
            onKeyDown={onInputKey}
            placeholder="Tìm đỉnh, phù điêu, nguồn hoặc trang… (vd: cao đỉnh, bản đồ)"
            className="w-full bg-transparent text-base text-foreground outline-none placeholder:text-muted-foreground"
            aria-label="Tìm kiếm"
          />
          <kbd className="hidden rounded border border-border px-1.5 py-0.5 text-[10px] text-muted-foreground sm:inline">
            ESC
          </kbd>
        </div>

        <div ref={listRef} className="max-h-[52vh] overflow-y-auto py-2">
          {results.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-muted-foreground">
              Không tìm thấy kết quả cho “{query}”.
            </div>
          ) : (
            results.map((cmd, idx) => {
              const Icon = cmd.icon || Compass;
              const isActive = idx === active;
              return (
                <button
                  key={cmd.id}
                  type="button"
                  data-idx={idx}
                  onMouseEnter={() => setActive(idx)}
                  onClick={() => go(cmd)}
                  className={`flex w-full items-center gap-3 px-4 py-2.5 text-left transition ${
                    isActive ? "bg-primary/12 text-foreground" : "text-muted-foreground hover:bg-secondary/60"
                  }`}
                >
                  <span
                    className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg ${
                      isActive ? "bg-primary/20 text-primary" : "bg-secondary text-muted-foreground"
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium text-foreground">{cmd.label}</span>
                    <span className="block truncate text-xs text-muted-foreground">{cmd.hint}</span>
                  </span>
                  {isActive ? <CornerDownLeft className="h-4 w-4 shrink-0 text-primary" /> : null}
                </button>
              );
            })
          )}
        </div>

        <div className="flex items-center justify-between border-t border-border px-4 py-2 text-[11px] text-muted-foreground">
          <span>↑↓ di chuyển · ↵ mở · ESC đóng</span>
          <span>⌘K / Ctrl+K</span>
        </div>
      </div>
    </div>
  );
}
