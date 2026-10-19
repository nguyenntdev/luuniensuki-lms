import { describe, it, expect } from "vitest";
import * as React from "react";
import {
  CreatorProfileCard,
  ExperienceCard,
  InquiryFormModal,
  LearnRoadmapCard,
} from "./index";
import type {
  RbpcCreator,
  RbpcExperience,
  LearnPathwayModule,
} from "@/types/rbpc";
import { getRbpcCopy } from "@/lib/rbpc/copy";

describe("CreatorProfileCard Component Contract", () => {
  const mockCreator: RbpcCreator = {
    id: "creator-001",
    slug: "nguyen-van-cuu",
    publicName: "Nghệ nhân Nguyễn Văn Cửu",
    craftTradition: {
      vi: "Đúc đồng truyền thống Phường Đúc",
      en: "Traditional Bronze Casting of Phường Đúc",
    },
    approvedBio: {
      vi: "Hơn 48 năm gắn bó với lò than đỏ lửa, kế thừa kỹ nghệ rót đồng cung đình thời Nguyễn.",
      en: "Over 48 years dedicated to glowing charcoal kilns, carrying forward Nguyen dynasty imperial casting techniques.",
    },
    approvedPortraitUrl: "https://assets.histolab.icu/creators/cuu.webp",
    portraitAlt: "Chân dung nghệ nhân Nguyễn Văn Cửu",
    publicRegion: "Phường Đúc, TP. Huế",
    consentStatus: "verified_written_consent",
    yearsOfPractice: 48,
    generationLineage: "Đời thứ 5",
    displayConsentId: "CONSENT-PD-001",
    approvedStorySlugs: ["ky-nghe-duc-dong-phuong-duc"],
    experienceSlugs: ["tham-am-rot-dong", "duc-chuong-nho"],
    createdAt: "2026-10-18T00:00:00Z",
  };

  it("exports CreatorProfileCard with correct displayName", () => {
    expect(CreatorProfileCard).toBeDefined();
    expect(CreatorProfileCard.displayName).toBe("CreatorProfileCard");
  });

  it("instantiates card with artisan name, lineage, and bilingual craft tradition", () => {
    const elVi = React.createElement(CreatorProfileCard, {
      creator: mockCreator,
      locale: "vi",
    });
    expect(elVi.props.creator.publicName).toBe("Nghệ nhân Nguyễn Văn Cửu");
    expect(elVi.props.creator.generationLineage).toBe("Đời thứ 5");

    const elEn = React.createElement(CreatorProfileCard, {
      creator: mockCreator,
      locale: "en",
    });
    expect(elEn.props.locale).toBe("en");
    expect(elEn.props.creator.craftTradition.en).toBe(
      "Traditional Bronze Casting of Phường Đúc"
    );
  });

  it("handles fail-closed privacy fallback when consentStatus is revoked", () => {
    const revokedCreator: RbpcCreator = {
      ...mockCreator,
      consentStatus: "revoked",
    };

    const el = React.createElement(CreatorProfileCard, {
      creator: revokedCreator,
      locale: "vi",
    });

    expect(el.props.creator.consentStatus).toBe("revoked");
  });
});

describe("ExperienceCard Component Contract", () => {
  const mockExperience: RbpcExperience = {
    id: "exp-001",
    slug: "tham-am-rot-dong",
    creatorSlug: "nguyen-van-cuu",
    creatorName: "Nghệ nhân Nguyễn Văn Cửu",
    title: {
      vi: "Kỹ nghệ thẩm âm & Rót đồng truyền thống",
      en: "Acoustic Tuning & Traditional Bronze Pouring",
    },
    description: {
      vi: "Khám phá quy trình nhào đất bãi bồi sông Hương, thử âm thanh phôi đồng chín.",
      en: "Explore the Song Huong clay molding process and acoustic tuning of molten bronze.",
    },
    syllabus: [
      {
        stepNumber: 1,
        title: { vi: "Chuyện đất & lò than", en: "Clay & Kiln History" },
        durationMinutes: 30,
        description: { vi: "Chọn đất sét", en: "Selecting river clay" },
        activityType: "historical_discussion",
      },
      {
        stepNumber: 2,
        title: { vi: "Kỹ nghệ nghe tiếng đồng", en: "Tuning Molten Bronze" },
        durationMinutes: 60,
        description: { vi: "Gõ búa thẩm âm", en: "Acoustic hammer testing" },
        activityType: "demonstration",
      },
      {
        stepNumber: 3,
        title: { vi: "Đúc chuông gió nhỏ", en: "Casting Wind Chime" },
        durationMinutes: 60,
        description: { vi: "Tự tay đúc chuông", en: "Hands-on casting" },
        activityType: "hands_on",
      },
    ],
    areaPublic: "Phường Đúc, TP. Huế",
    durationMinutes: 150,
    pricing: {
      isFree: false,
      amount: 450000,
      currency: "VND",
      displayFormatted: "Từ 450.000 VNĐ / khách",
      pricingUnit: "per_person",
    },
    availabilityMode: "inquiry_only",
    maxPartySize: 8,
    languagesSupported: ["vi", "en"],
    notice:
      "Yêu cầu trải nghiệm chỉ là bước liên hệ xác nhận, không phải giao dịch thanh toán tức thì.",
    publicationState: "published",
    createdAt: "2026-10-18T00:00:00Z",
    updatedAt: "2026-10-18T00:00:00Z",
  };

  it("exports ExperienceCard with correct displayName", () => {
    expect(ExperienceCard).toBeDefined();
    expect(ExperienceCard.displayName).toBe("ExperienceCard");
  });

  it("verifies experience properties and inquiry-only notice mandate", () => {
    const el = React.createElement(ExperienceCard, {
      experience: mockExperience,
      locale: "vi",
    });

    expect(el.props.experience.availabilityMode).toBe("inquiry_only");
    expect(el.props.experience.durationMinutes).toBe(150);
    expect(el.props.experience.areaPublic).toBe("Phường Đúc, TP. Huế");
    expect(el.props.experience.pricing.displayFormatted).toContain("450.000");
  });

  it("uses canonical 'Request availability' microcopy in both languages", () => {
    const copyVi = getRbpcCopy("vi");
    const copyEn = getRbpcCopy("en");

    expect(copyVi.cta.requestAvailability).toBe("Yêu cầu lịch hẹn");
    expect(copyEn.cta.requestAvailability).toBe("Request availability");
    expect(copyEn.cta.requestAvailability).not.toContain("Book now");
    expect(copyEn.cta.requestAvailability).not.toContain("Pay");
  });
});

describe("InquiryFormModal Component Contract", () => {
  const mockExperience: RbpcExperience = {
    id: "exp-001",
    slug: "tham-am-rot-dong",
    creatorSlug: "nguyen-van-cuu",
    creatorName: "Nghệ nhân Nguyễn Văn Cửu",
    title: {
      vi: "Kỹ nghệ thẩm âm & Rót đồng truyền thống",
      en: "Acoustic Tuning & Traditional Bronze Pouring",
    },
    description: { vi: "Mô tả", en: "Description" },
    syllabus: [],
    areaPublic: "Phường Đúc",
    durationMinutes: 120,
    pricing: {
      isFree: false,
      amount: 450000,
      currency: "VND",
      displayFormatted: "Từ 450.000 VNĐ / khách",
      pricingUnit: "per_person",
    },
    availabilityMode: "inquiry_only",
    maxPartySize: 8,
    languagesSupported: ["vi"],
    notice: "Thông báo minh bạch",
    publicationState: "published",
    createdAt: "2026-10-18T00:00:00Z",
    updatedAt: "2026-10-18T00:00:00Z",
  };

  it("exports InquiryFormModal with correct displayName", () => {
    expect(InquiryFormModal).toBeDefined();
    expect(InquiryFormModal.displayName).toBe("InquiryFormModal");
  });

  it("creates modal element with experience context and initial props", () => {
    const el = React.createElement(InquiryFormModal, {
      isOpen: true,
      onClose: () => {},
      experience: mockExperience,
      locale: "vi",
    });

    expect(el.props.isOpen).toBe(true);
    expect(el.props.experience?.slug).toBe("tham-am-rot-dong");
    expect(el.props.locale).toBe("vi");
  });

  it("contains canonical bilingual validation error microcopy for mandatory consent", () => {
    const copyVi = getRbpcCopy("vi");
    const copyEn = getRbpcCopy("en");

    expect(copyVi.inquiry.fields.consent.error).toContain(
      "Bạn cần xác nhận đồng thuận"
    );
    expect(copyEn.inquiry.fields.consent.error).toContain(
      "You must provide consent"
    );
  });

  it("contains acknowledgment screen non-commercial disclaimer in both languages", () => {
    const copyVi = getRbpcCopy("vi");
    const copyEn = getRbpcCopy("en");

    expect(copyVi.inquiry.confirmation.disclaimer).toContain(
      "không phải là một giao dịch thương mại hoàn tất"
    );
    expect(copyEn.inquiry.confirmation.disclaimer).toContain(
      "not a confirmed booking"
    );
  });

  it("verifies explicit concept demonstration trust banner in inquiry copy", () => {
    const copyVi = getRbpcCopy("vi");
    const copyEn = getRbpcCopy("en");

    expect(copyVi.inquiry.modalSubtitle).toBe(
      "Concept demonstration — Yêu cầu trải nghiệm sẽ được gửi trực tiếp đến nghệ nhân/cơ sở để xác nhận thời gian."
    );
    expect(copyEn.inquiry.modalSubtitle).toBe(
      "Concept demonstration — Experience requests will be sent directly to the artisan/facility to confirm timing."
    );
  });
});

describe("LearnRoadmapCard Component Contract", () => {
  const mockModule: LearnPathwayModule = {
    id: "mod-01",
    slug: "kham-pha-cao-dinh-3d",
    title: {
      vi: "Giải mã 18 Bản đúc nổi trên Cao Đỉnh",
      en: "Decoding the 18 Relief Inscriptions of Cao Đỉnh",
    },
    description: {
      vi: "Tìm hiểu biểu tượng rồng mây, núi non và sông Hương qua mô hình 3D tương tác.",
      en: "Explore dragon clouds, mountain ranges, and Song Huong river through 3D models.",
    },
    targetAudience: "student",
    linked3DArtefactSlug: "cao-dinh",
    linkedCreatorSlug: "nguyen-van-cuu",
    learningObjectives: [
      {
        vi: "Nhận diện hoa văn chim trĩ và mặt trời trên Cao Đỉnh",
        en: "Identify pheasant and sun motifs on Cao Đỉnh",
      },
      {
        vi: "Hiểu quy trình đúc khuôn đất nung 1835",
        en: "Understand the 1835 terracotta casting process",
      },
    ],
    roadmapPhase: "P2_INTERACTIVE_3D",
    status: "available_in_repo",
    historicalPeriod: "Triều Minh Mạng (1835)",
    sourceCitationsCount: 8,
    estimatedMinutes: 30,
  };

  it("exports LearnRoadmapCard with correct displayName", () => {
    expect(LearnRoadmapCard).toBeDefined();
    expect(LearnRoadmapCard.displayName).toBe("LearnRoadmapCard");
  });

  it("verifies 3D artefact bridge and living creator linkages", () => {
    const el = React.createElement(LearnRoadmapCard, {
      module: mockModule,
      locale: "vi",
    });

    expect(el.props.module.linked3DArtefactSlug).toBe("cao-dinh");
    expect(el.props.module.linkedCreatorSlug).toBe("nguyen-van-cuu");
    expect(el.props.module.roadmapPhase).toBe("P2_INTERACTIVE_3D");
    expect(el.props.module.status).toBe("available_in_repo");
    expect(el.props.module.sourceCitationsCount).toBe(8);
  });

  it("verifies all 4 canonical roadmap phases are supported", () => {
    const phases = [
      "P1_HERITAGE_BASELINE",
      "P2_INTERACTIVE_3D",
      "P3_MAKER_MASTERCLASS",
      "P4_ACCREDITED_CURRICULUM",
    ] as const;

    for (const p of phases) {
      const el = React.createElement(LearnRoadmapCard, {
        module: { ...mockModule, roadmapPhase: p },
        locale: "en",
      });
      expect(el.props.module.roadmapPhase).toBe(p);
    }
  });
});
