import { describe, it, expect } from "vitest";
import {
  createTeacherAssignment,
  fetchArtDetail,
  fetchClues,
  fetchGameQuestions,
  fetchMediaHotspots,
  fetchSiteArtDetails,
  fetchSiteLearningMedia,
  fetchTeacherAssignments,
  saveArtDetail,
  saveMediaHotspot,
  submitClueAttempt,
  submitGameAnswer,
} from "./v51-api";
import {
  EVIDENCE_STRENGTH_METADATA,
  STORY_TYPE_METADATA,
} from "./v51-types";

describe("STTTNNĐ V5.1 API & Types Client Suite", () => {
  it("fetchSiteLearningMedia returns learning media for Điện Thái Hòa with valid UV hotspots", async () => {
    const mediaList = await fetchSiteLearningMedia("dien-thai-hoa");
    expect(mediaList).toBeDefined();
    expect(mediaList.length).toBeGreaterThanOrEqual(1);

    const firstMedia = mediaList[0];
    expect(firstMedia.media_url).toBeDefined();
    expect(["image", "panorama360", "model3d"]).toContain(firstMedia.kind);

    if (firstMedia.hotspots && firstMedia.hotspots.length > 0) {
      firstMedia.hotspots.forEach((h) => {
        expect(h.u).toBeGreaterThanOrEqual(0);
        expect(h.u).toBeLessThanOrEqual(1);
        expect(h.v).toBeGreaterThanOrEqual(0);
        expect(h.v).toBeLessThanOrEqual(1);
        expect(h.title).toBeDefined();
      });
    }
  });

  it("fetchMediaHotspots retrieves hotspots with normalized UV coordinates", async () => {
    const hotspots = await fetchMediaHotspots("media-thai-hoa-2d");
    expect(hotspots).toBeDefined();
    expect(hotspots.length).toBeGreaterThanOrEqual(2);

    hotspots.forEach((h) => {
      expect(h.media_id).toBe("media-thai-hoa-2d");
      expect(h.u).toBeGreaterThanOrEqual(0.0);
      expect(h.u).toBeLessThanOrEqual(1.0);
      expect(h.v).toBeGreaterThanOrEqual(0.0);
      expect(h.v).toBeLessThanOrEqual(1.0);
    });
  });

  it("fetchArtDetail returns full 6-section historical & pedagogical record", async () => {
    const detail = await fetchArtDetail("ngai-vang-hoang-de");
    expect(detail).toBeDefined();
    expect(detail?.title).toContain("Ngai Vàng");
    expect(detail?.slug).toBe("ngai-vang-hoang-de");

    // 1. Observation
    expect(detail?.description_observation).toBeDefined();
    expect(detail?.motif).toBeDefined();
    expect(detail?.material).toBeDefined();

    // 2. Story & Story Type Badge
    expect(detail?.story_body).toBeDefined();
    expect(["documented_event", "legend", "oral_account", "interpretation"]).toContain(
      detail?.story_type,
    );
    expect(STORY_TYPE_METADATA[detail!.story_type]).toBeDefined();

    // 3. Meaning
    expect(detail?.meaning_body).toBeDefined();

    // 4. Values (Historical, Cultural, Art)
    expect(detail?.historical_value_body).toBeDefined();
    expect(detail?.cultural_value_body).toBeDefined();
    expect(detail?.art_value_body).toBeDefined();

    // 5. Sources & Citations
    expect(detail?.claim_sources).toBeDefined();
    expect(detail?.claim_sources?.length).toBeGreaterThanOrEqual(1);
    detail?.claim_sources?.forEach((src) => {
      expect(src.source_title).toBeDefined();
      expect(src.claim_text).toBeDefined();
      expect(["verified", "probable", "traditional"]).toContain(src.evidence_strength);
      expect(EVIDENCE_STRENGTH_METADATA[src.evidence_strength]).toBeDefined();
    });

    // 6. Formative Reinforcement Questions
    expect(detail?.questions).toBeDefined();
    expect(detail?.questions?.length).toBeGreaterThanOrEqual(1);
    detail?.questions?.forEach((q) => {
      expect(q.prompt).toBeDefined();
      expect(q.options.length).toBeGreaterThanOrEqual(2);
      expect(q.answer_key).toBeDefined();
    });
  });

  it("fetchSiteArtDetails returns all art details belonging to a site", async () => {
    const details = await fetchSiteArtDetails("dien-thai-hoa");
    expect(details.length).toBeGreaterThanOrEqual(1);
    expect(details.some((d) => d.slug === "ngai-vang-hoang-de")).toBe(true);
  });

  it("fetchClues and submitClueAttempt evaluate progressive clues accurately", async () => {
    const clues = await fetchClues();
    expect(clues.length).toBeGreaterThanOrEqual(1);

    const firstClue = clues[0];
    expect(firstClue.clue_text).toBeDefined();
    expect(firstClue.hint_steps.length).toBeGreaterThanOrEqual(1);

    // Correct attempt
    const successResult = await submitClueAttempt(
      firstClue.id,
      firstClue.target_id || "",
    );
    expect(successResult.success).toBe(true);
    expect(successResult.points_awarded).toBeGreaterThan(0);

    // Incorrect attempt
    const failResult = await submitClueAttempt(firstClue.id, "wrong-target-id");
    expect(failResult.success).toBe(false);
    expect(failResult.points_awarded).toBe(0);
  });

  it("fetchGameQuestions and submitGameAnswer provide instant pedagogical feedback", async () => {
    const questions = await fetchGameQuestions();
    expect(questions.length).toBeGreaterThanOrEqual(1);

    const firstQ = questions[0];
    expect(firstQ.prompt).toBeDefined();
    expect(firstQ.options.length).toBeGreaterThanOrEqual(2);

    const answerIdx = firstQ.answer_key ? parseInt(firstQ.answer_key, 10) : 1;
    const submitResult = await submitGameAnswer(firstQ.id, answerIdx);
    expect(submitResult.correct).toBe(true);
    expect(submitResult.explanation).toBeDefined();
  });

  it("fetchTeacherAssignments and createTeacherAssignment handle teacher workflows", async () => {
    const assignments = await fetchTeacherAssignments();
    expect(assignments.length).toBeGreaterThanOrEqual(1);

    const created = await createTeacherAssignment({
      class_name: "Lớp 9A1 Di Sản Huế",
      title: "Khảo sát Ngọ Môn và Lầu Ngũ Phụng",
      journey_slug: "truc-trung-tam",
    });
    expect(created).toBeDefined();
    expect(created.id).toBeDefined();
    expect(created.title).toBe("Khảo sát Ngọ Môn và Lầu Ngũ Phụng");
    expect(created.is_active).toBe(true);
  });

  it("saveMediaHotspot clamps UV coordinates strictly between 0.0 and 1.0", async () => {
    const spot = await saveMediaHotspot({
      media_id: "media-thai-hoa-2d",
      u: 1.25, // over limit
      v: -0.4, // under limit
      title: "Test Clamped Hotspot",
    });

    expect(spot.u).toBe(1.0);
    expect(spot.v).toBe(0.0);
  });

  it("saveArtDetail preserves all 6 sections and persists correctly", async () => {
    const newDetail = await saveArtDetail({
      title: "Đầu đao mái rồng lầu Ngũ Phụng",
      slug: "dau-dao-mai-rong-ngu-phung",
      kind: "carving",
      motif: "Rồng vờn mây",
      material: "Vữa vôi cổ truyền và mảnh sành sứ",
      technique: "Khảm sành sứ",
      description_observation: "Đầu đao uốn cong thanh thoát...",
      story_body: "Chế tác dưới triều vua Minh Mạng...",
      story_type: "documented_event",
      meaning_body: "Biểu trưng cho vũ trụ và ngũ hành...",
      historical_value_body: "Giá trị bảo tồn thế kỷ XIX...",
      cultural_value_body: "Dấu ấn văn hóa cung đình Huế...",
      art_value_body: "Đỉnh cao khảm sành sứ...",
      claim_sources: [
        {
          section: "Chính sử",
          claim_text: "Xây dựng năm 1833",
          source_title: "Đại Nam Thực Lục",
          evidence_strength: "verified",
        },
      ],
      questions: [
        {
          id: "q-test-1",
          question_type: "multiple_choice",
          prompt: "Đầu đao này được khảm bằng gì?",
          options: ["Sành sứ", "Đồng", "Bạc", "Gốm thường"],
          answer_key: "0",
          explanation: "Khảm từ các mảnh sành bát sứ ngũ sắc.",
          display_order: 1,
        },
      ],
    });

    expect(newDetail.id).toBeDefined();
    expect(newDetail.slug).toBe("dau-dao-mai-rong-ngu-phung");
    expect(newDetail.claim_sources?.length).toBe(1);
    expect(newDetail.questions?.length).toBe(1);
  });
});
