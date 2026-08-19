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

export interface HistoryStory {
  id?: string | number;
  slug?: string | null;
  title_vi?: string | null;
  title_en?: string | null;
  summary_vi?: string | null;
  summary_en?: string | null;
  hero_image_url?: string | null;
  blocks?: Array<Record<string, unknown>> | null;
  status?: string | null;
  publication_status?: string | null;
  featured?: boolean | null;
  published_at?: string | null;
  [key: string]: unknown;
}

export function asStoryList(payload: unknown): HistoryStory[] {
  if (Array.isArray(payload)) return payload as HistoryStory[];
  if (payload && typeof payload === "object") {
    const items = (payload as HistoryListResponse<HistoryStory>).items;
    if (Array.isArray(items)) return items;
  }
  return [];
}

export interface HistoryCollection {
  id?: string | number;
  slug?: string | null;
  title_vi?: string | null;
  title_en?: string | null;
  description_vi?: string | null;
  status?: string | null;
  visibility?: string | null;
  entity_ids?: string[];
  source_ids?: string[];
  story_ids?: string[];
  question_ids?: string[];
  published_at?: string | null;
  [key: string]: unknown;
}

export function asCollectionList(payload: unknown): HistoryCollection[] {
  if (Array.isArray(payload)) return payload as HistoryCollection[];
  if (payload && typeof payload === "object") {
    const items = (payload as HistoryListResponse<HistoryCollection>).items;
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
  if (m) return m[1];
  if (KNOWN_URNS.some((u) => u.slug === s)) return "01";
  return "";
}

// Legacy motif mesh names (e.g. `mesh_urn_cao_dinh_02_v1` or the bare legacy
// id `urn_cao_dinh_02`) map deterministically to the canonical relief slug
// `cao-dinh-02`. Returns null when the mesh does not parse into a KNOWN_URNS
// relief — in particular the urns' own self-portrait meshes at position `01`,
// which are modeled as urn entities, not relief entities, in the history DB.
export function reliefSlugFromMeshName(
  meshName: string | null | undefined,
): string | null {
  const m = String(meshName || "").trim();
  if (!m) return null;
  const match = m.match(/^(?:mesh_)?urn_(.+?)(?:_v\d+)?$/i);
  if (!match) return null;
  const slug = match[1].replace(/_/g, "-").toLowerCase();
  if (!/^[a-z]+(?:-[a-z]+)*-\d{1,3}$/.test(slug)) return null;
  if (!KNOWN_URNS.some((u) => u.slug === urnSlugFromReliefSlug(slug))) {
    return null;
  }
  const number = reliefNumberFromSlug(slug);
  if (!number || parseInt(number, 10) < 2) return null;
  return slug;
}

// Inverse of `reliefSlugFromMeshName`: build the deterministic legacy mesh
// name for a relief slug (e.g. `cao-dinh-02` → `mesh_urn_cao_dinh_02_v1`) so
// pages can look up the matching legacy lesson motif without a fragile
// mapping table. Returns null for slugs that cannot be expressed as a mesh.
export function meshNameFromReliefSlug(
  slug: string | null | undefined,
): string | null {
  const s = String(slug || "").trim();
  const urnSlug = urnSlugFromReliefSlug(s);
  const number = reliefNumberFromSlug(s);
  if (!urnSlug || !number) return null;
  return `mesh_urn_${urnSlug.replace(/-/g, "_")}_${number}_v1`;
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
  { slug: "tuyen-dinh", nameVi: "Tuyên Đỉnh" },
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

// Display name for a relation's object, tolerant of the embedded `object`
// object, denormalized `object_name`, or a bare id fallback.
export function relationObjectName(
  rel: HistoryRelation | null | undefined,
): string {
  if (!rel) return "";
  return (
    rel.object_name ||
    rel.object?.name_vi ||
    rel.object?.name_en ||
    rel.object?.slug ||
    (rel.object_entity_id != null ? `#${rel.object_entity_id}` : "")
  );
}

export const ENTITY_TYPE_LABELS: Record<string, string> = {
  urn: "Đỉnh",
  relief: "Phù điêu",
  person: "Nhân vật",
  place: "Địa danh",
  settlement: "Điểm dân cư",
  region: "Vùng",
  water_body: "Sông / biển",
  mountain: "Núi",
  island: "Đảo",
  event: "Sự kiện",
  period: "Giai đoạn",
  source: "Nguồn",
  object: "Hiện vật",
  concept: "Khái niệm",
  story: "Câu chuyện",
};

export function entityTypeLabel(type: string | null | undefined): string {
  const t = String(type || "").trim().toLowerCase();
  if (!t) return "Thực thể";
  return ENTITY_TYPE_LABELS[t] || t;
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

const EPISTEMIC_BY_PUBLICATION: Record<string, EpistemicInfo> = {
  published: { label: "Đã xuất bản", tone: "documented" },
  verified: { label: "Đã kiểm chứng", tone: "documented" },
  public_unverified: { label: "Công khai chưa kiểm chứng", tone: "unreviewed" },
  draft: { label: "Bản nháp", tone: "unreviewed" },
  internal_review: { label: "Đang rà soát nội bộ", tone: "unreviewed" },
  disputed: { label: "Có tranh luận", tone: "disputed" },
  archived: { label: "Đã lưu trữ", tone: "uncertain" },
};

// Map a publication_status onto an epistemic tone so pages can render the
// established EpistemicLabel pill for entity status.
export function publicationEpistemic(
  status: string | null | undefined,
): EpistemicInfo {
  const s = String(status || "").trim().toLowerCase();
  if (s && EPISTEMIC_BY_PUBLICATION[s]) return EPISTEMIC_BY_PUBLICATION[s];
  const label = publicationStatusLabel(status);
  return label
    ? { label, tone: "unreviewed" }
    : { label: "Chưa kiểm chứng", tone: "unreviewed" };
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

// ---------------------------------------------------------------------------
// 100% Exact 1-to-1 Image Mappings for all 9 Urns and 153 Relief Motifs
// ---------------------------------------------------------------------------
export const RELIEF_IMAGE_MAP: Record<string, string> = {
  "cao-dinh": "/assets/ban-duc-noi/CAO%20DINH/CAO%20%C4%90%E1%BB%88NH.jpg",
  "cao-dinh-02": "/assets/ban-duc-noi/CAO%20DINH/LONG.jpg",
  "cao-dinh-03": "/assets/ban-duc-noi/CAO%20DINH/BA%20LA%20M%E1%BA%ACT.jpg",
  "cao-dinh-04": "/assets/ban-duc-noi/CAO%20DINH/CANH.jpg",
  "cao-dinh-05": "/assets/ban-duc-noi/CAO%20DINH/TH%C3%94NG.jpg",
  "cao-dinh-06": "/assets/ban-duc-noi/CAO%20DINH/T%E1%BB%AC%20VI%20HOA.jpg",
  "cao-dinh-07": "/assets/ban-duc-noi/CAO%20DINH/TR%C4%A8.jpg",
  "cao-dinh-08": "/assets/ban-duc-noi/CAO%20DINH/%C4%90%C3%94NG%20H%E1%BA%A2I.jpg",
  "cao-dinh-09": "/assets/ban-duc-noi/CAO%20DINH/V%C4%A8NH%20T%E1%BA%BE%20H%C3%80.jpg",
  "cao-dinh-10": "/assets/ban-duc-noi/CAO%20DINH/NH%E1%BA%ACT.jpg",
  "cao-dinh-11": "/assets/ban-duc-noi/CAO%20DINH/NG%C6%AFU%20CH%E1%BB%AE%20GIANG.jpg",
  "cao-dinh-12": "/assets/ban-duc-noi/CAO%20DINH/THI%C3%8AN%20T%C3%94N%20S%C6%A0N.jpg",
  "cao-dinh-13": "/assets/ban-duc-noi/CAO%20DINH/THI%E1%BA%BET%20M%E1%BB%98C.jpg",
  "cao-dinh-14": "/assets/ban-duc-noi/CAO%20DINH/H%E1%BB%94.jpg",
  "cao-dinh-15": "/assets/ban-duc-noi/CAO%20DINH/%C4%90A%20T%C3%81C%20THUY%E1%BB%80N.jpg",
  "cao-dinh-16": "/assets/ban-duc-noi/CAO%20DINH/%C4%90%E1%BA%A0I%20B%C3%81C.jpg",
  "cao-dinh-17": "/assets/ban-duc-noi/CAO%20DINH/TR%E1%BA%A6M%20H%C6%AF%C6%A0NG.jpg",
  "cao-dinh-18": "/assets/ban-duc-noi/CAO%20DINH/MI%E1%BA%BET.jpg",
  "nhan-dinh": "/assets/ban-duc-noi/NHAN%20DINH/NH%C3%82N%20%C4%90%E1%BB%88NH.jpg",
  "nhan-dinh-02": "/assets/ban-duc-noi/NHAN%20DINH/NG%C3%94%20%C4%90%E1%BB%92NG.jpg",
  "nhan-dinh-03": "/assets/ban-duc-noi/NHAN%20DINH/K%E1%BB%B2%20NAM.jpg",
  "nhan-dinh-04": "/assets/ban-duc-noi/NHAN%20DINH/NOA.jpg",
  "nhan-dinh-05": "/assets/ban-duc-noi/NHAN%20DINH/NAM%20TR%C3%82N.jpg",
  "nhan-dinh-06": "/assets/ban-duc-noi/NHAN%20DINH/LI%C3%8AN%20HOA.jpg",
  "nhan-dinh-07": "/assets/ban-duc-noi/NHAN%20DINH/KH%E1%BB%94NG%20T%C6%AF%E1%BB%9AC.jpg",
  "nhan-dinh-08": "/assets/ban-duc-noi/NHAN%20DINH/NAM%20H%E1%BA%A2I.jpg",
  "nhan-dinh-09": "/assets/ban-duc-noi/NHAN%20DINH/PH%E1%BB%94%20L%E1%BB%A2I%20H%C3%80.jpg",
  "nhan-dinh-10": "/assets/ban-duc-noi/NHAN%20DINH/NGUY%E1%BB%86T.jpg",
  "nhan-dinh-11": "/assets/ban-duc-noi/NHAN%20DINH/HU%C6%A0U%20GIANG.jpg",
  "nhan-dinh-12": "/assets/ban-duc-noi/NHAN%20DINH/NG%E1%BB%B0%20B%C3%8CNH%20S%C6%A0N.jpg",
  "nhan-dinh-13": "/assets/ban-duc-noi/NHAN%20DINH/NH%C3%82N%20NG%C6%AF.jpg",
  "nhan-dinh-14": "/assets/ban-duc-noi/NHAN%20DINH/C%E1%BB%ACU.jpg",
  "nhan-dinh-15": "/assets/ban-duc-noi/NHAN%20DINH/L%C3%82U%20THUY%E1%BB%80N.jpg",
  "nhan-dinh-16": "/assets/ban-duc-noi/NHAN%20DINH/LU%C3%82N%20XA%20PH%C3%81O.jpg",
  "nhan-dinh-17": "/assets/ban-duc-noi/NHAN%20DINH/B%C3%81O.jpg",
  "nhan-dinh-18": "/assets/ban-duc-noi/NHAN%20DINH/%C4%90%E1%BA%A0I%20MAO.jpg",
  "chuong-dinh": "/assets/ban-duc-noi/CHUONG%20DINH/CH%C6%AF%C6%A0NG%20%C4%90%E1%BB%88NH.jpg",
  "chuong-dinh-02": "/assets/ban-duc-noi/CHUONG%20DINH/M%E1%BA%A0T%20LI.jpg",
  "chuong-dinh-03": "/assets/ban-duc-noi/CHUONG%20DINH/AM%20LA.jpg",
  "chuong-dinh-04": "/assets/ban-duc-noi/CHUONG%20DINH/%C4%90%E1%BA%ACU%20KH%E1%BA%A4U.jpg",
  "chuong-dinh-05": "/assets/ban-duc-noi/CHUONG%20DINH/L%E1%BB%A4C%20%C4%90%E1%BA%ACU.jpg",
  "chuong-dinh-06": "/assets/ban-duc-noi/CHUONG%20DINH/GI%E1%BB%9AI.jpg",
  "chuong-dinh-07": "/assets/ban-duc-noi/CHUONG%20DINH/K%C3%8A.jpg",
  "chuong-dinh-08": "/assets/ban-duc-noi/CHUONG%20DINH/TH%C6%AF%E1%BB%A2NG%20S%C6%A0N.jpg",
  "chuong-dinh-09": "/assets/ban-duc-noi/CHUONG%20DINH/L%E1%BB%A2I%20N%C3%94NG%20H%C3%80.jpg",
  "chuong-dinh-10": "/assets/ban-duc-noi/CHUONG%20DINH/M%E1%BB%98C%20TINH%20-%20HO%E1%BA%A2%20TINH%20-%20TH%E1%BB%94%20TINH%20-%20KIM%20TINH%20-%20THU%E1%BB%B6%20TINH.jpg",
  "chuong-dinh-11": "/assets/ban-duc-noi/CHUONG%20DINH/LINH%20GIANG.jpg",
  "chuong-dinh-12": "/assets/ban-duc-noi/CHUONG%20DINH/T%C3%82Y%20H%E1%BA%A2I.jpg",
  "chuong-dinh-13": "/assets/ban-duc-noi/CHUONG%20DINH/THU%E1%BA%ACN%20M%E1%BB%98C.jpg",
  "chuong-dinh-14": "/assets/ban-duc-noi/CHUONG%20DINH/NG%E1%BA%A0C%20NG%C6%AF.jpg",
  "chuong-dinh-15": "/assets/ban-duc-noi/CHUONG%20DINH/M%C3%94NG%20%C4%90%E1%BB%92NG%20THUY%E1%BB%80N.jpg",
  "chuong-dinh-16": "/assets/ban-duc-noi/CHUONG%20DINH/%C4%90I%E1%BB%82U%20TH%C6%AF%C6%A0NG.jpg",
  "chuong-dinh-17": "/assets/ban-duc-noi/CHUONG%20DINH/T%C3%8A.jpg",
  "chuong-dinh-18": "/assets/ban-duc-noi/CHUONG%20DINH/LINH%20QUY.jpg",
  "anh-dinh": "/assets/ban-duc-noi/ANH%20DINH/ANH%20%C4%90%E1%BB%88NH.jpg",
  "anh-dinh-02": "/assets/ban-duc-noi/ANH%20DINH/THI%E1%BB%80N.jpg",
  "anh-dinh-03": "/assets/ban-duc-noi/ANH%20DINH/T%C3%94%20H%E1%BB%A2P.jpg",
  "anh-dinh-04": "/assets/ban-duc-noi/ANH%20DINH/U%E1%BA%A4T%20KIM.jpg",
  "anh-dinh-05": "/assets/ban-duc-noi/ANH%20DINH/T%C3%82N%20LANG.jpg",
  "anh-dinh-06": "/assets/ban-duc-noi/ANH%20DINH/KH%C3%94I%20H%E1%BA%A0C.jpg",
  "anh-dinh-07": "/assets/ban-duc-noi/ANH%20DINH/MAI%20KH%C3%94I%20HOA.jpg",
  "anh-dinh-08": "/assets/ban-duc-noi/ANH%20DINH/NG%C3%82N%20H%C3%81N.jpg",
  "anh-dinh-09": "/assets/ban-duc-noi/ANH%20DINH/M%C3%83%20GIANG.jpg",
  "anh-dinh-10": "/assets/ban-duc-noi/ANH%20DINH/B%E1%BA%AEC%20%C4%90%E1%BA%A8U.jpg",
  "anh-dinh-11": "/assets/ban-duc-noi/ANH%20DINH/L%C3%94%20H%C3%80.jpg",
  "anh-dinh-12": "/assets/ban-duc-noi/ANH%20DINH/H%E1%BB%92NG%20S%C6%A0N.jpg",
  "anh-dinh-13": "/assets/ban-duc-noi/ANH%20DINH/M%C3%83.jpg",
  "anh-dinh-14": "/assets/ban-duc-noi/ANH%20DINH/TANG.jpg",
  "anh-dinh-15": "/assets/ban-duc-noi/ANH%20DINH/K%E1%BB%B2.jpg",
  "anh-dinh-16": "/assets/ban-duc-noi/ANH%20DINH/H%E1%BB%92%20%C4%90I%E1%BB%86P%20T%E1%BB%AC.jpg",
  "anh-dinh-17": "/assets/ban-duc-noi/ANH%20DINH/NHI%C3%8AM%20X%C3%80.jpg",
  "anh-dinh-18": "/assets/ban-duc-noi/ANH%20DINH/T%E1%BB%AC%20M%E1%BB%98C.jpg",
  "nghi-dinh": "/assets/ban-duc-noi/NGHI%20DINH/NGHI%20DINH.jpg",
  "nghi-dinh-02": "/assets/ban-duc-noi/NGHI%20DINH/MAI.jpg",
  "nghi-dinh-03": "/assets/ban-duc-noi/NGHI%20DINH/%C4%90%C3%80N%20M%E1%BB%98C.jpg",
  "nghi-dinh-04": "/assets/ban-duc-noi/NGHI%20DINH/QU%E1%BA%BE.jpg",
  "nghi-dinh-05": "/assets/ban-duc-noi/NGHI%20DINH/BI%E1%BB%82N%20%C4%90%E1%BA%ACU.jpg",
  "nghi-dinh-06": "/assets/ban-duc-noi/NGHI%20DINH/H%E1%BA%A2I%20%C4%90%C6%AF%E1%BB%9CNG%20HOA.jpg",
  "nghi-dinh-07": "/assets/ban-duc-noi/NGHI%20DINH/H%E1%BB%92%20DA%20T%E1%BB%AC.jpg",
  "nghi-dinh-08": "/assets/ban-duc-noi/NGHI%20DINH/QU%E1%BA%A2NG%20B%C3%8CNH%20QUAN.jpg",
  "nghi-dinh-09": "/assets/ban-duc-noi/NGHI%20DINH/C%E1%BB%ACU%20AN%20H%C3%80.jpg",
  "nghi-dinh-10": "/assets/ban-duc-noi/NGHI%20DINH/NAM%20%C4%90%E1%BA%A8U.jpg",
  "nghi-dinh-11": "/assets/ban-duc-noi/NGHI%20DINH/B%E1%BA%A0CH%20%C4%90%E1%BA%B0NG%20GIANG.jpg",
  "nghi-dinh-12": "/assets/ban-duc-noi/NGHI%20DINH/THU%E1%BA%ACN%20AN%20H%E1%BA%A2I%20KH%E1%BA%A8U.png",
  "nghi-dinh-13": "/assets/ban-duc-noi/NGHI%20DINH/L%E1%BB%A4C%20HOA%20NG%C6%AF.jpg",
  "nghi-dinh-14": "/assets/ban-duc-noi/NGHI%20DINH/GI%E1%BB%9AI.jpg",
  "nghi-dinh-15": "/assets/ban-duc-noi/NGHI%20DINH/TR%C6%AF%E1%BB%9CNG%20TH%C6%AF%C6%A0NG.jpg",
  "nghi-dinh-16": "/assets/ban-duc-noi/NGHI%20DINH/H%E1%BA%A2I%20%C4%90AO.jpg",
  "nghi-dinh-17": "/assets/ban-duc-noi/NGHI%20DINH/UY%C3%8AN%20%C6%AF%C6%A0NG.jpg",
  "nghi-dinh-18": "/assets/ban-duc-noi/NGHI%20DINH/T%C6%AF%E1%BB%A2NG.jpg",
  "thuan-dinh": "/assets/ban-duc-noi/THUAN%20DINH/THU%E1%BA%A6N%20%C4%90%E1%BB%88NH.jpg",
  "thuan-dinh-02": "/assets/ban-duc-noi/THUAN%20DINH/%C4%90%C3%80O.jpg",
  "thuan-dinh-03": "/assets/ban-duc-noi/THUAN%20DINH/S%C3%9AC%20SA%20M%E1%BA%ACT.jpg",
  "thuan-dinh-04": "/assets/ban-duc-noi/THUAN%20DINH/H%C6%AF%C6%A0NG%20NHU.jpg",
  "thuan-dinh-05": "/assets/ban-duc-noi/THUAN%20DINH/HO%C3%80NG%20%C4%90%C3%82U.jpg",
  "thuan-dinh-06": "/assets/ban-duc-noi/THUAN%20DINH/QU%E1%BB%B2%20HOA.jpg",
  "thuan-dinh-07": "/assets/ban-duc-noi/THUAN%20DINH/HO%C3%80NG%20ANH.jpg",
  "thuan-dinh-08": "/assets/ban-duc-noi/THUAN%20DINH/T%E1%BA%A2N%20VI%C3%8AN%20S%C6%A0N.jpg",
  "thuan-dinh-09": "/assets/ban-duc-noi/THUAN%20DINH/V%C4%A8NH%20%C4%90%E1%BB%8ANH%20H%C3%80.jpg",
  "thuan-dinh-10": "/assets/ban-duc-noi/THUAN%20DINH/PHONG.jpg",
  "thuan-dinh-11": "/assets/ban-duc-noi/THUAN%20DINH/TH%E1%BA%A0CH%20H%C3%83N%20GIANG.jpg",
  "thuan-dinh-12": "/assets/ban-duc-noi/THUAN%20DINH/C%E1%BA%A6N%20GI%E1%BB%9C%20H%E1%BA%A2I%20KH%E1%BA%A8U.jpg",
  "thuan-dinh-13": "/assets/ban-duc-noi/THUAN%20DINH/%C4%90%E1%BA%B6NG%20S%C6%A0N%20NG%C6%AF.jpg",
  "thuan-dinh-14": "/assets/ban-duc-noi/THUAN%20DINH/B%E1%BA%A0NG.jpg",
  "thuan-dinh-15": "/assets/ban-duc-noi/THUAN%20DINH/B%C3%80I%20%C4%90AO.jpg",
  "thuan-dinh-16": "/assets/ban-duc-noi/THUAN%20DINH/%C4%90%E1%BB%88NH.jpg",
  "thuan-dinh-17": "/assets/ban-duc-noi/THUAN%20DINH/NAM%20M%E1%BB%98C.jpg",
  "thuan-dinh-18": "/assets/ban-duc-noi/THUAN%20DINH/LY%20NG%C6%AFU.jpg",
  "tuyen-dinh": "/assets/ban-duc-noi/TUYEN%20DINH/TUYEN%20DINH.jpg",
  "tuyen-dinh-02": "/assets/ban-duc-noi/TUYEN%20DINH/T%E1%BA%A6N%20C%C3%81T%20LI%E1%BB%84U.jpg",
  "tuyen-dinh-03": "/assets/ban-duc-noi/TUYEN%20DINH/Y%E1%BA%BEN%20OA.jpg",
  "tuyen-dinh-04": "/assets/ban-duc-noi/TUYEN%20DINH/LONG%20NH%C3%83N.jpg",
  "tuyen-dinh-05": "/assets/ban-duc-noi/TUYEN%20DINH/TR%C3%82N%20CH%C3%82U%20HOA.jpg",
  "tuyen-dinh-06": "/assets/ban-duc-noi/TUYEN%20DINH/%C4%90%E1%BB%8AA%20%C4%90%E1%BA%ACU.jpg",
  "tuyen-dinh-07": "/assets/ban-duc-noi/TUYEN%20DINH/B%C3%81.jpg",
  "tuyen-dinh-08": "/assets/ban-duc-noi/TUYEN%20DINH/DU%E1%BB%86%20S%C6%A0N.png",
  "tuyen-dinh-09": "/assets/ban-duc-noi/TUYEN%20DINH/NH%C4%A8%20H%C3%80.jpg",
  "tuyen-dinh-10": "/assets/ban-duc-noi/TUYEN%20DINH/V%C3%82N.jpg",
  "tuyen-dinh-11": "/assets/ban-duc-noi/TUYEN%20DINH/%C4%90%E1%BA%A0I%20L%C3%83NH.jpg",
  "tuyen-dinh-12": "/assets/ban-duc-noi/TUYEN%20DINH/LAM%20GIANG.jpg",
  "tuyen-dinh-13": "/assets/ban-duc-noi/TUYEN%20DINH/H%E1%BA%ACU%20NG%C6%AF.jpg",
  "tuyen-dinh-14": "/assets/ban-duc-noi/TUYEN%20DINH/KH%C6%AF%C6%A0NG.jpg",
  "tuyen-dinh-15": "/assets/ban-duc-noi/TUYEN%20DINH/N%E1%BB%96.jpg",
  "tuyen-dinh-16": "/assets/ban-duc-noi/TUYEN%20DINH/L%C3%8A%20THUY%E1%BB%80N.jpg",
  "tuyen-dinh-17": "/assets/ban-duc-noi/TUYEN%20DINH/TH%E1%BB%88.jpg",
  "tuyen-dinh-18": "/assets/ban-duc-noi/TUYEN%20DINH/NGOAN.jpg",
  "du-dinh": "/assets/ban-duc-noi/DU%20DINH/D%E1%BB%A4%20%C4%90%E1%BB%88NH.jpg",
  "du-dinh-02": "/assets/ban-duc-noi/DU%20DINH/ANH%20V%C5%A8.jpg",
  "du-dinh-03": "/assets/ban-duc-noi/DU%20DINH/L%C3%8A.jpg",
  "du-dinh-04": "/assets/ban-duc-noi/DU%20DINH/PH%C3%99%20L%C6%AFU.jpg",
  "du-dinh-05": "/assets/ban-duc-noi/DU%20DINH/B%E1%BA%A0CH%20%C4%90%E1%BA%A6U.jpg",
  "du-dinh-06": "/assets/ban-duc-noi/DU%20DINH/THU%E1%BA%A6N%20HOA.jpg",
  "du-dinh-07": "/assets/ban-duc-noi/DU%20DINH/T%C3%99NG.jpg",
  "du-dinh-08": "/assets/ban-duc-noi/DU%20DINH/H%E1%BA%A2I%20V%C3%82N%20QUAN.jpg",
  "du-dinh-09": "/assets/ban-duc-noi/DU%20DINH/V%C4%A8NH%20%C4%90I%E1%BB%86N%20H%C3%80.jpg",
  "du-dinh-10": "/assets/ban-duc-noi/DU%20DINH/L%C3%94I.jpg",
  "du-dinh-11": "/assets/ban-duc-noi/DU%20DINH/V%E1%BB%86%20GIANG.jpg",
  "du-dinh-12": "/assets/ban-duc-noi/DU%20DINH/%C4%90%C3%80%20N%E1%BA%B4NG%20H%E1%BA%A2I%20KH%E1%BA%A8U.jpg",
  "du-dinh-13": "/assets/ban-duc-noi/DU%20DINH/TH%E1%BA%A0CH%20TH%E1%BB%A6%20NG%C6%AF.jpg",
  "du-dinh-14": "/assets/ban-duc-noi/DU%20DINH/T%E1%BB%AC%20T%C3%94.jpg",
  "du-dinh-15": "/assets/ban-duc-noi/DU%20DINH/%C3%94%20THUY%E1%BB%80N.jpg",
  "du-dinh-16": "/assets/ban-duc-noi/DU%20DINH/PH%C3%81C%20%C4%90AO.jpg",
  "du-dinh-17": "/assets/ban-duc-noi/DU%20DINH/C%C3%81P.jpg",
  "du-dinh-18": "/assets/ban-duc-noi/DU%20DINH/D%C6%AF%C6%A0NG.jpg",
  "huyen-dinh": "/assets/ban-duc-noi/HUYEN%20DINH/HUY%E1%BB%80N%20%C4%90%E1%BB%88NH.jpg",
  "huyen-dinh-02": "/assets/ban-duc-noi/HUYEN%20DINH/NG%E1%BB%AE%20%C4%90I%E1%BB%86P%20LAN.jpg",
  "huyen-dinh-03": "/assets/ban-duc-noi/HUYEN%20DINH/L%E1%BB%86%20CHI.jpg",
  "huyen-dinh-04": "/assets/ban-duc-noi/HUYEN%20DINH/TO%C3%81N.jpg",
  "huyen-dinh-05": "/assets/ban-duc-noi/HUYEN%20DINH/NAM%20S%C3%82M.jpg",
  "huyen-dinh-06": "/assets/ban-duc-noi/HUYEN%20DINH/MI%C3%8AN.jpg",
  "huyen-dinh-07": "/assets/ban-duc-noi/HUYEN%20DINH/TH%E1%BB%90C%20THU.jpg",
  "huyen-dinh-08": "/assets/ban-duc-noi/HUYEN%20DINH/H%E1%BB%92NG.jpg",
  "huyen-dinh-09": "/assets/ban-duc-noi/HUYEN%20DINH/H%E1%BA%ACU%20GIANG%20-%20TI%E1%BB%80N%20GIANG.jpg",
  "huyen-dinh-10": "/assets/ban-duc-noi/HUYEN%20DINH/V%C5%A8.jpg",
  "huyen-dinh-11": "/assets/ban-duc-noi/HUYEN%20DINH/HO%C3%80NG%20S%C6%A0N.jpg",
  "huyen-dinh-12": "/assets/ban-duc-noi/HUYEN%20DINH/THAO%20H%C3%80.jpg",
  "huyen-dinh-13": "/assets/ban-duc-noi/HUYEN%20DINH/QU%E1%BA%BE%20%C4%90%E1%BB%8E.jpg",
  "huyen-dinh-14": "/assets/ban-duc-noi/HUYEN%20DINH/XA.jpg",
  "huyen-dinh-15": "/assets/ban-duc-noi/HUYEN%20DINH/M%C3%83NG%20X%C3%80.jpg",
  "huyen-dinh-16": "/assets/ban-duc-noi/HUYEN%20DINH/HO%E1%BA%A2%20PH%C3%9AN%20%C4%90%E1%BB%92NG.jpg",
  "huyen-dinh-17": "/assets/ban-duc-noi/HUYEN%20DINH/S%C6%A0N%20M%C3%83.jpg",
  "huyen-dinh-18": "/assets/ban-duc-noi/HUYEN%20DINH/T%E1%BA%A4T%20M%E1%BB%98C.jpg"
};

export function reliefThumbnailUrl(
  slug: string | null | undefined,
  fallback?: string,
): string {
  if (!slug) return fallback || "/assets/ban-duc-noi/CAO%20DINH/CAO%20%C4%90%E1%BB%88NH.jpg";
  const s = String(slug).trim().toLowerCase();
  if (RELIEF_IMAGE_MAP[s]) return RELIEF_IMAGE_MAP[s];
  const urnSlug = urnSlugFromReliefSlug(s);
  return (
    RELIEF_IMAGE_MAP[urnSlug] ||
    fallback ||
    "/assets/ban-duc-noi/CAO%20DINH/CAO%20%C4%90%E1%BB%88NH.jpg"
  );
}
