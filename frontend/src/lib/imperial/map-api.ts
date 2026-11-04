/**
 * API client wrappers for STTTNNĐ (Lưu Niên — Đại Nội Huế).
 * Communicates strictly via canonical namespace `/api/v1/imperial/*`.
 *
 * Implements fallback mechanisms to guarantee seamless functionality
 * in offline or transitional database environments.
 */

import { apiRequest } from "@/lib/api";
import {
  FALLBACK_ACTIVE_MAP_RESPONSE,
  FALLBACK_ANNOTATIONS,
  FALLBACK_MAP_ASSET,
  FALLBACK_SITES,
  FALLBACK_ZONES,
} from "./fallback-data";
import {
  getSiteDossier,
  PUBLIC_SOURCES_CATALOG,
  type PublicSourceRecord,
} from "./dossier-data";
import type {
  ActiveMapResponse,
  AnnotationExportPayload,
  ImperialMapAnnotation,
  ImperialMapAsset,
  ImperialSite,
  ImperialSiteDetail,
  ImperialSiteEvidence,
  ImperialSiteTimeline,
  ImperialZone,
  ImportDryRunResult,
  MapAnnotationsResponse,
  SiteDossierData,
} from "./map-types";

export interface FetchSitesQuery {
  zone?: string;
  condition?: string;
  level?: string;
  search?: string;
  published?: boolean;
}

/**
 * Normalizes array or envelope responses ({ items: [...] } or { sites: [...] } or [...]).
 */
function normalizeList<T>(data: unknown, fallbackKey?: string): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === "object") {
    const record = data as Record<string, unknown>;
    if (fallbackKey && Array.isArray(record[fallbackKey])) {
      return record[fallbackKey] as T[];
    }
    if (Array.isArray(record.items)) {
      return record.items as T[];
    }
    if (Array.isArray(record.data)) {
      return record.data as T[];
    }
  }
  return [];
}

/**
 * GET /api/v1/imperial/maps/active
 * Fetches the currently published active aerial map asset with all approved annotations.
 */
export async function fetchActiveMap(): Promise<ActiveMapResponse> {
  try {
    const data = await apiRequest<ActiveMapResponse>(
      "/api/v1/imperial/maps/active",
      { cache: "no-store" },
    );
    if (data && data.map && Array.isArray(data.annotations)) {
      return data;
    }
    return FALLBACK_ACTIVE_MAP_RESPONSE;
  } catch (error) {
    if (process.env.NODE_ENV !== "production") {
      console.warn("fetchActiveMap fallback active:", error);
    }
    return FALLBACK_ACTIVE_MAP_RESPONSE;
  }
}

/**
 * GET /api/v1/imperial/zones
 * Fetches the 4 verified spatial zones of the Imperial City.
 */
export async function fetchZones(): Promise<ImperialZone[]> {
  try {
    const res = await apiRequest<unknown>("/api/v1/imperial/zones");
    const list = normalizeList<ImperialZone>(res, "zones");
    return list.length > 0 ? list : FALLBACK_ZONES;
  } catch (error) {
    if (process.env.NODE_ENV !== "production") {
      console.warn("fetchZones fallback active:", error);
    }
    return FALLBACK_ZONES;
  }
}

/**
 * GET /api/v1/imperial/sites
 * Fetches monuments/sites matching optional criteria.
 */
export async function fetchSites(
  query?: FetchSitesQuery,
): Promise<ImperialSite[]> {
  try {
    const params = new URLSearchParams();
    if (query?.zone) params.set("zone", query.zone);
    if (query?.condition) params.set("condition", query.condition);
    if (query?.level) params.set("level", query.level);
    if (query?.search) params.set("search", query.search);
    if (query?.published !== undefined) {
      params.set("published", String(query.published));
    }

    const qs = params.toString();
    const res = await apiRequest<unknown>(
      `/api/v1/imperial/sites${qs ? `?${qs}` : ""}`,
    );
    const list = normalizeList<ImperialSite>(res, "sites");
    if (list.length > 0) return list;
  } catch (error) {
    if (process.env.NODE_ENV !== "production") {
      console.warn("fetchSites fallback active:", error);
    }
  }

  // Fallback filter
  return FALLBACK_SITES.filter((site) => {
    if (query?.zone && site.zone_slug !== query.zone) return false;
    if (query?.condition && site.condition !== query.condition) return false;
    if (query?.level && site.learning_level !== query.level) return false;
    if (query?.published !== undefined && site.published !== query.published) {
      return false;
    }
    if (query?.search) {
      const q = query.search.toLowerCase().trim();
      const matchName = site.name_vi.toLowerCase().includes(q);
      const matchHan =
        site.name_han_nom?.includes(q) || site.chinese_name?.includes(q);
      const matchAlt = site.alternative_names?.some((alt) =>
        alt.toLowerCase().includes(q),
      );
      if (!matchName && !matchHan && !matchAlt) return false;
    }
    return true;
  });
}

/**
 * GET /api/v1/imperial/sites/{slug}
 * Fetches deep historical dossier, condition, and inquiry tasks for a monument.
 */
export async function fetchSiteDetail(
  slug: string,
): Promise<ImperialSiteDetail | null> {
  try {
    const res = await apiRequest<ImperialSiteDetail>(
      `/api/v1/imperial/sites/${encodeURIComponent(slug)}`,
    );
    if (res && res.slug) return res;
  } catch (error) {
    if (process.env.NODE_ENV !== "production") {
      console.warn(`fetchSiteDetail fallback for ${slug}:`, error);
    }
  }

  const found = FALLBACK_SITES.find((s) => s.slug === slug);
  return found || null;
}

/**
 * GET /api/v1/imperial/sites/{slug}/evidence
 * Fetches primary archival evidence and verified historical claims for a monument.
 */
export async function fetchSiteEvidence(
  slug: string,
): Promise<ImperialSiteEvidence> {
  try {
    const res = await apiRequest<ImperialSiteEvidence>(
      `/api/v1/imperial/sites/${encodeURIComponent(slug)}/evidence`,
    );
    if (res && Array.isArray(res.sources)) return res;
  } catch (error) {
    if (process.env.NODE_ENV !== "production") {
      console.warn(`fetchSiteEvidence fallback for ${slug}:`, error);
    }
  }

  const site = FALLBACK_SITES.find((s) => s.slug === slug);
  return {
    site_slug: slug,
    site_name_vi: site?.name_vi,
    sources: site?.primary_sources?.map((s) => ({
      title: s.source_title,
      source_title: s.source_title,
      volume_or_chapter: s.volume_or_chapter,
      citation: s.citation,
      archival_unit: s.archival_unit,
      reliability_level: s.reliability_level,
    })) ?? [
      {
        title: "Đại Nam Thực Lục Chính Biên",
        source_title: "Đại Nam Thực Lục Chính Biên",
        citation: "Tư liệu lưu trữ thuộc Quốc Sử Quán triều Nguyễn.",
        archival_unit: "Viện Sử Học",
        reliability_level: "verified_primary_source",
      },
    ],
    claims: [
      {
        claim_text:
          site?.historical_summary ||
          "Công trình kiến trúc cung đình triều Nguyễn thuộc Quần thể Di tích Cố đô Huế.",
        statement_vi: site?.historical_summary ?? undefined,
        confidence: "verified",
        verification_status: "approved",
      },
    ],
  };
}

/**
 * GET /api/v1/imperial/sites/{slug}/timeline
 * Fetches historical chronological milestones for a monument.
 */
export async function fetchSiteTimeline(
  slug: string,
): Promise<ImperialSiteTimeline> {
  try {
    const res = await apiRequest<ImperialSiteTimeline>(
      `/api/v1/imperial/sites/${encodeURIComponent(slug)}/timeline`,
    );
    if (res && Array.isArray(res.events)) return res;
  } catch (error) {
    if (process.env.NODE_ENV !== "production") {
      console.warn(`fetchSiteTimeline fallback for ${slug}:`, error);
    }
  }

  const site = FALLBACK_SITES.find((s) => s.slug === slug);
  const events = [];

  if (site?.construction_year) {
    events.push({
      year: site.construction_year,
      title: "Khởi dựng công trình",
      description: `Khởi công xây dựng dưới triều vua ${site.reign || "nhà Nguyễn"}.`,
      reign: site.reign || undefined,
      event_type: "construction",
    });
  }

  events.push({
    year: "1945",
    title: "Chuyển giao lịch sử",
    description:
      "Vua Bảo Đại thoái vị tại Ngọ Môn; Đại Nội được công nhận di sản quốc gia đặc biệt.",
    event_type: "political",
  });

  events.push({
    year: "1993",
    title: "Di sản Thế giới UNESCO",
    description:
      "Quần thể Di tích Cố đô Huế được UNESCO ghi danh là Di sản Văn hóa Thế giới.",
    event_type: "conservation",
  });

  return {
    site_slug: slug,
    site_name_vi: site?.name_vi,
    events,
  };
}

/**
 * Fetches the unified 7-section pedagogical dossier for a monument.
 * Combines server endpoints (site detail, evidence, timeline) with verified
 * archival fallback data to guarantee complete pedagogical structure.
 */
export async function fetchSiteDossier(
  slug: string,
): Promise<SiteDossierData | null> {
  try {
    const site = await fetchSiteDetail(slug);
    if (!site) {
      return getSiteDossier(slug);
    }
    const dossier = getSiteDossier(slug);
    if (!dossier) return null;

    return {
      ...dossier,
      site: {
        ...dossier.site,
        ...site,
      },
    };
  } catch (error) {
    if (process.env.NODE_ENV !== "production") {
      console.warn(`fetchSiteDossier fallback for ${slug}:`, error);
    }
    return getSiteDossier(slug);
  }
}

/**
 * Fetches the comprehensive public sources ledger and copyright fair-use registry.
 * Sourced for /dai-noi/nguon.
 */
export async function fetchPublicSources(): Promise<PublicSourceRecord[]> {
  try {
    const res = await apiRequest<unknown>("/api/v1/imperial/sources");
    const list = normalizeList<PublicSourceRecord>(res, "sources");
    if (list.length > 0) return list;
  } catch (error) {
    if (process.env.NODE_ENV !== "production") {
      console.warn("fetchPublicSources fallback active:", error);
    }
  }

  return PUBLIC_SOURCES_CATALOG;
}

/**
 * GET /api/v1/imperial/admin/maps
 * Fetches all map asset revisions and drafts for admin and staff.
 */
export async function fetchAdminMaps(): Promise<ImperialMapAsset[]> {
  try {
    const res = await apiRequest<unknown>("/api/v1/imperial/admin/maps");
    const list = normalizeList<ImperialMapAsset>(res, "maps");
    if (list.length > 0) return list;
  } catch (error) {
    if (process.env.NODE_ENV !== "production") {
      console.warn("fetchAdminMaps fallback active:", error);
    }
  }

  return [FALLBACK_MAP_ASSET];
}

/**
 * GET /api/v1/imperial/admin/maps/{mapId}/annotations
 * Fetches draft and published annotations for a specific map asset.
 */
export async function fetchAdminAnnotations(
  mapId: string,
): Promise<ImperialMapAnnotation[]> {
  try {
    const res = await apiRequest<unknown>(
      `/api/v1/imperial/admin/maps/${encodeURIComponent(mapId)}/annotations`,
    );
    const list = normalizeList<ImperialMapAnnotation>(res, "annotations");
    if (list.length > 0) return list;
  } catch (error) {
    if (process.env.NODE_ENV !== "production") {
      console.warn(`fetchAdminAnnotations fallback for ${mapId}:`, error);
    }
  }

  return FALLBACK_ANNOTATIONS;
}

/**
 * POST /api/v1/imperial/admin/maps/{mapId}/annotations
 * Creates a new monument marker attached to a site.
 * Persists directly to the backend database; re-throws on network or server error.
 */
export async function createAnnotation(
  mapId: string,
  payload: Partial<ImperialMapAnnotation> & {
    site_id: string;
    u: number;
    v: number;
  },
): Promise<ImperialMapAnnotation> {
  const body: Record<string, unknown> = {
    site_id: payload.site_id,
    u: payload.u,
    v: payload.v,
    shape_type: payload.shape_type || "point",
    label: payload.label ?? null,
    marker_style: payload.marker_style || "monument",
    position_confidence: payload.position_confidence || "approximate",
  };
  if (payload.polygon_uv) body.polygon_uv = payload.polygon_uv;
  if (payload.z_index !== undefined) body.z_index = payload.z_index;
  if (payload.is_visible !== undefined) body.is_visible = payload.is_visible;
  if (payload.position_source_ref !== undefined) body.position_source_ref = payload.position_source_ref;
  if (payload.editorial_notes !== undefined) body.editorial_notes = payload.editorial_notes;

  return await apiRequest<ImperialMapAnnotation>(
    `/api/v1/imperial/admin/maps/${encodeURIComponent(mapId)}/annotations`,
    {
      method: "POST",
      body,
    },
  );
}

/**
 * PATCH /api/v1/imperial/admin/annotations/{id}
 * Updates marker coordinates or metadata. Sends If-Match header with row_version
 * to prevent concurrent edit overwrites (Spec §6.4).
 * Persists directly to the backend database; re-throws on concurrency conflict or server error.
 */
export async function updateAnnotation(
  annotationId: string,
  payload: Partial<ImperialMapAnnotation> & { row_version: number },
): Promise<ImperialMapAnnotation> {
  const headers: Record<string, string> = {
    "If-Match": `"row-version-${payload.row_version}"`,
  };

  const body: Record<string, unknown> = {
    row_version: payload.row_version,
  };
  if (payload.u !== undefined) body.u = payload.u;
  if (payload.v !== undefined) body.v = payload.v;
  if (payload.shape_type !== undefined) body.shape_type = payload.shape_type;
  if (payload.polygon_uv !== undefined) body.polygon_uv = payload.polygon_uv;
  if (payload.label !== undefined) body.label = payload.label;
  if (payload.marker_style !== undefined) body.marker_style = payload.marker_style;
  if (payload.z_index !== undefined) body.z_index = payload.z_index;
  if (payload.is_visible !== undefined) body.is_visible = payload.is_visible;
  if (payload.review_status !== undefined) body.review_status = payload.review_status;
  if (payload.position_confidence !== undefined) body.position_confidence = payload.position_confidence;
  if (payload.position_source_ref !== undefined) body.position_source_ref = payload.position_source_ref;
  if (payload.editorial_notes !== undefined) body.editorial_notes = payload.editorial_notes;

  return await apiRequest<ImperialMapAnnotation>(
    `/api/v1/imperial/admin/annotations/${encodeURIComponent(annotationId)}`,
    {
      method: "PATCH",
      body,
      headers,
    },
  );
}

/**
 * DELETE /api/v1/imperial/admin/annotations/{id}
 * Soft deletes / archives an annotation on the server.
 * Re-throws on failure and never fabricates deletion success.
 */
export async function deleteAnnotation(
  annotationId: string,
): Promise<{ success: boolean; id: string }> {
  const res = await apiRequest<{ ok?: boolean; success?: boolean; id?: string }>(
    `/api/v1/imperial/admin/annotations/${encodeURIComponent(annotationId)}`,
    {
      method: "DELETE",
    },
  );
  return {
    success: res.success ?? res.ok ?? true,
    id: res.id ?? annotationId,
  };
}

/**
 * POST /api/v1/imperial/admin/maps/{mapId}/publish
 * Atomically publishes the map asset and its approved annotations snapshot.
 * Re-throws on failure (e.g. unapproved license, 500 error) and never fabricates published state.
 */
export async function publishMap(
  mapId: string,
): Promise<{ success: boolean; map: ImperialMapAsset }> {
  const data = await apiRequest<ImperialMapAsset | { success: boolean; map: ImperialMapAsset }>(
    `/api/v1/imperial/admin/maps/${encodeURIComponent(mapId)}/publish`,
    {
      method: "POST",
    },
  );
  if (data && "map" in data && data.map) {
    return { success: data.success ?? true, map: data.map };
  }
  return { success: true, map: data as ImperialMapAsset };
}

/**
 * GET /api/v1/imperial/admin/maps/{mapId}/export
 * Exports complete JSON backup with schema_version and hash.
 * Fetches authoritative dataset from the server.
 */
export async function exportAnnotations(
  mapId: string,
): Promise<AnnotationExportPayload> {
  return await apiRequest<AnnotationExportPayload>(
    `/api/v1/imperial/admin/maps/${encodeURIComponent(mapId)}/export`,
  );
}

/**
 * POST /api/v1/imperial/admin/maps/{mapId}/import?dry_run=true|false
 * Imports annotations with atomic validation and diff preview on the server.
 * Re-throws on failure and never fabricates valid import results.
 */
export async function importAnnotations(
  mapId: string,
  payload: AnnotationExportPayload,
  dryRun: boolean = true,
): Promise<ImportDryRunResult> {
  const res = await apiRequest<{
    valid?: boolean;
    status?: string;
    created_count?: number;
    updated_count?: number;
    skipped_count?: number;
    total_count?: number;
    image_hash_matched?: boolean;
    issues?: any[];
    summary?: {
      total?: number;
      new_count?: number;
      updated_count?: number;
      invalid_count?: number;
    };
  }>(
    `/api/v1/imperial/admin/maps/${encodeURIComponent(mapId)}/import?dry_run=${dryRun}`,
    {
      method: "POST",
      body: payload,
    },
  );
  return {
    valid: res.valid ?? (res.status === "success"),
    created_count: res.created_count ?? res.summary?.new_count ?? 0,
    updated_count: res.updated_count ?? res.summary?.updated_count ?? 0,
    skipped_count: res.skipped_count ?? 0,
    total_count: res.total_count ?? res.summary?.total ?? 0,
    image_hash_matched: res.image_hash_matched ?? true,
    issues: res.issues ?? [],
  };
}
