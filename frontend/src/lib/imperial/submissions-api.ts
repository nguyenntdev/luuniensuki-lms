/**
 * Verified student submissions and teacher assessment mock data & state management
 * for STTTNNĐ (Lưu Niên — Đại Nội Huế).
 * Ref: Spec (§20, S1-S4 Rubrics)
 */

import type { RubricScoreState, StudentSubmission } from "./map-types";
import { enqueueOfflineSubmission } from "./offline-sync";

export const INITIAL_STUDENT_SUBMISSIONS: StudentSubmission[] = [
  {
    id: "sub-001",
    monument_slug: "ngo-mon",
    monument_name_vi: "Ngọ Môn",
    trail_slug: "truc-dung-dao-quyen-luc",
    trail_title: "Trục Dũng Đạo & Quyền Lực Hoàng Triều",
    student_id: "stu-101",
    student_name: "Nguyễn Lê Hoàng Nam",
    student_class: "11 Sử — THPT Chuyên Quốc Học Huế",
    student_avatar: "https://api.dicebear.com/7.x/bottts/svg?seed=Nam",
    claim:
      "Ngọ Môn không chỉ đóng vai trò một cổng thành kiên cố mà cấu trúc 'năm cửa chín lầu' chính là công cụ trực quan hóa trật tự đẳng cấp tuyệt đối của nền quân chủ triều Nguyễn.",
    evidence:
      "Theo Khâm Định Đại Nam Hội Điển Sự Lệ (Quyển 78), cửa giữa lợp ngói lưu ly màu vàng 'chỉ dành cho Thiên tử đi', hai cửa Tả Giáp Môn và Hữu Giáp Môn lợp ngói màu xanh 'dành cho thân vương đại thần'. Hai cửa Dịch Môn khoét vòm đá cuội bên ngoài dành cho binh lính và voi ngựa kéo pháo.",
    evidence_citations: [
      "Khâm Định Đại Nam Hội Điển Sự Lệ, Quyển 78 (Công Bộ)",
      "Bản đồ không ảnh trực giao tỉ lệ 1:1 Đại Nội Huế",
    ],
    explanation:
      "Bằng chứng trên cho thấy sự phân chia vật chất (chất liệu đá, màu men ngói, chiều rộng lối đi) tương ứng chính xác với trật tự phẩm hàm xã hội. Bất kỳ ai bước đến Ngọ Môn đều bị ép buộc phải nhận thức ngay vị trí của mình so với đấng quân vương, từ đó phục tùng uy quyền tuyệt đối mà không cần dùng đến vũ lực.",
    notes: "Em đã đối chiếu với ảnh chụp lầu Ngũ Phụng của trường EFEO năm 1920 để xác thực kết cấu hàng cột gỗ lim.",
    submitted_at: "2026-10-14T08:30:00Z",
    status: "graded",
    scores: {
      s1_spatial: 3,
      s2_temporal: 3,
      s3_evidence: 3,
      s4_argument: 3,
      total: 12,
      normalized_10: 10.0,
    },
    teacher_feedback:
      "Bài làm xuất sắc! Lập luận sắc bén theo đúng mô hình M-E-E. Trích dẫn Hội Điển chính xác, liên hệ không gian kiến trúc với tư tưởng chính trị chặt chẽ. Đạt điểm tối đa cả 4 tiêu chuẩn S1-S4.",
    graded_at: "2026-10-14T10:15:00Z",
    graded_by: "TS. Trần Văn Thọ — GV Lịch sử",
  },
  {
    id: "sub-002",
    monument_slug: "dien-thai-hoa",
    monument_name_vi: "Điện Thái Hòa",
    trail_slug: "truc-dung-dao-quyen-luc",
    trail_title: "Trục Dũng Đạo & Quyền Lực Hoàng Triều",
    student_id: "stu-102",
    student_name: "Trần Mai Phương Thảo",
    student_class: "10 Văn — THPT Hai Bà Trưng Huế",
    student_avatar: "https://api.dicebear.com/7.x/bottts/svg?seed=Thao",
    claim:
      "Em kết luận rằng Điện Thái Hòa là biểu tượng đỉnh cao của khát vọng thái bình thịnh trị và khẳng định chủ quyền lãnh thổ độc lập của Đại Nam thông qua nghệ thuật 'nhất thi nhất họa'.",
    evidence:
      "Trên các liên ba bảng ngạch trong điện, vua Thiệu Trị đã khắc bài thơ khẳng định: 'Văn hiến thiên niên quốc / Sơn hà vạn dặm đồ' (Nước ngàn năm văn hiến / Bản đồ muôn dặm giang sơn). Hệ mái trùng thiềm điệp ốc gồm 80 cột gỗ lim thếp vàng vờn mây.",
    evidence_citations: [
      "Hồ sơ Di sản Tư liệu UNESCO: Thơ văn trên kiến trúc cung đình Huế",
      "Đại Nam Thực Lục Chính Biên (Tập 2, Kỷ Đệ Tam)",
    ],
    explanation:
      "Sự kết hợp giữa thơ văn chữ Hán thể hiện lòng tự hào dân tộc và không gian ngai vàng uy nghiêm tạo nên một bảo tàng tri thức sống, giáo dục thần dân và khẳng định vị thế bình đẳng với các vương triều phương Bắc.",
    submitted_at: "2026-10-15T01:45:00Z",
    status: "submitted",
  },
  {
    id: "sub-003",
    monument_slug: "the-to-mieu",
    monument_name_vi: "Thế Tổ Miếu",
    trail_slug: "khong-gian-ky-uc-tuong-niem",
    trail_title: "Không Gian Ký Ức & Tưởng Niệm Tổ Tiên",
    student_id: "stu-103",
    student_name: "Lê Quốc Bảo",
    student_class: "12 A1 — THPT Nguyễn Huệ",
    student_avatar: "https://api.dicebear.com/7.x/bottts/svg?seed=Bao",
    claim:
      "Thế Tổ Miếu được bố trí theo đúng nguyên tắc phong thủy và tông pháp 'Tả Chiêu Hữu Mục', tuy nhiên sự phối thờ các vua sau này cho thấy lịch sử đã điều chỉnh để vinh danh lòng yêu nước.",
    evidence:
      "Vua Gia Long ngự gian chính giữa. Đến năm 1959, Hội đồng Hoàng tộc và nhân dân đã rước bài vị của ba vị vua chống thực dân Pháp là Hàm Nghi, Thành Thái và Duy Tân vào phối thờ ở hai gian chái ngoài cùng.",
    evidence_citations: [
      "Biên bản khánh thành phối thờ di tích Thế Miếu (1959)",
      "Bản ảnh khảo sát gian thờ Thế Miếu",
    ],
    explanation:
      "Việc bổ sung này chứng minh không gian di sản không bị đóng băng trong quá khứ mà luôn vận động, tôn vinh những giá trị vì nước vì dân cao đẹp nhất của dân tộc.",
    submitted_at: "2026-10-15T03:10:00Z",
    status: "submitted",
  },
  {
    id: "sub-004",
    monument_slug: "dien-kien-trung",
    monument_name_vi: "Điện Kiến Trung",
    trail_slug: "tu-cam-thanh-bien-doi-phuc-hoi",
    trail_title: "Tử Cấm Thành — Biến Đổi Lịch Sử & Phục Hồi Di Sản",
    student_id: "stu-104",
    student_name: "Phạm Hồng Ngọc",
    student_class: "11 Chuyên Lịch Sử — Quốc Học Huế",
    student_avatar: "https://api.dicebear.com/7.x/bottts/svg?seed=Ngoc",
    claim:
      "Điện Kiến Trung là minh chứng sống động của phong cách nghệ thuật Đông Dương (Indochinois) tân cổ điển, phản ánh thời kỳ tiếp biến văn hóa sâu sắc giữa phương Tây và bản địa.",
    evidence:
      "Mặt tiền công trình có ban công thức cột Doric và vòm cửa kiểu Pháp, nhưng toàn bộ hoa văn tường và mái lại được nghệ nhân đắp nổi bằng hàng vạn mảnh sành sứ bát đĩa tạo hình rồng phượng, chữ Phúc Lộc Thọ.",
    evidence_citations: [
      "Bản vẽ Nha Công Chính Đông Dương (1923)",
      "Hồ sơ phục chế khánh thành năm 2024 của Trung tâm BTDT Cố đô Huế",
    ],
    explanation:
      "Công trình vừa đáp ứng nhu cầu tiện nghi sinh hoạt hiện đại kiểu phương Tây của vua Khải Định và Bảo Đại, vừa giữ vững bản sắc vương quyền Á Đông qua hình tượng rồng mây truyền thống.",
    submitted_at: "2026-10-15T04:20:00Z",
    status: "submitted",
  },
  {
    id: "sub-005",
    monument_slug: "cung-dien-tho",
    monument_name_vi: "Cung Diên Thọ",
    trail_slug: "doi-song-cung-dinh-dien-tho",
    trail_title: "Đời Sống Hoàng Gia & Cung Diên Thọ",
    student_id: "stu-105",
    student_name: "Võ Thị Quỳnh Anh",
    student_class: "10 Chuyên Địa Lý — Quốc Học Huế",
    student_avatar: "https://api.dicebear.com/7.x/bottts/svg?seed=QuynhAnh",
    claim:
      "Cung Diên Thọ được thiết kế như một quần thể 'vi khí hậu' biệt lập, tạo nên không gian an dưỡng thanh tịnh nhất Đại Nội dành cho Hoàng Thái Hậu.",
    evidence:
      "Phía trước có hồ sen Tạ Trường Du, chung quanh trồng nhiều bóng cây cổ thụ và tường hoa ngăn cách tiếng ồn ào từ bên ngoài. Các tòa nhà nối với nhau bằng hệ thống trường lang có mái che chống mưa Huế.",
    evidence_citations: [
      "Đại Nam Thực Lục (Kỷ Đệ Tứ)",
      "Bản đồ không ảnh tỷ lệ 1:1 khu vực Tây Bắc Hoàng Thành",
    ],
    explanation:
      "Không gian mặt nước làm giảm nhiệt độ mùa hè oi bức, trong khi trường lang bảo vệ sức khỏe người già trong mùa đông giá rét, thể hiện sự am hiểu khí hậu sâu sắc của kiến trúc truyền thống Huế.",
    submitted_at: "2026-10-13T14:15:00Z",
    status: "graded",
    scores: {
      s1_spatial: 3,
      s2_temporal: 2,
      s3_evidence: 2,
      s4_argument: 3,
      total: 10,
      normalized_10: 8.5,
    },
    teacher_feedback:
      "Phân tích không gian vi khí hậu rất tốt và sáng tạo (S1). Tuy nhiên cần bổ sung thêm dẫn chứng văn bản cụ thể về các đời Thái hậu cư ngụ tại đây để nâng điểm phần sử liệu (S3).",
    graded_at: "2026-10-14T07:20:00Z",
    graded_by: "Cô Đặng Thị Thu Hà — Tổ Lịch sử",
  },
];

const SUBMISSIONS_STORAGE_KEY = "luunien_imperial_student_submissions_v1";

export function loadStudentSubmissions(): StudentSubmission[] {
  if (typeof window === "undefined") {
    return INITIAL_STUDENT_SUBMISSIONS;
  }
  try {
    const raw = localStorage.getItem(SUBMISSIONS_STORAGE_KEY);
    if (!raw) {
      localStorage.setItem(SUBMISSIONS_STORAGE_KEY, JSON.stringify(INITIAL_STUDENT_SUBMISSIONS));
      return INITIAL_STUDENT_SUBMISSIONS;
    }
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed) && parsed.length > 0) {
      return parsed;
    }
  } catch (err) {
    console.warn("Failed reading student submissions from storage:", err);
  }
  return INITIAL_STUDENT_SUBMISSIONS;
}

export function saveStudentSubmission(newSub: Omit<StudentSubmission, "id" | "submitted_at" | "status">): StudentSubmission {
  const current = loadStudentSubmissions();
  const created: StudentSubmission = {
    ...newSub,
    id: `sub-${Date.now()}`,
    submitted_at: new Date().toISOString(),
    status: "submitted",
  };
  const updated = [created, ...current];
  if (typeof window !== "undefined") {
    localStorage.setItem(SUBMISSIONS_STORAGE_KEY, JSON.stringify(updated));
    // If client is currently offline, automatically enqueue in IndexedDB offline queue
    if (!navigator.onLine) {
      enqueueOfflineSubmission(newSub).catch((err) => {
        console.warn("[submissions-api] Failed to enqueue offline submission:", err);
      });
    }
  }
  return created;
}

export function gradeStudentSubmission(
  submissionId: string,
  scores: { s1: number; s2: number; s3: number; s4: number },
  feedback: string,
  teacherName: string,
): StudentSubmission | null {
  const current = loadStudentSubmissions();
  const total = scores.s1 + scores.s2 + scores.s3 + scores.s4;
  const normalized_10 = Number(((total / 12) * 10).toFixed(1));

  let matched: StudentSubmission | null = null;
  const updated = current.map((sub) => {
    if (sub.id === submissionId) {
      const g: StudentSubmission = {
        ...sub,
        status: "graded",
        scores: {
          s1_spatial: scores.s1,
          s2_temporal: scores.s2,
          s3_evidence: scores.s3,
          s4_argument: scores.s4,
          total,
          normalized_10,
        },
        teacher_feedback: feedback,
        graded_at: new Date().toISOString(),
        graded_by: teacherName,
      };
      matched = g;
      return g;
    }
    return sub;
  });

  if (typeof window !== "undefined") {
    localStorage.setItem(SUBMISSIONS_STORAGE_KEY, JSON.stringify(updated));
  }
  return matched;
}
