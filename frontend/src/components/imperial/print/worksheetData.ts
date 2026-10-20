import { PrintableStation, RubricDimensionItem, ExitTicketQuestion } from "./types";
import zonesAndSites from "../../../../../data/imperial/zones_and_sites.json";
import fieldworkData from "../../../../../data/imperial/fieldwork_worksheet.json";

interface RawSiteSource {
  source_title: string;
  volume_or_chapter?: string;
  citation: string;
  archival_unit?: string;
  reliability_level?: string;
}

interface RawSite {
  id: string;
  slug: string;
  zone_slug: string;
  name_vi: string;
  name_en?: string;
  construction_year?: number;
  reign?: string;
  condition_description_vi?: string;
  historical_summary?: string;
  guiding_inquiry_question?: string;
  primary_sources?: RawSiteSource[];
  pedagogical_task?: {
    title?: string;
    task_prompt?: string;
    expected_evidence?: string;
    uncertainty_prompt?: string;
  };
  rubrics?: {
    S1_spatial?: string;
    S2_temporal?: string;
    S3_evidence?: string;
    S4_argument?: string;
  };
}

const ZONE_NAME_MAP: Record<string, string> = {
  "central-ceremonial-axis": "Trục nghi lễ trung tâm (Central Ceremonial Axis)",
  "ancestral-worship-space": "Không gian thờ tự tổ tiên (Ancestral Worship Space)",
  "purple-forbidden-city": "Tử Cấm Thành hoàng gia (Purple Forbidden City)",
  "royal-living-gardens": "Khu sinh hoạt & Ngự uyển (Royal Living & Gardens)",
};

// 16 monuments comprehensively formatted for fieldwork printing
export const ALL_16_PRINTABLE_STATIONS: PrintableStation[] = (
  zonesAndSites.sites as unknown as RawSite[]
).map((site, index) => {
  const zoneName = ZONE_NAME_MAP[site.zone_slug] || "Khu vực Hoàng Thành";
  const firstSource = site.primary_sources?.[0] || {
    source_title: "Đại Nam Thực Lục Chính Biên",
    volume_or_chapter: "Quốc Sử Quán triều Nguyễn",
    citation: "Tư liệu lưu trữ Quốc Sử Quán và Nội các triều Nguyễn.",
  };

  // Check if site is one of the 4 stations in fieldworkData for exact curated wording
  const curated = (fieldworkData.stations as Array<{
    monument_slug: string;
    observation_prompt_vi: string;
    guiding_source: { source_title: string; volume: string; key_quote_vi: string };
    conclusion_guide_vi: string;
  }>).find((s) => s.monument_slug === site.slug);

  const observationPrompt =
    curated?.observation_prompt_vi ||
    site.pedagogical_task?.task_prompt ||
    `Quan sát kiến trúc mặt tiền, số tầng nền, bậc cấp, vật liệu gỗ - đá và tình trạng bảo tồn hiện tại của ${site.name_vi}.`;

  const observationSample =
    site.condition_description_vi
      ? `${site.condition_description_vi}. ${site.historical_summary?.slice(0, 160)}...`
      : `Công trình mang phong cách cung đình triều ${site.reign || "Nguyễn"}, khởi dựng năm ${site.construction_year || "1804-1833"}.`;

  const primaryCitation = curated?.guiding_source
    ? {
        source_title: curated.guiding_source.source_title,
        volume_or_chapter: curated.guiding_source.volume,
        citation: curated.guiding_source.key_quote_vi,
      }
    : firstSource;

  // Split uncertainty prompt into claim and uncertainty
  const uncertainty = site.pedagogical_task?.uncertainty_prompt || curated?.conclusion_guide_vi || "";
  let claimSample = `${site.name_vi} phản ánh tập quyền tuyệt đối và quy thức lễ nghi triều Nguyễn.`;
  let evidenceSample = `Đối chiếu với ${primaryCitation.source_title} (${primaryCitation.volume_or_chapter || ""}).`;
  let uncertaintySample = "Cần kiểm chứng thêm sự thay đổi vật liệu qua các thời kỳ tu sửa cận đại.";

  if (uncertainty.includes("Điều") && uncertainty.includes("Điều cần")) {
    const parts = uncertainty.split("Điều cần");
    claimSample = parts[0]?.replace(/^Điều\s*(em)?\s*(biết)?\s*chắc:?\s*/i, "").trim() || claimSample;
    uncertaintySample = (parts[1] || "").replace(/^(kiểm chứng|xác minh):?\s*/i, "").trim() || uncertaintySample;
    if (site.pedagogical_task?.expected_evidence) {
      evidenceSample = site.pedagogical_task.expected_evidence;
    }
  }

  return {
    station_index: index + 1,
    monument_slug: site.slug,
    monument_name_vi: site.name_vi,
    zone_name_vi: zoneName,
    zone_slug: site.zone_slug,
    reign: site.reign,
    construction_year: site.construction_year,
    condition_description_vi: site.condition_description_vi,
    observation_prompt_vi: observationPrompt,
    observation_sample_answer_vi: observationSample,
    primary_source: {
      source_title: primaryCitation.source_title,
      volume_or_chapter: primaryCitation.volume_or_chapter,
      citation: primaryCitation.citation,
    },
    conclusion_guide_vi:
      curated?.conclusion_guide_vi ||
      site.pedagogical_task?.uncertainty_prompt ||
      "Phân định rõ ràng: (1) Điều khẳng định chắc chắn; (2) Giới hạn tư liệu cần kiểm chứng thêm.",
    mee_claim_sample_vi: claimSample,
    mee_evidence_sample_vi: evidenceSample,
    mee_uncertainty_sample_vi: uncertaintySample,
    digital_coordinate_hint: `/dai-noi/cong-trinh/${site.slug}`,
  };
});

// The 4 core standard stations matching fieldwork_worksheet.json
export const STANDARD_4_STATIONS_SLUGS = [
  "ngo-mon",
  "dien-thai-hoa",
  "hien-lam-cac",
  "cung-dien-tho",
];

export const STATION_CLUSTERS = [
  {
    id: "standard_4",
    title_vi: "Hành trình trọng điểm (4 trạm chuẩn 45 phút)",
    description_vi: "Ngọ Môn ➔ Điện Thái Hòa ➔ Hiển Lâm Các ➔ Cung Diên Thọ",
    slugs: STANDARD_4_STATIONS_SLUGS,
  },
  {
    id: "all_16",
    title_vi: "Toàn bộ 16 di tích Hoàng Thành Huế",
    description_vi: "Khảo sát toàn diện mọi trạm trên bản đồ trực giao",
    slugs: ALL_16_PRINTABLE_STATIONS.map((s) => s.monument_slug),
  },
  {
    id: "central_axis",
    title_vi: "Cụm Trục trung tâm (4 công trình)",
    description_vi: "Ngọ Môn, Cầu Trung Đạo, Sân Đại Triều Nghi, Điện Thái Hòa",
    slugs: ["ngo-mon", "cau-trung-dao", "san-dai-trieu-nghi", "dien-thai-hoa"],
  },
  {
    id: "ancestral_space",
    title_vi: "Cụm Không gian thờ tự (5 công trình)",
    description_vi: "Thế Tổ Miếu, Hiển Lâm Các, Hưng Tổ Miếu, Triệu Tổ Miếu, Điện Phụng Tiên",
    slugs: ["the-to-mieu", "hien-lam-cac", "hung-to-mieu", "trieu-to-mieu", "dien-phung-tien"],
  },
  {
    id: "purple_forbidden",
    title_vi: "Cụm Tử Cấm Thành (5 công trình)",
    description_vi: "Đại Cung Môn, Điện Cần Chánh, Điện Kiến Trung, Duyệt Thị Đường, Thái Bình Lâu",
    slugs: ["dai-cung-mon", "dien-can-chanh", "dien-kien-trung", "duyet-thi-duong", "thai-binh-lau"],
  },
  {
    id: "royal_living",
    title_vi: "Cụm Không gian sinh hoạt hoàng gia (2 công trình)",
    description_vi: "Cung Diên Thọ, Cung Trường Sanh",
    slugs: ["cung-dien-tho", "cung-truong-sanh"],
  },
];

export const RUBRIC_DIMENSIONS: RubricDimensionItem[] = [
  {
    id: "S1",
    name_vi: "Năng lực Không gian (Spatial Reasoning)",
    dimension: "Địa lý lịch sử",
    description_vi: "Xác định chuẩn xác tọa độ, trục Thần đạo, phân khu chức năng trên bản đồ trực giao.",
    max_score: 3,
  },
  {
    id: "S2",
    name_vi: "Năng lực Thời gian (Chronological Thinking)",
    dimension: "Tiến trình lịch sử",
    description_vi: "Nêu đúng mốc khởi dựng, niên hiệu hoàng đế, phân biệt công trình gốc vs đại trùng tu.",
    max_score: 3,
  },
  {
    id: "S3",
    name_vi: "Năng lực Sử liệu (Historical Evidence Analysis)",
    dimension: "Phê phán sử liệu",
    description_vi: "Dẫn đúng bộ sử (ĐNTL, Hội Điển Sự Lệ), số quyển, câu trích chứng minh trực tiếp.",
    max_score: 3,
  },
  {
    id: "S4",
    name_vi: "Năng lực Lập luận (Argumentation - M-E-E)",
    dimension: "Tư duy phản biện",
    description_vi: "Rút ra mệnh đề sắc bén, phân định rõ ràng giữa điều chắc chắn và điều cần kiểm chứng thêm.",
    max_score: 3,
  },
];

export const EXIT_TICKET_QUESTIONS: ExitTicketQuestion[] = [
  {
    id: "et_q1",
    question_vi:
      "Hãy chọn một cặp công trình có quan hệ không gian trực tiếp (ví dụ: Ngọ Môn - Sân Đại Triều, hoặc Hiển Lâm Các - Thế Miếu) và giải thích mối liên kết công năng giữa chúng.",
    space_for_answer_lines: 3,
    sample_answer_vi:
      "Ví dụ: Ngọ Môn và Sân Đại Triều Nghi liên kết trực tiếp qua cầu Trung Đạo và hồ Thái Dịch. Ngọ Môn là cửa ngõ kiểm soát nghi lễ phân luồng, khi vua lên lầu Ngũ Phụng phát lệnh, quan viên đã tề tựu trật tự theo phẩm trật trên hai tầng sân trước điện Thái Hòa, tạo nên trục quyền lực thiêng liêng và tôn ti trật tự tuyệt đối.",
  },
  {
    id: "et_q2",
    question_vi:
      "Nêu một điều em phát hiện chắc chắn dựa trên tư liệu sử học và một điều em nhận thấy còn cần tiếp tục nghiên cứu, kiểm chứng tại di tích.",
    space_for_answer_lines: 3,
    sample_answer_vi:
      "Điều biết chắc: Quy chế phân luồng 5 cửa Ngọ Môn và phân hàng quan văn tả - võ hữu tại sân Đại Triều đã được ghi chép tường minh trong Đại Nam Thực Lục và Hội Điển. Điều cần kiểm chứng thêm: Các lớp vật liệu lợp ngói và chi tiết mộng gỗ qua các đợt hạ giải phục dựng sau chiến tranh 1968.",
  },
];
