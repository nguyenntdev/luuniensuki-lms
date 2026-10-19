/**
 * LƯU NIÊN — Heritage Knowledge Catalogue & Information Architecture Types
 *
 * Scoped to Hue-wide heritage ecosystem under the RBPC_HUE content scope.
 * Aligned with backend schemas in `backend/apischemas/heritage.py` and
 * additive database models defined in ADR 03 / Master Spec V2.
 */

// ---------------------------------------------------------------------------
// Controlled Vocabularies & Enum Types
// ---------------------------------------------------------------------------

/**
 * Structural classification of a heritage entity in the Hue landscape.
 */
export type HeritageEntityType =
  | "site" // Broad physical site (e.g. Imperial Citadel, Complex of Hue Monuments)
  | "monument" // Free-standing commemorative or civic structure (e.g. Ngo Mon, Ky Dai)
  | "building" // Specific hall, palace, or pavilion (e.g. Dien Thai Hoa, Thai Binh Lau)
  | "object" // Movable or fixed artifact (e.g. Cuu Dinh urn, royal stele, bell)
  | "landscape" // Natural or sacred geographic feature (e.g. Song Huong, Nui Ngu Binh)
  | "intangible" // Living practice or performing art (e.g. Nha nhac, Ca Hue, Royal culinary)
  | "community" // Living craft settlement or practitioner group (e.g. Phuoc Tich pottery, Phuong Duc bronze)
  | "collection"; // Curated group of related assets (e.g. Nine Dynastic Urns, Nguyen Woodblocks)

/**
 * Editorial lifecycle and verification status of a heritage record.
 */
export type EditorialStatus =
  | "candidate" // Ingested lead; awaiting primary source validation
  | "draft" // In active research; initial claims articulated
  | "source_backed" // Anchored to at least 1 verified authoritative bibliographic source
  | "in_review" // Under independent historian / editorial board review
  | "approved" // Formally approved by editorial board for publication
  | "published" // Publicly visible on platform catalogue
  | "withdrawn"; // Revoked due to disputes, rights revocation, or factual corrections

/**
 * Domain category for high-level visitor discovery and facet filtering.
 */
export type HeritageCategory =
  | "imperial_architecture" // Kiến trúc Hoàng gia / Cung đình Đại Nội
  | "royal_tomb" // Lăng tẩm Hoàng gia Triều Nguyễn
  | "craft_living_culture" // Làng nghề & Di sản sống (Pháp lam, Đúc đồng, Hoa giấy...)
  | "music_performance" // Âm nhạc & Nghệ thuật biểu diễn (Nhã nhạc, Tuồng, Ca Huế)
  | "landscape_nature" // Danh thắng & Cảnh quan thiên nhiên (Sông Hương, Núi Ngự)
  | "religious_spiritual" // Tín ngưỡng & Tôn giáo (Thiên Mụ, Điện Hòn Chén, Văn Miếu)
  | "museum_archive" // Bảo tàng & Di sản tư liệu (Châu bản, Mộc bản, Cổ vật)
  | "culinary_heritage"; // Ẩm thực Cung đình & Dân gian Huế

/**
 * Media asset format classification.
 */
export type MediaType =
  | "photo" // 2D documentary still image
  | "audio" // Oral history, court music clip, or pronunciation guide
  | "video" // Documentary or artisan demonstration video
  | "sketchfab_embed" // Verified third-party 3D interactive viewer
  | "glb" // Self-hosted sanitized binary 3D model (rights-cleared only)
  | "document"; // Archival scan, architectural drawing, or rubbings

/**
 * Epistemic rigor and technical precision grade of 3D digital twins and visual assets.
 */
export type AccuracyGrade =
  | "survey_grade" // Millimeter-accurate LiDAR / terrestrial laser survey
  | "measured_photogrammetry" // Calibrated multi-angle photogrammetry (e.g. CyArk / OpenHeritage)
  | "historian_reviewed" // Reconstructed model reviewed and signed off by heritage experts
  | "illustrative_only" // Artist impression based on photographic references; not measured
  | "unreviewed" // Newly indexed; epistemic veracity unverified
  | "rejected_accuracy"; // Permanently blocked due to historical inaccuracy or fantasy elements

/**
 * Commercial usage clearance under licensing terms.
 */
export type CommercialUseStatus =
  | "permitted" // Fully licensed for commercial display and attribution
  | "blocked_nc" // CC NonCommercial restriction; strictly prohibited from commercial funnel
  | "unreviewed" // Awaiting legal / rights evaluation
  | "requires_custom_grant"; // Needs direct bilateral agreement with copyright holder

/**
 * Third-party 3D embedding permission status.
 */
export type EmbedPermissionStatus =
  | "permitted" // Verified permissible for responsive iframe embed with attribution
  | "needs_rights_review" // Found in registry; awaiting author / platform terms review
  | "blocked" // Embedding disallowed or restricted by creator
  | "author_contacted"; // Student team outreach initiated; awaiting formal response

/**
 * Content readiness status for public display.
 */
export type ContentReadinessStatus =
  | "candidate" // In queue; not visible to public
  | "cleared_for_this_use" // Rights reviewed and authorized for platform context
  | "blocked" // Prohibited from public display
  | "withdrawn"; // Previously published, now taken down

/**
 * Verification state of bibliographic source evidence.
 */
export type EvidenceStatus =
  | "needs_review" // Initial claim extracted; citation needs book/page validation
  | "verified" // Page, edition, and quote confirmed by research team
  | "disputed" // Competing historical claims exist (e.g. varying construction dates)
  | "rejected"; // False or fabricated reference; blocked from retrieval

/**
 * Copyright reuse status for bibliographic and media source citations.
 */
export type HeritageReuseRights =
  | "public_domain" // Out of copyright (e.g. Nguyen dynasty imperial chronicles)
  | "cc_by" // Creative Commons Attribution
  | "cc_by_sa" // Creative Commons Attribution-ShareAlike
  | "cc_by_nc_sa" // Creative Commons NonCommercial ShareAlike
  | "educational_fair_use" // Fair use quote for scholarly citation
  | "restricted" // All rights reserved by publisher / archive
  | "unknown"; // Rights status under investigation

/**
 * Semantic relationship typology connecting heritage places, objects, and traditions.
 */
export type RelationType =
  | "contains" // Parent entity encloses child (e.g. Kinh thanh contains The Mieu)
  | "contained_in" // Child entity situated within parent
  | "honors" // Dedicated in veneration of sovereign or deity
  | "architectural_twin" // Structural or stylistic counterpart
  | "historical_successor" // Chronological continuation or replacement
  | "associated_craft" // Living artisan tradition tied to site's creation/conservation
  | "historical_patronage" // Royal patronage or institutional commission of artisanal works
  | "ceremonial_connection" // Ritual or seasonal procession linkage
  | "contemporary_influence" // Cultural continuation into modern heritage
  | "leads_to" // Direct spatial axis or physical entranceway
  | "oriented_to" // Cardinal or geomantic alignment
  | "faces" // Direct spatial dialogue across esplanade/courtyard
  | "adjacent_to" // Direct geographic contiguity within heritage buffer zone
  | "defensive_satellite" // Strategic military or naval outpost
  | "cultural_trade"; // Socio-economic exchange and ritual provision

/**
 * Sort options for heritage catalogue queries.
 */
export type HeritageSortOption =
  | "relevance"
  | "name_asc"
  | "name_desc"
  | "period_asc"
  | "period_desc"
  | "newest";

// ---------------------------------------------------------------------------
// Core Interfaces
// ---------------------------------------------------------------------------

/**
 * Comprehensive licensing and copyright governance metadata for an asset.
 */
export interface LicensingStatus {
  license_label?: string | null;
  license_url?: string | null;
  noai: boolean;
  commercial_use_status: CommercialUseStatus;
  embed_permission_status: EmbedPermissionStatus;
  content_status: ContentReadinessStatus;
  rights_reviewed_by?: string | null;
  rights_reviewed_at?: string | null;
}

/**
 * Multimedia asset attached to a heritage place or story.
 */
export interface HeritageMediaAsset {
  id: string;
  place_id?: string | null;
  media_type: MediaType;
  source_platform?: string | null; // e.g. "sketchfab", "wikimedia", "openheritage3d", "cyark"
  original_url: string;
  title?: string | null;
  creator_name?: string | null;
  creator_url?: string | null;
  model_uid?: string | null; // Exact 32-hex character ID for Sketchfab
  license_label?: string | null;
  license_url?: string | null;
  noai: boolean;
  commercial_use_status: CommercialUseStatus;
  embed_permission_status: EmbedPermissionStatus;
  accuracy_grade: AccuracyGrade;
  provenance_notes?: string | null;
  attribution_text?: string | null;
  content_status: ContentReadinessStatus;
  embed_url?: string | null; // Sanitized embed URL (e.g. https://sketchfab.com/models/{uid}/embed)
  content_scope: string; // Defaults to "RBPC_HUE"
  created_at: string;
}

/**
 * Bibliographic citation and verified claim anchoring a heritage narrative.
 */
export interface HeritageSourceEvidence {
  id: string;
  place_id: string;
  source_url?: string | null;
  source_title: string;
  source_author?: string | null;
  publisher?: string | null;
  publication_year?: number | null;
  cited_section?: string | null;
  cited_page?: string | null;
  retrieved_at?: string | null;
  statement: string;
  interpretation_note?: string | null;
  evidence_status: EvidenceStatus;
  reuse_rights: HeritageReuseRights;
  reviewer_id?: string | null;
  reviewed_at?: string | null;
  content_scope: string; // Defaults to "RBPC_HUE"
}

/**
 * Directed semantic relationship between two heritage places.
 */
export interface HeritageRelation {
  id: string;
  from_place_id: string;
  to_place_id: string;
  from_place_slug?: string;
  from_place_name?: string;
  to_place_slug?: string;
  to_place_name?: string;
  relationship_type: RelationType;
  claim_id?: string | null;
  review_state: "draft" | "verified" | "disputed";
  created_at: string;
}

/**
 * Contextual engagement call-to-action on a heritage place.
 */
export interface HeritageEngagement {
  cta_kind: "none" | "story_journey" | "experience_inquiry" | "maker_profile";
  target_slug?: string | null;
  title_vi?: string | null;
  title_en?: string | null;
  notice?: string | null;
}

/**
 * Summary card model for heritage places in browse catalogue, search results, and maps.
 */
export interface HeritagePlace {
  id: string;
  slug: string;
  name_vi: string;
  name_en?: string | null;
  entity_type: HeritageEntityType;
  heritage_category: HeritageCategory | string;
  parent_id?: string | null;
  official_designation?: string | null; // e.g. "UNESCO World Heritage Component"
  official_reference_id?: string | null; // e.g. "678-001", "678-007"
  period_label?: string | null; // e.g. "Thời Nguyễn (1802-1945)"
  historical_state?:
    | "standing"
    | "restored"
    | "partially_lost"
    | "ruins"
    | "vanished"
    | string
    | null;
  location_lat?: number | null;
  location_lon?: number | null;
  geo_precision?:
    | "exact_gps"
    | "approximate_site"
    | "polygon_centroid"
    | "none_intangible"
    | null;
  current_access_status:
    | "open"
    | "restricted"
    | "undergoing_restoration"
    | "closed"
    | "unknown";
  access_notes?: string | null;
  visitor_summary_vi?: string | null;
  visitor_summary_en?: string | null;
  editorial_status: EditorialStatus;
  content_scope: string; // "RBPC_HUE"
  has_3d: boolean;
  thumbnail_url?: string | null;
  published_at?: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Deep place model for `/heritage/[slug]` place detail view,
 * containing verified narratives, source citations, media assets, and relationships.
 */
export interface HeritagePlaceDetail extends HeritagePlace {
  historical_summary_vi?: string | null;
  historical_summary_en?: string | null;
  parent_place?: HeritagePlace | null;
  child_places: HeritagePlace[];
  relations: HeritageRelation[];
  sources: HeritageSourceEvidence[];
  media: HeritageMediaAsset[];
  engagement?: HeritageEngagement | null;
}

// ---------------------------------------------------------------------------
// Search & Filter Parameters
// ---------------------------------------------------------------------------

/**
 * Filter and query parameters for `/explore` catalogue and API requests.
 */
export interface HeritageSearchFilters {
  q?: string;
  category?: HeritageCategory | "all";
  entity_type?: HeritageEntityType | "all";
  has_3d?: boolean;
  access_status?: "open" | "restricted" | "all";
  unesco_only?: boolean;
  sort?: HeritageSortOption;
  cursor?: string | null;
  limit?: number;
  scope?: string; // Defaults to "RBPC_HUE"
}

/**
 * Paginated list response for heritage catalogue queries.
 */
export interface HeritagePlaceListResponse {
  items: HeritagePlace[];
  next_cursor?: string | null;
  has_more: boolean;
  total_count?: number | null;
}

/**
 * Search hit item with relevance scoring and highlight field.
 */
export interface HeritageSearchItem {
  id: string;
  slug: string;
  name_vi: string;
  name_en?: string | null;
  entity_type: HeritageEntityType;
  heritage_category: HeritageCategory | string;
  summary?: string | null;
  matched_on?: "name_vi" | "name_en" | "official_reference_id" | "summary" | string | null;
  score?: number | null;
  has_3d: boolean;
  thumbnail_url?: string | null;
}

/**
 * Response for full-text / autocomplete search queries.
 */
export interface HeritageSearchResponse {
  items: HeritageSearchItem[];
  total: number;
  query: string;
  scope: string;
}
