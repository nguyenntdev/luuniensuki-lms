"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  BookOpen,
  Calendar,
  CheckCircle2,
  Clock,
  Compass,
  Download,
  FileCheck,
  FileSpreadsheet,
  FileText,
  GraduationCap,
  Layers,
  MapPin,
  Printer,
  Sparkles,
  Bot,
  ArrowRight,
  ShieldCheck,
  ExternalLink,
} from "lucide-react";
import ImperialHeader from "@/components/imperial/shell/ImperialHeader";
import { Button } from "@/components/ui/button";
import {
  PrintWorksheetModal,
} from "@/components/imperial/print";
import {
  LESSON_PLAN_45M,
  FIELDWORK_WORKSHEET,
} from "@/lib/imperial/pedagogy-data";
import { cn } from "@/lib/utils";

type TabKey = "plan" | "worksheet" | "rubric";

export default function ImperialLearningResourcesPage() {
  const [activeTab, setActiveTab] = useState<TabKey>("plan");
  const [isPrintModalOpen, setIsPrintModalOpen] = useState(false);
  const [printTeacherMode, setPrintTeacherMode] = useState(false);

  const handleOpenPrintModal = (teacherMode = false) => {
    setPrintTeacherMode(teacherMode);
    setIsPrintModalOpen(true);
  };


  return (
    <div className="min-h-screen bg-background flex flex-col selection:bg-primary/20 selection:text-primary">
      {/* Top Header */}
      <ImperialHeader />

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-8 sm:px-6 space-y-8">
        {/* Hero Banner */}
        <div className="rounded-3xl border border-border/80 bg-gradient-to-br from-card via-card/90 to-primary/5 p-6 sm:p-8 shadow-xl space-y-4 print:hidden">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="space-y-1.5 max-w-2xl">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20">
                <GraduationCap className="size-3.5" />
                <span>Học liệu Sư phạm & Điền dã Di sản (Chuẩn GDPT 2018)</span>
              </div>
              <h1 className="font-serif font-bold text-2xl sm:text-3xl text-foreground">
                Kế hoạch Bài dạy 45 Phút & Phiếu Học tập Điền dã
              </h1>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Tài liệu phục vụ giảng dạy môn Lịch sử và Giáo dục địa phương lớp 10 THPT. Thiết kế dựa trên mô hình khám phá không gian trực giao, tra cứu chứng cứ chính sử triều Nguyễn và khung đánh giá năng lực Rubric S1–S4.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2.5">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleOpenPrintModal(false)}
                className="gap-2 border-primary/50 text-foreground hover:bg-primary/10 shadow-sm"
              >
                <Printer className="size-4 text-primary" />
                <span>Xuất Phiếu Điền Dã In Sẵn (A4)</span>
              </Button>

              <Button
                variant="secondary"
                size="sm"
                onClick={() => handleOpenPrintModal(true)}
                className="gap-2 bg-amber-500/10 text-amber-800 dark:text-amber-300 border border-amber-500/30 hover:bg-amber-500/20 shadow-sm"
              >
                <Sparkles className="size-4 text-amber-600 dark:text-amber-400" />
                <span>Bản Giáo Viên (Có Đáp Án)</span>
              </Button>

              <Link href="/dai-noi/ai">
                <Button size="sm" className="gap-2 bg-primary text-primary-foreground shadow-md">
                  <Bot className="size-4" />
                  <span>Trợ lý Lịch sử AI</span>
                </Button>
              </Link>
            </div>
          </div>

          {/* Quick Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-border/60">
            <div className="p-3 rounded-xl bg-background/60 border border-border/60">
              <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider block">
                Thời lượng bài dạy
              </span>
              <span className="text-lg font-serif font-bold text-foreground">
                45 phút (4 hoạt động)
              </span>
            </div>
            <div className="p-3 rounded-xl bg-background/60 border border-border/60">
              <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider block">
                Trạm khảo sát thực địa
              </span>
              <span className="text-lg font-serif font-bold text-foreground">
                4 trạm trọng điểm
              </span>
            </div>
            <div className="p-3 rounded-xl bg-background/60 border border-border/60">
              <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider block">
                Cấu trúc phiếu học tập
              </span>
              <span className="text-lg font-serif font-bold text-foreground">
                4 cột chứng cứ
              </span>
            </div>
            <div className="p-3 rounded-xl bg-background/60 border border-border/60">
              <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider block">
                Khung đánh giá
              </span>
              <span className="text-lg font-serif font-bold text-foreground">
                Rubric S1–S4 (0–12 điểm)
              </span>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 border-b border-border/70 pb-px print:hidden">
          <button
            type="button"
            onClick={() => setActiveTab("plan")}
            className={cn(
              "flex items-center gap-2 px-4 py-2.5 rounded-t-xl text-sm font-semibold border-b-2 transition-colors",
              activeTab === "plan"
                ? "border-primary text-primary bg-primary/5"
                : "border-transparent text-muted-foreground hover:text-foreground hover:bg-secondary/40",
            )}
          >
            <Clock className="size-4" />
            <span>Kế hoạch bài dạy 45 phút</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("worksheet")}
            className={cn(
              "flex items-center gap-2 px-4 py-2.5 rounded-t-xl text-sm font-semibold border-b-2 transition-colors",
              activeTab === "worksheet"
                ? "border-primary text-primary bg-primary/5"
                : "border-transparent text-muted-foreground hover:text-foreground hover:bg-secondary/40",
            )}
          >
            <FileSpreadsheet className="size-4" />
            <span>Phiếu học tập 4 cột</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("rubric")}
            className={cn(
              "flex items-center gap-2 px-4 py-2.5 rounded-t-xl text-sm font-semibold border-b-2 transition-colors",
              activeTab === "rubric"
                ? "border-primary text-primary bg-primary/5"
                : "border-transparent text-muted-foreground hover:text-foreground hover:bg-secondary/40",
            )}
          >
            <FileCheck className="size-4" />
            <span>Khung đánh giá Rubric S1–S4</span>
          </button>
        </div>

        {/* ============================================================== */}
        {/* Tab 1: Kế hoạch bài dạy 45 phút (Lesson Plan)                   */}
        {/* ============================================================== */}
        {activeTab === "plan" && (
          <div className="space-y-8 animate-in fade-in duration-200">
            {/* Header info */}
            <div className="p-6 rounded-2xl border border-border/80 bg-card space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-4">
                <div>
                  <h2 className="font-serif font-bold text-xl text-foreground">
                    {LESSON_PLAN_45M.title_vi}
                  </h2>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Đối tượng: {LESSON_PLAN_45M.target_grade} • Môn học: {LESSON_PLAN_45M.subject}
                  </p>
                </div>
                <div className="px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-700 dark:text-amber-400 font-semibold text-xs">
                  Thời lượng: {LESSON_PLAN_45M.duration_minutes} phút
                </div>
              </div>

              {/* Objectives: Historical Competencies */}
              <div className="space-y-3">
                <h3 className="font-serif font-bold text-sm text-foreground flex items-center gap-2">
                  <CheckCircle2 className="size-4 text-primary" />
                  <span>I. Mục tiêu bài dạy (Yêu cầu cần đạt)</span>
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {LESSON_PLAN_45M.objectives.historical_competencies.map((comp) => (
                    <div
                      key={comp.code}
                      className="p-3.5 rounded-xl border border-border/70 bg-secondary/30 space-y-1"
                    >
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold px-1.5 py-0.5 rounded bg-primary/10 text-primary">
                          {comp.code}
                        </span>
                        <span className="font-semibold text-xs text-foreground">
                          {comp.name_vi}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground leading-relaxed">
                        {comp.description_vi}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Materials */}
              <div className="space-y-3 pt-2">
                <h3 className="font-serif font-bold text-sm text-foreground flex items-center gap-2">
                  <Layers className="size-4 text-primary" />
                  <span>II. Thiết bị dạy học và học liệu số</span>
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div className="p-3.5 rounded-xl border border-border/70 bg-secondary/30 space-y-1.5">
                    <span className="font-semibold text-foreground">Giáo viên:</span>
                    <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                      {LESSON_PLAN_45M.teaching_equipment_and_digital_materials.teacher_materials.map((m, idx) => (
                        <li key={idx}>{m}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="p-3.5 rounded-xl border border-border/70 bg-secondary/30 space-y-1.5">
                    <span className="font-semibold text-foreground">Học sinh:</span>
                    <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                      {LESSON_PLAN_45M.teaching_equipment_and_digital_materials.student_materials.map((m, idx) => (
                        <li key={idx}>{m}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            {/* 4 Pedagogical Activities Timeline */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-serif font-bold text-lg text-foreground flex items-center gap-2">
                  <Clock className="size-5 text-primary" />
                  <span>III. Tiến trình 4 hoạt động dạy học (Tổng: 45 phút)</span>
                </h3>
                <span className="text-xs text-muted-foreground">
                  Chuẩn quy trình sư phạm theo công văn 5512/BGDĐT
                </span>
              </div>

              <div className="space-y-4">
                {LESSON_PLAN_45M.activities.map((act) => (
                  <div
                    key={act.activity_number}
                    className="p-5 rounded-2xl border border-border/80 bg-card space-y-3.5 shadow-sm"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-3">
                      <div className="flex items-center gap-2.5">
                        <span className="size-7 rounded-lg bg-primary text-primary-foreground font-bold text-xs flex items-center justify-center shrink-0">
                          {act.activity_number}
                        </span>
                        <h4 className="font-serif font-bold text-base text-foreground">
                          Hoạt động {act.activity_number}: {act.name_vi}
                        </h4>
                      </div>
                      <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20">
                        {act.duration_minutes} phút
                      </span>
                    </div>

                    <p className="text-xs font-medium text-primary/90">
                      <strong>Mục tiêu:</strong> {act.objective_vi}
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs pt-1">
                      <div className="space-y-1.5 p-3 rounded-xl bg-secondary/40 border border-border/50">
                        <span className="font-bold text-foreground">Hoạt động của Giáo viên:</span>
                        <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                          {act.teacher_actions.map((actItem, aIdx) => (
                            <li key={aIdx}>{actItem}</li>
                          ))}
                        </ul>
                      </div>

                      <div className="space-y-1.5 p-3 rounded-xl bg-secondary/40 border border-border/50">
                        <span className="font-bold text-foreground">Hoạt động của Học sinh:</span>
                        <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                          {act.student_actions.map((actItem, aIdx) => (
                            <li key={aIdx}>{actItem}</li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1 text-muted-foreground border-t border-border/50">
                      <div>
                        <strong className="text-foreground">Sản phẩm đầu ra:</strong> {act.deliverables_vi}
                      </div>
                      <div>
                        <strong className="text-foreground">Tiêu chí đánh giá:</strong> {act.assessment_criteria_vi}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Exit Ticket Appendix */}
            {LESSON_PLAN_45M.appendix?.exit_ticket_sample && (
              <div className="p-5 rounded-2xl border border-primary/30 bg-primary/5 space-y-2">
                <h4 className="font-serif font-bold text-sm text-primary flex items-center gap-2">
                  <FileCheck className="size-4" />
                  <span>Phụ lục: Đề bài Exit Ticket (Thu hoạch kết thúc giờ học)</span>
                </h4>
                <p className="text-xs text-foreground font-medium">
                  {LESSON_PLAN_45M.appendix.exit_ticket_sample.prompt_vi}
                </p>
                <p className="text-[11px] text-muted-foreground">
                  <strong>Dẫn chứng kỳ vọng:</strong> {LESSON_PLAN_45M.appendix.exit_ticket_sample.expected_evidence_vi}
                </p>
              </div>
            )}
          </div>
        )}

        {/* ============================================================== */}
        {/* Tab 2: Phiếu học tập 4 cột (Fieldwork Worksheet)                */}
        {/* ============================================================== */}
        {activeTab === "worksheet" && (
          <div className="space-y-6 animate-in fade-in duration-200">
            <div className="p-6 rounded-2xl border border-border/80 bg-card space-y-4">
              <div className="border-b border-border/60 pb-3 flex flex-wrap items-center justify-between gap-3">
                <div className="space-y-1">
                  <h2 className="font-serif font-bold text-xl text-foreground">
                    {FIELDWORK_WORKSHEET.title_vi}
                  </h2>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {FIELDWORK_WORKSHEET.subtitle_vi} • {FIELDWORK_WORKSHEET.target_audience}
                  </p>
                  <p className="text-xs text-primary font-medium mt-2">
                    <strong>Hướng dẫn:</strong> {FIELDWORK_WORKSHEET.instructions_vi}
                  </p>
                </div>

                <div className="flex items-center gap-2 print:hidden">
                  <Button
                    onClick={() => handleOpenPrintModal(false)}
                    size="sm"
                    className="gap-2 bg-primary text-primary-foreground font-semibold shadow-md"
                  >
                    <Printer className="size-4" />
                    <span>In Phiếu Điền Dã A4</span>
                  </Button>
                </div>
              </div>

              {/* Student Header Template Box */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3.5 rounded-xl bg-secondary/40 border border-border/70 text-xs">
                {FIELDWORK_WORKSHEET.metadata_fields.map((f) => (
                  <div key={f.key} className="space-y-1">
                    <span className="text-[10px] text-muted-foreground font-semibold uppercase">
                      {f.label_vi}
                    </span>
                    <div className="h-6 border-b border-dashed border-border/80" />
                  </div>
                ))}
              </div>

              {/* 4-Column Table */}
              <div className="overflow-x-auto">
                <table className="w-full border-collapse border border-border/80 text-xs">
                  <thead>
                    <tr className="bg-secondary/70">
                      {FIELDWORK_WORKSHEET.columns.map((col) => (
                        <th
                          key={col.column_id}
                          className="border border-border/80 p-3 text-left font-serif font-bold text-foreground min-w-[200px]"
                        >
                          <div className="text-[10px] text-primary uppercase font-mono">
                            Cột {col.number}
                          </div>
                          <div>{col.title_vi}</div>
                          <div className="text-[10px] font-normal text-muted-foreground font-sans mt-0.5">
                            {col.description_vi}
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {FIELDWORK_WORKSHEET.stations.map((st) => (
                      <tr key={st.station_index} className="hover:bg-card/70">
                        {/* Col 1: Station */}
                        <td className="border border-border/80 p-3 align-top bg-secondary/20">
                          <div className="font-bold text-foreground">
                            Trạm {st.station_index}: {st.monument_name_vi}
                          </div>
                          <div className="text-[10px] text-muted-foreground mt-0.5">
                            {st.zone_name_vi}
                          </div>
                          <Link
                            href={`/dai-noi/cong-trinh/${st.monument_slug}`}
                            className="inline-flex items-center gap-1 text-[11px] text-primary hover:underline mt-2 print:hidden"
                          >
                            <span>Xem hồ sơ</span>
                            <ExternalLink className="size-3" />
                          </Link>
                        </td>

                        {/* Col 2: Observation */}
                        <td className="border border-border/80 p-3 align-top">
                          <p className="text-muted-foreground leading-relaxed">
                            {st.observation_prompt_vi}
                          </p>
                          <div className="mt-3 min-h-[40px] border-b border-dashed border-border/60 text-[10px] text-muted-foreground/60 italic">
                            (Học sinh ghi chép hiện trạng...)
                          </div>
                        </td>

                        {/* Col 3: Evidence */}
                        <td className="border border-border/80 p-3 align-top bg-amber-500/5">
                          <div className="font-semibold text-amber-800 dark:text-amber-300 text-[11px]">
                            {st.guiding_source.source_title} ({st.guiding_source.volume})
                          </div>
                          <blockquote className="mt-1 pl-2 border-l border-amber-500/40 text-[11px] italic text-muted-foreground">
                            &ldquo;{st.guiding_source.key_quote_vi}&rdquo;
                          </blockquote>
                        </td>

                        {/* Col 4: Conclusion */}
                        <td className="border border-border/80 p-3 align-top bg-primary/5">
                          <p className="text-foreground/90 font-medium leading-relaxed">
                            {st.conclusion_guide_vi}
                          </p>
                          <div className="mt-3 min-h-[40px] border-b border-dashed border-border/60 text-[10px] text-muted-foreground/60 italic">
                            (Học sinh phân định điều chắc chắn vs cần kiểm chứng...)
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Exit Ticket */}
              <div className="p-4 rounded-xl border border-border/80 bg-secondary/30 space-y-3">
                <h3 className="font-serif font-bold text-sm text-foreground">
                  {FIELDWORK_WORKSHEET.exit_ticket.title_vi}
                </h3>
                <p className="text-xs text-muted-foreground">
                  {FIELDWORK_WORKSHEET.exit_ticket.instructions_vi}
                </p>

                <div className="space-y-3 pt-1">
                  {FIELDWORK_WORKSHEET.exit_ticket.questions.map((q, idx) => (
                    <div key={q.id} className="space-y-1">
                      <span className="text-xs font-semibold text-foreground">
                        Câu {idx + 1}: {q.question_vi}
                      </span>
                      <div className="min-h-[48px] rounded border border-border/60 bg-card p-2 text-xs text-muted-foreground/40 italic">
                        (Phần trả lời của học sinh...)
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* Tab 3: Khung đánh giá Rubric S1-S4                              */}
        {/* ============================================================== */}
        {activeTab === "rubric" && (
          <div className="space-y-6 animate-in fade-in duration-200">
            <div className="p-6 rounded-2xl border border-border/80 bg-card space-y-5">
              <div className="border-b border-border/60 pb-3">
                <h2 className="font-serif font-bold text-xl text-foreground">
                  Khung Tiêu chí Đánh giá Năng lực Lịch sử (Rubric S1–S4)
                </h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {LESSON_PLAN_45M.rubrics.scale_description}
                </p>
              </div>

              {/* Criteria Cards */}
              <div className="space-y-4">
                {LESSON_PLAN_45M.rubrics.criteria.map((crit) => (
                  <div
                    key={crit.id}
                    className="p-4 rounded-xl border border-border/80 bg-secondary/20 space-y-3"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-primary text-primary-foreground">
                        {crit.id}
                      </span>
                      <h3 className="font-serif font-bold text-sm text-foreground">
                        {crit.name_vi}
                      </h3>
                      <span className="text-xs text-muted-foreground">
                        ({crit.dimension})
                      </span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 text-xs">
                      {["0", "1", "2", "3"].map((levelKey) => {
                        const levelObj = LESSON_PLAN_45M.rubrics.levels.find(
                          (l) => l.score.toString() === levelKey,
                        );
                        return (
                          <div
                            key={levelKey}
                            className="p-3 rounded-lg border border-border/70 bg-card space-y-1"
                          >
                            <div className="flex items-center justify-between font-semibold">
                              <span className="text-primary font-mono">
                                {levelKey} điểm
                              </span>
                              <span className="text-[10px] text-muted-foreground">
                                {levelObj?.label_vi}
                              </span>
                            </div>
                            <p className="text-[11px] text-muted-foreground leading-normal">
                              {crit.descriptors[levelKey]}
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>

              {/* Overall Score Bands */}
              <div className="space-y-3 pt-2">
                <h3 className="font-serif font-bold text-sm text-foreground">
                  Thang xếp loại kết quả học tập (Tổng điểm tối đa: 12)
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                  {LESSON_PLAN_45M.rubrics.overall_bands.map((band, bIdx) => (
                    <div
                      key={bIdx}
                      className="p-3.5 rounded-xl border border-border/70 bg-secondary/30 space-y-1"
                    >
                      <div className="font-mono font-bold text-primary">
                        {band.min_score} – {band.max_score} điểm
                      </div>
                      <div className="font-semibold text-foreground text-[11px]">
                        {band.classification_vi}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 1-Click A4 Printable Fieldwork Worksheet Modal */}
        <PrintWorksheetModal
          open={isPrintModalOpen}
          onOpenChange={setIsPrintModalOpen}
          initialTeacherMode={printTeacherMode}
        />
      </main>
    </div>
  );
}
