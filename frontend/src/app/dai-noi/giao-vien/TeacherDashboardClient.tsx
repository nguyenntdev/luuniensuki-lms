"use client";

import React, { useState, useMemo, useEffect } from "react";
import Link from "next/link";
import {
  ArrowUpDown,
  Award,
  BookOpen,
  Calendar,
  CheckCircle2,
  Clock,
  Download,
  Eye,
  FileCheck2,
  FileText,
  Filter,
  GraduationCap,
  HelpCircle,
  Layers,
  MapPin,
  RefreshCw,
  Route,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  Printer,
  UserCheck,
  Users,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { useAuthStore } from "@/stores/authStore";
import {
  gradeStudentSubmission,
  gradeSubmissionWithApi,
  loadStudentSubmissions,
  fetchTeacherSubmissionsFromBackend,
  fetchSubmissionAuditFromBackend,
} from "@/lib/imperial/submissions-api";
import type { StudentSubmission } from "@/lib/imperial/map-types";
import { exportGradebookToCSV } from "@/lib/imperial/rubric-engine";
import RubricRadarChart from "@/components/imperial/dossier/RubricRadarChart";
import { IMPERIAL_TRAILS } from "@/lib/imperial/trails-data";
import type { AssignmentRelease } from "@/lib/imperial/v51-types";
import {
  fetchTeacherAssignments,
  createTeacherAssignment,
} from "@/lib/imperial/v51-api";
import {
  listClasses,
  fetchClassroomGradebook,
  exportClassroomGradebookCsv,
  type ClassroomGradebookResponse,
  type ClassroomGradebookStudent,
} from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const DEFAULT_FALLBACK_GRADEBOOK: ClassroomGradebookResponse = {
  classroom_id: "cls-001",
  classroom_name: "Lớp 10A1 — THPT Chuyên Quốc Học Huế",
  teacher_id: "teacher-001",
  total_students: 5,
  metrics: {
    total_students: 5,
    completed_count: 2,
    pending_count: 2,
    missing_count: 1,
    average_score: 8.8,
    average_completion_percent: 74.5,
  },
  roster: [
    {
      student_id: "stu-101",
      display_name: "Nguyễn Lê Hoàng Nam",
      email: "nam.nguyen@quochoc.edu.vn",
      role: "learner",
      avatar_url: null,
      joined_at: "2026-09-05T08:00:00Z",
      overall_completion_percent: 92.0,
      total_xp: 450,
      quizzes_passed: 4,
      avg_quiz_score: 9.5,
      assignments: [
        {
          assignment_id: "assign-01",
          title: "Khảo sát Ngọ Môn & Trục Dũng Đạo",
          due_at: "2026-10-20T17:00:00Z",
          status: "completed",
          score: 10.0,
          completed_at: "2026-10-14T08:30:00Z",
          is_missing: false,
          is_pending: false,
        },
      ],
      completed_count: 1,
      pending_count: 0,
      missing_count: 0,
      status: "completed",
    },
    {
      student_id: "stu-102",
      display_name: "Trần Mai Phương Thảo",
      email: "thao.tran@haibatrung.edu.vn",
      role: "learner",
      avatar_url: null,
      joined_at: "2026-09-06T09:30:00Z",
      overall_completion_percent: 65.0,
      total_xp: 280,
      quizzes_passed: 2,
      avg_quiz_score: 8.0,
      assignments: [
        {
          assignment_id: "assign-01",
          title: "Khảo sát Điện Thái Hòa & Nhất Thi Nhất Họa",
          due_at: "2026-10-30T17:00:00Z",
          status: "submitted",
          score: null,
          completed_at: null,
          is_missing: false,
          is_pending: true,
        },
      ],
      completed_count: 0,
      pending_count: 1,
      missing_count: 0,
      status: "pending",
    },
    {
      student_id: "stu-103",
      display_name: "Lê Quốc Bảo",
      email: "bao.le@nguyenhue.edu.vn",
      role: "learner",
      avatar_url: null,
      joined_at: "2026-09-10T07:45:00Z",
      overall_completion_percent: 45.0,
      total_xp: 150,
      quizzes_passed: 1,
      avg_quiz_score: 7.0,
      assignments: [
        {
          assignment_id: "assign-01",
          title: "Khảo sát Thế Tổ Miếu & Bài Vị Ba Vua",
          due_at: "2026-10-10T17:00:00Z",
          status: "missing",
          score: null,
          completed_at: null,
          is_missing: true,
          is_pending: false,
        },
      ],
      completed_count: 0,
      pending_count: 0,
      missing_count: 1,
      status: "missing",
    },
    {
      student_id: "stu-104",
      display_name: "Phạm Hồng Ngọc",
      email: "ngoc.pham@quochoc.edu.vn",
      role: "learner",
      avatar_url: null,
      joined_at: "2026-09-05T08:00:00Z",
      overall_completion_percent: 85.0,
      total_xp: 390,
      quizzes_passed: 3,
      avg_quiz_score: 9.0,
      assignments: [
        {
          assignment_id: "assign-01",
          title: "Khảo sát Điện Kiến Trung & Nghệ Thuật Khảm Sành Sứ",
          due_at: "2026-10-25T17:00:00Z",
          status: "in_progress",
          score: null,
          completed_at: null,
          is_missing: false,
          is_pending: true,
        },
      ],
      completed_count: 0,
      pending_count: 1,
      missing_count: 0,
      status: "pending",
    },
    {
      student_id: "stu-105",
      display_name: "Võ Thị Quỳnh Anh",
      email: "quynhanh.vo@quochoc.edu.vn",
      role: "learner",
      avatar_url: null,
      joined_at: "2026-09-05T08:00:00Z",
      overall_completion_percent: 88.0,
      total_xp: 410,
      quizzes_passed: 4,
      avg_quiz_score: 8.8,
      assignments: [
        {
          assignment_id: "assign-01",
          title: "Khảo sát Cung Diên Thọ & Vi Khí Hậu",
          due_at: "2026-10-18T17:00:00Z",
          status: "completed",
          score: 8.5,
          completed_at: "2026-10-14T07:20:00Z",
          is_missing: false,
          is_pending: false,
        },
      ],
      completed_count: 1,
      pending_count: 0,
      missing_count: 0,
      status: "completed",
    },
  ],
};

// Standard Rubric S1-S4 Level Descriptions (Spec §20)
const RUBRIC_CRITERIA = {
  S1: {
    title: "S1 • Năng lực Không gian (Spatial Reasoning)",
    description: "Nhận diện vị trí, hướng trục Dũng Đạo, trật tự phân tầng không gian và phương vị phong thủy.",
    levels: [
      { score: 0, label: "Chưa đạt (0đ)", desc: "Chưa xác định được vị trí hoặc nhầm lẫn nghiêm trọng về không gian di tích." },
      { score: 1, label: "Cơ bản (1đ)", desc: "Xác định được công trình đơn lẻ nhưng chưa thấy mối liên hệ với trục quy hoạch chung." },
      { score: 2, label: "Khá (2đ)", desc: "Xác định chính xác vị trí, hướng nhìn và vai trò của công trình trên trục Dũng Đạo." },
      { score: 3, label: "Xuất sắc (3đ)", desc: "Phân tích sâu sắc vị thế phong thủy, trục thần đạo và sự phân tầng không gian quyền lực." },
    ],
  },
  S2: {
    title: "S2 • Năng lực Thời gian (Temporal Dimension)",
    description: "Nhận diện mốc khởi dựng, các giai đoạn trùng tu, tác động của chiến tranh và phục hồi di sản.",
    levels: [
      { score: 0, label: "Chưa đạt (0đ)", desc: "Không nêu hoặc nêu sai mốc thời gian lịch sử của di tích." },
      { score: 1, label: "Cơ bản (1đ)", desc: "Nêu được niên đại khởi công xây dựng cơ bản (triều vua Gia Long hoặc Minh Mạng)." },
      { score: 2, label: "Khá (2đ)", desc: "Nêu đúng các mốc biến thiên: khởi dựng, tái thiết thời Khải Định và tổn thất chiến tranh." },
      { score: 3, label: "Xuất sắc (3đ)", desc: "Đặt công trình vào bối cảnh lịch sử cụ thể, phân tích ý nghĩa phục hồi di sản thời hiện đại." },
    ],
  },
  S3: {
    title: "S3 • Năng lực Sử liệu (Historical Evidence)",
    description: "Khai thác chính ngạch: Đại Nam Thực Lục, Hội Điển Sự Lệ, châu bản, văn khắc và ảnh tư liệu.",
    levels: [
      { score: 0, label: "Chưa đạt (0đ)", desc: "Không có dẫn chứng sử liệu hoặc chỉ đưa ra nhận định cảm tính không căn cứ." },
      { score: 1, label: "Cơ bản (1đ)", desc: "Có dẫn chứng chung chung nhưng không rõ nguồn gốc hoặc chưa đối chiếu kiểm chứng." },
      { score: 2, label: "Khá (2đ)", desc: "Trích dẫn đúng tên văn bản chính sử triều Nguyễn hoặc tư liệu ảnh lưu trữ Pháp (EFEO)." },
      { score: 3, label: "Xuất sắc (3đ)", desc: "Phê phán và đối chiếu đa nguồn: kết hợp chính sử triều Nguyễn, ảnh tư liệu và khảo cổ học." },
    ],
  },
  S4: {
    title: "S4 • Năng lực Lập luận (Historical Argumentation)",
    description: "Cấu trúc câu trả lời theo mô hình M-E-E, logic mạch lạc, phân biệt giữa sự thật và suy diễn.",
    levels: [
      { score: 0, label: "Chưa đạt (0đ)", desc: "Thiếu lập luận, câu trả lời mâu thuẫn hoặc chưa cấu trúc thành mệnh đề hoàn chỉnh." },
      { score: 1, label: "Cơ bản (1đ)", desc: "Lập luận đơn giản, có nêu mệnh đề nhưng mối liên kết với bằng chứng còn rời rạc." },
      { score: 2, label: "Khá (2đ)", desc: "Lập luận mạch lạc theo mô hình M-E-E: Mệnh đề rõ, Bằng chứng khớp, Diễn giải logic." },
      { score: 3, label: "Xuất sắc (3đ)", desc: "Lập luận sắc bén, có tư duy phản biện, phân biệt rõ sự thật lịch sử và cách diễn giải đương đại." },
    ],
  },
};

const QUICK_FEEDBACK_PROMPTS = [
  "Bài làm xuất sắc! Lập luận theo mô hình M-E-E rất mạch lạc, trích dẫn Hội Điển chính xác.",
  "Phân tích không gian trục Dũng Đạo rất chuẩn xác (S1). Cần đào sâu thêm tư duy phản biện.",
  "Cần bổ sung thêm dẫn chứng văn bản từ Đại Nam Thực Lục để củng cố độ tin cậy của mệnh đề (S3).",
  "Phát hiện rất độc đáo về sự phối hợp giữa kiến trúc và cảnh quan phong thủy vi khí hậu.",
  "Mệnh đề rõ ràng nhưng phần diễn giải (Explanation) cần chỉ rõ hơn mối liên hệ nhân quả.",
];

export default function TeacherDashboardClient() {
  const user = useAuthStore((s) => s.user);

  // Teacher / Staff Role Verification
  const isTeacherRole =
    Boolean(user) &&
    ["teacher", "staff", "admin", "super_admin", "editor", "reviewer"].includes(
      user?.role || "",
    );

  // Teacher Demo Mode toggle (allows learners/evaluators to test the grading workflow)
  const [demoMode, setDemoMode] = useState<boolean>(!isTeacherRole);

  // Submissions State
  const [submissions, setSubmissions] = useState<StudentSubmission[]>(() => {
    return loadStudentSubmissions({ demoMode: !isTeacherRole });
  });
  const [isLoadingSubmissions, setIsLoadingSubmissions] = useState<boolean>(false);
  const [loadingError, setLoadingError] = useState<string | null>(null);

  // Filter States
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "submitted" | "graded">("all");
  const [classFilter, setClassFilter] = useState<string>("all");

  // Grading Drawer State
  const [selectedSubmission, setSelectedSubmission] = useState<StudentSubmission | null>(null);
  const [isGradingOpen, setIsGradingOpen] = useState(false);
  const [isSavingGrade, setIsSavingGrade] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccessMessage, setSaveSuccessMessage] = useState<string | null>(null);
  const [submissionAuditTrail, setSubmissionAuditTrail] = useState<any[]>([]);
  const [isLoadingAudit, setIsLoadingAudit] = useState(false);

  // Server sync on mount if teacher role or update when demoMode changes
  useEffect(() => {
    if (demoMode) {
      setSubmissions(loadStudentSubmissions({ demoMode: true }));
      setLoadingError(null);
      return;
    }

    if (isTeacherRole) {
      setIsLoadingSubmissions(true);
      fetchTeacherSubmissionsFromBackend({ demoMode: false })
        .then((subs) => {
          setSubmissions(subs);
          setLoadingError(null);
        })
        .catch((err) => {
          console.warn("Failed fetching server submissions:", err);
          setLoadingError("Không thể đồng bộ danh sách bài nộp từ máy chủ.");
        })
        .finally(() => {
          setIsLoadingSubmissions(false);
        });
    } else {
      setSubmissions(loadStudentSubmissions({ demoMode: false }));
    }
  }, [isTeacherRole, demoMode]);

  // Grading Form State (Scores S1-S4)
  const [s1Score, setS1Score] = useState<number>(2);
  const [s2Score, setS2Score] = useState<number>(2);
  const [s3Score, setS3Score] = useState<number>(2);
  const [s4Score, setS4Score] = useState<number>(2);
  const [feedbackText, setFeedbackText] = useState<string>("");

  // Open grading drawer and prefill scores if already graded
  const handleOpenGrading = (sub: StudentSubmission) => {
    setSelectedSubmission(sub);
    setSaveError(null);
    setSaveSuccessMessage(null);
    if (sub.scores) {
      setS1Score(sub.scores.s1_spatial);
      setS2Score(sub.scores.s2_temporal);
      setS3Score(sub.scores.s3_evidence);
      setS4Score(sub.scores.s4_argument);
    } else {
      setS1Score(2);
      setS2Score(2);
      setS3Score(2);
      setS4Score(2);
    }
    setFeedbackText(sub.teacher_feedback || "");
    setIsGradingOpen(true);

    // Fetch audit history / revisions
    setIsLoadingAudit(true);
    fetchSubmissionAuditFromBackend(sub.id)
      .then((history: any[]) => {
        setSubmissionAuditTrail(history || []);
      })
      .catch((err: unknown) => {
        console.warn("Failed loading submission audit:", err);
        setSubmissionAuditTrail([]);
      })
      .finally(() => {
        setIsLoadingAudit(false);
      });
  };

  // Live Score Calculations
  const totalScore = s1Score + s2Score + s3Score + s4Score; // 0 - 12
  const normalized10 = Number(((totalScore / 12) * 10).toFixed(1)); // 0.0 - 10.0

  // Save Grade Handler
  const handleSaveGrade = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSubmission) return;

    // Negative abuse check: unauthorized students cannot forge a graded status
    if (!isTeacherRole && !demoMode) {
      setSaveError("Bạn không có quyền giáo viên để chấm điểm bài nộp này.");
      return;
    }

    const teacherName =
      user?.display_name || user?.username || "Thầy Trần Văn Thọ — Tổ Lịch sử";

    setIsSavingGrade(true);
    setSaveError(null);

    try {
      const updated = await gradeSubmissionWithApi(
        selectedSubmission.id,
        { s1: s1Score, s2: s2Score, s3: s3Score, s4: s4Score },
        feedbackText.trim() || "Bài làm đạt yêu cầu theo chuẩn Rubric S1-S4.",
        teacherName,
        { demoMode },
      );

      if (updated) {
        setSubmissions((prev) =>
          prev.map((item) => (item.id === updated.id ? updated : item)),
        );
        setSelectedSubmission(updated);
        setSaveSuccessMessage("Đã lưu điểm và ghi nhận lịch sử kiểm toán thành công.");
      }
      setTimeout(() => {
        setIsGradingOpen(false);
        setIsSavingGrade(false);
      }, 500);
    } catch (err: any) {
      console.error("Grading failed:", err);
      if (err?.status === 403) {
        setSaveError("Lỗi 403: Không có quyền giáo viên/thẩm định để thực hiện chấm điểm.");
      } else {
        setSaveError(err?.message || "Không thể lưu điểm vào hệ thống máy chủ.");
      }
      setIsSavingGrade(false);
    }
  };

  // Distinct Classes for Filter Dropdown
  const uniqueClasses = useMemo(() => {
    const set = new Set<string>();
    submissions.forEach((s) => {
      if (s.student_class) set.add(s.student_class);
    });
    return Array.from(set);
  }, [submissions]);

  // Filtered Submissions
  const filteredSubmissions = useMemo(() => {
    return submissions.filter((sub) => {
      if (statusFilter !== "all" && sub.status !== statusFilter) return false;
      if (classFilter !== "all" && sub.student_class !== classFilter) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchStudent = sub.student_name.toLowerCase().includes(q);
        const matchMonument = (sub.monument_name_vi || "").toLowerCase().includes(q);
        const matchClaim = sub.claim.toLowerCase().includes(q);
        const matchClass = sub.student_class.toLowerCase().includes(q);
        if (!matchStudent && !matchMonument && !matchClaim && !matchClass) {
          return false;
        }
      }
      return true;
    });
  }, [submissions, statusFilter, classFilter, searchQuery]);

  // Aggregate Metrics
  const stats = useMemo(() => {
    const total = submissions.length;
    const graded = submissions.filter((s) => s.status === "graded").length;
    const pending = total - graded;

    const scoresSum = submissions
      .filter((s) => s.scores?.total !== undefined)
      .reduce((acc, curr) => acc + (curr.scores?.total || 0), 0);
    const avgScore = graded > 0 ? (scoresSum / graded).toFixed(1) : "0.0";
    const avgNormalized = graded > 0 ? (((Number(avgScore) / 12) * 10).toFixed(1)) : "0.0";

    return { total, graded, pending, avgScore, avgNormalized };
  }, [submissions]);

  // Assignments State & Create Modal
  const [assignments, setAssignments] = useState<AssignmentRelease[]>([]);
  const [isCreateAssignmentOpen, setIsCreateAssignmentOpen] = useState(false);
  const [editingAssignmentId, setEditingAssignmentId] = useState<string | null>(null);
  const [assignmentClass, setAssignmentClass] = useState("Lớp 10A1 — THPT Quốc Học Huế");
  const [assignmentTitle, setAssignmentTitle] = useState("Khảo sát trục nghi lễ Ngọ Môn — Điện Thái Hòa");
  const [assignmentJourney, setAssignmentJourney] = useState(IMPERIAL_TRAILS[0]?.slug || "truc-chinh-dao-hoang-thanh");
  const [assignmentDueDate, setAssignmentDueDate] = useState(() => {
    const d = new Date(Date.now() + 7 * 86400000);
    return d.toISOString().slice(0, 10);
  });
  // Rubric weights on 0-4 scale per criterion
  const [rubricWeightS1, setRubricWeightS1] = useState<number>(3);
  const [rubricWeightS2, setRubricWeightS2] = useState<number>(2);
  const [rubricWeightS3, setRubricWeightS3] = useState<number>(3);
  const [rubricWeightS4, setRubricWeightS4] = useState<number>(2);
  const [idorWarning, setIdorWarning] = useState<string | null>(null);

  // Fetch teacher assignments on mount
  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        const data = await fetchTeacherAssignments();
        if (mounted) setAssignments(data);
      } catch (err) {
        console.error("Failed to fetch teacher assignments:", err);
      }
    }
    load();
    return () => {
      mounted = false;
    };
  }, []);

  const handleOpenCreateAssignment = () => {
    setEditingAssignmentId(null);
    setAssignmentClass("Lớp 10A1 — THPT Quốc Học Huế");
    setAssignmentTitle("Khảo sát trục nghi lễ Ngọ Môn — Điện Thái Hòa");
    setAssignmentJourney(IMPERIAL_TRAILS[0]?.slug || "truc-chinh-dao-hoang-thanh");
    setRubricWeightS1(3);
    setRubricWeightS2(2);
    setRubricWeightS3(3);
    setRubricWeightS4(2);
    setIdorWarning(null);
    setIsCreateAssignmentOpen(true);
  };

  const handleOpenEditAssignment = (assign: AssignmentRelease) => {
    // IDOR Protection: verify current teacher owns the assignment
    const isOwner =
      demoMode ||
      !assign.teacher_id ||
      assign.teacher_id === user?.id ||
      assign.class_name.includes(user?.username || "");

    if (!isOwner) {
      setIdorWarning(
        `Cảnh báo an toàn (IDOR): Bạn chỉ có quyền chỉnh sửa bài tập của lớp do bạn phụ trách. Bài tập này thuộc giáo viên khác.`,
      );
      return;
    }

    setEditingAssignmentId(assign.id);
    setAssignmentClass(assign.class_name);
    setAssignmentTitle(assign.title);
    setAssignmentJourney(assign.journey_slug);
    if (assign.due_date) {
      setAssignmentDueDate(assign.due_date.slice(0, 10));
    }
    if (assign.rubric_weights) {
      setRubricWeightS1(assign.rubric_weights.S1_spatial ?? 3);
      setRubricWeightS2(assign.rubric_weights.S2_temporal ?? 2);
      setRubricWeightS3(assign.rubric_weights.S3_evidence ?? 3);
      setRubricWeightS4(assign.rubric_weights.S4_argument ?? 2);
    }
    setIdorWarning(null);
    setIsCreateAssignmentOpen(true);
  };

  const handleSaveAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload: Partial<AssignmentRelease> = {
      id: editingAssignmentId || undefined,
      teacher_id: user?.id,
      class_name: assignmentClass.trim() || "Lớp học di sản Huế",
      title: assignmentTitle.trim() || "Bài tập khảo sát di sản",
      journey_slug: assignmentJourney,
      due_date: assignmentDueDate ? new Date(assignmentDueDate).toISOString() : null,
      rubric_weights: {
        S1_spatial: rubricWeightS1,
        S2_temporal: rubricWeightS2,
        S3_evidence: rubricWeightS3,
        S4_argument: rubricWeightS4,
      },
      is_active: true,
    };

    try {
      const created = await createTeacherAssignment(payload);
      if (editingAssignmentId) {
        setAssignments((prev) =>
          prev.map((a) => (a.id === editingAssignmentId ? { ...a, ...created } : a)),
        );
      } else {
        setAssignments((prev) => [created, ...prev]);
      }
      setIsCreateAssignmentOpen(false);
    } catch (err) {
      console.error("Failed to save assignment:", err);
    }
  };

  // Export CSV (Standard)
  const handleExportCSV = () => {
    const csvContent = exportGradebookToCSV(filteredSubmissions);
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Danh_sach_cham_diem_Dai_Noi_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Export CSV (Anonymized Student IDs)
  const handleExportAnonymizedCSV = () => {
    const csvContent = exportGradebookToCSV(filteredSubmissions, {
      anonymize: true,
      anonymizePrefix: "HS-ANON-",
    });
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Danh_sach_cham_diem_AN_DANH_Dai_Noi_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // ========================================================================= //
  // Classroom Gradebook & Real Roster State (V5.1 / W03-A06)
  // ========================================================================= //
  const [classrooms, setClassrooms] = useState<Array<{ id: string; name: string }>>([
    { id: "demo-10a1", name: "Lớp 10A1 — THPT Chuyên Quốc Học Huế" },
    { id: "demo-10v", name: "Lớp 10 Chuyên Văn — THPT Hai Bà Trưng Huế" },
  ]);
  const [selectedClassroomId, setSelectedClassroomId] = useState<string>("demo-10a1");
  const [gradebookData, setGradebookData] = useState<ClassroomGradebookResponse>(DEFAULT_FALLBACK_GRADEBOOK);
  const [isGradebookLoading, setIsGradebookLoading] = useState<boolean>(false);
  const [gradebookStatusFilter, setGradebookStatusFilter] = useState<"all" | "missing" | "pending" | "completed">("all");
  const [gradebookSearch, setGradebookSearch] = useState<string>("");
  const [exportError, setExportError] = useState<string | null>(null);
  const [exportSuccess, setExportSuccess] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState<boolean>(false);

  // Load teacher classrooms on mount
  useEffect(() => {
    let mounted = true;
    async function loadClasses() {
      try {
        const clsList = await listClasses();
        if (mounted && Array.isArray(clsList) && clsList.length > 0) {
          const formatted = clsList.map((c: any) => ({
            id: String(c.id),
            name: c.name || `Lớp ${c.class_code || c.id}`,
          }));
          setClassrooms(formatted);
          setSelectedClassroomId(formatted[0].id);
        }
      } catch (err) {
        // Fallback to initial demo classrooms if offline or unauthorized
      }
    }
    loadClasses();
    return () => {
      mounted = false;
    };
  }, []);

  // Fetch gradebook when selected classroom changes or filters change
  useEffect(() => {
    let mounted = true;
    async function loadGradebook() {
      if (!selectedClassroomId || selectedClassroomId.startsWith("demo-")) {
        return;
      }
      setIsGradebookLoading(true);
      try {
        const data = await fetchClassroomGradebook({
          classroomId: selectedClassroomId,
          statusFilter: gradebookStatusFilter,
          search: gradebookSearch,
        });
        if (mounted && data) {
          setGradebookData(data);
          setExportError(null);
        }
      } catch (err: any) {
        if (mounted) {
          if (err?.status === 403 || err?.message?.includes("403")) {
            setExportError(
              "Cảnh báo phân quyền (403 Forbidden): Bạn không có quyền truy cập sổ điểm của lớp học này (Bảo vệ Horizontal Privilege Escalation).",
            );
          }
        }
      } finally {
        if (mounted) setIsGradebookLoading(false);
      }
    }
    loadGradebook();
    return () => {
      mounted = false;
    };
  }, [selectedClassroomId, gradebookStatusFilter, gradebookSearch]);

  // Displayed Roster computed with local or server data
  const displayedRoster = useMemo(() => {
    const list = gradebookData?.roster || DEFAULT_FALLBACK_GRADEBOOK.roster;
    return list.filter((student) => {
      if (gradebookStatusFilter !== "all" && student.status !== gradebookStatusFilter) {
        return false;
      }
      if (gradebookSearch.trim()) {
        const q = gradebookSearch.toLowerCase().trim();
        const matchName = student.display_name.toLowerCase().includes(q);
        const matchEmail = student.email.toLowerCase().includes(q);
        const matchId = student.student_id.toLowerCase().includes(q);
        if (!matchName && !matchEmail && !matchId) {
          return false;
        }
      }
      return true;
    });
  }, [gradebookData, gradebookStatusFilter, gradebookSearch]);

  // Authenticated CSV Export for Gradebook
  const handleExportBackendGradebook = async (anonymize: boolean) => {
    setExportError(null);
    setExportSuccess(null);
    setIsExporting(true);

    try {
      if (selectedClassroomId && !selectedClassroomId.startsWith("demo-")) {
        const csvContent = await exportClassroomGradebookCsv({
          classroomId: selectedClassroomId,
          statusFilter: gradebookStatusFilter,
          search: gradebookSearch,
          anonymize,
        });
        const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        const anonTag = anonymize ? "_AN_DANH" : "";
        a.download = `Bang_diem_lop_${selectedClassroomId}${anonTag}_${new Date().toISOString().slice(0, 10)}.csv`;
        a.click();
        URL.revokeObjectURL(url);
        setExportSuccess(`Xuất sổ điểm CSV ${anonymize ? "ẩn danh" : "chính thức"} thành công!`);
      } else {
        // Local fallback export for demo mode / testing
        const currentClassName =
          classrooms.find((c) => c.id === selectedClassroomId)?.name ||
          gradebookData?.classroom_name ||
          "Lớp học di sản Huế";

        const headers = [
          "Mã học sinh",
          "Họ và tên",
          "Email",
          "Lớp học",
          "Tiến độ hoàn thành (%)",
          "Tổng XP",
          "Số bài trắc nghiệm đạt",
          "Điểm TB trắc nghiệm",
          "Bài tập hoàn thành",
          "Bài tập chờ nộp/chấm (Pending)",
          "Bài tập trễ hạn (Missing)",
          "Trạng thái chung",
        ];

        const rows = displayedRoster.map((s, idx) => {
          const sCode = anonymize ? `HS-ANON-${String(idx + 1).padStart(3, "0")}` : s.student_id;
          const sName = anonymize ? `Học sinh ${idx + 1}` : s.display_name;
          const sEmail = anonymize ? `anon_${idx + 1}@hidden.local` : s.email;
          const statusVi =
            s.status === "missing"
              ? "Trễ hạn (Missing)"
              : s.status === "pending"
                ? "Đang chờ (Pending)"
                : "Hoàn thành (Completed)";

          return [
            sCode,
            sName,
            sEmail,
            currentClassName,
            `${s.overall_completion_percent}%`,
            s.total_xp,
            s.quizzes_passed,
            s.avg_quiz_score,
            s.completed_count,
            s.pending_count,
            s.missing_count,
            statusVi,
          ];
        });

        const csvContent =
          "\ufeff" +
          [
            headers.map((h) => `"${h}"`).join(","),
            ...rows.map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(",")),
          ].join("\n");

        const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        const anonTag = anonymize ? "_AN_DANH" : "";
        a.download = `Bang_diem_lop${anonTag}_${new Date().toISOString().slice(0, 10)}.csv`;
        a.click();
        URL.revokeObjectURL(url);
        setExportSuccess(`Xuất sổ điểm CSV ${anonymize ? "ẩn danh" : "chính thức"} thành công!`);
      }
    } catch (err: any) {
      console.error("Export gradebook failed:", err);
      if (
        err?.status === 403 ||
        err?.message?.includes("403") ||
        err?.message?.includes("Not authorized") ||
        err?.message?.includes("Staff access required")
      ) {
        setExportError(
          "Lỗi phân quyền (HTTP 403 Forbidden): Giáo viên không có quyền xuất sổ điểm của lớp học này (chặn Horizontal Privilege Escalation).",
        );
      } else {
        setExportError(err?.message || "Không thể xuất sổ điểm CSV từ máy chủ. Vui lòng thử lại sau.");
      }
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header Banner */}
      <section className="border-b border-border/70 bg-secondary/30 py-8 md:py-10">
        <div className="mx-auto max-w-7xl px-4 lg:px-8 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <Badge className="bg-primary/10 text-primary border-primary/20 text-xs font-semibold gap-1.5 py-1 px-3">
                  <GraduationCap className="h-3.5 w-3.5" />
                  Sư Phạm Lịch Sử & Đánh Giá Năng Lực
                </Badge>
                {demoMode && (
                  <Badge variant="outline" className="border-amber-500/40 bg-amber-500/10 text-amber-700 dark:text-amber-400 text-xs">
                    Chế độ Demo Giáo viên
                  </Badge>
                )}
              </div>

              <h1 className="font-serif text-2xl font-bold tracking-tight text-foreground md:text-4xl">
                Bảng Đánh Giá Khảo Sát Lịch Sử (Rubric S1 - S4)
              </h1>
              <p className="text-xs text-muted-foreground md:text-sm">
                Quản lý bài nộp nghiên cứu thực địa Đại Nội Huế của học sinh theo mô hình <strong>M-E-E</strong>. Chấm điểm trực quan và phản hồi sư phạm tức thì.
              </p>
            </div>

            {/* Quick Actions & Demo Switch */}
            <div className="flex flex-wrap items-center gap-2.5">
              <Button
                size="sm"
                onClick={handleOpenCreateAssignment}
                className="text-xs h-9 gap-1.5 bg-primary text-primary-foreground font-semibold shadow-sm"
              >
                <FileCheck2 className="h-3.5 w-3.5" />
                <span>Giao bài cho lớp</span>
              </Button>

              <Button
                variant={demoMode ? "secondary" : "outline"}
                size="sm"
                onClick={() => setDemoMode(!demoMode)}
                className="text-xs h-9 gap-1.5"
                title="Bật/tắt chế độ xem thử dành cho người đánh giá"
              >
                <Sparkles className="h-3.5 w-3.5 text-primary" />
                <span>{demoMode ? "Đang bật chế độ Demo" : "Xem chế độ Demo"}</span>
              </Button>

              <Link href="/dai-noi/hoc-tap">
                <Button
                  variant="outline"
                  size="sm"
                  className="text-xs h-9 gap-1.5 border-border/80"
                  title="Xuất phiếu điền dã in sẵn A4 chuẩn Công văn 5512/BGDĐT"
                >
                  <Printer className="h-3.5 w-3.5" />
                  <span>In Phiếu Điền Dã (A4)</span>
                </Button>
              </Link>

              <Button
                variant="outline"
                size="sm"
                onClick={handleExportAnonymizedCSV}
                className="text-xs h-9 gap-1.5 font-semibold text-primary border-primary/30"
                title="Xuất bảng điểm ẩn danh mã học sinh bảo vệ quyền riêng tư"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Xuất CSV (Ẩn danh)</span>
              </Button>

              <Button
                variant="ghost"
                size="sm"
                onClick={handleExportCSV}
                className="text-xs h-9 gap-1.5 font-medium text-muted-foreground"
              >
                <Download className="h-3.5 w-3.5" />
                <span>CSV Đầy đủ</span>
              </Button>
            </div>
          </div>

          {/* Teacher guidance notice */}
          {!isTeacherRole && demoMode && (
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-3.5 text-xs text-amber-800 dark:text-amber-300 flex items-start gap-2.5">
              <ShieldCheck className="h-4 w-4 shrink-0 mt-0.5 text-amber-600 dark:text-amber-400" />
              <div className="space-y-1">
                <span className="font-bold">Chế độ Demo dành cho Giáo viên & Chuyên gia:</span>
                <p className="leading-relaxed opacity-90">
                  Bạn đang xem trước bảng điều khiển dành riêng cho giáo viên bộ môn Lịch sử. Bạn có thể mở bất kỳ bài nộp nào bên dưới, chọn điểm các tiêu chí S1-S4 trong ngăn kéo (drawer) và gửi nhận xét để kiểm tra quy trình chấm bài!
                </p>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Main Content */}
      <div className="mx-auto max-w-7xl px-4 py-8 lg:px-8 space-y-8">
        {/* KPI Metrics Cards */}
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <Card className="border border-border/80 bg-card rounded-2xl shadow-2xs">
            <CardHeader className="p-4 pb-1">
              <CardDescription className="text-xs flex items-center gap-1.5 font-medium">
                <Users className="h-3.5 w-3.5 text-primary" />
                Tổng số bài nộp
              </CardDescription>
              <CardTitle className="text-2xl font-bold font-serif text-foreground">
                {stats.total}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-1 text-[11px] text-muted-foreground">
              Từ các lớp THPT tham gia khảo sát
            </CardContent>
          </Card>

          <Card className="border border-border/80 bg-card rounded-2xl shadow-2xs">
            <CardHeader className="p-4 pb-1">
              <CardDescription className="text-xs flex items-center gap-1.5 font-medium">
                <Clock className="h-3.5 w-3.5 text-amber-500" />
                Chờ chấm điểm
              </CardDescription>
              <CardTitle className="text-2xl font-bold font-serif text-amber-600 dark:text-amber-400">
                {stats.pending}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-1 text-[11px] text-muted-foreground">
              Cần giáo viên đối chiếu Rubric
            </CardContent>
          </Card>

          <Card className="border border-border/80 bg-card rounded-2xl shadow-2xs">
            <CardHeader className="p-4 pb-1">
              <CardDescription className="text-xs flex items-center gap-1.5 font-medium">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                Đã hoàn tất chấm
              </CardDescription>
              <CardTitle className="text-2xl font-bold font-serif text-emerald-600 dark:text-emerald-400">
                {stats.graded}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-1 text-[11px] text-muted-foreground">
              Đã gửi phản hồi sư phạm
            </CardContent>
          </Card>

          <Card className="border border-border/80 bg-card rounded-2xl shadow-2xs">
            <CardHeader className="p-4 pb-1">
              <CardDescription className="text-xs flex items-center gap-1.5 font-medium">
                <Award className="h-3.5 w-3.5 text-primary" />
                Điểm trung bình
              </CardDescription>
              <CardTitle className="text-2xl font-bold font-serif text-foreground">
                {stats.avgScore}<span className="text-sm font-normal text-muted-foreground">/12</span>{" "}
                <span className="text-xs font-semibold text-primary">({stats.avgNormalized}/10)</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-1 text-[11px] text-muted-foreground">
              Quy chuẩn 4 năng lực S1-S4
            </CardContent>
          </Card>
        </div>

        {/* Filter and Search Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border/80 bg-card p-4 shadow-2xs">
          <div className="flex flex-1 flex-wrap items-center gap-3 min-w-[280px]">
            {/* Search Input */}
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Tìm kiếm học sinh, lớp, di tích hoặc từ khóa..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 h-9 text-xs rounded-xl"
              />
            </div>

            {/* Status Filter */}
            <div className="flex items-center gap-1 rounded-xl border border-border/70 p-1 bg-secondary/30">
              <button
                type="button"
                onClick={() => setStatusFilter("all")}
                className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-colors ${
                  statusFilter === "all" ? "bg-background text-foreground shadow-2xs font-bold" : "text-muted-foreground"
                }`}
              >
                Tất cả ({submissions.length})
              </button>
              <button
                type="button"
                onClick={() => setStatusFilter("submitted")}
                className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-colors ${
                  statusFilter === "submitted" ? "bg-background text-amber-600 dark:text-amber-400 shadow-2xs font-bold" : "text-muted-foreground"
                }`}
              >
                Chờ chấm ({stats.pending})
              </button>
              <button
                type="button"
                onClick={() => setStatusFilter("graded")}
                className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-colors ${
                  statusFilter === "graded" ? "bg-background text-emerald-600 dark:text-emerald-400 shadow-2xs font-bold" : "text-muted-foreground"
                }`}
              >
                Đã chấm ({stats.graded})
              </button>
            </div>

            {/* Class Filter Dropdown */}
            {uniqueClasses.length > 0 && (
              <select
                value={classFilter}
                onChange={(e) => setClassFilter(e.target.value)}
                className="h-9 rounded-xl border border-border bg-background px-3 text-xs text-foreground focus:border-primary focus:outline-none"
              >
                <option value="all">Tất cả các lớp</option>
                {uniqueClasses.map((cls) => (
                  <option key={cls} value={cls}>
                    {cls}
                  </option>
                ))}
              </select>
            )}
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setSearchQuery("");
              setStatusFilter("all");
              setClassFilter("all");
            }}
            className="text-xs h-9 text-muted-foreground hover:text-foreground"
          >
            <RefreshCw className="h-3.5 w-3.5 mr-1" />
            Đặt lại
          </Button>
        </div>

        {/* IDOR Warning Banner */}
        {idorWarning && (
          <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 p-3.5 text-xs text-rose-800 dark:text-rose-300 flex items-start gap-2.5 animate-in fade-in">
            <ShieldCheck className="h-4 w-4 shrink-0 mt-0.5 text-rose-600 dark:text-rose-400" />
            <div className="space-y-1">
              <span className="font-bold">Bảo vệ quyền hạn Giáo viên (IDOR Protection):</span>
              <p className="leading-relaxed opacity-90">{idorWarning}</p>
            </div>
          </div>
        )}

        {/* SECTION: Real Classroom Gradebook & Student Roster (V5.1 / Wave W03-A06) */}
        <div className="rounded-2xl border border-border/80 bg-card p-6 shadow-2xs space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border/70 pb-5">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Badge className="bg-primary/10 text-primary border-primary/20 text-xs font-semibold gap-1.5 py-0.5 px-2.5">
                  <GraduationCap className="h-3.5 w-3.5" />
                  Sổ Điểm Điện Tử & Bảng Điểm Lớp Học
                </Badge>
                {isGradebookLoading && (
                  <Badge variant="secondary" className="text-[10px] animate-pulse">
                    Đang tải sổ điểm...
                  </Badge>
                )}
              </div>
              <h2 className="font-serif font-bold text-xl text-foreground flex items-center gap-2">
                <span>Sổ Điểm & Danh Sách Học Sinh Lớp Học</span>
              </h2>
              <p className="text-xs text-muted-foreground">
                Bảng tổng hợp điểm số, theo dõi bài tập trễ hạn (Missing), đang chờ nộp (Pending) và xuất báo cáo CSV chính thức.
              </p>
            </div>

            {/* Class Selector & CSV Export Controls */}
            <div className="flex flex-wrap items-center gap-2.5">
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-muted-foreground shrink-0" />
                <select
                  value={selectedClassroomId}
                  onChange={(e) => setSelectedClassroomId(e.target.value)}
                  className="h-9 rounded-xl border border-border bg-background px-3 text-xs font-medium text-foreground focus:border-primary focus:outline-none"
                  title="Chọn lớp học để xem sổ điểm"
                >
                  {classrooms.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <Button
                size="sm"
                variant="outline"
                onClick={() => handleExportBackendGradebook(true)}
                disabled={isExporting}
                className="text-xs h-9 gap-1.5 border-primary/30 text-primary font-semibold hover:bg-primary/5"
                title="Xuất bảng điểm ẩn danh HS-ANON bảo vệ quyền riêng tư học sinh"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Xuất CSV (Ẩn danh)</span>
              </Button>

              <Button
                size="sm"
                onClick={() => handleExportBackendGradebook(false)}
                disabled={isExporting}
                className="text-xs h-9 gap-1.5 bg-primary text-primary-foreground font-semibold shadow-xs"
                title="Xuất sổ điểm CSV chính thức có đầy đủ tên và điểm số học sinh"
              >
                <Download className="h-3.5 w-3.5" />
                <span>{isExporting ? "Đang xuất..." : "Xuất Sổ Điểm CSV"}</span>
              </Button>
            </div>
          </div>

          {/* Export Notifications / Security Alerts */}
          {exportError && (
            <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 p-3.5 text-xs text-rose-800 dark:text-rose-300 flex items-start gap-2.5 animate-in fade-in">
              <ShieldCheck className="h-4 w-4 shrink-0 mt-0.5 text-rose-600 dark:text-rose-400" />
              <div className="space-y-1">
                <span className="font-bold">Bảo vệ phân quyền & chống xâm nhập ngang (403 Forbidden):</span>
                <p className="leading-relaxed opacity-90">{exportError}</p>
              </div>
            </div>
          )}

          {exportSuccess && (
            <div className="rounded-xl border border-emerald-500/40 bg-emerald-500/10 p-3 text-xs text-emerald-800 dark:text-emerald-300 flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
              <span>{exportSuccess}</span>
            </div>
          )}

          {/* Gradebook Quick KPI Metrics */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
            <div className="rounded-xl border border-border/70 bg-secondary/20 p-3">
              <span className="text-[11px] text-muted-foreground block font-medium">Sĩ số lớp</span>
              <span className="font-serif text-xl font-bold text-foreground">
                {gradebookData?.metrics?.total_students ?? displayedRoster.length}
              </span>
              <span className="text-[10px] text-muted-foreground block">học sinh</span>
            </div>
            <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3">
              <span className="text-[11px] text-emerald-700 dark:text-emerald-400 block font-medium">Đã hoàn thành</span>
              <span className="font-serif text-xl font-bold text-emerald-600 dark:text-emerald-400">
                {gradebookData?.metrics?.completed_count ?? 0}
              </span>
              <span className="text-[10px] text-emerald-700/80 dark:text-emerald-400/80 block">đạt chuẩn</span>
            </div>
            <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-3">
              <span className="text-[11px] text-amber-700 dark:text-amber-400 block font-medium">Đang chờ (Pending)</span>
              <span className="font-serif text-xl font-bold text-amber-600 dark:text-amber-400">
                {gradebookData?.metrics?.pending_count ?? 0}
              </span>
              <span className="text-[10px] text-amber-700/80 dark:text-amber-400/80 block">đang làm / chờ nộp</span>
            </div>
            <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-3">
              <span className="text-[11px] text-rose-700 dark:text-rose-400 block font-medium">Quá hạn (Missing)</span>
              <span className="font-serif text-xl font-bold text-rose-600 dark:text-rose-400">
                {gradebookData?.metrics?.missing_count ?? 0}
              </span>
              <span className="text-[10px] text-rose-700/80 dark:text-rose-400/80 block">cần nhắc nhở</span>
            </div>
            <div className="rounded-xl border border-border/70 bg-secondary/20 p-3">
              <span className="text-[11px] text-muted-foreground block font-medium">Điểm TB trắc nghiệm</span>
              <span className="font-serif text-xl font-bold text-primary">
                {gradebookData?.metrics?.average_score ? `${gradebookData.metrics.average_score}/10` : "--/10"}
              </span>
              <span className="text-[10px] text-muted-foreground block">
                Tiến độ TB: {gradebookData?.metrics?.average_completion_percent ?? 0}%
              </span>
            </div>
          </div>

          {/* Gradebook Filter & Search Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border/70 bg-secondary/15 p-3">
            <div className="flex flex-1 flex-wrap items-center gap-2.5 min-w-[260px]">
              {/* Search */}
              <div className="relative flex-1 min-w-[180px]">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder="Lọc học sinh theo tên hoặc email..."
                  value={gradebookSearch}
                  onChange={(e) => setGradebookSearch(e.target.value)}
                  className="pl-8 h-8 text-xs rounded-lg"
                />
              </div>

              {/* Status Filter Buttons */}
              <div className="flex items-center gap-1 rounded-lg border border-border/60 p-0.5 bg-background">
                <button
                  type="button"
                  onClick={() => setGradebookStatusFilter("all")}
                  className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                    gradebookStatusFilter === "all" ? "bg-primary text-primary-foreground font-semibold shadow-2xs" : "text-muted-foreground"
                  }`}
                >
                  Tất cả ({gradebookData?.roster?.length ?? displayedRoster.length})
                </button>
                <button
                  type="button"
                  onClick={() => setGradebookStatusFilter("pending")}
                  className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                    gradebookStatusFilter === "pending" ? "bg-amber-500/20 text-amber-700 dark:text-amber-300 font-semibold" : "text-muted-foreground"
                  }`}
                >
                  Chờ nộp / Chờ chấm ({gradebookData?.metrics?.pending_count ?? 0})
                </button>
                <button
                  type="button"
                  onClick={() => setGradebookStatusFilter("missing")}
                  className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                    gradebookStatusFilter === "missing" ? "bg-rose-500/20 text-rose-700 dark:text-rose-300 font-semibold" : "text-muted-foreground"
                  }`}
                >
                  Quá hạn ({gradebookData?.metrics?.missing_count ?? 0})
                </button>
                <button
                  type="button"
                  onClick={() => setGradebookStatusFilter("completed")}
                  className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                    gradebookStatusFilter === "completed" ? "bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 font-semibold" : "text-muted-foreground"
                  }`}
                >
                  Đã xong ({gradebookData?.metrics?.completed_count ?? 0})
                </button>
              </div>
            </div>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setGradebookSearch("");
                setGradebookStatusFilter("all");
              }}
              className="text-xs h-8 text-muted-foreground hover:text-foreground"
            >
              <RefreshCw className="h-3 w-3 mr-1" />
              Đặt lại bộ lọc
            </Button>
          </div>

          {/* Real Student Roster Table */}
          <div className="rounded-xl border border-border/80 overflow-hidden bg-background">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-secondary/40 border-b border-border/70 text-muted-foreground uppercase text-[10px] tracking-wider font-semibold">
                  <tr>
                    <th className="p-3.5 pl-5">Học sinh & Email</th>
                    <th className="p-3.5">Tiến độ (%)</th>
                    <th className="p-3.5 text-center">Tổng XP</th>
                    <th className="p-3.5 text-center">Trắc nghiệm</th>
                    <th className="p-3.5 text-center">Nhiệm vụ / Bài tập</th>
                    <th className="p-3.5 text-center">Trạng thái</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {displayedRoster.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="p-8 text-center text-muted-foreground">
                        Không tìm thấy học sinh nào phù hợp với bộ lọc sổ điểm.
                      </td>
                    </tr>
                  ) : (
                    displayedRoster.map((student) => {
                      const isMissing = student.status === "missing";
                      const isPending = student.status === "pending";

                      return (
                        <tr key={student.student_id} className="hover:bg-secondary/15 transition-colors">
                          {/* Student Info */}
                          <td className="p-3.5 pl-5">
                            <div className="flex items-center gap-3">
                              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 border border-primary/20 text-primary font-bold text-xs">
                                {student.display_name.trim().charAt(0)}
                              </div>
                              <div>
                                <span className="font-bold text-foreground block text-xs">
                                  {student.display_name}
                                </span>
                                <span className="text-[11px] text-muted-foreground block font-mono">
                                  {student.email}
                                </span>
                              </div>
                            </div>
                          </td>

                          {/* Completion Progress Bar */}
                          <td className="p-3.5 min-w-[130px]">
                            <div className="space-y-1">
                              <div className="flex items-center justify-between text-[11px]">
                                <span className="font-semibold text-foreground">{student.overall_completion_percent}%</span>
                              </div>
                              <div className="h-1.5 w-full rounded-full bg-secondary overflow-hidden">
                                <div
                                  className="h-full bg-primary rounded-full transition-all duration-300"
                                  style={{ width: `${Math.min(100, Math.max(0, student.overall_completion_percent))}%` }}
                                />
                              </div>
                            </div>
                          </td>

                          {/* XP */}
                          <td className="p-3.5 text-center font-mono font-bold text-primary whitespace-nowrap">
                            <Badge variant="outline" className="text-[11px] border-primary/20 bg-primary/5">
                              {student.total_xp} XP
                            </Badge>
                          </td>

                          {/* Quiz Stats */}
                          <td className="p-3.5 text-center whitespace-nowrap">
                            <div className="text-[11px]">
                              <span className="font-bold text-foreground">{student.avg_quiz_score}/10</span>
                              <span className="text-muted-foreground block text-[10px]">
                                {student.quizzes_passed} bài đạt
                              </span>
                            </div>
                          </td>

                          {/* Assignments Status Breakdown */}
                          <td className="p-3.5 text-center whitespace-nowrap">
                            <div className="inline-flex items-center gap-1.5 text-[10px]">
                              <Badge className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-0 py-0.5 px-1.5" title="Đã hoàn thành">
                                ✓ {student.completed_count}
                              </Badge>
                              {student.pending_count > 0 && (
                                <Badge className="bg-amber-500/10 text-amber-700 dark:text-amber-400 border-0 py-0.5 px-1.5" title="Đang chờ nộp/chấm">
                                  ⏳ {student.pending_count}
                                </Badge>
                              )}
                              {student.missing_count > 0 && (
                                <Badge className="bg-rose-500/10 text-rose-700 dark:text-rose-400 border-0 py-0.5 px-1.5" title="Trễ hạn / Thiếu bài">
                                  ⚠ {student.missing_count}
                                </Badge>
                              )}
                            </div>
                          </td>

                          {/* Overall Status Badge */}
                          <td className="p-3.5 text-center whitespace-nowrap">
                            {isMissing ? (
                              <Badge className="bg-rose-500/10 text-rose-700 dark:text-rose-300 border-rose-500/20 text-[10px] gap-1 font-semibold">
                                <Clock className="h-3 w-3" />
                                Quá hạn / Thiếu
                              </Badge>
                            ) : isPending ? (
                              <Badge className="bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/20 text-[10px] gap-1 font-semibold">
                                <Clock className="h-3 w-3" />
                                Đang chờ nộp
                              </Badge>
                            ) : (
                              <Badge className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/20 text-[10px] gap-1 font-semibold">
                                <CheckCircle2 className="h-3 w-3" />
                                Hoàn thành tốt
                              </Badge>
                            )}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* SECTION: Active Classroom Assignments (SPEC V5.1) */}
        <div className="rounded-2xl border border-border/80 bg-card p-5 shadow-2xs space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="font-serif font-bold text-lg text-foreground flex items-center gap-2">
                <FileCheck2 className="h-4 w-4 text-primary" />
                <span>Nhiệm Vụ Học Tập Đã Giao Cho Lớp</span>
              </h2>
              <p className="text-xs text-muted-foreground">
                Quản lý các hành trình di sản 35–45 phút và phiếu khảo cứu thực địa đã phát hành cho học sinh.
              </p>
            </div>

            <Button
              size="sm"
              onClick={handleOpenCreateAssignment}
              className="text-xs h-8 gap-1.5 bg-primary text-primary-foreground font-semibold shadow-xs"
            >
              <FileCheck2 className="h-3.5 w-3.5" />
              <span>+ Giao bài mới</span>
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5 pt-1">
            {assignments.length === 0 ? (
              <div className="col-span-full py-6 text-center text-xs text-muted-foreground">
                Chưa có nhiệm vụ nào được giao. Hãy nhấn nút &ldquo;Giao bài cho lớp&rdquo; để phát hành bài tập mới.
              </div>
            ) : (
              assignments.map((assign) => {
                const isOwner =
                  demoMode ||
                  !assign.teacher_id ||
                  assign.teacher_id === user?.id ||
                  assign.class_name.includes(user?.username || "");

                return (
                  <div
                    key={assign.id}
                    className="rounded-xl border border-border/70 bg-secondary/15 p-4 space-y-3 flex flex-col justify-between"
                  >
                    <div className="space-y-2">
                      <div className="flex items-center justify-between gap-2">
                        <Badge
                          variant="outline"
                          className={cn(
                            "text-[10px] font-semibold",
                            isOwner
                              ? "border-primary/40 text-primary bg-primary/5"
                              : "text-muted-foreground border-border",
                          )}
                        >
                          {isOwner ? "Lớp của bạn" : "Lớp giáo viên khác"}
                        </Badge>
                        <Badge
                          variant="secondary"
                          className="text-[10px] bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-0 font-medium"
                        >
                          Đang hoạt động
                        </Badge>
                      </div>

                      <h4 className="font-serif font-bold text-sm text-foreground line-clamp-1">
                        {assign.title}
                      </h4>

                      <div className="space-y-1 text-xs text-muted-foreground">
                        <p className="flex items-center gap-1.5 font-medium text-foreground">
                          <Users className="size-3 text-primary shrink-0" />
                          <span className="truncate">{assign.class_name}</span>
                        </p>
                        <p className="flex items-center gap-1.5">
                          <Route className="size-3 text-muted-foreground shrink-0" />
                          <span className="truncate">Tuyến: {assign.journey_slug}</span>
                        </p>
                        {assign.due_date && (
                          <p className="flex items-center gap-1.5">
                            <Calendar className="size-3 text-muted-foreground shrink-0" />
                            <span>Hạn nộp: {new Date(assign.due_date).toLocaleDateString("vi-VN")}</span>
                          </p>
                        )}
                      </div>

                      {/* Rubric Weights preview (0-4 scale) */}
                      {assign.rubric_weights && (
                        <div className="pt-1.5 border-t border-border/50 text-[10px] text-muted-foreground flex items-center justify-between">
                          <span>Trọng số Rubric:</span>
                          <span className="font-mono font-medium text-foreground">
                            S1:{assign.rubric_weights.S1_spatial ?? 3} S2:{assign.rubric_weights.S2_temporal ?? 2} S3:{assign.rubric_weights.S3_evidence ?? 3} S4:{assign.rubric_weights.S4_argument ?? 2}
                          </span>
                        </div>
                      )}
                    </div>

                    <div className="pt-2 border-t border-border/50 flex items-center justify-between gap-2">
                      <Button
                        size="sm"
                        variant={isOwner ? "outline" : "ghost"}
                        onClick={() => handleOpenEditAssignment(assign)}
                        disabled={!isOwner}
                        className={cn(
                          "text-xs h-7 w-full gap-1.5 font-medium",
                          !isOwner && "opacity-50 cursor-not-allowed",
                        )}
                        title={
                          isOwner
                            ? "Chỉnh sửa bài giao cho lớp"
                            : "Bảo vệ IDOR: Bạn chỉ có quyền sửa bài tập của chính lớp mình phụ trách"
                        }
                      >
                        <FileCheck2 className="size-3" />
                        <span>{isOwner ? "Sửa bài tập" : "Không có quyền sửa"}</span>
                      </Button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Submissions List Table / Cards */}
        <div className="rounded-2xl border border-border/80 bg-card overflow-hidden shadow-2xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-secondary/40 border-b border-border/70 text-muted-foreground uppercase text-[10px] tracking-wider font-semibold">
                <tr>
                  <th className="p-4 pl-6">Học sinh & Lớp</th>
                  <th className="p-4">Di tích & Tuyến khảo sát</th>
                  <th className="p-4">Nội dung Mệnh đề [M]</th>
                  <th className="p-4">Thời gian nộp</th>
                  <th className="p-4 text-center">Trạng thái</th>
                  <th className="p-4 text-center">Điểm số</th>
                  <th className="p-4 pr-6 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {filteredSubmissions.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-muted-foreground">
                      Không tìm thấy bài nộp nào phù hợp với bộ lọc.
                    </td>
                  </tr>
                ) : (
                  filteredSubmissions.map((sub) => {
                    const isGraded = sub.status === "graded";

                    return (
                      <tr
                        key={sub.id}
                        className="hover:bg-secondary/20 transition-colors group"
                      >
                        {/* Student Column */}
                        <td className="p-4 pl-6">
                          <div className="flex items-center gap-3">
                            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary/10 border border-primary/20 text-primary font-bold text-xs">
                              {sub.student_name.trim().charAt(0)}
                            </div>
                            <div>
                              <span className="font-bold text-foreground block text-xs">
                                {sub.student_name}
                              </span>
                              <span className="text-[11px] text-muted-foreground block">
                                {sub.student_class}
                              </span>
                            </div>
                          </div>
                        </td>

                        {/* Monument Column */}
                        <td className="p-4">
                          <div>
                            <span className="font-semibold text-foreground block">
                              {sub.monument_name_vi || "Khảo sát thực địa"}
                            </span>
                            {sub.trail_title ? (
                              <span className="text-[11px] text-primary/80 line-clamp-1">
                                {sub.trail_title}
                              </span>
                            ) : (
                              <span className="text-[10px] text-muted-foreground">
                                Khảo sát hồ sơ đơn lẻ
                              </span>
                            )}
                          </div>
                        </td>

                        {/* Claim Excerpt */}
                        <td className="p-4 max-w-xs">
                          <p className="line-clamp-2 text-muted-foreground italic text-xs leading-relaxed">
                            &ldquo;{sub.claim}&rdquo;
                          </p>
                        </td>

                        {/* Timestamp */}
                        <td className="p-4 whitespace-nowrap text-muted-foreground font-mono text-[11px]">
                          {new Date(sub.submitted_at).toLocaleDateString("vi-VN", {
                            day: "2-digit",
                            month: "2-digit",
                            year: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </td>

                        {/* Status Badge */}
                        <td className="p-4 text-center whitespace-nowrap">
                          {isGraded ? (
                            <Badge className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/20 text-[10px] gap-1 font-semibold">
                              <CheckCircle2 className="h-3 w-3" />
                              Đã chấm
                            </Badge>
                          ) : (
                            <Badge className="bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/20 text-[10px] gap-1 font-semibold">
                              <Clock className="h-3 w-3" />
                              Chờ chấm
                            </Badge>
                          )}
                        </td>

                        {/* Score */}
                        <td className="p-4 text-center whitespace-nowrap">
                          {isGraded && sub.scores ? (
                            <div className="font-mono">
                              <span className="font-bold text-foreground text-sm">
                                {sub.scores.total}
                              </span>
                              <span className="text-muted-foreground text-xs">/12</span>
                              <span className="block text-[10px] text-primary font-bold">
                                ({sub.scores.normalized_10}/10)
                              </span>
                            </div>
                          ) : (
                            <span className="text-muted-foreground/60 font-mono text-xs">--/12</span>
                          )}
                        </td>

                        {/* Action Button */}
                        <td className="p-4 pr-6 text-right whitespace-nowrap">
                          <Button
                            size="sm"
                            variant={isGraded ? "outline" : "default"}
                            onClick={() => handleOpenGrading(sub)}
                            className="text-xs h-8 gap-1.5 font-semibold"
                          >
                            <FileCheck2 className="h-3.5 w-3.5" />
                            <span>{isGraded ? "Xem & Sửa điểm" : "Chấm bài (Rubric)"}</span>
                          </Button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Interactive Grading Drawer / Sheet with Rubric S1-S4 */}
      <Sheet open={isGradingOpen} onOpenChange={setIsGradingOpen}>
        <SheetContent
          side="right"
          className="w-full sm:max-w-2xl overflow-y-auto p-0 gap-0 border-border/80 bg-card"
        >
          {selectedSubmission && (
            <form onSubmit={handleSaveGrade} className="flex flex-col h-full">
              {/* Sheet Header */}
              <div className="border-b border-border/70 p-6 pb-4 bg-secondary/20">
                <div className="flex items-center justify-between">
                  <Badge variant="outline" className="text-xs font-semibold border-primary/30 text-primary gap-1">
                    <GraduationCap className="h-3.5 w-3.5" />
                    Phiếu Chấm Điểm Rubric S1 - S4
                  </Badge>
                  <span className="font-mono text-xs text-muted-foreground">
                    Mã: {selectedSubmission.id}
                  </span>
                </div>

                <SheetTitle className="mt-2 font-serif text-xl font-bold tracking-tight text-foreground md:text-2xl">
                  {selectedSubmission.student_name}
                </SheetTitle>
                <SheetDescription className="text-xs text-muted-foreground mt-0.5">
                  {selectedSubmission.student_class} • Khảo sát {selectedSubmission.monument_name_vi}
                </SheetDescription>
              </div>

              {/* Sheet Body (Scrollable) */}
              <div className="flex-1 p-6 space-y-6 overflow-y-auto">
                {/* SECTION 1: Student's M-E-E Inquiry Submission */}
                <div className="space-y-3 rounded-2xl border border-border/80 bg-secondary/15 p-4 text-xs">
                  <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-primary text-[11px]">
                    <FileText className="h-4 w-4" />
                    <span>Bài làm của học sinh theo mô hình M-E-E:</span>
                  </div>

                  {/* Claim [M] */}
                  <div className="rounded-xl border border-border/60 bg-background p-3 space-y-1">
                    <span className="font-bold text-primary flex items-center gap-1">
                      <span className="flex h-4 w-4 items-center justify-center rounded-full bg-primary/20 text-[10px] font-bold text-primary">M</span>
                      Mệnh đề kết luận (Claim):
                    </span>
                    <p className="text-foreground leading-relaxed font-medium">
                      {selectedSubmission.claim}
                    </p>
                  </div>

                  {/* Evidence [E] */}
                  <div className="rounded-xl border border-border/60 bg-background p-3 space-y-1">
                    <span className="font-bold text-primary flex items-center gap-1">
                      <span className="flex h-4 w-4 items-center justify-center rounded-full bg-primary/20 text-[10px] font-bold text-primary">E</span>
                      Bằng chứng sử liệu & Hiện trường (Evidence):
                    </span>
                    <p className="text-foreground leading-relaxed whitespace-pre-line">
                      {selectedSubmission.evidence}
                    </p>

                    {selectedSubmission.evidence_citations && selectedSubmission.evidence_citations.length > 0 && (
                      <div className="flex flex-wrap gap-1 pt-1 border-t border-border/40 mt-1">
                        {selectedSubmission.evidence_citations.map((c, idx) => (
                          <Badge key={idx} variant="secondary" className="text-[10px] font-normal">
                            {c}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Explanation [E] */}
                  <div className="rounded-xl border border-border/60 bg-background p-3 space-y-1">
                    <span className="font-bold text-primary flex items-center gap-1">
                      <span className="flex h-4 w-4 items-center justify-center rounded-full bg-primary/20 text-[10px] font-bold text-primary">E</span>
                      Diễn giải logic (Explanation):
                    </span>
                    <p className="text-foreground leading-relaxed">
                      {selectedSubmission.explanation}
                    </p>
                  </div>

                  {/* Uncertainty/Notes if present */}
                  {selectedSubmission.notes && (
                    <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-3 space-y-1">
                      <span className="font-bold text-amber-800 dark:text-amber-300 flex items-center gap-1">
                        <HelpCircle className="h-3.5 w-3.5" />
                        Tư duy phản biện / Ghi chú hoài nghi sử liệu:
                      </span>
                      <p className="text-foreground/90 leading-relaxed italic">
                        {selectedSubmission.notes}
                      </p>
                    </div>
                  )}
                </div>

                {/* SECTION 2: Interactive Rubrics S1 - S4 */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-border/70 pb-2">
                    <div className="flex items-center gap-2">
                      <Award className="h-4 w-4 text-primary" />
                      <h3 className="font-serif text-base font-bold text-foreground">
                        Thang điểm đánh giá Rubric S1 - S4
                      </h3>
                    </div>
                    <Badge className="bg-primary/10 text-primary border-primary/20 font-mono text-xs">
                      Tổng: {totalScore}/12 điểm ({normalized10}/10)
                    </Badge>
                  </div>

                  {/* Rubric S1: Spatial */}
                  <div className="space-y-2 rounded-xl border border-border/70 bg-card p-3.5">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="font-bold text-xs text-foreground block">
                          {RUBRIC_CRITERIA.S1.title}
                        </span>
                        <span className="text-[11px] text-muted-foreground block">
                          {RUBRIC_CRITERIA.S1.description}
                        </span>
                      </div>
                      <Badge className="font-mono text-xs bg-primary text-primary-foreground">
                        {s1Score} / 3đ
                      </Badge>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
                      {RUBRIC_CRITERIA.S1.levels.map((lvl) => (
                        <button
                          key={lvl.score}
                          type="button"
                          onClick={() => setS1Score(lvl.score)}
                          className={`rounded-lg p-2 text-left border text-xs transition-all ${
                            s1Score === lvl.score
                              ? "border-primary bg-primary/10 text-primary font-bold ring-2 ring-primary/20"
                              : "border-border/60 bg-secondary/20 hover:bg-secondary/50 text-muted-foreground"
                          }`}
                        >
                          <div className="font-semibold">{lvl.label}</div>
                          <div className="text-[10px] font-normal leading-tight opacity-80 mt-1 line-clamp-3">
                            {lvl.desc}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Rubric S2: Temporal */}
                  <div className="space-y-2 rounded-xl border border-border/70 bg-card p-3.5">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="font-bold text-xs text-foreground block">
                          {RUBRIC_CRITERIA.S2.title}
                        </span>
                        <span className="text-[11px] text-muted-foreground block">
                          {RUBRIC_CRITERIA.S2.description}
                        </span>
                      </div>
                      <Badge className="font-mono text-xs bg-primary text-primary-foreground">
                        {s2Score} / 3đ
                      </Badge>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
                      {RUBRIC_CRITERIA.S2.levels.map((lvl) => (
                        <button
                          key={lvl.score}
                          type="button"
                          onClick={() => setS2Score(lvl.score)}
                          className={`rounded-lg p-2 text-left border text-xs transition-all ${
                            s2Score === lvl.score
                              ? "border-primary bg-primary/10 text-primary font-bold ring-2 ring-primary/20"
                              : "border-border/60 bg-secondary/20 hover:bg-secondary/50 text-muted-foreground"
                          }`}
                        >
                          <div className="font-semibold">{lvl.label}</div>
                          <div className="text-[10px] font-normal leading-tight opacity-80 mt-1 line-clamp-3">
                            {lvl.desc}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Rubric S3: Evidence */}
                  <div className="space-y-2 rounded-xl border border-border/70 bg-card p-3.5">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="font-bold text-xs text-foreground block">
                          {RUBRIC_CRITERIA.S3.title}
                        </span>
                        <span className="text-[11px] text-muted-foreground block">
                          {RUBRIC_CRITERIA.S3.description}
                        </span>
                      </div>
                      <Badge className="font-mono text-xs bg-primary text-primary-foreground">
                        {s3Score} / 3đ
                      </Badge>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
                      {RUBRIC_CRITERIA.S3.levels.map((lvl) => (
                        <button
                          key={lvl.score}
                          type="button"
                          onClick={() => setS3Score(lvl.score)}
                          className={`rounded-lg p-2 text-left border text-xs transition-all ${
                            s3Score === lvl.score
                              ? "border-primary bg-primary/10 text-primary font-bold ring-2 ring-primary/20"
                              : "border-border/60 bg-secondary/20 hover:bg-secondary/50 text-muted-foreground"
                          }`}
                        >
                          <div className="font-semibold">{lvl.label}</div>
                          <div className="text-[10px] font-normal leading-tight opacity-80 mt-1 line-clamp-3">
                            {lvl.desc}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Rubric S4: Argumentation */}
                  <div className="space-y-2 rounded-xl border border-border/70 bg-card p-3.5">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="font-bold text-xs text-foreground block">
                          {RUBRIC_CRITERIA.S4.title}
                        </span>
                        <span className="text-[11px] text-muted-foreground block">
                          {RUBRIC_CRITERIA.S4.description}
                        </span>
                      </div>
                      <Badge className="font-mono text-xs bg-primary text-primary-foreground">
                        {s4Score} / 3đ
                      </Badge>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
                      {RUBRIC_CRITERIA.S4.levels.map((lvl) => (
                        <button
                          key={lvl.score}
                          type="button"
                          onClick={() => setS4Score(lvl.score)}
                          className={`rounded-lg p-2 text-left border text-xs transition-all ${
                            s4Score === lvl.score
                              ? "border-primary bg-primary/10 text-primary font-bold ring-2 ring-primary/20"
                              : "border-border/60 bg-secondary/20 hover:bg-secondary/50 text-muted-foreground"
                          }`}
                        >
                          <div className="font-semibold">{lvl.label}</div>
                          <div className="text-[10px] font-normal leading-tight opacity-80 mt-1 line-clamp-3">
                            {lvl.desc}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Score Summary Box */}
                <div className="rounded-xl border border-primary/30 bg-primary/5 p-4 flex items-center justify-between">
                  <div>
                    <span className="text-xs font-bold text-foreground block">
                      Tổng kết điểm Rubric S1 - S4:
                    </span>
                    <span className="text-xs text-muted-foreground">
                      Xếp loại:{" "}
                      <strong className="text-primary font-bold">
                        {normalized10 >= 9.0
                          ? "Xuất sắc"
                          : normalized10 >= 8.0
                          ? "Giỏi"
                          : normalized10 >= 6.5
                          ? "Khá"
                          : "Đang rèn luyện"}
                      </strong>
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="font-mono text-2xl font-extrabold text-primary">
                      {totalScore}
                    </span>
                    <span className="font-mono text-xs text-muted-foreground"> / 12 điểm</span>
                    <span className="block font-mono text-xs font-bold text-foreground">
                      = {normalized10} / 10.0
                    </span>
                  </div>
                </div>

                {/* Live SVG Radar Chart */}
                <div className="pt-1">
                  <RubricRadarChart
                    studentScores={{ s1: s1Score, s2: s2Score, s3: s3Score, s4: s4Score }}
                    studentLabel={`Bài làm của ${selectedSubmission.student_name}`}
                    className="bg-background/80"
                    showScoreSummary={false}
                  />
                </div>

                {/* SECTION 3: Qualitative Teacher Feedback */}
                <div className="space-y-2.5">
                  <label htmlFor="teacher-feedback" className="text-xs font-bold text-foreground flex items-center gap-1.5">
                    <UserCheck className="h-4 w-4 text-primary" />
                    <span>Nhận xét định tính của Giáo viên (Qualitative Feedback):</span>
                  </label>

                  {/* Quick template suggestion chips */}
                  <div className="flex flex-wrap gap-1.5">
                    {QUICK_FEEDBACK_PROMPTS.map((prompt, pIdx) => (
                      <button
                        key={pIdx}
                        type="button"
                        onClick={() =>
                          setFeedbackText((prev) =>
                            prev ? `${prev} ${prompt}` : prompt,
                          )
                        }
                        className="rounded-md border border-border/80 bg-secondary/40 px-2 py-1 text-[11px] text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors text-left"
                      >
                        + {prompt.slice(0, 36)}...
                      </button>
                    ))}
                  </div>

                  <textarea
                    id="teacher-feedback"
                    rows={4}
                    value={feedbackText}
                    onChange={(e) => setFeedbackText(e.target.value)}
                    placeholder="Ghi nhận xét chi tiết, khen ngợi điểm nổi bật và hướng dẫn học sinh cải thiện lập luận..."
                    className="w-full rounded-xl border border-border bg-background p-3 text-xs placeholder:text-muted-foreground/60 focus:border-primary focus:outline-none"
                  />
                </div>

                {/* SECTION 4: Reviewer & Audit History Trail */}
                <div className="space-y-3 rounded-xl border border-border/70 bg-card p-3.5 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-foreground flex items-center gap-1.5">
                      <ShieldCheck className="h-4 w-4 text-primary" />
                      Lịch sử chấm điểm & Kiểm toán (Audit Revisions):
                    </span>
                    {isLoadingAudit && (
                      <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                        <RefreshCw className="h-3 w-3 animate-spin" /> Đang tải...
                      </span>
                    )}
                  </div>

                  {selectedSubmission.status === "graded" && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] p-2.5 rounded-lg bg-secondary/30">
                      <div>
                        <span className="text-muted-foreground">Người thẩm định: </span>
                        <strong className="text-foreground">{selectedSubmission.graded_by || "TS. Trần Văn Thọ"}</strong>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Thời điểm chấm: </span>
                        <span className="font-mono text-foreground">
                          {selectedSubmission.graded_at ? new Date(selectedSubmission.graded_at).toLocaleString("vi-VN") : "Gần đây"}
                        </span>
                      </div>
                    </div>
                  )}

                  {submissionAuditTrail.length > 0 ? (
                    <div className="space-y-1.5 pt-1">
                      {submissionAuditTrail.map((audit, aIdx) => (
                        <div
                          key={audit.id || aIdx}
                          className="flex items-start justify-between rounded-md border border-border/50 bg-background/60 p-2 text-[11px]"
                        >
                          <div>
                            <div className="font-semibold text-foreground flex items-center gap-1">
                              <Badge variant="outline" className="text-[9px] py-0 px-1 font-mono">
                                {audit.action || "rubric_grade"}
                              </Badge>
                              <span>Phiên bản {audit.new_value?.row_version || aIdx + 1}</span>
                            </div>
                            <div className="text-[10px] text-muted-foreground mt-0.5">
                              Người chấm: {audit.user_id || audit.reviewer_id || "Giáo viên"}
                            </div>
                          </div>
                          <div className="text-right">
                            <span className="font-mono text-[10px] text-primary font-bold block">
                              {audit.new_value?.score != null ? `${audit.new_value.score}/12đ` : "Đã cập nhật"}
                            </span>
                            <span className="text-[9px] text-muted-foreground font-mono">
                              {audit.created_at ? new Date(audit.created_at).toLocaleDateString("vi-VN") : ""}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-[11px] text-muted-foreground italic">
                      Chưa có lịch sử sửa điểm trước đó. Bài nộp sẽ được ghi nhận vào sổ kiểm toán khi lưu.
                    </p>
                  )}
                </div>

                {/* Alerts / Error feedback */}
                {saveError && (
                  <div className="rounded-xl border border-destructive/50 bg-destructive/10 p-3 text-xs text-destructive flex items-center gap-2">
                    <HelpCircle className="h-4 w-4 shrink-0" />
                    <span>{saveError}</span>
                  </div>
                )}
                {saveSuccessMessage && (
                  <div className="rounded-xl border border-emerald-500/50 bg-emerald-500/10 p-3 text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 shrink-0" />
                    <span>{saveSuccessMessage}</span>
                  </div>
                )}
              </div>

              {/* Sheet Footer */}
              <SheetFooter className="border-t border-border/70 p-4 bg-secondary/20 flex items-center justify-between gap-3">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsGradingOpen(false)}
                >
                  Hủy bỏ
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={isSavingGrade}
                  className="gap-2 font-semibold"
                >
                  {isSavingGrade ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    <CheckCircle2 className="h-4 w-4" />
                  )}
                  {isSavingGrade ? "Đang lưu..." : "Lưu điểm & Gửi nhận xét"}
                </Button>
              </SheetFooter>
            </form>
          )}
        </SheetContent>
      </Sheet>

      {/* Create / Edit Classroom Assignment Modal (SPEC V5.1) */}
      <Dialog open={isCreateAssignmentOpen} onOpenChange={setIsCreateAssignmentOpen}>
        <DialogContent className="max-w-lg p-0 gap-0 border-border/80 bg-background/95 backdrop-blur-xl">
          <form onSubmit={handleSaveAssignment}>
            <DialogHeader className="p-5 pb-3 border-b border-border/60">
              <div className="flex items-center gap-2">
                <Badge className="bg-primary/10 text-primary border-primary/20 text-xs font-semibold gap-1 py-0.5 px-2.5">
                  <GraduationCap className="size-3.5" />
                  <span>Sư Phạm Lịch Sử THPT</span>
                </Badge>
              </div>
              <DialogTitle className="font-serif text-xl text-foreground mt-1">
                {editingAssignmentId ? "Chỉnh Sửa Bài Tập Lớp" : "Giao Bài Tập Cho Lớp"}
              </DialogTitle>
              <DialogDescription className="text-xs text-muted-foreground">
                Tạo bài giao khảo sát di sản Đại Nội theo tuyến 35-45 phút và thiết lập trọng số Rubric (thang điểm 0–4).
              </DialogDescription>
            </DialogHeader>

            <div className="p-5 space-y-4 text-xs">
              {/* Class Name */}
              <div className="space-y-1.5">
                <label className="font-bold text-foreground block">
                  Tên lớp học được giao:
                </label>
                <Input
                  value={assignmentClass}
                  onChange={(e) => setAssignmentClass(e.target.value)}
                  placeholder="Ví dụ: Lớp 10A1 — THPT Chuyên Quốc Học"
                  required
                  className="h-9 text-xs rounded-xl"
                />
              </div>

              {/* Assignment Title */}
              <div className="space-y-1.5">
                <label className="font-bold text-foreground block">
                  Tiêu đề bài khảo sát:
                </label>
                <Input
                  value={assignmentTitle}
                  onChange={(e) => setAssignmentTitle(e.target.value)}
                  placeholder="Ví dụ: Khảo sát trục thần đạo Ngọ Môn — Điện Thái Hòa"
                  required
                  className="h-9 text-xs rounded-xl"
                />
              </div>

              {/* Select Journey / Activity */}
              <div className="space-y-1.5">
                <label className="font-bold text-foreground block">
                  Chọn hành trình khảo cứu di sản (35-45 phút):
                </label>
                <select
                  value={assignmentJourney}
                  onChange={(e) => setAssignmentJourney(e.target.value)}
                  className="w-full h-9 rounded-xl border border-input bg-background px-3 py-1 text-xs shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                >
                  {IMPERIAL_TRAILS.map((t) => (
                    <option key={t.slug} value={t.slug}>
                      {t.title} ({t.duration_minutes} phút)
                    </option>
                  ))}
                </select>
              </div>

              {/* Due Date */}
              <div className="space-y-1.5">
                <label className="font-bold text-foreground block">
                  Hạn nộp bài:
                </label>
                <Input
                  type="date"
                  value={assignmentDueDate}
                  onChange={(e) => setAssignmentDueDate(e.target.value)}
                  className="h-9 text-xs rounded-xl"
                />
              </div>

              {/* Rubric Weights (0 - 4 scale) */}
              <div className="space-y-2 rounded-xl border border-border/70 bg-muted/20 p-3">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-foreground text-xs">
                    Trọng số Rubric đánh giá (Thang 0 – 4):
                  </span>
                  <Badge variant="outline" className="text-[10px]">
                    Chuẩn GDPT 2018
                  </Badge>
                </div>
                <div className="grid grid-cols-2 gap-2.5 pt-1">
                  <div>
                    <span className="text-[11px] text-muted-foreground block truncate">
                      S1: Không gian
                    </span>
                    <Input
                      type="number"
                      min={0}
                      max={4}
                      value={rubricWeightS1}
                      onChange={(e) => setRubricWeightS1(Number(e.target.value))}
                      className="h-8 text-xs font-mono"
                    />
                  </div>
                  <div>
                    <span className="text-[11px] text-muted-foreground block truncate">
                      S2: Thời gian
                    </span>
                    <Input
                      type="number"
                      min={0}
                      max={4}
                      value={rubricWeightS2}
                      onChange={(e) => setRubricWeightS2(Number(e.target.value))}
                      className="h-8 text-xs font-mono"
                    />
                  </div>
                  <div>
                    <span className="text-[11px] text-muted-foreground block truncate">
                      S3: Sử liệu
                    </span>
                    <Input
                      type="number"
                      min={0}
                      max={4}
                      value={rubricWeightS3}
                      onChange={(e) => setRubricWeightS3(Number(e.target.value))}
                      className="h-8 text-xs font-mono"
                    />
                  </div>
                  <div>
                    <span className="text-[11px] text-muted-foreground block truncate">
                      S4: Lập luận
                    </span>
                    <Input
                      type="number"
                      min={0}
                      max={4}
                      value={rubricWeightS4}
                      onChange={(e) => setRubricWeightS4(Number(e.target.value))}
                      className="h-8 text-xs font-mono"
                    />
                  </div>
                </div>
              </div>
            </div>

            <DialogFooter className="p-4 border-t border-border/60 flex items-center justify-between gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setIsCreateAssignmentOpen(false)}
                className="text-xs"
              >
                Hủy
              </Button>
              <Button
                type="submit"
                size="sm"
                className="text-xs bg-primary text-primary-foreground font-semibold px-4"
              >
                {editingAssignmentId ? "Lưu thay đổi" : "Phát hành bài tập"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
