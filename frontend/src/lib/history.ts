// Shared types + defensive normalizers + label maps for the History-First
// public surface (Cửu Đỉnh rebuild). Pure module: no React, no server-only
// imports, safe to import from client components.
//
// The backend /api/v1/history/* contract is still evolving, so every normalizer
// here tolerates both `{ items: [...] }` list envelopes and raw arrays, and
// each type's fields are optional.

export interface HistoryEntity {
  id?: string | number;
  entity_type?: string | null;
  slug?: string | null;
  name_vi?: string | null;
  name_en?: string | null;
  name_han_nom?: string | null;
  han_nom?: string | null;
  alternative_names?: string[] | null;
  summary_vi?: string | null;
  summary_en?: string | null;
  summary?: string | null;
  publication_status?: string | null;
  thumbnail_url?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  date_precision?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  geo_precision?: string | null;
  urn_slug?: string | null;
  [key: string]: unknown;
}

export interface HistoryListResponse<T> {
  items?: T[];
  total?: number;
  offset?: number;
  limit?: number;
}

export interface HistoryClaim {
  id?: string | number;
  entity_id?: string | number | null;
  claim_key?: string | null;
  claim_type?: string | null;
  statement_vi?: string | null;
  statement_en?: string | null;
  claim_text?: string | null;
  statement?: string | null;
  verification_status?: string | null;
  epistemic_class?: string | null;
  confidence?: string | number | null;
  origin?: string | null;
  risk_level?: string | null;
  review_notes?: string | null;
  valid_from?: string | null;
  valid_to?: string | null;
  [key: string]: unknown;
}

export interface HistorySource {
  id?: string | number;
  source_type?: string | null;
  title?: string | null;
  subtitle?: string | null;
  author_text?: string | null;
  editor_text?: string | null;
  publisher?: string | null;
  publication_year?: number | string | null;
  publication_date?: string | null;
  edition?: string | null;
  volume?: string | null;
  issue?: string | null;
  pages?: string | null;
  isbn?: string | null;
  issn?: string | null;
  doi?: string | null;
  url?: string | null;
  archive_url?: string | null;
  language?: string | null;
  citation_text?: string | null;
  rights_status?: string | null;
  license?: string | null;
  attribution_text?: string | null;
  public_display_allowed?: boolean | null;
  derivative_allowed?: boolean | null;
  verification_status?: string | null;
  [key: string]: unknown;
}

export interface HistoryRelation {
  id?: string | number;
  subject_entity_id?: string | number | null;
  predicate?: string | null;
  object_entity_id?: string | number | null;
  object_slug?: string | null;
  object_name?: string | null;
  object?: HistoryEntity | null;
  confidence?: string | null;
  verification_status?: string | null;
  [key: string]: unknown;
}

export interface HistoryGeography {
  id?: string | number;
  entity_id?: string | number | null;
  name?: string | null;
  name_vi?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  geo_precision?: string | null;
  mapping_status?: string | null;
  [key: string]: unknown;
}

export interface HistorySearchItem {
  id?: string | number;
  entity_type?: string | null;
  slug?: string | null;
  name_vi?: string | null;
  name_en?: string | null;
  summary_vi?: string | null;
  publication_status?: string | null;
  [key: string]: unknown;
}

// ---------------------------------------------------------------------------
// List normalizers
// ---------------------------------------------------------------------------

export function asEntityList(payload: unknown): HistoryEntity[] {
  if (Array.isArray(payload)) return payload as HistoryEntity[];
  if (payload && typeof payload === "object") {
    const items = (payload as HistoryListResponse<HistoryEntity>).items;
    if (Array.isArray(items)) return items;
  }
  return [];
}

export function asClaimList(payload: unknown): HistoryClaim[] {
  if (Array.isArray(payload)) return payload as HistoryClaim[];
  if (payload && typeof payload === "object") {
    const items = (payload as HistoryListResponse<HistoryClaim>).items;
    if (Array.isArray(items)) return items;
  }
  return [];
}

export function asSourceList(payload: unknown): HistorySource[] {
  if (Array.isArray(payload)) return payload as HistorySource[];
  if (payload && typeof payload === "object") {
    const items = (payload as HistoryListResponse<HistorySource>).items;
    if (Array.isArray(items)) return items;
  }
  return [];
}

export function asRelations(payload: unknown): HistoryRelation[] {
  if (Array.isArray(payload)) return payload as HistoryRelation[];
  if (payload && typeof payload === "object") {
    const p = payload as { relations?: HistoryRelation[]; items?: HistoryRelation[] };
    if (Array.isArray(p.relations)) return p.relations;
    if (Array.isArray(p.items)) return p.items;
  }
  return [];
}

export function asGeographies(payload: unknown): HistoryGeography[] {
  if (Array.isArray(payload)) return payload as HistoryGeography[];
  if (payload && typeof payload === "object") {
    const p = payload as { items?: HistoryGeography[]; geographies?: HistoryGeography[] };
    if (Array.isArray(p.items)) return p.items;
    if (Array.isArray(p.geographies)) return p.geographies;
  }
  return [];
}

export function asSearchItems(payload: unknown): HistorySearchItem[] {
  if (Array.isArray(payload)) return payload as HistorySearchItem[];
  if (payload && typeof payload === "object") {
    const p = payload as {
      items?: HistorySearchItem[];
      results?: HistorySearchItem[];
      entities?: HistorySearchItem[];
    };
    if (Array.isArray(p.items)) return p.items;
    if (Array.isArray(p.results)) return p.results;
    if (Array.isArray(p.entities)) return p.entities;
  }
  return [];
}

export function listTotal(payload: unknown): number | null {
  if (payload && typeof payload === "object") {
    const total = (payload as { total?: unknown }).total;
    if (typeof total === "number" && Number.isFinite(total)) return total;
  }
  return null;
}

// ---------------------------------------------------------------------------
// Slug helpers
// ---------------------------------------------------------------------------

// Relief slugs look like `cao-dinh-02`; the urn part is everything before the
// trailing numeric segment.
export function urnSlugFromReliefSlug(
  slug: string | null | undefined,
): string {
  const s = String(slug || "").trim();
  if (!s) return "";
  const m = s.match(/^(.*?)-(\d{1,3})$/);
  if (m && m[1]) return m[1];
  return s;
}

export function reliefNumberFromSlug(
  slug: string | null | undefined,
): string {
  const s = String(slug || "").trim();
  const m = s.match(/-(\d{1,3})$/);
  return m ? m[1] : "";
}

// The nine urns migrated so far. Used for display fallback and filter labels
// only — the authoritative names always come from the API when available.
export const KNOWN_URNS: Array<{ slug: string; nameVi: string }> = [
  { slug: "cao-dinh", nameVi: "Cao Đỉnh" },
  { slug: "nhan-dinh", nameVi: "Nhân Đỉnh" },
  { slug: "chuong-dinh", nameVi: "Chương Đỉnh" },
  { slug: "anh-dinh", nameVi: "Anh Đỉnh" },
  { slug: "nghi-dinh", nameVi: "Nghị Đỉnh" },
  { slug: "thuan-dinh", nameVi: "Thuần Đỉnh" },
  { slug: "tuyen-dinh", nameVi: "Tuyền Đỉnh" },
  { slug: "du-dinh", nameVi: "Dụ Đỉnh" },
  { slug: "huyen-dinh", nameVi: "Huyền Đỉnh" },
];

export function urnNameFromSlug(
  slug: string | null | undefined,
): string {
  const s = String(slug || "");
  const known = KNOWN_URNS.find((u) => u.slug === s);
  if (known) return known.nameVi;
  return s
    .split("-")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function entityName(e: HistoryEntity | null | undefined): string {
  if (!e) return "";
  return (
    e.name_vi ||
    e.name_en ||
    e.slug ||
    e.summary_vi ||
    "Chưa đặt tên"
  );
}

// ---------------------------------------------------------------------------
// Accent-insensitive search normalization
// ---------------------------------------------------------------------------

export function deburr(s: unknown): string {
  return String(s || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLowerCase();
}

// ---------------------------------------------------------------------------
// Label maps
// ---------------------------------------------------------------------------

export type EpistemicTone =
  | "documented"
  | "interpretation"
  | "traditional"
  | "uncertain"
  | "disputed"
  | "unreviewed";

export interface EpistemicInfo {
  label: string;
  tone: EpistemicTone;
}

const EPISTEMIC_BY_CLASS: Record<string, EpistemicInfo> = {
  documented: { label: "Được nguồn xác nhận", tone: "documented" },
  interpretation: { label: "Diễn giải", tone: "interpretation" },
  modern_interpretation: { label: "Diễn giải hiện đại", tone: "interpretation" },
  traditional_account: { label: "Ghi chép / truyền thống", tone: "traditional" },
  traditional: { label: "Ghi chép / truyền thống", tone: "traditional" },
  uncertain: { label: "Chưa chắc chắn", tone: "uncertain" },
  disputed: { label: "Có tranh luận", tone: "disputed" },
  unreviewed: { label: "Chưa kiểm chứng", tone: "unreviewed" },
};

const EPISTEMIC_BY_VERIFICATION: Record<string, EpistemicInfo> = {
  expert_verified: { label: "Được nguồn xác nhận", tone: "documented" },
  editor_reviewed: { label: "Được nguồn xác nhận", tone: "documented" },
  source_attached: { label: "Đã gắn nguồn — chưa duyệt", tone: "unreviewed" },
  needs_source: { label: "Chưa kiểm chứng", tone: "unreviewed" },
  unreviewed: { label: "Chưa kiểm chứng", tone: "unreviewed" },
  rejected: { label: "Bị bác bỏ", tone: "disputed" },
  disputed: { label: "Có tranh luận", tone: "disputed" },
  superseded: { label: "Đã thay thế", tone: "uncertain" },
};

export function claimEpistemic(claim: HistoryClaim | null | undefined): EpistemicInfo {
  const raw = String(claim?.epistemic_class || "").trim().toLowerCase();
  if (raw && EPISTEMIC_BY_CLASS[raw]) return EPISTEMIC_BY_CLASS[raw];

  const verification = String(claim?.verification_status || "")
    .trim()
    .toLowerCase();
  if (verification && EPISTEMIC_BY_VERIFICATION[verification]) {
    return EPISTEMIC_BY_VERIFICATION[verification];
  }

  const type = String(claim?.claim_type || "").trim().toLowerCase();
  if (type === "traditional_account") {
    return EPISTEMIC_BY_CLASS.traditional_account;
  }
  if (
    type === "interpretation" ||
    type === "modern_interpretation" ||
    type === "symbolism"
  ) {
    return EPISTEMIC_BY_CLASS.interpretation;
  }
  if (type === "disputed") return EPISTEMIC_BY_CLASS.disputed;

  return EPISTEMIC_BY_CLASS.unreviewed;
}

export function claimText(claim: HistoryClaim | null | undefined): string {
  if (!claim) return "";
  return (
    claim.statement_vi ||
    claim.statement ||
    claim.claim_text ||
    claim.statement_en ||
    ""
  );
}

export const CLAIM_TYPE_LABELS: Record<string, string> = {
  factual: "Sự kiện / thực tế",
  chronology: "Niên đại",
  geographic: "Địa lý",
  identification: "Nhận định danh tính",
  attribution: "Quy kết",
  material: "Chất liệu",
  measurement: "Đo đạc",
  production: "Chế tác",
  symbolism: "Biểu tượng",
  interpretation: "Diễn giải",
  modern_interpretation: "Diễn giải hiện đại",
  traditional_account: "Ghi chép truyền thống",
  disputed: "Tranh luận",
  classification: "Phân loại",
  relationship: "Quan hệ",
  translation: "Dịch nghĩa",
  etymology: "Từ nguyên",
};

export function claimTypeLabel(type: string | null | undefined): string {
  const t = String(type || "").trim();
  if (!t) return "Khác";
  return CLAIM_TYPE_LABELS[t.toLowerCase()] || t;
}

export const SOURCE_TYPE_LABELS: Record<string, string> = {
  primary_source: "Nguồn sơ cấp",
  royal_record: "Châu bản / sử triều",
  archival_record: "Hồ sơ lưu trữ",
  inscription: "Văn khắc",
  museum_catalog: "Danh mục bảo tàng",
  heritage_authority: "Cơ quan di sản",
  government_publication: "Ấn phẩm nhà nước",
  scholarly_book: "Sách học thuật",
  peer_reviewed_article: "Bài báo phản biện",
  dissertation: "Luận văn",
  conference_paper: "Tham luận hội thảo",
  critical_edition: "Bản khảo đính",
  reference_work: "Sách tra cứu",
  trusted_website: "Trang web tin cậy",
  newspaper: "Báo chí",
  oral_history: "Lịch sử truyền khẩu",
  community_source: "Nguồn cộng đồng",
  other: "Khác",
};

export function sourceTypeLabel(type: string | null | undefined): string {
  const t = String(type || "").trim();
  if (!t) return "Khác";
  return SOURCE_TYPE_LABELS[t.toLowerCase()] || t;
}

export const VERIFICATION_STATUS_LABELS: Record<string, string> = {
  unreviewed: "Chưa kiểm chứng",
  needs_source: "Thiếu nguồn",
  source_attached: "Đã gắn nguồn",
  editor_reviewed: "Biên tập đã duyệt",
  expert_verified: "Chuyên gia xác nhận",
  rejected: "Bị bác bỏ",
  disputed: "Có tranh luận",
  superseded: "Đã thay thế",
};

export function verificationStatusLabel(
  status: string | null | undefined,
): string {
  const s = String(status || "").trim().toLowerCase();
  if (!s) return "Chưa kiểm chứng";
  return VERIFICATION_STATUS_LABELS[s] || s;
}

export const PUBLICATION_STATUS_LABELS: Record<string, string> = {
  draft: "Bản nháp",
  internal_review: "Đang rà soát nội bộ",
  public_unverified: "Công khai chưa kiểm chứng",
  verified: "Đã kiểm chứng",
  published: "Đã xuất bản",
  disputed: "Có tranh luận",
  archived: "Đã lưu trữ",
};

export function publicationStatusLabel(
  status: string | null | undefined,
): string {
  const s = String(status || "").trim().toLowerCase();
  if (!s) return "";
  return PUBLICATION_STATUS_LABELS[s] || s;
}

export const SOURCE_RIGHTS_LABELS: Record<string, string> = {
  public_domain: "Phạm vi công cộng",
  copyright: "Có bản quyền",
  open_access: "Truy cập mở",
  restricted: "Hạn chế truy cập",
  unknown: "Chưa rõ",
};

export function sourceRightsLabel(status: string | null | undefined): string {
  const s = String(status || "").trim().toLowerCase();
  if (!s) return "";
  return SOURCE_RIGHTS_LABELS[s] || s;
}

export const RELATION_PREDICATE_LABELS: Record<string, string> = {
  located_in: "Nằm tại",
  part_of: "Thuộc về",
  depicts: "Mô tả",
  represents: "Thể hiện",
  cast_during: "Đúc trong",
  commissioned_by: "Được đặt làm bởi",
  related_to: "Liên quan đến",
  precedes: "Trước",
  follows: "Sau",
  contemporary_of: "Cùng thời với",
  associated_with: "Gắn với",
  based_on: "Dựa trên",
  influenced_by: "Chịu ảnh hưởng của",
};

export function relationPredicateLabel(
  predicate: string | null | undefined,
): string {
  const p = String(predicate || "").trim().toLowerCase();
  if (!p) return "Liên quan đến";
  return RELATION_PREDICATE_LABELS[p] || p;
}