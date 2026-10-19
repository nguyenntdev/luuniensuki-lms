import { describe, it, expect } from "vitest";
import * as React from "react";
import { CulturalBridgePanel } from "./CulturalBridgePanel";
import type { CulturalBridgeCitation, CulturalBridgeAnswerPayload } from "./CulturalBridgePanel";

describe("CulturalBridgePanel Component Contract", () => {
  it("exports a valid React component", () => {
    expect(CulturalBridgePanel).toBeDefined();
    expect(typeof CulturalBridgePanel).toBe("function");
  });

  it("creates element with Vietnamese defaults", () => {
    const el = React.createElement(CulturalBridgePanel, {
      locale: "vi",
      entityName: "Điện Kiến Trung",
      entitySlug: "dien-kien-trung",
    });
    expect(el.props.locale).toBe("vi");
    expect(el.props.entityName).toBe("Điện Kiến Trung");
    expect(el.props.entitySlug).toBe("dien-kien-trung");
  });

  it("creates element with English locale", () => {
    const el = React.createElement(CulturalBridgePanel, {
      locale: "en",
      entityName: "Kiến Trung Palace",
      storySlug: "nghe-thuat-phap-lam-hue",
    });
    expect(el.props.locale).toBe("en");
    expect(el.props.entityName).toBe("Kiến Trung Palace");
    expect(el.props.storySlug).toBe("nghe-thuat-phap-lam-hue");
  });

  it("conforms to CulturalBridgeCitation interface", () => {
    const citation: CulturalBridgeCitation = {
      citation_number: 1,
      source_id: "00000000-0000-0000-0000-000000000001",
      source_title: "Khâm Định Đại Nam Hội Điển Sự Lệ",
      locator: "Quyển 159, tr. 40",
      cited_statement: "Đúc Cửu Đỉnh năm 1835",
    };
    expect(citation.citation_number).toBe(1);
    expect(citation.source_title).toBe("Khâm Định Đại Nam Hội Điển Sự Lệ");
  });

  it("conforms to CulturalBridgeAnswerPayload fail-closed schema", () => {
    const payload: CulturalBridgeAnswerPayload = {
      status: "insufficient_evidence",
      locale: "vi",
      answer_markdown: "Hệ thống chưa đủ tư liệu kiểm chứng.",
      citations: [],
      epistemic_certainty: "insufficient_sources",
      context_boundary: "AI không phỏng đoán ngoài nguồn.",
      linked_experience_slug: "workshop-phap-lam-hue",
      linked_experience_title: "Lớp học nghệ thuật họa Pháp lam hoàng cung",
    };
    expect(payload.status).toBe("insufficient_evidence");
    expect(payload.citations).toHaveLength(0);
    expect(payload.linked_experience_slug).toBe("workshop-phap-lam-hue");
  });
});
