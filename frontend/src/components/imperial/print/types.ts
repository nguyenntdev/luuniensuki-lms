export interface PrimarySourceItem {
  source_title: string;
  volume_or_chapter?: string;
  citation: string;
  archival_unit?: string;
  reliability_level?: string;
  rights_owner?: string;
  license?: string;
}

export interface OfflineRubbingItem {
  asset_url: string;
  local_path?: string;
  caption_vi?: string;
  high_contrast_css?: string;
  rights_attribution?: string;
  legal_basis?: string;
}

export interface OfflineInspectionTaskItem {
  task_title_vi: string;
  instructions_vi: string;
  checkpoints: string[];
  sketch_prompt_vi?: string;
  paper_achievable: boolean;
  ar_or_smartphone_required: boolean;
}

export interface AudioGuideTranscriptItem {
  track_title_vi: string;
  narrator: string;
  duration_text: string;
  duration_seconds?: number;
  script_text: string;
  key_quotes_vi?: string[];
}

export interface PrintableStation {
  station_index: number;
  monument_slug: string;
  monument_name_vi: string;
  zone_name_vi: string;
  zone_slug?: string;
  reign?: string;
  construction_year?: number;
  condition_description_vi?: string;
  observation_prompt_vi: string;
  observation_sample_answer_vi: string;
  primary_source: PrimarySourceItem;
  secondary_sources?: PrimarySourceItem[];
  conclusion_guide_vi: string;
  mee_claim_sample_vi: string;
  mee_evidence_sample_vi: string;
  mee_uncertainty_sample_vi: string;
  digital_coordinate_hint?: string;
  rubbing_asset?: OfflineRubbingItem;
  offline_task?: OfflineInspectionTaskItem;
  audio_transcript?: AudioGuideTranscriptItem;
}

export interface RubricDimensionItem {
  id: "S1" | "S2" | "S3" | "S4";
  name_vi: string;
  dimension: string;
  description_vi: string;
  max_score: number;
}

export interface ExitTicketQuestion {
  id: string;
  question_vi: string;
  space_for_answer_lines: number;
  sample_answer_vi?: string;
}

export interface WorksheetPrintConfig {
  school_name: string;
  department_name: string;
  lesson_code: string;
  grade_level: string;
  class_name: string;
  student_name?: string;
  teacher_name?: string;
  date_vi?: string;
  orientation: "landscape" | "portrait";
  teacher_key_mode: boolean;
  include_qr: boolean;
  include_rubric: boolean;
  include_exit_ticket: boolean;
  include_rubbings?: boolean;
  include_transcripts?: boolean;
  include_offline_tasks?: boolean;
  high_contrast_rubbings?: boolean;
  selected_monument_slugs: string[];
}
