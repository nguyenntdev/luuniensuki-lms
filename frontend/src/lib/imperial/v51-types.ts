/**
 * TypeScript definitions for STTTNNĐ (Lưu Niên — Đại Nội Huế) Follow-On SPEC V5.1.
 * Covers:
 * 1. Learning Media & Media Hotspots (image-local UV coordinates, 2D/360°/3D)
 * 2. Art Details (6 core pedagogical sections: observation, story, symbolism, values, sources, questions)
 * 3. Heritage Detective Clues & Interactive Game Questions
 * 4. Teacher Assignment Releases
 *
 * Scope: STTT_IMPERIAL_CITY
 * Ref: LUU_NIEN_STTTNND_DAI_NOI_MASTER_SPEC_V5_1
 */

export type PointKind = "point" | "rect" | "polygon";

export type LearningMediaKind = "image" | "panorama360" | "model3d";

export type MediaAssetContext = "extant" | "historical_photo" | "restoration_drawing";

export type ArtDetailKind = "carving" | "pattern" | "painting" | "mosaic" | "relief";

export type ArtDetailStoryType =
  | "documented_event"
  | "legend"
  | "oral_account"
  | "interpretation";

export type EvidenceStrength = "verified" | "probable" | "traditional";

export type ClueTargetType = "site" | "art_detail";

export type QuestionType = "multiple_choice" | "matching" | "hotspot_identify";

export interface UVCoordinate {
  u: number;
  v: number;
}

export interface PositionPayload {
  yaw?: number;
  pitch?: number;
  fov?: number;
  width?: number;
  height?: number;
  points?: UVCoordinate[];
  [key: string]: unknown;
}

export interface ImperialMediaHotspot {
  id: string;
  media_id: string;
  point_kind: PointKind;
  u: number; // 0.0 .. 1.0 (left)
  v: number; // 0.0 .. 1.0 (top)
  position_payload?: PositionPayload | null;
  title: string;
  description?: string | null;
  detail_id?: string | null;
  art_detail_slug?: string | null;
  art_detail?: ImperialArtDetail | null;
  review_status?: "draft" | "in_review" | "approved" | "published" | "archived";
  created_at?: string;
  updated_at?: string;
  row_version?: number;
}

export interface ImperialLearningMedia {
  id: string;
  content_scope?: string;
  site_id?: string | null;
  site_slug?: string | null;
  site_name_vi?: string | null;
  kind: LearningMediaKind;
  media_url: string;
  thumbnail_url?: string | null;
  title_vi: string;
  title_en?: string | null;
  asset_revision?: number;
  width_px?: number | null;
  height_px?: number | null;
  license_status?: "pending" | "approved" | "rejected";
  review_status?: "draft" | "in_review" | "approved" | "published" | "archived";
  alt_text?: string | null;
  credit_text?: string | null;
  asset_context?: MediaAssetContext;
  hotspots?: ImperialMediaHotspot[];
  created_at?: string;
  updated_at?: string;
  row_version?: number;
}

export interface ArtDetailClaimSource {
  id?: string;
  detail_id?: string;
  section: string;
  claim_text: string;
  source_title: string;
  source_locator?: string | null;
  evidence_strength: EvidenceStrength;
  reliability_level?: string;
  citation_quote?: string;
  created_at?: string;
}

export interface ArtDetailQuestion {
  id: string;
  detail_id?: string;
  question_type: QuestionType;
  prompt: string;
  options: string[];
  answer_key: string;
  explanation?: string | null;
  display_order?: number;
  created_at?: string;
}

export interface ImperialArtDetail {
  id: string;
  content_scope?: string;
  site_id?: string | null;
  site_slug?: string | null;
  site_name_vi?: string | null;
  title: string;
  slug: string;
  kind: ArtDetailKind;
  motif?: string | null;
  material?: string | null;
  technique?: string | null;
  // 1. Visual observation
  description_observation?: string | null;
  // 2. Story / Legend / Event
  story_body?: string | null;
  story_type: ArtDetailStoryType;
  // 3. Symbolic Meaning
  meaning_body?: string | null;
  // 4. Cultural & Historical Value
  historical_value_body?: string | null;
  cultural_value_body?: string | null;
  art_value_body?: string | null;
  review_status?: "draft" | "in_review" | "approved" | "published" | "archived";
  content_revision?: number;
  image_url?: string | null;
  gallery_urls?: string[];
  // 5. Corroborating Sources
  claim_sources?: ArtDetailClaimSource[];
  // 6. Formative Reinforcement Questions
  questions?: ArtDetailQuestion[];
  hotspots?: ImperialMediaHotspot[];
  created_at?: string;
  updated_at?: string;
  row_version?: number;
}

export interface ImperialClue {
  id: string;
  title: string;
  clue_text: string;
  target_type: ClueTargetType;
  target_id?: string;
  target_slug?: string;
  hint_steps: string[];
  grade_level?: string | null;
  difficulty?: "easy" | "medium" | "hard" | string | null;
  points?: number;
  review_status?: string;
  created_at?: string;
}

export interface ClueAttemptResult {
  success: boolean;
  points_awarded: number;
  message: string;
  next_clue_id?: string | null;
  clue_id: string;
  attempt_number: number;
}

export interface GameQuestion {
  id: string;
  site_id?: string | null;
  site_slug?: string | null;
  detail_id?: string | null;
  question_type: QuestionType;
  prompt: string;
  options: string[];
  answer_key?: string;
  points?: number;
  explanation_why?: string | null;
  source_citation?: string | null;
}

export interface GameSubmitResult {
  correct: boolean;
  correct_index: number;
  explanation: string;
  score_delta: number;
}

export interface AssignmentRelease {
  id: string;
  teacher_id?: string;
  class_name: string;
  journey_slug: string;
  title: string;
  due_date?: string | null;
  rubric_weights?: Record<string, number>;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

// Story type badge and label metadata
export const STORY_TYPE_METADATA: Record<
  ArtDetailStoryType,
  { label: string; badgeColor: string; description: string }
> = {
  documented_event: {
    label: "Sử liệu thành văn",
    badgeColor: "bg-blue-500/15 text-blue-700 dark:text-blue-300 border-blue-500/30",
    description: "Sự kiện được ghi chép trong chính sử triều Nguyễn (Đại Nam Thực Lục, Hội Điển).",
  },
  legend: {
    label: "Huyền sử & Điển tích",
    badgeColor: "bg-purple-500/15 text-purple-700 dark:text-purple-300 border-purple-500/30",
    description: "Điển tích văn học, biểu tượng vũ trụ hoặc truyền thuyết gắn với cung đình.",
  },
  oral_account: {
    label: "Giai thoại dân gian",
    badgeColor: "bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/30",
    description: "Giai thoại dân gian và lời kể truyền khẩu của nhân chứng lịch sử xứ Huế.",
  },
  interpretation: {
    label: "Khảo cứu mỹ thuật",
    badgeColor: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-500/30",
    description: "Nhận định và khảo cứu từ các chuyên gia bảo tồn di sản và mỹ thuật học.",
  },
};

export const EVIDENCE_STRENGTH_METADATA: Record<
  EvidenceStrength,
  { label: string; badgeColor: string }
> = {
  verified: {
    label: "Sử liệu nguyên cấp",
    badgeColor: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-500/30",
  },
  probable: {
    label: "Tài liệu đối chiếu",
    badgeColor: "bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-500/30",
  },
  traditional: {
    label: "Truyền thống lưu truyền",
    badgeColor: "bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/30",
  },
};
