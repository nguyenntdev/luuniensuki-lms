/**
 * Verified student submissions and teacher assessment data & state management
 * for STTTNNĐ (Lưu Niên — Đại Nội Huế).
 * Ref: Spec (§20, S1-S4 Rubrics, V5-T031)
 */

import { apiRequest } from "@/lib/api";
import type { RubricScoreState, StudentSubmission } from "./map-types";
import { enqueueOfflineSubmission } from "./offline-sync";

/**
 * Isolated demo fixture data for evaluation / preview mode only.
 * STRICT ISOLATION: Must NEVER be injected into production journeys or empty local storage.
 */
export const DEMO_STUDENT_SUBMISSIONS: StudentSubmission[] = [
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

/**
 * Backward-compatibility alias for DEMO_STUDENT_SUBMISSIONS.
 * @deprecated Use DEMO_STUDENT_SUBMISSIONS with explicit demoMode flag.
 * Kept for test harnesses that specifically import INITIAL_STUDENT_SUBMISSIONS.
 */
export const INITIAL_STUDENT_SUBMISSIONS: StudentSubmission[] = DEMO_STUDENT_SUBMISSIONS;

const SUBMISSIONS_STORAGE_KEY = "luunien_imperial_student_submissions_v1";

export interface LoadStudentSubmissionsOptions {
  demoMode?: boolean;
}

/**
 * Loads student submissions.
 * In production mode (demoMode: false or undefined), strictly loads real saved submissions
 * from localStorage. If empty or uninitialized, returns empty list `[]`.
 * Never automatically injects mock/fictional records in production!
 */
export function loadStudentSubmissions(options?: LoadStudentSubmissionsOptions): StudentSubmission[] {
  if (options?.demoMode) {
    return DEMO_STUDENT_SUBMISSIONS;
  }
  if (typeof window === "undefined") {
    return [];
  }
  try {
    const raw = localStorage.getItem(SUBMISSIONS_STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) {
      return parsed;
    }
  } catch (err) {
    console.warn("Failed reading student submissions from storage:", err);
  }
  return [];
}

export function saveStudentSubmission(
  newSub: Omit<StudentSubmission, "id" | "submitted_at" | "status">,
  options?: LoadStudentSubmissionsOptions,
): StudentSubmission {
  const current = loadStudentSubmissions(options);
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
  options?: LoadStudentSubmissionsOptions,
): StudentSubmission | null {
  const current = loadStudentSubmissions(options);
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

export interface BackendSubmissionShape {
  id: string;
  activity_id: string;
  student_id: string;
  classroom_id?: string | null;
  status: "submitted" | "graded" | "resubmit_requested";
  answer_text: string;
  evidence_refs?: Array<string | { source_title?: string; quote?: string; chapter?: string }>;
  score?: number | null;
  rubric_scores?: Record<string, number> | null;
  feedback?: string | null;
  graded_by?: string | null;
  graded_at?: string | null;
  submitted_at: string;
  updated_at: string;
  row_version?: number;
  monument_slug?: string;
  monument_name_vi?: string;
  student_name?: string;
  student_class?: string;
}

export function mapBackendSubmissionToClient(s: BackendSubmissionShape): StudentSubmission {
  const rubrics = s.rubric_scores || {};
  const s1 = rubrics.s1_spatial ?? rubrics.S1_spatial ?? rubrics.s1 ?? 0;
  const s2 = rubrics.s2_temporal ?? rubrics.S2_temporal ?? rubrics.s2 ?? 0;
  const s3 = rubrics.s3_evidence ?? rubrics.S3_evidence ?? rubrics.s3 ?? 0;
  const s4 = rubrics.s4_argument ?? rubrics.S4_argument ?? rubrics.s4 ?? 0;
  const total = s.score != null ? s.score : s1 + s2 + s3 + s4;
  const normalized_10 = Number(((total / 12) * 10).toFixed(1));

  const evidenceCitations = (s.evidence_refs || []).map((e) => {
    if (typeof e === "string") return e;
    return `${e.source_title || ""}: ${e.quote || ""}`.trim();
  }).filter(Boolean);

  return {
    id: s.id,
    monument_slug: s.monument_slug || "ngo-mon",
    monument_name_vi: s.monument_name_vi || "Đại Nội Huế",
    student_id: s.student_id,
    student_name: s.student_name || `Học sinh (${s.student_id.slice(0, 8)})`,
    student_class: s.student_class || "Lớp Di sản Huế",
    claim: s.answer_text,
    evidence: (s.evidence_refs && typeof s.evidence_refs[0] === "object" && s.evidence_refs[0]?.quote)
      || (s.evidence_refs && typeof s.evidence_refs[0] === "string" && s.evidence_refs[0])
      || "Tư liệu thực địa khảo sát",
    evidence_citations: evidenceCitations.length > 0 ? evidenceCitations : ["Tư liệu khảo sát thực địa"],
    explanation: s.answer_text,
    submitted_at: s.submitted_at,
    status: s.status,
    scores: s.status === "graded" || s.score != null
      ? {
          s1_spatial: s1,
          s2_temporal: s2,
          s3_evidence: s3,
          s4_argument: s4,
          total,
          normalized_10,
        }
      : undefined,
    teacher_feedback: s.feedback || undefined,
    graded_at: s.graded_at || undefined,
    graded_by: s.graded_by || undefined,
  };
}

export interface FetchTeacherSubmissionsOptions {
  activityId?: string;
  classroomId?: string;
  demoMode?: boolean;
}

export async function fetchTeacherSubmissionsFromBackend(
  options?: string | FetchTeacherSubmissionsOptions,
): Promise<StudentSubmission[]> {
  const opts: FetchTeacherSubmissionsOptions =
    typeof options === "string" ? { activityId: options } : options || {};

  if (opts.demoMode) {
    return DEMO_STUDENT_SUBMISSIONS;
  }

  try {
    const queryParams = new URLSearchParams();
    if (opts.activityId) queryParams.set("activity_id", opts.activityId);
    if (opts.classroomId) queryParams.set("classroom_id", opts.classroomId);
    const qs = queryParams.toString() ? `?${queryParams.toString()}` : "";

    let data: BackendSubmissionShape[] | null = null;
    try {
      data = await apiRequest<BackendSubmissionShape[]>(
        `/api/v1/imperial/teacher/submissions${qs}`,
        { cache: "no-store" },
      );
    } catch {
      data = await apiRequest<BackendSubmissionShape[]>(
        `/api/v1/history/submissions${qs}`,
        { cache: "no-store" },
      );
    }

    if (Array.isArray(data)) {
      const serverSubs = data.map(mapBackendSubmissionToClient);
      const local = loadStudentSubmissions({ demoMode: false });
      const ids = new Set(serverSubs.map((s) => s.id));
      return [...serverSubs, ...local.filter((l) => !ids.has(l.id))];
    }
  } catch (err) {
    if (process.env.NODE_ENV !== "production") {
      console.warn("fetchTeacherSubmissionsFromBackend falling back to local:", err);
    }
  }
  return loadStudentSubmissions({ demoMode: false });
}

export async function gradeSubmissionWithApi(
  submissionId: string,
  scores: { s1: number; s2: number; s3: number; s4: number },
  feedback: string,
  teacherName?: string,
  options?: { demoMode?: boolean },
): Promise<StudentSubmission> {
  if (options?.demoMode || submissionId.startsWith("sub-")) {
    const local = gradeStudentSubmission(
      submissionId,
      scores,
      feedback,
      teacherName || "Giáo viên",
      options,
    );
    if (!local) throw new Error("Submission not found in local store");
    return local;
  }

  const total = scores.s1 + scores.s2 + scores.s3 + scores.s4;
  const payload = {
    score: total,
    rubric_scores: {
      s1_spatial: scores.s1,
      s2_temporal: scores.s2,
      s3_evidence: scores.s3,
      s4_argument: scores.s4,
    },
    feedback,
    status: "graded",
  };

  let res: BackendSubmissionShape;
  try {
    res = await apiRequest<BackendSubmissionShape>(
      `/api/v1/imperial/teacher/submissions/${submissionId}/grade`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
  } catch {
    res = await apiRequest<BackendSubmissionShape>(
      `/api/v1/history/submissions/${submissionId}/grade`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
  }

  const mapped = mapBackendSubmissionToClient(res);
  gradeStudentSubmission(submissionId, scores, feedback, teacherName || "Giáo viên", options);
  return mapped;
}

export interface PersistSubmissionOptions {
  assignmentId?: string;
  activityId?: string;
  idempotencyKey?: string;
  offlineQueueIfUnavailable?: boolean;
}

export interface SubmissionServerResponse {
  id: string;
  status: "submitted" | "graded" | "resubmit_requested";
  submitted_at: string;
  server_confirmed: boolean;
  idempotency_key?: string | null;
}

/**
 * Persists a student submission to the authoritative backend.
 * Enforces:
 * - Content validation (M-E-E).
 * - Offline safety: Offline browser CANNOT report server submitted.
 * - Idempotency handling: Re-submitting with the same key returns the existing server record.
 */
export async function persistStudentSubmissionToServer(
  newSub: Omit<StudentSubmission, "id" | "submitted_at" | "status">,
  options: PersistSubmissionOptions = {},
): Promise<StudentSubmission> {
  // 1. Content validation check
  const claim = (newSub.claim || "").trim();
  const evidence = (newSub.evidence || "").trim();
  const explanation = (newSub.explanation || "").trim();

  if (!claim || !evidence || !explanation) {
    throw new Error("INVALID_SUBMISSION_CONTENT: Mệnh đề (M), Bằng chứng (E) và Diễn giải (E) không được để trống");
  }

  // 2. Negative Abuse Protection: Check online status
  const isOnline = typeof navigator !== "undefined" && typeof navigator.onLine === "boolean" ? navigator.onLine : true;
  if (!isOnline) {
    if (options.offlineQueueIfUnavailable) {
      await enqueueOfflineSubmission(newSub);
    }
    throw new Error("CLIENT_OFFLINE: Offline client cannot fake a server-confirmed submission");
  }

  const idempotencyKey = options.idempotencyKey || `idem-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;

  // 3. If target assignmentId is provided, submit to history learning assignment endpoint
  if (options.assignmentId) {
    try {
      const response = await apiRequest<any>(
        `/api/v1/history/assignments/${options.assignmentId}/submit`,
        {
          method: "POST",
          body: JSON.stringify({
            submission_content: {
              claim: newSub.claim,
              evidence: newSub.evidence,
              evidence_citations: newSub.evidence_citations,
              explanation: newSub.explanation,
              notes: newSub.notes,
              monument_slug: newSub.monument_slug,
              monument_name_vi: newSub.monument_name_vi,
            },
            idempotency_key: idempotencyKey,
          }),
        },
      );

      const created: StudentSubmission = {
        ...newSub,
        id: String(response.id),
        submitted_at: response.submitted_at || new Date().toISOString(),
        status: response.status || "submitted",
        scores: response.score != null
          ? {
              s1_spatial: response.rubric_evaluation?.s1 ?? 0,
              s2_temporal: response.rubric_evaluation?.s2 ?? 0,
              s3_evidence: response.rubric_evaluation?.s3 ?? 0,
              s4_argument: response.rubric_evaluation?.s4 ?? 0,
              total: response.score,
              normalized_10: Number(((response.score / 12) * 10).toFixed(1)),
            }
          : undefined,
        teacher_feedback: response.teacher_feedback || undefined,
      };

      // Sync into local list for offline lookup cache
      const current = loadStudentSubmissions();
      const updated = [created, ...current.filter((c) => c.id !== created.id)];
      if (typeof window !== "undefined") {
        localStorage.setItem(SUBMISSIONS_STORAGE_KEY, JSON.stringify(updated));
      }
      return created;
    } catch (err: any) {
      if (options.offlineQueueIfUnavailable) {
        await enqueueOfflineSubmission(newSub);
      }
      throw err;
    }
  }

  // 4. Default: submit to imperial activity submissions endpoint
  const targetActivityId = options.activityId || (newSub as any).activity_id;
  if (targetActivityId) {
    try {
      const response = await apiRequest<BackendSubmissionShape>(
        `/api/v1/imperial/activities/${targetActivityId}/submissions`,
        {
          method: "POST",
          body: JSON.stringify({
            answer_text: `${claim}\n\n${explanation}`,
            evidence_refs: newSub.evidence_citations && newSub.evidence_citations.length > 0
              ? newSub.evidence_citations.map((c) => ({ source_title: c, quote: evidence }))
              : [{ source_title: "Khảo sát thực địa", quote: evidence }],
          }),
        },
      );
      const created = mapBackendSubmissionToClient(response);
      created.monument_slug = newSub.monument_slug;
      created.monument_name_vi = newSub.monument_name_vi;
      created.student_name = newSub.student_name;
      created.student_class = newSub.student_class;
      created.claim = claim;
      created.evidence = evidence;
      created.explanation = explanation;

      const current = loadStudentSubmissions();
      const updated = [created, ...current.filter((c) => c.id !== created.id)];
      if (typeof window !== "undefined") {
        localStorage.setItem(SUBMISSIONS_STORAGE_KEY, JSON.stringify(updated));
      }
      return created;
    } catch (err: any) {
      if (options.offlineQueueIfUnavailable) {
        await enqueueOfflineSubmission(newSub);
      }
      throw err;
    }
  }

  // If no network endpoints matched, local save with offline queueing
  return saveStudentSubmission(newSub);
}

export async function fetchSubmissionAuditFromBackend(submissionId: string): Promise<any[]> {
  try {
    return await apiRequest<any[]>(`/api/v1/imperial/submissions/${submissionId}/audit`);
  } catch {
    return [];
  }
}
