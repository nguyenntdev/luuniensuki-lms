import type { LearnPathwayModule } from '@/types/rbpc';

export const LEARN_PATHWAY_MODULES: LearnPathwayModule[] = [
  // =========================================================================
  // PHASE 1: IMPERIAL ARCHIVAL FOUNDATION
  // =========================================================================
  {
    id: "mod-p1-01",
    slug: "kham-dinh-dai-nam-hoi-dien",
    title: {
      vi: "Thư tịch: Khâm Định Đại Nam Hội Điển Sự Lệ",
      en: "Imperial Archives: Khâm Định Đại Nam Administrative Statutes",
    },
    description: {
      vi: "Khảo cứu các chỉ dụ của Hoàng đế Minh Mạng năm 1835 về việc chọn đất, công thức hợp kim đồng thau và điều động nghệ nhân đúc Cửu Đỉnh.",
      en: "Examine Emperor Minh Mạng’s 1835 edicts concerning clay selection, bronze alloy formulas, and the mobilization of foundry artisans.",
    },
    targetAudience: "student",
    learningObjectives: [
      {
        vi: "Hiểu bối cảnh chính trị và văn hóa triều Nguyễn khi khởi đúc Cửu Đỉnh năm 1835",
        en: "Understand the political and cultural context of casting the Nine Dynastic Urns in 1835",
      },
      {
        vi: "Phân tích 3 bản chỉ dụ từ Nội các triều Nguyễn về quy chuẩn đúc đồng",
        en: "Analyze 3 imperial cabinet decrees specifying royal bronze metallurgical standards",
      },
      {
        vi: "Đối chiếu nguồn thư tịch Hán Nôm với tư liệu khảo cổ học đương đại",
        en: "Cross-reference classical Sino-Nom archival texts with modern archaeological evidence",
      },
    ],
    roadmapPhase: "P1_HERITAGE_BASELINE",
    status: "available_in_repo",
    historicalPeriod: "Triều Minh Mạng (1835–1837)",
    sourceCitationsCount: 8,
    estimatedMinutes: 35,
  },
  {
    id: "mod-p1-02",
    slug: "dia-ba-phuong-duc-1835",
    title: {
      vi: "Địa bạ Phường Đúc & Sắc lệnh Thành lập Vụ Đúc",
      en: "Phường Đúc Land Records & Imperial Bronze Directorate Decree",
    },
    description: {
      vi: "Tìm hiểu vị trí địa lý lò than, nguồn phù sa sông Hương và cơ cấu tổ chức ty thợ đúc Nội vụ phủ thế kỷ XIX.",
      en: "Investigate kiln geography, Perfume River alluvial loam deposits, and the guild organization of the Imperial Bronze Directorate in the 19th century.",
    },
    targetAudience: "visitor",
    learningObjectives: [
      {
        vi: "Xác định tọa độ lò đúc cung đình xưa so với bản đồ thực địa Phường Đúc ngày nay",
        en: "Map historical royal foundry coordinates against modern Phường Đúc topography",
      },
      {
        vi: "Nhận biết vai trò của thợ cả và phân cấp thợ phụ trong hiệp thợ đúc đồng hoàng cung",
        en: "Identify the hierarchy and division of labor between master casters and apprentices",
      },
    ],
    roadmapPhase: "P1_HERITAGE_BASELINE",
    status: "available_in_repo",
    historicalPeriod: "Thế kỷ XIX",
    sourceCitationsCount: 6,
    estimatedMinutes: 25,
  },

  // =========================================================================
  // PHASE 2: INTERACTIVE 3D METALLURGY
  // =========================================================================
  {
    id: "mod-p2-01",
    slug: "giai-ma-18-ban-duc-cao-dinh",
    title: {
      vi: "Giải mã 18 Bản đúc nổi trên Cao Đỉnh",
      en: "Decoding the 18 Relief Inscriptions of Cao Đỉnh",
    },
    description: {
      vi: "Khám phá mô hình số 3D tương tác độ phân giải cao của Cao Đỉnh: Khảo sát hình tượng rồng mây, núi non, sông Hương và vũ khí hoàng gia.",
      en: "Interact with the high-resolution 3D digital twin of Cao Đỉnh: Explore dragon clouds, sacred mountains, the Perfume River, and imperial armaments.",
    },
    targetAudience: "student",
    linked3DArtefactSlug: "cao-dinh",
    linkedCreatorSlug: "nguyen-van-cuu",
    learningObjectives: [
      {
        vi: "Quan sát chi tiết 18 bản đúc qua mô hình 3D và hệ thống điểm tương tác (hotspots)",
        en: "Inspect 18 relief inscriptions through the interactive 3D model and spatial hotspot annotations",
      },
      {
        vi: "Giải mã ý nghĩa biểu tượng vũ trụ quan và chủ quyền lãnh thổ Việt Nam",
        en: "Decode cosmological symbolism and Vietnamese territorial sovereignty represented in bronze",
      },
      {
        vi: "So sánh kỹ thuật chạm nổi trên thân đỉnh với hoa văn kiến trúc cung đình Huế",
        en: "Compare relief chiseling craftsmanship with royal architectural decorative motifs",
      },
    ],
    roadmapPhase: "P2_INTERACTIVE_3D",
    status: "available_in_repo",
    historicalPeriod: "1835–1837",
    sourceCitationsCount: 12,
    estimatedMinutes: 40,
  },
  {
    id: "mod-p2-02",
    slug: "ky-thuat-duc-rong-thuan-dinh",
    title: {
      vi: "Kỹ thuật Đúc rỗng & Khuôn đất sét Thuần Đỉnh",
      en: "Hollow Casting & Loam Mold Engineering on Thuần Đỉnh",
    },
    description: {
      vi: "Khảo sát giải phẫu kỹ thuật đúc đồng nguyên khối nặng hàng tấn qua mô hình 3D Thuần Đỉnh và phân rã các lớp vật liệu khuôn đúc.",
      en: "Examine multi-ton monolithic hollow casting techniques using the Thuần Đỉnh 3D model and structural mold layer breakdowns.",
    },
    targetAudience: "educator",
    linked3DArtefactSlug: "thuan-dinh",
    learningObjectives: [
      {
        vi: "Phân tích quy trình tạo lõi đất nung và lớp sáp ong trong kỹ thuật đúc rỗng cổ truyền",
        en: "Analyze terracotta inner core preparation and lost-wax layering in ancient hollow casting",
      },
      {
        vi: "Khảo sát tỷ lệ phối hợp hợp kim đồng - chì - kẽm giúp dung dịch đồng chảy đều trong khuôn lớn",
        en: "Examine copper-lead-zinc alloy fluidity ratios designed for massive monumental molds",
      },
    ],
    roadmapPhase: "P2_INTERACTIVE_3D",
    status: "available_in_repo",
    historicalPeriod: "Triều Minh Mạng",
    sourceCitationsCount: 7,
    estimatedMinutes: 30,
  },

  // =========================================================================
  // PHASE 3: LIVING MAKER MASTERCLASSES
  // =========================================================================
  {
    id: "mod-p3-01",
    slug: "tham-am-rot-dong-phuong-duc",
    title: {
      vi: "Kỹ nghệ Thẩm âm & Rót đồng cùng Nghệ nhân Cửu",
      en: "Acoustic Tuning & Bronze Pouring with Master Cửu",
    },
    description: {
      vi: "Chương trình thực tế tại xưởng đúc Phường Đúc: Lắng nghe nghệ nhân đời thứ 5 thẩm định tiếng phôi đồng và nhào đất sét bãi bồi sông Hương.",
      en: "Fieldwork practicum at Phường Đúc foundry: Learn from a 5th-generation master on acoustic resonance assessment and alluvial clay preparation.",
    },
    targetAudience: "visitor",
    linkedCreatorSlug: "nguyen-van-cuu",
    learningObjectives: [
      {
        vi: "Thử nghiệm phân biệt âm vang của hợp kim đồng nguyên chất so với phôi pha tạp",
        en: "Experience acoustic pitch discernment between pure copper alloy and impure bronze castings",
      },
      {
        vi: "Trực tiếp quan sát quy trình đúc khuôn đất nung truyền thống tại xưởng đúc sống",
        en: "Witness authentic terracotta mold pouring and kiln cooling techniques in an active workshop",
      },
    ],
    roadmapPhase: "P3_MAKER_MASTERCLASS",
    status: "available_in_repo",
    historicalPeriod: "Di sản sống hiện đại",
    sourceCitationsCount: 5,
    estimatedMinutes: 120,
  },
  {
    id: "mod-p3-02",
    slug: "nghe-thuat-phap-lam-hue",
    title: {
      vi: "Sắc màu Hoàng cung: Nhập môn Kỹ nghệ Pháp lam Huế",
      en: "Imperial Pigments: Hue Vitreous Enamel Masterclass",
    },
    description: {
      vi: "Trải nghiệm tạo hoa văn đồng mạ men màu theo kỹ nghệ từng thất truyền từ thời vua Minh Mạng, nay được phục hồi tại xưởng Pháp lam Huế.",
      en: "Hands-on masterclass reviving royal vitreous enamel craft on copper plate, painstakingly restored by Hue research artisans.",
    },
    targetAudience: "student",
    linkedCreatorSlug: "do-huu-tri",
    learningObjectives: [
      {
        vi: "Nhận biết các loại men thủy tinh và quặng màu tự nhiên dùng trong nghệ thuật Pháp lam",
        en: "Identify natural vitreous frit powders and mineral pigment colorants used in royal enamel art",
      },
      {
        vi: "Thực hành kỹ thuật uốn sợi đồng (cloisons) và nung men ở nhiệt độ 850°C",
        en: "Practice copper cloisons wire forming and controlled 850°C muffle kiln firing",
      },
    ],
    roadmapPhase: "P3_MAKER_MASTERCLASS",
    status: "available_in_repo",
    historicalPeriod: "Phục hồi di sản đương đại",
    sourceCitationsCount: 6,
    estimatedMinutes: 90,
  },

  // =========================================================================
  // PHASE 4: ACCREDITED SCHOOL CURRICULUM (ROADMAP 2027–2028)
  // =========================================================================
  {
    id: "mod-p4-01",
    slug: "de-an-chung-chi-di-san-pho-thong",
    title: {
      vi: "Đề án Khung Chứng chỉ Số Di sản Huế (2027–2028)",
      en: "Hue Heritage Micro-Credential Curriculum Framework (2027–2028)",
    },
    description: {
      vi: "Lộ trình thí điểm tích hợp bài học Cửu Đỉnh 3D và nhật ký học tập xưởng nghề vào chương trình Giáo dục Địa phương cho học sinh THCS/THPT Thừa Thiên Huế.",
      en: "Pilot proposal integrating Cửu Đỉnh 3D digital twins and artisan fieldwork journals into local secondary school heritage curricula in Thừa Thiên Huế.",
    },
    targetAudience: "educator",
    learningObjectives: [
      {
        vi: "Xây dựng tiêu chuẩn đánh giá năng lực hiểu biết di sản số và thực hành văn hóa địa phương",
        en: "Establish competency rubrics assessing digital heritage fluency and vernacular cultural engagement",
      },
      {
        vi: "Kết nối hệ thống điểm tích lũy học tập mở (Open Badges) với học bạ số của các trường đối tác",
        en: "Bridge verifiable Open Badges and micro-credentials with participating schools’ academic records",
      },
    ],
    roadmapPhase: "P4_ACCREDITED_CURRICULUM",
    status: "roadmap_phase_2",
    historicalPeriod: "Kế hoạch 2027–2028",
    sourceCitationsCount: 10,
    estimatedMinutes: 45,
  },
  {
    id: "mod-p4-02",
    slug: "tin-chi-thuc-nghiem-bao-tang-xuong-nghe",
    title: {
      vi: "Hệ thống Tín chỉ Thực nghiệm Bảo tàng & Xưởng nghề",
      en: "Museum & Artisan Guild Experiential Practicum Framework",
    },
    description: {
      vi: "Mô hình hợp tác ba bên giữa Trường học – Trung tâm Bảo tồn Di tích Cố đô Huế – Xưởng nghề thủ công, tạo môi trường học tập sống động.",
      en: "Tripartite practicum model uniting schools, the Hue Monuments Conservation Centre, and craft guilds into an immersive experiential learning loop.",
    },
    targetAudience: "student",
    learningObjectives: [
      {
        vi: "Thiết kế phiếu học tập thực địa tại Đại Nội và các phường nghề đúc đồng, hoa giấy, pháp lam",
        en: "Design structured fieldwork investigation logs for the Imperial Citadel and traditional artisan quarters",
      },
      {
        vi: "Quy chuẩn hóa đạo đức học tập và phỏng vấn nghệ nhân cao tuổi trong nghiên cứu cộng đồng",
        en: "Standardize ethics protocols for student interviews with master elder tradition bearers",
      },
    ],
    roadmapPhase: "P4_ACCREDITED_CURRICULUM",
    status: "roadmap_phase_2",
    historicalPeriod: "Kế hoạch 2027–2028",
    sourceCitationsCount: 8,
    estimatedMinutes: 60,
  },
];
