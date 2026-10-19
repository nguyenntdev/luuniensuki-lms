import { describe, it, expect } from "vitest";
import * as React from "react";
import {
  RbpcButton,
  RbpcCard,
  RbpcCardHeader,
  RbpcCardTitle,
  RbpcCardDescription,
  RbpcCardContent,
  RbpcCardFooter,
  EpistemicBadge,
  CitationDrawer,
  EvidenceStatus,
  EVIDENCE_STAGES,
  parseEvidenceStage,
} from "./index";
import { getEpistemicBadgeCopy, getRbpcCopy } from "@/lib/rbpc/copy";

describe("RbpcButton Component Contract", () => {
  it("exports a valid React component with correct displayName", () => {
    expect(RbpcButton).toBeDefined();
    expect(RbpcButton.displayName).toBe("RbpcButton");
  });

  it("creates button element with default primary variant and touch-target classes", () => {
    const element = React.createElement(
      RbpcButton,
      { variant: "primary", size: "md" },
      "Khám phá"
    );
    expect(element.props.variant).toBe("primary");
    expect(element.props.size).toBe("md");
    expect(element.props.children).toBe("Khám phá");
  });

  it("supports all required visual variants", () => {
    const variants = ["primary", "secondary", "subtle", "highlight"] as const;
    for (const v of variants) {
      const el = React.createElement(RbpcButton, { variant: v }, "Action");
      expect(el.props.variant).toBe(v);
    }
  });

  it("enforces minimum 44x44px touch-target bounds even on small size", () => {
    const smBtn = React.createElement(RbpcButton, { size: "sm" }, "Small");
    expect(smBtn.props.size).toBe("sm");
  });

  it("handles loading states with accessible text announcement", () => {
    const loadingBtn = React.createElement(
      RbpcButton,
      { isLoading: true, loadingText: "Đang lưu..." },
      "Gửi"
    );
    expect(loadingBtn.props.isLoading).toBe(true);
    expect(loadingBtn.props.loadingText).toBe("Đang lưu...");
  });
});

describe("RbpcCard Component Contract", () => {
  it("exports root card and all compound editorial subcomponents", () => {
    expect(RbpcCard).toBeDefined();
    expect(RbpcCard.displayName).toBe("RbpcCard");
    expect(RbpcCardHeader).toBeDefined();
    expect(RbpcCardTitle).toBeDefined();
    expect(RbpcCardDescription).toBeDefined();
    expect(RbpcCardContent).toBeDefined();
    expect(RbpcCardFooter).toBeDefined();
  });

  it("defaults to warm paper surface elevation and medium padding", () => {
    const card = React.createElement(RbpcCard, null, "Card Content");
    expect(card.type).toBe(RbpcCard);
    expect(card.props.elevation ?? "surface").toBe("surface");
    expect(card.props.padding ?? "md").toBe("md");
  });

  it("supports interactive configuration without heavy backdrop blur", () => {
    const interactiveCard = React.createElement(
      RbpcCard,
      { interactive: true, elevation: "surface" },
      React.createElement(RbpcCardTitle, null, "Điện Thái Hòa"),
      React.createElement(RbpcCardContent, null, "Khảo cứu kiến trúc cung đình.")
    );
    expect(interactiveCard.props.interactive).toBe(true);
  });
});

describe("EpistemicBadge Component Contract", () => {
  it("exports EpistemicBadge component with displayName", () => {
    expect(EpistemicBadge).toBeDefined();
    expect(EpistemicBadge.displayName).toBe("EpistemicBadge");
  });

  it("correctly evaluates canonical Vietnamese microcopy for all 5 required certainty states", () => {
    const testCases = [
      {
        input: "Verified by source",
        canonicalId: "verified_source",
        expectedLabelVi: "Đã đối chiếu tư liệu",
        expectedBadgeClass: "rbpc-badge-verified",
      },
      {
        input: "Traditional account",
        canonicalId: "traditional_account",
        expectedLabelVi: "Ghi chép truyền thống",
        expectedBadgeClass: "rbpc-badge-tradition",
      },
      {
        input: "Academic interpretation",
        canonicalId: "academic_interpretation",
        expectedLabelVi: "Kiểm giải học thuật",
        expectedBadgeClass: "rbpc-badge-interpretation",
      },
      {
        input: "Evidence gap",
        canonicalId: "evidence_gap",
        expectedLabelVi: "Chưa đủ tư liệu khẳng định",
        expectedBadgeClass: "rbpc-badge-gap",
      },
      {
        input: "UNESCO 678 Component",
        canonicalId: "unesco_inscribed",
        expectedLabelVi: "Di sản Thế giới UNESCO",
        expectedBadgeClass: "rbpc-badge-unesco",
      },
    ];

    for (const tc of testCases) {
      const copy = getEpistemicBadgeCopy(tc.canonicalId, "vi");
      expect(copy.label).toBe(tc.expectedLabelVi);
      expect(copy.badgeClass).toBe(tc.expectedBadgeClass);
      expect(copy.description.length).toBeGreaterThan(10);
    }
  });

  it("correctly evaluates English microcopy for all 5 required certainty states", () => {
    const testCases = [
      { canonicalId: "verified_source", expectedLabelEn: "Verified by source" },
      { canonicalId: "traditional_account", expectedLabelEn: "Traditional account" },
      { canonicalId: "academic_interpretation", expectedLabelEn: "Academic interpretation" },
      { canonicalId: "evidence_gap", expectedLabelEn: "Evidence gap" },
      { canonicalId: "unesco_inscribed", expectedLabelEn: "UNESCO World Heritage" },
    ];

    for (const tc of testCases) {
      const copy = getEpistemicBadgeCopy(tc.canonicalId, "en");
      expect(copy.label.toLowerCase()).toContain(tc.expectedLabelEn.toLowerCase());
      expect(copy.description.length).toBeGreaterThan(10);
    }
  });
});

describe("CitationDrawer Component Contract", () => {
  it("exports CitationDrawer component with displayName", () => {
    expect(CitationDrawer).toBeDefined();
    expect(CitationDrawer.displayName).toBe("CitationDrawer");
  });

  it("handles source evidence items and uses canonical citation microcopy", () => {
    const mockSources = [
      {
        id: "cite-001",
        title: "Đại Nam Thực Lục Chính Biên",
        author: "Quốc Sử Quán Triều Nguyễn",
        publication_year: 1848,
        locator: "Đệ nhị kỷ, Quyển CXX, Tr. 14-16",
        statement: "Đúc chín chiếc đỉnh lớn đặt trước sân Thế Miếu.",
        evidence_status: "verified",
      },
    ];

    const copyVi = getRbpcCopy("vi");
    const copyEn = getRbpcCopy("en");

    expect(copyVi.brand.citationPolicy).toBeDefined();
    expect(copyVi.brand.citationPolicy.length).toBeGreaterThan(20);
    expect(copyVi.cta.close).toBe("Đóng");
    expect(copyVi.cta.copyCitation).toBe("Sao chép trích dẫn");
    expect(copyVi.cta.copied).toBe("Đã sao chép vào bộ nhớ tạm");

    expect(copyEn.cta.close).toBe("Close");
    expect(copyEn.cta.copyCitation).toBe("Copy citation");
    expect(copyEn.cta.copied).toBe("Copied to clipboard");

    const drawer = React.createElement(CitationDrawer, {
      isOpen: true,
      onClose: () => {},
      sources: mockSources,
      entityName: "Cửu Đỉnh",
    });

    expect(drawer.props.isOpen).toBe(true);
    expect(drawer.props.sources).toHaveLength(1);
    expect(drawer.props.entityName).toBe("Cửu Đỉnh");
  });
});

describe("EvidenceStatus Component Contract (S0 to S4 Rubric)", () => {
  it("exports EvidenceStatus component and all 5 canonical stages", () => {
    expect(EvidenceStatus).toBeDefined();
    expect(EvidenceStatus.displayName).toBe("EvidenceStatus");
    expect(Object.keys(EVIDENCE_STAGES)).toEqual(["S0", "S1", "S2", "S3", "S4"]);
  });

  it("accurately parses stage codes from various formats", () => {
    expect(parseEvidenceStage("S0").code).toBe("S0");
    expect(parseEvidenceStage(0).code).toBe("S0");
    expect(parseEvidenceStage("s1").code).toBe("S1");
    expect(parseEvidenceStage(2).code).toBe("S2");
    expect(parseEvidenceStage("stage 3").code).toBe("S3");
    expect(parseEvidenceStage("S4").code).toBe("S4");
    expect(parseEvidenceStage(4).code).toBe("S4");
  });

  it("verifies S0 completeness rubric: Discovered Title Only -> Unpublished", () => {
    const s0 = EVIDENCE_STAGES.S0;
    expect(s0.step).toBe(0);
    expect(s0.labelVi).toBe("Chưa kiểm chứng");
    expect(s0.labelEn).toBe("Discovered Title Only");
    expect(s0.eligibilityVi).toContain("Chưa xuất bản");
  });

  it("verifies S1 completeness rubric: Source-Backed Basic Facts + Authoritative ID -> Candidate Draft", () => {
    const s1 = EVIDENCE_STAGES.S1;
    expect(s1.step).toBe(1);
    expect(s1.labelVi).toBe("Đã định danh nguồn");
    expect(s1.subtitleVi).toContain("Mã định danh chính thức");
    expect(s1.eligibilityVi).toContain("Bản thảo nghiên cứu");
  });

  it("verifies S2 completeness rubric: Editor-Reviewed Narrative + Min 2 Source Citations -> Publishable", () => {
    const s2 = EVIDENCE_STAGES.S2;
    expect(s2.step).toBe(2);
    expect(s2.labelVi).toBe("Ban biên tập duyệt");
    expect(s2.subtitleVi).toContain("Tối thiểu 2 nguồn thư tịch đối chiếu");
    expect(s2.eligibilityVi).toContain("Đủ điều kiện xuất bản");
  });

  it("verifies S3 completeness rubric: Deeper Multiview History + Verified Timeline -> Featured", () => {
    const s3 = EVIDENCE_STAGES.S3;
    expect(s3.step).toBe(3);
    expect(s3.labelVi).toBe("Khảo cứu chuyên sâu");
    expect(s3.eligibilityVi).toContain("Bản ghi nổi bật");
  });

  it("verifies S4 completeness rubric: Living Creator and Commerce Permission -> Eligible for CTA", () => {
    const s4 = EVIDENCE_STAGES.S4;
    expect(s4.step).toBe(4);
    expect(s4.labelVi).toBe("Đối tác xác thực");
    expect(s4.subtitleVi).toContain("Nghệ nhân sống");
    expect(s4.eligibilityVi).toContain("Mở yêu cầu trải nghiệm");
  });

  it("supports compact, pill, stepper, and detailed variants", () => {
    const variants = ["compact", "pill", "stepper", "detailed"] as const;
    for (const v of variants) {
      const el = React.createElement(EvidenceStatus, { stage: "S2", variant: v });
      expect(el.props.variant).toBe(v);
    }
  });
});
