import { describe, it, expect } from "vitest";
import {
  calculateRubricScore,
  validateRubricScores,
  formatRubricFeedback,
  exportGradebookToCSV,
  generateAnonymizedStudentCode,
  normalizeScoreKeys,
  normalizeWeights,
  classifyScore,
  RUBRIC_METADATA,
} from "./rubric-engine";
import type { StudentSubmission } from "./map-types";

describe("Rubric Scoring Engine (rubric-engine.ts)", () => {
  // ========================================================================= //
  // 1. Calculations & Weights Suite
  // ========================================================================= //
  describe("calculateRubricScore", () => {
    it("calculates perfect scores on standard 0-3 scale", () => {
      const result = calculateRubricScore({ s1: 3, s2: 3, s3: 3, s4: 3 });

      expect(result.rawScore).toBe(12);
      expect(result.maxPossibleScore).toBe(12);
      expect(result.percentage).toBe(100);
      expect(result.normalized10).toBe(10.0);
      expect(result.classification).toBe("Xuất sắc");
      expect(result.classificationEn).toBe("Excellent");

      expect(result.criteriaBreakdown.s1.levelLabel).toBe("Xuất sắc");
      expect(result.criteriaBreakdown.s1.rawScore).toBe(3);
    });

    it("calculates minimum 0 scores correctly", () => {
      const result = calculateRubricScore({ s1: 0, s2: 0, s3: 0, s4: 0 });

      expect(result.rawScore).toBe(0);
      expect(result.maxPossibleScore).toBe(12);
      expect(result.percentage).toBe(0);
      expect(result.normalized10).toBe(0.0);
      expect(result.classification).toBe("Cần rèn luyện");
      expect(result.classificationEn).toBe("Needs Improvement");
    });

    it("calculates realistic mixed scores (10/12) as Giỏi", () => {
      const result = calculateRubricScore({ s1: 3, s2: 2, s3: 2, s4: 3 });

      expect(result.rawScore).toBe(10);
      expect(result.maxPossibleScore).toBe(12);
      expect(result.percentage).toBe(83.3);
      expect(result.normalized10).toBe(8.3);
      expect(result.classification).toBe("Giỏi");
      expect(result.classificationEn).toBe("Very Good");
    });

    it("evaluates all 5 competency classification thresholds accurately", () => {
      // Xuất sắc: >= 9.0 (e.g. 11/12 = 9.17 -> 9.2)
      expect(calculateRubricScore({ s1: 3, s2: 3, s3: 3, s4: 2 }).classification).toBe("Xuất sắc");

      // Giỏi: 8.0 - 8.9 (e.g. 10/12 = 8.3)
      expect(calculateRubricScore({ s1: 3, s2: 2, s3: 2, s4: 3 }).classification).toBe("Giỏi");

      // Khá: 6.5 - 7.9 (e.g. 8/12 = 6.67 -> 6.7)
      expect(calculateRubricScore({ s1: 2, s2: 2, s3: 2, s4: 2 }).classification).toBe("Khá");

      // Đạt: 5.0 - 6.4 (e.g. 6/12 = 5.0)
      expect(calculateRubricScore({ s1: 2, s2: 1, s3: 2, s4: 1 }).classification).toBe("Đạt");

      // Cần rèn luyện: < 5.0 (e.g. 5/12 = 4.17 -> 4.2)
      expect(calculateRubricScore({ s1: 1, s2: 1, s3: 2, s4: 1 }).classification).toBe("Cần rèn luyện");
    });

    it("supports 0-4 point scale option seamlessly", () => {
      const result = calculateRubricScore(
        { s1: 4, s2: 3, s3: 3, s4: 4 },
        undefined,
        { maxScorePerCriterion: 4 },
      );

      expect(result.rawScore).toBe(14);
      expect(result.maxPossibleScore).toBe(16);
      expect(result.percentage).toBe(87.5);
      expect(result.normalized10).toBe(8.8);
      expect(result.classification).toBe("Giỏi");
      expect(result.criteriaBreakdown.s1.maxScore).toBe(4);
    });

    it("accepts alias key names (s1_spatial, s2_temporal, S3_evidence, etc.)", () => {
      const result = calculateRubricScore({
        s1_spatial: 3,
        s2_temporal: 2,
        s3_evidence: 3,
        s4_argument: 2,
      });

      expect(result.rawScore).toBe(10);
      expect(result.criteriaBreakdown.s1.rawScore).toBe(3);
      expect(result.criteriaBreakdown.s2.rawScore).toBe(2);
      expect(result.criteriaBreakdown.s3.rawScore).toBe(3);
      expect(result.criteriaBreakdown.s4.rawScore).toBe(2);
    });

    it("applies customizable weighting multipliers correctly", () => {
      // S3 (Evidence) and S4 (Argument) weighted 2x heavier than S1 and S2
      const weights = { s1: 1, s2: 1, s3: 2, s4: 2 };
      // Max score: 1*3 + 1*3 + 2*3 + 2*3 = 18
      // Actual score: 1*0 + 1*0 + 2*3 + 2*3 = 12
      // Percentage: 12 / 18 = 66.7%, Normalized 10: 6.7 -> Khá
      const result = calculateRubricScore(
        { s1: 0, s2: 0, s3: 3, s4: 3 },
        weights,
      );

      expect(result.weightedScore).toBe(12);
      expect(result.maxWeightedScore).toBe(18);
      expect(result.percentage).toBe(66.7);
      expect(result.normalized10).toBe(6.7);
      expect(result.classification).toBe("Khá");
    });

    it("supports assignment-style weights with string keys (S1_spatial: 30, etc.)", () => {
      const weights = {
        S1_spatial: 30,
        S2_temporal: 20,
        S3_evidence: 30,
        S4_argument: 20,
      };
      const result = calculateRubricScore({ s1: 3, s2: 3, s3: 3, s4: 3 }, weights);
      expect(result.normalized10).toBe(10.0);
      expect(result.percentage).toBe(100);
    });
  });

  // ========================================================================= //
  // 2. Validation Suite
  // ========================================================================= //
  describe("validateRubricScores", () => {
    it("approves valid score sets within [0..3]", () => {
      const check = validateRubricScores({ s1: 3, s2: 2, s3: 1, s4: 0 });
      expect(check.valid).toBe(true);
      expect(check.errors).toHaveLength(0);
      expect(check.normalizedScores).toEqual({ s1: 3, s2: 2, s3: 1, s4: 0 });
    });

    it("rejects scores exceeding max limit", () => {
      const check = validateRubricScores({ s1: 4, s2: 2, s3: 1, s4: 0 }, { maxScore: 3 });
      expect(check.valid).toBe(false);
      expect(check.errors.some((e) => e.includes("vượt quá điểm tối đa 3"))).toBe(true);
    });

    it("rejects negative scores", () => {
      const check = validateRubricScores({ s1: -1, s2: 2, s3: 1, s4: 2 });
      expect(check.valid).toBe(false);
      expect(check.errors.some((e) => e.includes("không được âm"))).toBe(true);
    });

    it("rejects non-numeric and NaN values", () => {
      const check = validateRubricScores({ s1: "abc", s2: 2, s3: NaN, s4: true });
      expect(check.valid).toBe(false);
      expect(check.errors.length).toBeGreaterThanOrEqual(2);
    });

    it("flags missing criteria when partial scoring is disabled", () => {
      const check = validateRubricScores({ s1: 2, s2: 2 });
      expect(check.valid).toBe(false);
      expect(check.errors.some((e) => e.includes("Thiếu điểm tiêu chí S3"))).toBe(true);
      expect(check.errors.some((e) => e.includes("Thiếu điểm tiêu chí S4"))).toBe(true);
    });

    it("allows partial scores when allowPartial is true", () => {
      const check = validateRubricScores({ s1: 2, s2: 2 }, { allowPartial: true });
      expect(check.valid).toBe(true);
      expect(check.errors).toHaveLength(0);
    });

    it("handles null or non-object input gracefully", () => {
      const check = validateRubricScores(null);
      expect(check.valid).toBe(false);
      expect(check.errors[0]).toContain("không hợp lệ");
    });
  });

  // ========================================================================= //
  // 3. Feedback Generation Suite
  // ========================================================================= //
  describe("formatRubricFeedback", () => {
    it("identifies high scoring criteria as strengths and low criteria as improvement areas", () => {
      const feedback = formatRubricFeedback(
        { s1: 3, s2: 1, s3: 3, s4: 1 },
        "Em cần rèn thêm cách lập luận M-E-E.",
      );

      expect(feedback.classification).toBe("Khá");
      expect(feedback.normalized10).toBe(6.7);

      // Strengths should include S1 and S3
      expect(feedback.strengths.some((s) => s.includes("S1"))).toBe(true);
      expect(feedback.strengths.some((s) => s.includes("S3"))).toBe(true);

      // Improvement areas should include S2 and S4
      expect(feedback.improvementAreas.some((ia) => ia.includes("S2"))).toBe(true);
      expect(feedback.improvementAreas.some((ia) => ia.includes("S4"))).toBe(true);

      // Recommendations should provide actionable tips
      expect(feedback.recommendations.length).toBeGreaterThanOrEqual(1);

      // Full report includes teacher notes
      expect(feedback.fullReportText).toContain("Em cần rèn thêm cách lập luận M-E-E.");
      expect(feedback.fullReportText).toContain("ĐÁNH GIÁ NĂNG LỰC LỊCH SỬ");
    });

    it("handles all-max score feedback properly", () => {
      const feedback = formatRubricFeedback({ s1: 3, s2: 3, s3: 3, s4: 3 });
      expect(feedback.classification).toBe("Xuất sắc");
      expect(feedback.strengths.length).toBe(4);
      expect(feedback.improvementAreas.length).toBe(0);
    });

    it("handles all-zero score feedback properly", () => {
      const feedback = formatRubricFeedback({ s1: 0, s2: 0, s3: 0, s4: 0 });
      expect(feedback.classification).toBe("Cần rèn luyện");
      expect(feedback.improvementAreas.length).toBe(4);
      expect(feedback.recommendations.length).toBe(4);
    });
  });

  // ========================================================================= //
  // 4. Gradebook CSV Export Suite
  // ========================================================================= //
  describe("exportGradebookToCSV", () => {
    const mockSubmissions: StudentSubmission[] = [
      {
        id: "sub-1",
        student_id: "stu-101",
        student_name: "Nguyễn Lê Hoàng Nam",
        student_class: "11 Sử — Quốc Học Huế",
        monument_name_vi: "Ngọ Môn",
        claim: "Ngọ Môn biểu hiện quyền lực.",
        evidence: "Khâm Định Hội Điển Sự Lệ.",
        evidence_citations: ["Hội Điển"],
        explanation: "Cửa giữa vua đi.",
        submitted_at: "2026-10-14T08:30:00Z",
        status: "graded",
        scores: {
          s1_spatial: 3,
          s2_temporal: 3,
          s3_evidence: 3,
          s4_argument: 3,
          total: 12,
          normalized_10: 10.0,
        },
        teacher_feedback: "Bài làm rất xuất sắc, lập luận chặt chẽ!",
        graded_at: "2026-10-14T10:15:00Z",
        graded_by: "TS. Trần Văn Thọ",
      },
      {
        id: "sub-2",
        student_id: "stu-102",
        student_name: "Trần Mai Phương Thảo",
        student_class: "10 Văn — Hai Bà Trưng",
        monument_name_vi: "Điện Thái Hòa",
        claim: "Điện Thái Hòa có nghệ thuật nhất thi nhất họa.",
        evidence: "Thơ vua Thiệu Trị.",
        evidence_citations: ["Đại Nam Thực Lục"],
        explanation: "Văn hiến thiên niên quốc.",
        submitted_at: "2026-10-15T01:45:00Z",
        status: "graded",
        scores: {
          s1_spatial: 3,
          s2_temporal: 2,
          s3_evidence: 2,
          s4_argument: 3,
          total: 10,
          normalized_10: 8.3,
        },
        teacher_feedback: 'Cần bổ sung trích dẫn "Đại Nam Thực Lục" cụ thể hơn.',
        graded_at: "2026-10-15T04:00:00Z",
        graded_by: "Cô Đặng Thị Thu Hà",
      },
    ];

    it("generates CSV with UTF-8 BOM and correct headers", () => {
      const csv = exportGradebookToCSV(mockSubmissions);

      // Check UTF-8 BOM (\uFEFF)
      expect(csv.startsWith("\uFEFF")).toBe(true);

      // Check header columns
      expect(csv).toContain("Mã học sinh");
      expect(csv).toContain("Họ và tên");
      expect(csv).toContain("S1: Không gian");
      expect(csv).toContain("S2: Thời gian");
      expect(csv).toContain("S3: Sử liệu");
      expect(csv).toContain("S4: Lập luận");
      expect(csv).toContain("Tổng điểm thô");
      expect(csv).toContain("Điểm quy đổi (hệ 10)");
      expect(csv).toContain("Xếp loại năng lực");
    });

    it("escapes quotes and special characters properly", () => {
      const csv = exportGradebookToCSV(mockSubmissions);

      // sub-2 contains quotes in feedback: 'Cần bổ sung trích dẫn "Đại Nam Thực Lục" cụ thể hơn.'
      expect(csv).toContain('""Đại Nam Thực Lục""');
    });

    it("supports student anonymization mode", () => {
      const csv = exportGradebookToCSV(mockSubmissions, { anonymize: true });

      // Real student names should NOT appear in the CSV
      expect(csv).not.toContain("Nguyễn Lê Hoàng Nam");
      expect(csv).not.toContain("Trần Mai Phương Thảo");

      // Anonymized codes should appear
      expect(csv).toContain("HS-101");
      expect(csv).toContain("HS-102");
    });

    it("handles empty submissions list gracefully", () => {
      const csv = exportGradebookToCSV([]);
      expect(csv.startsWith("\uFEFF")).toBe(true);
      expect(csv).toContain("Mã học sinh");
      const lines = csv.trim().split("\r\n");
      expect(lines.length).toBe(1); // Only header row
    });
  });

  // ========================================================================= //
  // 5. Utility Helpers Suite
  // ========================================================================= //
  describe("utility functions", () => {
    it("generateAnonymizedStudentCode handles various inputs", () => {
      expect(generateAnonymizedStudentCode("stu-105")).toBe("HS-105");
      expect(generateAnonymizedStudentCode("student_42")).toBe("HS-42");
      expect(generateAnonymizedStudentCode("", "ANON-", 5)).toBe("ANON-005");
    });

    it("classifyScore categorizes score ranges properly", () => {
      expect(classifyScore(9.5).vi).toBe("Xuất sắc");
      expect(classifyScore(8.5).vi).toBe("Giỏi");
      expect(classifyScore(7.0).vi).toBe("Khá");
      expect(classifyScore(5.5).vi).toBe("Đạt");
      expect(classifyScore(4.5).vi).toBe("Cần rèn luyện");
    });

    it("RUBRIC_METADATA contains all 4 criteria S1-S4", () => {
      expect(RUBRIC_METADATA.s1.id).toBe("S1");
      expect(RUBRIC_METADATA.s2.id).toBe("S2");
      expect(RUBRIC_METADATA.s3.id).toBe("S3");
      expect(RUBRIC_METADATA.s4.id).toBe("S4");
      expect(RUBRIC_METADATA.s1.levels).toHaveLength(5);
    });
  });
});
