/**
 * TypeScript definitions and catalog for STTTNNĐ Royal Seals & Digital Passport Engine.
 * SPEC ID: STTT-SPEC-AUDIO-PASSPORT-002
 * Scope: STTT_IMPERIAL_CITY (Đại Nội Huế — 16 Historical Monuments)
 *
 * Implements authentic royal seal aesthetics (Ấn triện son Hoàng triều),
 * geometric frames, Han-Nom seal texts, and passport data models.
 */

export type SealStatus = "locked" | "unlocked" | "stamping";

export type SealShape = "square" | "circle" | "octagon" | "arch";

export type SealBorderPattern =
  | "double_imperial"
  | "cloud_fire"
  | "dragon_flame"
  | "lotus_scroll"
  | "fretwork"
  | "water_wave";

export type StampSurface = "paper" | "parchment" | "silk" | "wood";

export type SealMotifType = "monument" | "kim_bao" | "ngu_ty";
export type RoyalSealCategory = "monument" | "zone_royal" | "grand_royal";
export type SealMaterialType = "wood" | "stone" | "jade" | "gold";

export interface MonumentSeal {
  id: string;
  monumentSlug: string;
  monumentNameVi: string;
  monumentNameHanNom: string;
  zoneSlug: string;
  zoneTitleVi: string;
  sealTextQuocNgu: string;
  sealTextHanNom: string;
  sealScriptCharacters: string[];
  shape: SealShape;
  borderPattern: SealBorderPattern;
  symbolDescriptionVi: string;
  historicalEra: string;
  defaultTiltAngle: number;
  inkColor: string;
  goldPatina: boolean;
  status: SealStatus;
  motif?: SealMotifType;
  sealCategory?: RoyalSealCategory;
  material?: SealMaterialType;
  unlockedAt?: string;
  unlockedByTaskId?: string;
  unlockedByTaskTitle?: string;
  evidenceNotes?: string;
}

export interface StampEvent {
  eventId: string;
  monumentSlug: string;
  sealId: string;
  timestamp: string;
  studentName?: string;
  taskSolved?: string;
  coordinates?: { x: number; y: number };
  surface?: StampSurface;
  score?: number;
}

export interface PassportStampRecord {
  isUnlocked: boolean;
  unlockedAt?: string;
  taskSolved?: string;
  rotation?: number;
  score?: number;
}

export interface PassportData {
  passportId: string;
  studentName: string;
  studentClass?: string;
  schoolName?: string;
  issuedAt: string;
  lastStampedAt?: string;
  stamps: Record<string, PassportStampRecord>;
  totalStamped: number;
  totalMonuments: number;
  completionPercentage: number;
  currentRank: string;
}

export interface PassportProgressSummary {
  total: number;
  unlocked: number;
  percentage: number;
  rankTitle: string;
  nextMilestoneTitle: string;
  remainingForNextMilestone: number;
}

/**
 * Single Source of Truth for all 16 Đại Nội Huế Royal Monument Seals.
 * Reflects authentic Sino-Vietnamese Han-Nom epigraphy and Nguyen Dynasty seal craft.
 */
export const MONUMENT_SEALS_CATALOG: MonumentSeal[] = [
  // -------------------------------------------------------------------------
  // ZONE 1: TRỤC TRUNG TÂM (Central Ceremonial Axis)
  // -------------------------------------------------------------------------
  {
    id: "seal-ngo-mon",
    monumentSlug: "ngo-mon",
    monumentNameVi: "Ngọ Môn",
    monumentNameHanNom: "午門",
    zoneSlug: "central-ceremonial-axis",
    zoneTitleVi: "Trục trung tâm",
    sealTextQuocNgu: "Ngọ Môn Chi Ấn",
    sealTextHanNom: "午門之印",
    sealScriptCharacters: ["午", "門", "之", "印"],
    shape: "square",
    borderPattern: "double_imperial",
    symbolDescriptionVi: "Cổng vương triều tráng lệ với năm cửa ngự đạo và vọng lầu Ngũ Phụng đón gió thái bình.",
    historicalEra: "Minh Mạng Thập Tứ Niên (1833)",
    defaultTiltAngle: -1.6,
    inkColor: "#A62B2B",
    goldPatina: true,
    status: "locked",
  },
  {
    id: "seal-cau-trung-dao",
    monumentSlug: "cau-trung-dao",
    monumentNameVi: "Cầu Trung Đạo",
    monumentNameHanNom: "中道橋",
    zoneSlug: "central-ceremonial-axis",
    zoneTitleVi: "Trục trung tâm",
    sealTextQuocNgu: "Trung Đạo Kiều Ký",
    sealTextHanNom: "中道橋記",
    sealScriptCharacters: ["中", "道", "橋", "記"],
    shape: "circle",
    borderPattern: "water_wave",
    symbolDescriptionVi: "Cầu đá thanh bắc ngang hồ Thái Dịch ngát hương sen, nối nhịp tiền tiêu và chốn triều nghi.",
    historicalEra: "Minh Mạng Thập Tứ Niên (1833)",
    defaultTiltAngle: 1.8,
    inkColor: "#A62B2B",
    goldPatina: true,
    status: "locked",
  },
  {
    id: "seal-san-dai-trieu-nghi",
    monumentSlug: "san-dai-trieu-nghi",
    monumentNameVi: "Sân Đại Triều Nghi",
    monumentNameHanNom: "大朝儀丹墀",
    zoneSlug: "central-ceremonial-axis",
    zoneTitleVi: "Trục trung tâm",
    sealTextQuocNgu: "Đại Triều Đan Trì",
    sealTextHanNom: "大朝丹墀",
    sealScriptCharacters: ["大", "朝", "丹", "墀"],
    shape: "octagon",
    borderPattern: "fretwork",
    symbolDescriptionVi: "Sân bái mạng hai tầng cẩn đá, hai hàng phẩm tán văn tả võ hữu trang nghiêm tề chỉnh.",
    historicalEra: "Gia Long Tứ Niên (1805)",
    defaultTiltAngle: -2.1,
    inkColor: "#A62B2B",
    goldPatina: true,
    status: "locked",
  },
  {
    id: "seal-dien-thai-hoa",
    monumentSlug: "dien-thai-hoa",
    monumentNameVi: "Điện Thái Hòa",
    monumentNameHanNom: "太和殿",
    zoneSlug: "central-ceremonial-axis",
    zoneTitleVi: "Trục trung tâm",
    sealTextQuocNgu: "Thái Hòa Điện Khảo Ký",
    sealTextHanNom: "太和殿考記",
    sealScriptCharacters: ["太", "和", "殿", "考", "記", "印"],
    shape: "square",
    borderPattern: "dragon_flame",
    symbolDescriptionVi: "Trùng thiềm điệp ốc uy nghiêm, bửu tán ngai vàng cửu long mây lửa hội tụ linh khí quốc gia.",
    historicalEra: "Gia Long Tứ Niên (1805) / Minh Mạng 1833",
    defaultTiltAngle: 1.2,
    inkColor: "#A62B2B",
    goldPatina: true,
    status: "locked",
  },

  // -------------------------------------------------------------------------
  // ZONE 2: KHÔNG GIAN THỜ TỰ (Ancestral Worship Space)
  // -------------------------------------------------------------------------
  {
    id: "seal-the-to-mieu",
    monumentSlug: "the-to-mieu",
    monumentNameVi: "Thế Tổ Miếu",
    monumentNameHanNom: "世祖廟",
    zoneSlug: "ancestral-worship-space",
    zoneTitleVi: "Không gian thờ tự",
    sealTextQuocNgu: "Thế Miếu Phụng Tự Triện",
    sealTextHanNom: "世廟奉祀篆",
    sealScriptCharacters: ["世", "廟", "奉", "祀", "之", "篆"],
    shape: "square",
    borderPattern: "lotus_scroll",
    symbolDescriptionVi: "Chín gian hai chái phụng thờ tiên đế, trật tự tả chiêu hữu mục cùng Cửu Đỉnh sừng sững.",
    historicalEra: "Minh Mạng Nhị Niên (1821)",
    defaultTiltAngle: -1.7,
    inkColor: "#A62B2B",
    goldPatina: true,
    status: "locked",
  },
  {
    id: "seal-hien-lam-cac",
    monumentSlug: "hien-lam-cac",
    monumentNameVi: "Hiển Lâm Các",
    monumentNameHanNom: "顯臨閣",
    zoneSlug: "ancestral-worship-space",
    zoneTitleVi: "Không gian thờ tự",
    sealTextQuocNgu: "Hiển Lâm Các Ký",
    sealTextHanNom: "顯臨閣記",
    sealScriptCharacters: ["顯", "臨", "閣", "記"],
    shape: "arch",
    borderPattern: "cloud_fire",
    symbolDescriptionVi: "Đài gác gỗ ba tầng cao mười bảy mét vươn tới trời xanh, tôn vinh công đức các bậc khai quốc công thần.",
    historicalEra: "Minh Mạng Nhị Niên (1821 - 1822)",
    defaultTiltAngle: 2.3,
    inkColor: "#A62B2B",
    goldPatina: true,
    status: "locked",
  },
  {
    id: "seal-hung-to-mieu",
    monumentSlug: "hung-to-mieu",
    monumentNameVi: "Hưng Tổ Miếu",
    monumentNameHanNom: "興祖廟",
    zoneSlug: "ancestral-worship-space",
    zoneTitleVi: "Không gian thờ tự",
    sealTextQuocNgu: "Hưng Miếu Khâm Kính",
    sealTextHanNom: "興廟欽敬",
    sealScriptCharacters: ["興", "廟", "欽", "敬"],
    shape: "square",
    borderPattern: "lotus_scroll",
    symbolDescriptionVi: "Nơi tri ân và phụng thờ thân sinh hoàng đế Gia Long, biểu thị lòng hiếu nghĩa muôn đời.",
    historicalEra: "Gia Long Tam Niên (1804)",
    defaultTiltAngle: -1.3,
    inkColor: "#A62B2B",
    goldPatina: true,
    status: "locked",
  },
  {
    id: "seal-trieu-to-mieu",
    monumentSlug: "trieu-to-mieu",
    monumentNameVi: "Triệu Tổ Miếu",
    monumentNameHanNom: "肇祖廟",
    zoneSlug: "ancestral-worship-space",
    zoneTitleVi: "Không gian thờ tự",
    sealTextQuocNgu: "Triệu Miếu Sùng Phụng",
    sealTextHanNom: "肇廟崇奉",
    sealScriptCharacters: ["肇", "廟", "崇", "奉"],
    shape: "circle",
    borderPattern: "double_imperial",
    symbolDescriptionVi: "Miếu đường tôn kính Triệu Tổ Tĩnh Hoàng đế Nguyễn Kim, cội nguồn khởi lập sự nghiệp chúa Nguyễn.",
    historicalEra: "Gia Long Tam Niên (1804)",
    defaultTiltAngle: 1.5,
    inkColor: "#A62B2B",
    goldPatina: true,
    status: "locked",
  },
  {
    id: "seal-dien-phung-tien",
    monumentSlug: "dien-phung-tien",
    monumentNameVi: "Điện Phụng Tiên",
    monumentNameHanNom: "奉先殿",
    zoneSlug: "ancestral-worship-space",
    zoneTitleVi: "Không gian thờ tự",
    sealTextQuocNgu: "Phụng Tiên Từ Ấn",
    sealTextHanNom: "奉先祠印",
    sealScriptCharacters: ["奉", "先", "祠", "印"],
    shape: "square",
    borderPattern: "lotus_scroll",
    symbolDescriptionVi: "Miếu điện tôn kính dành riêng cho phái nữ hoàng cung chiêm bái tổ tiên, cửa tam quan trầm mặc rêu phong.",
    historicalEra: "Gia Long Thập Tam Niên (1814)",
    defaultTiltAngle: 2.0,
    inkColor: "#A62B2B",
    goldPatina: true,
    status: "locked",
  },

  // -------------------------------------------------------------------------
  // ZONE 3: TỬ CẤM THÀNH (Purple Forbidden City)
  // -------------------------------------------------------------------------
  {
    id: "seal-dai-cung-mon",
    monumentSlug: "dai-cung-mon",
    monumentNameVi: "Đại Cung Môn",
    monumentNameHanNom: "大宮門",
    zoneSlug: "purple-forbidden-city",
    zoneTitleVi: "Tử Cấm Thành",
    sealTextQuocNgu: "Đại Cung Môn Ấn",
    sealTextHanNom: "大宮門印",
    sealScriptCharacters: ["大", "宮", "門", "印"],
    shape: "square",
    borderPattern: "fretwork",
    symbolDescriptionVi: "Cửa son chính diện dẫn vào Tử Cấm Thành, ranh giới linh thiêng bảo mật của hoàng đế.",
    historicalEra: "Minh Mạng Thập Tứ Niên (1833)",
    defaultTiltAngle: -1.1,
    inkColor: "#A62B2B",
    goldPatina: true,
    status: "locked",
  },
  {
    id: "seal-dien-can-chanh",
    monumentSlug: "dien-can-chanh",
    monumentNameVi: "Điện Cần Chánh",
    monumentNameHanNom: "勤政殿",
    zoneSlug: "purple-forbidden-city",
    zoneTitleVi: "Tử Cấm Thành",
    sealTextQuocNgu: "Cần Chánh Điện Tích",
    sealTextHanNom: "勤政殿跡",
    sealScriptCharacters: ["勤", "政", "殿", "跡"],
    shape: "square",
    borderPattern: "cloud_fire",
    symbolDescriptionVi: "Nơi thường nhật ngự tọa bàn việc quân cơ mật thiết và lưu bút ngòi son châu phê của các đấng quân vương.",
    historicalEra: "Gia Long Tam Niên (1804)",
    defaultTiltAngle: 1.9,
    inkColor: "#A62B2B",
    goldPatina: true,
    status: "locked",
  },
  {
    id: "seal-dien-kien-trung",
    monumentSlug: "dien-kien-trung",
    monumentNameVi: "Điện Kiến Trung",
    monumentNameHanNom: "建忠殿",
    zoneSlug: "purple-forbidden-city",
    zoneTitleVi: "Tử Cấm Thành",
    sealTextQuocNgu: "Kiến Trung Tân Ký",
    sealTextHanNom: "建忠新記",
    sealScriptCharacters: ["建", "忠", "新", "記"],
    shape: "octagon",
    borderPattern: "fretwork",
    symbolDescriptionVi: "Kiệt tác hòa quyện phong cách Pháp - Ý với nghệ thuật khảm sành sứ cung đình Huế lộng lẫy.",
    historicalEra: "Khải Định Bát Niên (1923)",
    defaultTiltAngle: -1.8,
    inkColor: "#A62B2B",
    goldPatina: true,
    status: "locked",
  },
  {
    id: "seal-duyet-thi-duong",
    monumentSlug: "duyet-thi-duong",
    monumentNameVi: "Duyệt Thị Đường",
    monumentNameHanNom: "閱是堂",
    zoneSlug: "purple-forbidden-city",
    zoneTitleVi: "Tử Cấm Thành",
    sealTextQuocNgu: "Duyệt Thị Hí Viện",
    sealTextHanNom: "閱是戲院",
    sealScriptCharacters: ["閱", "是", "戲", "院"],
    shape: "circle",
    borderPattern: "lotus_scroll",
    symbolDescriptionVi: "Nhà hát hoàng cung cổ nhất nước Việt, ngân vang thanh âm Nhã nhạc cung đình dưới vòm trời ngàn sao.",
    historicalEra: "Minh Mạng Thất Niên (1826)",
    defaultTiltAngle: 1.4,
    inkColor: "#A62B2B",
    goldPatina: true,
    status: "locked",
  },
  {
    id: "seal-thai-binh-lau",
    monumentSlug: "thai-binh-lau",
    monumentNameVi: "Thái Bình Lâu",
    monumentNameHanNom: "太平樓",
    zoneSlug: "purple-forbidden-city",
    zoneTitleVi: "Tử Cấm Thành",
    sealTextQuocNgu: "Thái Bình Thư Các",
    sealTextHanNom: "太平書閣",
    sealScriptCharacters: ["太", "平", "書", "閣"],
    shape: "arch",
    borderPattern: "cloud_fire",
    symbolDescriptionVi: "Thư phòng hai tầng trầm mặc bên hồ nước, chốn hoàng đế tĩnh tâm đọc sách và ngâm vịnh tao nhã.",
    historicalEra: "Khải Định Lục Niên (1921)",
    defaultTiltAngle: -2.4,
    inkColor: "#A62B2B",
    goldPatina: true,
    status: "locked",
  },

  // -------------------------------------------------------------------------
  // ZONE 4: KHÔNG GIAN SINH HOẠT & HOA VIÊN (Royal Living & Gardens)
  // -------------------------------------------------------------------------
  {
    id: "seal-cung-dien-tho",
    monumentSlug: "cung-dien-tho",
    monumentNameVi: "Cung Diên Thọ",
    monumentNameHanNom: "延壽宮",
    zoneSlug: "royal-living-gardens",
    zoneTitleVi: "Không gian sinh hoạt",
    sealTextQuocNgu: "Diên Thọ Cung Triện",
    sealTextHanNom: "延壽宮篆",
    sealScriptCharacters: ["延", "壽", "宮", "篆"],
    shape: "circle",
    borderPattern: "lotus_scroll",
    symbolDescriptionVi: "Quần thể cung đình toàn bích dành cho Hoàng Thái Hậu, hội tụ ngũ phúc cát tường và đạo hiếu vương triều.",
    historicalEra: "Gia Long Tam Niên (1804)",
    defaultTiltAngle: 1.7,
    inkColor: "#A62B2B",
    goldPatina: true,
    status: "locked",
  },
  {
    id: "seal-cung-truong-sanh",
    monumentSlug: "cung-truong-sanh",
    monumentNameVi: "Cung Trường Sanh",
    monumentNameHanNom: "長生宮",
    zoneSlug: "royal-living-gardens",
    zoneTitleVi: "Không gian sinh hoạt",
    sealTextQuocNgu: "Trường Sanh Cung Triện",
    sealTextHanNom: "長生宮篆",
    sealScriptCharacters: ["長", "生", "宮", "篆"],
    shape: "octagon",
    borderPattern: "water_wave",
    symbolDescriptionVi: "Cung điện hoa viên của Thái Hoàng Thái Hậu, non bộ soi bóng hồ nước quanh co tựa chốn bồng lai tiên cảnh.",
    historicalEra: "Minh Mạng Tam Niên (1822)",
    defaultTiltAngle: -1.4,
    inkColor: "#A62B2B",
    goldPatina: true,
    status: "locked",
    motif: "monument",
    sealCategory: "monument",
    material: "wood",
  },
];

/**
 * Unique Royal Seals for Completed Zones (Kim Bảo & Ngự Tỷ Motifs)
 * Representing authentic Nguyen Dynasty imperial seals of state:
 * - Trục trung tâm: Kim Bảo "Hoàng Đế Chi Bảo" (Minh Mạng 1823)
 * - Không gian thờ tự: Ngự Tỷ "Tôn Miếu Ngự Tỷ" (Minh Mạng 1827)
 * - Tử Cấm Thành: Kim Bảo "Ngự Tiền Chi Bảo" (Gia Long 1802)
 * - Không gian sinh hoạt: Ngự Tỷ "Diên Thọ Ngự Tỷ" (Gia Long 1814)
 */
export const ZONE_ROYAL_SEALS_CATALOG: Record<string, MonumentSeal> = {
  "central-ceremonial-axis": {
    id: "seal-zone-central-kim-bao",
    monumentSlug: "zone-central-ceremonial-axis",
    monumentNameVi: "Trục Trung Tâm Hoàng Thành",
    monumentNameHanNom: "皇城中道",
    zoneSlug: "central-ceremonial-axis",
    zoneTitleVi: "Trục trung tâm",
    sealTextQuocNgu: "Hoàng Đế Chi Bảo",
    sealTextHanNom: "皇帝之寶",
    sealScriptCharacters: ["皇", "帝", "之", "寶"],
    shape: "square",
    borderPattern: "dragon_flame",
    symbolDescriptionVi:
      "Kim Bảo đúc bằng vàng ròng với hình tượng rồng cuộn Kim Long Nữu, biểu trưng cho quyền lực tối cao trên trục Thần đạo Đại Nội.",
    historicalEra: "Minh Mạng Tứ Niên (1823)",
    defaultTiltAngle: -1.2,
    inkColor: "#A62B2B",
    goldPatina: true,
    status: "locked",
    motif: "kim_bao",
    sealCategory: "zone_royal",
    material: "gold",
  },
  "ancestral-worship-space": {
    id: "seal-zone-worship-ngu-ty",
    monumentSlug: "zone-ancestral-worship-space",
    monumentNameVi: "Không Gian Thờ Tự Hoàng Tộc",
    monumentNameHanNom: "宗廟祀禮",
    zoneSlug: "ancestral-worship-space",
    zoneTitleVi: "Không gian thờ tự",
    sealTextQuocNgu: "Tôn Miếu Ngự Tỷ",
    sealTextHanNom: "宗廟之璽",
    sealScriptCharacters: ["宗", "廟", "之", "璽"],
    shape: "circle",
    borderPattern: "lotus_scroll",
    symbolDescriptionVi:
      "Ngự Tỷ ngọc bích khắc phụng tự tổ tiên và các bậc tiên đế triều Nguyễn, biểu thị lòng hiếu đạo và gia pháp vương triều.",
    historicalEra: "Minh Mạng Bát Niên (1827)",
    defaultTiltAngle: 1.5,
    inkColor: "#A62B2B",
    goldPatina: true,
    status: "locked",
    motif: "ngu_ty",
    sealCategory: "zone_royal",
    material: "jade",
  },
  "purple-forbidden-city": {
    id: "seal-zone-forbidden-kim-bao",
    monumentSlug: "zone-purple-forbidden-city",
    monumentNameVi: "Tử Cấm Thành Cung Điện",
    monumentNameHanNom: "紫禁城",
    zoneSlug: "purple-forbidden-city",
    zoneTitleVi: "Tử Cấm Thành",
    sealTextQuocNgu: "Ngự Tiền Chi Bảo",
    sealTextHanNom: "御前之寶",
    sealScriptCharacters: ["御", "前", "之", "寶"],
    shape: "octagon",
    borderPattern: "cloud_fire",
    symbolDescriptionVi:
      "Kim Bảo ngự tiền dùng phê duyệt văn kiện cơ mật triều chính và sắc dụ khẩn cấp nơi Tử Cấm Thành.",
    historicalEra: "Gia Long Khởi Nguyên (1802)",
    defaultTiltAngle: -1.8,
    inkColor: "#A62B2B",
    goldPatina: true,
    status: "locked",
    motif: "kim_bao",
    sealCategory: "zone_royal",
    material: "gold",
  },
  "royal-living-gardens": {
    id: "seal-zone-living-ngu-ty",
    monumentSlug: "zone-royal-living-gardens",
    monumentNameVi: "Không Gian Sinh Hoạt Cung Uyển",
    monumentNameHanNom: "皇居頤養",
    zoneSlug: "royal-living-gardens",
    zoneTitleVi: "Không gian sinh hoạt",
    sealTextQuocNgu: "Diên Thọ Ngự Tỷ",
    sealTextHanNom: "延壽之璽",
    sealScriptCharacters: ["延", "壽", "之", "璽"],
    shape: "arch",
    borderPattern: "water_wave",
    symbolDescriptionVi:
      "Ngự Tỷ ngọc thọ chạm khắc mây lành hoa mẫu đơn, biểu trưng cho sự trường thọ, cát tường và lòng thành phụng dưỡng mẫu hậu.",
    historicalEra: "Gia Long Thập Tam Niên (1814)",
    defaultTiltAngle: 1.9,
    inkColor: "#A62B2B",
    goldPatina: true,
    status: "locked",
    motif: "ngu_ty",
    sealCategory: "zone_royal",
    material: "jade",
  },
};

/**
 * Grand Royal Seal (Đại Kim Bảo) awarded upon 16/16 full mastery of Hue Imperial City
 */
export const GRAND_ROYAL_SEAL: MonumentSeal = {
  id: "seal-grand-master-kim-bao",
  monumentSlug: "grand-master-all",
  monumentNameVi: "Đại Nam Hoàng Triều Toàn Cảnh",
  monumentNameHanNom: "大南皇朝",
  zoneSlug: "all",
  zoneTitleVi: "Toàn bộ Hoàng Thành Huế",
  sealTextQuocNgu: "Đại Nam Hoàng Đế Chi Bảo",
  sealTextHanNom: "大南皇帝之寶",
  sealScriptCharacters: ["大", "南", "皇", "帝", "之", "寶"],
  shape: "square",
  borderPattern: "dragon_flame",
  symbolDescriptionVi:
    "Đại Kim Bảo truyền quốc tối thượng của triều Nguyễn, vương bảo trấn quốc đúc năm Minh Mạng thứ 20 (1839).",
  historicalEra: "Minh Mạng Nhị Thập Niên (1839)",
  defaultTiltAngle: 0.8,
  inkColor: "#A62B2B",
  goldPatina: true,
  status: "locked",
  motif: "kim_bao",
  sealCategory: "grand_royal",
  material: "gold",
};

/**
 * Gets unique royal seal (Kim Bảo or Ngự Tỷ) for a given completed zone.
 */
export function getZoneRoyalSeal(zoneSlug: string): MonumentSeal | undefined {
  if (!zoneSlug) return undefined;
  const clean = zoneSlug.toLowerCase().trim();

  // Match canonical zone slug
  if (ZONE_ROYAL_SEALS_CATALOG[clean]) {
    return ZONE_ROYAL_SEALS_CATALOG[clean];
  }

  // Support alternate aliases
  for (const [key, seal] of Object.entries(ZONE_ROYAL_SEALS_CATALOG)) {
    if (
      key === clean ||
      seal.id === clean ||
      seal.monumentSlug === clean ||
      seal.sealTextQuocNgu.toLowerCase() === clean
    ) {
      return seal;
    }
  }

  return undefined;
}

/**
 * Gets the Grand Imperial Seal (Đại Kim Bảo).
 */
export function getGrandRoyalSeal(): MonumentSeal {
  return GRAND_ROYAL_SEAL;
}

/**
 * Finds a MonumentSeal definition by monument slug, zone slug, or ID.
 */
export function getMonumentSeal(slugOrId: string): MonumentSeal | undefined {
  if (!slugOrId) return undefined;
  const clean = slugOrId.toLowerCase().trim();

  // 1. Direct monument match
  const monument = MONUMENT_SEALS_CATALOG.find(
    (s) => s.monumentSlug === clean || s.id === clean || s.id === `seal-${clean}`,
  );
  if (monument) return monument;

  // 2. Zone Royal Seal match
  const zoneSeal = getZoneRoyalSeal(clean);
  if (zoneSeal) return zoneSeal;

  // 3. Grand Royal Seal match
  if (
    clean === "grand-master-all" ||
    clean === "master" ||
    clean === "grand" ||
    clean === "dai-nam-hoang-de-chi-bao" ||
    clean === GRAND_ROYAL_SEAL.id
  ) {
    return GRAND_ROYAL_SEAL;
  }

  return undefined;
}

/**
 * Returns rank label based on number of collected seals out of 16.
 */
export function getHeritageRankTitle(totalUnlocked: number): string {
  if (totalUnlocked >= 16) return "Đại Học Sĩ Thái Hòa Điển Tịch";
  if (totalUnlocked >= 12) return "Hàn Lâm Viện Thị Giảng Học Sĩ";
  if (totalUnlocked >= 8) return "Bác Học Viện Sĩ Cố Đô";
  if (totalUnlocked >= 4) return "Khảo Cứu Sinh Hoàng Triều";
  if (totalUnlocked >= 1) return "Tập Sự Khám Phá Di Sản";
  return "Học Tử Nhập Môn";
}

/**
 * Calculates current progress summary for the heritage passport.
 */
export function calculatePassportProgress(
  stamps: Record<string, PassportStampRecord> | undefined,
): PassportProgressSummary {
  const total = 16;
  if (!stamps) {
    return {
      total,
      unlocked: 0,
      percentage: 0,
      rankTitle: getHeritageRankTitle(0),
      nextMilestoneTitle: "Tập Sự Khám Phá Di Sản (1 di tích)",
      remainingForNextMilestone: 1,
    };
  }

  const unlocked = Object.values(stamps).filter((s) => s?.isUnlocked).length;
  const percentage = Math.round((unlocked / total) * 100);
  const rankTitle = getHeritageRankTitle(unlocked);

  let nextMilestoneTitle = "Hoàn thành toàn bộ di tích Hoàng Triều!";
  let remainingForNextMilestone = 0;

  if (unlocked < 1) {
    nextMilestoneTitle = "Tập Sự Khám Phá Di Sản";
    remainingForNextMilestone = 1 - unlocked;
  } else if (unlocked < 4) {
    nextMilestoneTitle = "Khảo Cứu Sinh Hoàng Triều (4 di tích)";
    remainingForNextMilestone = 4 - unlocked;
  } else if (unlocked < 8) {
    nextMilestoneTitle = "Bác Học Viện Sĩ Cố Đô (8 di tích)";
    remainingForNextMilestone = 8 - unlocked;
  } else if (unlocked < 12) {
    nextMilestoneTitle = "Hàn Lâm Viện Thị Giảng Học Sĩ (12 di tích)";
    remainingForNextMilestone = 12 - unlocked;
  } else if (unlocked < 16) {
    nextMilestoneTitle = "Đại Học Sĩ Thái Hòa Điển Tịch (16 di tích)";
    remainingForNextMilestone = 16 - unlocked;
  }

  return {
    total,
    unlocked,
    percentage,
    rankTitle,
    nextMilestoneTitle,
    remainingForNextMilestone,
  };
}

/**
 * Generates an initial passport object with default values.
 */
export function createDefaultPassportData(
  studentName = "Học sinh Khảo cứu",
  schoolOrClass = "Trường THPT Huế",
): PassportData {
  const initialStamps: Record<string, PassportStampRecord> = {};
  MONUMENT_SEALS_CATALOG.forEach((seal) => {
    initialStamps[seal.monumentSlug] = {
      isUnlocked: false,
      rotation: seal.defaultTiltAngle,
    };
  });

  return {
    passportId: `passport-${Date.now().toString(36)}`,
    studentName,
    studentClass: schoolOrClass,
    schoolName: "Cố đô Huế",
    issuedAt: new Date().toISOString(),
    stamps: initialStamps,
    totalStamped: 0,
    totalMonuments: 16,
    completionPercentage: 0,
    currentRank: getHeritageRankTitle(0),
  };
}
