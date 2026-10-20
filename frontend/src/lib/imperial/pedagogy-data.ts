import lessonPlan from "../../../../data/imperial/lesson_plan_45m.json";
import fieldworkWorksheet from "../../../../data/imperial/fieldwork_worksheet.json";

export interface LessonPlanData {
  content_scope: string;
  document_type: string;
  version: string;
  title_vi: string;
  target_grade: string;
  subject: string;
  duration_minutes: number;
  curriculum_framework: string;
  objectives: {
    historical_competencies: Array<{
      code: string;
      name_vi: string;
      description_vi: string;
    }>;
    qualities: Array<{
      name_vi: string;
      description_vi: string;
    }>;
  };
  teaching_equipment_and_digital_materials: {
    teacher_materials: string[];
    student_materials: string[];
  };
  activities: Array<{
    activity_number: number;
    name_vi: string;
    duration_minutes: number;
    objective_vi: string;
    teacher_actions: string[];
    student_actions: string[];
    deliverables_vi: string;
    assessment_criteria_vi: string;
  }>;
  rubrics: {
    scale_description: string;
    levels: Array<{ score: number; label_vi: string }>;
    criteria: Array<{
      id: string;
      dimension: string;
      name_vi: string;
      descriptors: Record<string, string>;
    }>;
    overall_bands: Array<{
      min_score: number;
      max_score: number;
      classification_vi: string;
    }>;
  };
  appendix?: {
    exit_ticket_sample?: {
      prompt_vi: string;
      expected_evidence_vi: string;
      time_allowed_minutes: number;
    };
  };
}

export interface FieldworkWorksheetData {
  content_scope: string;
  document_type: string;
  version: string;
  title_vi: string;
  subtitle_vi: string;
  target_audience: string;
  instructions_vi: string;
  metadata_fields: Array<{ key: string; label_vi: string }>;
  columns: Array<{
    column_id: string;
    number: number;
    title_vi: string;
    description_vi: string;
  }>;
  stations: Array<{
    station_index: number;
    monument_slug: string;
    monument_name_vi: string;
    zone_name_vi: string;
    observation_prompt_vi: string;
    evidence_prompt_vi: string;
    guiding_source: {
      source_title: string;
      volume: string;
      key_quote_vi: string;
    };
    conclusion_guide_vi: string;
  }>;
  exit_ticket: {
    title_vi: string;
    instructions_vi: string;
    questions: Array<{
      id: string;
      question_vi: string;
      space_for_answer_lines: number;
    }>;
  };
  rubric_summary: {
    dimensions: Array<{ id: string; name_vi: string; target: string }>;
  };
  export_helper?: {
    printable_css_page_setup: string;
    target_dpi: number;
    recommended_layout: string;
  };
}

export const LESSON_PLAN_45M: LessonPlanData = lessonPlan as unknown as LessonPlanData;
export const FIELDWORK_WORKSHEET: FieldworkWorksheetData = fieldworkWorksheet as unknown as FieldworkWorksheetData;
