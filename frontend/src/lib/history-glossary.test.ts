import { describe, expect, it } from "vitest";
import {
  asGlossaryItem,
  asGlossaryList,
  filterGlossaryTerms,
  formatBilingualCitation,
  getGlossaryEpistemic,
  validateGlossaryTranslationIntegrity,
  GLOSSARY_CATEGORY_LABELS,
  TRANSLATION_ORIGIN_LABELS,
  type HistoryGlossaryItem,
} from "./history";

describe("History Multilingual Glossary & Epigraphy Client Suite (V5-T098)", () => {
  const verifiedTerm: HistoryGlossaryItem = {
    term_key: "cao-dinh",
    term_vi: "Cao Đỉnh",
    term_en: "Cao Urn (The Supreme Urn)",
    term_han_nom: "高鼎",
    reading_quoc_ngu: "Cao Đỉnh",
    category: "relic",
    definition_vi: "Chiếc đỉnh lớn nhất đặt ở vị trí trung tâm trong Cửu Đỉnh.",
    definition_en: "The foremost urn among the Nine Dynastic Urns situated at the center.",
    review_status: "verified",
    origin: "human_epigrapher",
    epigrapher_signoff: "Prof. Nguyen Dinh Chien",
    citation_locator: "Đại Nam Thực Lục, Đệ nhị kỷ, Quyển 162",
    bilingual_citation: {
      title_vi: "Đại Nam Thực Lục Chính Biên",
      title_en: "Veritable Records of Dai Nam",
      locator: "Quyển 162",
    },
    is_machine_translated: false,
    is_uncertain: false,
  };

  const machineTranslatedTerm: HistoryGlossaryItem = {
    term_key: "dang-son-ngu",
    term_vi: "Đăng Sơn Ngư",
    term_en: "Climbing perch fish",
    term_han_nom: null,
    reading_quoc_ngu: "Đăng Sơn Ngư",
    category: "flora_fauna",
    definition_vi: "Cá rô leo cây đúc trên Thuần Đỉnh.",
    definition_en: "Climbing perch fish depicted on Thuan Urn.",
    review_status: "unreviewed",
    origin: "machine_translated",
    is_machine_translated: true,
    is_uncertain: true,
    uncertainty_label: "Bản dịch máy tự động — chưa qua thẩm định chuyên gia Hán–Nôm.",
  };

  const mismatchedTerm: HistoryGlossaryItem = {
    term_key: "mismatched-entry",
    term_vi: "Thuần Đỉnh",
    term_en: "placeholder",
    definition_vi: "Chiếc đỉnh thứ năm biểu trưng cho sự thuần khiết.",
    definition_en: "Chiếc đỉnh thứ năm biểu trưng cho sự thuần khiết.",
    review_status: "provisional",
    origin: "ai_generated",
    is_machine_translated: false,
  };

  it("normalizes both list envelopes and raw arrays defensively", () => {
    expect(asGlossaryList(null)).toEqual([]);
    expect(asGlossaryList(undefined)).toEqual([]);
    expect(asGlossaryList("invalid")).toEqual([]);
    expect(asGlossaryList([verifiedTerm])).toHaveLength(1);
    expect(asGlossaryList({ items: [verifiedTerm, machineTranslatedTerm], total: 2 })).toHaveLength(2);

    expect(asGlossaryItem(verifiedTerm)?.term_key).toBe("cao-dinh");
    expect(asGlossaryItem(null)).toBeNull();
  });

  it("resolves verified terms to documented epistemic tone", () => {
    const badge = getGlossaryEpistemic(verifiedTerm);
    expect(badge.code).toBe("su_lieu_xac_thuc");
    expect(badge.label).toBe("Sử liệu xác thực");
    expect(badge.tone).toBe("documented");
    expect(badge.description).toContain("Prof. Nguyen Dinh Chien");
  });

  it("resolves machine-translated or unreviewed terms to uncertain epistemic tone", () => {
    const badge = getGlossaryEpistemic(machineTranslatedTerm);
    expect(badge.code).toBe("dang_khao_cuu");
    expect(badge.label).toBe("Đang khảo cứu");
    expect(badge.tone).toBe("uncertain");
    expect(badge.description).toContain("Bản dịch máy tự động");
  });

  it("negative abuse: detects and flags placeholder and duplicate translations", () => {
    const validation = validateGlossaryTranslationIntegrity(mismatchedTerm);
    expect(validation.isValid).toBe(false);
    expect(validation.isUncertain).toBe(true);
    expect(validation.flags).toContain("PLACEHOLDER_TERM_EN");
    expect(validation.flags).toContain("UNTRANSLATED_DUPLICATION");
    expect(validation.uncertaintyLabel).toBeDefined();
  });

  it("formats bilingual citations accurately", () => {
    const citation = verifiedTerm.bilingual_citation;
    const formattedVi = formatBilingualCitation(citation, "vi");
    expect(formattedVi).toContain("Đại Nam Thực Lục Chính Biên");
    expect(formattedVi).toContain("(Veritable Records of Dai Nam)");
    expect(formattedVi).toContain("Quyển 162");

    const formattedEn = formatBilingualCitation(citation, "en");
    expect(formattedEn).toContain("Veritable Records of Dai Nam");
    expect(formattedEn).toContain("(Đại Nam Thực Lục Chính Biên)");
  });

  it("filters glossary terms by query, diacritics, and category", () => {
    const terms = [verifiedTerm, machineTranslatedTerm, mismatchedTerm];

    // Diacritic-insensitive search "cao dinh"
    const res1 = filterGlossaryTerms(terms, "cao dinh");
    expect(res1).toHaveLength(1);
    expect(res1[0].term_key).toBe("cao-dinh");

    // English search "perch"
    const res2 = filterGlossaryTerms(terms, "perch");
    expect(res2).toHaveLength(1);
    expect(res2[0].term_key).toBe("dang-son-ngu");

    // Category filter "relic"
    const res3 = filterGlossaryTerms(terms, "", { category: "relic" });
    expect(res3).toHaveLength(1);
    expect(res3[0].term_key).toBe("cao-dinh");

    // Verified only filter
    const res4 = filterGlossaryTerms(terms, "", { verifiedOnly: true });
    expect(res4).toHaveLength(1);
    expect(res4[0].term_key).toBe("cao-dinh");
  });

  it("exposes category and provenance labels with bilingual coverage", () => {
    expect(GLOSSARY_CATEGORY_LABELS.relic.vi).toBe("Bảo vật / Đỉnh đồng");
    expect(GLOSSARY_CATEGORY_LABELS.relic.en).toBe("Relic / Bronze Urn");
    expect(TRANSLATION_ORIGIN_LABELS.human_epigrapher.vi).toContain("Chuyên gia Hán–Nôm");
    expect(TRANSLATION_ORIGIN_LABELS.machine_translated.en).toBe("Machine Translated");
  });
});
