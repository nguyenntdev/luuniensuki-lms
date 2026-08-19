"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  AlertCircle,
  ArrowRight,
  Boxes,
  Network,
  Search,
  Share2,
  X,
} from "lucide-react";

import {
  getHistoryEntityById,
  getHistoryEntityBySlug,
  getHistoryGraph,
  listHistoryEntities,
  searchHistory,
} from "@/lib/api";
import {
  KNOWN_URNS,
  asEntityList,
  asSearchItems,
  entityName,
  entityTypeLabel,
  publicationEpistemic,
  relationPredicateLabel,
  urnSlugFromReliefSlug,
  verificationStatusLabel,
} from "@/lib/history";
import { cn } from "@/lib/utils";
import Skeleton from "@/components/Skeleton";
import EpistemicLabel from "@/components/history/EpistemicLabel";
import VerificationNote from "@/components/history/VerificationNote";
import { Input } from "@/components/ui/input";

const TYPE_COLORS = {
  urn: "#8a5a2b",
  relief: "#d97706",
  place: "#2563eb",
  water_body: "#2563eb",
  mountain: "#2563eb",
  settlement: "#2563eb",
  region: "#2563eb",
  island: "#2563eb",
  person: "#7c3aed",
  event: "#dc2626",
  period: "#0d9488",
  source: "#52525b",
};
const DEFAULT_COLOR = "#6b7280";

const LEGEND_ITEMS = [
  { type: "urn", label: "Đỉnh" },
  { type: "relief", label: "Phù điêu" },
  { type: "place", label: "Địa danh" },
  { type: "person", label: "Nhân vật" },
  { type: "event", label: "Sự kiện" },
];

function colorForType(type) {
  const t = String(type || "").toLowerCase();
  return TYPE_COLORS[t] || DEFAULT_COLOR;
}

function toEntity(value) {
  return value && typeof value === "object" ? value : null;
}

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

async function resolveEntityRef(ref) {
  const raw = String(ref || "").trim();
  if (!raw) return null;
  if (UUID_RE.test(raw)) {
    try {
      const entity = toEntity(await getHistoryEntityById(raw));
      if (entity) return entity;
    } catch {
      // Fallback to slug search below if UUID fetch fails
    }
  }
  try {
    const bySlug = toEntity(await getHistoryEntityBySlug(raw));
    if (bySlug) return bySlug;
  } catch {
    // If slug fails and it might be an ID or search term
  }
  return null;
}

// Radial layout: root centered, 1-hop neighbors on an inner ring, 2-hop
// neighbors clustered around the ray of their parent on an outer ring. Pure
// SVG, no external graph library.
const RING_1 = 92;
const RING_2 = 172;

function computeLayout(nodes, edges, rootId) {
  const key = (id) => String(id);
  const rootKey = key(rootId);
  const nodeKeys = new Set(nodes.map((n) => key(n.id)));

  const pos = new Map();
  pos.set(rootKey, { x: 0, y: 0, depth: 0 });

  const adjacency = new Map();
  for (const e of edges) {
    const s = key(e.source);
    const t = key(e.target);
    if (!nodeKeys.has(s) || !nodeKeys.has(t)) continue;
    if (!adjacency.has(s)) adjacency.set(s, []);
    if (!adjacency.has(t)) adjacency.set(t, []);
    adjacency.get(s).push(t);
    adjacency.get(t).push(s);
  }

  const children = new Map();
  const visited = new Set([rootKey]);
  const queue = [rootKey];
  while (queue.length) {
    const cur = queue.shift();
    const curDepth = pos.get(cur)?.depth ?? 0;
    if (curDepth >= 2) continue;
    for (const nb of adjacency.get(cur) || []) {
      if (visited.has(nb)) continue;
      visited.add(nb);
      pos.set(nb, { x: 0, y: 0, depth: curDepth + 1 });
      if (!children.has(cur)) children.set(cur, []);
      children.get(cur).push(nb);
      queue.push(nb);
    }
  }

  const depth1 = (children.get(rootKey) || []).filter((id) => pos.has(id));
  depth1.forEach((id, i) => {
    const angle = (2 * Math.PI * i) / Math.max(depth1.length, 1) - Math.PI / 2;
    pos.set(id, {
      ...pos.get(id),
      x: RING_1 * Math.cos(angle),
      y: RING_1 * Math.sin(angle),
      depth: 1,
    });
  });

  for (const [pid, kids] of children) {
    if (pid === rootKey) continue;
    const p = pos.get(pid);
    if (!p || p.depth !== 1) continue;
    const parentAngle = Math.atan2(p.y, p.x);
    const list = kids.filter((id) => pos.get(id)?.depth === 2);
    list.forEach((id, i) => {
      const spread = Math.min(0.55, Math.PI / 2 / Math.max(list.length, 1));
      const angle =
        parentAngle + (i - (list.length - 1) / 2) * spread;
      pos.set(id, {
        ...pos.get(id),
        x: RING_2 * Math.cos(angle),
        y: RING_2 * Math.sin(angle),
        depth: 2,
      });
    });
  }

  let extra = 0;
  for (const n of nodes) {
    const k = key(n.id);
    if (!pos.has(k)) {
      const col = extra % 5;
      const row = Math.floor(extra / 5);
      pos.set(k, { x: (col - 2) * 72, y: RING_2 + 64 + row * 56, depth: 2 });
      extra += 1;
    }
  }

  return pos;
}

function nodeHref(node) {
  const slug = String(node?.slug || "").trim();
  const type = String(node?.entity_type || "").toLowerCase();
  if (!slug) return null;
  if (type === "urn") return `/cuu-dinh/${slug}`;
  if (type === "relief") {
    return `/atlas/${urnSlugFromReliefSlug(slug)}/${slug}`;
  }
  return null;
}

function shortName(name, max = 20) {
  const s = String(name || "").trim();
  return s.length > max ? `${s.slice(0, max - 1)}…` : s;
}

function GraphSvg({
  nodes,
  edges,
  positions,
  rootId,
  selectedId,
  activeEdgeKey,
  onSelectNode,
  onActivateEdge,
  onDeactivateEdge,
  onNavigate,
}) {
  const nodeById = useMemo(
    () => new Map(nodes.map((n) => [String(n.id), n])),
    [nodes],
  );
  const rootKey = String(rootId);

  const bounds = useMemo(() => {
    const xs = [];
    const ys = [];
    for (const p of positions.values()) {
      xs.push(p.x);
      ys.push(p.y);
    }
    const minX = Math.min(-110, ...xs) - 50;
    const maxX = Math.max(110, ...xs) + 50;
    const minY = Math.min(-110, ...ys) - 50;
    const maxY = Math.max(110, ...ys) + 50;
    return { minX, minY, width: maxX - minX, height: maxY - minY };
  }, [positions]);

  const handleNodeKey = (e, node) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onNavigate(node);
    }
  };

  const handleEdgeKey = (e, edge, edgeKey) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onActivateEdge(edgeKey);
    }
  };

  return (
    <svg
      viewBox={`${bounds.minX} ${bounds.minY} ${bounds.width} ${bounds.height}`}
      className="h-auto w-full"
      role="img"
      aria-label="Sơ đồ mạng lưới liên kết của thực thể đang chọn"
    >
      {/* Edges */}
      {edges.map((edge) => {
        const sPos = positions.get(String(edge.source));
        const tPos = positions.get(String(edge.target));
        if (!sPos || !tPos) return null;
        const edgeKey = `${String(edge.source)}->${String(edge.target)}`;
        const active = activeEdgeKey === edgeKey;
        const label = relationPredicateLabel(edge.predicate);
        const midX = (sPos.x + tPos.x) / 2;
        const midY = (sPos.y + tPos.y) / 2;
        return (
          <g
            key={edgeKey}
            role="button"
            tabIndex={0}
            aria-label={`Liên kết: ${label}`}
            data-edge-key={edgeKey}
            onClick={() => onActivateEdge(edgeKey)}
            onMouseEnter={() => onActivateEdge(edgeKey)}
            onMouseLeave={onDeactivateEdge}
            onFocus={() => onActivateEdge(edgeKey)}
            onBlur={onDeactivateEdge}
            onKeyDown={(e) => handleEdgeKey(e, edge, edgeKey)}
            className="cursor-pointer outline-none focus-visible:opacity-100"
          >
            <line
              x1={sPos.x}
              y1={sPos.y}
              x2={tPos.x}
              y2={tPos.y}
              stroke={active ? "#8a5a2b" : "#b7ad99"}
              strokeWidth={active ? 2.5 : 1.5}
              strokeDasharray={active ? undefined : "5 4"}
            />
            <title>{label}</title>
            {active ? (
              <text
                x={midX}
                y={midY - 8}
                textAnchor="middle"
                fontSize="11"
                fontWeight="600"
                fill="#57534e"
                paintOrder="stroke"
                stroke="hsl(var(--card))"
                strokeWidth="4"
                strokeLinejoin="round"
                className="pointer-events-none select-none"
              >
                {label}
              </text>
            ) : null}
          </g>
        );
      })}

      {/* Nodes */}
      {nodes.map((node) => {
        const key = String(node.id);
        const p = positions.get(key);
        if (!p) return null;
        const isRoot = key === rootKey;
        const selected = selectedId != null && String(selectedId) === key;
        const color = colorForType(node.entity_type);
        const name = entityName(node);
        const typeLabel = entityTypeLabel(node.entity_type);
        return (
          <g
            key={key}
            role="button"
            tabIndex={0}
            aria-label={`${name} (${typeLabel})${isRoot ? " — thực thể trung tâm" : ""}. Enter để mở.`}
            data-node-id={key}
            onClick={() => onNavigate(node)}
            onMouseEnter={() => onSelectNode(node.id)}
            onFocus={() => onSelectNode(node.id)}
            onKeyDown={(e) => handleNodeKey(e, node)}
            className="cursor-pointer outline-none"
            style={{ opacity: selected ? 1 : 0.85 }}
          >
            <circle
              cx={p.x}
              cy={p.y}
              r={isRoot ? 16 : 10}
              fill={color}
              opacity={selected ? 1 : 0.9}
              stroke={selected ? "#f5f0e6" : "rgba(0,0,0,0.18)"}
              strokeWidth={selected ? 3 : 1}
            />
            {isRoot ? (
              <circle
                cx={p.x}
                cy={p.y}
                r={22}
                fill="none"
                stroke={color}
                strokeWidth={1.5}
                strokeDasharray="3 3"
              />
            ) : null}
            <text
              x={p.x}
              y={p.y + (isRoot ? 34 : 26)}
              textAnchor="middle"
              fontSize="11"
              fill="#44403c"
              paintOrder="stroke"
              stroke="hsl(var(--card))"
              strokeWidth="3"
              strokeLinejoin="round"
              className="pointer-events-none select-none"
            >
              {shortName(name)}
            </text>
            <title>{`${name} — ${typeLabel}`}</title>
          </g>
        );
      })}
    </svg>
  );
}

export default function ConnectionsPage() {
  const router = useRouter();
  const [entityRef, setEntityRef] = useState(null);
  const [root, setRoot] = useState(null);
  const [graph, setGraph] = useState(null);
  const [depth, setDepth] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [activeEdgeKey, setActiveEdgeKey] = useState(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [urns, setUrns] = useState([]);
  const searchTimer = useRef(null);

  useEffect(() => {
    const ref = (() => {
      if (typeof window === "undefined") return null;
      const p = new URLSearchParams(window.location.search);
      const v = p.get("entity");
      return v ? String(v).trim() : null;
    })();
    setEntityRef(ref);
  }, []);

  useEffect(() => {
    document.title = "Mạng lưới liên kết — Lưu Niên Sử Kí";
  }, []);

  useEffect(() => {
    let cancelled = false;
    listHistoryEntities({ entityType: "urn", limit: 20 })
      .then((res) => {
        if (!cancelled) setUrns(asEntityList(res));
      })
      .catch(() => {
        // Fall back to the known nine urns (slug-only) if the API is down.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!entityRef) {
      setRoot(null);
      setGraph(null);
      setSelectedId(null);
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    setGraph(null);
    (async () => {
      try {
        const entity = await resolveEntityRef(entityRef);
        if (cancelled) return;
        if (!entity || entity.id == null) {
          setError("Không tìm thấy thực thể để vẽ mạng lưới. Vui lòng chọn thực thể khác.");
          setRoot(null);
          return;
        }
        setRoot(entity);
        const g = await getHistoryGraph(entity.id, depth);
        if (cancelled) return;
        setGraph(g);
        setSelectedId(entity.id);
        setActiveEdgeKey(null);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Không tải được mạng lưới liên kết.",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [entityRef, depth]);

  useEffect(() => {
    return () => {
      if (searchTimer.current) window.clearTimeout(searchTimer.current);
    };
  }, []);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setSearchOpen(false);
      setSearchLoading(false);
      setSearchError(null);
      return;
    }
    if (searchTimer.current) window.clearTimeout(searchTimer.current);
    searchTimer.current = window.setTimeout(async () => {
      setSearchLoading(true);
      setSearchError(null);
      try {
        const res = await searchHistory(query.trim(), 10);
        setResults(asSearchItems(res).slice(0, 10));
        setSearchOpen(true);
      } catch (err) {
        setSearchError(
          err instanceof Error ? err.message : "Không tìm thấy kết quả.",
        );
        setResults([]);
      } finally {
        setSearchLoading(false);
      }
    }, 250);
    return undefined;
  }, [query]);

  const nodes = useMemo(() => {
    const list = Array.isArray(graph?.nodes) ? graph.nodes : [];
    return list.filter((n) => n && n.id != null);
  }, [graph]);

  const edges = useMemo(() => {
    const list = Array.isArray(graph?.edges) ? graph.edges : [];
    return list.filter((e) => e && e.source != null && e.target != null);
  }, [graph]);

  const positions = useMemo(() => {
    if (!root) return new Map();
    return computeLayout(nodes, edges, root.id);
  }, [nodes, edges, root]);

  const nodeById = useMemo(
    () => new Map(nodes.map((n) => [String(n.id), n])),
    [nodes],
  );
  const selectedNode =
    selectedId != null ? nodeById.get(String(selectedId)) || null : null;

  const activeEdge = useMemo(() => {
    if (!activeEdgeKey) return null;
    const [s, t] = activeEdgeKey.split("->");
    return (
      edges.find(
        (e) => String(e.source) === s && String(e.target) === t,
      ) || null
    );
  }, [activeEdgeKey, edges]);

  const hasLinks = nodes.length > 1 && edges.length > 0;
  const quickUrns = useMemo(() => {
    const bySlug = new Map(urns.map((u) => [String(u.slug), u]));
    return KNOWN_URNS.map((k) => {
      const u = bySlug.get(k.slug);
      return {
        slug: k.slug,
        nameVi: u ? entityName(u) : k.nameVi,
        id: u && u.id != null ? u.id : null,
      };
    });
  }, [urns]);

  const goToEntity = (value) => {
    const ref = String(value ?? "").trim();
    if (!ref) return;
    setEntityRef(ref);
    setSearchOpen(false);
    setResults([]);
    setQuery("");
    router.push(`/explore/connections?entity=${encodeURIComponent(ref)}`, {
      scroll: false,
    });
  };

  const navigateNode = (node) => {
    const href = nodeHref(node);
    if (href) {
      router.push(href);
      return;
    }
    goToEntity(node.id);
  };

  return (
    <main className="site-shell">
      <section className="heritage-hero p-6 md:p-9">
        <div className="relative max-w-4xl">
          <div className="heritage-chip">
            <Network className="h-4 w-4" aria-hidden="true" />
            Mạng lưới tri thức
          </div>
          <h1 className="mt-5 font-display text-3xl font-bold tracking-tight text-foreground md:text-5xl">
            Mạng lưới liên kết
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground md:text-lg">
            Mỗi thực thể — đỉnh, phù điêu, địa danh, nhân vật hay sự kiện — nằm
            trong một mạng lưới quan hệ được nạp từ máy chủ lịch sử. Chọn một
            thực thể để xem nó kết nối với những gì, và mở rộng thêm một bước
            nếu cần.
          </p>
        </div>
      </section>

      <div className="mt-5">
        <VerificationNote />
      </div>

      {/* Search + picker */}
      <section
        className="mt-6 rounded-lg border border-border bg-card/60 p-4"
        aria-label="Chọn thực thể xuất phát"
      >
        <div className="relative">
          <Search
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden="true"
          />
          <Input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => {
              if (results.length > 0) setSearchOpen(true);
            }}
            onBlur={() => {
              window.setTimeout(() => setSearchOpen(false), 150);
            }}
            placeholder="Tìm đỉnh, phù điêu, địa danh, nhân vật…"
            aria-label="Tìm thực thể để vẽ mạng lưới liên kết"
            aria-expanded={searchOpen}
            aria-controls="connections-search-results"
            role="combobox"
            className="pl-9"
          />
          {query && results.length > 0 && searchOpen ? (
            <div
              id="connections-search-results"
              role="listbox"
              className="absolute left-0 right-0 top-full z-20 mt-2 max-h-72 overflow-auto rounded-lg border border-border bg-popover p-1.5 shadow-xl"
            >
              {results.map((item) => (
                <button
                  key={String(item.id)}
                  type="button"
                  role="option"
                  aria-selected="false"
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => goToEntity(item.id)}
                  className="flex w-full items-center justify-between gap-3 rounded-md px-3 py-2 text-left text-sm hover:bg-secondary focus-visible:bg-secondary focus-visible:outline-none"
                >
                  <span className="min-w-0">
                    <span className="block truncate font-medium text-foreground">
                      {entityName(item)}
                    </span>
                    {item.slug ? (
                      <span className="block truncate text-xs text-muted-foreground">
                        {item.slug}
                      </span>
                    ) : null}
                  </span>
                  <span className="shrink-0 rounded-md bg-secondary/70 px-2 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
                    {entityTypeLabel(item.entity_type)}
                  </span>
                </button>
              ))}
            </div>
          ) : null}
        </div>

        {searchError ? (
          <p className="mt-2 text-xs text-destructive" role="alert">
            {searchError}
          </p>
        ) : null}

        <div className="mt-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Chín chiếc đỉnh
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            {quickUrns.map((urn) => (
              <button
                key={urn.slug}
                type="button"
                onClick={() => goToEntity(urn.id || urn.slug)}
                className="inline-flex items-center gap-1.5 rounded-lg border border-border/70 bg-background/60 px-3 py-1.5 text-xs font-medium text-foreground transition hover:border-primary/40 hover:bg-secondary"
              >
                <Boxes className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
                {urn.nameVi}
              </button>
            ))}
          </div>
        </div>
      </section>

      {error ? (
        <div
          role="alert"
          className="mt-5 rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive"
        >
          <div className="flex items-start gap-2">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            <span>{error}</span>
          </div>
        </div>
      ) : null}

      {!entityRef ? (
        <section className="mt-6">
          <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border/70 bg-card/45 px-6 py-14 text-center">
            <Network className="mb-3 h-9 w-9 text-muted-foreground" aria-hidden="true" />
            <h2 className="font-display text-base font-semibold text-foreground">
              Chọn một điểm khởi đầu
            </h2>
            <p className="mt-1 max-w-md text-sm text-muted-foreground">
              Tìm thực thể ở ô bên trên hoặc bấm một trong chín chiếc đỉnh. Sơ đồ
              sẽ vẽ các kết nối trực tiếp trước, và bạn có thể mở rộng thêm một
              bước khi cần.
            </p>
          </div>
        </section>
      ) : null}

      {entityRef && loading ? (
        <section className="mt-6 grid gap-4 lg:grid-cols-[1fr_320px]" aria-busy="true">
          <div className="rounded-lg border border-border bg-card/60 p-4">
            <Skeleton className="h-[420px] w-full" />
          </div>
          <div className="rounded-lg border border-border bg-card/60 p-4">
            <Skeleton className="h-5 w-2/3" />
            <Skeleton className="mt-3 h-4 w-full" />
            <Skeleton className="mt-2 h-24 w-full" />
          </div>
        </section>
      ) : null}

      {entityRef && !loading && !error && root ? (
        <>
          <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span className="rounded-md border border-border/60 bg-background/70 px-2.5 py-1 text-xs font-medium text-foreground">
                {entityName(root)}
              </span>
              <span className="text-xs">·</span>
              <span className="text-xs">
                {nodes.length} thực thể · {edges.length} liên kết
              </span>
            </div>
            <div
              className="inline-flex items-center gap-1 rounded-lg border border-border/70 bg-background/60 p-1"
              role="group"
              aria-label="Độ sâu mạng lưới"
            >
              <button
                type="button"
                aria-pressed={depth === 1}
                onClick={() => setDepth(1)}
                className={cn(
                  "rounded-md px-3 py-1.5 text-xs font-semibold transition",
                  depth === 1
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-secondary",
                )}
              >
                1 bước
              </button>
              <button
                type="button"
                aria-pressed={depth === 2}
                onClick={() => setDepth(2)}
                className={cn(
                  "rounded-md px-3 py-1.5 text-xs font-semibold transition",
                  depth === 2
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-secondary",
                )}
              >
                2 bước
              </button>
            </div>
          </div>

          <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_320px]">
            <section
              className="rounded-lg border border-border bg-card/60 p-4"
              aria-label="Sơ đồ mạng lưới"
            >
              {hasLinks ? (
                <>
                  <GraphSvg
                    nodes={nodes}
                    edges={edges}
                    positions={positions}
                    rootId={root.id}
                    selectedId={selectedId}
                    activeEdgeKey={activeEdgeKey}
                    onSelectNode={setSelectedId}
                    onActivateEdge={setActiveEdgeKey}
                    onDeactivateEdge={() => setActiveEdgeKey(null)}
                    onNavigate={navigateNode}
                  />
                  <ul className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1.5 border-t border-border/60 pt-3 text-[11px] text-muted-foreground">
                    {LEGEND_ITEMS.map((item) => (
                      <li key={item.type} className="inline-flex items-center gap-1.5">
                        <span
                          className="h-2.5 w-2.5 rounded-full"
                          style={{ backgroundColor: colorForType(item.type) }}
                          aria-hidden="true"
                        />
                        {item.label}
                      </li>
                    ))}
                    <li className="inline-flex items-center gap-1.5">
                      <span
                        className="h-2.5 w-2.5 rounded-full border border-dashed border-muted-foreground/60"
                        aria-hidden="true"
                      />
                      Liên kết đã xác nhận (nét liền khi chọn)
                    </li>
                  </ul>
                </>
              ) : (
                <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border/70 bg-card/45 px-6 py-14 text-center">
                  <Network className="mb-3 h-8 w-8 text-muted-foreground" aria-hidden="true" />
                  <h3 className="font-display text-base font-semibold text-foreground">
                    Chưa có liên kết nào được ghi nhận
                  </h3>
                  <p className="mt-1 max-w-md text-sm text-muted-foreground">
                    {entityName(root)} hiện chưa có quan hệ nào được nạp từ máy
                    chủ lịch sử. Thử chọn thực thể khác, hoặc quay lại sau khi
                    dữ liệu quan hệ được bổ sung.
                  </p>
                  <button
                    type="button"
                    onClick={() => setDepth(depth === 1 ? 2 : 1)}
                    className="mt-4 rounded-lg border border-border px-4 py-2 text-sm font-semibold text-foreground transition hover:bg-secondary"
                  >
                    {depth === 1 ? "Thử mở rộng 2 bước" : "Thu về 1 bước"}
                  </button>
                </div>
              )}
            </section>

            <aside
              className="rounded-lg border border-border bg-card/60 p-4"
              aria-label="Chi tiết lựa chọn"
            >
              {activeEdge ? (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-primary">
                    Liên kết đang chọn
                  </p>
                  <h3 className="mt-1 font-display text-lg font-bold text-foreground">
                    {relationPredicateLabel(activeEdge.predicate)}
                  </h3>
                  <dl className="mt-3 space-y-2 text-sm text-muted-foreground">
                    <div>
                      <dt className="text-xs uppercase tracking-wide">Trạng thái kiểm chứng</dt>
                      <dd className="mt-0.5 text-foreground">
                        {verificationStatusLabel(activeEdge.verification_status)}
                      </dd>
                    </div>
                    {activeEdge.source_id != null ? (
                      <div>
                        <dt className="text-xs uppercase tracking-wide">Nguồn gắn kèm</dt>
                        <dd className="mt-0.5 text-foreground">#{activeEdge.source_id}</dd>
                      </div>
                    ) : null}
                  </dl>
                </div>
              ) : selectedNode ? (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-primary">
                    {String(selectedNode.id) === String(root.id)
                      ? "Thực thể trung tâm"
                      : entityTypeLabel(selectedNode.entity_type)}
                  </p>
                  <h3 className="mt-1 font-display text-lg font-bold text-foreground">
                    {entityName(selectedNode)}
                  </h3>
                  {selectedNode.name_en ? (
                    <p className="mt-1 text-sm text-muted-foreground">
                      {selectedNode.name_en}
                    </p>
                  ) : null}
                  {selectedNode.slug ? (
                    <p className="mt-1 text-xs text-muted-foreground">
                      {selectedNode.slug}
                    </p>
                  ) : null}
                  <div className="mt-3">
                    <EpistemicLabel
                      info={publicationEpistemic(selectedNode.publication_status)}
                    />
                  </div>
                  <p className="mt-3 text-sm leading-6 text-foreground/85">
                    {selectedNode.summary_vi ||
                      selectedNode.summary ||
                      selectedNode.summary_en ||
                      "Chưa có tóm tắt cho thực thể này — nội dung đang được soạn thảo."}
                  </p>
                  {nodeHref(selectedNode) ? (
                    <Link
                      href={nodeHref(selectedNode)}
                      className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:underline"
                    >
                      Xem chi tiết
                      <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
                    </Link>
                  ) : (
                    <button
                      type="button"
                      onClick={() => goToEntity(selectedNode.id)}
                      className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:underline"
                    >
                      Vẽ mạng lưới quanh thực thể này
                      <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
                    </button>
                  )}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  Di chuyển chuột hoặc bàn phím lên một nút để xem chi tiết.
                </p>
              )}

              <button
                type="button"
                onClick={() => {
                  const href = nodeHref(root);
                  if (href) router.push(href);
                }}
                className="mt-4 inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-xs font-semibold text-muted-foreground transition hover:bg-secondary hover:text-foreground"
              >
                <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
                Trang chi tiết của thực thể trung tâm
              </button>

              <p className="mt-4 flex items-start gap-1.5 text-[11px] leading-5 text-muted-foreground">
                <Share2 className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                Liên kết chia sẻ đã có sẵn trong thanh địa chỉ (?entity=…).
              </p>
            </aside>
          </div>
        </>
      ) : null}

      {entityRef && !loading && !error && !root ? (
        <section className="mt-6">
          <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border/70 bg-card/45 px-6 py-14 text-center">
            <X className="mb-3 h-8 w-8 text-muted-foreground" aria-hidden="true" />
            <h3 className="font-display text-base font-semibold text-foreground">
              Không có thực thể để vẽ
            </h3>
            <p className="mt-1 max-w-md text-sm text-muted-foreground">
              Thực thể theo địa chỉ “{entityRef}” không có dữ liệu trên máy chủ
              lịch sử. Hãy chọn một thực thể khác ở ô tìm kiếm.
            </p>
          </div>
        </section>
      ) : null}

      <p className="mt-8 text-xs leading-relaxed text-muted-foreground">
        Sơ đồ chỉ vẽ các quan hệ đã được nạp từ máy chủ lịch sử; mỗi liên kết
        đều có trạng thái kiểm chứng riêng. Không phải mọi liên kết đều là kết
        luận lịch sử đã xác nhận.
      </p>
    </main>
  );
}