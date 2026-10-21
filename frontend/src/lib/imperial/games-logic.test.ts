import { describe, it, expect } from "vitest";
import {
  TIMELINE_CHALLENGES,
  CIPHER_CHALLENGES,
  CANDIDATE_MONUMENTS,
  verifyTimelineOrdering,
  verifyCipherSubmission,
} from "./games-data";
import {
  FALLBACK_CLUES,
  FALLBACK_GAME_QUESTIONS,
  fetchClues,
  fetchGameQuestions,
  submitClueAttempt,
  submitGameAnswer,
} from "./v51-api";

describe("Heritage Games & Educational Quizzes Suite", () => {
  // -------------------------------------------------------------------------
  // 1. Trắc nghiệm di sản & Định vị cấu kiện
  // -------------------------------------------------------------------------
  describe("Trắc nghiệm di sản (Quizzes & Space Hotspots)", () => {
    it("provides diverse question formats: multiple_choice, matching, hotspot_identify", async () => {
      const questions = await fetchGameQuestions();
      expect(questions.length).toBeGreaterThanOrEqual(6);

      const types = new Set(questions.map((q) => q.question_type));
      expect(types.has("multiple_choice")).toBe(true);
      expect(types.has("matching")).toBe(true);
      expect(types.has("hotspot_identify")).toBe(true);
    });

    it("ensures every quiz question includes pedagogical explanation and source citation", () => {
      FALLBACK_GAME_QUESTIONS.forEach((q) => {
        expect(q.prompt).toBeTruthy();
        expect(q.options.length).toBeGreaterThanOrEqual(2);
        expect(q.explanation_why).toBeTruthy();
        expect(q.source_citation).toBeTruthy();
        expect(q.points).toBeGreaterThan(0);
      });
    });

    it("evaluates multiple choice answers with accurate score delta and explanation", async () => {
      const q = FALLBACK_GAME_QUESTIONS.find((item) => item.id === "gq-deep-1");
      expect(q).toBeDefined();

      // gq-deep-1 answer_key is "2"
      const correctRes = await submitGameAnswer("gq-deep-1", 2);
      expect(correctRes.correct).toBe(true);
      expect(correctRes.score_delta).toBeGreaterThan(0);
      expect(correctRes.explanation).toContain("tư tưởng phong thủy và chính trị triều Nguyễn");

      const wrongRes = await submitGameAnswer("gq-deep-1", 0);
      expect(wrongRes.correct).toBe(false);
      expect(wrongRes.score_delta).toBe(0);
    });
  });

  // -------------------------------------------------------------------------
  // 2. Thám tử cổ vật (Heritage Detective Clues)
  // -------------------------------------------------------------------------
  describe("Thám tử cổ vật (Heritage Detective Clues)", () => {
    it("includes rich detective riddles for all major Đại Nội sites", async () => {
      const clues = await fetchClues();
      expect(clues.length).toBeGreaterThanOrEqual(4);

      const targetSlugs = clues.map((c) => c.target_slug);
      expect(targetSlugs).toContain("ngo-mon");
      expect(targetSlugs).toContain("dien-thai-hoa");
      expect(targetSlugs).toContain("dien-kien-trung");
      expect(targetSlugs).toContain("hien-lam-cac");
    });

    it("verifies multi-step progressive hint mechanisms for all clues", () => {
      FALLBACK_CLUES.forEach((clue) => {
        expect(clue.title).toBeTruthy();
        expect(clue.clue_text).toBeTruthy();
        expect(clue.hint_steps.length).toBeGreaterThanOrEqual(3);
        expect(clue.points).toBeGreaterThanOrEqual(30);
      });
    });

    it("evaluates candidate target attempts with flexible slug prefixes", async () => {
      // Test clue-ngu-phung target ngo-mon
      const resBare = await submitClueAttempt("clue-ngu-phung", "ngo-mon");
      expect(resBare.success).toBe(true);
      expect(resBare.points_awarded).toBeGreaterThan(0);

      const resPrefixed = await submitClueAttempt("clue-ngu-phung", "site-ngo-mon");
      expect(resPrefixed.success).toBe(true);

      const resWrong = await submitClueAttempt("clue-ngu-phung", "dien-kien-trung");
      expect(resWrong.success).toBe(false);
      expect(resWrong.points_awarded).toBe(0);
    });
  });

  // -------------------------------------------------------------------------
  // 3. Sắp xếp niên biểu (Timeline Chronology Game)
  // -------------------------------------------------------------------------
  describe("Sắp xếp niên biểu (Timeline Chronology Game)", () => {
    it("defines verified chronological challenges with monotonically increasing milestones", () => {
      expect(TIMELINE_CHALLENGES.length).toBeGreaterThanOrEqual(3);

      TIMELINE_CHALLENGES.forEach((challenge) => {
        expect(challenge.title).toBeTruthy();
        expect(challenge.events.length).toBeGreaterThanOrEqual(4);
        expect(challenge.hints.length).toBeGreaterThanOrEqual(3);
        expect(challenge.explanation).toBeTruthy();
        expect(challenge.source_citation).toBeTruthy();

        // Check years are in strict non-decreasing order in the solution definition
        for (let i = 1; i < challenge.events.length; i++) {
          expect(challenge.events[i].year).toBeGreaterThanOrEqual(challenge.events[i - 1].year);
        }
      });
    });

    it("verifyTimelineOrdering approves correct chronological sequence and awards full points", () => {
      const challenge = TIMELINE_CHALLENGES[0];
      const correctOrder = challenge.events.map((e) => e.id);

      const result = verifyTimelineOrdering(challenge, correctOrder);
      expect(result.isCorrect).toBe(true);
      expect(result.correctCount).toBe(challenge.events.length);
      expect(result.scoreAwarded).toBe(challenge.points);
      expect(result.feedback).toContain("hoàn hảo");
    });

    it("verifyTimelineOrdering detects misplaced events and awards partial proportional score", () => {
      const challenge = TIMELINE_CHALLENGES[0];
      const correctOrder = challenge.events.map((e) => e.id);

      // Invert first two events
      const scrambled = [...correctOrder];
      scrambled[0] = correctOrder[1];
      scrambled[1] = correctOrder[0];

      const result = verifyTimelineOrdering(challenge, scrambled);
      expect(result.isCorrect).toBe(false);
      expect(result.correctCount).toBe(challenge.events.length - 2);
      expect(result.scoreAwarded).toBeLessThan(challenge.points);
      expect(result.scoreAwarded).toBeGreaterThan(0);
    });
  });

  // -------------------------------------------------------------------------
  // 4. Giải mã mật mã cung đình (Imperial Royal Cipher)
  // -------------------------------------------------------------------------
  describe("Giải mã mật mã cung đình (Imperial Royal Cipher)", () => {
    it("contains authentic royal poetic inscriptions and mottoes", () => {
      expect(CIPHER_CHALLENGES.length).toBeGreaterThanOrEqual(3);

      CIPHER_CHALLENGES.forEach((cipher) => {
        expect(cipher.title).toBeTruthy();
        expect(cipher.monument_name).toBeTruthy();
        expect(cipher.solution_tokens.length).toBeGreaterThanOrEqual(1);
        expect(cipher.scrambled_tokens.length).toBeGreaterThanOrEqual(cipher.solution_tokens.length);
        expect(cipher.hint_steps.length).toBeGreaterThanOrEqual(3);
        expect(cipher.explanation).toBeTruthy();
        expect(cipher.source_citation).toBeTruthy();
      });
    });

    it("verifyCipherSubmission validates exact royal phrase sequence", () => {
      const cipher = CIPHER_CHALLENGES[0];
      const solution = cipher.solution_tokens;

      const validResult = verifyCipherSubmission(cipher, solution);
      expect(validResult.isCorrect).toBe(true);
      expect(validResult.scoreAwarded).toBe(cipher.points);
      expect(validResult.feedback).toContain("Chính xác");

      // Wrong sequence
      const invalidResult = verifyCipherSubmission(cipher, [solution[1], solution[0]]);
      expect(invalidResult.isCorrect).toBe(false);
      expect(invalidResult.scoreAwarded).toBe(0);
    });

    it("handles case-insensitive and trimmed token comparison", () => {
      const cipher = CIPHER_CHALLENGES[1]; // "CHÍNH", "ĐẠI", "QUANG", "MINH"
      const lowerTokens = cipher.solution_tokens.map((t) => `  ${t.toLowerCase()} `);

      const result = verifyCipherSubmission(cipher, lowerTokens);
      expect(result.isCorrect).toBe(true);
      expect(result.scoreAwarded).toBe(cipher.points);
    });
  });

  // -------------------------------------------------------------------------
  // 5. Candidate Monuments
  // -------------------------------------------------------------------------
  describe("Candidate Monuments", () => {
    it("includes all 6 key Đại Nội monuments for detective investigations", () => {
      expect(CANDIDATE_MONUMENTS.length).toBe(6);
      const slugs = CANDIDATE_MONUMENTS.map((m) => m.slug);
      expect(slugs).toContain("ngo-mon");
      expect(slugs).toContain("dien-thai-hoa");
      expect(slugs).toContain("dien-kien-trung");
      expect(slugs).toContain("hien-lam-cac");
      expect(slugs).toContain("the-to-mieu");
      expect(slugs).toContain("thai-binh-lau");
    });
  });
});
