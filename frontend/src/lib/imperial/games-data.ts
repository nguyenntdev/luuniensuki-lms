/**
 * Comprehensive dataset and helper methods for STTTNNĐ Heritage Mini-Games:
 * 1. Trắc nghiệm di sản (Hiểu sâu "Vì sao", Ghép chi tiết - Ý nghĩa, Định vị cấu kiện)
 * 2. Thám tử cổ vật (Riddle dossiers, progressive clues, monument targeting, royal seal reward)
 * 3. Sắp xếp niên biểu (Chronological ordering & timeline sequencing challenges)
 * 4. Giải mã mật mã cung đình (Imperial cipher, poetic inscriptions, royal emblems)
 */

import type { GameQuestion, ImperialClue } from "./v51-types";
import { FALLBACK_GAME_QUESTIONS, FALLBACK_CLUES } from "./v51-api";

// =========================================================================== //
// 1. CHRONOLOGICAL TIMELINE ORDERING TYPES & DATA
// =========================================================================== //

export interface TimelineEventItem {
  id: string;
  year: number;
  year_label: string;
  title: string;
  description: string;
  site_slug?: string;
}

export interface TimelineChallenge {
  id: string;
  title: string;
  subtitle: string;
  description: string;
  target_competency: "S2_temporal";
  points: number;
  events: TimelineEventItem[]; // Array stored in correct chronological order
  explanation: string;
  source_citation: string;
  hints: string[];
}

export const TIMELINE_CHALLENGES: TimelineChallenge[] = [
  {
    id: "timeline-ch-1",
    title: "Biên Niên Khởi Tạo Đại Nội (Gia Long — Minh Mạng)",
    subtitle: "Năng lực S2 — Thời gian & Niên đại kiến trúc",
    description:
      "Sắp xếp các mốc lịch sử khởi dựng những công trình trọng yếu nhất của Hoàng thành Huế theo đúng trình tự thời gian từ xưa đến nay.",
    target_competency: "S2_temporal",
    points: 70,
    hints: [
      "Vua Gia Long lập vương triều Nguyễn năm 1802 và khởi công Kinh thành ngay sau đó.",
      "Hiển Lâm Các được xây dựng năm 1821 trước khi dựng Cổng Ngọ Môn.",
      "Cửu Đỉnh được đúc vào cuối thời vua Minh Mạng (1835-1837).",
    ],
    explanation:
      "Quy hoạch Kinh thành Huế diễn ra theo lộ trình chiến lược: Năm 1802 vua Gia Long lập triều đại; 1805 bắt đầu đắp thành và dựng Điện Thái Hòa nguyên sơ; năm 1821 vua Minh Mạng dựng Hiển Lâm Các; năm 1833 triệt hạ đài Nam Sách cũ dựng Ngọ Môn và lầu Ngũ Phụng; năm 1835 đúc Cửu Đỉnh làm biểu tượng vĩnh định của non sông.",
    source_citation: "Đại Nam Thực Lục Chính Biên (Đệ nhất kỷ & Đệ nhị kỷ)",
    events: [
      {
        id: "evt-1802",
        year: 1802,
        year_label: "Năm 1802",
        title: "Vua Gia Long định đô tại Phú Xuân",
        description:
          "Vua Gia Long thống nhất đất nước, chọn Phú Xuân làm kinh đô, chuẩn bị quy hoạch Hoàng thành.",
        site_slug: "dien-thai-hoa",
      },
      {
        id: "evt-1805",
        year: 1805,
        year_label: "Năm 1805",
        title: "Khởi công xây đắp Kinh thành & dựng Điện Thái Hòa",
        description:
          "Bắt đầu xây đắp thành lũy kiên cố bằng gạch vồ và khánh thành tòa Điện Thái Hòa đầu tiên.",
        site_slug: "dien-thai-hoa",
      },
      {
        id: "evt-1821",
        year: 1821,
        year_label: "Năm 1821",
        title: "Dựng Hiển Lâm Các tưởng niệm tiền nhân",
        description:
          "Vua Minh Mạng sai dựng tòa gác gỗ lim 3 tầng cao nhất Hoàng thành trước sân Thế Miếu.",
        site_slug: "hien-lam-cac",
      },
      {
        id: "evt-1833",
        year: 1833,
        year_label: "Năm 1833",
        title: "Xây dựng cổng Ngọ Môn & lầu Ngũ Phụng",
        description:
          "Triệt hạ đài Nam Sách cũ để khánh thành Ngọ Môn với 5 cửa ngõ và lầu Ngũ Phụng 9 nóc mái.",
        site_slug: "ngo-mon",
      },
      {
        id: "evt-1835",
        year: 1835,
        year_label: "Năm 1835",
        title: "Đúc Cửu Đỉnh — Bảo vật giang sơn",
        description:
          "Vua Minh Mạng ban lệnh đúc chín đỉnh đồng vĩ đại biểu trưng cho sự thống nhất và vững bền muôn thuở.",
        site_slug: "the-to-mieu",
      },
    ],
  },
  {
    id: "timeline-ch-2",
    title: "Dấu Mốc Biến Thiên & Hồi Sinh Di Sản (XIX — XXI)",
    subtitle: "Năng lực S2 — Biến thiên lịch sử & Bảo tồn",
    description:
      "Sắp xếp các bước ngoặt thăng trầm và công cuộc bảo tồn, phục hồi di sản Cố đô Huế qua các thời kỳ.",
    target_competency: "S2_temporal",
    points: 70,
    hints: [
      "Biến cố kinh thành xảy ra vào thế kỷ XIX (1885).",
      "Vua Khải Định xây Điện Kiến Trung vào những năm 1920.",
      "Vua Bảo Đại thoái vị vào mùa thu lịch sử 1945.",
      "Năm 1993 Huế được vinh danh là Di sản Thế giới đầu tiên của Việt Nam.",
    ],
    explanation:
      "Trải qua biến cố chiến tranh năm 1885 và sự tàn phá năm 1947, Đại Nội Huế từng bước chuyển mình: Lễ thoái vị năm 1945 khép lại thời quân chủ; năm 1993 UNESCO ghi danh Cố đô Huế; và năm 2024 khánh thành đại trùng tu Điện Kiến Trung và Điện Thái Hòa.",
    source_citation: "Trung tâm Bảo tồn Di tích Cố đô Huế & Hồ sơ UNESCO 1993",
    events: [
      {
        id: "evt-1885",
        year: 1885,
        year_label: "Năm 1885",
        title: "Biến cố Kinh thành Huế",
        description:
          "Quân Pháp tấn công Hoàng thành, triều đình rời kinh đô mở đầu phong trào Cần Vương.",
        site_slug: "ngo-mon",
      },
      {
        id: "evt-1923",
        year: 1923,
        year_label: "Năm 1923",
        title: "Khánh thành Điện Kiến Trung tân cổ điển",
        description:
          "Vua Khải Định hoàn tất công trình kết hợp mỹ thuật khảm sành sứ Á Đông và phong cách Pháp.",
        site_slug: "dien-kien-trung",
      },
      {
        id: "evt-1945",
        year: 1945,
        year_label: "Năm 1945",
        title: "Lễ thoái vị của vua Bảo Đại tại Ngọ Môn",
        description:
          "Ngày 30/8/1945, vua Bảo Đại trao ấn kiếm tuyên bố thoái vị, chấm dứt thời kỳ phong kiến Việt Nam.",
        site_slug: "ngo-mon",
      },
      {
        id: "evt-1993",
        year: 1993,
        year_label: "Năm 1993",
        title: "UNESCO ghi danh Quần thể Di tích Cố đô Huế",
        description:
          "Cố đô Huế trở thành Di sản Văn hóa Thế giới đầu tiên của Việt Nam được quốc tế công nhận.",
        site_slug: "dien-thai-hoa",
      },
      {
        id: "evt-2024",
        year: 2024,
        year_label: "Năm 2024",
        title: "Khánh thành đại trùng tu Điện Kiến Trung & Thái Hòa",
        description:
          "Hoàn thành các dự án trùng tu phục hồi quy mô lớn nhất lịch sử, đưa hai cung điện phục vụ du khách.",
        site_slug: "dien-kien-trung",
      },
    ],
  },
  {
    id: "timeline-ch-3",
    title: "Trình Tự Nghi Lễ Đại Triều Tại Điện Thái Hòa",
    subtitle: "Năng lực S3 — Khảo cứu Điển lễ Cung đình",
    description:
      "Dựa theo quy định của Khâm Định Đại Nam Hội Điển Sự Lệ, hãy sắp xếp 4 bước diễn tiến một buổi lễ thiết Đại triều vào ngày sóc vọng.",
    target_competency: "S2_temporal",
    points: 70,
    hints: [
      "Bước đầu tiên bắt đầu từ sự xuất hiện của Loan giá từ nội cung.",
      "Hiệu lệnh chuông trống nổi lên trước khi bách quan chỉnh tề hàng ngũ.",
      "Nghi thức lạy ngũ bái tam khấu diễn ra ở bước cuối cùng khi quan Lễ Bộ xướng lễ.",
    ],
    explanation:
      "Khâm Định Đại Nam Hội Điển Sự Lệ (Quyển 102) quy định: 1. Hoàng đế xuất ngự từ cung điện sang bảo tọa; 2. Khua đại hồng chung và trống lệnh lầu Ngũ Phụng báo hiệu; 3. Bách quan văn võ chỉnh tề theo hàng bia phẩm tán tại sân Đại Triều Nghi; 4. Quan Lễ Bộ tuyên xướng, toàn thể đình thần đồng loạt hành lễ ngũ bái tam khấu.",
    source_citation: "Khâm Định Đại Nam Hội Điển Sự Lệ (Quyển 102: Lễ Bộ nghi thức)",
    events: [
      {
        id: "evt-step-1",
        year: 1,
        year_label: "Bước 1",
        title: "Loan giá Hoàng đế xuất ngự",
        description: "Hoàng đế xuất ngự từ cung điện sang thăng tọa trên ngai vàng Cửu Long.",
        site_slug: "dien-thai-hoa",
      },
      {
        id: "evt-step-2",
        year: 2,
        year_label: "Bước 2",
        title: "Phát hiệu lệnh chuông trống Ngọ Môn",
        description: "Khua đại hồng chung và đại cổ trên lầu Ngũ Phụng báo hiệu bắt đầu buổi lễ.",
        site_slug: "ngo-mon",
      },
      {
        id: "evt-step-3",
        year: 3,
        year_label: "Bước 3",
        title: "Đình thần định vị theo phẩm tán",
        description: "Văn võ bách quan sắp hàng trang nghiêm theo trật tự 9 phẩm từ nhất phẩm đến cửu phẩm.",
        site_slug: "dien-thai-hoa",
      },
      {
        id: "evt-step-4",
        year: 4,
        year_label: "Bước 4",
        title: "Hành đại lễ Ngũ Bái Tam Khấu",
        description: "Quan Lễ Bộ tuyên xướng, đình thần đồng thanh tung hô vạn tuế và hành lễ bái tạ đấng chí tôn.",
        site_slug: "dien-thai-hoa",
      },
    ],
  },
];

// =========================================================================== //
// 2. IMPERIAL CIPHER & INSCRIPTION DECODING TYPES & DATA
// =========================================================================== //

export interface CipherChallenge {
  id: string;
  title: string;
  subtitle: string;
  cipher_type: "poetic_inscription" | "royal_anagram" | "fengshui_numerology";
  target_competency: "S3_evidence" | "S4_argument";
  monument_name: string;
  monument_slug: string;
  background_story: string;
  clue_prompt: string;
  encoded_display: string;
  scrambled_tokens: string[]; // Tokens shown to the learner
  solution_tokens: string[];  // Correct order
  hint_steps: string[];
  explanation: string;
  source_citation: string;
  points: number;
}

export const CIPHER_CHALLENGES: CipherChallenge[] = [
  {
    id: "cipher-ch-1",
    title: "Mật Thư 'Nhất Thi Nhất Họa' Điện Thái Hòa",
    subtitle: "Năng lực S3 — Thơ văn Kiến trúc Di sản UNESCO",
    cipher_type: "poetic_inscription",
    target_competency: "S3_evidence",
    monument_name: "Điện Thái Hòa",
    monument_slug: "dien-thai-hoa",
    background_story:
      "Trên các ô liên ba và cổ diềm của Điện Thái Hòa, vua Thiệu Trị đã cho khắc thếp vàng hàng trăm bài thơ ngũ ngôn tuyệt tác. Trong đó có bài thơ đanh thép khẳng định nền văn hiến và chủ quyền dân tộc từ thời lập quốc.",
    clue_prompt:
      "Hãy giải mã và sắp xếp 4 câu thơ ngự chế ngũ ngôn tuyệt cú của vua Thiệu Trị theo đúng vần luật và trật tự chính sử:",
    encoded_display: "[ ? ? ? ? ] ➔ [ ? ? ? ? ] ➔ [ ? ? ? ? ] ➔ [ ? ? ? ? ]",
    scrambled_tokens: [
      "Hồng Bàng khai tịch hậu",
      "Sơn hà vạn dặm đồ",
      "Nam phục nhất Đường Ngu",
      "Văn hiến thiên niên quốc",
    ],
    solution_tokens: [
      "Văn hiến thiên niên quốc",
      "Sơn hà vạn dặm đồ",
      "Hồng Bàng khai tịch hậu",
      "Nam phục nhất Đường Ngu",
    ],
    hint_steps: [
      "Câu mở đầu khẳng định truyền thống văn hiến ngàn năm của quốc gia.",
      "Câu thứ hai miêu tả bức họa đồ non sông giang sơn rộng lớn vạn dặm.",
      "Câu thứ ba nhắc đến cội nguồn dân tộc bắt đầu từ thuở mở nước thời vua Hùng (Hồng Bàng).",
      "Câu kết ước vọng phương Nam là một cõi thái bình thịnh trị như thời Nghiêu - Thuấn (Đường Ngu).",
    ],
    explanation:
      "Bài thơ ngự chế của vua Thiệu Trị (1841-1847) được chạm khắc trên gian chính điện Thái Hòa mang ý nghĩa: Nước ngàn năm văn hiến / Núi sông vạn dặm tranh / Sau thuở Hồng Bàng mở nước / Phương Nam một cõi Đường Ngu thịnh trị. Đây là chứng tích đỉnh cao của hệ thống Thơ văn trên kiến trúc cung đình Huế được UNESCO công nhận là Di sản Tư liệu Thế giới năm 2016.",
    source_citation:
      "Ngự chế thi tập (Vua Thiệu Trị) & Hồ sơ Di sản Tư liệu UNESCO Thơ văn trên kiến trúc cung đình Huế",
    points: 80,
  },
  {
    id: "cipher-ch-2",
    title: "Mật Mã Hoành Phi Thần Đạo 'Chính Đại Quang Minh'",
    subtitle: "Năng lực S4 — Triết lý Trị quốc Triều Nguyễn",
    cipher_type: "royal_anagram",
    target_competency: "S4_argument",
    monument_name: "Điện Thái Hòa",
    monument_slug: "dien-thai-hoa",
    background_story:
      "Phía trên ngai vàng của đấng chí tôn giăng bức bửu tán lộng lẫy và hoành phi đại tự. Bốn chữ vàng này là mật mã răn dạy đấng quân vương phải giữ lòng ngay thẳng, công minh và sáng suốt soi tỏ thiên hạ.",
    clue_prompt:
      "Chọn và ghép 4 chữ đại tự tạo thành thông điệp tối thượng treo chính giữa điện Thái Hòa:",
    encoded_display: "[ 1 ] — [ 2 ] — [ 3 ] — [ 4 ]",
    scrambled_tokens: ["QUANG", "CHÍNH", "THÁI", "ĐẠI", "BÌNH", "MINH"],
    solution_tokens: ["CHÍNH", "ĐẠI", "QUANG", "MINH"],
    hint_steps: [
      "Chữ đầu tiên có nghĩa là ngay thẳng, chính đáng, không thiên vị (CHÍNH).",
      "Chữ thứ hai thể hiện sự vĩ đại, lớn lao của giang sơn xã tắc (ĐẠI).",
      "Hai chữ sau cùng biểu trưng cho ánh sáng rực rỡ và sự sáng suốt của bậc Thiên tử (QUANG MINH).",
    ],
    explanation:
      "Bốn chữ 'CHÍNH ĐẠI QUANG MINH' (正大光明) là triết lý chính trị Nho giáo cốt lõi của vương triều: người đứng đầu thiên hạ muốn trăm quan tuân phục, lòng dân hòa hợp thì mọi chính lệnh ban ra từ ngôi báu phải tuyệt đối chân chính, ngay thẳng, quang minh lỗi lạc như vầng thái dương.",
    source_citation: "Khâm Định Đại Nam Hội Điển Sự Lệ (Quyển 102 & 214)",
    points: 80,
  },
  {
    id: "cipher-ch-3",
    title: "Mật Mã Số Học Phong Thủy Hoàng Thành",
    subtitle: "Năng lực S1 — Không gian & Phong thủy Cung đình",
    cipher_type: "fengshui_numerology",
    target_competency: "S3_evidence",
    monument_name: "Ngọ Môn & Thế Miếu",
    monument_slug: "ngo-mon",
    background_story:
      "Kiến trúc Đại Nội tuân thủ tuyệt đối quy luật số học phong thủy của Kinh Dịch. Các con số Dương (số lẻ: 1, 3, 5, 9) tượng trưng cho trời, ánh sáng và quyền uy của hoàng đế.",
    clue_prompt:
      "Giải mật mã số học hoàng cung để mở hòm tài liệu: (Số rồng trên ngai vàng Cửu Long) + (Số đỉnh đồng trước Thế Miếu) + (Số cửa ngõ của Ngọ Môn) = ?",
    encoded_display: "Cửu Long (?) + Cửu Đỉnh (?) + Ngũ Môn (?) = [ Mật Số ? ]",
    scrambled_tokens: ["21", "23", "25", "27"],
    solution_tokens: ["23"],
    hint_steps: [
      "'Cửu Long' chạm khắc trên ngai vàng tương ứng với số 9.",
      "'Cửu Đỉnh' sừng sững trước sân Thế Miếu tương ứng với số 9.",
      "'Ngũ Môn' là năm cửa vòm đá của cổng chính Ngọ Môn tương ứng với số 5.",
      "Tính tổng: 9 + 9 + 5 = 23 (con số lẻ chí dương).",
    ],
    explanation:
      "Mật số chính xác là 23 (9 + 9 + 5). Theo Dịch học cung đình Huế, số 9 là số Cực Dương cao nhất của quẻ Càn (Trời), biểu trưng cho Hoàng đế. Số 5 tượng trưng cho Ngũ hành (Kim, Mộc, Thủy, Hỏa, Thổ) và ngũ phương. Việc kết hợp các số dương khẳng định sự trường tồn vĩnh cửu của quốc gia.",
    source_citation: "Khảo cứu phong thủy Kinh thành Huế — Trung tâm BTDT Cố đô Huế",
    points: 80,
  },
];

// =========================================================================== //
// 3. CANDIDATE TARGETS FOR DETECTIVE WIDGET
// =========================================================================== //

export interface CandidateMonument {
  slug: string;
  name: string;
  zone: string;
  brief: string;
  thumbnail: string;
}

export const CANDIDATE_MONUMENTS: CandidateMonument[] = [
  {
    slug: "dien-thai-hoa",
    name: "Điện Thái Hòa",
    zone: "Trục Trung Tâm",
    brief: "Ngai vàng 13 vị vua, 80 cột lim sơn thếp rồng mây",
    thumbnail: "/panoramas/the-mieu.jpg",
  },
  {
    slug: "ngo-mon",
    name: "Ngọ Môn",
    zone: "Cửa Nam Hoàng Thành",
    brief: "Lầu Ngũ Phụng 100 cột, ngói hoàng thanh lưu ly",
    thumbnail: "/panoramas/ngo-mon.jpg",
  },
  {
    slug: "dien-kien-trung",
    name: "Điện Kiến Trung",
    zone: "Tử Cấm Thành",
    brief: "Đỉnh cao nghệ thuật khảm sành sứ tân cổ điển Đông - Tây",
    thumbnail: "/panoramas/cuu-dinh.jpg",
  },
  {
    slug: "hien-lam-cac",
    name: "Hiển Lâm Các",
    zone: "Khu Vực Thế Miếu",
    brief: "Gác gỗ 3 tầng cao 17m, bình hồ lô pháp lam ngũ sắc",
    thumbnail: "/assets/imperial/heritage/dainoitrencao.jpg",
  },
  {
    slug: "thai-binh-lau",
    name: "Thái Bình Lâu",
    zone: "Tử Cấm Thành",
    brief: "Thư viện hoàng gia ngắm trăng đọc sách ngọc",
    thumbnail: "/panoramas/cuu-dinh.jpg",
  },
  {
    slug: "the-to-mieu",
    name: "Thế Tổ Miếu",
    zone: "Tây Nam Hoàng Thành",
    brief: "Nơi thờ tự các vị hoàng đế và Cửu Đỉnh giang sơn",
    thumbnail: "/panoramas/the-mieu.jpg",
  },
];

// =========================================================================== //
// 4. VERIFICATION HELPERS (PURE FUNCTIONS FOR TESTS AND RUNTIME)
// =========================================================================== //

/**
 * Validates a chronological timeline order submitted by the user.
 */
export function verifyTimelineOrdering(
  challenge: TimelineChallenge,
  submittedEventIds: string[],
): {
  isCorrect: boolean;
  correctCount: number;
  totalCount: number;
  scoreAwarded: number;
  feedback: string;
} {
  const correctOrder = challenge.events.map((e) => e.id);
  let correctCount = 0;

  submittedEventIds.forEach((id, index) => {
    if (id === correctOrder[index]) {
      correctCount++;
    }
  });

  const isCorrect = correctCount === correctOrder.length;
  const scoreAwarded = isCorrect
    ? challenge.points
    : Math.round((correctCount / correctOrder.length) * (challenge.points * 0.6));

  const feedback = isCorrect
    ? `Xuất sắc! Bạn đã sắp xếp hoàn hảo toàn bộ ${challenge.events.length} mốc niên biểu di sản.`
    : `Bạn đã xếp đúng ${correctCount}/${challenge.events.length} vị trí. Hãy quan sát gợi ý mốc năm và thử đổi lại các vị trí chưa khớp!`;

  return {
    isCorrect,
    correctCount,
    totalCount: correctOrder.length,
    scoreAwarded,
    feedback,
  };
}

/**
 * Validates an imperial cipher token sequence submitted by the user.
 */
export function verifyCipherSubmission(
  challenge: CipherChallenge,
  submittedTokens: string[],
): {
  isCorrect: boolean;
  scoreAwarded: number;
  feedback: string;
} {
  const expected = challenge.solution_tokens;
  const isCorrect =
    submittedTokens.length === expected.length &&
    submittedTokens.every((t, i) => t.trim().toUpperCase() === expected[i].trim().toUpperCase());

  const scoreAwarded = isCorrect ? challenge.points : 0;
  const feedback = isCorrect
    ? `Chính xác! Bạn đã giải mã thành công thông điệp ngự chế cung đình: "${expected.join(" — ")}".`
    : "Mật mã chưa trùng khớp với điển lễ chính sử. Hãy nghiên cứu thêm gợi ý văn hiến và sắp xếp lại!";

  return {
    isCorrect,
    scoreAwarded,
    feedback,
  };
}

export { FALLBACK_GAME_QUESTIONS, FALLBACK_CLUES };
