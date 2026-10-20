/**
 * STTTNNĐ (Lưu Niên — Đại Nội Huế) Certificate Utilities & Seal System.
 * Ref: STTT-SPEC-AUDIO-PASSPORT-002 (Royal Heritage Certificate of Completion)
 * Scope: STTT_IMPERIAL_CITY
 */

import {
  PASSPORT_SEALS,
  PASSPORT_ZONE_META,
  PASSPORT_STORAGE_KEY,
  PASSPORT_STUDENT_KEY,
  type PassportSealDefinition,
  type SpatialZoneSlug,
} from "./passport-storage";

export type HonorsTitleTier =
  | "novice"
  | "apprentice"
  | "explorer"
  | "scholar"
  | "master";

export interface HonorsTitleInfo {
  tier: HonorsTitleTier;
  title: string;
  titleEn: string;
  minSeals: number;
  maxSeals: number;
  badgeClass: string;
  accentColor: string;
  descriptionVi: string;
  epigraphVi: string;
}

export interface ZoneSealBreakdown {
  zoneSlug: SpatialZoneSlug;
  zoneTitleVi: string;
  zoneTitleHanNom: string;
  totalCount: number;
  unlockedCount: number;
  isCompleted: boolean;
  seals: Array<PassportSealDefinition & { isUnlocked: boolean }>;
}

export interface CertificateData {
  id: string;
  studentName: string;
  schoolName: string;
  issueDate: string;
  unlockedSiteSlugs: string[];
  totalScore: number;
  verificationHash?: string;
}

export const CERTIFICATE_STORAGE_KEY = "luuniensuki_imperial_certificate_v1";

export { PASSPORT_STORAGE_KEY, PASSPORT_STUDENT_KEY };

/**
 * Returns honors title info based on unlocked seal count.
 * Spec STTT-SPEC-AUDIO-PASSPORT-002:
 * - 4-7 seals: "Tập Sự Khảo Cứu Di Sản"
 * - 8-11 seals: "Thám Hiểm Cung Đình Huế"
 * - 12-15 seals: "Học Giả Di Sản Hoàng Thành"
 * - 16 seals: "Bậc Thầy Khảo Cứu Cố Đô"
 */
export function getHonorsTitle(sealCount: number): HonorsTitleInfo {
  const count = Math.max(0, Math.min(16, sealCount));

  if (count === 16) {
    return {
      tier: "master",
      title: "Bậc Thầy Khảo Cứu Cố Đô",
      titleEn: "Master Heritage Researcher of the Ancient Capital",
      minSeals: 16,
      maxSeals: 16,
      badgeClass: "bg-amber-600 text-white border-amber-500 shadow-md",
      accentColor: "#C68A2C",
      descriptionVi:
        "Xuất sắc giải mã trọn vẹn 16 di tích kiến trúc và thu thập toàn bộ 16 con dấu triện son Hoàng triều trên khắp 4 phân khu Đại Nội Huế.",
      epigraphVi: "Long Vân Khánh Hội — Bác Cổ Thông Kim",
    };
  }

  if (count >= 12) {
    return {
      tier: "scholar",
      title: "Học Giả Di Sản Hoàng Thành",
      titleEn: "Imperial Heritage Scholar",
      minSeals: 12,
      maxSeals: 15,
      badgeClass: "bg-blue-700 text-white border-blue-600 shadow-sm",
      accentColor: "#1D5C86",
      descriptionVi:
        "Hoàn thành xuất sắc khảo cứu chuyên sâu phần lớn di tích Hoàng Thành và Tử Cấm Thành, tinh tường đối chiếu tư liệu chính sử triều Nguyễn.",
      epigraphVi: "Khai Trí Tầm Văn — Tinh Thông Cung Điện",
    };
  }

  if (count >= 8) {
    return {
      tier: "explorer",
      title: "Thám Hiểm Cung Đình Huế",
      titleEn: "Imperial Citadel Explorer",
      minSeals: 8,
      maxSeals: 11,
      badgeClass: "bg-emerald-700 text-white border-emerald-600 shadow-sm",
      accentColor: "#2F6F55",
      descriptionVi:
        "Khám phá vững vàng các trục không gian chính của Hoàng Thành, giải mã thành công hệ thống câu hỏi suy luận điền dã di sản.",
      epigraphVi: "Lý Hành Dấu Xưa — Thấu Triệt Cương Vực",
    };
  }

  if (count >= 4) {
    return {
      tier: "apprentice",
      title: "Tập Sự Khảo Cứu Di Sản",
      titleEn: "Heritage Research Apprentice",
      minSeals: 4,
      maxSeals: 7,
      badgeClass: "bg-rose-700 text-white border-rose-600 shadow-sm",
      accentColor: "#A62B2B",
      descriptionVi:
        "Đã bước đầu làm quen với phương pháp đọc hiểu bản đồ không ảnh trực giao và giải mã các di tích trọng điểm của triều đình.",
      epigraphVi: "Sơ Nhập Hoàng Môn — Học Hỏi Sử Tích",
    };
  }

  return {
    tier: "novice",
    title: "Người Khởi Đầu Khám Phá",
    titleEn: "Heritage Explorer Novice",
    minSeals: 0,
    maxSeals: 3,
    badgeClass: "bg-stone-500 text-white border-stone-400",
    accentColor: "#675C4E",
    descriptionVi:
      "Cần thu thập tối thiểu 4 ấn triện son di tích để chính thức được sắc phong danh hiệu khảo cứu di sản Cố đô Huế.",
    epigraphVi: "Tầm Tích Dấu Xưa — Bắt Đầu Hành Trình",
  };
}

/**
 * Computes breakdown of unlocked seals across all 4 spatial zones.
 */
export function getZoneBreakdown(unlockedSlugs: string[]): ZoneSealBreakdown[] {
  const set = new Set(unlockedSlugs);
  const zoneSlugs: SpatialZoneSlug[] = [
    "central-ceremonial-axis",
    "ancestral-worship-space",
    "purple-forbidden-city",
    "royal-living-gardens",
  ];

  return zoneSlugs.map((slug) => {
    const meta = PASSPORT_ZONE_META[slug];
    const seals = PASSPORT_SEALS.filter((s) => s.zoneSlug === slug);
    const sealsWithStatus = seals.map((s) => ({
      ...s,
      isUnlocked: set.has(s.slug),
    }));
    const unlockedCount = sealsWithStatus.filter((s) => s.isUnlocked).length;

    return {
      zoneSlug: slug,
      zoneTitleVi: meta?.title || slug,
      zoneTitleHanNom: meta?.titleHanNom || "",
      totalCount: seals.length,
      unlockedCount,
      isCompleted: unlockedCount === seals.length && seals.length > 0,
      seals: sealsWithStatus,
    };
  });
}

/**
 * Generates a unique royal certificate serial code.
 * Format: LN-DN-2026-XXXX-XXXX
 */
export function generateCertificateId(studentName?: string): string {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  const pick = (n: number) => {
    let s = "";
    for (let i = 0; i < n; i++) {
      s += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return s;
  };

  if (!studentName) {
    return `LN-DN-2026-${pick(4)}-${pick(4)}`;
  }

  // Generate deterministic-looking prefix for student
  const hash = Math.abs(
    studentName.split("").reduce((acc, c) => acc + c.charCodeAt(0), 108),
  )
    .toString(36)
    .toUpperCase()
    .padStart(4, "0")
    .slice(0, 4);

  return `LN-DN-2026-${hash}-${pick(4)}`;
}

/**
 * Formats a Date or date string into traditional Vietnamese royal decree date style.
 * Example: "Huế, ngày 16 tháng 10 năm 2026"
 */
export function formatImperialDate(inputDate?: string | Date): string {
  const date = inputDate
    ? typeof inputDate === "string"
      ? new Date(inputDate)
      : inputDate
    : new Date();

  const d = isNaN(date.getTime()) ? new Date() : date;
  const day = d.getDate();
  const month = d.getMonth() + 1;
  const year = d.getFullYear();

  return `Huế, ngày ${day} tháng ${month} năm ${year}`;
}

/**
 * Creates default initial certificate data.
 */
export function createDefaultCertificate(
  defaultDisplayName?: string | null,
): CertificateData {
  const name = defaultDisplayName?.trim() || "Nguyễn Hoàng Minh";
  return {
    id: generateCertificateId(name),
    studentName: name,
    schoolName: "Trường THPT Chuyên Quốc Học Huế",
    issueDate: formatImperialDate(new Date()),
    unlockedSiteSlugs: PASSPORT_SEALS.map((s) => s.slug),
    totalScore: 1600,
  };
}

/**
 * Loads certificate data from local storage or returns defaults.
 */
export function loadSavedCertificate(
  defaultDisplayName?: string | null,
): CertificateData {
  if (typeof window === "undefined") {
    return createDefaultCertificate(defaultDisplayName);
  }

  try {
    // 1. Try reading directly saved certificate state
    const saved = localStorage.getItem(CERTIFICATE_STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved) as CertificateData;
      if (parsed && parsed.id && Array.isArray(parsed.unlockedSiteSlugs)) {
        return parsed;
      }
    }

    // 2. Try checking if digital passport already unlocked seals
    const savedPassport = localStorage.getItem(PASSPORT_STORAGE_KEY);
    let passportSlugs: string[] = [];
    if (savedPassport) {
      const parsed = JSON.parse(savedPassport);
      if (Array.isArray(parsed)) {
        passportSlugs = parsed
          .map((item) => (typeof item === "string" ? item : item?.slug))
          .filter(Boolean);
      }
    }

    // 3. Try reading student name from passport student key
    const savedStudent = localStorage.getItem(PASSPORT_STUDENT_KEY);
    let studentName = defaultDisplayName?.trim() || "Nguyễn Hoàng Minh";
    let schoolName = "Trường THPT Chuyên Quốc Học Huế";
    if (savedStudent) {
      const parsed = JSON.parse(savedStudent);
      if (parsed.name) studentName = parsed.name;
      if (parsed.class) schoolName = parsed.class;
    }

    const cert = createDefaultCertificate(studentName);
    cert.schoolName = schoolName;

    if (passportSlugs.length > 0) {
      cert.unlockedSiteSlugs = passportSlugs;
      cert.totalScore = passportSlugs.length * 100;
    }

    return cert;
  } catch {
    return createDefaultCertificate(defaultDisplayName);
  }
}

/**
 * Saves current certificate state to local storage.
 */
export function saveCertificateData(data: CertificateData): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(CERTIFICATE_STORAGE_KEY, JSON.stringify(data));
  } catch {
    // Storage quota or private browsing fallback
  }
}

/**
 * Helper to build shareable / verifiable URL.
 */
export function buildCertificateUrl(
  origin: string,
  data: Pick<CertificateData, "id" | "studentName" | "schoolName" | "unlockedSiteSlugs">,
  verify = false,
): string {
  const params = new URLSearchParams();
  params.set("id", data.id);
  params.set("name", data.studentName);
  if (data.schoolName) {
    params.set("school", data.schoolName);
  }
  params.set("seals", data.unlockedSiteSlugs.length.toString());
  if (verify) {
    params.set("verify", "1");
  }
  return `${origin}/dai-noi/chung-nhan?${params.toString()}`;
}
