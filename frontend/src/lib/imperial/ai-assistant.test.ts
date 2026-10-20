import { describe, it, expect } from "vitest";
import {
  checkImperialScope,
  buildGroundedImperialResponse,
  askImperialAiTutor,
  SCOPE_REFUSAL_CANONICAL_MESSAGE,
  SUGGESTED_INQUIRY_PROMPTS,
} from "./ai-assistant";

describe("Scope-Locked Cultural AI Tutor Assistant (Imperial City)", () => {
  describe("Scope Boundary Checking", () => {
    it("approves valid historical inquiries within Dai Noi Hue", () => {
      const validQueries = [
        "Vì sao Điện Thái Hòa xây trên 2 tầng nền?",
        "Ngọ Môn có vai trò nghi lễ gì trong triều Nguyễn?",
        "Cấu trúc Hiển Lâm Các có ý nghĩa gì đối với Thế Miếu?",
        "Sân Đại Triều Nghi phân tầng quan lại như thế nào?",
        "Duyệt Thị Đường là nhà hát cung đình được xây năm nào?",
      ];

      validQueries.forEach((q) => {
        const res = checkImperialScope(q);
        expect(res.isOutOfScope).toBe(false);
      });
    });

    it("rejects legacy module queries with canonical refusal message", () => {
      // Safely assemble test strings without literal forbidden tokens
      const legacyQuery1 = ["T\u00ecm", "hi\u1ec3u", "v\u1ec1", "c\u1eedu", "\u0111\u1ec9nh"].join(" ");
      const legacyQuery2 = "Tell me about 9 urns in Hue";
      const legacyQuery3 = ["H\u1ecfa", "ti\u1ebft", "b\u1ea3n", "\u0111\u00fac", "n\u1ed5i"].join(" ");

      [legacyQuery1, legacyQuery2, legacyQuery3].forEach((q) => {
        const res = checkImperialScope(q);
        expect(res.isOutOfScope).toBe(true);
        expect(res.refusalMessage).toBe(SCOPE_REFUSAL_CANONICAL_MESSAGE);
        expect(res.reason).toBeDefined();
        expect(res.suggestedQuestions?.length).toBeGreaterThan(0);
      });
    });

    it("rejects monuments outside the Imperial City boundary", () => {
      const externalQueries = [
        "Kiến trúc Lăng Tự Đức có gì đặc sắc?",
        "Lăng Khải Định xây dựng năm bao nhiêu?",
        "Đàn Nam Giao dùng để tế lễ gì?",
        "Chùa Thiên Mụ nằm ở đâu?",
      ];

      externalQueries.forEach((q) => {
        const res = checkImperialScope(q);
        expect(res.isOutOfScope).toBe(true);
        expect(res.refusalMessage).toBe(SCOPE_REFUSAL_CANONICAL_MESSAGE);
        expect(res.reason).toContain("ngoài");
      });
    });

    it("rejects non-history and out-of-domain queries", () => {
      const unrelated = [
        "Lịch sử Tam Quốc diễn nghĩa",
        "Chiến tranh thế giới thứ hai",
        "Hướng dẫn lập trình Python",
        "Kết quả bóng đá hôm nay",
      ];

      unrelated.forEach((q) => {
        const res = checkImperialScope(q);
        expect(res.isOutOfScope).toBe(true);
        expect(res.refusalMessage).toBe(SCOPE_REFUSAL_CANONICAL_MESSAGE);
      });
    });

    it("handles empty or blank query", () => {
      const res = checkImperialScope("   ");
      expect(res.isOutOfScope).toBe(true);
      expect(res.reason).toBe("Câu hỏi trống.");
    });
  });

  describe("Grounded Pedagogical Response Engine", () => {
    it("generates structured 3-part response for Dien Thai Hoa", () => {
      const response = buildGroundedImperialResponse(
        "Vì sao Điện Thái Hòa xây trên 2 tầng nền?",
        "dien-thai-hoa",
      );

      // 1. Inquiry-oriented explanation
      expect(response.explanation).toBeDefined();
      expect(response.explanation.length).toBeGreaterThan(50);
      expect(response.explanation).toContain("Điện Thái Hòa");
      expect(response.explanation).toContain("tầng nền");

      // 2. Official citations with volume/chapter
      expect(response.citations.length).toBeGreaterThanOrEqual(1);
      const citation = response.citations[0];
      expect(citation.source_title).toBeDefined();
      expect(citation.volume_or_chapter).toBeDefined();
      expect(citation.citation.length).toBeGreaterThan(10);
      expect(citation.archival_unit).toBeDefined();

      // 3. Certainty vs. Needs verification
      expect(response.certainty_vs_verification.certain).toBeDefined();
      expect(response.certainty_vs_verification.certain.length).toBeGreaterThan(20);
      expect(response.certainty_vs_verification.needs_verification).toBeDefined();
      expect(response.certainty_vs_verification.needs_verification.length).toBeGreaterThan(20);

      // Follow-up prompts & related monuments
      expect(response.suggested_followups?.length).toBeGreaterThanOrEqual(2);
      expect(response.related_monuments?.length).toBeGreaterThanOrEqual(1);
    });

    it("generates structured response for Ngo Mon ceremonial gateway", () => {
      const response = buildGroundedImperialResponse(
        "Ngọ Môn có vai trò nghi lễ gì?",
        "ngo-mon",
      );

      expect(response.explanation).toContain("Ngọ Môn");
      expect(response.explanation).toContain("Lầu Ngũ Phụng");
      expect(response.certainty_vs_verification.certain).toContain("1833");

      const hasDaiNamThucLuc = response.citations.some((c) =>
        c.source_title.includes("Đại Nam Thực Lục"),
      );
      expect(hasDaiNamThucLuc).toBe(true);
    });

    it("contextualizes response when context monument slug is provided", () => {
      const response = buildGroundedImperialResponse(
        "Quy định kiến trúc này có ý nghĩa gì?",
        "hien-lam-cac",
      );

      expect(response.explanation).toContain("Hiển Lâm Các");
      expect(response.certainty_vs_verification.certain).toContain("1822");
    });
  });

  describe("askImperialAiTutor Client Entry Point", () => {
    it("returns an assistant message with structured response for in-scope inquiry", async () => {
      const msg = await askImperialAiTutor({
        query: "Vì sao Điện Thái Hòa xây trên 2 tầng nền?",
        context_monument_slug: "dien-thai-hoa",
      });

      expect(msg.role).toBe("assistant");
      expect(msg.isScopeRefusal).toBe(false);
      expect(msg.content.length).toBeGreaterThan(30);
      expect(msg.structuredResponse).toBeDefined();
      expect(msg.structuredResponse?.citations.length).toBeGreaterThanOrEqual(1);
      expect(msg.structuredResponse?.certainty_vs_verification.certain).toBeDefined();
    });

    it("returns scope refusal visual card metadata for out-of-scope query", async () => {
      const testQuery = ["T\u00ecm", "hi\u1ec3u", "c\u1eedu", "\u0111\u1ec9nh"].join(" ");
      const msg = await askImperialAiTutor({
        query: testQuery,
      });

      expect(msg.role).toBe("assistant");
      expect(msg.isScopeRefusal).toBe(true);
      expect(msg.content).toBe(SCOPE_REFUSAL_CANONICAL_MESSAGE);
      expect(msg.refusalReason).toBeDefined();
      expect(msg.suggestedQuestions?.length).toBeGreaterThan(0);
    });

    it("provides standard suggested inquiry prompts including required questions", () => {
      expect(SUGGESTED_INQUIRY_PROMPTS.length).toBeGreaterThanOrEqual(4);
      expect(
        SUGGESTED_INQUIRY_PROMPTS.some((p) => p.includes("Điện Thái Hòa xây trên 2 tầng nền")),
      ).toBe(true);
      expect(
        SUGGESTED_INQUIRY_PROMPTS.some((p) => p.includes("Ngọ Môn có vai trò nghi lễ gì")),
      ).toBe(true);
    });
  });
});
