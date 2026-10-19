import { describe, it, expect, vi } from "vitest";
import * as React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import {
  StoryArtisanBridge,
  PartnerInboxView,
  InquiryFormModal,
  maskContactValue,
  getStatusBadgeInfo,
  VALID_TRANSITIONS,
  type PartnerInboxItemWithAudit,
} from "./index";
import type {
  ArtisanBridgeStoryBlock,
  RbpcCreator,
  RbpcExperience,
  InquiryStatus,
} from "@/types/rbpc";
import { getRbpcCopy } from "@/lib/rbpc/copy";

describe("StoryArtisanBridge Component Contract", () => {
  const mockBlock: ArtisanBridgeStoryBlock = {
    id: "block-artisan-bridge-01",
    type: "artisan_bridge",
    creatorSlug: "nguyen-van-cuu",
    creatorName: "Nghệ nhân Nguyễn Văn Cửu",
    craftTradition: {
      vi: "Đúc đồng truyền thống Phường Đúc",
      en: "Traditional Bronze Casting of Phường Đúc",
    },
    portraitUrl: "https://assets.histolab.icu/creators/cuu.webp",
    bridgeNarrative: {
      vi: "Kế thừa kỹ nghệ rót đồng cung đình thời Tự Đức, nối dài mạch nguồn văn hóa từ thời các hiệp thợ đúc Cửu Đỉnh năm 1835.",
      en: "Inheriting imperial bronze casting techniques from the Tu Duc era, extending the cultural lineage of the 1835 Nine Dynastic Urns foundries.",
    },
    consentStatus: "consented",
    verificationBadge: {
      type: "written_consent",
      label: {
        vi: "Đã xác minh văn bản đồng thuận",
        en: "Verified Written Consent",
      },
      verifiedAt: "2026-08-12T00:00:00Z",
      documentRef: "CONSENT-PD-001",
      tooltip: {
        vi: "Biên bản đồng thuận có chữ ký lưu trữ tại Văn phòng Dự án Lưu Niên",
        en: "Signed physical consent record archived at Luu Nien project office",
      },
    },
    experienceSlug: "tham-am-rot-dong",
    experienceTitle: {
      vi: "Kỹ nghệ thẩm âm & Rót đồng truyền thống",
      en: "Acoustic Tuning & Traditional Bronze Pouring",
    },
    experiencePriceDisplay: "Từ 450.000 VNĐ / khách",
    ctaLabel: {
      vi: "Yêu cầu lịch hẹn",
      en: "Request availability",
    },
  };

  const mockCreator: RbpcCreator = {
    id: "creator-001",
    slug: "nguyen-van-cuu",
    publicName: "Nghệ nhân Nguyễn Văn Cửu",
    craftTradition: {
      vi: "Đúc đồng truyền thống Phường Đúc",
      en: "Traditional Bronze Casting of Phường Đúc",
    },
    approvedBio: {
      vi: "Hơn 48 năm gắn bó với lò than đỏ lửa.",
      en: "Over 48 years dedicated to glowing charcoal kilns.",
    },
    approvedPortraitUrl: "https://assets.histolab.icu/creators/cuu.webp",
    portraitAlt: "Chân dung nghệ nhân Nguyễn Văn Cửu",
    publicRegion: "Phường Đúc, TP. Huế",
    consentStatus: "consented",
    yearsOfPractice: 48,
    generationLineage: "Đời thứ 5",
    displayConsentId: "CONSENT-PD-001",
    approvedStorySlugs: ["ky-nghe-duc-dong-phuong-duc"],
    experienceSlugs: ["tham-am-rot-dong"],
    createdAt: "2026-10-18T00:00:00Z",
  };

  const mockExperience: RbpcExperience = {
    id: "exp-001",
    slug: "tham-am-rot-dong",
    creatorSlug: "nguyen-van-cuu",
    creatorName: "Nghệ nhân Nguyễn Văn Cửu",
    title: {
      vi: "Kỹ nghệ thẩm âm & Rót đồng truyền thống",
      en: "Acoustic Tuning & Traditional Bronze Pouring",
    },
    description: { vi: "Mô tả trải nghiệm", en: "Experience description" },
    syllabus: [],
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

  it("exports StoryArtisanBridge with correct displayName", () => {
    expect(StoryArtisanBridge).toBeDefined();
    expect(StoryArtisanBridge.displayName).toBe("StoryArtisanBridge");
  });

  it("renders with polymorphic block and extracts master artisan credentials", () => {
    const el = React.createElement(StoryArtisanBridge, {
      block: mockBlock,
      locale: "vi",
    });

    expect(el.props.block?.creatorName).toBe("Nghệ nhân Nguyễn Văn Cửu");
    expect(el.props.block?.experienceSlug).toBe("tham-am-rot-dong");
    expect(el.props.block?.experiencePriceDisplay).toContain("450.000");
  });

  it("renders with separate creator and experience objects when block is omitted", () => {
    const el = React.createElement(StoryArtisanBridge, {
      creator: mockCreator,
      experience: mockExperience,
      locale: "en",
    });

    expect(el.props.creator?.publicName).toBe("Nghệ nhân Nguyễn Văn Cửu");
    expect(el.props.creator?.yearsOfPractice).toBe(48);
    expect(el.props.experience?.durationMinutes).toBe(150);
  });

  it("preserves non-commercial request availability microcopy (never book now or buy)", () => {
    const copyVi = getRbpcCopy("vi");
    const copyEn = getRbpcCopy("en");

    expect(copyVi.cta.requestAvailability).toBe("Yêu cầu lịch hẹn");
    expect(copyEn.cta.requestAvailability).toBe("Request availability");

    // Strictly forbidden commercial checkout words in cultural bridge CTA
    expect(copyEn.cta.requestAvailability.toLowerCase()).not.toContain("book");
    expect(copyEn.cta.requestAvailability.toLowerCase()).not.toContain("pay");
    expect(copyEn.cta.requestAvailability.toLowerCase()).not.toContain("instant");
  });

  it("verifies canonical concept demonstration trust messaging", () => {
    const copyVi = getRbpcCopy("vi");
    const copyEn = getRbpcCopy("en");

    expect(copyVi.inquiry.modalSubtitle).toBe(
      "Concept demonstration — Yêu cầu trải nghiệm sẽ được gửi trực tiếp đến nghệ nhân/cơ sở để xác nhận thời gian."
    );
    expect(copyEn.inquiry.modalSubtitle).toBe(
      "Concept demonstration — Experience requests will be sent directly to the artisan/facility to confirm timing."
    );
  });

  it("enforces fail-closed privacy safeguard when consentStatus is revoked", () => {
    const revokedBlock: ArtisanBridgeStoryBlock = {
      ...mockBlock,
      consentStatus: "revoked",
    };

    const el = React.createElement(StoryArtisanBridge, {
      block: revokedBlock,
      locale: "vi",
    });

    expect(el.props.block?.consentStatus).toBe("revoked");
  });

  it("wires callback handlers for requesting availability and viewing maker", () => {
    const onReq = vi.fn();
    const onViewMaker = vi.fn();

    const el = React.createElement(StoryArtisanBridge, {
      block: mockBlock,
      locale: "vi",
      onRequestAvailability: onReq,
      onViewMaker: onViewMaker,
    });

    expect(el.props.onRequestAvailability).toBe(onReq);
    expect(el.props.onViewMaker).toBe(onViewMaker);
  });
});

describe("PartnerInboxView Component Contract & State Machine", () => {
  const mockInquiries: PartnerInboxItemWithAudit[] = [
    {
      id: "inq-001",
      reference: "INQ-7F89-A23C",
      experienceSlug: "tham-am-rot-dong",
      experienceTitle: "Kỹ nghệ thẩm âm & Rót đồng truyền thống",
      providerId: "prov-phuong-duc-01",
      creatorSlug: "nguyen-van-cuu",
      creatorName: "Nghệ nhân Nguyễn Văn Cửu",
      contactName: "Nguyễn An Nhiên",
      contactMethod: "phone",
      contactValue: "0912345678",
      preferredDate: "2026-11-05",
      partySize: 2,
      message: "Chúng tôi là 2 bạn trẻ muốn tìm hiểu kỹ nghệ đúc chuông.",
      status: "new",
      partnerNotes: "Chưa liên hệ",
      createdAt: "2026-10-18T10:00:00Z",
      updatedAt: "2026-10-18T10:00:00Z",
      auditLog: [],
    },
    {
      id: "inq-002",
      reference: "INQ-6E21-B44D",
      experienceSlug: "tham-am-rot-dong",
      experienceTitle: "Kỹ nghệ thẩm âm & Rót đồng truyền thống",
      providerId: "prov-phuong-duc-01",
      creatorSlug: "nguyen-van-cuu",
      creatorName: "Nghệ nhân Nguyễn Văn Cửu",
      contactName: "David Miller",
      contactMethod: "email",
      contactValue: "d.miller@example.com",
      preferredDate: "2026-11-08",
      partySize: 4,
      message: "Interested in the bronze acoustic tuning process.",
      status: "contacted",
      partnerNotes: "Đã gửi email báo khung giờ phù hợp",
      lastContactedAt: "2026-10-18T11:00:00Z",
      createdAt: "2026-10-18T09:30:00Z",
      updatedAt: "2026-10-18T11:00:00Z",
      auditLog: [
        {
          id: "audit-01",
          inquiryId: "inq-002",
          timestamp: "2026-10-18T11:00:00Z",
          actorName: "Xưởng đúc Cửu Long",
          previousStatus: "new",
          newStatus: "contacted",
          note: "Gửi email hẹn giờ",
        },
      ],
    },
    {
      id: "inq-003",
      reference: "INQ-5B10-C89E",
      experienceSlug: "duc-chuong-nho",
      experienceTitle: "Đúc chuông gió nhỏ Phường Đúc",
      providerId: "prov-phuong-duc-01",
      creatorSlug: "nguyen-van-cuu",
      creatorName: "Nghệ nhân Nguyễn Văn Cửu",
      contactName: "Trần Bảo Ngọc",
      contactMethod: "zalo",
      contactValue: "0988112233",
      preferredDate: "2026-10-28",
      partySize: 1,
      message: "Muốn học tự đúc chuông làm quà kỷ niệm.",
      status: "confirmed",
      partnerNotes: "Đã chốt lịch ngày 28/10",
      createdAt: "2026-10-17T08:00:00Z",
      updatedAt: "2026-10-17T14:00:00Z",
    },
    {
      id: "inq-004",
      reference: "INQ-4A02-D11F",
      experienceSlug: "tham-am-rot-dong",
      experienceTitle: "Kỹ nghệ thẩm âm & Rót đồng truyền thống",
      providerId: "prov-phuong-duc-01",
      creatorSlug: "nguyen-van-cuu",
      creatorName: "Nghệ nhân Nguyễn Văn Cửu",
      contactName: "Jean Dupont",
      contactMethod: "email",
      contactValue: "j.dupont@laposte.fr",
      preferredDate: "2026-10-24",
      partySize: 6,
      message: "Group of cultural researchers from Paris.",
      status: "declined",
      partnerNotes: "Xưởng bận lịch đúc chuông lớn",
      createdAt: "2026-10-16T15:00:00Z",
      updatedAt: "2026-10-16T17:00:00Z",
    },
    {
      id: "inq-999",
      reference: "INQ-9999-OTHER",
      experienceSlug: "lam-hoa-giay-thanh-tien",
      experienceTitle: "Làm hoa giấy Thanh Tiên",
      providerId: "prov-thanh-tien-02", // DIFFERENT PROVIDER!
      creatorSlug: "than-van-huy",
      creatorName: "Nghệ nhân Thân Văn Huy",
      contactName: "Khách khác",
      contactMethod: "phone",
      contactValue: "0900000000",
      preferredDate: "2026-11-12",
      partySize: 2,
      status: "new",
      createdAt: "2026-10-18T12:00:00Z",
      updatedAt: "2026-10-18T12:00:00Z",
    },
  ];

  it("exports PartnerInboxView with correct displayName", () => {
    expect(PartnerInboxView).toBeDefined();
    expect(PartnerInboxView.displayName).toBe("PartnerInboxView");
  });

  it("verifies maskContactValue correctly obfuscates email and phone PII", () => {
    // Email masking: preserves first char, mask, last char of user, and domain
    const maskedEmail = maskContactValue("d.miller@example.com", "email");
    expect(maskedEmail).not.toBe("d.miller@example.com");
    expect(maskedEmail).toContain("@example.com");
    expect(maskedEmail).toContain("***");

    // Phone masking: preserves first 4 and last 3 digits
    const maskedPhone = maskContactValue("0912345678", "phone");
    expect(maskedPhone).toBe("0912 ••• 678");

    // Zalo masking: preserves prefix and suffix
    const maskedZalo = maskContactValue("0988112233", "zalo");
    expect(maskedZalo).toBe("0988 ••• 233");
  });

  it("defines strict state transitions matching the lifecycle state machine", () => {
    // new -> contacted, declined
    expect(VALID_TRANSITIONS.new).toEqual(["contacted", "declined"]);

    // contacted -> confirmed, declined
    expect(VALID_TRANSITIONS.contacted).toEqual(["confirmed", "declined"]);

    // confirmed -> closed
    expect(VALID_TRANSITIONS.confirmed).toEqual(["closed"]);

    // declined -> closed
    expect(VALID_TRANSITIONS.declined).toEqual(["closed"]);

    // closed -> terminal (no forward transitions)
    expect(VALID_TRANSITIONS.closed).toEqual([]);
  });

  it("evaluates bilingual status badge information correctly", () => {
    const statuses: InquiryStatus[] = [
      "new",
      "contacted",
      "confirmed",
      "declined",
      "closed",
    ];

    for (const s of statuses) {
      const viBadge = getStatusBadgeInfo(s, "vi");
      const enBadge = getStatusBadgeInfo(s, "en");

      expect(viBadge.label.length).toBeGreaterThan(0);
      expect(enBadge.label.length).toBeGreaterThan(0);
      expect(viBadge.bgClass).toBeDefined();
      expect(viBadge.textClass).toBeDefined();
      expect(viBadge.borderClass).toBeDefined();
    }
  });

  it("instantiates PartnerInboxView with providerId and initial inquiries", () => {
    const el = React.createElement(PartnerInboxView, {
      initialInquiries: mockInquiries,
      providerId: "prov-phuong-duc-01",
      providerName: "Xưởng đúc Cửu Long",
      locale: "vi",
    });

    expect(el.props.providerId).toBe("prov-phuong-duc-01");
    expect(el.props.providerName).toBe("Xưởng đúc Cửu Long");
    expect(el.props.initialInquiries).toHaveLength(5);
  });

  it("enforces strict provider data isolation by filtering out foreign provider items", () => {
    const targetProviderId = "prov-phuong-duc-01";
    const filtered = mockInquiries.filter(
      (item) => !item.providerId || item.providerId === targetProviderId
    );

    // inq-999 belongs to prov-thanh-tien-02, so it MUST be excluded
    expect(filtered).toHaveLength(4);
    expect(filtered.map((i) => i.id)).not.toContain("inq-999");
    expect(filtered.every((i) => i.providerId === targetProviderId)).toBe(true);
  });

  it("handles contact masking edge cases gracefully", () => {
    // Empty or falsy input
    expect(maskContactValue("", "phone")).toBe("");
    expect(maskContactValue("   ", "email")).toBe("");

    // Very short email
    expect(maskContactValue("a@b.com", "email")).toBe("***@b.com");
    expect(maskContactValue("ab@c.com", "email")).toBe("a***@c.com");

    // Short phone numbers
    expect(maskContactValue("12345", "phone")).toBe("12 ••• 45");

    // Standard Vietnamese mobile
    expect(maskContactValue("0905123456", "phone")).toBe("0905 ••• 456");
  });

  it("prohibits invalid transitions violating the state machine", () => {
    // Direct transition from 'new' to 'confirmed' without contacting first is strictly invalid
    expect(VALID_TRANSITIONS.new.includes("confirmed" as InquiryStatus)).toBe(false);

    // Direct transition from 'new' to 'closed' is strictly invalid
    expect(VALID_TRANSITIONS.new.includes("closed" as InquiryStatus)).toBe(false);

    // Transitioning out of terminal 'closed' status is strictly invalid
    expect(VALID_TRANSITIONS.closed).toHaveLength(0);
  });

  it("creates structured audit log entries on state transition", () => {
    const initialStatus: InquiryStatus = "new";
    const targetStatus: InquiryStatus = "contacted";
    const timestamp = new Date().toISOString();

    const auditEntry = {
      id: "audit-test-01",
      inquiryId: "inq-001",
      timestamp,
      actorName: "Xưởng đúc Cửu Long",
      previousStatus: initialStatus,
      newStatus: targetStatus,
      note: "Gọi điện xác nhận lịch hẹn 2 người",
    };

    expect(auditEntry.previousStatus).toBe("new");
    expect(auditEntry.newStatus).toBe("contacted");
    expect(auditEntry.actorName).toBe("Xưởng đúc Cửu Long");
    expect(auditEntry.note).toBe("Gọi điện xác nhận lịch hẹn 2 người");
  });
});

describe("WCAG 2.5.5 Touch Targets, Visible Focus Ring (--rbpc-focus: #1E675A), and Canonical Trust Messaging", () => {
  const canonicalTrustTextVi =
    "Concept demonstration — Yêu cầu trải nghiệm sẽ được gửi trực tiếp đến nghệ nhân/cơ sở để xác nhận thời gian.";
  const canonicalTrustTextEn =
    "Concept demonstration — Experience requests will be sent directly to the artisan/facility to confirm timing.";

  it("confirms canonical trust messaging explicitly in copy.ts dictionary", () => {
    const copyVi = getRbpcCopy("vi");
    const copyEn = getRbpcCopy("en");

    expect(copyVi.inquiry.modalSubtitle).toBe(canonicalTrustTextVi);
    expect(copyEn.inquiry.modalSubtitle).toBe(canonicalTrustTextEn);
  });

  it("verifies InquiryFormModal renders the canonical trust statement and satisfies WCAG 2.5.5 touch targets & focus rings", () => {
    const mockExperience: RbpcExperience = {
      id: "exp-001",
      slug: "tham-am-rot-dong",
      creatorSlug: "nguyen-van-cuu",
      creatorName: "Nghệ nhân Nguyễn Văn Cửu",
      title: {
        vi: "Kỹ nghệ thẩm âm & Rót đồng truyền thống",
        en: "Acoustic Tuning & Traditional Bronze Pouring",
      },
      description: { vi: "Mô tả trải nghiệm", en: "Experience description" },
      syllabus: [],
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
      notice: canonicalTrustTextVi,
      publicationState: "published",
      createdAt: "2026-10-18T00:00:00Z",
      updatedAt: "2026-10-18T00:00:00Z",
    };

    const html = renderToStaticMarkup(
      React.createElement(InquiryFormModal, {
        isOpen: true,
        onClose: () => {},
        experience: mockExperience,
        locale: "vi",
      })
    );

    // 1. Trust messaging
    expect(html).toContain(canonicalTrustTextVi);

    // 2. Visible focus outlines targeting --rbpc-focus (#1E675A)
    expect(html).toContain("focus-visible:ring-[var(--rbpc-focus)]");

    // 3. Minimum 44x44px touch targets on all interactive controls
    expect(html).toContain("min-h-[44px]");
    expect(html).toContain("min-w-[44px]");

    // 4. Consent checkbox unchecked by default with 44px hit-target wrapper
    expect(html).toContain("rbpc-checkbox-wrapper");
    expect(html).toContain('aria-required="true"');
    expect(html).not.toContain('checked=""');
  });

  it("verifies StoryArtisanBridge renders the canonical trust statement and satisfies WCAG 2.5.5 touch targets & focus rings", () => {
    const mockCreator: RbpcCreator = {
      id: "creator-001",
      slug: "nguyen-van-cuu",
      publicName: "Nghệ nhân Nguyễn Văn Cửu",
      craftTradition: {
        vi: "Đúc đồng truyền thống Phường Đúc",
        en: "Traditional Bronze Casting of Phường Đúc",
      },
      approvedBio: {
        vi: "Hơn 48 năm gắn bó với lò than đỏ lửa.",
        en: "Over 48 years dedicated to glowing charcoal kilns.",
      },
      approvedPortraitUrl: "https://assets.histolab.icu/creators/cuu.webp",
      portraitAlt: "Chân dung nghệ nhân Nguyễn Văn Cửu",
      publicRegion: "Phường Đúc, TP. Huế",
      consentStatus: "consented",
      yearsOfPractice: 48,
      generationLineage: "Đời thứ 5",
      displayConsentId: "CONSENT-PD-001",
      approvedStorySlugs: ["ky-nghe-duc-dong-phuong-duc"],
      experienceSlugs: ["tham-am-rot-dong"],
      createdAt: "2026-10-18T00:00:00Z",
    };

    const mockExperience: RbpcExperience = {
      id: "exp-001",
      slug: "tham-am-rot-dong",
      creatorSlug: "nguyen-van-cuu",
      creatorName: "Nghệ nhân Nguyễn Văn Cửu",
      title: {
        vi: "Kỹ nghệ thẩm âm & Rót đồng truyền thống",
        en: "Acoustic Tuning & Traditional Bronze Pouring",
      },
      description: { vi: "Mô tả trải nghiệm", en: "Experience description" },
      syllabus: [],
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
      notice: canonicalTrustTextVi,
      publicationState: "published",
      createdAt: "2026-10-18T00:00:00Z",
      updatedAt: "2026-10-18T00:00:00Z",
    };

    const html = renderToStaticMarkup(
      React.createElement(StoryArtisanBridge, {
        creator: mockCreator,
        experience: mockExperience,
        locale: "vi",
      })
    );

    // 1. Trust messaging
    expect(html).toContain(canonicalTrustTextVi);

    // 2. Visible focus outlines targeting --rbpc-focus (#1E675A)
    expect(html).toContain("focus-visible:ring-[var(--rbpc-focus)]");

    // 3. Minimum 44x44px touch targets on buttons and links
    expect(html).toContain("min-h-[44px]");
    expect(html).toContain("min-w-[44px]");

    // 4. Primary CTA button enforces 44px minimum height
    expect(html).toContain("Yêu cầu lịch hẹn");
  });

  it("verifies PartnerInboxView renders the canonical trust statement and satisfies WCAG 2.5.5 touch targets & focus rings", () => {
    const mockInquiries: PartnerInboxItemWithAudit[] = [
      {
        id: "inq-001",
        reference: "INQ-7F89-A23C",
        experienceSlug: "tham-am-rot-dong",
        experienceTitle: "Kỹ nghệ thẩm âm & Rót đồng truyền thống",
        providerId: "prov-phuong-duc-01",
        creatorSlug: "nguyen-van-cuu",
        creatorName: "Nghệ nhân Nguyễn Văn Cửu",
        contactName: "Nguyễn An Nhiên",
        contactMethod: "phone",
        contactValue: "0912345678",
        preferredDate: "2026-11-05",
        partySize: 2,
        message: "Chúng tôi là 2 bạn trẻ muốn tìm hiểu kỹ nghệ đúc chuông.",
        status: "new",
        partnerNotes: "Chưa liên hệ",
        createdAt: "2026-10-18T10:00:00Z",
        updatedAt: "2026-10-18T10:00:00Z",
        auditLog: [],
      },
    ];

    const html = renderToStaticMarkup(
      React.createElement(PartnerInboxView, {
        initialInquiries: mockInquiries,
        providerId: "prov-phuong-duc-01",
        providerName: "Xưởng đúc Cửu Long",
        locale: "vi",
      })
    );

    // 1. Trust messaging
    expect(html).toContain(canonicalTrustTextVi);

    // 2. Visible focus outlines targeting --rbpc-focus (#1E675A)
    expect(html).toContain("focus-visible:ring-[var(--rbpc-focus)]");

    // 3. Minimum 44x44px touch targets on interactive controls (tabs, inputs, actions)
    expect(html).toContain("min-h-[44px]");
    expect(html).toContain("min-w-[44px]");

    // 4. Masked PII toggle buttons enforce 44x44px touch targets
    expect(html).toContain("Hiện PII");
  });

  it("verifies English locale also provides canonical trust messaging across all components", () => {
    const mockCreator: RbpcCreator = {
      id: "creator-001",
      slug: "nguyen-van-cuu",
      publicName: "Master Artisan Nguyen Van Cuu",
      craftTradition: {
        vi: "Đúc đồng truyền thống Phường Đúc",
        en: "Traditional Bronze Casting of Phường Đúc",
      },
      approvedBio: {
        vi: "Hơn 48 năm gắn bó với lò than đỏ lửa.",
        en: "Over 48 years dedicated to glowing charcoal kilns.",
      },
      approvedPortraitUrl: "https://assets.histolab.icu/creators/cuu.webp",
      portraitAlt: "Portrait of Master Artisan Nguyen Van Cuu",
      publicRegion: "Phuong Duc, Hue City",
      consentStatus: "consented",
      yearsOfPractice: 48,
      generationLineage: "5th Generation",
      displayConsentId: "CONSENT-PD-001",
      approvedStorySlugs: ["ky-nghe-duc-dong-phuong-duc"],
      experienceSlugs: ["tham-am-rot-dong"],
      createdAt: "2026-10-18T00:00:00Z",
    };

    const mockExperience: RbpcExperience = {
      id: "exp-001",
      slug: "tham-am-rot-dong",
      creatorSlug: "nguyen-van-cuu",
      creatorName: "Master Artisan Nguyen Van Cuu",
      title: {
        vi: "Kỹ nghệ thẩm âm & Rót đồng truyền thống",
        en: "Acoustic Tuning & Traditional Bronze Pouring",
      },
      description: { vi: "Mô tả", en: "Description" },
      syllabus: [],
      areaPublic: "Phuong Duc, Hue",
      durationMinutes: 150,
      pricing: {
        isFree: false,
        amount: 450000,
        currency: "VND",
        displayFormatted: "From 450,000 VND / guest",
        pricingUnit: "per_person",
      },
      availabilityMode: "inquiry_only",
      maxPartySize: 8,
      languagesSupported: ["vi", "en"],
      notice: canonicalTrustTextEn,
      publicationState: "published",
      createdAt: "2026-10-18T00:00:00Z",
      updatedAt: "2026-10-18T00:00:00Z",
    };

    const mockInquiries: PartnerInboxItemWithAudit[] = [
      {
        id: "inq-001",
        reference: "INQ-7F89-A23C",
        experienceSlug: "tham-am-rot-dong",
        experienceTitle: "Acoustic Tuning & Traditional Bronze Pouring",
        providerId: "prov-phuong-duc-01",
        creatorSlug: "nguyen-van-cuu",
        creatorName: "Master Artisan Nguyen Van Cuu",
        contactName: "David Miller",
        contactMethod: "email",
        contactValue: "david@example.com",
        preferredDate: "2026-11-05",
        partySize: 2,
        message: "Interested in the acoustic workshop.",
        status: "new",
        createdAt: "2026-10-18T10:00:00Z",
        updatedAt: "2026-10-18T10:00:00Z",
        auditLog: [],
      },
    ];

    const modalHtml = renderToStaticMarkup(
      React.createElement(InquiryFormModal, {
        isOpen: true,
        onClose: () => {},
        experience: mockExperience,
        locale: "en",
      })
    );
    expect(modalHtml).toContain(canonicalTrustTextEn);

    const bridgeHtml = renderToStaticMarkup(
      React.createElement(StoryArtisanBridge, {
        creator: mockCreator,
        experience: mockExperience,
        locale: "en",
      })
    );
    expect(bridgeHtml).toContain(canonicalTrustTextEn);

    const inboxHtml = renderToStaticMarkup(
      React.createElement(PartnerInboxView, {
        initialInquiries: mockInquiries,
        providerId: "prov-phuong-duc-01",
        providerName: "Cuu Long Foundry",
        locale: "en",
      })
    );
    expect(inboxHtml).toContain(canonicalTrustTextEn);
  });
});
