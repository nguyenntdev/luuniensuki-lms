"use client";

/**
 * CommandPalette — global quick-launcher (⌘K / Ctrl+K, or "/").
 *
 * Lets users jump to any page or any đỉnh (urn) instantly with fuzzy,
 * accent-insensitive search and full keyboard navigation. Mounted globally in
 * the root layout. Lazily loads the urn list the first time it opens.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  Home,
  Compass,
  Brain,
  Sparkles,
  User,
  BookOpen,
  Globe,
  Trophy,
  Users,
  Clock,
  Medal,
  Mountain,
  CornerDownLeft,
} from "lucide-react";

import { getUrns } from "@/lib/api";

function deburr(s) {
  return String(s || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLowerCase();
}

const PAGE_COMMANDS = [
  { id: "p-dashboard", label: "Học tập", hint: "Bảng điều khiển", href: "/dashboard", icon: Home },
  { id: "p-explore", label: "Khám phá", hint: "Mở đỉnh và họa tiết", href: "/explore", icon: Compass },
  { id: "p-practice", label: "Ôn tập", hint: "Phiên ngắn theo trí nhớ", href: "/practice", icon: Brain },
  { id: "p-ai", label: "Giáo viên AI", hint: "Hỏi đáp với gia sư AI", href: "/ai", icon: Sparkles },
  { id: "p-vr360", label: "Tham quan ảo 360°", hint: "Đi dạo Hoàng thành Huế", href: "/vr360", icon: Globe },
  { id: "p-collection", label: "Bộ sưu tập", hint: "Họa tiết đã mở khóa", href: "/collection", icon: BookOpen },
  { id: "p-quests", label: "Hành trình", hint: "Nhiệm vụ và lộ trình", href: "/quests", icon: Compass },
  { id: "p-trails", label: "Lộ trình di sản", hint: "Chuỗi họa tiết theo chủ đề", href: "/trails", icon: Mountain },
  { id: "p-leaderboard", label: "Bảng xếp hạng", hint: "Thứ hạng người học", href: "/leaderboard", icon: Trophy },
  { id: "p-achievements", label: "Thành tích", hint: "Huy hiệu và cột mốc", href: "/achievements", icon: Medal },
  { id: "p-friends", label: "Bạn học", hint: "Kết nối bạn bè", href: "/friends", icon: Users },
  { id: "p-timeline", label: "Dòng thời gian", hint: "Lịch sử triều Nguyễn", href: "/timeline", icon: Clock },
  { id: "p-profile", label: "Cá nhân", hint: "Hồ sơ của bạn", href: "/profile", icon: User },
];

export default function CommandPalette() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const [urns, setUrns] = useState([]);
  const [urnsLoaded, setUrnsLoaded] = useState(false);
  const inputRef = useRef(null);
  const listRef = useRef(null);

  // Lazily load urns the first time the palette opens.
  useEffect(() => {
    if (!open || urnsLoaded) return;
    let cancelled = false;
    getUrns()
      .then((res) => {
        if (cancelled) return;
        const list = Array.isArray(res) ? res : res?.urns || [];
        setUrns(list);
        setUrnsLoaded(true);
      })
      .catch(() => setUrnsLoaded(true));
    return () => {
      cancelled = true;
    };
  }, [open, urnsLoaded]);

  // Global hotkeys: ⌘K / Ctrl+K toggles; "/" opens when not typing elsewhere.
  useEffect(() => {
    function onKey(e) {
      const k = e.key?.toLowerCase();
      const inField =
        ["input", "textarea", "select"].includes(e.target?.tagName?.toLowerCase()) ||
        e.target?.isContentEditable;
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
    const urnCmds = urns
      .filter((u) => u?.slug)
      .map((u) => ({
        id: `u-${u.slug}`,
        label: u.name || u.slug,
        hint: `Đỉnh · ${u.motif_count ?? 0} họa tiết`,
        href: `/urns/${u.slug}`,
        icon: Mountain,
      }));
    const all = [...PAGE_COMMANDS, ...urnCmds];
    const q = deburr(query.trim());
    if (!q) return all;
    return all.filter((c) => deburr(`${c.label} ${c.hint}`).includes(q));
  }, [urns, query]);

  useEffect(() => {
    setActive((a) => Math.min(a, Math.max(0, results.length - 1)));
  }, [results.length]);

  const go = useCallback(
    (cmd) => {
      if (!cmd) return;
      setOpen(false);
      router.push(cmd.href);
    },
    [router],
  );

  const onInputKey = (e) => {
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
            placeholder="Tìm trang hoặc đỉnh… (vd: cao đỉnh, ôn tập, 360)"
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
