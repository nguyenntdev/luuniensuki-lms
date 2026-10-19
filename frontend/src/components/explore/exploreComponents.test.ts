import { describe, it, expect, vi } from "vitest";
import * as React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import {
  HeritageMediaTabs,
  ACCURACY_GRADE_LABELS,
  SourceEvidenceRail,
  formatBibliographicCitation,
  EVIDENCE_STATUS_CONFIG,
  LivingBridgeCard,
  resolveLocalizedText,
  StoryChapterViewer,
  StoryBlockRenderer,
  HeritageCard,
  HeritageFilters,
  FILTER_CATEGORY_TABS,
  DEFAULT_HERITAGE_PLACES,
  filterHeritagePlaces,
  removeDiacritics,
  isUnescoComponent,
  type StoryViewerStoryData,
} from "./index";
import type {
  HeritagePlace,
  HeritageCategory,
  HeritageMediaAsset,
  HeritageSourceEvidence,
} from "@/types/heritage";
import type {
  RbpcCreator,
  RbpcExperience,
  RbpcStory,
  StoryChapter,
  StoryBlock,
  RbpcClaimEvidence,
  ArtisanBridgeStoryBlock,
} from "@/types/rbpc";
import ExplorePage from "@/app/explore/page";

// ============================================================================
// 1. HeritageMediaTabs Unit & Contract Tests
// ============================================================================

describe("HeritageMediaTabs Component Contract", () => {
  const mockMedia: HeritageMediaAsset[] = [
    {
      id: "media-3d-001",
      media_type: "sketchfab_embed",
      original_url: "https://sketchfab.com/3d-models/tomb-of-tu-duc",
      title: "Mô hình 3D Lăng Tự Đức",
      creator_name: "matousekfoto",
      creator_url: "https://sketchfab.com/matousekfoto",
      model_uid: "77728a86ad1d4964824b63844d50bfe7",
      license_label: "CC BY 4.0",
      noai: false,
      commercial_use_status: "permitted",
      embed_permission_status: "permitted",
      accuracy_grade: "measured_photogrammetry",
      provenance_notes: "Dữ liệu đo vẽ CyArk và HMCC",
      content_status: "cleared_for_this_use",
      content_scope: "RBPC_HUE",
      created_at: "2026-10-18T00:00:00Z",
    },
    {
      id: "media-photo-001",
      media_type: "photo",
      original_url: "https://assets.histolab.icu/heritage/ngo-mon-main.webp",
      title: "Toàn cảnh Ngọ Môn nhìn từ Kỳ Đài",
      creator_name: "Nguyễn Văn Hùng",
      creator_url: "https://commons.wikimedia.org",
      license_label: "CC BY-SA 4.0",
      noai: false,
      commercial_use_status: "permitted",
      embed_permission_status: "permitted",
      accuracy_grade: "historian_reviewed",
      provenance_notes: "Ảnh chụp thực địa tháng 4/2026",
      content_status: "cleared_for_this_use",
      content_scope: "RBPC_HUE",
      created_at: "2026-10-18T00:00:00Z",
    },
    {
      id: "media-doc-001",
      media_type: "document",
      original_url: "https://assets.histolab.icu/archives/chau-ban-tu-duc.pdf",
      title: "Châu bản triều Tự Đức về việc xây Khiêm Lăng",
      creator_name: "Trung tâm Lưu trữ Quốc gia I",
      license_label: "Public Domain",
      noai: true,
      commercial_use_status: "permitted",
      embed_permission_status: "permitted",
      accuracy_grade: "survey_grade",
      provenance_notes: "Mộc bản / Châu bản triều Nguyễn, tập 12",
      content_status: "cleared_for_this_use",
      content_scope: "RBPC_HUE",
      created_at: "2026-10-18T00:00:00Z",
    },
  ];

  it("exports HeritageMediaTabs with correct displayName", () => {
    expect(HeritageMediaTabs).toBeDefined();
    expect(HeritageMediaTabs.displayName).toBe("HeritageMediaTabs");
  });

  it("renders tab navigation with counts for 3D, photos, and archival documents", () => {
    const html = renderToStaticMarkup(
      React.createElement(HeritageMediaTabs, {
        media: mockMedia,
        placeName: "Lăng Tự Đức",
        locale: "vi",
      })
    );

    expect(html).toContain("Mô hình 3D");
    expect(html).toContain("Thư viện ảnh");
    expect(html).toContain("Tư liệu lưu trữ");
    expect(html).toContain('role="tablist"');
    expect(html).toContain('id="tab-3d"');
    expect(html).toContain('id="tab-photos"');
    expect(html).toContain('id="tab-documents"');
  });

  it("prioritizes 3D tab by default when 3D models are available", () => {
    const html = renderToStaticMarkup(
      React.createElement(HeritageMediaTabs, {
        media: mockMedia,
        placeName: "Lăng Tự Đức",
        locale: "vi",
      })
    );

    expect(html).toContain('aria-selected="true"');
    expect(html).toContain("Quang trắc chuẩn hóa (CyArk)");
    expect(html).toContain("matousekfoto");
  });

  it("renders English localization when locale is en", () => {
    const html = renderToStaticMarkup(
      React.createElement(HeritageMediaTabs, {
        media: mockMedia,
        placeName: "Lăng Tự Đức",
        placeNameEn: "Tomb of Tu Duc",
        locale: "en",
      })
    );

    expect(html).toContain("Tomb of Tu Duc");
    expect(html).toContain("3D Exhibit");
    expect(html).toContain("Photo Gallery");
    expect(html).toContain("Archival Documents");
    expect(html).toContain("Measured Photogrammetry");
  });

  it("renders empty state gracefully when tab has zero media assets", () => {
    const emptyMedia: HeritageMediaAsset[] = [];
    const html = renderToStaticMarkup(
      React.createElement(HeritageMediaTabs, {
        media: emptyMedia,
        placeName: "Di tích mới",
        locale: "vi",
      })
    );

    expect(html).toContain("Chưa có hình ảnh tư liệu");
  });

  it("renders photo gallery items when photos tab is pre-selected", () => {
    const html = renderToStaticMarkup(
      React.createElement(HeritageMediaTabs, {
        media: mockMedia,
        placeName: "Ngọ Môn",
        defaultTab: "photos",
        locale: "vi",
      })
    );

    expect(html).toContain("Toàn cảnh Ngọ Môn nhìn từ Kỳ Đài");
    expect(html).toContain("Nguyễn Văn Hùng");
    expect(html).toContain("CC BY-SA 4.0");
  });

  it("renders archival documents when documents tab is pre-selected", () => {
    const html = renderToStaticMarkup(
      React.createElement(HeritageMediaTabs, {
        media: mockMedia,
        placeName: "Khiêm Lăng",
        defaultTab: "documents",
        locale: "vi",
      })
    );

    expect(html).toContain("Châu bản triều Tự Đức về việc xây Khiêm Lăng");
    expect(html).toContain("Trung tâm Lưu trữ Quốc gia I");
    expect(html).toContain("Xem văn bản gốc");
  });
});

// ============================================================================
// 2. SourceEvidenceRail Unit & Contract Tests
// ============================================================================

describe("SourceEvidenceRail Component Contract", () => {
  const mockSources: HeritageSourceEvidence[] = [
    {
      id: "src-001",
      place_id: "place-ngo-mon",
      source_title: "Đại Nam Nhất Thống Chí",
      source_author: "Quốc sử quán triều Nguyễn",
      publisher: "NXB Thuận Hóa",
      publication_year: 1882,
      cited_section: "Tập Kinh sư",
      cited_page: "Tr. 42-45",
      statement: "Ngọ Môn dựng năm Minh Mạng thứ 14 (1833), là cổng chính phía Nam của Hoàng thành.",
      evidence_status: "verified",
      reuse_rights: "public_domain",
      content_scope: "RBPC_HUE",
    },
    {
      id: "src-002",
      place_id: "place-ngo-mon",
      source_title: "Hồ sơ đề cử Di sản Thế giới 678",
      source_author: "Trung tâm Bảo tồn Di tích Cố đô Huế",
      publisher: "UNESCO World Heritage Centre",
      publication_year: 1993,
      cited_page: "p. 18",
      statement: "Quần thể di tích Cố đô Huế được công nhận là Di sản Văn hóa Thế giới ngày 11/12/1993.",
      evidence_status: "verified",
      reuse_rights: "educational_fair_use",
      content_scope: "RBPC_HUE",
    },
    {
      id: "src-003",
      place_id: "place-ngo-mon",
      source_title: "Khảo sát niên đại gỗ Lầu Ngũ Phụng",
      source_author: "Viện Bảo tồn Di tích",
      publication_year: 2021,
      cited_page: "Tr. 88",
      statement: "Một số cấu kiện gỗ lim tại tầng 2 có niên đại thay thế vào đợt trùng tu năm 1923.",
      interpretation_note: "Cần thẩm định thêm mẫu vân gỗ độc lập.",
      evidence_status: "needs_review",
      reuse_rights: "restricted",
      content_scope: "RBPC_HUE",
    },
  ];

  it("exports SourceEvidenceRail with correct displayName", () => {
    expect(SourceEvidenceRail).toBeDefined();
    expect(SourceEvidenceRail.displayName).toBe("SourceEvidenceRail");
  });

  it("formats APA/Chicago style citation accurately with formatBibliographicCitation", () => {
    const citation = formatBibliographicCitation(mockSources[0]);
    expect(citation).toContain("Quốc sử quán triều Nguyễn.");
    expect(citation).toContain("Đại Nam Nhất Thống Chí (1882).");
    expect(citation).toContain("NXB Thuận Hóa.");
    expect(citation).toContain("Tr. 42-45.");
  });

  it("renders verified ratio badge and primary sources count", () => {
    const html = renderToStaticMarkup(
      React.createElement(SourceEvidenceRail, {
        sources: mockSources,
        placeName: "Ngọ Môn Huế",
        locale: "vi",
      })
    );

    expect(html).toContain("2/3 đã đối chiếu");
    expect(html).toContain("Đại Nam Nhất Thống Chí");
    expect(html).toContain("Tr. 42-45");
    expect(html).toContain("Đã đối chiếu thư tịch");
    expect(html).toContain("Chờ kiểm chứng");
  });

  it("supports sidebar layout mode with sticky styling", () => {
    const html = renderToStaticMarkup(
      React.createElement(SourceEvidenceRail, {
        sources: mockSources,
        placeName: "Ngọ Môn Huế",
        layout: "sidebar",
        locale: "vi",
      })
    );

    expect(html).toContain("sticky top-24");
  });

  it("supports bottom rail layout mode with multi-column grid", () => {
    const html = renderToStaticMarkup(
      React.createElement(SourceEvidenceRail, {
        sources: mockSources,
        placeName: "Ngọ Môn Huế",
        layout: "bottom",
        locale: "vi",
      })
    );

    expect(html).toContain("grid-cols-1 md:grid-cols-2 lg:grid-cols-3");
  });

  it("renders drawer trigger when onOpenCitationDrawer callback is provided", () => {
    const dummyDrawerHandler = () => {};
    const html = renderToStaticMarkup(
      React.createElement(SourceEvidenceRail, {
        sources: mockSources,
        placeName: "Ngọ Môn Huế",
        onOpenCitationDrawer: dummyDrawerHandler,
        locale: "vi",
      })
    );

    expect(html).toContain("Mở toàn bộ mục lục trích dẫn");
  });

  it("renders empty state when sources array is empty", () => {
    const html = renderToStaticMarkup(
      React.createElement(SourceEvidenceRail, {
        sources: [],
        placeName: "Di tích chưa ghi nhận",
        locale: "vi",
      })
    );

    expect(html).toContain("Không có thư tịch phù hợp bộ lọc");
  });
});

// ============================================================================
// 3. Shared Mock Data for LivingBridgeCard & StoryChapterViewer
// ============================================================================

const mockArtisan: RbpcCreator = {
  id: "creator-001",
  slug: "nguyen-van-cuu",
  publicName: "Nghệ nhân Nguyễn Văn Cửu",
  craftTradition: {
    vi: "Đúc đồng truyền thống Phường Đúc",
    en: "Traditional Bronze Casting of Phường Đúc",
  },
  approvedBio: {
    vi: "48 năm gắn bó với lò than đỏ lửa, kế thừa kỹ nghệ rót đồng Cung đình triều Nguyễn.",
    en: "Over 48 years of dedicated practice carrying forward royal casting arts.",
  },
  approvedPortraitUrl: "https://assets.histolab.icu/creators/cuu.webp",
  portraitAlt: "Chân dung nghệ nhân Nguyễn Văn Cửu",
  publicRegion: "Phường Đúc, TP. Huế",
  consentStatus: "verified_written_consent",
  yearsOfPractice: 48,
  generationLineage: "Kế thừa đời thứ 5",
  approvedStorySlugs: ["duc-dong-phuong-duc"],
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
    en: "Acoustic Tuning & Bronze Pouring Workshop",
  },
  description: {
    vi: "Trải nghiệm nhào đất khuôn và nghe thanh âm phôi đồng chín.",
    en: "Hands-on mold making and molten bronze acoustic tuning.",
  },
  syllabus: [],
  areaPublic: "Phường Đúc, TP. Huế",
  durationMinutes: 120,
  pricing: {
    isFree: false,
    amount: 450000,
    currency: "VND",
    displayFormatted: "450.000 VNĐ / khách",
    pricingUnit: "per_person",
  },
  availabilityMode: "inquiry_only",
  maxPartySize: 8,
  languagesSupported: ["vi", "en"],
  notice: "Yêu cầu trải nghiệm chỉ là bước liên hệ xác nhận, không phải giao dịch thanh toán tức thì.",
  publicationState: "published",
  createdAt: "2026-10-18T00:00:00Z",
  updatedAt: "2026-10-18T00:00:00Z",
};

describe("LivingBridgeCard Component Contract", () => {

  it("exports LivingBridgeCard with correct displayName", () => {
    expect(LivingBridgeCard).toBeDefined();
    expect(LivingBridgeCard.displayName).toBe("LivingBridgeCard");
  });

  it("resolves LocalizedField correctly via resolveLocalizedText helper", () => {
    expect(resolveLocalizedText("Chuỗi thường", "vi")).toBe("Chuỗi thường");
    expect(resolveLocalizedText({ vi: "Tiếng Việt", en: "English" }, "vi")).toBe("Tiếng Việt");
    expect(resolveLocalizedText({ vi: "Tiếng Việt", en: "English" }, "en")).toBe("English");
    expect(resolveLocalizedText(undefined, "vi", "Mặc định")).toBe("Mặc định");
  });

  it("renders dual anchor connecting monument to living artisan counterpart", () => {
    const html = renderToStaticMarkup(
      React.createElement(LivingBridgeCard, {
        monumentName: "Thế Miếu & Cửu Đỉnh",
        monumentPeriod: "Triều Minh Mạng (1835-1837)",
        artisan: mockArtisan,
        bridgeNarrative: {
          vi: "Từ thế kỷ XIX, các nghệ nhân tiền nhân phường Đúc đã được triệu vào kinh đô đúc Cửu Đỉnh. Kỹ nghệ rót đồng vẫn được gìn giữ qua 5 thế hệ.",
          en: "Since the 19th century, foundry masters were summoned to cast the Nine Dynastic Urns. The casting craft lives on unbroken.",
        },
        experience: mockExperience,
        locale: "vi",
      })
    );

    expect(html).toContain("Thế Miếu &amp; Cửu Đỉnh");
    expect(html).toContain("Triều Minh Mạng (1835-1837)");
    expect(html).toContain("Nghệ nhân Nguyễn Văn Cửu");
    expect(html).toContain("Đúc đồng truyền thống Phường Đúc");
    expect(html).toContain("Kế thừa đời thứ 5");
    expect(html).toContain("48 năm tuổi nghề");
    expect(html).toContain("Đã xác thực chấp thuận");
    expect(html).toContain("Kỹ nghệ thẩm âm &amp; Rót đồng truyền thống");
    expect(html).toContain("450.000 VNĐ / khách");
    expect(html).toContain("Yêu cầu trải nghiệm");
  });

  it("renders English localization when locale is en", () => {
    const html = renderToStaticMarkup(
      React.createElement(LivingBridgeCard, {
        monumentName: "Thế Miếu & Cửu Đỉnh",
        monumentNameEn: "The Mieu & Nine Dynastic Urns",
        artisan: mockArtisan,
        bridgeNarrative: {
          vi: "Kỹ nghệ lưu truyền qua 5 thế hệ.",
          en: "Craft passed down across 5 generations.",
        },
        experience: mockExperience,
        locale: "en",
      })
    );

    expect(html).toContain("The Mieu &amp; Nine Dynastic Urns");
    expect(html).toContain("Living Heritage Bridge");
    expect(html).toContain("Traditional Bronze Casting of Phường Đúc");
    expect(html).toContain("Craft passed down across 5 generations.");
    expect(html).toContain("Verified Written Consent");
    expect(html).toContain("Inquire Experience");
  });

  it("activates fail-closed safeguard when consentStatus is revoked", () => {
    const revokedArtisan: RbpcCreator = {
      ...mockArtisan,
      consentStatus: "revoked",
    };

    const html = renderToStaticMarkup(
      React.createElement(LivingBridgeCard, {
        monumentName: "Thế Miếu",
        artisan: revokedArtisan,
        bridgeNarrative: "Cầu nối lịch sử.",
        locale: "vi",
      })
    );

    // Suppresses PII and renders dignified privacy notice
    expect(html).not.toContain("Nghệ nhân Nguyễn Văn Cửu");
    expect(html).not.toContain("https://assets.histolab.icu/creators/cuu.webp");
    expect(html).toContain("Cầu nối nghệ nhân tạm thời không khả dụng");
    expect(html).toContain("quy chế chấp thuận và quyền riêng tư");
  });

  it("ensures action triggers support opening the workshop inquiry modal", () => {
    // 1. Initial state: Action triggers are rendered with correct testids and accessible labels
    const closedHtml = renderToStaticMarkup(
      React.createElement(LivingBridgeCard, {
        monumentName: "Thế Miếu & Cửu Đỉnh",
        artisan: mockArtisan,
        bridgeNarrative: "Mạch nguồn kỹ nghệ đúc đồng tiếp nối.",
        experience: mockExperience,
        locale: "vi",
        enableInquiryModal: true,
        initialInquiryModalOpen: false,
      })
    );

    // Experience inquiry trigger button
    expect(closedHtml).toContain('data-testid="living-bridge-inquire-btn"');
    expect(closedHtml).toContain('aria-label="Yêu cầu trải nghiệm"');

    // Footer direct workshop inquiry trigger
    expect(closedHtml).toContain('data-testid="living-bridge-inquire-modal-trigger"');
    expect(closedHtml).toContain('aria-label="Mở phiếu yêu cầu trải nghiệm xưởng nghề"');
    expect(closedHtml).toContain("Yêu cầu lịch hẹn xưởng nghề");

    // Modal is not open initially
    expect(closedHtml).not.toContain('role="dialog"');

    // 2. Opened state: When modal is triggered open, InquiryFormModal is rendered
    const openedHtml = renderToStaticMarkup(
      React.createElement(LivingBridgeCard, {
        monumentName: "Thế Miếu & Cửu Đỉnh",
        artisan: mockArtisan,
        bridgeNarrative: "Mạch nguồn kỹ nghệ đúc đồng tiếp nối.",
        experience: mockExperience,
        locale: "vi",
        enableInquiryModal: true,
        initialInquiryModalOpen: true,
      })
    );

    expect(openedHtml).toContain('role="dialog"');
    expect(openedHtml).toContain("Yêu cầu lịch hẹn xưởng nghề");
    expect(openedHtml).toContain("Kỹ nghệ thẩm âm &amp; Rót đồng truyền thống");
    expect(openedHtml).toContain("Nghệ nhân Nguyễn Văn Cửu");
  });

  it("synthesizes workshop experience and opens inquiry modal when experience prop is omitted", () => {
    // When experience prop is omitted, LivingBridgeCard synthesizes a fallback workshop experience for the artisan
    const html = renderToStaticMarkup(
      React.createElement(LivingBridgeCard, {
        monumentName: "Kinh thành Huế",
        artisan: mockArtisan,
        bridgeNarrative: "Kỹ nghệ đúc đồng lưu truyền.",
        locale: "vi",
        enableInquiryModal: true,
        initialInquiryModalOpen: true,
      })
    );

    expect(html).toContain('role="dialog"');
    expect(html).toContain("Nghệ nhân Nguyễn Văn Cửu");
    expect(html).toContain("Trải nghiệm xưởng nghề Nghệ nhân Nguyễn Văn Cửu");
  });

  it("suppresses inquiry modal when enableInquiryModal is false", () => {
    const html = renderToStaticMarkup(
      React.createElement(LivingBridgeCard, {
        monumentName: "Thế Miếu",
        artisan: mockArtisan,
        bridgeNarrative: "Kỹ nghệ truyền đời.",
        experience: mockExperience,
        locale: "vi",
        enableInquiryModal: false,
        initialInquiryModalOpen: true,
      })
    );

    expect(html).not.toContain('role="dialog"');
    expect(html).not.toContain('data-testid="living-bridge-inquire-modal-trigger"');
  });
});

// ============================================================================
// 4. StoryChapterViewer Unit & Contract Tests
// ============================================================================

describe("StoryChapterViewer Component Contract", () => {
  const mockStory: RbpcStory = {
    id: "story-001",
    slug: "ky-nghe-duc-dong-phuong-duc",
    title: {
      vi: "Tiếng đồng ngân qua năm thế hệ Phường Đúc",
      en: "Echoes of Bronze: Five Generations in Phường Đúc",
    },
    intro: {
      vi: "Hành trình tìm lại lửa than thời Cửu Đỉnh qua ký ức nghệ nhân.",
      en: "Rediscovering imperial charcoal kilns through living artisan memories.",
    },
    approvedSummary: {
      vi: "Câu chuyện lịch sử về làng nghề đúc đồng và sự tiếp nối ngày nay.",
      en: "Historical narrative on Hue bronze casting continuity.",
    },
    readingTimeMinutes: 12,
    contentScope: "RBPC_HUE",
    status: "approved",
    version: 1,
    createdAt: "2026-10-18T00:00:00Z",
    updatedAt: "2026-10-18T00:00:00Z",
    evidenceClaims: [
      {
        id: "claim-001",
        statement: "Vua Minh Mạng ban chỉ dụ đúc Cửu Đỉnh vào tháng 10 năm Ất Mùi (1835).",
        locale: "vi",
        claimCategory: "historical_fact",
        sourceTitle: "Đại Nam Thực Lục Chính Biên",
        locator: "Đệ nhị kỷ, quyển 162",
        supportType: "direct",
        reviewStatus: "verified",
        citationLabel: "1",
      },
    ],
    chapters: [
      {
        id: "chap-01",
        chapterNumber: 1,
        slug: "chieu-chi-minh-mang",
        title: {
          vi: "Chiếu chỉ đúc Cửu Đỉnh thời Minh Mạng",
          en: "Minh Mang's Imperial Decree on the Nine Urns",
        },
        summary: {
          vi: "Bối cảnh lịch sử mùa đông năm 1835 khi thợ đúc quy tụ về bờ Nam sông Hương.",
          en: "Winter 1835 historical setting as master founders gathered on the southern bank.",
        },
        readingTimeMinutes: 4,
        blocks: [
          {
            id: "blk-01",
            type: "text",
            title: "Mùa than rực đỏ",
            body: "Tháng mười năm Ất Mùi, triều đình hạ lệnh đúc chín đỉnh đồng lớn tượng trưng cho giang sơn xã tắc [1]. Thợ giỏi khắp bốn phương hội tụ tại bờ sông Hương.",
          },
          {
            id: "blk-02",
            type: "quote",
            quote: "Đỉnh đồng không chỉ là vật chứa mà là linh hồn xã tắc, gõ vào phải ngân như chuông chùa sớm mai.",
            speaker: "Nghệ nhân Nguyễn Văn Cửu",
            roleOrLineage: "Đời thứ 5 Phường Đúc",
            sourceCitation: "Ghi chép truyền khẩu 2026",
          },
          {
            id: "blk-03",
            type: "callout",
            tone: "epistemic",
            title: "Kiểm chứng sử liệu",
            body: "Chi tiết về tỉ lệ hợp kim đồng và kẽm được ghi chép đồng nhất trong cả Khâm Định Đại Nam Hội Điển Sự Lệ.",
          },
          {
            id: "blk-04",
            type: "source_excerpt",
            sourceTitle: "Đại Nam Thực Lục Chính Biên",
            originalText: "Đúc chín đỉnh đồng để ở trước sân Thế Miếu. Đỉnh lớn nặng hơn bốn nghìn cân.",
            modernTranslation: "Đúc 9 vạc đỉnh bằng đồng đặt tại sân Thế Miếu. Đỉnh lớn nhất nặng trên 2,6 tấn.",
            locator: "Quyển 162, tr. 14",
            certainty: "high",
          },
        ],
      },
      {
        id: "chap-02",
        chapterNumber: 2,
        slug: "giu-lua-ngay-nay",
        title: {
          vi: "Giữ lửa lò than giữa lòng thành phố",
          en: "Keeping the Kiln Fire Burning Today",
        },
        readingTimeMinutes: 5,
        blocks: [
          {
            id: "blk-05",
            type: "text",
            body: "Trải qua chiến tranh và biến thiên thời cuộc, tiếng búa gõ phôi đồng vẫn vang lên mỗi sớm mai bên bờ sông Hương.",
          },
        ],
      },
    ],
  };

  it("exports StoryChapterViewer with correct displayName", () => {
    expect(StoryChapterViewer).toBeDefined();
    expect(StoryChapterViewer.displayName).toBe("StoryChapterViewer");
  });

  it("renders story reading progress bar and active chapter header", () => {
    const html = renderToStaticMarkup(
      React.createElement(StoryChapterViewer, {
        story: mockStory,
        initialChapterIndex: 0,
        locale: "vi",
      })
    );

    expect(html).toContain('role="progressbar"');
    expect(html).toContain("Tiếng đồng ngân qua năm thế hệ Phường Đúc");
    expect(html).toContain("Chương 01");
    expect(html).toContain("Chiếu chỉ đúc Cửu Đỉnh thời Minh Mạng");
    expect(html).toContain("4 phút đọc");
  });

  it("renders polymorphic blocks: text with citation button, quote callout, epistemic callout, source excerpt", () => {
    const html = renderToStaticMarkup(
      React.createElement(StoryChapterViewer, {
        story: mockStory,
        initialChapterIndex: 0,
        locale: "vi",
      })
    );

    // Text block with inline citation
    expect(html).toContain("Mùa than rực đỏ");
    expect(html).toContain("[1]");
    expect(html).toContain('aria-label="Trích dẫn [1]"');

    // Quote callout
    expect(html).toContain("Đỉnh đồng không chỉ là vật chứa mà là linh hồn xã tắc");
    expect(html).toContain("Nghệ nhân Nguyễn Văn Cửu");
    expect(html).toContain("Đời thứ 5 Phường Đúc");

    // Callout
    expect(html).toContain("Kiểm chứng sử liệu");
    expect(html).toContain("Khâm Định Đại Nam Hội Điển Sự Lệ");

    // Source excerpt
    expect(html).toContain("Đại Nam Thực Lục Chính Biên");
    expect(html).toContain("Đúc chín đỉnh đồng để ở trước sân Thế Miếu");
    expect(html).toContain("Độ tin cậy cao (Đa nguồn chính sử)");
  });

  it("renders chapter navigation with Next button on first chapter", () => {
    const html = renderToStaticMarkup(
      React.createElement(StoryChapterViewer, {
        story: mockStory,
        initialChapterIndex: 0,
        locale: "vi",
      })
    );

    expect(html).toContain("Chương tiếp theo:");
    expect(html).toContain("Giữ lửa lò than giữa lòng thành phố");
  });

  it("renders completion notice on the last chapter", () => {
    const html = renderToStaticMarkup(
      React.createElement(StoryChapterViewer, {
        story: mockStory,
        initialChapterIndex: 1,
        locale: "vi",
      })
    );

    expect(html).toContain("Bạn đã hoàn thành câu chuyện!");
    expect(html).toContain("Chương trước:");
  });

  it("handles flat blocks fallback gracefully when story has no chapters array", () => {
    const flatStory: StoryViewerStoryData = {
      id: "flat-01",
      slug: "chuyen-ngan",
      title: "Chuyện ngắn về cổng Ngọ Môn",
      readingTimeMinutes: 3,
      blocks: [
        {
          id: "fb-1",
          type: "text",
          body: "Ngọ Môn là biểu tượng kiến trúc đỉnh cao của triều Nguyễn.",
        },
      ],
    };

    const html = renderToStaticMarkup(
      React.createElement(StoryChapterViewer, {
        story: flatStory,
        locale: "vi",
      })
    );

    expect(html).toContain("Chuyện ngắn về cổng Ngọ Môn");
    expect(html).toContain("Ngọ Môn là biểu tượng kiến trúc đỉnh cao của triều Nguyễn.");
  });

  it("renders StoryBlockRenderer reflection_prompt, comparison, and audio_recording blocks", () => {
    const reflectionBlock: StoryBlock = {
      id: "rf-1",
      type: "reflection_prompt",
      question: "Theo bạn, vì sao người xưa chọn hình tượng núi sông khắc lên Cửu Đỉnh?",
      helperText: "Hãy liên hệ đến cương vực và chủ quyền lãnh thổ.",
    };

    const comparisonBlock: StoryBlock = {
      id: "cmp-1",
      type: "comparison",
      historical: {
        title: "Kỹ nghệ đúc Cửu Đỉnh 1835",
        description: "Hàng trăm thợ đúc chia ca rót đồng liên tục trong 3 ngày đêm.",
      },
      contemporary: {
        title: "Kỹ nghệ Phường Đúc 2026",
        description: "Áp dụng công nghệ đo nhiệt độ quang phổ kết hợp kỹ nghệ thẩm âm gia truyền.",
      },
      synthesisNote: "Kỹ nghệ giữ lửa thủ công kết hợp chuẩn hóa khoa học hiện đại.",
    };

    const audioBlock: StoryBlock = {
      id: "aud-1",
      type: "audio_recording",
      title: "Ký ức tiếng chuông đồng",
      audioUrl: "https://assets.histolab.icu/audio/tieng-chuong.mp3",
      durationSeconds: 180,
      speakerName: "Nghệ nhân Nguyễn Văn Cửu",
      transcript: "Tiếng chuông ngân dài hay ngắn là do đất khuôn ủ đủ nắng hay chưa.",
    };

    const rfHtml = renderToStaticMarkup(
      React.createElement(StoryBlockRenderer, { block: reflectionBlock, locale: "vi" })
    );
    expect(rfHtml).toContain("Gợi mở Suy ngẫm");
    expect(rfHtml).toContain("Theo bạn, vì sao người xưa chọn hình tượng núi sông");

    const cmpHtml = renderToStaticMarkup(
      React.createElement(StoryBlockRenderer, { block: comparisonBlock, locale: "vi" })
    );
    expect(cmpHtml).toContain("Đối sánh Lịch sử &amp; Hiện tại");
    expect(cmpHtml).toContain("Kỹ nghệ đúc Cửu Đỉnh 1835");
    expect(cmpHtml).toContain("Kỹ nghệ Phường Đúc 2026");

    const audHtml = renderToStaticMarkup(
      React.createElement(StoryBlockRenderer, { block: audioBlock, locale: "vi" })
    );
    expect(audHtml).toContain("Ký ức tiếng chuông đồng");
    expect(audHtml).toContain("Tiếng chuông ngân dài hay ngắn là do đất khuôn");
  });

  it("integrates StoryArtisanBridge at the end of story chapters when artisan is attached", () => {
    const storyWithArtisan: RbpcStory = {
      ...mockStory,
      creator: mockArtisan,
      experience: mockExperience,
    };

    const html = renderToStaticMarkup(
      React.createElement(StoryChapterViewer, {
        story: storyWithArtisan,
        initialChapterIndex: 0,
        locale: "vi",
      })
    );

    expect(html).toContain('data-testid="story-chapter-artisan-bridge"');
    expect(html).toContain("Cầu nối di sản sống • Từ trang sử đến bàn tay người thợ");
    expect(html).toContain("Nghệ nhân Nguyễn Văn Cửu");
    expect(html).toContain("Đúc đồng truyền thống Phường Đúc");
    expect(html).toContain("Kỹ nghệ thẩm âm &amp; Rót đồng truyền thống");
    expect(html).toContain("Yêu cầu lịch hẹn");
  });

  it("renders StoryArtisanBridge in English at the end of story chapters", () => {
    const storyWithArtisan: RbpcStory = {
      ...mockStory,
      creator: mockArtisan,
      experience: mockExperience,
    };

    const html = renderToStaticMarkup(
      React.createElement(StoryChapterViewer, {
        story: storyWithArtisan,
        initialChapterIndex: 0,
        locale: "en",
      })
    );

    expect(html).toContain('data-testid="story-chapter-artisan-bridge"');
    expect(html).toContain("Living Heritage Bridge • From Imperial Archive to Living Hands");
    expect(html).toContain("Traditional Bronze Casting of Phường Đúc");
    expect(html).toContain("Acoustic Tuning &amp; Bronze Pouring Workshop");
    expect(html).toContain("Request availability");
  });

  it("renders StoryArtisanBridge for polymorphic artisan_bridge block in StoryBlockRenderer", () => {
    const artisanBridgeBlock: ArtisanBridgeStoryBlock = {
      id: "blk-bridge-01",
      type: "artisan_bridge",
      creatorSlug: "nguyen-van-cuu",
      creatorName: "Nghệ nhân Nguyễn Văn Cửu",
      craftTradition: {
        vi: "Đúc đồng truyền thống Phường Đúc",
        en: "Traditional Bronze Casting",
      },
      portraitUrl: "https://assets.histolab.icu/creators/cuu.webp",
      bridgeNarrative: {
        vi: "Kế thừa kỹ nghệ rót đồng cung đình thời Nguyễn.",
        en: "Inheriting royal bronze casting craft.",
      },
      consentStatus: "consented",
      experienceSlug: "tham-am-rot-dong",
      experienceTitle: {
        vi: "Kỹ nghệ thẩm âm & Rót đồng truyền thống",
        en: "Acoustic Tuning & Bronze Pouring",
      },
      experiencePriceDisplay: "Từ 450.000 VNĐ / khách",
    };

    const html = renderToStaticMarkup(
      React.createElement(StoryBlockRenderer, {
        block: artisanBridgeBlock,
        locale: "vi",
      })
    );

    expect(html).toContain("Cầu nối di sản sống • Từ trang sử đến bàn tay người thợ");
    expect(html).toContain("Nghệ nhân Nguyễn Văn Cửu");
    expect(html).toContain("Đúc đồng truyền thống Phường Đúc");
    expect(html).toContain("Yêu cầu lịch hẹn");
  });

  it("respects showArtisanBridge prop to explicitly toggle bridge visibility at chapter end", () => {
    const storyWithArtisan: RbpcStory = {
      ...mockStory,
      creator: mockArtisan,
      experience: mockExperience,
    };

    // When showArtisanBridge is false, bridge is suppressed
    const hiddenHtml = renderToStaticMarkup(
      React.createElement(StoryChapterViewer, {
        story: storyWithArtisan,
        showArtisanBridge: false,
        locale: "vi",
      })
    );
    expect(hiddenHtml).not.toContain('data-testid="story-chapter-artisan-bridge"');

    // When showArtisanBridge is true, bridge is explicitly displayed
    const shownHtml = renderToStaticMarkup(
      React.createElement(StoryChapterViewer, {
        story: storyWithArtisan,
        showArtisanBridge: true,
        locale: "vi",
      })
    );
    expect(shownHtml).toContain('data-testid="story-chapter-artisan-bridge"');
  });

  it("activates fail-closed privacy safeguard in StoryArtisanBridge at chapter end when artisan consent is revoked", () => {
    const storyWithRevokedArtisan: RbpcStory = {
      ...mockStory,
      creator: {
        ...mockArtisan,
        consentStatus: "revoked",
      },
    };

    const html = renderToStaticMarkup(
      React.createElement(StoryChapterViewer, {
        story: storyWithRevokedArtisan,
        locale: "vi",
      })
    );

    // Suppresses PII and portrait
    expect(html).not.toContain("https://assets.histolab.icu/creators/cuu.webp");
    expect(html).toContain("Cầu nối nghệ nhân tạm thời không khả dụng");
    expect(html).toContain("thông tin cá nhân");
  });
});

// ============================================================================
// 5. Explore Catalogue Interactions: Search, Filters & Aspect Ratio
// ============================================================================

describe("Explore Catalogue Interactions: Diacritic-Tolerant Search & Facet Filters", () => {
  it("normalizes Vietnamese strings and removes diacritics with removeDiacritics helper", () => {
    expect(removeDiacritics("Ngọ Môn")).toBe("ngo mon");
    expect(removeDiacritics("Lăng Tự Đức")).toBe("lang tu duc");
    expect(removeDiacritics("Phường Đúc")).toBe("phuong duc");
    expect(removeDiacritics("Đại Nội")).toBe("dai noi");
    expect(removeDiacritics("Khải Định")).toBe("khai dinh");
    expect(removeDiacritics("Điện Thái Hòa")).toBe("dien thai hoa");
    expect(removeDiacritics("Thanh Tiên")).toBe("thanh tien");
    expect(removeDiacritics("Nhã nhạc Cung đình")).toBe("nha nhac cung dinh");
    expect(removeDiacritics("Hải Vân Quan")).toBe("hai van quan");
  });

  it("identifies official UNESCO 678 property components accurately", () => {
    const tuDuc = DEFAULT_HERITAGE_PLACES.find((p) => p.slug === "lang-tu-duc");
    const ngoMon = DEFAULT_HERITAGE_PLACES.find((p) => p.slug === "ngo-mon");
    const craft = DEFAULT_HERITAGE_PLACES.find((p) => p.slug === "duc-dong-phuong-duc");

    expect(tuDuc).toBeDefined();
    expect(isUnescoComponent(tuDuc!)).toBe(true);

    expect(ngoMon).toBeDefined();
    expect(isUnescoComponent(ngoMon!)).toBe(true);

    expect(craft).toBeDefined();
    expect(isUnescoComponent(craft!)).toBe(false);
  });

  it("filters places with diacritic-tolerant accent-insensitive queries", () => {
    // 1. Search 'tu duc' without accents matches 'Lăng Tự Đức'
    const resultsNoAccent = filterHeritagePlaces(DEFAULT_HERITAGE_PLACES, {
      q: "tu duc",
      category: "all",
    });
    expect(resultsNoAccent.length).toBeGreaterThan(0);
    expect(resultsNoAccent.some((p) => p.slug === "lang-tu-duc")).toBe(true);

    // 2. Search 'Tự Đức' with accents matches 'Lăng Tự Đức'
    const resultsWithAccent = filterHeritagePlaces(DEFAULT_HERITAGE_PLACES, {
      q: "Tự Đức",
      category: "all",
    });
    expect(resultsWithAccent.some((p) => p.slug === "lang-tu-duc")).toBe(true);

    // 3. Search 'ngo mon' matches 'Ngọ Môn'
    const resultsNgoMon = filterHeritagePlaces(DEFAULT_HERITAGE_PLACES, {
      q: "ngo mon",
      category: "all",
    });
    expect(resultsNgoMon.some((p) => p.slug === "ngo-mon")).toBe(true);

    // 4. Search 'phuong duc' matches 'Phường Đúc' bronze craft
    const resultsPhuongDuc = filterHeritagePlaces(DEFAULT_HERITAGE_PLACES, {
      q: "phuong duc",
      category: "all",
    });
    expect(resultsPhuongDuc.some((p) => p.slug === "duc-dong-phuong-duc")).toBe(true);

    // 5. Search '678-007' matches by official UNESCO reference ID
    const resultsRef = filterHeritagePlaces(DEFAULT_HERITAGE_PLACES, {
      q: "678-007",
      category: "all",
    });
    expect(resultsRef.some((p) => p.slug === "lang-tu-duc")).toBe(true);
  });

  it("filters places strictly by category facets", () => {
    // 1. Royal Tombs
    const royalTombs = filterHeritagePlaces(DEFAULT_HERITAGE_PLACES, {
      q: "",
      category: "royal_tomb",
    });
    expect(royalTombs.length).toBeGreaterThan(0);
    expect(royalTombs.every((p) => p.heritage_category === "royal_tomb")).toBe(true);
    expect(royalTombs.some((p) => p.slug === "lang-tu-duc")).toBe(true);
    expect(royalTombs.some((p) => p.slug === "lang-khai-dinh")).toBe(true);

    // 2. Living Crafts
    const crafts = filterHeritagePlaces(DEFAULT_HERITAGE_PLACES, {
      q: "",
      category: "craft_living_culture",
    });
    expect(crafts.length).toBeGreaterThan(0);
    expect(crafts.every((p) => p.heritage_category === "craft_living_culture")).toBe(true);
    expect(crafts.some((p) => p.slug === "duc-dong-phuong-duc")).toBe(true);
    expect(crafts.some((p) => p.slug === "hoa-giay-thanh-tien")).toBe(true);

    // 3. Imperial Architecture
    const monuments = filterHeritagePlaces(DEFAULT_HERITAGE_PLACES, {
      q: "",
      category: "imperial_architecture",
    });
    expect(monuments.length).toBeGreaterThan(0);
    expect(monuments.every((p) => p.heritage_category === "imperial_architecture")).toBe(true);
    expect(monuments.some((p) => p.slug === "kinh-thanh-hue")).toBe(true);
    expect(monuments.some((p) => p.slug === "ngo-mon")).toBe(true);

    // 4. Intangible Traditions / Performing Arts
    const intangible = filterHeritagePlaces(DEFAULT_HERITAGE_PLACES, {
      q: "",
      category: "music_performance",
    });
    expect(intangible.length).toBeGreaterThan(0);
    expect(intangible.some((p) => p.slug === "nha-nhac-cung-dinh-hue")).toBe(true);
  });

  it("filters places strictly by unescoOnly flag", () => {
    const unescoPlaces = filterHeritagePlaces(DEFAULT_HERITAGE_PLACES, {
      q: "",
      category: "all",
      unescoOnly: true,
    });

    expect(unescoPlaces.length).toBeGreaterThan(0);
    expect(unescoPlaces.every((p) => isUnescoComponent(p))).toBe(true);
    expect(unescoPlaces.some((p) => p.slug === "duc-dong-phuong-duc")).toBe(false);
  });

  it("filters places strictly by has3dOnly flag", () => {
    const threeDPlaces = filterHeritagePlaces(DEFAULT_HERITAGE_PLACES, {
      q: "",
      category: "all",
      has3dOnly: true,
    });

    expect(threeDPlaces.length).toBeGreaterThan(0);
    expect(threeDPlaces.every((p) => p.has_3d)).toBe(true);
    expect(threeDPlaces.some((p) => p.slug === "lang-tu-duc")).toBe(true);
    expect(threeDPlaces.some((p) => p.slug === "ngo-mon")).toBe(true);
  });

  it("combines multiple filters conjunctively (category + 3D + search)", () => {
    const combined = filterHeritagePlaces(DEFAULT_HERITAGE_PLACES, {
      q: "Tu Duc",
      category: "royal_tomb",
      has3dOnly: true,
      unescoOnly: true,
    });

    expect(combined.length).toBe(1);
    expect(combined[0].slug).toBe("lang-tu-duc");
  });
});

describe("HeritageCard Aspect Ratio & Fallback Management", () => {
  const mockPlace: HeritagePlace = {
    id: "678-007",
    slug: "lang-tu-duc",
    name_vi: "Lăng Tự Đức (Khiêm Lăng)",
    name_en: "Tomb of Emperor Tu Duc",
    entity_type: "monument",
    heritage_category: "royal_tomb",
    official_reference_id: "678-007",
    official_designation: "UNESCO World Heritage Component",
    period_label: "Thời Tự Đức (1864–1867)",
    visitor_summary_vi: "Quần thể lăng tẩm mang vẻ đẹp thi vị, hòa quyện với thiên nhiên.",
    visitor_summary_en: "Poetic royal tomb complex blending harmoniously with nature.",
    current_access_status: "open",
    editorial_status: "published",
    content_scope: "RBPC_HUE",
    has_3d: true,
    thumbnail_url: null, // Test graceful fallback
    created_at: "2026-10-18T00:00:00Z",
    updated_at: "2026-10-18T00:00:00Z",
  };

  it("renders 16:10 aspect ratio container and graceful architectural fallback when thumbnail is missing", () => {
    const html = renderToStaticMarkup(
      React.createElement(HeritageCard, {
        place: mockPlace,
        locale: "vi",
      })
    );

    // Aspect ratio container (16:10)
    expect(html).toContain("aspect-[16/10]");

    // Fallback category icon and label
    expect(html).toContain("Lăng tẩm Hoàng gia");
    expect(html).toContain("Lăng Tự Đức (Khiêm Lăng)");
    expect(html).toContain("Tomb of Emperor Tu Duc");
    expect(html).toContain("Thời Tự Đức (1864–1867)");
    expect(html).toContain("UNESCO 678-007");
    expect(html).toContain("3D");
    expect(html).toContain("Mở cửa");
    expect(html).toContain("href=\"/heritage/lang-tu-duc\"");
  });

  it("renders thumbnail image tag when thumbnail_url is provided", () => {
    const placeWithImage: HeritagePlace = {
      ...mockPlace,
      thumbnail_url: "https://assets.histolab.icu/heritage/tu-duc.webp",
    };

    const html = renderToStaticMarkup(
      React.createElement(HeritageCard, {
        place: placeWithImage,
        locale: "vi",
      })
    );

    expect(html).toContain("aspect-[16/10]");
    expect(html).toContain("src=\"https://assets.histolab.icu/heritage/tu-duc.webp\"");
    expect(html).toContain("alt=\"Lăng Tự Đức (Khiêm Lăng)\"");
  });
});

describe("HeritageFilters Component Integration", () => {
  it("renders all 5 category tabs, search input, view mode toggle, and chips", () => {
    const dummyOnChange = vi.fn();
    const dummyOnViewModeChange = vi.fn();

    const html = renderToStaticMarkup(
      React.createElement(HeritageFilters, {
        values: {
          q: "Ngọ Môn",
          category: "imperial_architecture",
          unescoOnly: true,
          has3dOnly: true,
          accessStatus: "open",
        },
        onChange: dummyOnChange,
        viewMode: "grid",
        onViewModeChange: dummyOnViewModeChange,
        totalCount: 14,
        locale: "vi",
      })
    );

    // Row 1: Search input and view toggle
    expect(html).toContain("role=\"search\"");
    expect(html).toContain("value=\"Ngọ Môn\"");
    expect(html).toContain("Dạng lưới");
    expect(html).toContain("Bản đồ");

    // Row 2: Category tabs
    expect(html).toContain("Tất cả di sản");
    expect(html).toContain("Kiến trúc Cung đình");
    expect(html).toContain("Lăng tẩm Hoàng gia");
    expect(html).toContain("Làng nghề thủ công");
    expect(html).toContain("Di sản phi vật thể");

    // Row 3: Facet pills & counts
    expect(html).toContain("Chỉ hiện UNESCO (14 Cấu phần)");
    expect(html).toContain("Có mô hình 3D");
    expect(html).toContain("14");
    expect(html).toContain("Xóa bộ lọc");
  });

  it("enforces WCAG 2.5.5 min 44x44px touch targets and visible focus rings across all filter controls", () => {
    const html = renderToStaticMarkup(
      React.createElement(HeritageFilters, {
        values: {
          q: "Phường Đúc",
          category: "craft_living_culture",
          unescoOnly: false,
          has3dOnly: true,
        },
        onChange: vi.fn(),
        viewMode: "grid",
        onViewModeChange: vi.fn(),
        totalCount: 3,
        locale: "vi",
      })
    );

    // Search input and clear button min 44px
    expect(html).toContain("min-h-[44px]");
    expect(html).toContain("min-w-[44px]");

    // Focus rings with #1E675A emerald token
    expect(html).toContain("focus-visible:ring-[var(--rbpc-focus,#1E675A)]");
    expect(html).toContain("focus-visible:ring-offset-2");
  });
});

describe("Phase 5 Responsive & Performance Invariants", () => {
  it("confirms HeritageCard eliminates heavy backdrop-blur to protect mobile GPU frame rates", () => {
    const mockPlace: HeritagePlace = {
      id: "678-001",
      slug: "ngo-mon",
      name_vi: "Ngọ Môn — Đại Nội Huế",
      name_en: "Meridian Gate, Hue Imperial City",
      entity_type: "monument",
      heritage_category: "imperial_architecture",
      official_reference_id: "678-001",
      official_designation: "UNESCO World Heritage Component",
      current_access_status: "open",
      editorial_status: "published",
      content_scope: "RBPC_HUE",
      has_3d: true,
      period_label: "Thời Minh Mạng (1833)",
      created_at: "2026-10-18T00:00:00Z",
      updated_at: "2026-10-18T00:00:00Z",
    };

    const html = renderToStaticMarkup(
      React.createElement(HeritageCard, {
        place: mockPlace,
        locale: "vi",
      })
    );

    // Zero heavy backdrop blur
    expect(html).not.toContain("backdrop-blur-md");
    expect(html).not.toContain("backdrop-blur-sm");
    expect(html).not.toContain("backdrop-blur-lg");
    expect(html).not.toContain("backdrop-blur-xl");

    // Accessible focus rings
    expect(html).toContain("focus-visible:ring-[var(--rbpc-focus,#1E675A)]");
  });

  it("confirms StoryChapterViewer constrains prose reading measure to max-w-[720px] and has zero heavy backdrop-blur", () => {
    const html = renderToStaticMarkup(
      React.createElement(StoryChapterViewer, {
        story: {
          id: "story-readability",
          slug: "readability-test",
          title: "Đoạn văn đọc chuẩn mực",
          blocks: [
            {
              id: "b-read-1",
              type: "text",
              body: "Nội dung khảo cứu di sản lịch sử Cố đô Huế.",
            },
          ],
        },
        locale: "vi",
      })
    );

    // Prose container constrained to 720px
    expect(html).toContain("max-w-[720px]");

    // Zero backdrop blur
    expect(html).not.toContain("backdrop-blur-md");
    expect(html).not.toContain("backdrop-blur-sm");
    expect(html).not.toContain("backdrop-blur-xs");
  });

  it("confirms HeritageMediaTabs enforces min 44x44px touch targets and zero backdrop-blur", () => {
    const html = renderToStaticMarkup(
      React.createElement(HeritageMediaTabs, {
        media: [
          {
            id: "m-1",
            place_id: "p-1",
            media_type: "photo",
            original_url: "https://example.com/test.jpg",
            title: "Khảo sát thực địa",
            license_label: "CC BY 4.0",
            noai: false,
            commercial_use_status: "permitted",
            embed_permission_status: "permitted",
            accuracy_grade: "historian_reviewed",
            content_status: "cleared_for_this_use",
            content_scope: "RBPC_HUE",
            created_at: "2026-10-18T00:00:00Z",
          },
        ],
        locale: "vi",
        defaultTab: "photos",
      })
    );

    // Min 44px touch bounding box on tabs and buttons
    expect(html).toContain("min-h-[44px]");

    // Zero backdrop blur
    expect(html).not.toContain("backdrop-blur-md");
    expect(html).not.toContain("backdrop-blur-sm");
    expect(html).not.toContain("backdrop-blur-xs");
  });

  describe("ExplorePage Component Load & Layout Contract", () => {
    it("exports ExplorePage as a valid React component with Suspense wrapper", () => {
      expect(ExplorePage).toBeDefined();
      expect(typeof ExplorePage).toBe("function");

      const element = React.createElement(ExplorePage);
      expect(element).toBeDefined();
      expect(element.type).toBe(ExplorePage);
    });

    it("renders fallback skeleton shell cleanly in static markup without runtime error", () => {
      // In static markup, Suspense resolves either fallback or wrapped tree
      const element = React.createElement(ExplorePage);
      expect(() => renderToStaticMarkup(element)).not.toThrow();
    });
  });
});



