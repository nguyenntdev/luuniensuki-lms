/**
 * Curriculum Competency Catalog Types (Vietnam 2018 General Education Program).
 * Ticket V5-T095 / Wave W09 / Slot A05.
 */

export type StandardCompetencyDomain =
  | 'historical_literacy'
  | 'source_criticism'
  | 'historical_empathy'
  | 'historical_communication';

export type CompetencyGradeBand = 'GRADE_6_7' | 'GRADE_8_9' | 'GRADE_10_12' | 'ALL';

export type CompetencyMappingStatus = 'unreviewed' | 'verified' | 'flagged' | 'deprecated';

export type CompetencyFlagReason =
  | 'inaccurate_grade_level'
  | 'misaligned_competency'
  | 'historical_inaccuracy'
  | 'pedagogical_concern'
  | 'other';

export interface GradeBandDescriptor {
  min_grade: number;
  max_grade: number;
  descriptor_vi: string;
  descriptor_en?: string;
}

export interface CurriculumCompetency {
  id: string;
  code: string;
  standard_framework: string;
  domain: StandardCompetencyDomain;
  name_vi: string;
  name_en: string;
  description_vi: string;
  description_en: string;
  grade_band_descriptors: Record<string, GradeBandDescriptor>;
  is_active: boolean;
  created_at: string;
}

export interface CurriculumCompetencyRelicMapping {
  id: string;
  competency_id: string;
  competency_code?: string;
  competency_name_vi?: string;
  competency_domain?: string;
  relic_urn_slug?: string | null;
  relic_motif_id?: string | null;
  entity_slug?: string | null;
  grade_band: CompetencyGradeBand | string;
  min_grade: number;
  max_grade: number;
  learning_activity_vi: string;
  learning_activity_en?: string | null;
  evidence_requirement_vi: string;
  evidence_requirement_en?: string | null;
  status: CompetencyMappingStatus;
  is_reviewed: boolean;
  review_warning?: string | null;
  flag_count: number;
  created_by_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CurriculumCompetencyFlag {
  id: string;
  mapping_id: string;
  flagged_by_id: string;
  flagged_by_name?: string | null;
  reason: CompetencyFlagReason | string;
  commentary: string;
  suggested_correction?: Record<string, unknown> | null;
  status: 'pending' | 'reviewed' | 'resolved' | 'dismissed';
  resolved_by_id?: string | null;
  resolution_notes?: string | null;
  created_at: string;
  resolved_at?: string | null;
}

export interface FlagMappingInput {
  reason: CompetencyFlagReason | string;
  commentary: string;
  suggested_correction?: Record<string, unknown>;
}

export interface EditMappingInput {
  min_grade?: number;
  max_grade?: number;
  grade_band?: string;
  learning_activity_vi?: string;
  learning_activity_en?: string;
  evidence_requirement_vi?: string;
  evidence_requirement_en?: string;
}
