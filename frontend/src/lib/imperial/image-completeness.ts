/**
 * Image Completeness & Gap Registry for STTTNNĐ (Lưu Niên — Đại Nội Huế).
 * Ref: Spec Patch V2.2 & V2.3
 *
 * Implements strict image completeness evaluation across all 16 monuments in Đại Nội Huế.
 * Enforces the core rule:
 * - Never assign wrong images to the wrong architecture/site.
 * - Never invent fake architecture visuals.
 * - Accurately flag missing image categories and provide structured calls to action.
 */

import { HERITAGE_IMAGES } from "./heritage-images";
import { FALLBACK_SITES, FALLBACK_ZONES } from "./fallback-data";

export type ImageCompletenessStatus = "complete" | "partial" | "missing";

export interface CategoryCompleteness {
  label: string;
  available: boolean;
  count: number;
  neededDescription: string;
}

export interface SiteImageCompleteness {
  siteSlug: string;
  siteNameVi: string;
  siteNameHanNom?: string;
  zoneSlug: string;
  zoneTitle: string;
  condition: string;
  status: ImageCompletenessStatus;
  totalImages: number;
  coveragePercent: number;
  availableImages: typeof HERITAGE_IMAGES;
  categories: {
    facade: CategoryCompleteness;
    interior: CategoryCompleteness;
    architectural_detail: CategoryCompleteness;
    archival: CategoryCompleteness;
    aerial_context: CategoryCompleteness;
  };
  missingItems: string[];
  historicalContextNote: string;
  callToActionPrompt: string;
}

export interface RouteImageCompletenessReport {
  trailSlug: string;
  trailTitle: string;
  totalStops: number;
  stopsWithImages: number;
  stopsMissingImages: number;
  overallCoveragePercent: number;
  stops: SiteImageCompleteness[];
}

// Cultural & historical audit notes regarding architectural visual documentation
const SITE_AUDIT_SPECS: Record<
  string,
  {
    historicalContextNote: string;
    missingSuggestions: {
      facade?: string;
      interior?: string;
      architectural_detail?: string;
      archival?: string;
      aerial_context?: string;
    };
  }
> = {
  "ngo-mon": {
    historicalContextNote:
      "Ngọ Môn là cổng chính lớn nhất của Hoàng Thành Huế (xây năm 1833), bảo tồn nguyên vẹn qua các đợt đại trùng tu. Hệ thống ảnh hiện trạng mặt tiền và 5 cửa vòm đá rất đầy đủ.",
    missingSuggestions: {
      interior: "Ảnh chi tiết nội thất tầng lầu Ngũ Phụng với 100 cây cột gỗ lim và trần sơn thếp.",
    },
  },
  "cau-trung-dao": {
    historicalContextNote:
      "Cầu đá bắc qua hồ Thái Dịch trên trục dũng đạo (xây năm 1833). Đã có ảnh toàn cảnh góc cao kết nối hồ sen và thềm điện.",
    missingSuggestions: {
      architectural_detail: "Cận cảnh 2 cửa đồng quán (cổng đồng đúc hoa văn rồng vờn mây) và lan can cẩm thạch.",
      archival: "Bản vẽ kỹ thuật hoặc ảnh chụp hai cổng đồng thời kỳ đầu thế kỷ 20.",
    },
  },
  "san-dai-trieu-nghi": {
    historicalContextNote:
      "Khoảng sân rộng 2 tầng lát đá Thanh Phước và gạch Bát Tràng trước Điện Thái Hòa, nơi quan viên đứng bái mạng. Đã có ảnh không gian tổng thể sân chầu.",
    missingSuggestions: {
      architectural_detail: "Ảnh chụp cận cảnh các bia đá nhỏ ghi phẩm trật (phẩm thạch từ chánh nhất phẩm đến tòng cửu phẩm).",
      interior: "Bản vẽ phối cảnh bố trí quan văn bên tả, quan võ bên hữu trong lễ Đại triều.",
      archival: "Ảnh tư liệu lễ Tứ tuần Đại khánh thời Khải Định (1924) bách quan quỳ lạy.",
    },
  },
  "dien-thai-hoa": {
    historicalContextNote:
      "Tòa điện thiết đại triều quan trọng nhất triều Nguyễn theo thức 'trùng thiềm điệp ốc', vừa khánh thành đại trùng tu toàn diện 2021-2025. Đã có ảnh mặt tiền và góc nghiêng mái ngói hoàng lưu ly.",
    missingSuggestions: {
      interior: "Ảnh chụp trực diện bảo tọa ngai vàng thiên tử dưới bửu tán sơn son thếp vàng.",
      architectural_detail: "Cận cảnh các ô hộc khắc thơ văn chữ Hán ngự chế theo phong cách 'nhất thi nhất họa' trên dải liên ba.",
    },
  },
  "dien-can-chanh": {
    historicalContextNote:
      "Ngôi điện thiết thường triều hàng ngày nằm ngay sau Đại Cung Môn. Tòa nhà bị bom đạn chiến tranh phá hủy hoàn toàn vào năm 1947, hiện trạng thực tế chỉ còn lại nền móng đá thanh và chân cột.",
    missingSuggestions: {
      facade: "Ảnh chụp khảo cổ học hiện trạng nền móng đá thanh và chân cột lim còn lại ngoài thực địa.",
      interior: "Ảnh chụp không gian ngự tọa và bàn làm việc của vua với Cơ Mật Viện trước năm 1947.",
      archival: "Bộ sưu tập ảnh tư liệu do học giả Pháp (L. Cadière / EFEO) chụp nội thất chạm lộng gỗ tinh xảo đầu thế kỷ 20.",
      architectural_detail: "Bản vẽ bình đồ kỹ thuật nghiên cứu khảo cổ phục vụ dự án phục dựng.",
    },
  },
  "the-to-mieu": {
    historicalContextNote:
      "Tổ hợp đền miếu 9 gian 2 chái phụng thờ các vị hoàng đế triều Nguyễn (xây năm 1821), lưu giữ nguyên vẹn hệ thống khám thờ và bài vị.",
    missingSuggestions: {
      facade: "Ảnh chụp toàn cảnh chính diện Thế Tổ Miếu nhìn từ sân trước.",
      interior: "Ảnh chụp gian chính giữa thờ vua Gia Long và các khám thờ theo nguyên tắc Tả Chiêu Hữu Mục.",
      architectural_detail: "Chi tiết bờ nóc đắp nổi lưỡng long chầu nguyệt và các án hương án gỗ sơn son.",
      archival: "Ảnh tư liệu lễ tế bốn mùa của hoàng gia thời Bảo Đại.",
    },
  },
  "hien-lam-cac": {
    historicalContextNote:
      "Tòa lầu gỗ 3 tầng cao 17m án ngữ phía nam sân Thế Miếu, là công trình cao nhất trong Đại Nội mang ý nghĩa đài tưởng niệm công thần khai quốc.",
    missingSuggestions: {
      facade: "Ảnh chụp chính diện toàn cảnh 3 tầng lầu Hiển Lâm Các từ hướng sân gạch.",
      architectural_detail: "Chi tiết bờ nóc mái gắn bầu rượu pháp lam và hoa văn rồng ngậm bờ nóc.",
      interior: "Kết cấu bộ khung gỗ lim chịu lực 3 tầng nguyên bản thời Minh Mạng.",
    },
  },
  "hung-to-mieu": {
    historicalContextNote:
      "Miếu thờ thân phụ và mẫu thân vua Gia Long (Nguyễn Phúc Luân và Thoại Thánh Hoàng thái hậu), xây dựng năm 1804 ở góc tây nam.",
    missingSuggestions: {
      facade: "Ảnh chụp mặt đứng chính diện Hưng Tổ Miếu và khoảng sân nhỏ.",
      interior: "Khám thờ và ngai vị của Hưng Tổ Hiếu Khang Hoàng đế.",
    },
  },
  "trieu-to-mieu": {
    historicalContextNote:
      "Miếu thờ thủy tổ Nguyễn Kim ở góc đông nam Hoàng Thành (xây năm 1804), đối xứng phong thủy với Thế Tổ Miếu.",
    missingSuggestions: {
      facade: "Ảnh chụp mặt tiền Triệu Miếu và hệ thống tường hoa bao quanh.",
      interior: "Án thờ Triệu Tổ Tĩnh Hoàng đế.",
    },
  },
  "dai-cung-mon": {
    historicalContextNote:
      "Cổng chính diện 5 gian 3 cửa sơn son dẫn vào Tử Cấm Thành. Bị phá hủy năm 1947, hiện Trung tâm Bảo tồn Cố đô đang triển khai khảo cổ nền móng.",
    missingSuggestions: {
      facade: "Ảnh chụp hiện trạng các bậc đá thềm rồng và dấu tích chân tường Đại Cung Môn.",
      archival: "Ảnh chụp màu Autochrome của Albert Kahn (1915) ghi nhận cổng khi còn nguyên vẹn.",
    },
  },
  "dien-kien-trung": {
    historicalContextNote:
      "Cung điện 2 tầng phong cách Á - Âu xây thời Khải Định (1921-1923), phục hồi toàn diện xuất sắc năm 2023. Đã có ảnh mặt tiền rực rỡ gốm sứ.",
    missingSuggestions: {
      interior: "Ảnh nội thất phòng làm việc và buồng ngủ của Hoàng hậu Nam Phương cùng vua Bảo Đại.",
      architectural_detail: "Cận cảnh chi tiết mảnh sành sứ khảm nổi hình chim phượng, hoa cúc và phù điêu phong cách Phục hưng.",
    },
  },
  "duyet-thi-duong": {
    historicalContextNote:
      "Nhà hát hoàng gia cổ nhất Việt Nam (xây năm 1826) trong Tử Cấm Thành, hiện là không gian diễn xướng Nhã nhạc cung đình Huế.",
    missingSuggestions: {
      facade: "Ảnh toàn cảnh cửa vào nhà hát Duyệt Thị Đường từ hoa viên.",
      interior: "Ảnh chụp sân khấu diễn xướng trung tâm và ngự tọa trên gác lầu nhìn xuống sàn diễn.",
      architectural_detail: "Trần nhà hát vẽ bầu trời đêm với mặt trăng, mặt trời và chòm sao dát bạc.",
    },
  },
  "thai-binh-lau": {
    historicalContextNote:
      "Thư viện hoàng gia 2 tầng bằng gỗ xây thời Khải Định bên hồ sen nhỏ, nơi nhà vua nghỉ ngơi, ngâm thơ và đọc sách.",
    missingSuggestions: {
      facade: "Ảnh toàn cảnh Thái Bình Lâu soi bóng trên mặt nước hồ cảnh.",
      architectural_detail: "Hoa văn trang trí khảm sành sứ hai bên hồi và tượng rồng hồi long ngậm ngọc.",
      interior: "Tủ sách gỗ và án thư chạm khắc nơi ngự lãm thư tịch.",
    },
  },
  "cung-dien-tho": {
    historicalContextNote:
      "Quần thể cung điện dành riêng cho Hoàng Thái Hậu (xây từ 1804), liên kết bằng hệ thống trường lang có mái che. Đã có ảnh nhà Tạ Trường Du.",
    missingSuggestions: {
      facade: "Ảnh chụp mặt tiền Chính điện Cung Diên Thọ và sân gạch trước điện.",
      interior: "Nội thất điện Thọ Ninh và Lầu Tịnh Minh kiến trúc Pháp (xây năm 1927).",
      architectural_detail: "Chi tiết chạm lộng hoa văn rèm gỗ và bức hoành phi chữ Hán.",
    },
  },
  "cung-truong-sanh": {
    historicalContextNote:
      "Khuôn viên cung điện hoa viên ở góc tây bắc Hoàng Thành (xây năm 1821), ban đầu là ngự uyển hoa viên, sau là nơi ở của Thái Hoàng Thái Hậu.",
    missingSuggestions: {
      facade: "Ảnh chụp toàn cảnh cổng tam quan và cầu đá bắc qua hồ Đào Thái.",
      architectural_detail: "Cảnh quan hòn non bộ đá tự nhiên và rạch nước trong vườn ngự.",
    },
  },
  "dien-phung-tien": {
    historicalContextNote:
      "Điện thờ tổ tiên dành cho nữ giới hoàng tộc dâng hương (do phụ nữ không vào Thế Miếu). Bị tàn phá năm 1947, hiện đã phục dựng cổng và tường bao.",
    missingSuggestions: {
      facade: "Ảnh chụp cổng Tam Quan phục chế và dấu tích khảo cổ nền móng chính điện.",
      archival: "Ảnh chụp cổng ngõ và sân bái đường đầu thế kỷ 20.",
    },
  },
};

/**
 * Calculates completeness statistics and missing categories for a single monument.
 */
export function getSiteImageCompleteness(siteSlug: string): SiteImageCompleteness {
  const site: any = FALLBACK_SITES.find((s) => s.slug === siteSlug) || {
    id: `site-${siteSlug}`,
    slug: siteSlug,
    name_vi: siteSlug,
    zone_slug: "central-ceremonial-axis",
    condition: "unknown",
  };

  const zone = FALLBACK_ZONES.find((z) => z.slug === site.zone_slug);
  const siteImages = HERITAGE_IMAGES.filter((img) => img.siteSlug === siteSlug);

  // Group images by category
  const facadeImgs = siteImages.filter(
    (img) => (img.viewpoint === "front" || img.viewpoint === "oblique") && img.category === "monument",
  );
  const interiorImgs = siteImages.filter(
    (img) => img.viewpoint === "detail" && img.caption.toLowerCase().includes("nội"),
  );
  const detailImgs = siteImages.filter(
    (img) => img.imageType === "architectural_detail" || img.viewpoint === "detail",
  );
  const archivalImgs = siteImages.filter(
    (img) => img.imageType === "archival",
  );
  const aerialImgs = siteImages.filter(
    (img) => img.imageType === "aerial_reference" || img.viewpoint === "aerial",
  );

  const audit = SITE_AUDIT_SPECS[siteSlug] || {
    historicalContextNote: "Công trình kiến trúc di sản thuộc quần thể Đại Nội Huế.",
    missingSuggestions: {},
  };

  const categories = {
    facade: {
      label: "Mặt tiền / Toàn cảnh",
      available: facadeImgs.length > 0,
      count: facadeImgs.length,
      neededDescription:
        audit.missingSuggestions.facade ||
        `Ảnh chụp góc thẳng hoặc góc nghiêng rõ nét bao quát toàn bộ mặt tiền ${site.name_vi}.`,
    },
    interior: {
      label: "Không gian nội thất",
      available: interiorImgs.length > 0,
      count: interiorImgs.length,
      neededDescription:
        audit.missingSuggestions.interior ||
        `Ảnh chụp bên trong công trình: ngai vàng, án thờ, hệ cột lim hoặc bàn ghế ngự dụng.`,
    },
    architectural_detail: {
      label: "Cấu kiện kiến trúc & Mỹ thuật",
      available: detailImgs.length > 0,
      count: detailImgs.length,
      neededDescription:
        audit.missingSuggestions.architectural_detail ||
        `Ảnh chụp cận cảnh vì kèo, ngói tráng men, hoa văn bờ nóc hoặc nghệ thuật khảm sành sứ.`,
    },
    archival: {
      label: "Ảnh tư liệu lịch sử (trước 1947)",
      available: archivalImgs.length > 0,
      count: archivalImgs.length,
      neededDescription:
        audit.missingSuggestions.archival ||
        `Ảnh tư liệu đầu thế kỷ 20 (EFEO, Albert Kahn, BAVH) thể hiện hiện trạng lịch sử.`,
    },
    aerial_context: {
      label: "Không ảnh định vị tọa độ",
      available: true, // The master aerial map dai-noi-aerial-v1.webp covers all 16
      count: 1,
      neededDescription: "Đã có bản đồ không ảnh trực giao tham chiếu tọa độ chuẩn hóa UV.",
    },
  };

  const missingItems: string[] = [];
  if (!categories.facade.available) missingItems.push(categories.facade.neededDescription);
  if (!categories.interior.available) missingItems.push(categories.interior.neededDescription);
  if (!categories.architectural_detail.available) missingItems.push(categories.architectural_detail.neededDescription);
  if (!categories.archival.available) missingItems.push(categories.archival.neededDescription);

  let status: ImageCompletenessStatus = "missing";
  let coveragePercent = 20; // 20% baseline from master aerial map

  if (siteImages.length >= 3) {
    status = "complete";
    coveragePercent = 85;
  } else if (siteImages.length > 0) {
    status = "partial";
    coveragePercent = 40 + siteImages.length * 15;
  } else {
    status = "missing";
    coveragePercent = 20; // only master aerial
  }

  const callToActionPrompt =
    status === "missing"
      ? `Công trình ${site.name_vi} hiện chưa có tư liệu hình ảnh chi tiết được xác minh trong kho học liệu. Dự án Lưu Niên hoan nghênh thầy cô, học sinh và các nhà nghiên cứu cung cấp ảnh chụp thực tế hoặc tư liệu lưu trữ có trích nguồn chính xác.`
      : status === "partial"
      ? `Công trình ${site.name_vi} đã có một số ảnh hiện trạng nhưng còn thiếu góc chụp chi tiết cấu kiện và nội thất. Đóng góp thêm ảnh sẽ giúp học sinh có trải nghiệm khảo sát sâu sắc hơn.`
      : `Công trình ${site.name_vi} đã có đầy đủ hồ sơ ảnh hiện trạng và cấu kiện phục vụ học tập.`;

  return {
    siteSlug,
    siteNameVi: site.name_vi,
    siteNameHanNom: site.name_han_nom || site.chinese_name,
    zoneSlug: site.zone_slug || "central-ceremonial-axis",
    zoneTitle: zone?.title_vi || "Khu vực Hoàng Thành",
    condition: site.condition || "extant",
    status,
    totalImages: siteImages.length,
    coveragePercent,
    availableImages: siteImages,
    categories,
    missingItems,
    historicalContextNote: audit.historicalContextNote,
    callToActionPrompt,
  };
}

/**
 * Returns image completeness evaluations for all 16 monuments.
 */
export function getAllSitesImageCompleteness(): SiteImageCompleteness[] {
  return FALLBACK_SITES.map((site) => getSiteImageCompleteness(site.slug));
}

/**
 * Returns only sites that are missing images (status === 'missing' or 'partial').
 */
export function getSitesNeedingImages(): SiteImageCompleteness[] {
  return getAllSitesImageCompleteness().filter((s) => s.status !== "complete");
}

/**
 * Generates an aggregated image report for a specific educational walking route.
 */
export function getRouteImageCompletenessReport(
  trailSlug: string,
  trailTitle: string,
  stops: Array<{ monument_slug: string }>,
): RouteImageCompletenessReport {
  const stopCompleteness = stops.map((s) => getSiteImageCompleteness(s.monument_slug));
  const stopsWithImages = stopCompleteness.filter((s) => s.totalImages > 0).length;
  const stopsMissingImages = stopCompleteness.filter((s) => s.totalImages === 0).length;

  const totalCoverage = stopCompleteness.reduce((acc, curr) => acc + curr.coveragePercent, 0);
  const overallCoveragePercent = Math.round(totalCoverage / (stopCompleteness.length || 1));

  return {
    trailSlug,
    trailTitle,
    totalStops: stops.length,
    stopsWithImages,
    stopsMissingImages,
    overallCoveragePercent,
    stops: stopCompleteness,
  };
}
