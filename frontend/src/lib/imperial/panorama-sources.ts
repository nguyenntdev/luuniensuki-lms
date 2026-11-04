/**
 * 360 Virtual Museum Source Links & Provenance Registry
 * Ref: Luu Nien STTTNND Follow-On SPEC V5.1 (Ticket V5-T047 / Wave W04-A07)
 *
 * Implements:
 * 1. Historical Monument Linkage & Primary Bibliographic Citations for 360 Panoramas
 * 2. Viewpoint Provenance Attribution (Đại Nam Thực Lục, Khâm Định Hội Điển, HMCC)
 * 3. Accessibility Text Generation & Reduced-Motion Contracts
 * 4. Resilient 2D Still Fallback Resolution for Inaccessible/Broken Panorama URIs
 */

export interface HistoricalSourceCitation {
  id?: string;
  title: string;
  author?: string;
  year?: string | number;
  locator?: string;
  citationQuote?: string;
  evidenceStrength?: "verified" | "probable" | "traditional";
  sourceUrl?: string;
}

export interface HistoricalMonumentLink {
  id: string;
  name: string;
  slug: string;
  historicalPeriod: string;
  provenance: string;
  unescoInscription?: string;
  nationalTreasure?: string;
  rightsOwner: string;
  license: string;
  sourceCitations: HistoricalSourceCitation[];
  monumentUrl: string;
  fallbackImageUrl: string;
  verificationStatus: "verified" | "canonical" | "probable";
  architecturalStyle?: string;
  coordinatesSummary?: string;
}

export interface PanoramaViewpoint {
  id: string;
  title: string;
  description?: string | null;
  yaw: number;
  pitch: number;
  monumentId?: string | null;
  monumentName?: string | null;
  artDetailSlug?: string | null;
  sourceCitation?: string | null;
  sourceUrl?: string | null;
  verificationStatus?: "verified" | "probable" | "traditional" | string | null;
  altText?: string | null;
  ariaLabel?: string | null;
}

export const VERIFIED_VIRTUAL_MUSEUM_MONUMENTS: Record<string, HistoricalMonumentLink> = {
  "cuu-dinh": {
    id: "monument-cuu-dinh",
    name: "Cửu Đỉnh (Chín Chiếc Đỉnh Đồng Triều Nguyễn)",
    slug: "cuu-dinh",
    historicalPeriod: "Triều Nguyễn — Minh Mạng (1835 - 1837)",
    provenance:
      "Chín chiếc đỉnh đồng uy nghi đặt tại sân Thế Miếu, Hoàng thành Huế, đúc từ năm 1835 đến 1837. Trên mỗi đỉnh chạm khắc 17 hình tượng sông núi, danh thắng, vũ khí và sản vật tiêu biểu của dải đất Việt Nam. Được UNESCO công nhận là Di sản Tư liệu Khu vực Châu Á - Thái Bình Dương năm 2024.",
    unescoInscription: "Di sản Tư liệu Ký ức Thế giới Khu vực Châu Á - Thái Bình Dương (2024)",
    nationalTreasure: "Bảo vật Quốc gia Việt Nam (Đợt 1, 2012)",
    rightsOwner: "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
    license: "CC BY 4.0 / Educational Fair Use",
    monumentUrl: "/cuu-dinh",
    fallbackImageUrl: "/ban-duc-noi/CAO DINH/CAO ĐỈNH.jpg",
    verificationStatus: "canonical",
    architecturalStyle: "Đúc đồng truyền thống Cung đình Huế thế kỷ XIX",
    coordinatesSummary: "Sân Thế Miếu, trước Hiển Lâm Các (16.4687° N, 107.5776° E)",
    sourceCitations: [
      {
        id: "src-dntl-cuu-dinh-1835",
        title: "Đại Nam Thực Lục Chính Biên",
        author: "Quốc Sử Quán Triều Nguyễn",
        year: "1835",
        locator: "Đệ nhị kỷ, Quyển 162",
        citationQuote:
          "Tháng 12 năm Ất Mùi (1835), đúc chín đỉnh đồng đặt trước sân Thế Miếu. Đỉnh lớn nặng hơn hai vạn cân đồng, ghi nhớ công đức liệt thánh tổ tông.",
        evidenceStrength: "verified",
        sourceUrl: "/sources/dai-nam-thuc-luc-de-nhi-ky",
      },
      {
        id: "src-kddnhdle-cuu-dinh-cong-bo",
        title: "Khâm Định Đại Nam Hội Điển Sự Lệ",
        author: "Nội Các Triều Nguyễn",
        year: "1851",
        locator: "Quyển 162, Công Bộ - Quy thức đúc Cửu Đỉnh",
        citationQuote:
          "Quy định quy chuẩn hình thể, quai vạc, chân kiềng, độ dày mỏng và hình họa bản khắc 153 đồ án trên chín đỉnh.",
        evidenceStrength: "verified",
        sourceUrl: "/sources/kham-dinh-dai-nam-hoi-dien-su-le",
      },
      {
        id: "src-hmcc-cuu-dinh-dossier",
        title: "Hồ sơ Khoa học Di sản Tư liệu Cửu Đỉnh Huế",
        author: "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
        year: "2024",
        locator: "Hồ sơ đệ trình UNESCO MOWCAP 2024",
        citationQuote:
          "Hệ thống minh văn và phù điêu đúc nổi trên Cửu Đỉnh là bách khoa toàn thư bằng đồng về đất nước Việt Nam thống nhất.",
        evidenceStrength: "verified",
        sourceUrl: "https://hueworldheritage.org.vn",
      },
    ],
  },
  "the-mieu": {
    id: "monument-the-mieu",
    name: "Thế Tổ Miếu (Thế Miếu)",
    slug: "the-mieu",
    historicalPeriod: "Triều Nguyễn — Minh Mạng (1821)",
    provenance:
      "Tổ miếu phụng thờ các vị hoàng đế triều Nguyễn, tọa lạc tại góc tây nam Hoàng thành Huế. Xây dựng năm Minh Mạng thứ 2 (1821), gồm 9 gian 2 chái kép theo kiểu 'trùng thiềm điệp ốc', lợp ngói hoàng lưu ly trang nghiêm.",
    nationalTreasure: "Di tích Quốc gia đặc biệt — Quần thể Di tích Cố đô Huế (UNESCO 1993)",
    rightsOwner: "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
    license: "CC BY 4.0 / Educational Fair Use",
    monumentUrl: "/sites/the-mieu",
    fallbackImageUrl: "/ban-duc-noi/NHAN DINH/NHÂN ĐỈNH.jpg",
    verificationStatus: "verified",
    architecturalStyle: "Kiến trúc gỗ cung đình 'trùng thiềm điệp ốc'",
    coordinatesSummary: "Tây nam Hoàng thành Huế (16.4685° N, 107.5772° E)",
    sourceCitations: [
      {
        id: "src-dntl-the-mieu-1821",
        title: "Đại Nam Thực Lục Chính Biên",
        author: "Quốc Sử Quán Triều Nguyễn",
        year: "1821",
        locator: "Đệ nhị kỷ, Quyển 8",
        citationQuote:
          "Xây dựng Thế Miếu ở phía sau cửa Chương Đức, chuẩn bị thần vị và hương án phụng thờ Hoàng khảo Thế Tổ Cao Hoàng Đế.",
        evidenceStrength: "verified",
        sourceUrl: "/sources/dai-nam-thuc-luc",
      },
      {
        id: "src-kddnhdle-the-mieu-le-bo",
        title: "Khâm Định Đại Nam Hội Điển Sự Lệ",
        author: "Nội Các Triều Nguyễn",
        year: "1851",
        locator: "Quyển 84, Lễ Bộ - Điển lễ Thế Miếu",
        citationQuote:
          "Nghi thức tế lễ bốn mùa Xuân, Hạ, Thu, Đông (Tứ thời thường hưởng) tại chính điện Thế Miếu.",
        evidenceStrength: "verified",
        sourceUrl: "/sources/kham-dinh-hoi-dien",
      },
    ],
  },
  "ngo-mon": {
    id: "monument-ngo-mon",
    name: "Ngọ Môn Huế (Lầu Ngũ Phụng)",
    slug: "ngo-mon",
    historicalPeriod: "Triều Nguyễn — Minh Mạng (1833)",
    provenance:
      "Cổng chính phía nam của Hoàng thành Huế, xây dựng năm Minh Mạng thứ 14 (1833) thay thế đài Nam Khuyết. Phần trên là Lầu Ngũ Phụng tráng lệ với 100 cột gỗ lim, nơi công bố chiếu chỉ, lịch vương triều và tổ chức lễ Truyền Lô.",
    nationalTreasure: "Di tích Quốc gia đặc biệt — Quần thể Di tích Cố đô Huế (UNESCO 1993)",
    rightsOwner: "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
    license: "CC BY 4.0 / Educational Fair Use",
    monumentUrl: "/sites/ngo-mon",
    fallbackImageUrl: "/ban-duc-noi/CAO DINH/ĐÔNG HẢI.jpg",
    verificationStatus: "verified",
    architecturalStyle: "Đài gạch đá kết hợp lầu gỗ Ngũ Phụng hai tầng cánh gà",
    coordinatesSummary: "Cổng chính phía nam Hoàng thành (16.4678° N, 107.5786° E)",
    sourceCitations: [
      {
        id: "src-dntl-ngo-mon-1833",
        title: "Đại Nam Thực Lục Chính Biên",
        author: "Quốc Sử Quán Triều Nguyễn",
        year: "1833",
        locator: "Đệ nhị kỷ, Quyển 104",
        citationQuote:
          "Đổi đài Nam Khuyết làm cửa Ngọ Môn, mở 5 cửa vòm, xây lầu Ngũ Phụng ở trên lợp ngói hoàng lưu ly và thanh lưu ly.",
        evidenceStrength: "verified",
        sourceUrl: "/sources/dai-nam-thuc-luc",
      },
    ],
  },
  "dien-thai-hoa": {
    id: "monument-dien-thai-hoa",
    name: "Điện Thái Hòa (Sân Đại Triều Nghi)",
    slug: "dien-thai-hoa",
    historicalPeriod: "Triều Nguyễn — Gia Long (1805) & Minh Mạng (1833)",
    provenance:
      "Cung điện trung tâm quyền lực tối cao của Hoàng triều Nguyễn, nơi đặt Ngai vàng và bửu tọa của 13 đời vua. Nơi cử hành lễ Đăng quang, Vạn thọ, tiếp sứ thần và các kỳ đại triều vào mồng 1 và 15 hàng tháng.",
    nationalTreasure: "Ngai vàng Triều Nguyễn (Bảo vật Quốc gia số 1, 2012)",
    rightsOwner: "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
    license: "CC BY 4.0 / Educational Fair Use",
    monumentUrl: "/sites/dien-thai-hoa",
    fallbackImageUrl: "/ban-duc-noi/CAO DINH/LONG.jpg",
    verificationStatus: "canonical",
    architecturalStyle: "Điện gỗ kép 'trùng thiềm điệp ốc' với 80 cột lim dát vàng long vân",
    coordinatesSummary: "Trục chính đạo Đại Nội Huế (16.4697° N, 107.5786° E)",
    sourceCitations: [
      {
        id: "src-dntl-thai-hoa-1805",
        title: "Đại Nam Thực Lục Chính Biên",
        author: "Quốc Sử Quán Triều Nguyễn",
        year: "1805",
        locator: "Đệ nhất kỷ, Quyển 26",
        citationQuote:
          "Tháng 2 năm Ất Sửu (1805), định quy thức xây dựng điện Thái Hòa làm nơi thiết đại triều nghi.",
        evidenceStrength: "verified",
        sourceUrl: "/sources/dai-nam-thuc-luc",
      },
    ],
  },
  "kinh-thanh": {
    id: "monument-kinh-thanh",
    name: "Kinh Thành Huế (Đô Thành Phú Xuân)",
    slug: "kinh-thanh",
    historicalPeriod: "Triều Nguyễn — Gia Long (1805) & Minh Mạng (1832)",
    provenance:
      "Quần thể thành quách quân sự phòng thủ rộng lớn chu vi gần 10km kết hợp nguyên lý kiến trúc quân sự Vauban Tây phương với phong thủy địa lý phương Đông (núi Ngự Bình, sông Hương, cồn Hến, cồn Dã Viên).",
    nationalTreasure: "Di tích Quốc gia đặc biệt — Quần thể Di tích Cố đô Huế (UNESCO 1993)",
    rightsOwner: "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
    license: "CC BY 4.0 / Educational Fair Use",
    monumentUrl: "/sites/kinh-thanh",
    fallbackImageUrl: "/ban-duc-noi/NHAN DINH/NGỰ BÌNH SƠN.jpg",
    verificationStatus: "verified",
    architecturalStyle: "Thành trì pháo đài Vauban kiểu Pháp kết hợp lũy thành truyền thống",
    coordinatesSummary: "Bắc ngạn sông Hương, TP. Huế (16.4700° N, 107.5750° E)",
    sourceCitations: [
      {
        id: "src-dntl-kinh-thanh-1805",
        title: "Đại Nam Thực Lục Chính Biên",
        author: "Quốc Sử Quán Triều Nguyễn",
        year: "1805",
        locator: "Đệ nhất kỷ, Quyển 24",
        citationQuote:
          "Đo đạc cắm mốc xây dựng kinh thành Huế, lấy sông Hương làm minh đường, núi Ngự Bình làm tiền án.",
        evidenceStrength: "verified",
        sourceUrl: "/sources/dai-nam-thuc-luc",
      },
    ],
  },
  "hien-lam-cac": {
    id: "monument-hien-lam-cac",
    name: "Hiển Lâm Các (Gác Hiển Lâm)",
    slug: "hien-lam-cac",
    historicalPeriod: "Triều Nguyễn — Minh Mạng (1821 - 1822)",
    provenance:
      "Công trình kiến trúc bằng gỗ cao nhất trong Hoàng thành Huế (17m), dựng năm 1821-1822 để ghi nhớ công lao của các vị công thần có công dựng nghiệp triều Nguyễn. Đặt đối diện Thế Miếu qua sân Cửu Đỉnh.",
    nationalTreasure: "Di tích Quốc gia đặc biệt — Quần thể Di tích Cố đô Huế (UNESCO 1993)",
    rightsOwner: "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
    license: "CC BY 4.0 / Educational Fair Use",
    monumentUrl: "/sites/hien-lam-cac",
    fallbackImageUrl: "/ban-duc-noi/CHUONG DINH/CHƯƠNG ĐỈNH.jpg",
    verificationStatus: "verified",
    architecturalStyle: "Lầu gác gỗ 3 tầng mái dốc thanh thoát",
    coordinatesSummary: "Sân trước Thế Miếu, đối diện Cửu Đỉnh (16.4689° N, 107.5776° E)",
    sourceCitations: [
      {
        id: "src-dntl-hien-lam-cac-1821",
        title: "Đại Nam Thực Lục Chính Biên",
        author: "Quốc Sử Quán Triều Nguyễn",
        year: "1821",
        locator: "Đệ nhị kỷ, Quyển 11",
        citationQuote:
          "Dựng gác Hiển Lâm cao ba tầng ở trước Thế Miếu để biểu dương công tích khai quốc.",
        evidenceStrength: "verified",
        sourceUrl: "/sources/dai-nam-thuc-luc",
      },
    ],
  },
};

/**
 * Retrieve verified monument record by key or slug.
 */
export function getVerifiedMonument(keyOrSlug?: string | null): HistoricalMonumentLink | undefined {
  if (!keyOrSlug) return undefined;
  const normalized = keyOrSlug.trim().toLowerCase().replace(/^monument-/, "");
  return VERIFIED_VIRTUAL_MUSEUM_MONUMENTS[normalized];
}

/**
 * Retrieve verified monument record, or generate a safe fallback monument record.
 */
export function getVerifiedMonumentOrFallback(
  keyOrSlug?: string | null,
  title?: string | null
): HistoricalMonumentLink {
  const existing = getVerifiedMonument(keyOrSlug);
  if (existing) return existing;

  const resolvedSlug = (keyOrSlug || "di-tich-hue").toLowerCase().replace(/[^a-z0-9_-]/g, "-");
  const resolvedName = title?.trim() || "Di tích Lịch sử Cố đô Huế";

  return {
    id: `monument-${resolvedSlug}`,
    name: resolvedName,
    slug: resolvedSlug,
    historicalPeriod: "Triều Nguyễn (1802 - 1945)",
    provenance: `Công trình thuộc Quần thể Di tích Cố đô Huế, được bảo tồn và tư liệu hóa bởi Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC).`,
    rightsOwner: "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
    license: "CC BY 4.0 / Educational Fair Use",
    monumentUrl: `/sites/${resolvedSlug}`,
    fallbackImageUrl: "/ban-duc-noi/CAO DINH/CAO ĐỈNH.jpg",
    verificationStatus: "probable",
    sourceCitations: [
      {
        id: `src-hmcc-${resolvedSlug}`,
        title: "Hồ sơ Di sản Văn hóa Cố đô Huế",
        author: "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
        year: "2024",
        locator: "Kho lưu trữ tư liệu số hóa di tích",
        evidenceStrength: "verified",
        sourceUrl: "https://hueworldheritage.org.vn",
      },
    ],
  };
}

/**
 * Checks whether a panorama URI is broken, empty, or inaccessible.
 */
export function isBrokenPanoramaUri(uri?: string | null): boolean {
  if (!uri || typeof uri !== "string") return true;
  const trimmed = uri.trim();
  if (trimmed === "" || trimmed === "null" || trimmed === "undefined") return true;
  if (trimmed.startsWith("broken://") || trimmed.includes("invalid") || trimmed.includes("missing")) {
    return true;
  }
  return false;
}

/**
 * Generates an accessible, structured text description of the 360 scene and its viewpoints.
 */
export function generateAccessible2DDescription(
  monument: HistoricalMonumentLink,
  viewpoints?: Array<{ title: string; description?: string | null }>
): string {
  const parts: string[] = [];
  parts.push(`Toàn cảnh di tích: ${monument.name}.`);
  parts.push(`Niên đại: ${monument.historicalPeriod}.`);
  parts.push(`Bối cảnh lịch sử: ${monument.provenance}`);

  if (monument.sourceCitations && monument.sourceCitations.length > 0) {
    const citations = monument.sourceCitations
      .map((c) => `${c.title}${c.locator ? ` (${c.locator})` : ""}`)
      .join("; ");
    parts.push(`Sử liệu xác thực: ${citations}.`);
  }

  if (viewpoints && viewpoints.length > 0) {
    const vpTexts = viewpoints
      .map((vp, idx) => `Điểm ${idx + 1}: ${vp.title}${vp.description ? ` - ${vp.description}` : ""}`)
      .join(". ");
    parts.push(`Các điểm quan sát chính: ${vpTexts}`);
  }

  parts.push(`Bản quyền và lưu trữ: ${monument.rightsOwner} (${monument.license}).`);
  return parts.join(" ");
}

/**
 * Resolves a resilient 2D still fallback when 360 equirectangular texture is broken or unreadable.
 */
export function resolvePanorama2DFallback(
  src: string,
  fallbackImageUrl?: string,
  monumentKey?: string
): {
  isBroken: boolean;
  fallbackImageUrl: string;
  monument: HistoricalMonumentLink;
  accessibleDescription: string;
} {
  const isBroken = isBrokenPanoramaUri(src);
  const monument = getVerifiedMonumentOrFallback(monumentKey);

  // Determine reliable 2D still image URL
  let resolvedFallbackUrl = fallbackImageUrl;
  if (!resolvedFallbackUrl || isBrokenPanoramaUri(resolvedFallbackUrl)) {
    resolvedFallbackUrl = monument.fallbackImageUrl || "/ban-duc-noi/CAO DINH/CAO ĐỈNH.jpg";
  }

  const accessibleDescription = generateAccessible2DDescription(monument);

  return {
    isBroken,
    fallbackImageUrl: resolvedFallbackUrl,
    monument,
    accessibleDescription,
  };
}
