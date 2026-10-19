/**
 * LƯU NIÊN — RBPC 2026: Centralized Canonical Bilingual Microcopy Dictionary
 * Scope: Pure English product facing & culturally authentic Vietnamese translations.
 * Spec Reference: Master Spec Section 4.5 & V2-A.2
 *
 * Core Mandates:
 * - Localise meaning, not word order.
 * - Preserve Vietnamese diacritics in proper names (Huế, Cửu Đỉnh, Phường Đúc, etc.).
 * - Epistemic honesty: Explicit badges for verified sources, evidence gaps, traditional lore.
 * - Commercial clarity: "Request availability", NEVER "Book now" or false instant confirmation.
 * - Strict type safety across all dictionary trees.
 */

export type RbpcLocale = "vi" | "en";

export interface EpistemicStatusItem {
  id: string;
  label: string;
  description: string;
  badgeClass: string;
}

export interface RbpcCopyDictionary {
  brand: {
    name: string;
    fullName: string;
    strapline: string;
    promise: string;
    productDescriptor: string;
    heroExplanation: string;
    eyebrow: string;
    subheadline: string;
    citationPolicy: string;
    unescoDisclaimer: string;
  };
  nav: {
    discover: string;
    makers: string;
    experiences: string;
    about: string;
    learn: string;
    privacy: string;
    partnerInbox: string;
    impact: string;
    backToStory: string;
    menuToggle: string;
    closeMenu: string;
    languageSwitch: string;
    skipToContent: string;
  };
  cta: {
    exploreStory: string;
    meetMaker: string;
    requestAvailability: string;
    requestExperience: string;
    viewSources: string;
    howItWorks: string;
    askCulturalContext: string;
    quickExplanation: string;
    exploreDeeper: string;
    submitInquiry: string;
    submitting: string;
    viewThirdParty3d: string;
    viewPhotosSources: string;
    readApprovedStory: string;
    backHome: string;
    contactPartner: string;
    copyCitation: string;
    copied: string;
    close: string;
  };
  epistemic: {
    sectionTitle: string;
    sectionSubtitle: string;
    verifiedSource: EpistemicStatusItem;
    traditionalAccount: EpistemicStatusItem;
    academicInterpretation: EpistemicStatusItem;
    evidenceGap: EpistemicStatusItem;
    unescoInscribed: EpistemicStatusItem;
    livingTradition: EpistemicStatusItem;
    humanReviewed: EpistemicStatusItem;
    preExistingResearch: EpistemicStatusItem;
  };
  inquiry: {
    modalTitle: string;
    modalSubtitle: string;
    experienceProvider: string;
    durationLabel: string;
    locationLabel: string;
    feeLabel: string;
    fields: {
      name: {
        label: string;
        placeholder: string;
        error: string;
      };
      email: {
        label: string;
        placeholder: string;
        error: string;
      };
      phone: {
        label: string;
        placeholder: string;
        error: string;
      };
      preferredDate: {
        label: string;
        placeholder: string;
        helper: string;
      };
      partySize: {
        label: string;
        placeholder: string;
        helper: string;
      };
      message: {
        label: string;
        placeholder: string;
        helper: string;
        error: string;
      };
      consent: {
        label: string;
        error: string;
      };
    };
    confirmation: {
      title: string;
      message: string;
      statusBadge: string;
      referencePrefix: string;
      nextStepsTitle: string;
      nextStepsBody: string;
      disclaimer: string;
      backButton: string;
    };
    states: {
      pending: string;
      contacted: string;
      confirmed: string;
      declined: string;
      closed: string;
    };
  };
  consent: {
    bannerTitle: string;
    artisanConsentNotice: string;
    withdrawnNotice: string;
    privacyNoticeTitle: string;
    privacyNoticeBody: string;
    cookieMinimal: string;
    noMarketingPledge: string;
  };
  ai: {
    title: string;
    subtitle: string;
    inputPlaceholder: string;
    buttonAsk: string;
    quickExplainer: string;
    deepExplainer: string;
    guidedPromptsTitle: string;
    guidedPrompts: Array<{
      prompt: string;
      description: string;
    }>;
    citationHeader: string;
    groundedBadge: string;
    comparisonDisclaimer: string;
    limitationWarning: string;
    systemUnavailable: string;
    rateLimited: string;
    noSourcesFound: string;
  };
  media: {
    thirdParty3dTitle: string;
    thirdParty3dNotice: string;
    thirdParty3dUnverified: string;
    thirdParty3dUnavailable: string;
    rightsAttribution: string;
    licenseLabel: string;
    creatorLabel: string;
    externalPlatformLink: string;
    stillPhotoFallbackNotice: string;
  };
  commercial: {
    illustrativeScenario: string;
    sponsorshipDeclaration: string;
    providerInactive: string;
    pilotScopeNotice: string;
    revenueDisclaimer: string;
  };
  errors: {
    notFoundTitle: string;
    notFoundMessage: string;
    generalErrorTitle: string;
    generalErrorMessage: string;
    networkOffline: string;
    validationFailed: string;
    retryAction: string;
  };
}

export const RBPC_COPY: Record<RbpcLocale, RbpcCopyDictionary> = {
  vi: {
    brand: {
      name: "LƯU NIÊN",
      fullName: "LƯU NIÊN — Cầu Nối Di Sản Sống",
      strapline: "Khám phá câu chuyện. Gặp gỡ con người. Giữ gìn mạch nguồn di sản.",
      promise: "Văn hóa không chỉ là những gì ta nhìn thấy.",
      productDescriptor: "Câu chuyện có nguồn. Trải nghiệm cùng con người.",
      heroExplanation:
        "Tìm hiểu câu chuyện đằng sau mỗi địa danh — và gặp những con người đang tiếp nối mạch nguồn văn hóa.",
      eyebrow: "DI SẢN SỐNG, CÂU CHUYỆN CON NGƯỜI",
      subheadline:
        "Một hệ thống khám phá di sản Cố đô Huế kết hợp tư liệu kiểm chứng học thuật và kết nối trải nghiệm cùng nghệ nhân địa phương.",
      citationPolicy:
        "Mọi thông tin lịch sử trên LƯU NIÊN đều được đối chiếu từ thư tịch lưu trữ hoặc công trình khảo cứu có nguồn gốc rõ ràng.",
      unescoDisclaimer:
        "Các công trình thuộc Quần thể Di tích Cố đô Huế được đối chiếu theo danh mục bảo tồn chính thức của UNESCO (Mã số 678).",
    },
    nav: {
      discover: "Khám phá",
      makers: "Gặp người làm nghề",
      experiences: "Trải nghiệm",
      about: "Về chúng tôi",
      learn: "Góc học tập",
      privacy: "Quyền riêng tư",
      partnerInbox: "Hộp thư đối tác",
      impact: "Tác động & Minh chứng",
      backToStory: "Quay lại câu chuyện",
      menuToggle: "Mở menu điều hướng",
      closeMenu: "Đóng menu điều hướng",
      languageSwitch: "English",
      skipToContent: "Chuyển thẳng đến nội dung chính",
    },
    cta: {
      exploreStory: "Khám phá câu chuyện",
      meetMaker: "Gặp người làm nghề",
      requestAvailability: "Yêu cầu lịch hẹn",
      requestExperience: "Gửi yêu cầu trải nghiệm",
      viewSources: "Xem nguồn tư liệu",
      howItWorks: "Cách thức hoạt động",
      askCulturalContext: "Hỏi về bối cảnh văn hóa",
      quickExplanation: "Giải thích ngắn gọn (dưới 120 từ)",
      exploreDeeper: "Tìm hiểu sâu hơn (kèm dẫn chứng)",
      submitInquiry: "Gửi yêu cầu trải nghiệm",
      submitting: "Đang gửi yêu cầu...",
      viewThirdParty3d: "Xem mô hình 3D từ bên thứ ba",
      viewPhotosSources: "Xem ảnh chụp thực tế và nguồn tư liệu",
      readApprovedStory: "Đọc câu chuyện đã được kiểm chứng",
      backHome: "Về trang chủ",
      contactPartner: "Liên hệ đối tác",
      copyCitation: "Sao chép trích dẫn",
      copied: "Đã sao chép vào bộ nhớ tạm",
      close: "Đóng",
    },
    epistemic: {
      sectionTitle: "Mức độ xác thực tư liệu",
      sectionSubtitle:
        "Hệ thống phân biệt rành mạch giữa sự thật lịch sử đã đối chiếu, ký ức văn hóa dân gian và giả thuyết học thuật.",
      verifiedSource: {
        id: "verified_source",
        label: "Đã đối chiếu tư liệu",
        description:
          "Nội dung được đối chiếu trực tiếp từ nguồn thư tịch triều Nguyễn, tài liệu lưu trữ quốc gia hoặc khảo cứu khoa học đã xuất bản.",
        badgeClass: "rbpc-badge-verified",
      },
      traditionalAccount: {
        id: "traditional_account",
        label: "Ghi chép truyền thống",
        description:
          "Lưu truyền trong dân gian hoặc truyền khẩu làng nghề mang giá trị văn hóa sống; không khẳng định như sự kiện vật lý tuyệt đối.",
        badgeClass: "rbpc-badge-tradition",
      },
      academicInterpretation: {
        id: "academic_interpretation",
        label: "Kiểm giải học thuật",
        description:
          "Góc nhìn phân tích, phục dựng hoặc giả thuyết nghiên cứu của các chuyên gia văn hóa - lịch sử.",
        badgeClass: "rbpc-badge-interpretation",
      },
      evidenceGap: {
        id: "evidence_gap",
        label: "Chưa đủ tư liệu khẳng định",
        description:
          "Tư liệu hiện có chưa đủ để xác quyết chi tiết này. Hệ thống chủ động để trống thay vì suy đoán.",
        badgeClass: "rbpc-badge-gap",
      },
      unescoInscribed: {
        id: "unesco_inscribed",
        label: "Di sản Thế giới UNESCO",
        description:
          "Thành phần chính thức thuộc Quần thể Di tích Cố đô Huế (được ghi danh năm 1993, mã số 678).",
        badgeClass: "rbpc-badge-unesco",
      },
      livingTradition: {
        id: "living_tradition",
        label: "Di sản sống & Làng nghề",
        description:
          "Nghệ thuật thủ công hoặc phong tục đang được nghệ nhân thực tế gìn giữ và trao truyền tại địa phương.",
        badgeClass: "rbpc-badge-tradition",
      },
      humanReviewed: {
        id: "human_reviewed",
        label: "Biên tập viên nhân văn đã duyệt",
        description:
          "Nội dung đã qua thẩm định của biên tập viên chuyên môn; không phải dữ liệu AI tạo sinh tự do.",
        badgeClass: "rbpc-badge-verified",
      },
      preExistingResearch: {
        id: "pre_existing_research",
        label: "Tài liệu nghiên cứu có trước cuộc thi",
        description:
          "Tư liệu nền tảng hình thành trong quá trình nghiên cứu khoa học trước đó, minh bạch theo điều lệ cuộc thi.",
        badgeClass: "rbpc-badge-review",
      },
    },
    inquiry: {
      modalTitle: "Gửi yêu cầu lịch hẹn trải nghiệm",
      modalSubtitle:
        "Concept demonstration — Yêu cầu trải nghiệm sẽ được gửi trực tiếp đến nghệ nhân/cơ sở để xác nhận thời gian.",
      experienceProvider: "Người phụ trách trải nghiệm",
      durationLabel: "Thời lượng",
      locationLabel: "Địa điểm xưởng nghề",
      feeLabel: "Đóng góp trải nghiệm dự kiến",
      fields: {
        name: {
          label: "Họ và tên của bạn",
          placeholder: "Ví dụ: Nguyễn Văn An",
          error: "Vui lòng nhập họ và tên của bạn (tối thiểu 2 ký tự).",
        },
        email: {
          label: "Địa chỉ email nhận phản hồi",
          placeholder: "tenban@example.com",
          error: "Vui lòng nhập địa chỉ email hợp lệ.",
        },
        phone: {
          label: "Số điện thoại liên hệ (ưu tiên Zalo/WhatsApp)",
          placeholder: "0901 234 567",
          error: "Vui lòng nhập số điện thoại hợp lệ (8–15 chữ số).",
        },
        preferredDate: {
          label: "Ngày dự kiến (không bắt buộc)",
          placeholder: "Chọn ngày bạn mong muốn tham gia",
          helper: "Thời gian đón tiếp phụ thuộc vào lịch sản xuất thực tế của xưởng nghề.",
        },
        partySize: {
          label: "Số lượng người tham gia",
          placeholder: "Ví dụ: 2 người lớn, 1 trẻ em",
          helper: "Để đảm bảo chất lượng, hầu hết xưởng nghề giới hạn dưới 6 khách mỗi buổi.",
        },
        message: {
          label: "Ghi chú hoặc mong muốn gửi gắm",
          placeholder: "Chia sẻ sở thích của bạn về nghề thủ công, các lưu ý về thời gian hoặc yêu cầu ngôn ngữ...",
          helper: "Tối đa 500 ký tự.",
          error: "Lời nhắn không được vượt quá 500 ký tự.",
        },
        consent: {
          label:
            "Tôi đồng ý chia sẻ thông tin liên hệ này với nghệ nhân/đơn vị phụ trách để tiếp nhận và phản hồi yêu cầu trải nghiệm.",
          error: "Bạn cần xác nhận đồng thuận chia sẻ thông tin liên hệ để tiếp tục.",
        },
      },
      confirmation: {
        title: "Đã tiếp nhận yêu cầu",
        message:
          "Yêu cầu của bạn đã được chuyển đến nghệ nhân/đơn vị phụ trách trải nghiệm. Lưu ý: Lịch hẹn chưa được xác nhận tự động.",
        statusBadge: "Đang chờ xưởng phản hồi",
        referencePrefix: "Mã yêu cầu",
        nextStepsTitle: "Các bước tiếp theo diễn ra như thế nào?",
        nextStepsBody:
          "Người làm nghề hoặc điều phối viên bản địa sẽ liên hệ trực tiếp với bạn qua email hoặc số điện thoại trong vòng 24–48 giờ làm việc để xác nhận lịch trống và hướng dẫn chuẩn bị.",
        disclaimer:
          "Yêu cầu trải nghiệm không phải là một giao dịch thương mại hoàn tất. Lịch đón tiếp phụ thuộc vào điều kiện sức khỏe và nhịp làm việc thực tế của nghệ nhân.",
        backButton: "Quay lại trang câu chuyện",
      },
      states: {
        pending: "Tiếp nhận mới",
        contacted: "Đã liên hệ người gửi",
        confirmed: "Đã xác nhận lịch hẹn",
        declined: "Xưởng bận / Không tiếp nhận",
        closed: "Đã hoàn thành",
      },
    },
    consent: {
      bannerTitle: "Minh bạch và Tôn trọng Quyền riêng tư",
      artisanConsentNotice:
        "Mọi chân dung, lời kể và thông tin xưởng nghề đều được đăng tải sau khi nghệ nhân ký văn bản đồng thuận tham gia.",
      withdrawnNotice:
        "Nghệ nhân có toàn quyền yêu cầu điều chỉnh hoặc tạm ẩn thông tin cá nhân bất kỳ lúc nào.",
      privacyNoticeTitle: "Cam kết bảo vệ dữ liệu người dùng",
      privacyNoticeBody:
        "Thông tin liên hệ bạn cung cấp trong biểu mẫu chỉ được chuyển tiếp đến người phụ trách trải nghiệm tương ứng. Hệ thống tuyệt đối không bán hoặc cung cấp dữ liệu cho bất kỳ bên thứ ba nào vì mục đích quảng cáo.",
      cookieMinimal:
        "Trang web chỉ sử dụng bộ nhớ cục bộ để lưu tuỳ chọn ngôn ngữ và trợ năng; không lưu trữ cookie theo dõi hành vi xuyên trang.",
      noMarketingPledge: "Không gửi thư rác, không quảng cáo tự động.",
    },
    ai: {
      title: "Trợ lý Văn hóa LƯU NIÊN",
      subtitle: "Giải đáp bối cảnh văn hóa dựa trên hệ thống tư liệu đã được đối chiếu",
      inputPlaceholder: "Đặt câu hỏi về câu chuyện văn hóa hoặc nghề thủ công...",
      buttonAsk: "Gửi câu hỏi",
      quickExplainer: "Giải thích ngắn gọn (dưới 120 từ)",
      deepExplainer: "Tìm hiểu chuyên sâu (kèm dẫn chứng)",
      guidedPromptsTitle: "Gợi ý câu hỏi:",
      guidedPrompts: [
        {
          prompt: "Ý nghĩa của hoa văn này trong đời sống đương đại là gì?",
          description: "Tìm hiểu cách biểu tượng văn hóa xưa được ứng dụng hôm nay.",
        },
        {
          prompt: "Quy trình chế tác thủ công truyền thống diễn ra như thế nào?",
          description: "Khám phá các bước nhào đất, đúc đồng, pha chế men màu...",
        },
        {
          prompt: "Điểm khác biệt giữa hiện vật bảo tàng và sản phẩm nghề hôm nay?",
          description: "Phân biệt giữa cổ vật hoàng cung và đồ thủ công dân gian.",
        },
      ],
      citationHeader: "Nguồn thư tịch & Dẫn chứng đối chiếu",
      groundedBadge: "Phản hồi có dẫn chứng",
      comparisonDisclaimer:
        "Đối chiếu mang tính gợi mở bối cảnh văn hóa — không phải sự tương đương lịch sử tuyệt đối.",
      limitationWarning: "Nguồn hiện có chưa đủ để khẳng định chi tiết này.",
      systemUnavailable:
        "Trợ lý văn hóa đang tạm gián đoạn. Bạn vẫn có thể đọc toàn văn câu chuyện đã được kiểm chứng phía dưới.",
      rateLimited:
        "Bạn đã đạt giới hạn câu hỏi trong phiên này. Vui lòng nghỉ ngơi giây lát trước khi hỏi tiếp.",
      noSourcesFound: "Chưa tìm thấy tư liệu lưu trữ phù hợp cho câu hỏi này.",
    },
    media: {
      thirdParty3dTitle: "Mô hình tương tác 3D",
      thirdParty3dNotice:
        "Mô hình 3D từ bên thứ ba (Sketchfab) hiển thị qua khung nhúng theo giấy phép Creative Commons. Không lưu trữ tệp nhị phân trên máy chủ dự án.",
      thirdParty3dUnverified:
        "Mô hình minh họa; chưa qua hội đồng thẩm định về độ chính xác lịch sử.",
      thirdParty3dUnavailable:
        "Chưa có mô hình 3D đạt chuẩn bản quyền và thẩm định. Mời bạn xem ảnh chụp thực tế và tư liệu đính kèm.",
      rightsAttribution: "Bản quyền & Tác giả tư liệu",
      licenseLabel: "Giấy phép công bố",
      creatorLabel: "Tác giả / Nguồn thu thập",
      externalPlatformLink: "Xem trên nền tảng gốc",
      stillPhotoFallbackNotice:
        "Ảnh chụp tư liệu thực địa có chứng nhận quyền sử dụng và nguồn lưu trữ.",
    },
    commercial: {
      illustrativeScenario:
        "Kịch bản minh họa — không phải số liệu kinh doanh hay doanh thu thực tế.",
      sponsorshipDeclaration:
        "Tài trợ dịch vụ công nghệ tính bằng hiện vật (máy chủ BNIX và điểm API Phổ Tuệ đã ký biên bản), không phải doanh thu tiền mặt.",
      providerInactive: "Trải nghiệm này hiện chưa mở tiếp nhận yêu cầu.",
      pilotScopeNotice:
        "Dự án thử nghiệm phi thương mại phục vụ nghiên cứu và kết nối cộng đồng di sản Huế.",
      revenueDisclaimer:
        "Mọi khoản chi phí trải nghiệm nếu có đều được thanh toán trực tiếp giữa khách thăm quan và nghệ nhân địa phương.",
    },
    errors: {
      notFoundTitle: "Không tìm thấy nội dung",
      notFoundMessage:
        "Câu chuyện hoặc địa danh bạn đang tìm kiếm không tồn tại, hoặc đã được chuyển sang địa chỉ mới.",
      generalErrorTitle: "Đã xảy ra sự cố",
      generalErrorMessage:
        "Hệ thống gặp gián đoạn tạm thời trong quá trình xử lý. Vui lòng làm mới trang hoặc thử lại sau ít phút.",
      networkOffline: "Mất kết nối mạng. Đang hiển thị bản lưu ngoại tuyến.",
      validationFailed: "Vui lòng kiểm tra lại các trường thông tin có viền đỏ phía trên.",
      retryAction: "Thử lại",
    },
  },
  en: {
    brand: {
      name: "LUU NIEN",
      fullName: "LƯU NIÊN — The Living Heritage Bridge",
      strapline: "Discover the story. Meet the people. Keep heritage alive.",
      promise: "Culture is more than what we see.",
      productDescriptor: "Stories with sources. Experiences with people.",
      heroExplanation:
        "Understand the story behind a place—and discover the people keeping its traditions alive.",
      eyebrow: "LIVING HERITAGE, HUMAN STORIES",
      subheadline:
        "A cultural discovery platform for Huế, bridging verified historical knowledge with real encounters alongside living craft practitioners.",
      citationPolicy:
        "Every historical narrative on LƯU NIÊN is anchored in verified archival sources and peer-reviewed cultural scholarship.",
      unescoDisclaimer:
        "Monuments within the Complex of Hué Monuments are catalogued in alignment with official UNESCO World Heritage records (Ref 678).",
    },
    nav: {
      discover: "Discover",
      makers: "Meet the makers",
      experiences: "Experiences",
      about: "About",
      learn: "Learn",
      privacy: "Privacy",
      partnerInbox: "Partner Inbox",
      impact: "Impact & Evidence",
      backToStory: "Back to story",
      menuToggle: "Toggle navigation menu",
      closeMenu: "Close navigation menu",
      languageSwitch: "Tiếng Việt",
      skipToContent: "Skip directly to main content",
    },
    cta: {
      exploreStory: "Explore a story",
      meetMaker: "Meet the maker",
      requestAvailability: "Request availability",
      requestExperience: "Request an experience",
      viewSources: "View the sources",
      howItWorks: "How it works",
      askCulturalContext: "Ask about this story",
      quickExplanation: "Quick explanation (under 120 words)",
      exploreDeeper: "Explore deeper (with sources)",
      submitInquiry: "Submit request",
      submitting: "Submitting request...",
      viewThirdParty3d: "View third-party 3D model",
      viewPhotosSources: "View photos and sources",
      readApprovedStory: "Read the approved story",
      backHome: "Back to home",
      contactPartner: "Contact partner",
      copyCitation: "Copy citation",
      copied: "Copied to clipboard",
      close: "Close",
    },
    epistemic: {
      sectionTitle: "Epistemic Certainty Framework",
      sectionSubtitle:
        "Clear differentiation between verified archival facts, living folk traditions, and scholarly interpretations.",
      verifiedSource: {
        id: "verified_source",
        label: "Verified by source",
        description:
          "Directly referenced and cross-checked against published royal archives, state records, or peer-reviewed monographs.",
        badgeClass: "rbpc-badge-verified",
      },
      traditionalAccount: {
        id: "traditional_account",
        label: "Traditional account",
        description:
          "Community oral history or workshop traditions representing living cultural memory, distinct from verified physical events.",
        badgeClass: "rbpc-badge-tradition",
      },
      academicInterpretation: {
        id: "academic_interpretation",
        label: "Academic interpretation",
        description:
          "Analytical hypothesis or contextual reconstruction proposed by historical and cultural researchers.",
        badgeClass: "rbpc-badge-interpretation",
      },
      evidenceGap: {
        id: "evidence_gap",
        label: "Evidence gap",
        description:
          "Available historical records are insufficient to confirm this specific detail. The system openly reserves judgment.",
        badgeClass: "rbpc-badge-gap",
      },
      unescoInscribed: {
        id: "unesco_inscribed",
        label: "UNESCO World Heritage",
        description:
          "Officially designated component of the Complex of Hué Monuments (inscribed 1993, reference 678).",
        badgeClass: "rbpc-badge-unesco",
      },
      livingTradition: {
        id: "living_tradition",
        label: "Living Tradition",
        description:
          "Traditional craftsmanship or intangible cultural practice actively sustained by living local practitioners.",
        badgeClass: "rbpc-badge-tradition",
      },
      humanReviewed: {
        id: "human_reviewed",
        label: "Reviewed by a human editor",
        description:
          "Vetted by a human cultural researcher; not unconstrained generative model output.",
        badgeClass: "rbpc-badge-verified",
      },
      preExistingResearch: {
        id: "pre_existing_research",
        label: "Pre-existing research material",
        description:
          "Foundation material developed in prior scientific and pedagogical projects, transparently disclosed per competition guidelines.",
        badgeClass: "rbpc-badge-review",
      },
    },
    inquiry: {
      modalTitle: "Request Experience Availability",
      modalSubtitle:
        "Concept demonstration — Experience requests will be sent directly to the artisan/facility to confirm timing.",
      experienceProvider: "Host / Artisan",
      durationLabel: "Duration",
      locationLabel: "Workshop Location",
      feeLabel: "Estimated Contribution",
      fields: {
        name: {
          label: "Your Full Name",
          placeholder: "e.g. Alex Morgan",
          error: "Please enter your name (minimum 2 characters).",
        },
        email: {
          label: "Contact Email Address",
          placeholder: "alex@example.com",
          error: "Please enter a valid email address.",
        },
        phone: {
          label: "Phone / WhatsApp / Zalo",
          placeholder: "+84 901 234 567",
          error: "Please enter a valid phone number (8–15 digits).",
        },
        preferredDate: {
          label: "Preferred Date (Optional)",
          placeholder: "Select your preferred date",
          helper: "Actual scheduling depends on the workshop's active craft cycles.",
        },
        partySize: {
          label: "Party Size",
          placeholder: "e.g. 2 adults",
          helper: "To preserve authentic immersion, workshop groups are strictly capped (typically ≤6 participants).",
        },
        message: {
          label: "Notes or Specific Interests",
          placeholder: "Tell the artisan about your curiosity, special timing, or language needs...",
          helper: "Maximum 500 characters.",
          error: "Message must not exceed 500 characters.",
        },
        consent: {
          label:
            "I agree to share these contact details with the experience host so they may evaluate availability and follow up on my request.",
          error: "You must provide consent to share contact information before proceeding.",
        },
      },
      confirmation: {
        title: "Request Received",
        message:
          "Request received. The provider has not confirmed availability yet.",
        statusBadge: "Awaiting Workshop Response",
        referencePrefix: "Request Reference",
        nextStepsTitle: "What happens next?",
        nextStepsBody:
          "The maker or local cultural coordinator will follow up directly via email or phone within 24–48 business hours to confirm availability and logistics.",
        disclaimer:
          "An experience request is not a confirmed booking. Hosting depends on artisan availability and active studio cycles.",
        backButton: "Back to story",
      },
      states: {
        pending: "New Request",
        contacted: "Host Responded",
        confirmed: "Session Confirmed",
        declined: "Studio Unavailable",
        closed: "Completed",
      },
    },
    consent: {
      bannerTitle: "Transparency & Contributor Consent",
      artisanConsentNotice:
        "Every artisan narrative, photographic portrait, and studio profile appears only with signed, written consent.",
      withdrawnNotice:
        "Participating makers retain full sovereignty to update, restrict, or withdraw their profile at any time.",
      privacyNoticeTitle: "Data Protection Pledge",
      privacyNoticeBody:
        "Contact information submitted in inquiries is transmitted solely to the respective workshop coordinator. We never sell, broker, or utilize visitor data for external marketing.",
      cookieMinimal:
        "This platform uses only essential client-side storage for language and accessibility preferences; zero tracking cookies.",
      noMarketingPledge: "Zero spam, zero automated commercial marketing.",
    },
    ai: {
      title: "LƯU NIÊN Cultural Bridge",
      subtitle: "Explore cultural context grounded strictly in vetted historical sources",
      inputPlaceholder: "Ask about this cultural story or traditional craft...",
      buttonAsk: "Ask Guide",
      quickExplainer: "Quick explanation (under 120 words)",
      deepExplainer: "Explore deeper (with citations)",
      guidedPromptsTitle: "Suggested inquiries:",
      guidedPrompts: [
        {
          prompt: "Why does this matter in contemporary life?",
          description: "Explore how this historical symbol connects to modern Vietnamese culture.",
        },
        {
          prompt: "How is this traditionally crafted?",
          description: "Discover the material processes: bronze casting, paper making, firing techniques.",
        },
        {
          prompt: "What is the difference between the museum piece and today's living craft?",
          description: "Distinguish between imperial court relics and contemporary community craft.",
        },
      ],
      citationHeader: "Archival Sources & Evidence Citations",
      groundedBadge: "Source Grounded",
      comparisonDisclaimer:
        "A useful comparison—not a historical equivalence.",
      limitationWarning:
        "We couldn't verify this detail from our approved sources.",
      systemUnavailable:
        "The guide is temporarily unavailable. You can still read the approved story.",
      rateLimited:
        "Session question limit reached. Please pause a moment before continuing.",
      noSourcesFound: "No verified archival sources found for this specific inquiry.",
    },
    media: {
      thirdParty3dTitle: "Interactive 3D Exhibit",
      thirdParty3dNotice:
        "Third-party 3D model (Sketchfab) displayed via embed under Creative Commons license. Binary assets are not hosted on local project servers.",
      thirdParty3dUnverified:
        "Illustrative model; historical accuracy not reviewed by academic panel.",
      thirdParty3dUnavailable:
        "No suitable rights-cleared 3D model yet. View authenticated photos and sources below.",
      rightsAttribution: "Rights & Creator Attribution",
      licenseLabel: "Publishing License",
      creatorLabel: "Model Author / Source",
      externalPlatformLink: "View on source platform",
      stillPhotoFallbackNotice:
        "Documentary photograph with verified rights clearance and archive citation.",
    },
    commercial: {
      illustrativeScenario:
        "Illustrative scenario — not actual sales or income.",
      sponsorshipDeclaration:
        "Documented in-kind technology sponsorship (BNIX VPS & Phổ Tuệ API credits), not cash revenue.",
      providerInactive: "This experience is not accepting requests yet.",
      pilotScopeNotice:
        "Non-commercial exploratory pilot created for cultural research and community connection.",
      revenueDisclaimer:
        "All experience contributions, if applicable, are arranged directly between visitors and local artisans.",
    },
    errors: {
      notFoundTitle: "Page Not Found",
      notFoundMessage:
        "The story, place, or profile you are looking for does not exist or has been relocated.",
      generalErrorTitle: "Something Went Wrong",
      generalErrorMessage:
        "The system encountered an unexpected disruption. Please refresh the page or try again shortly.",
      networkOffline: "Network disconnected. Displaying offline cached content.",
      validationFailed: "Please review the highlighted invalid fields above.",
      retryAction: "Try Again",
    },
  },
};

/**
 * Retrieve the complete copy dictionary for a given locale.
 */
export function getRbpcCopy(locale: RbpcLocale = "vi"): RbpcCopyDictionary {
  return RBPC_COPY[locale] || RBPC_COPY.vi;
}

/**
 * Format a template string by replacing {key} placeholders with provided variables.
 * Example: formatCopy("Hello {name}", { name: "Thắng" }) -> "Hello Thắng"
 */
export function formatCopy(
  template: string,
  variables: Record<string, string | number> = {}
): string {
  return template.replace(/\{(\w+)\}/g, (match, key) => {
    return key in variables ? String(variables[key]) : match;
  });
}

/**
 * Lookup an epistemic certainty status item by identifier and locale.
 */
export function getEpistemicBadgeCopy(
  statusId: string,
  locale: RbpcLocale = "vi"
): EpistemicStatusItem {
  const dict = getRbpcCopy(locale);
  const mapping: Record<string, EpistemicStatusItem> = {
    verified_source: dict.epistemic.verifiedSource,
    traditional_account: dict.epistemic.traditionalAccount,
    academic_interpretation: dict.epistemic.academicInterpretation,
    evidence_gap: dict.epistemic.evidenceGap,
    unesco_inscribed: dict.epistemic.unescoInscribed,
    living_tradition: dict.epistemic.livingTradition,
    human_reviewed: dict.epistemic.humanReviewed,
    pre_existing_research: dict.epistemic.preExistingResearch,
  };

  return (
    mapping[statusId] || {
      id: statusId,
      label: statusId,
      description: "",
      badgeClass: "rbpc-badge-review",
    }
  );
}
