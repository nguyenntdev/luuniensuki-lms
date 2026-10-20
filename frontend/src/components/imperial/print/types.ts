export interface PrimarySourceItem {
  source_title: string;
  volume_or_chapter?: string;
  citation: string;
  archival_unit?: string;
  reliability_level?: string;
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
  selected_monument_slugs: string[];
}
