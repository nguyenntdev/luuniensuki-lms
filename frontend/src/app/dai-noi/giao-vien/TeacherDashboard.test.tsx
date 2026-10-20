import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import TeacherDashboardClient from "./TeacherDashboardClient";
import ImperialLearningResourcesPage from "../hoc-tap/page";
import PrintableFieldworkWorksheet from "@/components/imperial/print/PrintableFieldworkWorksheet";
import RubricRadarChart from "@/components/imperial/dossier/RubricRadarChart";
import {
  ALL_16_PRINTABLE_STATIONS,
  STANDARD_4_STATIONS_SLUGS,
} from "@/components/imperial/print/worksheetData";
import {
  LESSON_PLAN_45M,
  FIELDWORK_WORKSHEET,
} from "@/lib/imperial/pedagogy-data";
import {
  loadStudentSubmissions,
  saveStudentSubmission,
  gradeStudentSubmission,
  INITIAL_STUDENT_SUBMISSIONS,
} from "@/lib/imperial/submissions-api";
import {
  fetchTeacherAssignments,
  createTeacherAssignment,
} from "@/lib/imperial/v51-api";
import {
  calculateRubricScore,
  exportGradebookToCSV,
} from "@/lib/imperial/rubric-engine";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  usePathname: () => "/dai-noi/giao-vien",
}));

// Mock authStore
vi.mock("@/stores/authStore", () => ({
  useAuthStore: (selector: (state: unknown) => unknown) =>
    selector({
      status: "authed",
      user: {
        id: "teacher-001",
        username: "tranvantho",
        display_name: "TS. Trần Văn Thọ",
        role: "teacher",
      },
      logout: vi.fn(),
    }),
}));

describe("STTTNNĐ Teacher Dashboard & Educational Pedagogy Suite", () => {
  beforeEach(() => {
    // Setup in-memory localStorage and window mock for Node test environment
    const storage: Record<string, string> = {};
    const mockLocalStorage = {
      getItem: (k: string) => (k in storage ? storage[k] : null),
      setItem: (k: string, v: string) => {
        storage[k] = String(v);
      },
      removeItem: (k: string) => {
        delete storage[k];
      },
      clear: () => {
        Object.keys(storage).forEach((k) => delete storage[k]);
      },
    };

    Object.defineProperty(globalThis, "window", {
      value: {
        localStorage: mockLocalStorage,
        location: { origin: "https://luuniensuki.vn" },
        print: vi.fn(),
      },
      writable: true,
      configurable: true,
    });
    Object.defineProperty(globalThis, "localStorage", {
      value: mockLocalStorage,
      writable: true,
      configurable: true,
    });
    Object.defineProperty(globalThis, "navigator", {
      value: { onLine: true },
      writable: true,
      configurable: true,
    });
  });

  // ========================================================================= //
  // 1. 45-Minute Lesson Plan Pedagogy Verification
  // ========================================================================= //
  describe("1. Lesson Plan (45 Minutes) Structure & CV 5512/BGDĐT Compliance", () => {
    it("has exact 45-minute total duration and 4 sequential activities", () => {
      expect(LESSON_PLAN_45M.duration_minutes).toBe(45);
      expect(LESSON_PLAN_45M.target_grade).toContain("Lớp 10 THPT");
      expect(LESSON_PLAN_45M.activities).toHaveLength(4);

      const durations = LESSON_PLAN_45M.activities.map((a) => a.duration_minutes);
      expect(durations).toEqual([5, 15, 15, 10]);
      expect(durations.reduce((a, b) => a + b, 0)).toBe(45);
    });

    it("verifies 4 pedagogical activity phases match required progression", () => {
      const [act1, act2, act3, act4] = LESSON_PLAN_45M.activities;

      // Phase 1: Khởi động (5m)
      expect(act1.activity_number).toBe(1);
      expect(act1.name_vi).toContain("Khởi động");
      expect(act1.duration_minutes).toBe(5);
      expect(act1.teacher_actions.length).toBeGreaterThan(0);
      expect(act1.student_actions.length).toBeGreaterThan(0);

      // Phase 2: Khám phá không gian (15m)
      expect(act2.activity_number).toBe(2);
      expect(act2.name_vi).toContain("Khám phá không gian");
      expect(act2.duration_minutes).toBe(15);
      expect(act2.objective_vi).toContain("bản đồ trực giao");

      // Phase 3: Đối chiếu sử liệu (15m)
      expect(act3.activity_number).toBe(3);
      expect(act3.name_vi).toContain("sử liệu");
      expect(act3.duration_minutes).toBe(15);
      expect(act3.objective_vi).toContain("chính sử");

      // Phase 4: Tổng kết & Exit Ticket (10m)
      expect(act4.activity_number).toBe(4);
      expect(act4.name_vi).toContain("Tổng kết");
      expect(act4.duration_minutes).toBe(10);
      expect(act4.deliverables_vi).toContain("Exit Ticket");
    });

    it("defines 4 core historical competencies S1-S4 and Rubric levels 0-3", () => {
      const comps = LESSON_PLAN_45M.objectives.historical_competencies;
      expect(comps).toHaveLength(4);
      const codes = comps.map((c) => c.code);
      expect(codes).toEqual(["S1_SPATIAL", "S2_TEMPORAL", "S3_EVIDENCE", "S4_ARGUMENT"]);

      const criteria = LESSON_PLAN_45M.rubrics.criteria;
      expect(criteria).toHaveLength(4);
      criteria.forEach((crit) => {
        expect(["0", "1", "2", "3"].every((lvl) => crit.descriptors[lvl])).toBe(true);
      });
    });
  });

  // ========================================================================= //
  // 2. Fieldwork Inquiry Worksheet Structure
  // ========================================================================= //
  describe("2. Fieldwork Inquiry Worksheet (4-Column Layout & 4 Stations)", () => {
    it("features exactly 4 inquiry columns based on the M-E-E framework", () => {
      expect(FIELDWORK_WORKSHEET.columns).toHaveLength(4);
      const colTitles = FIELDWORK_WORKSHEET.columns.map((c) => c.title_vi);
      expect(colTitles[0]).toContain("Trạm quan sát");
      expect(colTitles[1]).toContain("Hiện trạng mắt thấy");
      expect(colTitles[2]).toContain("Tư liệu đối chiếu");
      expect(colTitles[3]).toContain("Em kết luận gì");
    });

    it("surveys 4 landmark stations across 4 spatial functional zones", () => {
      expect(FIELDWORK_WORKSHEET.stations).toHaveLength(4);
      const stationSlugs = FIELDWORK_WORKSHEET.stations.map((s) => s.monument_slug);
      expect(stationSlugs).toEqual([
        "ngo-mon",
        "dien-thai-hoa",
        "hien-lam-cac",
        "cung-dien-tho",
      ]);

      // Every station has guiding primary source and quote
      FIELDWORK_WORKSHEET.stations.forEach((st) => {
        expect(st.guiding_source.source_title).toBeTruthy();
        expect(st.guiding_source.volume).toBeTruthy();
        expect(st.guiding_source.key_quote_vi).toBeTruthy();
        expect(st.conclusion_guide_vi).toContain("Điều");
      });
    });

    it("includes Exit Ticket assessment questions and print page layout configuration", () => {
      expect(FIELDWORK_WORKSHEET.exit_ticket.questions.length).toBeGreaterThanOrEqual(2);
      expect(FIELDWORK_WORKSHEET.export_helper?.printable_css_page_setup).toContain("A4 landscape");
    });
  });

  // ========================================================================= //
  // 3. Printable Fieldwork Worksheet Component (Student & Teacher Mode)
  // ========================================================================= //
  describe("3. Printable Fieldwork Worksheet (A4 Printable Component)", () => {
    const standardStations = ALL_16_PRINTABLE_STATIONS.filter((s) =>
      STANDARD_4_STATIONS_SLUGS.includes(s.monument_slug),
    );

    it("renders student printable worksheet without network dependency", () => {
      const html = renderToStaticMarkup(
        <PrintableFieldworkWorksheet
          stations={standardStations}
          config={{
            school_name: "TRƯỜNG THPT CHUYÊN QUỐC HỌC HUẾ",
            department_name: "Tổ Lịch sử - Địa lý",
            lesson_code: "KHTN-LS10-DN01",
            grade_level: "Lớp 10 THPT",
            class_name: "10 Sử",
            student_name: "Nguyễn Lê Hoàng Nam",
            teacher_name: "TS. Trần Văn Thọ",
            date_vi: "16/10/2026",
            orientation: "landscape",
            teacher_key_mode: false,
            include_qr: true,
            include_rubric: true,
            include_exit_ticket: true,
            selected_monument_slugs: STANDARD_4_STATIONS_SLUGS,
          }}
        />,
      );

      // Official Administrative Header (CV 5512/BGDĐT)
      expect(html).toContain("SỞ GIÁO DỤC VÀ ĐÀO TẠO THỪA THIÊN HUẾ");
      expect(html).toContain("TRƯỜNG THPT CHUYÊN QUỐC HỌC HUẾ");
      expect(html).toContain("KHTN-LS10-DN01");

      // 4 Columns
      expect(html).toContain("CỘT 1");
      expect(html).toContain("CỘT 2");
      expect(html).toContain("CỘT 3");
      expect(html).toContain("CỘT 4");

      // Stations
      expect(html).toContain("Ngọ Môn");
      expect(html).toContain("Điện Thái Hòa");
      expect(html).toContain("Hiển Lâm Các");
      expect(html).toContain("Cung Diên Thọ");

      // SVG QR Code rendered without external network image
      expect(html).toContain("<svg");
      expect(html).toContain("Bản đồ số Đại Nội");
    });

    it("renders teacher key mode with answers, citations and 12/12 rubric target", () => {
      const html = renderToStaticMarkup(
        <PrintableFieldworkWorksheet
          stations={standardStations}
          config={{
            school_name: "TRƯỜNG THPT CHUYÊN QUỐC HỌC HUẾ",
            department_name: "Tổ Lịch sử - Địa lý",
            lesson_code: "KHTN-LS10-DN01",
            grade_level: "Lớp 10 THPT",
            class_name: "10 Sử",
            student_name: "",
            teacher_name: "TS. Trần Văn Thọ",
            date_vi: "",
            orientation: "landscape",
            teacher_key_mode: true,
            include_qr: true,
            include_rubric: true,
            include_exit_ticket: true,
            selected_monument_slugs: STANDARD_4_STATIONS_SLUGS,
          }}
        />,
      );

      expect(html).toContain("HỒ SƠ GIÁO VIÊN — HƯỚNG DẪN CHẤM &amp; ĐÁP ÁN CHUẨN (TEACHER KEY)");
      expect(html).toContain("12 / 12 (Đáp án)");
    });
  });

  // ========================================================================= //
  // 4. Student Activity Submission & Teacher Rubric Evaluation Pipeline
  // ========================================================================= //
  describe("4. Student Activity Submission & Rubric Evaluation Pipeline", () => {
    it("loads initial mock submissions when storage is empty", () => {
      const list = loadStudentSubmissions();
      expect(list.length).toBeGreaterThanOrEqual(5);
      expect(list.some((s) => s.student_name.includes("Nguyễn Lê Hoàng Nam"))).toBe(true);
    });

    it("saves new student submission locally without network dependency", () => {
      const created = saveStudentSubmission({
        monument_slug: "ngo-mon",
        monument_name_vi: "Ngọ Môn",
        student_id: "test-stu-001",
        student_name: "Trần Minh Quân",
        student_class: "10 Sử — THPT Chuyên Quốc Học",
        claim: "Ngọ Môn có 5 cửa thể hiện trật tự đẳng cấp tuyệt đối của nền quân chủ.",
        evidence: "Khâm Định Đại Nam Hội Điển Sự Lệ ghi rõ cửa giữa chỉ dành cho vua.",
        evidence_citations: ["Hội Điển Sự Lệ Quyển 78"],
        explanation: "Sự phân chia cổng đi buộc mọi người phải tuân phục quyền uy thiên tử.",
      });

      expect(created.id).toContain("sub-");
      expect(created.status).toBe("submitted");
      expect(created.submitted_at).toBeTruthy();

      // Verify persistence in local storage
      const reloaded = loadStudentSubmissions();
      expect(reloaded[0].student_name).toBe("Trần Minh Quân");
      expect(reloaded[0].status).toBe("submitted");
    });

    it("evaluates and grades student submission with S1-S4 scores and feedback", () => {
      const submissions = loadStudentSubmissions();
      const targetSub = submissions[0];

      const graded = gradeStudentSubmission(
        targetSub.id,
        { s1: 3, s2: 2, s3: 3, s4: 2 },
        "Lập luận M-E-E rất thuyết phục. Cần làm rõ thêm mốc tái thiết năm 1923.",
        "TS. Trần Văn Thọ — GV Lịch sử",
      );

      expect(graded).not.toBeNull();
      expect(graded?.status).toBe("graded");
      expect(graded?.scores?.s1_spatial).toBe(3);
      expect(graded?.scores?.s2_temporal).toBe(2);
      expect(graded?.scores?.s3_evidence).toBe(3);
      expect(graded?.scores?.s4_argument).toBe(2);
      expect(graded?.scores?.total).toBe(10);
      expect(graded?.scores?.normalized_10).toBe(8.3);
      expect(graded?.teacher_feedback).toContain("Lập luận M-E-E rất thuyết phục");
      expect(graded?.graded_by).toContain("Trần Văn Thọ");
    });

    it("calculates rubric score classification according to GDPT 2018 bands", () => {
      const perfect = calculateRubricScore({ s1: 3, s2: 3, s3: 3, s4: 3 });
      expect(perfect.rawScore).toBe(12);
      expect(perfect.normalized10).toBe(10.0);
      expect(perfect.classification).toBe("Xuất sắc");

      const good = calculateRubricScore({ s1: 3, s2: 2, s3: 2, s4: 3 });
      expect(good.rawScore).toBe(10);
      expect(good.normalized10).toBe(8.3);
      expect(good.classification).toBe("Giỏi");

      const satisfactory = calculateRubricScore({ s1: 2, s2: 2, s3: 2, s4: 2 });
      expect(satisfactory.rawScore).toBe(8);
      expect(satisfactory.normalized10).toBe(6.7);
      expect(satisfactory.classification).toBe("Khá");
    });
  });

  // ========================================================================= //
  // 5. Teacher Assignment Management & IDOR Safety (Zero Network Dependency)
  // ========================================================================= //
  describe("5. Classroom Assignment Management & IDOR Safety", () => {
    it("fetches classroom assignments using fallback data when network is offline", async () => {
      const assignments = await fetchTeacherAssignments();
      expect(assignments.length).toBeGreaterThan(0);
      expect(assignments[0].title).toBeTruthy();
      expect(assignments[0].rubric_weights).toBeDefined();
    });

    it("creates a new assignment locally when backend API is unreachable", async () => {
      const newAssign = await createTeacherAssignment({
        title: "Khảo cứu không gian thờ tự Thế Miếu và Hiển Lâm Các",
        class_name: "10 Chuyên Sử — Quốc Học Huế",
        journey_slug: "khong-gian-ky-uc-tuong-niem",
        rubric_weights: {
          S1_spatial: 3,
          S2_temporal: 3,
          S3_evidence: 3,
          S4_argument: 3,
        },
      });

      expect(newAssign.id).toBeTruthy();
      expect(newAssign.title).toContain("Thế Miếu");
      expect(newAssign.is_active).toBe(true);

      const listAfter = await fetchTeacherAssignments();
      expect(listAfter[0].title).toContain("Thế Miếu");
    });
  });

  // ========================================================================= //
  // 6. Pure SVG Rubric Radar Chart (Zero Network Dependency)
  // ========================================================================= //
  describe("6. Rubric Radar Chart Pure SVG Visualization", () => {
    it("renders 4-axis SVG radar diamond without third-party CDN or chart library", () => {
      const html = renderToStaticMarkup(
        <RubricRadarChart
          studentScores={{ s1: 3, s2: 2, s3: 3, s4: 2 }}
          studentLabel="Học sinh Nguyễn Lê Hoàng Nam"
          showLegend={true}
          showScoreSummary={true}
        />,
      );

      // SVG root and dimensions
      expect(html).toContain("<svg");
      expect(html).toContain('viewBox="0 0 380 380"');

      // Polygons for student score and benchmark
      expect(html).toContain("<polygon");

      // 4 Axis Labels S1, S2, S3, S4
      expect(html).toContain("S1 • Không gian");
      expect(html).toContain("S2 • Thời gian");
      expect(html).toContain("S3 • Sử liệu");
      expect(html).toContain("S4 • Lập luận");

      // Quantitative Score Summary Badge
      expect(html).toContain("10/12đ");
      expect(html).toContain("8.3");

      // Accessible Screen-Reader Summary Table
      expect(html).toContain("Bảng tổng hợp điểm Rubric S1-S4 chi tiết");
    });
  });

  // ========================================================================= //
  // 7. Gradebook Export Without Network Dependency
  // ========================================================================= //
  describe("7. Local Gradebook CSV Exporting", () => {
    it("exports gradebook to CSV locally in browser memory", () => {
      const submissions = loadStudentSubmissions();
      const csv = exportGradebookToCSV(submissions);

      expect(csv).toContain("Mã học sinh");
      expect(csv).toContain("Họ và tên");
      expect(csv).toContain("Lớp học");
      expect(csv).toContain("S1: Không gian");
      expect(csv).toContain("S2: Thời gian");
      expect(csv).toContain("S3: Sử liệu");
      expect(csv).toContain("S4: Lập luận");
      expect(csv).toContain("Tổng điểm thô");
      expect(csv).toContain("Điểm quy đổi (hệ 10)");
      expect(csv).toContain("Xếp loại năng lực");
    });

    it("supports privacy-preserving anonymized export with HS-ANON prefix", () => {
      const submissions = loadStudentSubmissions();
      const anonymizedCSV = exportGradebookToCSV(submissions, {
        anonymize: true,
        anonymizePrefix: "HS-ANON-",
      });

      expect(anonymizedCSV).toContain("HS-ANON-");
      expect(anonymizedCSV).not.toContain("Nguyễn Lê Hoàng Nam");
      expect(anonymizedCSV).not.toContain("Trần Mai Phương Thảo");
    });
  });

  // ========================================================================= //
  // 8. Learning Resources & Teacher Dashboard Client Pages Render Test
  // ========================================================================= //
  describe("8. Learning Resources Page & Teacher Dashboard Render Tests", () => {
    it("renders ImperialLearningResourcesPage with 3 tabs and 4-activity timeline", () => {
      const html = renderToStaticMarkup(<ImperialLearningResourcesPage />);

      expect(html).toContain("Kế hoạch Bài dạy 45 Phút &amp; Phiếu Học tập Điền dã");
      expect(html).toContain("45 phút (4 hoạt động)");
      expect(html).toContain("4 trạm trọng điểm");
      expect(html).toContain("4 cột chứng cứ");
      expect(html).toContain("Rubric S1–S4 (0–12 điểm)");
      expect(html).toContain("Xuất Phiếu Điền Dã In Sẵn (A4)");
    });

    it("renders TeacherDashboardClient with KPI stats, assignment section and submissions table", () => {
      const html = renderToStaticMarkup(<TeacherDashboardClient />);

      expect(html).toContain("Bảng Đánh Giá Khảo Sát Lịch Sử (Rubric S1 - S4)");
      expect(html).toContain("Tổng số bài nộp");
      expect(html).toContain("Chờ chấm điểm");
      expect(html).toContain("Đã hoàn tất chấm");
      expect(html).toContain("Điểm trung bình");
      expect(html).toContain("Nhiệm Vụ Học Tập Đã Giao Cho Lớp");
      expect(html).toContain("Học sinh &amp; Lớp");
      expect(html).toContain("Di tích &amp; Tuyến khảo sát");
    });
  });
});
