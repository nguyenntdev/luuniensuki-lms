/**
 * TypeScript definitions for the STTTNNĐ (Lưu Niên — Đại Nội Huế) Aerial Map Engine.
 * Single source of truth for map assets, normalized UV coordinates, monument annotations,
 * and review/export contracts.
 *
 * Scope: STTT_IMPERIAL_CITY
 * Ref: LUU_NIEN_STTTNND_DAI_NOI_MASTER_SPEC_V2_1_INTEGRATED.md (§4, §6, §20)
 */

export type ImperialSiteCondition =
  | "extant"
  | "reconstructed"
  | "ruin"
  | "archaeological"
  | "lost"
  | "unknown";

export type LearningLevel =
  | "L1_DOCUMENTED"
  | "L2_ANALYZED"
  | "L2_LEARNING_READY"
  | "L3_SYNTHESIZED";

export type ReviewStatus =
  | "draft"
  | "in_review"
  | "approved"
  | "published"
  | "archived";

export type PositionConfidence =
  | "verified"
  | "approximate"
  | "uncertain";

export type MarkerStyle =
  | "monument"
  | "gate"
  | "palace"
  | "temple"
  | "pavilion"
  | "garden"
  | "bridge"
  | "bastion"
  | "residence"
  | (string & {});

export type AnnotationShapeType = "point" | "polygon" | "bbox";

export type EditorMode = "select" | "pan" | "add-point" | "draw-polygon";

export interface ImperialZone {
  id: string;
  slug: string;
  title_vi: string;
  title_en?: string | null;
  description_vi?: string | null;
  description?: string | null;
  display_order: number;
  created_at?: string;
  updated_at?: string;
}

export interface ImperialSite {
  id: string;
  zone_id?: string | null;
  zone_slug?: string | null;
  slug: string;
  name_vi: string;
  name_en?: string | null;
  name_han_nom?: string | null;
  chinese_name?: string | null;
  alternative_names?: string[] | null;
  site_type?: string | null;
  condition: ImperialSiteCondition;
  condition_description_vi?: string | null;
  learning_level: LearningLevel;
  published: boolean;
  construction_year?: number | null;
  reign?: string | null;
  historical_summary?: string | null;
  description_vi?: string | null;
  historical_significance?: string | null;
  guiding_inquiry_question?: string | null;
  guiding_question?: string | null;
  learning_prompts?: string[];
  primary_sources?: Array<{
    source_title: string;
    volume_or_chapter?: string;
    citation?: string;
    archival_unit?: string;
    reliability_level?: string;
  }>;
  pedagogical_task?: PedagogicalTask;
  rubrics?: Record<string, string>;
  timeline?: TimelineEvent[];
  imagery?: HistoricalImage[];
  claims_evidence?: ClaimEvidence[];
  spatial_connections?: SpatialConnection[];
  created_at?: string;
  updated_at?: string;
}

export interface PedagogicalTask {
  title: string;
  task_prompt: string;
  deliverable_type?: string;
  expected_evidence?: string;
  transfer_activity?: string;
  uncertainty_prompt?: string;
}

export interface RubricGuidelines {
  S1_spatial: string;
  S2_temporal: string;
  S3_evidence: string;
  S4_argument: string;
  [key: string]: string;
}

export interface TimelineEvent {
  year?: number | null;
  period_label?: string | null;
  event_title: string;
  description: string;
  source_ref?: string | null;
  is_verified: boolean;
}

export interface HistoricalImage {
  id?: string;
  title: string;
  url: string;
  caption?: string | null;
  year?: number | string | null;
  author_or_source: string;
  archive?: string | null;
  license_kind: string;
  copyright_note: string;
}

export interface ClaimEvidence {
  id: string;
  claim_title: string;
  assertion_vi: string;
  source_title: string;
  volume_or_chapter?: string | null;
  citation: string;
  archival_unit?: string | null;
  epistemic_status: "verified" | "probable" | "disputed";
  notes?: string | null;
}

export interface SpatialConnection {
  target_slug: string;
  target_name_vi: string;
  direction: "prev" | "next" | "related";
  axis_description: string;
}

export interface SiteDossierData {
  site: ImperialSite;
  zone?: ImperialZone | null;
  timeline: TimelineEvent[];
  imagery: HistoricalImage[];
  claims: ClaimEvidence[];
  guiding_question: string;
  task: {
    title: string;
    task_prompt: string;
    deliverable_type?: string;
    expected_evidence?: string;
    transfer_activity?: string;
    uncertainty_prompt?: string;
  };
  rubrics: RubricGuidelines;
  connections: SpatialConnection[];
  annotation?: ImperialMapAnnotation | null;
}

/**
 * Normalized coordinate on an image plane:
 * 0.0 <= u <= 1.0 (horizontal, left to right)
 * 0.0 <= v <= 1.0 (vertical, top to bottom)
 */
export interface UVCoordinate {
  u: number;
  v: number;
}

/**
 * Screen pixel coordinate within a container or viewport.
 */
export interface ScreenCoordinate {
  x: number;
  y: number;
}

/**
 * Viewport transform parameters for pan/zoom and letterbox offset.
 */
export interface ViewportTransform {
  scale: number;
  translateX: number;
  translateY: number;
  offsetX?: number;
  offsetY?: number;
  fittedWidth?: number;
  fittedHeight?: number;
}

export interface ImperialMapAsset {
  id: string;
  content_scope?: string;
  title_vi: string;
  slug: string;
  version: number;
  image_storage_key?: string;
  preview_storage_key?: string | null;
  image_url: string;
  preview_url?: string | null;
  image_sha256: string;
  mime_type?: string;
  width_px: number;
  height_px: number;
  source_title?: string;
  source_locator?: string | null;
  copyright_holder?: string | null;
  credit_text: string;
  license_kind: string;
  license_status?: "pending" | "approved" | "rejected";
  review_status: ReviewStatus;
  is_active: boolean;
  revision?: number;
  row_version?: number;
  created_at?: string;
  updated_at?: string;
  published_at?: string | null;
}

export interface ImperialMapAnnotation {
  id: string;
  map_asset_id: string;
  site_id: string;
  shape_type: AnnotationShapeType;
  u: number;
  v: number;
  polygon_uv?: UVCoordinate[] | null;
  label?: string | null;
  marker_style: MarkerStyle;
  z_index?: number;
  is_visible?: boolean;
  review_status: ReviewStatus;
  position_confidence: PositionConfidence;
  position_source_ref?: string | null;
  editorial_notes?: string | null;
  row_version: number;
  site?: {
    id?: string;
    slug: string;
    name_vi: string;
    name_han_nom?: string | null;
    chinese_name?: string | null;
    summary_vi?: string | null;
    guiding_question?: string | null;
    zone_slug?: string;
    learning_level?: LearningLevel;
    condition?: ImperialSiteCondition;
  };
  created_at?: string;
  updated_at?: string;
  published_at?: string | null;
}

export type ImperialSiteDetail = ImperialSite;

export interface ImperialSiteEvidence {
  site_slug: string;
  site_name_vi?: string;
  sources: Array<{
    id?: string;
    title?: string;
    source_title?: string;
    volume_or_chapter?: string;
    citation?: string;
    archival_unit?: string;
    reliability_level?: string;
    source_type?: string;
    author?: string;
    year?: number | string;
    quote?: string;
  }>;
  claims?: Array<{
    id?: string;
    claim_text?: string;
    statement_vi?: string;
    confidence?: string;
    verification_status?: string;
  }>;
}

export interface ImperialSiteTimelineEvent {
  id?: string;
  year: number | string;
  title: string;
  description: string;
  reign?: string;
  event_type?: string;
}

export interface ImperialSiteTimeline {
  site_slug: string;
  site_name_vi?: string;
  events: ImperialSiteTimelineEvent[];
}

/**
 * Public response contract for the active aerial map (GET /api/v1/imperial/maps/active).
 */
export interface ActiveMapResponse {
  map: {
    id: string;
    slug?: string;
    title_vi?: string;
    version: number;
    image: {
      url: string;
      width: number;
      height: number;
    };
    credit: string;
    license_kind: string;
    revision: number;
  };
  annotations: ImperialMapAnnotation[];
}

/**
 * Annotations listing response contract (GET /api/v1/imperial/maps/{mapId}/annotations).
 */
export interface MapAnnotationsResponse {
  map_id: string;
  version: number;
  revision: number;
  annotations: ImperialMapAnnotation[];
  total: number;
}

export interface AnnotationExportItem {
  site_slug: string;
  u: number;
  v: number;
  shape_type: AnnotationShapeType;
  polygon_uv?: UVCoordinate[];
  label?: string;
  marker_style?: MarkerStyle;
  position_confidence?: PositionConfidence;
  position_source_ref?: string | null;
}

/**
 * Full export payload for atomic backup/import (schema imperial-annotations/1.0).
 */
export interface AnnotationExportPayload {
  schema_version: string;
  scope: string;
  map: {
    slug: string;
    version: number;
    image_sha256: string;
  };
  annotations: AnnotationExportItem[];
  exported_at: string;
  export_sha256: string;
}

export interface ImportDryRunIssue {
  type: "error" | "warning";
  code: string;
  message: string;
  site_slug?: string;
  annotation_index?: number;
}

export interface ImportDryRunResult {
  valid: boolean;
  created_count: number;
  updated_count: number;
  skipped_count: number;
  total_count: number;
  image_hash_matched: boolean;
  issues: ImportDryRunIssue[];
}

/**
 * Curated Historical Learning Trail / Path Definitions (§20).
 */
export interface ImperialTrailRequiredSource {
  title: string;
  citation: string;
  type: "chronicle" | "archival_photo" | "epigraphy" | "map" | "conservation_report";
}

export interface ImperialTrailStop {
  order: number;
  monument_slug: string;
  monument_name_vi: string;
  monument_name_han_nom?: string;
  title: string;
  inquiry_question: string;
  step_prompt: string;
  required_sources: ImperialTrailRequiredSource[];
  observation_points: string[];
  virtual_fieldwork: {
    overview_text: string;
    media_url: string;
    media_caption: string;
    historical_clues: string[];
  };
  task_prompt: string;
  expected_evidence?: string;
  u: number;
  v: number;
}

export interface ImperialTrail {
  slug: string;
  title: string;
  subtitle: string;
  description: string;
  duration_minutes: number;
  age_group: string;
  target_grade: string;
  pedagogical_objectives: string[];
  stops: ImperialTrailStop[];
  cover_image: string;
  theme_color: string;
  difficulty: "Cơ bản" | "Trung cấp" | "Nâng cao";
}

/**
 * Historical inquiry student submission and assessment types (M-E-E & S1-S4 Rubrics).
 */
export interface RubricScoreState {
  s1_spatial: number; // 0 - 3
  s2_temporal: number; // 0 - 3
  s3_evidence: number; // 0 - 3
  s4_argument: number; // 0 - 3
  total: number; // 0 - 12
  normalized_10: number; // 0.0 - 10.0
}

export interface StudentSubmission {
  id: string;
  monument_slug?: string;
  monument_name_vi?: string;
  trail_slug?: string;
  trail_title?: string;
  student_id: string;
  student_name: string;
  student_class: string;
  student_avatar?: string;
  claim: string;
  evidence: string;
  evidence_citations: string[];
  explanation: string;
  notes?: string;
  submitted_at: string;
  status: "submitted" | "graded" | "resubmit_requested";
  scores?: RubricScoreState;
  teacher_feedback?: string;
  graded_at?: string;
  graded_by?: string;
}

