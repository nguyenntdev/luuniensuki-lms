/**
 * Digital Heritage Passport Storage & Royal Seal Ledger.
 * STTTNNĐ Spec: STTT-SPEC-AUDIO-PASSPORT-002
 *
 * Single source of truth for the 16 royal seals of the Imperial City (Cố Đô Huế),
 * localStorage persistence, Web Audio API stamp synthesizer, progress calculations,
 * and cluster completion badges.
 */

import { useState, useEffect } from "react";
import toast from "react-hot-toast";
import {
  type MonumentSeal,
  type SealMotifType,
  ZONE_ROYAL_SEALS_CATALOG,
  GRAND_ROYAL_SEAL,
  getZoneRoyalSeal,
  getGrandRoyalSeal,
} from "./passport-types";
import {
  playStampSound as playAcousticStampSound,
  playZoneCompletionSound,
} from "./seal-audio";

export const PASSPORT_STORAGE_KEY = "luuniensuki_imperial_passport_seals";
export const PASSPORT_STUDENT_KEY = "luuniensuki_imperial_passport_student";
export const PASSPORT_ZONE_SEALS_KEY = "luuniensuki_imperial_zone_seals";
export const SEALS_STORAGE_KEY_LEGACY = "luunien_imperial_passport_seals_v1";
export const SEAL_UPDATE_EVENT_LEGACY = "luunien:seal-updated";

export {
  ZONE_ROYAL_SEALS_CATALOG,
  GRAND_ROYAL_SEAL,
  getZoneRoyalSeal,
  getGrandRoyalSeal,
};

export type SpatialZoneSlug =
  | "central-ceremonial-axis"
  | "ancestral-worship-space"
  | "purple-forbidden-city"
  | "royal-living-gardens";

export interface PassportSealDefinition {
  slug: string;
  name: string;
  nameHanNom: string;
  sealTitle: string;
  sealTitleHanNom: string;
  zoneSlug: SpatialZoneSlug;
  zoneName: string;
  summary: string;
  unlockHint: string;
  guidingQuestion: string;
  reign: string;
  constructionYear: number;
  order: number;
}

export interface UnlockedSealRecord {
  slug: string;
  unlockedAt: string;
  reason?: string;
  siteName?: string;
}

export interface ZoneProgress {
  zoneSlug: SpatialZoneSlug;
  zoneTitle: string;
  zoneTitleHanNom: string;
  description: string;
  totalSeals: number;
  unlockedCount: number;
  percentage: number;
  isComplete: boolean;
  badgeId: string;
  badgeName: string;
  badgeDescription: string;
  badgeIcon: string;
  seals: PassportSealDefinition[];
  royalSeal?: MonumentSeal;
  isZoneSealStamped?: boolean;
}

export interface PassportBadge {
  id: string;
  name: string;
  titleHanNom: string;
  description: string;
  zoneSlug?: SpatialZoneSlug;
  icon: string;
  earnedAt?: string;
}

export interface PassportProgress {
  totalSeals: number;
  unlockedCount: number;
  percentage: number;
  unlockedSlugs: string[];
  zones: ZoneProgress[];
  earnedBadges: PassportBadge[];
  allBadges: PassportBadge[];
  canExportCertificate: boolean;
  minCertificateSeals: number;
  grandRoyalSeal?: MonumentSeal;
  isGrandSealStamped?: boolean;
}

/**
 * 16 Royal Seal Definitions mapped strictly to the 4 verified spatial zones:
 * - Trục trung tâm (4 seals)
 * - Không gian thờ tự (4 seals)
 * - Tử Cấm Thành (5 seals)
 * - Không gian sinh hoạt (3 seals)
 */
export const PASSPORT_SEALS: PassportSealDefinition[] = [
  // 1. Trục trung tâm (4 seals)
  {
    slug: "ngo-mon",
    name: "Ngọ Môn",
    nameHanNom: "午門",
    sealTitle: "Ngọ Môn Chi Ấn",
    sealTitleHanNom: "午門之印",
    zoneSlug: "central-ceremonial-axis",
    zoneName: "Trục trung tâm",
    summary: "Cổng chính phía nam của Hoàng Thành Huế, dưới trổ năm cửa ngõ, trên là lầu Ngũ Phụng 100 cột.",
    unlockHint: "Khảo sát tính phân tầng không gian tại Ngọ Môn hoặc giải câu đố thám tử để đóng dấu.",
    guidingQuestion: "Vì sao cấu trúc 5 cửa ngõ và lầu Ngũ Phụng phản ánh quyền lực tối cao và lễ nghi triều Nguyễn?",
    reign: "Minh Mạng",
    constructionYear: 1833,
    order: 1,
  },
  {
    slug: "cau-trung-dao",
    name: "Cầu Trung Đạo",
    nameHanNom: "中道橋",
    sealTitle: "Trung Đạo Kiều Triện",
    sealTitleHanNom: "中道橋篆",
    zoneSlug: "central-ceremonial-axis",
    zoneName: "Trục trung tâm",
    summary: "Chiếc cầu lát đá thanh bắc qua hồ Thái Dịch trên trục thần đạo nối liền Ngọ Môn và sân Đại Triều Nghi.",
    unlockHint: "Khảo sát ý nghĩa phong thủy và nhịp chuyển tiếp của Cầu Trung Đạo bắc qua hồ Thái Dịch để đóng dấu.",
    guidingQuestion: "Cầu Trung Đạo và hồ Thái Dịch tạo nhịp chuyển tiếp tâm lý trước khi bước vào sân thiết đại triều ra sao?",
    reign: "Minh Mạng",
    constructionYear: 1833,
    order: 2,
  },
  {
    slug: "san-dai-trieu-nghi",
    name: "Sân Đại Triều Nghi",
    nameHanNom: "大朝儀丹墀",
    sealTitle: "Đại Triều Nghi Ký",
    sealTitleHanNom: "大朝儀記",
    zoneSlug: "central-ceremonial-axis",
    zoneName: "Trục trung tâm",
    summary: "Khoảng sân rộng hai tầng lát đá và gạch hoa cương trước điện Thái Hòa, nơi bách quan văn võ dự lễ Đại triều.",
    unlockHint: "Nộp bài khảo sát về trật tự phẩm trật văn võ hai tầng sân Đại Triều để đóng dấu triện son.",
    guidingQuestion: "Sự phân chia hai tầng sân và hệ thống bia phẩm trật tổ chức trật tự nghi lễ quan văn - quan võ như thế nào?",
    reign: "Gia Long",
    constructionYear: 1805,
    order: 3,
  },
  {
    slug: "dien-thai-hoa",
    name: "Điện Thái Hòa",
    nameHanNom: "太和殿",
    sealTitle: "Thái Hòa Điện Ấn",
    sealTitleHanNom: "太和殿印",
    zoneSlug: "central-ceremonial-axis",
    zoneName: "Trục trung tâm",
    summary: "Tòa điện quan trọng bậc nhất biểu trưng cho quyền lực tối cao của thiên tử, xây theo thức trùng thiềm điệp ốc.",
    unlockHint: "Giải mã bí mật chín rồng ngự trị hoặc bài khảo sát kiến trúc ngai vàng tại Điện Thái Hòa để đóng dấu.",
    guidingQuestion: "Kết cấu 'trùng thiềm điệp ốc' và bài trí ngai vàng ở điện Thái Hòa thể hiện vũ trụ quan ra sao?",
    reign: "Gia Long",
    constructionYear: 1805,
    order: 4,
  },

  // 2. Không gian thờ tự (4 seals)
  {
    slug: "the-to-mieu",
    name: "Thế Tổ Miếu",
    nameHanNom: "世祖廟",
    sealTitle: "Thế Miếu Phụng Tự Triện",
    sealTitleHanNom: "世廟奉祀篆",
    zoneSlug: "ancestral-worship-space",
    zoneName: "Không gian thờ tự",
    summary: "Tổ hợp đền miếu phụng thờ các vị hoàng đế triều Nguyễn theo nguyên tắc cổ truyền 'tả chiêu hữu mục'.",
    unlockHint: "Khảo sát quy tắc tả chiêu hữu mục và 9 gian 2 chái tại Thế Tổ Miếu để đóng dấu.",
    guidingQuestion: "Thế Tổ Miếu phản ánh nguyên tắc phụng thờ tổ tiên và trật tự kế vị hoàng đế như thế nào?",
    reign: "Minh Mạng",
    constructionYear: 1821,
    order: 5,
  },
  {
    slug: "hien-lam-cac",
    name: "Hiển Lâm Các",
    nameHanNom: "顯臨閣",
    sealTitle: "Hiển Lâm Các Ký",
    sealTitleHanNom: "顯臨閣記",
    zoneSlug: "ancestral-worship-space",
    zoneName: "Không gian thờ tự",
    summary: "Tòa lầu ba tầng bằng gỗ cao 17m, công trình kiến trúc cao nhất trong Hoàng Thành tưởng niệm công thần và tiên vương.",
    unlockHint: "Khảo sát vai trò đài tưởng niệm công thần và thế đứng uy nghi của Hiển Lâm Các để đóng dấu.",
    guidingQuestion: "Hiển Lâm Các mang ý nghĩa biểu tượng gì trong kiến trúc tưởng niệm công thần và tổ tiên vương triều?",
    reign: "Minh Mạng",
    constructionYear: 1821,
    order: 6,
  },
  {
    slug: "hung-to-mieu",
    name: "Hưng Tổ Miếu",
    nameHanNom: "興祖廟",
    sealTitle: "Hưng Miếu Phụng Tự Chi Ấn",
    sealTitleHanNom: "興廟奉祀之印",
    zoneSlug: "ancestral-worship-space",
    zoneName: "Không gian thờ tự",
    summary: "Ngôi miếu phụng thờ Thế tử Nguyễn Phúc Luân và Hoàng thái hậu Thoại Thánh, thân phụ và thân mẫu vua Gia Long.",
    unlockHint: "Khảo sát quy chuẩn hiếu lễ riêng biệt đối với thân phụ hoàng đế khai triều tại Hưng Tổ Miếu để đóng dấu.",
    guidingQuestion: "Vị trí độc lập của Hưng Miếu bên cạnh Thế Miếu phản ánh quy chuẩn hiếu lễ riêng biệt ra sao?",
    reign: "Gia Long",
    constructionYear: 1804,
    order: 7,
  },
  {
    slug: "trieu-to-mieu",
    name: "Triệu Tổ Miếu",
    nameHanNom: "肇祖廟",
    sealTitle: "Triệu Miếu Tôn Tự Triện",
    sealTitleHanNom: "肇廟尊祀篆",
    zoneSlug: "ancestral-worship-space",
    zoneName: "Không gian thờ tự",
    summary: "Miếu thờ vị khởi tổ khai sáng dòng chúa Nguyễn (Triệu Tổ Tĩnh Hoàng đế Nguyễn Kim) ở góc đông nam Hoàng Thành.",
    unlockHint: "Khảo sát sự đối xứng giữa Triệu Miếu và Thế Miếu trên trục nam bắc để đóng dấu.",
    guidingQuestion: "Sự đối xứng giữa Triệu Miếu ở phía đông và Thế Miếu ở phía tây phản ánh nguồn cội dòng họ ra sao?",
    reign: "Gia Long",
    constructionYear: 1804,
    order: 8,
  },

  // 3. Tử Cấm Thành (5 seals)
  {
    slug: "dai-cung-mon",
    name: "Đại Cung Môn",
    nameHanNom: "大宮門",
    sealTitle: "Đại Cung Môn Khảm",
    sealTitleHanNom: "大宮門鑑",
    zoneSlug: "purple-forbidden-city",
    zoneName: "Tử Cấm Thành",
    summary: "Cửa chính diện dẫn vào Tử Cấm Thành dành riêng cho hoàng đế, nay lưu giữ dấu tích nền móng khảo cổ.",
    unlockHint: "Khảo sát dấu tích nền móng và ranh giới phân định nội cung tại Đại Cung Môn để đóng dấu.",
    guidingQuestion: "Dấu tích nền móng Đại Cung Môn cho biết điều gì về ranh giới đối ngoại và nội bộ hoàng gia?",
    reign: "Minh Mạng",
    constructionYear: 1833,
    order: 9,
  },
  {
    slug: "dien-can-chanh",
    name: "Điện Cần Chánh",
    nameHanNom: "勤政殿",
    sealTitle: "Cần Chánh Điện Ngự Lãm",
    sealTitleHanNom: "勤政殿御覽",
    zoneSlug: "purple-forbidden-city",
    zoneName: "Tử Cấm Thành",
    summary: "Tòa điện thiết triều thường nhật và xử lý cơ mật quốc sự quan trọng nhất của hoàng đế triều Nguyễn.",
    unlockHint: "Khảo sát sự khác biệt về công năng hành chính giữa Điện Cần Chánh và Điện Thái Hòa để đóng dấu.",
    guidingQuestion: "Điện Cần Chánh khác biệt thế nào so với Điện Thái Hòa về công năng thực quyền hành chính?",
    reign: "Gia Long",
    constructionYear: 1804,
    order: 10,
  },
  {
    slug: "dien-kien-trung",
    name: "Điện Kiến Trung",
    nameHanNom: "建忠殿",
    sealTitle: "Kiến Trung Điện Bảo",
    sealTitleHanNom: "建忠殿寶",
    zoneSlug: "purple-forbidden-city",
    zoneName: "Tử Cấm Thành",
    summary: "Kiệt tác kiến trúc kết hợp nghệ thuật khảm sành sứ cung đình Huế và phong cách Art Nouveau tân cổ điển phương Tây.",
    unlockHint: "Giải mã câu đố về nghệ thuật sành sứ và giao thoa văn hóa Đông - Tây tại Điện Kiến Trung để đóng dấu.",
    guidingQuestion: "Sự xuất hiện của Điện Kiến Trung phản ánh những biến đổi về tư tưởng thẩm mỹ đầu thế kỷ XX ra sao?",
    reign: "Khải Định",
    constructionYear: 1923,
    order: 11,
  },
  {
    slug: "duyet-thi-duong",
    name: "Duyệt Thị Đường",
    nameHanNom: "閱是堂",
    sealTitle: "Duyệt Thị Đường Nhã Lạc",
    sealTitleHanNom: "閱是堂雅樂",
    zoneSlug: "purple-forbidden-city",
    zoneName: "Tử Cấm Thành",
    summary: "Nhà hát hoàng gia cổ kính nhất Việt Nam, nơi biểu diễn nhã nhạc và tuồng cổ phục vụ hoàng gia và sứ bộ ngoại giao.",
    unlockHint: "Khảo sát không gian thưởng thức nhã nhạc cung đình tại nhà hát Duyệt Thị Đường để đóng dấu.",
    guidingQuestion: "Không gian tại Duyệt Thị Đường bảo tồn và phản ánh văn hóa Nhã nhạc Cung đình Huế như thế nào?",
    reign: "Minh Mạng",
    constructionYear: 1826,
    order: 12,
  },
  {
    slug: "thai-binh-lau",
    name: "Thái Bình Lâu",
    nameHanNom: "太平樓",
    sealTitle: "Thái Bình Lâu Đồ Thư",
    sealTitleHanNom: "太平樓圖書",
    zoneSlug: "purple-forbidden-city",
    zoneName: "Tử Cấm Thành",
    summary: "Tòa lầu thư viện hai tầng bằng gỗ và sành sứ bên hồ nước tĩnh lặng, nơi hoàng đế nghỉ ngơi và đọc sách.",
    unlockHint: "Giải mã nghệ thuật pháp lam ngũ sắc trên bờ nóc thư viện Thái Bình Lâu để đóng dấu.",
    guidingQuestion: "Nghệ thuật khảm sành sứ và đắp nổi tại Thái Bình Lâu thể hiện đỉnh cao mỹ nghệ Huế ra sao?",
    reign: "Khải Định",
    constructionYear: 1921,
    order: 13,
  },

  // 4. Không gian sinh hoạt (3 seals)
  {
    slug: "cung-dien-tho",
    name: "Cung Diên Thọ",
    nameHanNom: "延壽宮",
    sealTitle: "Diên Thọ Cung Từ Ân",
    sealTitleHanNom: "延壽宮慈恩",
    zoneSlug: "royal-living-gardens",
    zoneName: "Không gian sinh hoạt",
    summary: "Quần thể cung điện quy mô hoàn chỉnh nhất dành cho Hoàng Thái Hậu, kết nối bằng hệ thống trường lang có mái che.",
    unlockHint: "Khảo sát cấu trúc trường lang và đạo hiếu phụng dưỡng thân mẫu tại Cung Diên Thọ để đóng dấu.",
    guidingQuestion: "Hệ thống hành lang có mái che và hồ nước Cung Diên Thọ phản ánh tiện nghi sinh hoạt ra sao?",
    reign: "Gia Long",
    constructionYear: 1804,
    order: 14,
  },
  {
    slug: "cung-truong-sanh",
    name: "Cung Trường Sanh",
    nameHanNom: "長生宮",
    sealTitle: "Trường Sanh Cung Dưỡng",
    sealTitleHanNom: "長生宮頤養",
    zoneSlug: "royal-living-gardens",
    zoneName: "Không gian sinh hoạt",
    summary: "Quần thể hoa viên ngự uyển và cung điện dành cho Thái Hoàng Thái Hậu ở phía tây bắc Hoàng Thành.",
    unlockHint: "Khảo sát nghệ thuật ngự uyển hoa viên và hồ Đào Thái tại Cung Trường Sanh để đóng dấu.",
    guidingQuestion: "Cách bố trí hệ thống hào nước và các hòn non bộ quanh Cung Trường Sanh thể hiện nghệ thuật vườn cung đình ra sao?",
    reign: "Minh Mạng",
    constructionYear: 1821,
    order: 15,
  },
  {
    slug: "dien-phung-tien",
    name: "Điện Phụng Tiên",
    nameHanNom: "奉先殿",
    sealTitle: "Phụng Tiên Điện Kính Tín",
    sealTitleHanNom: "奉先殿敬信",
    zoneSlug: "royal-living-gardens",
    zoneName: "Không gian sinh hoạt",
    summary: "Ngôi điện phụng thờ tổ tiên vương triều dành riêng cho hoàng thái hậu và phụ nữ hoàng tộc đến dâng hương lễ bái.",
    unlockHint: "Khảo sát quy thức phụng tự của nữ giới hoàng tộc tại Điện Phụng Tiên để đóng dấu.",
    guidingQuestion: "Vì sao có sự phân định không gian thờ tự giữa Thế Miếu và Điện Phụng Tiên cho nữ giới hoàng thất?",
    reign: "Minh Mạng",
    constructionYear: 1829,
    order: 16,
  },
];

/**
 * 4 Verified Spatial Zones Metadata
 */
export const PASSPORT_ZONE_META: Record<
  SpatialZoneSlug,
  {
    title: string;
    titleHanNom: string;
    description: string;
    badgeId: string;
    badgeName: string;
    badgeDescription: string;
    badgeIcon: string;
  }
> = {
  "central-ceremonial-axis": {
    title: "Trục trung tâm",
    titleHanNom: "皇城中道軸",
    description:
      "Trục chính đạo thiết lập trật tự không gian quyền lực và nghi lễ tối cao của triều đình, kéo dài từ Ngọ Môn đến Điện Thái Hòa.",
    badgeId: "badge-zone-central",
    badgeName: "Vương Quyền Thần Đạo",
    badgeDescription: "Thu thập trọn vẹn 4 con dấu ấn triện trên trục trung tâm tối thượng của Hoàng Thành Huế.",
    badgeIcon: "👑",
  },
  "ancestral-worship-space": {
    title: "Không gian thờ tự",
    titleHanNom: "宗廟祀禮區",
    description:
      "Khu vực các miếu điện linh thiêng nằm ở phía nam và tây nam Hoàng Thành dành cho việc phụng thờ tổ tiên và các vị vua triều Nguyễn.",
    badgeId: "badge-zone-worship",
    badgeName: "Hiếu Đạo Triều Miếu",
    badgeDescription: "Thu thập trọn vẹn 4 dấu ấn tại khu vực miếu điện phụng thờ tổ tiên và công thần khai quốc.",
    badgeIcon: "🕯️",
  },
  "purple-forbidden-city": {
    title: "Tử Cấm Thành",
    titleHanNom: "紫禁城禁密",
    description:
      "Khu vực cấm địa trung tâm bảo mật tuyệt đối, nơi hoàng đế thiết triều thường nhật, làm việc cơ mật và giải trí cung đình.",
    badgeId: "badge-zone-forbidden",
    badgeName: "Cấm Cung Mật Thám",
    badgeDescription: "Khám phá và đóng dấu trọn vẹn 5 công trình bí mật trong cấm địa Tử Cấm Thành.",
    badgeIcon: "🏯",
  },
  "royal-living-gardens": {
    title: "Không gian sinh hoạt",
    titleHanNom: "宮苑頤養區",
    description:
      "Cụm cung điện và hoa viên ở phía tây bắc dành riêng cho sinh hoạt, phụng dưỡng Hoàng Thái Hậu và nữ giới hoàng gia.",
    badgeId: "badge-zone-living",
    badgeName: "Hoàng Gia Nhàn Nhã",
    badgeDescription: "Hoàn tất 3 dấu triện tại khu ngự uyển hoa viên và cung điện phụng dưỡng hoàng thái hậu.",
    badgeIcon: "🪷",
  },
};

/**
 * All unlockable badges in the Digital Heritage Passport
 */
export const PASSPORT_ALL_BADGES: PassportBadge[] = [
  {
    id: "badge-zone-central",
    name: "Vương Quyền Thần Đạo",
    titleHanNom: "王權神道",
    description: "Thu thập trọn vẹn 4 dấu ấn triện trên trục trung tâm tối thượng của Hoàng Thành Huế.",
    zoneSlug: "central-ceremonial-axis",
    icon: "👑",
  },
  {
    id: "badge-zone-worship",
    name: "Hiếu Đạo Triều Miếu",
    titleHanNom: "孝道廟禮",
    description: "Thu thập trọn vẹn 4 dấu ấn tại khu vực miếu điện phụng thờ tổ tiên và các bậc tiền nhân.",
    zoneSlug: "ancestral-worship-space",
    icon: "🕯️",
  },
  {
    id: "badge-zone-forbidden",
    name: "Cấm Cung Mật Thám",
    titleHanNom: "禁宮秘覽",
    description: "Khám phá và đóng dấu trọn vẹn 5 công trình bí mật trong cấm địa Tử Cấm Thành.",
    zoneSlug: "purple-forbidden-city",
    icon: "🏯",
  },
  {
    id: "badge-zone-living",
    name: "Hoàng Gia Nhàn Nhã",
    titleHanNom: "皇居頤養",
    description: "Hoàn tất 3 dấu triện tại khu hoa viên ngự uyển và cung điện phụng dưỡng hoàng thái hậu.",
    zoneSlug: "royal-living-gardens",
    icon: "🪷",
  },
  {
    id: "badge-master-all",
    name: "Đại Nam Khảo Cứu Tinh Thông",
    titleHanNom: "大南博考通達",
    description: "Khảo cứu xuất sắc và đóng đầy đủ toàn bộ 16 con dấu triện son di tích Đại Nội Huế.",
    icon: "📜",
  },
];

/**
 * Synthesize an authentic wooden royal seal stamp sound with Web Audio API.
 * Produces an acoustic low-frequency impact thump followed by tactile parchment bounce.
 */
export function playStampSound(): void {
  if (typeof window === "undefined") return;

  try {
    const AudioCtxClass =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;

    if (!AudioCtxClass) return;

    const ctx = new AudioCtxClass();

    // 1. Low frequency resonant body thump: 140Hz -> 38Hz
    const osc = ctx.createOscillator();
    const oscGain = ctx.createGain();

    osc.type = "sine";
    const now = ctx.currentTime;

    osc.frequency.setValueAtTime(140, now);
    osc.frequency.exponentialRampToValueAtTime(38, now + 0.14);

    oscGain.gain.setValueAtTime(0.7, now);
    oscGain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);

    osc.connect(oscGain);
    oscGain.connect(ctx.destination);

    osc.start(now);
    osc.stop(now + 0.22);

    // 2. High-frequency parchment friction / seal slap impulse
    const bufferSize = Math.floor(ctx.sampleRate * 0.04);
    const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const data = buffer.getChannelData(0);

    for (let i = 0; i < bufferSize; i++) {
      data[i] = (Math.random() * 2 - 1) * Math.exp(-i / (ctx.sampleRate * 0.008));
    }

    const noise = ctx.createBufferSource();
    noise.buffer = buffer;

    const noiseFilter = ctx.createBiquadFilter();
    noiseFilter.type = "lowpass";
    noiseFilter.frequency.setValueAtTime(900, now);

    const noiseGain = ctx.createGain();
    noiseGain.gain.setValueAtTime(0.28, now);
    noiseGain.gain.exponentialRampToValueAtTime(0.005, now + 0.05);

    noise.connect(noiseFilter);
    noiseFilter.connect(noiseGain);
    noiseGain.connect(ctx.destination);

    noise.start(now);
  } catch (err) {
    // Graceful silent fallback if AudioContext is prevented by autoplay policy
    console.debug("Imperial seal audio stamp effect skipped:", err);
  }
}

function getStorage(): Storage | null {
  try {
    if (typeof window !== "undefined" && window.localStorage) {
      return window.localStorage;
    }
    if (typeof localStorage !== "undefined") {
      return localStorage;
    }
  } catch {}
  return null;
}

/**
 * Retrieve the list of all unlocked seal records from localStorage.
 */
export function getUnlockedSeals(): UnlockedSealRecord[] {
  const storage = getStorage();
  if (!storage) return [];

  try {
    const raw = storage.getItem(PASSPORT_STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed.filter((item) => item && typeof item.slug === "string");
      }

      // Support key-value dictionary { [slug: string]: { unlockedAt: ... } }
      if (parsed && typeof parsed === "object") {
        return Object.entries(parsed).map(([slug, val]) => ({
          slug,
          unlockedAt: (val as { unlockedAt?: string })?.unlockedAt || new Date().toISOString(),
          reason: (val as { reason?: string })?.reason,
          siteName: (val as { siteName?: string })?.siteName,
        }));
      }
    }

    // Fallback: check legacy storage key if present
    const legacyRaw = storage.getItem(SEALS_STORAGE_KEY_LEGACY);
    if (legacyRaw) {
      const parsedLegacy = JSON.parse(legacyRaw);
      if (Array.isArray(parsedLegacy) && parsedLegacy.length > 0) {
        return parsedLegacy.map((slug: string) => ({
          slug,
          unlockedAt: new Date().toISOString(),
          reason: "Đã khảo cứu di tích",
          siteName: PASSPORT_SEALS.find((s) => s.slug === slug)?.name || slug,
        }));
      }
    }

    return [];
  } catch (err) {
    console.warn("Failed to read passport seals from storage:", err);
    return [];
  }
}

/**
 * Lookup helper returning a map of unlocked seals for fast O(1) checks.
 */
export function getUnlockedSealsMap(): Record<string, UnlockedSealRecord> {
  const list = getUnlockedSeals();
  const map: Record<string, UnlockedSealRecord> = {};
  for (const item of list) {
    map[item.slug] = item;
  }
  return map;
}

/**
 * Check if a single monument seal is currently unlocked.
 */
export function isSealUnlocked(monumentSlug: string): boolean {
  const map = getUnlockedSealsMap();
  return Boolean(map[monumentSlug]);
}

/**
 * Get definition of a specific monument seal.
 */
export function getSealDefinition(monumentSlug: string): PassportSealDefinition | undefined {
  return PASSPORT_SEALS.find((s) => s.slug === monumentSlug);
}

/**
 * Retrieve explicit zone seal stamp records from localStorage.
 */
export function getStampedZoneSeals(): Record<string, { stampedAt: string; motif: string }> {
  const storage = getStorage();
  if (!storage) return {};

  try {
    const raw = storage.getItem(PASSPORT_ZONE_SEALS_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed === "object") {
        return parsed;
      }
    }
  } catch (err) {
    console.warn("Failed to read zone seals from storage:", err);
  }
  return {};
}

/**
 * Check if a specific completed zone's Royal Seal (Kim Bảo / Ngự Tỷ) is stamped.
 */
export function isZoneSealStamped(zoneSlug: SpatialZoneSlug): boolean {
  const stampedMap = getStampedZoneSeals();
  if (stampedMap[zoneSlug]) return true;

  // Fallback: if all monuments in this zone are unlocked, the zone seal is inherently earned
  const unlockedMap = getUnlockedSealsMap();
  const zoneSeals = PASSPORT_SEALS.filter((s) => s.zoneSlug === zoneSlug);
  return zoneSeals.length > 0 && zoneSeals.every((s) => Boolean(unlockedMap[s.slug]));
}

/**
 * Check if the Grand Royal Seal (Đại Kim Bảo) is stamped.
 */
export function isGrandSealStamped(): boolean {
  const stampedMap = getStampedZoneSeals();
  if (stampedMap["grand-master-all"]) return true;

  const unlockedMap = getUnlockedSealsMap();
  return PASSPORT_SEALS.length > 0 && PASSPORT_SEALS.every((s) => Boolean(unlockedMap[s.slug]));
}

/**
 * Calculate the complete progress of the Digital Heritage Passport,
 * including counts, percentages, zone completion statuses, zone royal seals, and earned badges.
 */
export function getPassportProgress(): PassportProgress {
  const unlockedList = getUnlockedSeals();
  const unlockedMap = getUnlockedSealsMap();
  const unlockedSlugs = Object.keys(unlockedMap);
  const stampedZoneMap = getStampedZoneSeals();

  const totalSeals = PASSPORT_SEALS.length; // 16
  const unlockedCount = unlockedSlugs.length;
  const percentage = Math.round((unlockedCount / totalSeals) * 100);

  // Group zones
  const zones: ZoneProgress[] = (
    [
      "central-ceremonial-axis",
      "ancestral-worship-space",
      "purple-forbidden-city",
      "royal-living-gardens",
    ] as SpatialZoneSlug[]
  ).map((zoneSlug) => {
    const meta = PASSPORT_ZONE_META[zoneSlug];
    const sealsInZone = PASSPORT_SEALS.filter((s) => s.zoneSlug === zoneSlug);
    const unlockedInZone = sealsInZone.filter((s) => Boolean(unlockedMap[s.slug]));
    const isComplete = sealsInZone.length > 0 && unlockedInZone.length === sealsInZone.length;
    const zonePercentage = Math.round((unlockedInZone.length / sealsInZone.length) * 100);
    const royalSeal = getZoneRoyalSeal(zoneSlug);
    const isStamped = Boolean(stampedZoneMap[zoneSlug]) || isComplete;

    return {
      zoneSlug,
      zoneTitle: meta.title,
      zoneTitleHanNom: meta.titleHanNom,
      description: meta.description,
      totalSeals: sealsInZone.length,
      unlockedCount: unlockedInZone.length,
      percentage: zonePercentage,
      isComplete,
      badgeId: meta.badgeId,
      badgeName: meta.badgeName,
      badgeDescription: meta.badgeDescription,
      badgeIcon: meta.badgeIcon,
      seals: sealsInZone,
      royalSeal: royalSeal
        ? {
            ...royalSeal,
            status: isStamped ? "unlocked" : "locked",
          }
        : undefined,
      isZoneSealStamped: isStamped,
    };
  });

  // Calculate earned badges
  const earnedBadges: PassportBadge[] = [];

  for (const zone of zones) {
    if (zone.isComplete) {
      const badgeDef = PASSPORT_ALL_BADGES.find((b) => b.id === zone.badgeId);
      if (badgeDef) {
        earnedBadges.push({
          ...badgeDef,
          earnedAt: new Date().toISOString(),
        });
      }
    }
  }

  // Master badge when all 16 seals are unlocked
  const isMasterComplete = unlockedCount === totalSeals && totalSeals > 0;
  if (isMasterComplete) {
    const masterBadge = PASSPORT_ALL_BADGES.find((b) => b.id === "badge-master-all");
    if (masterBadge) {
      earnedBadges.push({
        ...masterBadge,
        earnedAt: new Date().toISOString(),
      });
    }
  }

  // Active certificate requirement: at least 4 seals
  const minCertificateSeals = 4;
  const canExportCertificate = unlockedCount >= minCertificateSeals;

  const grandSealDef = getGrandRoyalSeal();
  const grandStamped = Boolean(stampedZoneMap["grand-master-all"]) || isMasterComplete;

  return {
    totalSeals,
    unlockedCount,
    percentage,
    unlockedSlugs,
    zones,
    earnedBadges,
    allBadges: PASSPORT_ALL_BADGES,
    canExportCertificate,
    minCertificateSeals,
    grandRoyalSeal: {
      ...grandSealDef,
      status: grandStamped ? "unlocked" : "locked",
    },
    isGrandSealStamped: grandStamped,
  };
}

/**
 * Stamps a unique royal seal (Kim Bảo or Ngự Tỷ) for a completed zone.
 * Saves to localStorage and triggers celebratory imperial audio chime.
 */
export function stampZoneSeal(zoneSlug: SpatialZoneSlug): {
  success: boolean;
  progress: PassportProgress;
  seal?: MonumentSeal;
} {
  const currentProgress = getPassportProgress();
  const zone = currentProgress.zones.find((z) => z.zoneSlug === zoneSlug);
  const zoneSeal = getZoneRoyalSeal(zoneSlug);

  if (!zone || !zoneSeal) {
    return { success: false, progress: currentProgress };
  }

  // Persist stamped record
  const storage = getStorage();
  const stampedMap = getStampedZoneSeals();
  stampedMap[zoneSlug] = {
    stampedAt: new Date().toISOString(),
    motif: zoneSeal.motif || "kim_bao",
  };

  if (storage) {
    try {
      storage.setItem(PASSPORT_ZONE_SEALS_KEY, JSON.stringify(stampedMap));
    } catch (err) {
      console.error("Failed to persist zone royal seal stamp:", err);
    }
  }

  // Play celebratory audio
  playZoneCompletionSound(zoneSeal.motif === "ngu_ty" ? "ngu_ty" : "kim_bao").catch(() => {});

  // Dispatch custom events
  if (typeof window !== "undefined") {
    try {
      window.dispatchEvent(
        new CustomEvent("imperial-zone-seal-stamped", {
          detail: {
            zoneSlug,
            seal: zoneSeal,
            stampedAt: stampedMap[zoneSlug].stampedAt,
          },
        }),
      );
      window.dispatchEvent(
        new CustomEvent("imperial-seal-unlocked", {
          detail: {
            slug: zoneSeal.monumentSlug,
            name: zoneSeal.sealTextQuocNgu,
            isZoneSeal: true,
          },
        }),
      );
    } catch {}
  }

  const motifLabel = zoneSeal.motif === "kim_bao" ? "Kim Bảo Hoàng Triều" : "Ngự Tỷ Hoàng Triều";
  toast.success(
    `Đã đóng dấu sắc phong ${motifLabel}: "${zoneSeal.sealTextQuocNgu}" (${zone.zoneTitle})!`,
    {
      id: `zone-seal-${zoneSlug}`,
      duration: 6000,
    },
  );

  return {
    success: true,
    progress: getPassportProgress(),
    seal: zoneSeal,
  };
}

/**
 * Stamps the Grand Royal Seal of Đại Nội (Đại Kim Bảo).
 */
export function stampGrandSeal(): {
  success: boolean;
  progress: PassportProgress;
  seal?: MonumentSeal;
} {
  const grandSeal = getGrandRoyalSeal();
  const storage = getStorage();
  const stampedMap = getStampedZoneSeals();
  stampedMap["grand-master-all"] = {
    stampedAt: new Date().toISOString(),
    motif: "kim_bao",
  };

  if (storage) {
    try {
      storage.setItem(PASSPORT_ZONE_SEALS_KEY, JSON.stringify(stampedMap));
    } catch (err) {
      console.error("Failed to persist grand royal seal:", err);
    }
  }

  playZoneCompletionSound("kim_bao").catch(() => {});

  if (typeof window !== "undefined") {
    try {
      window.dispatchEvent(
        new CustomEvent("imperial-zone-seal-stamped", {
          detail: {
            isGrand: true,
            seal: grandSeal,
            stampedAt: stampedMap["grand-master-all"].stampedAt,
          },
        }),
      );
    } catch {}
  }

  toast.success(
    `Đã đóng Đại Kim Bảo Tối Thượng: "${grandSeal.sealTextQuocNgu}" vinh danh Bậc Thầy Khảo Cứu Cố Đô!`,
    {
      id: "grand-seal-stamp",
      duration: 7000,
    },
  );

  return {
    success: true,
    progress: getPassportProgress(),
    seal: grandSeal,
  };
}

/**
 * Record a new seal unlock, play the royal stamp sound, and return updated progress.
 * If the seal is already unlocked, it still plays sound and returns current progress.
 */
export function unlockSeal(
  monumentSlug: string,
  reason = "Khảo sát nghiên cứu di tích",
): PassportProgress {
  if (typeof window === "undefined" && typeof localStorage === "undefined") {
    return getPassportProgress();
  }

  const existingList = getUnlockedSeals();
  const existingIndex = existingList.findIndex((s) => s.slug === monumentSlug);
  const sealDef = getSealDefinition(monumentSlug);
  const siteName = sealDef?.name || monumentSlug;

  let isNewlyUnlocked = false;

  if (existingIndex === -1) {
    isNewlyUnlocked = true;
    const newRecord: UnlockedSealRecord = {
      slug: monumentSlug,
      unlockedAt: new Date().toISOString(),
      reason,
      siteName,
    };
    existingList.push(newRecord);

    const storage = getStorage();
    if (storage) {
      try {
        storage.setItem(PASSPORT_STORAGE_KEY, JSON.stringify(existingList));
        const slugsOnly = existingList.map((s) => s.slug);
        storage.setItem(SEALS_STORAGE_KEY_LEGACY, JSON.stringify(slugsOnly));
      } catch (e) {
        console.error("Failed to write to passport storage:", e);
      }
    }
  }

  // Play auditory stamp feedback
  playStampSound();

  // Dispatch custom events for real-time reactivity across components
  if (typeof window !== "undefined") {
    try {
      window.dispatchEvent(
        new CustomEvent("imperial-seal-unlocked", {
          detail: {
            slug: monumentSlug,
            name: siteName,
            isNew: isNewlyUnlocked,
            reason,
            timestamp: new Date().toISOString(),
          },
        }),
      );
      window.dispatchEvent(
        new CustomEvent(SEAL_UPDATE_EVENT_LEGACY, {
          detail: {
            slug: monumentSlug,
            count: existingList.length,
            total: PASSPORT_SEALS.length,
          },
        }),
      );
    } catch (err) {
      console.debug("Window event dispatch failed:", err);
    }
  }

  // Optional background API synchronization (fails safely if offline or backend route absent)
  syncSealToApi(monumentSlug, reason).catch(() => {});

  return getPassportProgress();
}

/**
 * Display the standard celebratory toast notification for unlocking an imperial seal.
 * Shows royal stamp badge, monument name, and direct link to view the passport.
 */
export function showSealCelebrationToast(monumentSlug: string, monumentName?: string): void {
  if (typeof window === "undefined") return;

  const sealDef = getSealDefinition(monumentSlug);
  const name = monumentName || sealDef?.name || monumentSlug;
  const sealTitle = sealDef?.sealTitle || "Dấu Triện Hoàng Gia";

  toast.success(
    (t) => (
      <div className="flex items-center gap-3 py-1 text-left">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border-2 border-red-700 bg-red-950/20 text-red-600 dark:text-red-400 font-serif font-black text-xs shadow-sm ring-2 ring-red-500/20 uppercase tracking-tighter">
          ẤN
        </div>
        <div className="space-y-0.5 text-xs">
          <p className="font-bold text-foreground leading-tight">
            Bạn đã nhận được Dấu Triện Hoàng Gia:{" "}
            <span className="text-red-700 dark:text-red-400 font-serif font-semibold">
              {name}
            </span>
            !
          </p>
          <div className="flex items-center gap-2 pt-0.5 text-[11px] text-muted-foreground">
            <span className="italic font-serif">&ldquo;{sealTitle}&rdquo;</span>
            <span>•</span>
            <a
              href="/dai-noi/ho-chieu"
              onClick={() => toast.dismiss(t.id)}
              className="text-primary font-bold hover:underline"
            >
              Xem Hộ Chiếu →
            </a>
          </div>
        </div>
      </div>
    ),
    {
      id: `seal-unlocked-${monumentSlug}`,
      duration: 6500,
    },
  );
}

/**
 * Reset all passport seals in localStorage (useful for demo, testing, or reset button).
 */
export function resetPassport(): PassportProgress {
  const storage = getStorage();
  if (storage) {
    try {
      storage.removeItem(PASSPORT_STORAGE_KEY);
      storage.removeItem(PASSPORT_ZONE_SEALS_KEY);
      storage.removeItem(SEALS_STORAGE_KEY_LEGACY);
    } catch (err) {
      console.error("Failed to reset passport storage:", err);
    }
  }
  if (typeof window !== "undefined") {
    try {
      window.dispatchEvent(
        new CustomEvent("imperial-seal-unlocked", {
          detail: { reset: true },
        }),
      );
      window.dispatchEvent(
        new CustomEvent(SEAL_UPDATE_EVENT_LEGACY, {
          detail: { count: 0, total: PASSPORT_SEALS.length },
        }),
      );
    } catch (err) {
      console.debug("CustomEvent dispatch skipped:", err);
    }
  }
  return getPassportProgress();
}

/**
 * Demo / Testing helper: unlock all 16 seals at once.
 */
export function unlockAllSealsDemo(): PassportProgress {
  const storage = getStorage();
  const records: UnlockedSealRecord[] = PASSPORT_SEALS.map((s) => ({
    slug: s.slug,
    unlockedAt: new Date().toISOString(),
    reason: "Mở khóa khảo nghiệm đầy đủ (Demo)",
    siteName: s.name,
  }));
  if (storage) {
    try {
      storage.setItem(PASSPORT_STORAGE_KEY, JSON.stringify(records));
      storage.setItem(
        SEALS_STORAGE_KEY_LEGACY,
        JSON.stringify(PASSPORT_SEALS.map((s) => s.slug)),
      );
      // Also record all 4 zone seals and grand master seal as stamped
      const allZoneStamps: Record<string, { stampedAt: string; motif: string }> = {
        "central-ceremonial-axis": { stampedAt: new Date().toISOString(), motif: "kim_bao" },
        "ancestral-worship-space": { stampedAt: new Date().toISOString(), motif: "ngu_ty" },
        "purple-forbidden-city": { stampedAt: new Date().toISOString(), motif: "kim_bao" },
        "royal-living-gardens": { stampedAt: new Date().toISOString(), motif: "ngu_ty" },
        "grand-master-all": { stampedAt: new Date().toISOString(), motif: "kim_bao" },
      };
      storage.setItem(PASSPORT_ZONE_SEALS_KEY, JSON.stringify(allZoneStamps));
    } catch (err) {
      console.error("Failed to unlock all demo seals:", err);
    }
  }
  playStampSound();
  if (typeof window !== "undefined") {
    try {
      window.dispatchEvent(
        new CustomEvent("imperial-seal-unlocked", {
          detail: { all: true },
        }),
      );
      window.dispatchEvent(
        new CustomEvent(SEAL_UPDATE_EVENT_LEGACY, {
          detail: { count: records.length, total: PASSPORT_SEALS.length },
        }),
      );
    } catch (err) {
      console.debug("CustomEvent dispatch skipped:", err);
    }
  }
  return getPassportProgress();
}

/**
 * Demo / Testing helper: unlock minimum 4 seals to test Certificate unlocking.
 */
export function unlockCertificateDemo(): PassportProgress {
  const storage = getStorage();
  const sampleSlugs = ["ngo-mon", "cau-trung-dao", "san-dai-trieu-nghi", "dien-thai-hoa"];
  const records: UnlockedSealRecord[] = sampleSlugs.map((slug) => {
    const def = getSealDefinition(slug);
    return {
      slug,
      unlockedAt: new Date().toISOString(),
      reason: "Khảo sát Trục trung tâm (Demo Chứng nhận)",
      siteName: def?.name || slug,
    };
  });
  if (storage) {
    try {
      storage.setItem(PASSPORT_STORAGE_KEY, JSON.stringify(records));
      storage.setItem(SEALS_STORAGE_KEY_LEGACY, JSON.stringify(sampleSlugs));
    } catch (err) {
      console.error("Failed to unlock sample seals:", err);
    }
  }
  playStampSound();
  if (typeof window !== "undefined") {
    try {
      window.dispatchEvent(
        new CustomEvent("imperial-seal-unlocked", {
          detail: { demoCertificate: true },
        }),
      );
      window.dispatchEvent(
        new CustomEvent(SEAL_UPDATE_EVENT_LEGACY, {
          detail: { count: records.length, total: PASSPORT_SEALS.length },
        }),
      );
    } catch (err) {
      console.debug("CustomEvent dispatch skipped:", err);
    }
  }
  return getPassportProgress();
}

/**
 * Optional server-side sync with fallback.
 */
async function syncSealToApi(monumentSlug: string, reason: string): Promise<void> {
  try {
    if (typeof window === "undefined" || !navigator.onLine) return;

    await fetch("/api/v1/imperial/passport/unlock", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        monument_slug: monumentSlug,
        reason,
        client_timestamp: new Date().toISOString(),
      }),
    });
  } catch {
    // Intentionally ignore failure: localStorage is primary offline-ready store
  }
}

/**
 * React hook for consuming unlocked seal count and status in real-time across shells and navigation.
 */
export function usePassportProgress(): {
  unlockedCount: number;
  totalSeals: number;
  percentage: number;
  isLoaded: boolean;
  unlockedSlugs: string[];
} {
  const [progress, setProgress] = useState<PassportProgress>(() => getPassportProgress());
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    // Update after client hydration
    setProgress(getPassportProgress());
    setIsLoaded(true);

    const handleUpdate = () => {
      setProgress(getPassportProgress());
    };

    window.addEventListener("imperial-seal-unlocked", handleUpdate);
    window.addEventListener("storage", handleUpdate);

    return () => {
      window.removeEventListener("imperial-seal-unlocked", handleUpdate);
      window.removeEventListener("storage", handleUpdate);
    };
  }, []);

  return {
    unlockedCount: progress.unlockedCount,
    totalSeals: progress.totalSeals,
    percentage: progress.percentage,
    isLoaded,
    unlockedSlugs: progress.unlockedSlugs,
  };
}
