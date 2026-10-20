/**
 * Standalone Rubric Scoring Engine & Pedagogical Competency Analytics
 * for STTTNNĐ (Lưu Niên — Đại Nội Huế) Follow-On SPEC V5.1.
 * Ref: 07_ASSIGNMENTS_TEACHER.md & GDPT 2018 History Framework.
 *
 * Covers the 4 core pedagogical competencies:
 * - S1: Năng lực Không gian (Spatial Reasoning)
 * - S2: Năng lực Thời gian (Temporal Reasoning)
 * - S3: Năng lực Sử liệu & Bằng chứng (Source & Evidence Analysis)
 * - S4: Năng lực Lập luận & Giới hạn Tri thức (Historical Explanation & Epistemic Humility)
 */

import type { RubricScoreState, StudentSubmission } from "./map-types";

// =========================================================================== //
// Types & Interfaces
// =========================================================================== //

export type RubricCriterionKey = "s1" | "s2" | "s3" | "s4";

export type RubricCriterionKeyAlias =
  | "s1"
  | "s2"
  | "s3"
  | "s4"
  | "s1_spatial"
  | "s2_temporal"
  | "s3_evidence"
  | "s4_argument"
  | "S1"
  | "S2"
  | "S3"
  | "S4"
  | "S1_spatial"
  | "S2_temporal"
  | "S3_evidence"
  | "S4_argument";

export type CompetencyClassification =
  | "Xuất sắc"
  | "Giỏi"
  | "Khá"
  | "Đạt"
  | "Cần rèn luyện";

export type CompetencyClassificationEn =
  | "Excellent"
  | "Very Good"
  | "Good"
  | "Competent"
  | "Needs Improvement";

export interface RubricLevelDescriptor {
  score: number;
  label: string;
  desc: string;
}

export interface RubricCriterionMeta {
  id: "S1" | "S2" | "S3" | "S4";
  key: RubricCriterionKey;
  dimensionVi: string;
  dimensionEn: string;
  titleVi: string;
  description: string;
  levels: RubricLevelDescriptor[];
  recommendationPrompt: string;
}

export interface RubricRawScores {
  s1: number;
  s2: number;
  s3: number;
  s4: number;
}

export type RubricScoresInput =
  | RubricRawScores
  | RubricScoreState
  | {
      s1?: number;
      s2?: number;
      s3?: number;
      s4?: number;
      s1_spatial?: number;
      s2_temporal?: number;
      s3_evidence?: number;
      s4_argument?: number;
      [key: string]: unknown;
    };

export type RubricWeights = Partial<Record<RubricCriterionKeyAlias, number>> | Record<string, number>;

export interface RubricCalculationOptions {
  /** Maximum score per criterion (commonly 3 or 4). Default: 3. */
  maxScorePerCriterion?: number;
  /** Custom scale (3 for 0-3 scale, 4 for 0-4 scale). Default: 3. */
  scale?: 3 | 4 | number;
}

export interface CriterionBreakdown {
  criterionId: "S1" | "S2" | "S3" | "S4";
  key: RubricCriterionKey;
  dimensionVi: string;
  dimensionEn: string;
  rawScore: number;
  maxScore: number;
  weight: number;
  weightedScore: number;
  percentage: number;
  levelLabel: string;
  descriptor: string;
}

export interface RubricCalculationResult {
  rawScore: number;
  maxPossibleScore: number;
  weightedScore: number;
  maxWeightedScore: number;
  percentage: number;
  normalized10: number;
  classification: CompetencyClassification;
  classificationEn: CompetencyClassificationEn;
  criteriaBreakdown: Record<RubricCriterionKey, CriterionBreakdown>;
}

export interface RubricValidationResult {
  valid: boolean;
  errors: string[];
  normalizedScores?: RubricRawScores;
}

export interface RubricFeedbackResult {
  summary: string;
  classification: CompetencyClassification;
  normalized10: number;
  strengths: string[];
  improvementAreas: string[];
  recommendations: string[];
  teacherNotes?: string;
  fullReportText: string;
}

export interface CSVExportOptions {
  /** When true, masks student names (e.g., "Học sinh HS-101") and uses anonymized codes. Default: false. */
  anonymize?: boolean;
  /** Custom anonymization prefix. Default: "HS-". */
  anonymizePrefix?: string;
  /** Include timestamp columns. Default: true. */
  includeTimestamps?: boolean;
  /** Include teacher feedback text. Default: true. */
  includeTeacherFeedback?: boolean;
  /** Customizable weights for score calculation. */
  weights?: RubricWeights;
  /** Maximum score per criterion. Default: 3. */
  maxScorePerCriterion?: number;
  /** CSV delimiter. Default: ",". */
  delimiter?: string;
  /** Include UTF-8 Byte Order Mark (\uFEFF) for Microsoft Excel compatibility. Default: true. */
  includeBOM?: boolean;
}

// =========================================================================== //
// Criterion Master Metadata (Spec §20 & V5.1)
// =========================================================================== //

export const RUBRIC_METADATA: Record<RubricCriterionKey, RubricCriterionMeta> = {
  s1: {
    id: "S1",
    key: "s1",
    dimensionVi: "Năng lực Không gian",
    dimensionEn: "Spatial Reasoning",
    titleVi: "S1: Năng lực Không gian",
    description:
      "Nhận diện vị trí, hướng trục Dũng Đạo / Thần đạo, trật tự phân tầng không gian và phương vị phong thủy.",
    recommendationPrompt:
      "Rèn luyện kỹ năng định vị trên không ảnh trực giao, quan sát hướng trục Dũng Đạo và mối quan hệ giữa công trình với toàn bộ bố cục Hoàng thành.",
    levels: [
      {
        score: 0,
        label: "Chưa đạt",
        desc: "Chưa xác định được vị trí hoặc nhầm lẫn nghiêm trọng về không gian di tích.",
      },
      {
        score: 1,
        label: "Cơ bản",
        desc: "Xác định được công trình đơn lẻ nhưng chưa thấy mối liên hệ với trục quy hoạch chung.",
      },
      {
        score: 2,
        label: "Khá",
        desc: "Xác định chính xác vị trí, hướng nhìn và vai trò của công trình trên trục Dũng Đạo.",
      },
      {
        score: 3,
        label: "Xuất sắc",
        desc: "Phân tích sâu sắc vị thế phong thủy, trục thần đạo và sự phân tầng không gian quyền lực.",
      },
      {
        score: 4,
        label: "Chuyên sâu",
        desc: "Làm chủ tư duy không gian đa tầng, phân tích quan hệ vi khí hậu, kiến trúc cảnh quan và địa lý phong thủy Cố đô.",
      },
    ],
  },
  s2: {
    id: "S2",
    key: "s2",
    dimensionVi: "Năng lực Thời gian",
    dimensionEn: "Temporal Reasoning",
    titleVi: "S2: Năng lực Thời gian",
    description:
      "Nhận diện mốc khởi dựng, các giai đoạn trùng tu, tác động của biến thiên lịch sử, chiến tranh và phục hồi di sản.",
    recommendationPrompt:
      "Xây dựng dòng thời gian biên niên (chronological timeline), phân biệt rõ niên đại khởi dựng và các đợt đại trùng tu hoặc tái thiết sau chiến tranh.",
    levels: [
      {
        score: 0,
        label: "Chưa đạt",
        desc: "Không nêu hoặc nêu sai mốc thời gian lịch sử của di tích.",
      },
      {
        score: 1,
        label: "Cơ bản",
        desc: "Nêu được niên đại khởi công xây dựng cơ bản (triều vua Gia Long hoặc Minh Mạng).",
      },
      {
        score: 2,
        label: "Khá",
        desc: "Nêu đúng các mốc biến thiên: khởi dựng, tái thiết thời Khải Định và tổn thất chiến tranh.",
      },
      {
        score: 3,
        label: "Xuất sắc",
        desc: "Đặt công trình vào bối cảnh lịch sử cụ thể, phân tích ý nghĩa phục hồi di sản thời hiện đại.",
      },
      {
        score: 4,
        label: "Chuyên sâu",
        desc: "Tổng hợp tiến trình biến chuyển di sản qua các thời kỳ lịch sử, đánh giá tính chân xác và diễn biến qua các cuộc trùng tu lớn.",
      },
    ],
  },
  s3: {
    id: "S3",
    key: "s3",
    dimensionVi: "Năng lực Sử liệu & Bằng chứng",
    dimensionEn: "Source & Evidence Analysis",
    titleVi: "S3: Năng lực Sử liệu & Bằng chứng",
    description:
      "Khai thác chính sử triều Nguyễn (Đại Nam Thực Lục, Hội Điển), Châu bản, văn khắc và tư liệu ảnh lưu trữ (EFEO).",
    recommendationPrompt:
      "Tra cứu trực tiếp hồ sơ sử liệu (Evidence Ledger), ghi rõ tên bộ sử, số quyển và trích đoạn nguyên văn làm bằng chứng đối chiếu.",
    levels: [
      {
        score: 0,
        label: "Chưa đạt",
        desc: "Không có dẫn chứng sử liệu hoặc đưa ra nhận định cảm tính không căn cứ.",
      },
      {
        score: 1,
        label: "Cơ bản",
        desc: "Có dẫn chứng chung chung nhưng không rõ nguồn gốc hoặc chưa đối chiếu kiểm chứng.",
      },
      {
        score: 2,
        label: "Khá",
        desc: "Trích dẫn đúng tên văn bản chính sử triều Nguyễn hoặc tư liệu ảnh lưu trữ Pháp (EFEO).",
      },
      {
        score: 3,
        label: "Xuất sắc",
        desc: "Phê phán và đối chiếu đa nguồn: kết hợp chính sử triều Nguyễn, ảnh tư liệu và khảo cổ học.",
      },
      {
        score: 4,
        label: "Chuyên sâu",
        desc: "Giám định độ tin cậy của nguồn sử liệu nguyên cấp, chỉ ra giá trị và giới hạn của văn bản hành chính triều Nguyễn.",
      },
    ],
  },
  s4: {
    id: "S4",
    key: "s4",
    dimensionVi: "Năng lực Lập luận & Giới hạn Tri thức",
    dimensionEn: "Historical Explanation & Epistemic Humility",
    titleVi: "S4: Năng lực Lập luận & Giới hạn Tri thức",
    description:
      "Cấu trúc câu trả lời theo mô hình M-E-E, logic mạch lạc, phân định rành mạch giữa sự thật lịch sử và giới hạn tri thức.",
    recommendationPrompt:
      "Tuân thủ cấu trúc M-E-E (Mệnh đề - Bằng chứng - Diễn giải); phân định rõ 'Điều chắc chắn' và 'Điều còn cần kiểm chứng' (Epistemic Humility).",
    levels: [
      {
        score: 0,
        label: "Chưa đạt",
        desc: "Thiếu lập luận, câu trả lời mâu thuẫn hoặc chưa cấu trúc thành mệnh đề hoàn chỉnh.",
      },
      {
        score: 1,
        label: "Cơ bản",
        desc: "Lập luận đơn giản, có nêu mệnh đề nhưng mối liên kết với bằng chứng còn rời rạc.",
      },
      {
        score: 2,
        label: "Khá",
        desc: "Lập luận mạch lạc theo mô hình M-E-E: Mệnh đề rõ, Bằng chứng khớp, Diễn giải logic.",
      },
      {
        score: 3,
        label: "Xuất sắc",
        desc: "Lập luận sắc bén, có tư duy phản biện, phân biệt rõ sự thật lịch sử và cách diễn giải đương đại.",
      },
      {
        score: 4,
        label: "Chuyên sâu",
        desc: "Lập luận đa chiều mang tính học thuật cao, thể hiện rõ tính khiêm nhường tri thức trước các giả thuyết còn tranh biện.",
      },
    ],
  },
};

// =========================================================================== //
// Helper Normalizers
// =========================================================================== //

/**
 * Normalizes any variation of score key input into `{ s1, s2, s3, s4 }`.
 */
export function normalizeScoreKeys(input: RubricScoresInput | null | undefined): RubricRawScores {
  if (!input || typeof input !== "object") {
    return { s1: 0, s2: 0, s3: 0, s4: 0 };
  }

  const rec = input as Record<string, unknown>;

  const pickNum = (...keys: string[]): number => {
    for (const k of keys) {
      const v = rec[k];
      if (typeof v === "number" && !Number.isNaN(v)) return v;
      if (typeof v === "string" && v.trim() !== "" && !Number.isNaN(Number(v))) {
        return Number(v);
      }
    }
    return 0;
  };

  return {
    s1: pickNum("s1", "s1_spatial", "S1", "S1_spatial"),
    s2: pickNum("s2", "s2_temporal", "S2", "S2_temporal"),
    s3: pickNum("s3", "s3_evidence", "S3", "S3_evidence"),
    s4: pickNum("s4", "s4_argument", "S4", "S4_argument"),
  };
}

/**
 * Normalizes weight configuration into standard `{ s1, s2, s3, s4 }` multipliers.
 */
export function normalizeWeights(weights?: RubricWeights | null): RubricRawScores {
  if (!weights || typeof weights !== "object") {
    return { s1: 1, s2: 1, s3: 1, s4: 1 };
  }

  const rec = weights as Record<string, unknown>;

  const pickWeight = (fallback: number, ...keys: string[]): number => {
    for (const k of keys) {
      const v = rec[k];
      if (typeof v === "number" && !Number.isNaN(v) && v > 0) return v;
      if (typeof v === "string" && !Number.isNaN(Number(v)) && Number(v) > 0) {
        return Number(v);
      }
    }
    return fallback;
  };

  return {
    s1: pickWeight(1, "s1", "s1_spatial", "S1", "S1_spatial"),
    s2: pickWeight(1, "s2", "s2_temporal", "S2", "S2_temporal"),
    s3: pickWeight(1, "s3", "s3_evidence", "S3", "S3_evidence"),
    s4: pickWeight(1, "s4", "s4_argument", "S4", "S4_argument"),
  };
}

/**
 * Maps normalized 10.0 scale grade to 5-tier Vietnamese competency classification.
 */
export function classifyScore(normalized10: number): {
  vi: CompetencyClassification;
  en: CompetencyClassificationEn;
} {
  if (normalized10 >= 9.0) {
    return { vi: "Xuất sắc", en: "Excellent" };
  }
  if (normalized10 >= 8.0) {
    return { vi: "Giỏi", en: "Very Good" };
  }
  if (normalized10 >= 6.5) {
    return { vi: "Khá", en: "Good" };
  }
  if (normalized10 >= 5.0) {
    return { vi: "Đạt", en: "Competent" };
  }
  return { vi: "Cần rèn luyện", en: "Needs Improvement" };
}

// =========================================================================== //
// Core Scoring & Calculation Engine
// =========================================================================== //

/**
 * Calculates raw score, weighted percentage, normalized 10.0 grade,
 * and 5-tier pedagogical competency classification.
 *
 * @param scores Raw scores for S1-S4
 * @param weights Optional customizable weights per criterion
 * @param options Scale options (0-3 or 0-4 point scale)
 */
export function calculateRubricScore(
  scores: RubricScoresInput,
  weights?: RubricWeights,
  options?: RubricCalculationOptions,
): RubricCalculationResult {
  const maxScore = options?.maxScorePerCriterion ?? options?.scale ?? 3;
  const raw = normalizeScoreKeys(scores);
  const w = normalizeWeights(weights);

  const criteriaKeys: RubricCriterionKey[] = ["s1", "s2", "s3", "s4"];
  const criteriaBreakdown = {} as Record<RubricCriterionKey, CriterionBreakdown>;

  let totalRawScore = 0;
  let totalWeightedScore = 0;
  let totalMaxWeightedScore = 0;

  for (const k of criteriaKeys) {
    const meta = RUBRIC_METADATA[k];
    const scoreVal = Math.max(0, Math.min(raw[k], maxScore));
    const weightVal = w[k];
    const weightedVal = scoreVal * weightVal;
    const maxWeightedVal = maxScore * weightVal;

    totalRawScore += scoreVal;
    totalWeightedScore += weightedVal;
    totalMaxWeightedScore += maxWeightedVal;

    const percentage = maxScore > 0 ? (scoreVal / maxScore) * 100 : 0;
    const matchedLevel =
      meta.levels.find((l) => l.score === Math.round(scoreVal)) ||
      meta.levels[Math.min(Math.round(scoreVal), meta.levels.length - 1)];

    criteriaBreakdown[k] = {
      criterionId: meta.id,
      key: k,
      dimensionVi: meta.dimensionVi,
      dimensionEn: meta.dimensionEn,
      rawScore: scoreVal,
      maxScore,
      weight: weightVal,
      weightedScore: Number(weightedVal.toFixed(2)),
      percentage: Number(percentage.toFixed(1)),
      levelLabel: matchedLevel?.label ?? `${scoreVal}đ`,
      descriptor: matchedLevel?.desc ?? "",
    };
  }

  const maxPossibleScore = maxScore * criteriaKeys.length;
  const overallPercentage =
    totalMaxWeightedScore > 0
      ? Number(((totalWeightedScore / totalMaxWeightedScore) * 100).toFixed(1))
      : 0;

  // Normalized 10.0 grade rounded to 1 decimal place
  const normalized10 =
    totalMaxWeightedScore > 0
      ? Number(((totalWeightedScore / totalMaxWeightedScore) * 10).toFixed(1))
      : 0;

  const classificationPair = classifyScore(normalized10);

  return {
    rawScore: Number(totalRawScore.toFixed(2)),
    maxPossibleScore,
    weightedScore: Number(totalWeightedScore.toFixed(2)),
    maxWeightedScore: Number(totalMaxWeightedScore.toFixed(2)),
    percentage: overallPercentage,
    normalized10,
    classification: classificationPair.vi,
    classificationEn: classificationPair.en,
    criteriaBreakdown,
  };
}

// =========================================================================== //
// Validation
// =========================================================================== //

/**
 * Validates that all rubric score values are within numerical bounds [0 .. maxScore].
 *
 * @param scores Input scores object
 * @param options Validation options
 */
export function validateRubricScores(
  scores: unknown,
  options?: {
    maxScore?: number;
    allowPartial?: boolean;
  },
): RubricValidationResult {
  const errors: string[] = [];
  const maxScore = options?.maxScore ?? 3;
  const allowPartial = options?.allowPartial ?? false;

  if (!scores || typeof scores !== "object") {
    return {
      valid: false,
      errors: ["Dữ liệu điểm Rubric không hợp lệ (cần là đối tượng chứa điểm số)."],
    };
  }

  const rec = scores as Record<string, unknown>;
  const keys: Array<{ primary: RubricCriterionKey; label: string; aliases: string[] }> = [
    { primary: "s1", label: "S1 (Không gian)", aliases: ["s1", "s1_spatial", "S1", "S1_spatial"] },
    { primary: "s2", label: "S2 (Thời gian)", aliases: ["s2", "s2_temporal", "S2", "S2_temporal"] },
    { primary: "s3", label: "S3 (Sử liệu)", aliases: ["s3", "s3_evidence", "S3", "S3_evidence"] },
    { primary: "s4", label: "S4 (Lập luận)", aliases: ["s4", "s4_argument", "S4", "S4_argument"] },
  ];

  const parsedScores: RubricRawScores = { s1: 0, s2: 0, s3: 0, s4: 0 };

  for (const { primary, label, aliases } of keys) {
    let found = false;
    let val: unknown = undefined;

    for (const a of aliases) {
      if (a in rec && rec[a] !== undefined && rec[a] !== null) {
        val = rec[a];
        found = true;
        break;
      }
    }

    if (!found) {
      if (!allowPartial) {
        errors.push(`Thiếu điểm tiêu chí ${label}.`);
      }
      continue;
    }

    const num = Number(val);
    if (typeof val === "boolean" || Number.isNaN(num) || !Number.isFinite(num)) {
      errors.push(`Điểm tiêu chí ${label} phải là một số hợp lệ (nhận được: ${String(val)}).`);
      continue;
    }

    if (num < 0) {
      errors.push(`Điểm tiêu chí ${label} không được âm (nhận được: ${num}).`);
    } else if (num > maxScore) {
      errors.push(`Điểm tiêu chí ${label} vượt quá điểm tối đa ${maxScore} (nhận được: ${num}).`);
    } else {
      parsedScores[primary] = num;
    }
  }

  return {
    valid: errors.length === 0,
    errors,
    normalizedScores: errors.length === 0 ? parsedScores : undefined,
  };
}

// =========================================================================== //
// Pedagogical Evaluation Report & Qualitative Feedback
// =========================================================================== //

/**
 * Assembles a comprehensive pedagogical evaluation report with qualitative
 * strengths, actionable improvement areas, and integrated teacher notes.
 *
 * @param scores Raw or calculated rubric scores
 * @param teacherNotes Optional custom feedback notes written by the instructor
 * @param options Calculation and scale options
 */
export function formatRubricFeedback(
  scores: RubricScoresInput,
  teacherNotes?: string,
  options?: RubricCalculationOptions,
): RubricFeedbackResult {
  const calc = calculateRubricScore(scores, undefined, options);
  const maxScore = options?.maxScorePerCriterion ?? options?.scale ?? 3;

  const strengths: string[] = [];
  const improvementAreas: string[] = [];
  const recommendations: string[] = [];

  const criteriaKeys: RubricCriterionKey[] = ["s1", "s2", "s3", "s4"];

  // Sort criteria from highest to lowest percentage
  const sortedCriteria = criteriaKeys
    .map((k) => calc.criteriaBreakdown[k])
    .sort((a, b) => b.percentage - a.percentage);

  for (const item of sortedCriteria) {
    const meta = RUBRIC_METADATA[item.key];
    const thresholdHigh = maxScore >= 4 ? 3 : 2.5;
    const thresholdLow = maxScore >= 4 ? 2 : 1.5;

    if (item.rawScore >= thresholdHigh) {
      strengths.push(
        `${meta.dimensionVi} (${item.criterionId}): ${item.levelLabel} (${item.rawScore}/${item.maxScore}đ) — ${item.descriptor}`,
      );
    } else if (item.rawScore <= thresholdLow) {
      improvementAreas.push(
        `${meta.dimensionVi} (${item.criterionId}): ${item.levelLabel} (${item.rawScore}/${item.maxScore}đ) — Cần nâng cao năng lực theo tiêu chuẩn GDPT 2018.`,
      );
      recommendations.push(meta.recommendationPrompt);
    }
  }

  // Fallback if all scores are balanced
  if (strengths.length === 0 && sortedCriteria[0].rawScore > 0) {
    const top = sortedCriteria[0];
    const meta = RUBRIC_METADATA[top.key];
    strengths.push(
      `${meta.dimensionVi} (${top.criterionId}): Đạt mức ${top.levelLabel} (${top.rawScore}/${top.maxScore}đ).`,
    );
  }

  if (improvementAreas.length === 0 && sortedCriteria[3].rawScore < maxScore) {
    const bottom = sortedCriteria[3];
    const meta = RUBRIC_METADATA[bottom.key];
    improvementAreas.push(
      `${meta.dimensionVi} (${bottom.criterionId}): Có thể tiếp tục bồi dưỡng để đạt mức chuyên sâu tối đa.`,
    );
    recommendations.push(meta.recommendationPrompt);
  }

  // Clean teacher notes
  const trimmedNotes = teacherNotes?.trim();

  // Construct structured Markdown summary report
  const reportLines: string[] = [];
  reportLines.push(
    `### ĐÁNH GIÁ NĂNG LỰC LỊCH SỬ (RUBRIC S1-S4) — XẾP LOẠI: ${calc.classification.toUpperCase()}`,
  );
  reportLines.push(
    `- **Tổng điểm quy đổi**: ${calc.normalized10} / 10.0 (Thô: ${calc.rawScore}/${calc.maxPossibleScore} điểm, Tỷ lệ: ${calc.percentage}%)`,
  );
  reportLines.push(
    `- **Chuẩn năng lực**: S1 Không gian (${calc.criteriaBreakdown.s1.rawScore}/${maxScore}) • S2 Thời gian (${calc.criteriaBreakdown.s2.rawScore}/${maxScore}) • S3 Sử liệu (${calc.criteriaBreakdown.s3.rawScore}/${maxScore}) • S4 Lập luận (${calc.criteriaBreakdown.s4.rawScore}/${maxScore})`,
  );
  reportLines.push("");

  if (strengths.length > 0) {
    reportLines.push("**Điểm mạnh nổi bật:**");
    strengths.forEach((s) => reportLines.push(`- ${s}`));
    reportLines.push("");
  }

  if (improvementAreas.length > 0) {
    reportLines.push("**Điểm cần rèn luyện thêm:**");
    improvementAreas.forEach((ia) => reportLines.push(`- ${ia}`));
    reportLines.push("");
  }

  if (recommendations.length > 0) {
    reportLines.push("**Khuyến nghị học tập:**");
    recommendations.forEach((r) => reportLines.push(`- ${r}`));
    reportLines.push("");
  }

  if (trimmedNotes) {
    reportLines.push("**Nhận xét từ Giáo viên:**");
    reportLines.push(`> "${trimmedNotes}"`);
  }

  const summary = `Xếp loại ${calc.classification} (${calc.normalized10}/10.0 điểm). Năng lực nổi bật nhất ở ${sortedCriteria[0].dimensionVi}.`;

  return {
    summary,
    classification: calc.classification,
    normalized10: calc.normalized10,
    strengths,
    improvementAreas,
    recommendations,
    teacherNotes: trimmedNotes || undefined,
    fullReportText: reportLines.join("\n"),
  };
}

// =========================================================================== //
// Gradebook CSV Export Utility
// =========================================================================== //

/**
 * Escapes a single string field for RFC 4180 CSV compliance.
 */
function escapeCSVField(value: string | number | null | undefined, delimiter = ","): string {
  if (value === null || value === undefined) return "";
  const str = String(value);
  if (
    str.includes(delimiter) ||
    str.includes('"') ||
    str.includes("\n") ||
    str.includes("\r")
  ) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

/**
 * Generates an anonymized student identifier code.
 */
export function generateAnonymizedStudentCode(
  studentId: string,
  prefix = "HS-",
  index = 1,
): string {
  if (!studentId) {
    return `${prefix}${String(index).padStart(3, "0")}`;
  }
  // If studentId already has pattern stu-101 or 101, preserve suffix
  const match = studentId.match(/\d+/);
  if (match) {
    return `${prefix}${match[0]}`;
  }
  // Otherwise create a short consistent hash
  let hash = 0;
  for (let i = 0; i < studentId.length; i++) {
    hash = (hash << 5) - hash + studentId.charCodeAt(i);
    hash |= 0;
  }
  const positive = Math.abs(hash) % 1000;
  return `${prefix}${String(positive).padStart(3, "0")}`;
}

/**
 * Exports a list of student submissions to a cleanly formatted CSV gradebook.
 * Includes UTF-8 BOM by default so Microsoft Excel opens Vietnamese characters seamlessly.
 *
 * @param submissions Array of student submissions
 * @param options CSV export configuration options
 */
export function exportGradebookToCSV(
  submissions: StudentSubmission[],
  options?: CSVExportOptions,
): string {
  const delimiter = options?.delimiter ?? ",";
  const anonymize = options?.anonymize ?? false;
  const prefix = options?.anonymizePrefix ?? "HS-";
  const includeTimestamps = options?.includeTimestamps ?? true;
  const includeFeedback = options?.includeTeacherFeedback ?? true;
  const maxScore = options?.maxScorePerCriterion ?? 3;
  const weights = options?.weights;
  const includeBOM = options?.includeBOM ?? true;

  // Header columns
  const headers = [
    "Mã học sinh",
    "Họ và tên",
    "Lớp học",
    "Di tích / Chủ đề",
    `S1: Không gian (0-${maxScore}đ)`,
    `S2: Thời gian (0-${maxScore}đ)`,
    `S3: Sử liệu (0-${maxScore}đ)`,
    `S4: Lập luận (0-${maxScore}đ)`,
    `Tổng điểm thô (/${maxScore * 4}đ)`,
    "Điểm quy đổi (hệ 10)",
    "Xếp loại năng lực",
    "Trạng thái chấm",
  ];

  if (includeFeedback) {
    headers.push("Nhận xét của giáo viên");
  }

  if (includeTimestamps) {
    headers.push("Thời gian nộp");
    headers.push("Thời gian chấm");
    headers.push("Người chấm");
  }

  const rows: string[] = [];
  rows.push(headers.map((h) => escapeCSVField(h, delimiter)).join(delimiter));

  submissions.forEach((sub, idx) => {
    const studentCode = anonymize
      ? generateAnonymizedStudentCode(sub.student_id, prefix, idx + 1)
      : sub.student_id || generateAnonymizedStudentCode("", prefix, idx + 1);

    const studentName = anonymize ? `Học sinh ${studentCode}` : sub.student_name || "Chưa rõ";
    const studentClass = sub.student_class || "";
    const monument = sub.monument_name_vi || sub.trail_title || "Khảo sát di sản";

    const s1 = sub.scores?.s1_spatial ?? 0;
    const s2 = sub.scores?.s2_temporal ?? 0;
    const s3 = sub.scores?.s3_evidence ?? 0;
    const s4 = sub.scores?.s4_argument ?? 0;

    const calc = calculateRubricScore({ s1, s2, s3, s4 }, weights, {
      maxScorePerCriterion: maxScore,
    });

    const statusVi =
      sub.status === "graded"
        ? "Đã chấm điểm"
        : sub.status === "resubmit_requested"
        ? "Yêu cầu nộp lại"
        : "Chờ chấm điểm";

    const row = [
      escapeCSVField(studentCode, delimiter),
      escapeCSVField(studentName, delimiter),
      escapeCSVField(studentClass, delimiter),
      escapeCSVField(monument, delimiter),
      escapeCSVField(s1, delimiter),
      escapeCSVField(s2, delimiter),
      escapeCSVField(s3, delimiter),
      escapeCSVField(s4, delimiter),
      escapeCSVField(calc.rawScore, delimiter),
      escapeCSVField(calc.normalized10.toFixed(1), delimiter),
      escapeCSVField(calc.classification, delimiter),
      escapeCSVField(statusVi, delimiter),
    ];

    if (includeFeedback) {
      row.push(escapeCSVField(sub.teacher_feedback || "", delimiter));
    }

    if (includeTimestamps) {
      row.push(escapeCSVField(sub.submitted_at || "", delimiter));
      row.push(escapeCSVField(sub.graded_at || "", delimiter));
      row.push(escapeCSVField(sub.graded_by || "", delimiter));
    }

    rows.push(row.join(delimiter));
  });

  const csvContent = rows.join("\r\n");
  return includeBOM ? `\uFEFF${csvContent}` : csvContent;
}
