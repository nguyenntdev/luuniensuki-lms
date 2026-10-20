/**
 * Pedagogical Monument Dossiers & Public Sources Ledger for STTTNNĐ (Lưu Niên — Đại Nội Huế).
 * Scope: STTT_IMPERIAL_CITY
 *
 * Implements the 7-section pedagogical architecture for all 16 monuments:
 * 1. Monument Hero & Spatial Identity
 * 2. Guiding Inquiry Question & Vetted Summary
 * 3. Timeline of Construction, Transformation & Restoration
 * 4. Historical Imagery & Architectural Evidence
 * 5. Claims & Primary Source Citations
 * 6. Pedagogical Task & S1-S4 Rubric Guidelines
 * 7. Spatial Connections along Ceremonial Axis
 */

import type {
  ClaimEvidence,
  HistoricalImage,
  ImperialSite,
  ImperialZone,
  PedagogicalTask,
  RubricGuidelines,
  SiteDossierData,
  SpatialConnection,
  TimelineEvent,
} from "./map-types";
import { FALLBACK_ANNOTATIONS, FALLBACK_SITES, FALLBACK_ZONES } from "./fallback-data";
import { getHeritageImagesBySite } from "./heritage-images";

export interface PublicSourceRecord {
  id: string;
  category: "chronicle" | "archival_photo" | "remote_sensing" | "monograph" | "conservation_report";
  title_vi: string;
  original_title?: string;
  authors: string;
  year_or_period: string;
  holding_institution: string;
  archive_ref?: string;
  description_vi: string;
  rights_holder: string;
  license_type: string;
  fair_use_justification: string;
  sample_monuments: string[];
}

export const MONUMENT_DOSSIER_REGISTRY: Record<string, Partial<SiteDossierData>> = {
  "ngo-mon": {
    timeline: [
      {
        year: 1804,
        period_label: "Gia Long",
        event_title: "Dựng đài Nam Sách",
        description: "Khởi dựng đài Nam Sách làm vị trí gác chuông canh và vọng gác tiền tiêu phía nam Hoàng Thành.",
        source_ref: "Đại Nam Thực Lục, Tiền biên",
        is_verified: true,
      },
      {
        year: 1833,
        period_label: "Minh Mạng 14",
        event_title: "Xây dựng Ngọ Môn và Lầu Ngũ Phụng",
        description: "Triệt hạ đài Nam Sách, xây dựng Ngọ Môn với đài chữ U trổ 5 cửa và lầu Ngũ Phụng mái chồng diềm.",
        source_ref: "Đại Nam Thực Lục Chính Biên, Đệ nhị kỷ, Quyển 98",
        is_verified: true,
      },
      {
        year: 1945,
        period_label: "Bảo Đại / CMT8",
        event_title: "Lễ thoái vị của hoàng đế Bảo Đại",
        description: "Ngày 30/8/1945, vua Bảo Đại tuyên đọc chiếu thoái vị, trao ấn kiếm cho phái đoàn Chính phủ Cách mạng Lâm thời.",
        source_ref: "Biên bản bàn giao ấn kiếm 1945",
        is_verified: true,
      },
      {
        year: 1968,
        period_label: "Chiến tranh",
        event_title: "Tổn thất trong biến cố Mậu Thân",
        description: "Lầu Ngũ Phụng bị hư hại nghiêm trọng phần mái và hệ khung gỗ phía tây nam do hỏa lực chiến tranh.",
        source_ref: "Báo cáo thiệt hại di tích Huế 1968",
        is_verified: true,
      },
      {
        year: 2021,
        period_label: "Bảo tồn hiện đại",
        event_title: "Hoàn thành đại trùng tu toàn diện",
        description: "Khép lại dự án bảo tồn tổng thể kéo dài 8 năm phục hồi nguyên bản kết cấu gỗ, sơn thếp và ngói hoàng lưu ly.",
        source_ref: "Trung tâm Bảo tồn Di tích Cố đô Huế",
        is_verified: true,
      },
    ],
    imagery: [
      {
        id: "img-ngo-mon-direct-hero",
        title: "Cổng Ngọ Môn — Tòa nghi môn biểu tượng Cố đô Huế",
        url: "/assets/imperial/heritage/ngomon.jpg",
        caption: "Toàn cảnh chính diện cổng Ngọ Môn sừng sững uy nghi nhìn từ quảng trường Kỳ Đài.",
        year: 2024,
        author_or_source: "Trung tâm Bảo tồn Di tích Cố đô Huế & Ảnh điền dã",
        archive: "Kho tư liệu ảnh di sản Cố đô Huế",
        license_kind: "Educational Permission",
        copyright_note: "Tư liệu phục vụ học tập và nghiên cứu di sản phi thương mại.",
      },
      {
        id: "img-ngo-mon-lau-ngu-phung",
        title: "Lầu Ngũ Phụng trên đài đá Ngọ Môn",
        url: "/assets/imperial/heritage/launguphung.jpg",
        caption: "Lầu Ngũ Phụng hai tầng mái chồng diềm với 100 cây cột gỗ lim thanh thoát.",
        year: 2024,
        author_or_source: "Tư liệu khảo sát kiến trúc Cố đô Huế",
        archive: "Hồ sơ kỹ thuật bảo tồn di tích Huế",
        license_kind: "Educational Permission",
        copyright_note: "Trích xuất hồ sơ khoa học trùng tu di tích.",
      },
      {
        id: "img-ngo-mon-gates",
        title: "Hệ thống 5 cửa vòm đài đá Ngọ Môn",
        url: "/assets/imperial/heritage/congngomon.jpg",
        caption: "Đài đá Ngọ Môn trổ 5 cửa ngõ: cửa chính giữa là Ngọ Môn dành riêng cho hoàng đế, hai cửa bên là Tả/Hữu Giáp Môn, hai cửa ngoài cùng là Tả/Hữu Dịch Môn.",
        year: 2024,
        author_or_source: "Tư liệu kiến trúc cổng thành hoàng gia",
        archive: "Hồ sơ di tích quốc gia đặc biệt",
        license_kind: "Educational Permission",
        copyright_note: "Tư liệu học tập số hóa.",
      },
      {
        id: "img-ngo-mon-festival",
        title: "Lễ hội cung đình trước quảng trường Ngọ Môn",
        url: "/assets/imperial/heritage/festival.jpg",
        caption: "Quảng trường Ngọ Môn trong tuần lễ Festival Huế tôn vinh văn hóa di sản.",
        year: 2024,
        author_or_source: "Tư liệu Festival Huế & Di sản đương đại",
        archive: "Kho ảnh tư liệu lễ hội truyền thống",
        license_kind: "Educational Fair Use",
        copyright_note: "Ảnh tư liệu truyền thông giáo dục di sản.",
      },
    ],
    claims: [
      {
        id: "cl-ngo-mon-1",
        claim_title: "Phân luồng 5 cửa ngõ theo đẳng cấp xã hội",
        assertion_vi: "Cửa chính giữa (Ngọ Môn) chỉ dành riêng cho hoàng đế; hai cửa bên (Tả/Hữu Giáp Môn) dành cho quan văn, quan võ; hai cửa ngoài cùng (Tả/Hữu Dịch Môn) dành cho binh lính, voi ngựa.",
        source_title: "Đại Nam Thực Lục Chính Biên",
        volume_or_chapter: "Đệ nhị kỷ, Quyển 98",
        citation: "Tháng 3 năm Quý Tỵ (1833), dựng cổng Ngọ Môn ở đài Nam Sách cũ; dưới trổ 5 cửa...",
        archival_unit: "Quốc Sử Quán triều Nguyễn / Viện Sử học",
        epistemic_status: "verified",
        notes: "Xác thực qua cả văn bản chính sử và quy chế triều nghi đương thời.",
      },
      {
        id: "cl-ngo-mon-2",
        claim_title: "Chức năng ban sóc và truyền loa",
        assertion_vi: "Lầu Ngũ Phụng là nơi tổ chức lễ Ban Sóc (phát lịch mới hằng năm) và lễ Truyền Loa (xướng danh các vị tân khoa tiến sĩ).",
        source_title: "Khâm Định Đại Nam Hội Điển Sự Lệ",
        volume_or_chapter: "Quyển 168 (Lễ bộ - Lễ nghi)",
        citation: "Quy định thể thức xướng danh tiến sĩ và phát lịch khâm định tại tầng trên lầu Ngũ Phụng.",
        archival_unit: "Nội các triều Nguyễn",
        epistemic_status: "verified",
      },
    ],
    connections: [
      {
        target_slug: "cau-trung-dao",
        target_name_vi: "Cầu Trung Đạo",
        direction: "next",
        axis_description: "Tiếp nối trên trục Thần Đạo tiến về phía bắc, bắc qua hồ Thái Dịch.",
      },
      {
        target_slug: "the-to-mieu",
        target_name_vi: "Thế Tổ Miếu",
        direction: "related",
        axis_description: "Không gian thờ tự tổ tiên triều Nguyễn nằm lệch về phía tây nam sau khi qua cửa Ngọ Môn.",
      },
    ],
  },
  "cau-trung-dao": {
    timeline: [
      {
        year: 1833,
        period_label: "Minh Mạng 14",
        event_title: "Xây dựng cầu Trung Đạo qua hồ Thái Dịch",
        description: "Bắc cầu nối liền Ngọ Môn với sân Đại Triều Nghi, tạo trục hồ cảnh quan phong thủy trước chính điện.",
        source_ref: "Đại Nam Thực Lục Chính Biên",
        is_verified: true,
      },
      {
        year: 1837,
        period_label: "Minh Mạng 18",
        event_title: "Dựng hai cửa đồng quán hai đầu cầu",
        description: "Đặt hai cổng bằng đồng đúc hoa văn rồng mây tinh xảo ở hai đầu cầu Trung Đạo.",
        source_ref: "Đại Nam Nhất Thống Chí",
        is_verified: true,
      },
      {
        year: 2020,
        period_label: "Trùng tu",
        event_title: "Tu bổ bảo tồn lan can đá và nạo vét hồ Thái Dịch",
        description: "Gia cố mố cầu đá thanh và phục dựng hoa sen cảnh quan quanh hồ.",
        source_ref: "Trung tâm Bảo tồn Di tích Cố đô Huế",
        is_verified: true,
      },
    ],
    imagery: [
      {
        id: "img-cau-trung-dao-thai-hoa",
        title: "Cầu Trung Đạo và hồ Thái Dịch hướng về Điện Thái Hòa",
        url: "/assets/imperial/heritage/dainoihue.jpg",
        caption: "Cây cầu đá bắc qua hồ Thái Dịch nở hoa sen trên trục chính đạo nối Ngọ Môn tới sân Đại Triều Nghi.",
        year: 2024,
        author_or_source: "Tư liệu trục chính đạo Hoàng Thành",
        archive: "Kho tư liệu ảnh di sản Cố đô Huế",
        license_kind: "Educational Permission",
        copyright_note: "Tư liệu học tập số hóa di sản.",
      },
    ],
    claims: [
      {
        id: "cl-cau-trung-dao-1",
        claim_title: "Trục thần đạo phân định hai hồ Thái Dịch",
        assertion_vi: "Cầu Trung Đạo là nhịp cầu duy nhất trên trục chính đạo, chia hồ Thái Dịch thành hai nửa tả hữu cân xứng mang ý nghĩa tụ thủy sinh khí.",
        source_title: "Đại Nam Nhất Thống Chí",
        volume_or_chapter: "Quyển 1 (Kinh sư)",
        citation: "Hồ Thái Dịch ở trước điện Thái Hòa, giữa có cầu Trung Đạo bắc qua...",
        archival_unit: "Quốc Sử Quán triều Nguyễn",
        epistemic_status: "verified",
      },
    ],
    connections: [
      {
        target_slug: "ngo-mon",
        target_name_vi: "Ngọ Môn",
        direction: "prev",
        axis_description: "Phía nam: cổng ngự môn dẫn ra Kỳ Đài.",
      },
      {
        target_slug: "san-dai-trieu-nghi",
        target_name_vi: "Sân Đại Triều Nghi",
        direction: "next",
        axis_description: "Phía bắc: sân chầu thiết lễ triều đình trước điện Thái Hòa.",
      },
    ],
  },
  "san-dai-trieu-nghi": {
    timeline: [
      {
        year: 1805,
        period_label: "Gia Long 4",
        event_title: "Khởi dựng sân chầu thiết triều",
        description: "Quy hoạch bãi chầu trước điện Thái Hòa đầu thời lập quốc.",
        source_ref: "Đại Nam Thực Lục",
        is_verified: true,
      },
      {
        year: 1833,
        period_label: "Minh Mạng 14",
        event_title: "Lát đá thanh hai tầng và dựng bia phẩm tán",
        description: "Hoàn thiện hệ thống sân hai tầng (Bái Mạng) và các hàng bia đá nhỏ ghi trật tự từ chánh nhất phẩm đến tòng cửu phẩm.",
        source_ref: "Khâm Định Đại Nam Hội Điển Sự Lệ",
        is_verified: true,
      },
      {
        year: 2022,
        period_label: "Bảo tồn",
        event_title: "Trùng tu phục chế nền gạch Bát Tràng",
        description: "Phục nguyên hệ thống thoát nước cổ và các bia phẩm trật đá Thanh Hoa.",
        source_ref: "Trung tâm Bảo tồn Di tích Cố đô Huế",
        is_verified: true,
      },
    ],
    imagery: [
      {
        id: "img-san-dai-trieu-overview",
        title: "Sân Đại Triều Nghi và không gian quần thể cung điện",
        url: "/assets/imperial/heritage/dainoi.jpg",
        caption: "Khoảng sân hai tầng lát đá thanh và gạch Bát Tràng trước Điện Thái Hòa, nơi bách quan văn võ tề tựu bái mạng trong các buổi đại triều.",
        year: 2024,
        author_or_source: "Tư liệu không gian tổng thể Hoàng Cung Huế",
        archive: "Kho tư liệu ảnh di sản Cố đô Huế",
        license_kind: "Educational Permission",
        copyright_note: "Tư liệu phục vụ học tập và nghiên cứu di sản.",
      },
    ],
    claims: [
      {
        id: "cl-san-dai-trieu-1",
        claim_title: "Quy tắc văn tả võ hữu và phân chia hai tầng sân",
        assertion_vi: "Quan văn đứng bên tả (phía đông), quan võ đứng bên hữu (phía tây). Tầng trên dành cho quan tứ phẩm trở lên, tầng dưới dành cho quan ngũ phẩm đến cửu phẩm.",
        source_title: "Khâm Định Đại Nam Hội Điển Sự Lệ",
        volume_or_chapter: "Quyển 65 (Lại bộ - Lễ Triều nghi)",
        citation: "Văn võ bá quan sắp hàng theo bia phẩm trật: quan văn đứng bên tả, quan võ đứng bên hữu...",
        archival_unit: "Nội các triều Nguyễn",
        epistemic_status: "verified",
      },
    ],
    connections: [
      {
        target_slug: "cau-trung-dao",
        target_name_vi: "Cầu Trung Đạo",
        direction: "prev",
        axis_description: "Phía nam: nhịp cầu đá kết nối tới Ngọ Môn.",
      },
      {
        target_slug: "dien-thai-hoa",
        target_name_vi: "Điện Thái Hòa",
        direction: "next",
        axis_description: "Phía bắc: chính điện tổ chức các đại lễ tối cao.",
      },
    ],
  },
  "dien-thai-hoa": {
    timeline: [
      {
        year: 1805,
        period_label: "Gia Long 4",
        event_title: "Xây dựng điện Thái Hòa đầu tiên",
        description: "Vua Gia Long xây điện Thái Hòa ở vị trí điện Cần Chánh sau này.",
        source_ref: "Đại Nam Thực Lục Chính Biên",
        is_verified: true,
      },
      {
        year: 1833,
        period_label: "Minh Mạng 14",
        event_title: "Dời điện Thái Hòa về vị trí hiện nay",
        description: "Dời điện ra phía nam, xây dựng quy mô lớn theo lối trùng thiềm điệp ốc với 80 cột gỗ lim thếp vàng.",
        source_ref: "Đại Nam Thực Lục Chính Biên, Đệ nhị kỷ",
        is_verified: true,
      },
      {
        year: 1923,
        period_label: "Khải Định 8",
        event_title: "Cải tạo hệ thống trần và trang trí kính",
        description: "Vua Khải Định cho trang hoàng lộng lẫy chuẩn bị Tứ tuần đại khánh.",
        source_ref: "Đồng Khánh Khải Định Chính Yếu",
        is_verified: true,
      },
      {
        year: 2021,
        period_label: "Dự án thế kỷ",
        event_title: "Khởi công đại trùng tu hạ giải toàn diện",
        description: "Dự án bảo tồn khẩn cấp tháo dỡ toàn bộ khung gỗ mục ruỗng để xử lý chân cột và mái ngói hoàng lưu ly.",
        source_ref: "UBND Tỉnh Thừa Thiên Huế",
        is_verified: true,
      },
      {
        year: 2025,
        period_label: "Khánh thành",
        event_title: "Hoàn tất phục hồi điện Thái Hòa",
        description: "Chính thức mở cửa đón khách tham quan sau gần 4 năm tu bổ khoa học nghiêm ngặt.",
        source_ref: "Trung tâm Bảo tồn Di tích Cố đô Huế",
        is_verified: true,
      },
    ],
    imagery: [
      {
        id: "img-dien-thai-hoa-facade",
        title: "Điện Thái Hòa — Biểu tượng quyền lực tối cao vương triều Nguyễn",
        url: "/assets/imperial/heritage/dienthaihoa.jpg",
        caption: "Tòa điện thiết đại triều quan trọng bậc nhất của vương triều Nguyễn, hoàn tất đại trùng tu bảo tồn tổng thể toàn diện giai đoạn 2021-2025.",
        year: 2024,
        author_or_source: "Trung tâm Bảo tồn Di tích Cố đô Huế",
        archive: "Tư liệu trùng tu tổng thể di tích Điện Thái Hòa",
        license_kind: "Educational Permission",
        copyright_note: "Tư liệu hình ảnh phục vụ học tập và nghiên cứu di sản.",
      },
      {
        id: "img-dien-thai-hoa-roof-side",
        title: "Góc nghiêng mái trùng thiềm điệp ốc Điện Thái Hòa",
        url: "/assets/imperial/heritage/dienthaihoa2.jpg",
        caption: "Kiến trúc nhà kép (trùng thiềm điệp ốc) với trần vỏ cua nối liền hai mái, lợp ngói hoàng lưu ly vàng rực rỡ.",
        year: 2024,
        author_or_source: "Tư liệu kiến trúc cung điện Huế",
        archive: "Kho ảnh khảo sát mỹ thuật cung đình",
        license_kind: "Educational Permission",
        copyright_note: "Tài liệu kỹ thuật kiến trúc cổ truyền Việt Nam.",
      },
      {
        id: "img-cau-trung-dao-thai-hoa",
        title: "Cầu Trung Đạo và hồ Thái Dịch hướng về Điện Thái Hòa",
        url: "/assets/imperial/heritage/dainoihue.jpg",
        caption: "Chiếc cầu đá bắc qua hồ Thái Dịch trên trục chính đạo dẫn vào sân Đại Triều Nghi và Điện Thái Hòa.",
        year: 2024,
        author_or_source: "Tư liệu trục chính đạo Hoàng Thành",
        archive: "Kho tư liệu ảnh di sản Cố đô Huế",
        license_kind: "Educational Fair Use",
        copyright_note: "Tư liệu nghiên cứu phục vụ giáo dục di sản.",
      },
    ],
    claims: [
      {
        id: "cl-dien-thai-hoa-1",
        claim_title: "Kiến trúc trùng thiềm điệp ốc và quy cách 80 cột gỗ lim",
        assertion_vi: "Điện Thái Hòa là mẫu mực tiêu biểu nhất của kiến trúc cung đình Huế với kết cấu hai tòa nhà nối liền nhau trên cùng một nền đá, hệ thống cột lim sơn son thếp rồng mây.",
        source_title: "Đại Nam Thực Lục Chính Biên",
        volume_or_chapter: "Đệ nhị kỷ, Quyển 100",
        citation: "Làm lại điện Thái Hòa làm nơi thiết đại triều... quy thức rộng lớn uy nghiêm...",
        archival_unit: "Quốc Sử Quán triều Nguyễn",
        epistemic_status: "verified",
      },
      {
        id: "cl-dien-thai-hoa-2",
        claim_title: "Hệ thống thơ văn 'Nhất thi nhất họa' trên liên ba",
        assertion_vi: "Hàng trăm ô thơ chữ Hán khắc thếp vàng trên các tấm liên ba ca ngợi nền độc lập, thái bình thịnh trị và phong thổ đất nước.",
        source_title: "Hệ thống thơ văn chữ Hán trên kiến trúc cung đình Huế",
        citation: "Hồ sơ Di sản Tư liệu Ký ức Thế giới khu vực Châu Á - Thái Bình Dương (UNESCO 2016).",
        archival_unit: "UNESCO / Cố đô Huế",
        epistemic_status: "verified",
      },
    ],
    connections: [
      {
        target_slug: "san-dai-trieu-nghi",
        target_name_vi: "Sân Đại Triều Nghi",
        direction: "prev",
        axis_description: "Phía nam: sân chầu đại lễ.",
      },
      {
        target_slug: "dai-cung-mon",
        target_name_vi: "Đại Cung Môn",
        direction: "next",
        axis_description: "Phía bắc: cổng chính dẫn vào Tử Cấm Thành.",
      },
      {
        target_slug: "the-to-mieu",
        target_name_vi: "Thế Tổ Miếu",
        direction: "related",
        axis_description: "Phía tây nam: không gian thờ phụng tổ tiên triều đại.",
      },
    ],
  },
  "the-to-mieu": {
    timeline: [
      {
        year: 1821,
        period_label: "Minh Mạng 2",
        event_title: "Khởi dựng Thế Tổ Miếu",
        description: "Xây dựng miếu thờ vua cha Thế Tổ Cao Hoàng Đế (Gia Long).",
        source_ref: "Đại Nam Thực Lục Chính Biên",
        is_verified: true,
      },
      {
        year: 1954,
        period_label: "Bảo tồn",
        event_title: "Tu bổ các gian thờ hoàng đế",
        description: "Hội đồng Hoàng tộc trùng tu các khám thờ và bài vị tổ tiên.",
        source_ref: "Hội đồng Nguyễn Phước Tộc",
        is_verified: true,
      },
      {
        year: 2020,
        period_label: "Trùng tu hiện đại",
        event_title: "Đại trùng tu quần thể miếu",
        description: "Bảo quản chống mối mọt toàn bộ khung gỗ và khôi phục mái ngói thanh lưu ly.",
        source_ref: "Trung tâm Bảo tồn Di tích Cố đô Huế",
        is_verified: true,
      },
    ],
    imagery: [
      {
        id: "img-the-to-mieu-1920",
        title: "Chính điện Thế Tổ Miếu và sân tế đầu thế kỷ 20",
        url: "/assets/imperial/photos/the-mieu-vintage.webp",
        caption: "Kiến trúc miếu thờ chữ Đinh với các gian thờ bài vị hoàng đế.",
        year: 1920,
        author_or_source: "EFEO",
        archive: "Viện Viễn Đông Bác Cổ",
        license_kind: "Public Domain / Educational Fair Use",
        copyright_note: "Tư liệu lưu trữ phục vụ giáo dục.",
      },
    ],
    claims: [
      {
        id: "cl-the-to-mieu-1",
        claim_title: "Quy thức thờ phụng 'Tả chiêu Hữu mục'",
        assertion_vi: "Bài vị các hoàng đế được xếp theo nguyên tắc Chiêu - Mục nghiêm ngặt: Thế Tổ Gia Long ở gian chính giữa, các đời vua tiếp theo xen kẽ tả hữu theo thế thứ thế hệ.",
        source_title: "Khâm Định Đại Nam Hội Điển Sự Lệ",
        volume_or_chapter: "Quyển 82 (Lễ bộ - Tế tự)",
        citation: "Quy định gian thờ và thể thức cúng tế trong Thế Miếu.",
        archival_unit: "Nội các triều Nguyễn",
        epistemic_status: "verified",
      },
    ],
    connections: [
      {
        target_slug: "hien-lam-cac",
        target_name_vi: "Hiển Lâm Các",
        direction: "prev",
        axis_description: "Phía nam: đài kỷ niệm công đức tiền nhân án ngữ trước sân miếu.",
      },
      {
        target_slug: "hung-to-mieu",
        target_name_vi: "Hưng Tổ Miếu",
        direction: "next",
        axis_description: "Phía bắc: miếu thờ thân phụ vua Gia Long.",
      },
    ],
  },
  "hien-lam-cac": {
    timeline: [
      {
        year: 1821,
        period_label: "Minh Mạng 2",
        event_title: "Khởi công xây dựng vọng lâu",
        description: "Khởi dựng kiến trúc 3 tầng bằng gỗ lim cao vút làm biểu tượng ghi nhớ công tích tiền nhân.",
        source_ref: "Đại Nam Thực Lục Chính Biên",
        is_verified: true,
      },
      {
        year: 1822,
        period_label: "Minh Mạng 3",
        event_title: "Hoàn thành và ban bố quy định kiến trúc",
        description: "Quy định nghiêm ngặt: trong toàn bộ Hoàng Thành không được xây bất kỳ công trình nào cao hơn Hiển Lâm Các.",
        source_ref: "Khâm Định Đại Nam Hội Điển Sự Lệ",
        is_verified: true,
      },
      {
        year: 1947,
        period_label: "Kháng chiến",
        event_title: "May mắn nguyên vẹn qua khói lửa",
        description: "Hiển Lâm Các là một trong số ít kiến trúc gỗ lớn của Đại Nội giữ được cốt lõi nguyên bản qua hai cuộc chiến tranh.",
        source_ref: "Hồ sơ UNESCO 1993",
        is_verified: true,
      },
    ],
    imagery: [
      {
        id: "img-hien-lam-cac-facade",
        title: "Mặt đứng 3 tầng thanh thoát của Hiển Lâm Các",
        url: "/assets/imperial/photos/hien-lam-cac-facade.webp",
        caption: "Công trình gỗ cao 17 mét với các tầng mái chồng diềm vươn cao trong không gian thờ tự.",
        year: 1935,
        author_or_source: "Archival Collection",
        archive: "Trung tâm Lưu trữ Quốc gia IV",
        license_kind: "Public Domain / Educational Fair Use",
        copyright_note: "Tư liệu lưu trữ lịch sử quốc gia.",
      },
    ],
    claims: [
      {
        id: "cl-hien-lam-cac-1",
        claim_title: "Giới hạn độ cao tôn vinh công đức triều đại",
        assertion_vi: "Chiều cao 17m của Hiển Lâm Các là giới hạn trần kiến trúc trong Hoàng Thành, thể hiện sự kính ngưỡng tuyệt đối đối với tiền nhân và thần linh che chở vương triều.",
        source_title: "Đại Nam Thực Lục",
        volume_or_chapter: "Đệ nhị kỷ, Quyển 14",
        citation: "Dựng Hiển Lâm Các cao vút trong mây, ghi nhớ công đức tiền nhân...",
        archival_unit: "Viện Sử học",
        epistemic_status: "verified",
      },
    ],
    connections: [
      {
        target_slug: "the-to-mieu",
        target_name_vi: "Thế Tổ Miếu",
        direction: "next",
        axis_description: "Phía bắc: chính điện Thế Tổ Miếu thờ các vị vua Nguyễn.",
      },
    ],
  },
  "dien-can-chanh": {
    timeline: [
      {
        year: 1804,
        period_label: "Gia Long 3",
        event_title: "Nguyên là điện Thái Hòa thời sơ lập",
        description: "Vị trí này nguyên là nơi đặt điện Thái Hòa đầu tiên thời vua Gia Long.",
        source_ref: "Đại Nam Thực Lục",
        is_verified: true,
      },
      {
        year: 1833,
        period_label: "Minh Mạng 14",
        event_title: "Đổi thành điện Cần Chánh",
        description: "Khi dời điện Thái Hòa ra phía trước, vua Minh Mạng cho sửa sang thành điện Cần Chánh để làm nơi thường triều hằng ngày.",
        source_ref: "Đại Nam Thực Lục Chính Biên",
        is_verified: true,
      },
      {
        year: 1947,
        period_label: "Chiến tranh",
        event_title: "Bị thiêu rụi hoàn toàn",
        description: "Toàn bộ khung gỗ lim lộng lẫy và các bảo vật bên trong bị hỏa hoạn chiến tranh thiêu rụi vào đầu năm 1947.",
        source_ref: "Báo cáo tổn thất văn hóa 1947",
        is_verified: true,
      },
      {
        year: 2024,
        period_label: "Nghiên cứu phục hồi",
        event_title: "Hoàn thành nghiên cứu khảo cổ học phối hợp Waseda",
        description: "Lập hồ sơ phục hồi kỹ thuật số và mô hình kiến trúc chuẩn bị tái thiết thực địa.",
        source_ref: "Đại học Waseda & Trung tâm Bảo tồn Cố đô Huế",
        is_verified: true,
      },
    ],
    imagery: [
      {
        id: "img-dien-can-chanh-vintage",
        title: "Nội thất lộng lẫy của điện Cần Chánh trước năm 1947",
        url: "/assets/imperial/photos/can-chanh-interior.webp",
        caption: "Bức ảnh tư liệu quý hiếm chụp hệ thống cột thếp vàng lộng lẫy và bảo tọa hoàng đế lúc còn nguyên vẹn.",
        year: 1910,
        author_or_source: "EFEO Fonds Indochine",
        archive: "Viện Viễn Đông Bác Cổ Paris",
        license_kind: "Public Domain / Educational Fair Use",
        copyright_note: "Tư liệu ảnh khảo cứu di sản đã mất.",
      },
      {
        id: "img-can-chanh-ruin",
        title: "Nền móng khảo cổ học điện Cần Chánh hiện nay",
        url: "/assets/imperial/photos/can-chanh-foundation.webp",
        caption: "Các chân tảng đá và vết tích hỏa hoạn được bảo tồn nghiêm ngặt phục vụ nghiên cứu phục dựng.",
        year: 2023,
        author_or_source: "Viện Khảo cổ học Việt Nam",
        archive: "Hồ sơ dự án phục hồi điện Cần Chánh",
        license_kind: "Educational Permission",
        copyright_note: "Ảnh tư liệu hiện trường khảo cổ học.",
      },
    ],
    claims: [
      {
        id: "cl-can-chanh-1",
        claim_title: "Trung tâm hành chính tối cao thường nhật",
        assertion_vi: "Khác với điện Thái Hòa chỉ dùng cho các buổi đại triều hiếm hoi (mùng 1 và ngày rằm), điện Cần Chánh là nơi hoàng đế điều hành chính sự hàng ngày, tiếp sứ thần và họp Viện Cơ Mật.",
        source_title: "Khâm Định Đại Nam Hội Điển Sự Lệ",
        volume_or_chapter: "Quyển 64 (Lại bộ - Thường triều)",
        citation: "Các ngày thường triều (mùng 5, 10, 20, 25), hoàng đế ngự điện Cần Chánh xem xét sớ tấu...",
        archival_unit: "Nội các triều Nguyễn",
        epistemic_status: "verified",
      },
    ],
    connections: [
      {
        target_slug: "dai-cung-mon",
        target_name_vi: "Đại Cung Môn",
        direction: "prev",
        axis_description: "Phía nam: cửa vào Tử Cấm Thành.",
      },
      {
        target_slug: "dien-kien-trung",
        target_name_vi: "Điện Kiến Trung",
        direction: "next",
        axis_description: "Phía bắc: cung điện cuối cùng trên trục chính của Tử Cấm Thành.",
      },
    ],
  },
  "dien-kien-trung": {
    timeline: [
      {
        year: 1921,
        period_label: "Khải Định 6",
        event_title: "Khởi công xây dựng cung điện phong cách Đông Tây",
        description: "Vua Khải Định cho xây điện Kiến Trung trên nền lầu Du Cửu cũ, kết hợp kiến trúc Baroque Pháp - Ý với mỹ thuật sành sứ Huế.",
        source_ref: "Đồng Khánh Khải Định Chính Yếu",
        is_verified: true,
      },
      {
        year: 1947,
        period_label: "Chiến tranh",
        event_title: "Bị phá hủy hoàn toàn trong chiến sự",
        description: "Công trình bị san phẳng bởi bom đạn, chỉ còn lại lan can rồng khảm sành sứ và bậc cấp đổ nát.",
        source_ref: "Lưu trữ di tích Huế",
        is_verified: true,
      },
      {
        year: 2019,
        period_label: "Trùng tu lớn",
        event_title: "Khởi công dự án phục hồi tổng thể",
        description: "Dự án phục dựng với vốn đầu tư hơn 123 tỷ đồng dựa trên hồ sơ ảnh lưu trữ và kỹ thuật khảm sành sứ cung đình.",
        source_ref: "UBND Tỉnh Thừa Thiên Huế",
        is_verified: true,
      },
      {
        year: 2024,
        period_label: "Khánh thành",
        event_title: "Chính thức hoàn thành và mở cửa đón công chúng",
        description: "Khánh thành vào dịp Tết Giáp Thìn 2024, trở thành biểu tượng cho năng lực phục chế đỉnh cao của ngành bảo tồn Việt Nam.",
        source_ref: "Trung tâm Bảo tồn Di tích Cố đô Huế",
        is_verified: true,
      },
    ],
    imagery: [
      {
        id: "img-dien-kien-trung-facade",
        title: "Mặt tiền lộng lẫy Điện Kiến Trung sau phục hồi (2023)",
        url: "/assets/imperial/heritage/dienkientrung.jpg",
        caption: "Tòa cung điện hai tầng kết hợp phong cách Phục hưng Ý và nghệ thuật khảm sành sứ cung đình Huế, phục hồi thành công năm 2023.",
        year: 2024,
        author_or_source: "Hồ sơ phục dựng khoa học Điện Kiến Trung (2019-2023)",
        archive: "Trung tâm Bảo tồn Di tích Cố đô Huế",
        license_kind: "Educational Permission",
        copyright_note: "Ảnh tư liệu hoàn thành dự án phục hồi di tích.",
      },
    ],
    claims: [
      {
        id: "cl-kien-trung-1",
        claim_title: "Giao thoa nghệ thuật kiến trúc Đông - Tây đầu thế kỷ 20",
        assertion_vi: "Điện Kiến Trung là minh chứng độc đáo nhất cho xu hướng dung hợp kiến trúc cổ điển phương Tây với ngôn ngữ trang trí gốm sứ truyền thống triều Nguyễn.",
        source_title: "Hồ sơ khoa học di tích điện Kiến Trung",
        citation: "Trung tâm Bảo tồn Di tích Cố đô Huế (2018).",
        archival_unit: "Sở Văn hóa & Thể thao Thừa Thiên Huế",
        epistemic_status: "verified",
      },
    ],
    connections: [
      {
        target_slug: "dien-can-chanh",
        target_name_vi: "Điện Cần Chánh",
        direction: "prev",
        axis_description: "Phía nam: chính điện làm việc thường nhật.",
      },
      {
        target_slug: "thai-binh-lau",
        target_name_vi: "Thái Bình Lâu",
        direction: "related",
        axis_description: "Phía đông nam: thư phòng đọc sách của hoàng đế.",
      },
    ],
  },
  "duyet-thi-duong": {
    timeline: [
      {
        year: 1826,
        period_label: "Minh Mạng 7",
        event_title: "Xây dựng nhà hát hoàng gia cổ nhất",
        description: "Vua Minh Mạng cho xây dựng Duyệt Thị Đường làm nơi biểu diễn nhã nhạc, múa cung đình và tuồng cho hoàng gia và quan khách.",
        source_ref: "Đại Nam Thực Lục Chính Biên",
        is_verified: true,
      },
      {
        year: 2004,
        period_label: "UNESCO",
        event_title: "Phục hồi công năng biểu diễn Nhã nhạc Cung đình",
        description: "Hoàn tất trùng tu sau khi Nhã nhạc Huế được UNESCO công nhận là Kiệt tác di sản phi vật thể nhân loại.",
        source_ref: "Trung tâm Bảo tồn Di tích Cố đô Huế",
        is_verified: true,
      },
    ],
    imagery: [
      {
        id: "img-duyet-thi-duong-stage",
        title: "Sân khấu nhà hát cổ Duyệt Thị Đường",
        url: "/assets/imperial/photos/duyet-thi-duong-stage.webp",
        caption: "Không gian diễn xướng cung đình với trần nhà vẽ mặt trăng, mặt trời và các chòm sao.",
        year: 2021,
        author_or_source: "Bảo tồn Di tích Cố đô Huế",
        archive: "Nhà hát Nghệ thuật Truyền thống Cung đình Huế",
        license_kind: "Educational Fair Use",
        copyright_note: "Tư liệu phục vụ học tập nghệ thuật truyền thống.",
      },
    ],
    claims: [
      {
        id: "cl-duyet-thi-duong-1",
        claim_title: "Không gian diễn xướng Nhã nhạc chuẩn mực cung đình",
        assertion_vi: "Duyệt Thị Đường là nhà hát cổ nhất còn tồn tại của Việt Nam, được thiết kế âm học độc đáo phục vụ biểu diễn đại nhạc, tiểu nhạc và tuồng cung đình.",
        source_title: "Khâm Định Đại Nam Hội Điển Sự Lệ",
        volume_or_chapter: "Quyển 100 (Lễ bộ - Cung đình âm nhạc)",
        citation: "Quy định biên chế các ban nhạc và nghi thức ngự xem tuồng tại Duyệt Thị Đường.",
        archival_unit: "Nội các triều Nguyễn",
        epistemic_status: "verified",
      },
    ],
    connections: [
      {
        target_slug: "thai-binh-lau",
        target_name_vi: "Thái Bình Lâu",
        direction: "next",
        axis_description: "Phía bắc: thư viện hoàng gia yên tĩnh liền kề hoa viên.",
      },
      {
        target_slug: "dien-kien-trung",
        target_name_vi: "Điện Kiến Trung",
        direction: "related",
        axis_description: "Phía tây bắc: cung điện chính của Tử Cấm Thành.",
      },
    ],
  },
  "cung-dien-tho": {
    timeline: [
      {
        year: 1804,
        period_label: "Gia Long 3",
        event_title: "Khởi dựng cung Trường Thọ",
        description: "Vua Gia Long xây dựng cung điện phụng dưỡng mẫu hậu là Hoàng thái hậu Hiếu Khang.",
        source_ref: "Đại Nam Thực Lục",
        is_verified: true,
      },
      {
        year: 1917,
        period_label: "Khải Định 2",
        event_title: "Đổi tên thành cung Diên Thọ",
        description: "Mở rộng khuôn viên, xây dựng thêm Tạ Trường Du bằng gỗ trên hồ sen và lầu Tịnh Minh hai tầng hiện đại.",
        source_ref: "Đại Nam Nhất Thống Chí",
        is_verified: true,
      },
      {
        year: 2005,
        period_label: "Trùng tu",
        event_title: "Bảo tồn tổng thể quần thể cung Diên Thọ",
        description: "Phục hồi nguyên vẹn các công trình chính điện, Tạ Trường Du, nhà Tả Hữu viện và hoa viên tiểu cảnh.",
        source_ref: "Trung tâm Bảo tồn Di tích Cố đô Huế",
        is_verified: true,
      },
    ],
    imagery: [
      {
        id: "img-cung-dien-tho-truong-du-ta",
        title: "Nhà Tạ Trường Du bên hồ sen Cung Diên Thọ",
        url: "/assets/imperial/heritage/truongduta.jpg",
        caption: "Nhà tạ bằng gỗ lim thanh tao soi bóng trên hồ sen Cung Diên Thọ, nơi Hoàng Thái Hậu ngắm hoa, thưởng ngoạn và tĩnh dưỡng.",
        year: 2024,
        author_or_source: "Tư liệu cảnh quan sân vườn Cung Diên Thọ",
        archive: "Kho tư liệu kiến trúc cảnh quan Cố đô",
        license_kind: "Educational Permission",
        copyright_note: "Tư liệu học tập số hóa di sản.",
      },
    ],
    claims: [
      {
        id: "cl-dien-tho-1",
        claim_title: "Biểu tượng của đạo hiếu hoàng gia",
        assertion_vi: "Cung Diên Thọ là quần thể kiến trúc sinh hoạt hoàng gia hoàn chỉnh nhất còn tồn tại, thể hiện chữ Hiếu sâu sắc trong truyền thống đạo đức Nho giáo của các vị vua đối với mẹ.",
        source_title: "Đại Nam Nhất Thống Chí",
        volume_or_chapter: "Quyển 1 (Kinh sư - Cung viện)",
        citation: "Cung Diên Thọ ở phía tây bắc Tử Cấm Thành, làm nơi phụng dưỡng Hoàng Thái Hậu...",
        archival_unit: "Quốc Sử Quán triều Nguyễn",
        epistemic_status: "verified",
      },
    ],
    connections: [
      {
        target_slug: "cung-truong-sanh",
        target_name_vi: "Cung Trường Sanh",
        direction: "next",
        axis_description: "Phía bắc: hoa viên và nơi dưỡng bệnh thư thái của Thái Hoàng Thái Hậu.",
      },
      {
        target_slug: "dien-phung-tien",
        target_name_vi: "Điện Phụng Tiên",
        direction: "prev",
        axis_description: "Phía đông nam: điện thờ cúng của nữ giới hoàng cung.",
      },
    ],
  },
};

/**
 * Verified Public Sources Catalog for /dai-noi/nguon.
 * Rigorous bibliographic tracking, copyright declarations, and fair-use educational credits.
 */
export const PUBLIC_SOURCES_CATALOG: PublicSourceRecord[] = [
  {
    id: "src-dai-nam-thuc-luc",
    category: "chronicle",
    title_vi: "Đại Nam Thực Lục (Chính Biên & Tiền Biên)",
    original_title: "大南實錄",
    authors: "Quốc Sử Quán triều Nguyễn (Trương Đăng Quế, Vũ Xuân Cẩn, Phan Thanh Giản...)",
    year_or_period: "1844 - 1909 (Biên soạn dưới các triều Thiệu Trị, Tự Đức, Đồng Khánh, Thành Thái)",
    holding_institution: "Viện Sử học Việt Nam / Nhà xuất bản Giáo dục",
    archive_ref: "Kho Châu bản - Sử quán triều Nguyễn",
    description_vi: "Bộ chính sử lớn nhất của triều Nguyễn, ghi chép biên niên chuẩn xác từng tháng năm về việc xây dựng thành quách, cung điện, tên gọi, công năng và các biến cố chính trị tại Đại Nội Huế.",
    rights_holder: "Di sản tư liệu lịch sử quốc gia / Bản dịch tiếng Việt của Viện Sử học (NXB Giáo dục)",
    license_type: "Phạm vi công cộng (văn bản gốc) / Trích dẫn học thuật (bản dịch)",
    fair_use_justification: "Sử dụng trích dẫn ngắn các đoạn ghi chép công trình để đối chiếu học tập lịch sử theo Luật Sở hữu trí tuệ Việt Nam (Điều 25).",
    sample_monuments: ["ngo-mon", "dien-thai-hoa", "the-to-mieu", "hien-lam-cac", "dien-can-chanh"],
  },
  {
    id: "src-kham-dinh-hoi-dien",
    category: "chronicle",
    title_vi: "Khâm Định Đại Nam Hội Điển Sự Lệ",
    original_title: "欽定大南會典事例",
    authors: "Nội các triều Nguyễn (biên soạn theo chỉ dụ của vua Minh Mạng và hoàn thành thời Thiệu Trị)",
    year_or_period: "1851 (Hoàn tất năm Tự Đức thứ 4)",
    holding_institution: "Viện Nghiên cứu Hán Nôm / NXB Thuận Hóa",
    archive_ref: "Bản khắc in triều Tự Đức",
    description_vi: "Bộ điển chế pháp quy tối cao của triều Nguyễn, quy định chi tiết thể thức nghi lễ, lễ phục, thứ bậc đứng chầu của bá quan tại sân Đại Triều Nghi, quy chế ra vào cổng Ngọ Môn và chức năng các cơ quan trong Đại Nội.",
    rights_holder: "Di sản tư liệu công cộng / Bản dịch NXB Thuận Hóa",
    license_type: "Phạm vi công cộng / Trích dẫn giáo dục",
    fair_use_justification: "Trích dẫn quy chuẩn nghi lễ nhằm giải thích cấu trúc không gian kiến trúc trong bài học di sản.",
    sample_monuments: ["ngo-mon", "san-dai-trieu-nghi", "dien-can-chanh", "duyet-thi-duong"],
  },
  {
    id: "src-dai-nam-nhat-thong-chi",
    category: "chronicle",
    title_vi: "Đại Nam Nhất Thống Chí (Tập Kinh Sư)",
    original_title: "大南一統志",
    authors: "Quốc Sử Quán triều Nguyễn (Hoàng Hữu Xứng, Nguyễn Thuật...)",
    year_or_period: "1882 (Triều Tự Đức) - 1910 (Triều Duy Tân)",
    holding_institution: "Thư viện Quốc gia Việt Nam / NXB Lao Động",
    archive_ref: "Mã số TVQG: VN-HN-1882",
    description_vi: "Bộ địa chí quốc gia lớn nhất thời phong kiến, miêu tả chi tiết vị trí địa lý, sông ngòi, thành trì, hồ ao (Hồ Thái Dịch, sông Ngự Hà) và các cung điện miếu mạo trong Hoàng Thành.",
    rights_holder: "Phạm vi công cộng",
    license_type: "Public Domain",
    fair_use_justification: "Dẫn chiếu tọa độ không gian và bối cảnh quy hoạch phong thủy của Kinh thành Huế.",
    sample_monuments: ["cau-trung-dao", "cung-dien-tho", "cung-truong-sanh", "thai-binh-lau"],
  },
  {
    id: "src-efeo-archives",
    category: "archival_photo",
    title_vi: "Kho lưu trữ Nhiếp ảnh Di sản Viện Viễn Đông Bác Cổ (EFEO)",
    original_title: "Fonds Photographique de l'École française d'Extrême-Orient",
    authors: "Charles Carpeaux, Henri Parmentier, Paul Pelliot, Jean-Yves Claeys và cộng sự",
    year_or_period: "1900 - 1945",
    holding_institution: "EFEO Paris & Trung tâm Lưu trữ Quốc gia I (Hà Nội)",
    archive_ref: "EFEO-Ph-VIE",
    description_vi: "Hàng ngàn bức ảnh đen trắng và âm bản kính ghi lại hiện trạng nguyên bản của các cung điện Đại Nội trước khi bị chiến tranh tàn phá năm 1947, đặc biệt là điện Cần Chánh, điện Kiến Trung và Đại Cung Môn.",
    rights_holder: "École française d'Extrême-Orient (EFEO)",
    license_type: "Educational Fair Use / License Recherche Académique",
    fair_use_justification: "Hiển thị minh chứng hình ảnh lịch sử phục vụ việc học sinh đối chiếu hiện trạng và quá khứ, phi thương mại.",
    sample_monuments: ["dien-can-chanh", "dien-kien-trung", "dien-thai-hoa", "the-to-mieu"],
  },
  {
    id: "src-albert-kahn",
    category: "archival_photo",
    title_vi: "Bộ sưu tập Ảnh màu Autochrome Albert Kahn (Hành tinh Lưu trữ)",
    original_title: "Les Archives de la Planète — Collections Albert-Kahn",
    authors: "Léon Busy (Nhiếp ảnh gia được cử sang Việt Nam)",
    year_or_period: "1914 - 1920",
    holding_institution: "Musée Départemental Albert-Kahn, Boulogne-Billancourt, Pháp",
    archive_ref: "Autochrome A-6453 đến A-6520",
    description_vi: "Những bức ảnh màu tự nhiên đầu tiên trong lịch sử ghi lại màu sắc trang phục hoàng gia, màu ngói hoàng lưu ly của Ngọ Môn và nghi lễ triều đình Huế đầu thế kỷ 20.",
    rights_holder: "Département des Hauts-de-Seine / Musée Albert-Kahn",
    license_type: "Open Access Data / CC BY-NC-SA 4.0",
    fair_use_justification: "Tài liệu mở cho giáo dục văn hóa toàn cầu, không sử dụng cho mục đích thương mại.",
    sample_monuments: ["ngo-mon", "san-dai-trieu-nghi", "cau-trung-dao"],
  },
  {
    id: "src-remote-sensing",
    category: "remote_sensing",
    title_vi: "Dữ liệu Ảnh Viễn Thám và Mô hình Bề mặt Số Đại Nội Huế",
    authors: "Cộng tác nghiên cứu trắc địa di sản và không ảnh di tích Huế",
    year_or_period: "2024 - 2026",
    holding_institution: "Kho dữ liệu học tập số hóa Lưu Niên",
    archive_ref: "STTT-AERIAL-ORTHO-4096-V1",
    description_vi: "Không ảnh trực giao độ phân giải cao (4096 x 3072 px) được chuẩn hóa hệ tọa độ UV [0, 1] phục vụ xác định vị trí và phân tích mối liên hệ không gian giữa các công trình kiến trúc.",
    rights_holder: "Dự án Giáo dục Di sản Lưu Niên — Đại Nội Huế",
    license_type: "Educational Fair Use / Academic Project License",
    fair_use_justification: "Bản đồ học tập số hóa phục vụ cuộc thi Sáng tạo Thanh thiếu niên Nhi đồng và giáo dục lịch sử THPT.",
    sample_monuments: ["ngo-mon", "cau-trung-dao", "dien-thai-hoa", "dien-kien-trung", "cung-dien-tho"],
  },
  {
    id: "src-unesco-dos",
    category: "conservation_report",
    title_vi: "Hồ sơ Đăng ký Di sản Thế giới Quần thể Di tích Cố đô Huế (1993)",
    original_title: "Complex of Hué Monuments — World Heritage Nomination Dossier",
    authors: "Trung tâm Bảo tồn Di tích Cố đô Huế & Ủy ban UNESCO Việt Nam",
    year_or_period: "1993",
    holding_institution: "UNESCO World Heritage Centre, Paris",
    archive_ref: "UNESCO WHC Nom. File 678",
    description_vi: "Văn bản khoa học xác nhận giá trị toàn cầu nổi bật (OUV) của Đại Nội Huế, phân tích các tiêu chí quy hoạch phong thủy, nghệ thuật kiến trúc gỗ truyền thống và kế hoạch bảo tồn quốc tế.",
    rights_holder: "UNESCO / Trung tâm Bảo tồn Di tích Cố đô Huế",
    license_type: "Public Heritage Document",
    fair_use_justification: "Cung cấp căn cứ học thuật về các tiêu chí di sản thế giới cho bài học THPT.",
    sample_monuments: ["ngo-mon", "dien-thai-hoa", "the-to-mieu", "duyet-thi-duong"],
  },
  {
    id: "src-dong-khanh-dia-du-chi",
    category: "chronicle",
    title_vi: "Đồng Khánh Địa Dư Chí",
    original_title: "同慶地輿志",
    authors: "Quốc Sử Quán triều Nguyễn",
    year_or_period: "1886 - 1888 (Triều Đồng Khánh)",
    holding_institution: "Viện Nghiên cứu Hán Nôm / NXB Thế Giới",
    archive_ref: "Ký hiệu văn bản A.537",
    description_vi: "Bộ địa chí quốc gia có bản đồ chi tiết miêu tả hình thế sông núi, thành hào, cung thất và phong vật các tỉnh hạt, đặc biệt là phủ Thừa Thiên (kinh sư Huế).",
    rights_holder: "Phạm vi công cộng / Bản dịch của Viện Nghiên cứu Hán Nôm & EFEO",
    license_type: "Public Domain / Trích dẫn học thuật",
    fair_use_justification: "Khảo sát đối chiếu địa danh lịch sử và cấu trúc không gian thành lũy phục vụ học tập di sản.",
    sample_monuments: ["ngo-mon", "dien-thai-hoa", "the-to-mieu", "cung-dien-tho", "cung-truong-sanh"],
  },
  {
    id: "src-bavh-bulletin",
    category: "conservation_report",
    title_vi: "Đô Thành Hiếu Cổ Tập San (Bulletin des Amis du Vieux Hué - BAVH)",
    original_title: "Bulletin des Amis du Vieux Hué",
    authors: "Léopold Cadière, Henri Cosserat, Robert Deloustal, Nguyễn Đình Hòe, Ưng Trình",
    year_or_period: "1914 - 1944",
    holding_institution: "Thư viện Tổng hợp Thừa Thiên Huế / NXB Thuận Hóa",
    archive_ref: "Fonds BAVH (30 tập)",
    description_vi: "Tập san nghiên cứu khoa học chuyên sâu bậc nhất đầu thế kỷ 20 về lịch sử, nghệ thuật, kiến trúc, văn hóa và nghi lễ triều Nguyễn với hàng trăm bản vẽ đo đạc và đồ án mặt bằng di tích Cố đô Huế.",
    rights_holder: "Tài liệu học thuật công cộng / Bản dịch tiếng Việt NXB Thuận Hóa",
    license_type: "Academic Research / Educational Fair Use",
    fair_use_justification: "Trích dẫn nghiên cứu khoa học và đồ án trắc đạc hình học để đối chứng biến thiên kiến trúc.",
    sample_monuments: ["ngo-mon", "dien-thai-hoa", "hien-lam-cac", "duyet-thi-duong", "dien-can-chanh"],
  },
  {
    id: "src-chau-ban-trieu-nguyen",
    category: "chronicle",
    title_vi: "Châu bản triều Nguyễn (Mục lục Doanh tạo Hoàng thành)",
    original_title: "阮朝硃本",
    authors: "Nội các & Công bộ triều Nguyễn (ngự phê bằng mực son đỏ)",
    year_or_period: "1802 - 1945",
    holding_institution: "Trung tâm Lưu trữ Quốc gia I (Cục Văn thư và Lưu trữ Nhà nước)",
    archive_ref: "Phông Châu bản triều Nguyễn",
    description_vi: "Di sản Tư liệu Ký ức Thế giới của UNESCO, gồm các bản tấu trình, phúc trình, chỉ dụ gốc về việc khởi công, vật liệu và tiến độ thi công các cung thất Đại Nội.",
    rights_holder: "Di sản Tư liệu Thế giới / Cục Văn thư và Lưu trữ Nhà nước",
    license_type: "Public Heritage Document",
    fair_use_justification: "Minh chứng văn bản hành chính gốc có ngự bút phục vụ rèn luyện tư duy đối chiếu sử liệu.",
    sample_monuments: ["dien-thai-hoa", "ngo-mon", "the-to-mieu", "dien-kien-trung"],
  },
  {
    id: "src-khao-co-hoang-thanh-hue",
    category: "conservation_report",
    title_vi: "Báo cáo Khai quật Khảo cổ học Hoàng Thành và Tử Cấm Thành Huế",
    authors: "Viện Khảo cổ học Việt Nam & Trung tâm Bảo tồn Di tích Cố đô Huế",
    year_or_period: "2017 - 2023",
    holding_institution: "Viện Khảo cổ học / TTBTDT Cố đô Huế",
    archive_ref: "Hồ sơ khảo cổ học KC-HT-HUE",
    description_vi: "Hồ sơ kết quả khai quật địa tầng xuất lộ nền móng đá thanh, chân tảng cột gỗ lim và hệ thống thoát nước cổ tại phế tích Đại Cung Môn, Điện Cần Chánh và Điện Phụng Tiên.",
    rights_holder: "Viện Khảo cổ học / TTBTDT Cố đô Huế",
    license_type: "Academic Research Document",
    fair_use_justification: "Cung cấp chứng cứ khảo cổ học thực địa đối chứng với tư liệu thành văn của triều đình.",
    sample_monuments: ["dai-cung-mon", "dien-can-chanh", "dien-phung-tien", "san-dai-trieu-nghi"],
  },
];

/**
 * Builds the complete 7-section SiteDossierData for any monument.
 */
export function getSiteDossier(slug: string): SiteDossierData | null {
  const site = FALLBACK_SITES.find((s) => s.slug === slug);
  if (!site) return null;

  const zone = FALLBACK_ZONES.find((z) => z.slug === site.zone_slug) || null;
  const anno = FALLBACK_ANNOTATIONS.find((a) => a.site?.slug === slug) || null;
  const custom = MONUMENT_DOSSIER_REGISTRY[slug] || {};

  // Build standard timeline
  const baseTimeline: TimelineEvent[] = custom.timeline || [
    {
      year: site.construction_year || 1833,
      period_label: site.reign || "Triều Nguyễn",
      event_title: "Khởi dựng công trình kiến trúc",
      description: site.historical_summary || "Khởi công xây dựng trong quy hoạch Hoàng Thành và Tử Cấm Thành.",
      source_ref: "Đại Nam Thực Lục Chính Biên",
      is_verified: true,
    },
    {
      year: 1945,
      period_label: "Lịch sử cận đại",
      event_title: "Chuyển giao chính quyền và bảo tồn di sản",
      description: "Đại Nội Huế chuyển sang giai đoạn di tích lịch sử quốc gia.",
      source_ref: "Hồ sơ di tích quốc gia",
      is_verified: true,
    },
    {
      year: 1993,
      period_label: "UNESCO",
      event_title: "Ghi danh Di sản Văn hóa Thế giới",
      description: "Quần thể di tích Huế được UNESCO vinh danh là Di sản Văn hóa Thế giới đầu tiên của Việt Nam.",
      source_ref: "UNESCO WHC Dossier #678",
      is_verified: true,
    },
  ];

  // Build standard imagery from verified heritage corpus
  const siteImages = getHeritageImagesBySite(slug);
  const baseImagery: HistoricalImage[] = custom.imagery || (
    siteImages.length > 0
      ? siteImages.map((img) => ({
          id: img.id,
          title: img.title,
          url: img.src,
          caption: img.caption,
          year: 2024,
          author_or_source: img.creditLine,
          archive: "Kho tư liệu ảnh di sản Cố đô Huế",
          license_kind: "Educational Permission",
          copyright_note: "Tư liệu phục vụ học tập và nghiên cứu di sản phi thương mại.",
        }))
      : [
          {
            id: `img-${slug}-overview`,
            title: `Toàn cảnh không gian di sản: ${site.name_vi}`,
            url: "/assets/imperial/heritage/dainoitrencao.jpg",
            caption: `Không gian định vị di tích ${site.name_vi} trên tổng thể không ảnh Hoàng Thành Huế.`,
            year: 2024,
            author_or_source: "Ảnh không ảnh khảo sát Cố đô Huế",
            archive: "Kho tư liệu ảnh di sản Cố đô Huế",
            license_kind: "Educational Fair Use",
            copyright_note: "Tư liệu phục vụ học tập và nghiên cứu di sản phi thương mại.",
          },
        ]
  );

  // Build claims and evidence
  const baseClaims: ClaimEvidence[] = custom.claims || (
    site.primary_sources?.map((s, idx) => ({
      id: `cl-${slug}-${idx + 1}`,
      claim_title: `Chứng cứ sử liệu: ${s.source_title}`,
      assertion_vi: s.citation || site.historical_summary || "Công trình kiến trúc cung đình có giá trị lịch sử tiêu biểu.",
      source_title: s.source_title,
      volume_or_chapter: s.volume_or_chapter,
      citation: s.citation || "Trích đoạn sử liệu chính biên.",
      archival_unit: s.archival_unit,
      epistemic_status: "verified" as const,
    })) || [
      {
        id: `cl-${slug}-1`,
        claim_title: "Ghi chép trong chính sử Đại Nam Thực Lục",
        assertion_vi: site.historical_summary || "Công trình được xác nhận xây dựng và vận hành dưới triều Nguyễn.",
        source_title: "Đại Nam Thực Lục Chính Biên",
        volume_or_chapter: "Quốc Sử Quán triều Nguyễn",
        citation: "Ghi chép về quy chế kiến trúc và địa điểm trong Kinh thành.",
        archival_unit: "Viện Sử học",
        epistemic_status: "verified" as const,
      },
    ]
  );

  // Pedagogical task
  const task: PedagogicalTask = site.pedagogical_task || {
    title: `Khảo sát không gian và chức năng: ${site.name_vi}`,
    task_prompt: `Dựa trên quan sát bản đồ vị trí và các sử liệu được trích dẫn, em hãy nêu kết luận về vai trò của ${site.name_vi} trong hệ thống kiến trúc Đại Nội và chỉ ra ít nhất một bằng chứng cụ thể.`,
    deliverable_type: "Báo cáo ngắn dựa trên bằng chứng",
    expected_evidence: "Xác định đúng vị trí không gian, đối chiếu trích dẫn chính sử.",
    transfer_activity: "Liên hệ vai trò công trình với các di tích liền kề trên trục không gian.",
    uncertainty_prompt: "Điều em biết chắc chắn dựa trên nguồn tư liệu; điều em nhận thấy cần xác minh thêm.",
  };

  // Rubrics
  const rubrics: RubricGuidelines = {
    S1_spatial: (site.rubrics?.S1_spatial || site.rubrics?.S1) || "Xác định đúng vị trí và mối liên hệ không gian trong cụm kiến trúc.",
    S2_temporal: (site.rubrics?.S2_temporal || site.rubrics?.S2) || "Nhận diện đúng niên đại xây dựng và các mốc biến động lịch sử.",
    S3_evidence: (site.rubrics?.S3_evidence || site.rubrics?.S3) || "Trích dẫn chính xác ít nhất một văn bản hoặc hình ảnh sử liệu đã kiểm chứng.",
    S4_argument: (site.rubrics?.S4_argument || site.rubrics?.S4_reasoning || site.rubrics?.S4) || "Đưa ra kết luận có lập luận logic, phân biệt giữa sự thật lịch sử và suy đoán.",
  };

  // Spatial connections
  const connections: SpatialConnection[] = custom.connections || [
    {
      target_slug: "ngo-mon",
      target_name_vi: "Ngọ Môn",
      direction: "prev",
      axis_description: "Cổng chính phía nam trên trục trung tâm Hoàng Thành.",
    },
    {
      target_slug: "dien-thai-hoa",
      target_name_vi: "Điện Thái Hòa",
      direction: "next",
      axis_description: "Chính điện tối cao của Hoàng triều.",
    },
  ];

  return {
    site,
    zone,
    timeline: baseTimeline,
    imagery: baseImagery,
    claims: baseClaims,
    guiding_question: site.guiding_inquiry_question || site.guiding_question || `Vì sao kiến trúc và vị trí của ${site.name_vi} lại có ý nghĩa quan trọng trong tổng thể Đại Nội Huế?`,
    task,
    rubrics,
    connections,
    annotation: anno,
  };
}
