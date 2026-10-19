"use client";

import React, { useState, useEffect, useMemo, Suspense } from "react";
import Link from "next/link";
import {
  BookOpen,
  Box,
  Hammer,
  GraduationCap,
  Sparkles,
  Compass,
  CheckCircle2,
  ChevronRight,
  ArrowRight,
  ShieldCheck,
  Library,
  ExternalLink,
  Calendar,
  Users,
  Filter,
  Clock,
  Info,
  Layers,
  Award,
  FileText,
  X,
} from "lucide-react";
import type {
  LearnPathwayModule,
  LearnRoadmapPhase,
  LearnModuleStatus,
  RbpcLocale,
} from "@/types/rbpc";
import { getRbpcCopy } from "@/lib/rbpc/copy";
import { cn } from "@/lib/utils";
import { setPageMeta } from "@/lib/seo";
import { RbpcCard, RbpcCardHeader } from "@/components/rbpc/RbpcCard";
import { RbpcButton } from "@/components/rbpc/RbpcButton";
import { LearnRoadmapCard } from "@/components/rbpc/LearnRoadmapCard";
import { LEARN_PATHWAY_MODULES } from "@/lib/rbpc/learnModules";

const PHASE_FILTERS: Array<{
  id: "all" | LearnRoadmapPhase;
  labelVi: string;
  labelEn: string;
  icon: React.ComponentType<{ className?: string }>;
}> = [
  { id: "all", labelVi: "Tất cả 4 chặng", labelEn: "All 4 Phases", icon: Layers },
  {
    id: "P1_HERITAGE_BASELINE",
    labelVi: "Chặng 1: Thư tịch Hoàng gia",
    labelEn: "Phase 1: Archives",
    icon: BookOpen,
  },
  {
    id: "P2_INTERACTIVE_3D",
    labelVi: "Chặng 2: Tương tác 3D",
    labelEn: "Phase 2: 3D Metallurgy",
    icon: Box,
  },
  {
    id: "P3_MAKER_MASTERCLASS",
    labelVi: "Chặng 3: Thực địa Nghệ nhân",
    labelEn: "Phase 3: Masterclass",
    icon: Hammer,
  },
  {
    id: "P4_ACCREDITED_CURRICULUM",
    labelVi: "Chặng 4: Lộ trình 2027–2028",
    labelEn: "Phase 4: Curriculum",
    icon: GraduationCap,
  },
];

function LearnPageContent() {
  const [locale, setLocale] = useState<RbpcLocale>("vi");
  const copy = getRbpcCopy(locale);

  // Active Phase filter
  const [activePhase, setActivePhase] = useState<"all" | LearnRoadmapPhase>("all");

  // Active Audience filter
  const [audienceFilter, setAudienceFilter] = useState<
    "all" | "visitor" | "student" | "educator"
  >("all");

  // Selected module for detail modal
  const [selectedModule, setSelectedModule] = useState<LearnPathwayModule | null>(null);

  // Set Page SEO & Title
  useEffect(() => {
    setPageMeta({
      title:
        locale === "vi"
          ? "Lộ trình học tập di sản & Cửu Đỉnh 3D — LƯU NIÊN"
          : "Heritage Learning Pathway & 3D Metallurgy — LƯU NIÊN",
      description:
        locale === "vi"
          ? "Khung giáo dục di sản 4 giai đoạn kết nối thư tịch triều Nguyễn, mô hình 3D bản đúc nổi Cửu Đỉnh, trải nghiệm xưởng nghề và đề án chứng chỉ phổ thông."
          : "Source-grounded 4-phase educational pathway connecting imperial archives, interactive 3D twins of the Nine Dynastic Urns, and living artisan workshops in Hue.",
      path: "/learn",
    });
  }, [locale]);

  // Filter modules
  const filteredModules = useMemo(() => {
    return LEARN_PATHWAY_MODULES.filter((mod) => {
      if (activePhase !== "all" && mod.roadmapPhase !== activePhase) {
        return false;
      }
      if (audienceFilter !== "all" && mod.targetAudience !== audienceFilter) {
        return false;
      }
      return true;
    });
  }, [activePhase, audienceFilter]);

  // Summary counts
  const stats = useMemo(() => {
    const total = LEARN_PATHWAY_MODULES.length;
    const available = LEARN_PATHWAY_MODULES.filter(
      (m) => m.status === "available_in_repo"
    ).length;
    const roadmap = LEARN_PATHWAY_MODULES.filter(
      (m) => m.status === "roadmap_phase_2"
    ).length;
    const totalCitations = LEARN_PATHWAY_MODULES.reduce(
      (acc, m) => acc + m.sourceCitationsCount,
      0
    );
    return { total, available, roadmap, totalCitations };
  }, []);

  return (
    <div className="rbpc-theme min-h-screen bg-[var(--rbpc-bg)] text-[var(--rbpc-ink)] py-8 sm:py-12 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl space-y-8 sm:space-y-12">
        {/* ===================================================================
            1. Navigation Breadcrumb & Locale Toggle
            =================================================================== */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[var(--rbpc-divider-subtle)] pb-4">
          <nav
            aria-label="Breadcrumb"
            className="flex items-center gap-2 text-xs text-[var(--rbpc-muted)]"
          >
            <Link
              href="/"
              className="hover:text-[var(--rbpc-primary)] flex items-center gap-1 transition-colors"
            >
              <Compass className="h-3.5 w-3.5" aria-hidden="true" />
              <span>{locale === "vi" ? "Trang chủ" : "Home"}</span>
            </Link>
            <ChevronRight className="h-3 w-3" aria-hidden="true" />
            <Link
              href="/explore"
              className="hover:text-[var(--rbpc-primary)] transition-colors"
            >
              {copy.nav.discover}
            </Link>
            <ChevronRight className="h-3 w-3" aria-hidden="true" />
            <span className="font-semibold text-[var(--rbpc-ink)]">
              {locale === "vi" ? "Lộ trình học tập (Learn)" : "Learn Pathway"}
            </span>
          </nav>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setLocale(locale === "vi" ? "en" : "vi")}
              className="inline-flex min-h-[44px] items-center gap-1.5 rounded-full border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] px-3.5 py-1 text-xs font-semibold text-[var(--rbpc-ink)] hover:border-[var(--rbpc-primary-border)] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)]"
              aria-label="Toggle language"
            >
              <span>{locale === "vi" ? "English" : "Tiếng Việt"}</span>
            </button>

            <Link
              href="/cuu-dinh"
              className="inline-flex min-h-[44px] items-center gap-1.5 rounded-full border border-[var(--rbpc-primary-border)] bg-[var(--rbpc-primary-subtle)] px-3.5 py-1 text-xs font-semibold text-[var(--rbpc-primary)] hover:bg-[var(--rbpc-primary)] hover:text-white transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)]"
            >
              <Box className="h-3.5 w-3.5" aria-hidden="true" />
              <span>{locale === "vi" ? "Mô hình Cửu Đỉnh 3D" : "Cửu Đỉnh 3D Twins"}</span>
            </Link>
          </div>
        </div>

        {/* ===================================================================
            2. Header Banner & Pedagogical Narrative
            =================================================================== */}
        <header className="space-y-4">
          <div className="inline-flex items-center gap-2 rounded-full border border-[var(--rbpc-primary-border)] bg-[var(--rbpc-primary-subtle)] px-3.5 py-1 text-xs font-semibold text-[var(--rbpc-primary)]">
            <GraduationCap className="h-3.5 w-3.5" aria-hidden="true" />
            <span>
              {locale === "vi"
                ? "Khung kết nối giáo dục di sản LƯU NIÊN — 4 Chặng đồng hành"
                : "LƯU NIÊN Heritage Pedagogical Continuum — 4-Phase Pathway"}
            </span>
          </div>

          <h1 className="font-serif text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-[var(--rbpc-ink)] leading-tight">
            {locale === "vi"
              ? "Từ Ký Ức Thư Tịch Hoàng Triều Đến Bàn Tay Người Thợ Hôm Nay"
              : "From Imperial Archival Memory to Living Hands of Master Artisans"}
          </h1>

          <p className="text-sm sm:text-base text-[var(--rbpc-ink-subtle)] max-w-3xl leading-relaxed">
            {locale === "vi"
              ? "Lộ trình học tập có dẫn chứng sử liệu, kết nối tư liệu thành văn triều Nguyễn, bảo vật quốc gia Cửu Đỉnh qua mô hình 3D tương tác, trải nghiệm xưởng nghề và đề án chứng chỉ phổ thông."
              : "A source-grounded curriculum bridging classical imperial texts, national treasure 3D digital twins, authentic living workshops, and accredited secondary school frameworks."}
          </p>
        </header>

        {/* ===================================================================
            3. TRANSPARENT POSITIONING CALLOUT (Master Spec Mandate)
               "Learn is an educational extension and technical proof,
                not an enterprise SaaS MVP."
            =================================================================== */}
        <section aria-labelledby="epistemic-positioning-heading">
          <RbpcCard
            elevation="surface"
            padding="responsive"
            className="border-l-4 border-l-[var(--rbpc-primary)] bg-[var(--rbpc-surface)] space-y-3"
          >
            <div className="flex items-center gap-2 font-semibold text-sm text-[var(--rbpc-primary)]">
              <ShieldCheck className="h-5 w-5 shrink-0" aria-hidden="true" />
              <h2 id="epistemic-positioning-heading" className="text-sm font-bold uppercase tracking-wider">
                {locale === "vi"
                  ? "Định vị Kỹ thuật & Cam kết Tính Minh Bạch (Epistemic Positioning)"
                  : "Technical Positioning & Epistemic Transparency Statement"}
              </h2>
            </div>

            <div className="space-y-2 text-xs sm:text-sm text-[var(--rbpc-ink-subtle)] leading-relaxed">
              <p>
                {locale === "vi" ? (
                  <>
                    <strong className="text-[var(--rbpc-ink)]">
                      Lộ trình Học tập (Learn Pathway)
                    </strong>{" "}
                    là phần mở rộng giáo dục và bằng chứng năng lực kỹ thuật (
                    <em>technical proof of capability</em>) của LƯU NIÊN —{" "}
                    <strong className="text-[var(--rbpc-primary)]">
                      không phải sản phẩm phần mềm quản lý doanh nghiệp (enterprise SaaS MVP)
                    </strong>
                    . Chúng tôi không cố gắng thương mại hóa dữ liệu học viên hay thu phí thuê bao nền tảng.
                  </>
                ) : (
                  <>
                    <strong className="text-[var(--rbpc-ink)]">
                      The Learn Pathway
                    </strong>{" "}
                    serves as an educational extension and tangible technical proof of capability
                    for LƯU NIÊN —{" "}
                    <strong className="text-[var(--rbpc-primary)]">
                      not an enterprise SaaS MVP
                    </strong>
                    . We do not monetize learner data nor impose subscription paywalls on public heritage.
                  </>
                )}
              </p>

              <p>
                {locale === "vi"
                  ? "Mọi nội dung đều tuân thủ nguyên tắc tôn vinh nghệ nhân như chủ thể văn hóa, kết hợp giữa chứng cứ thư tịch chính sử và thực tế xưởng nghề truyền thống tại Thừa Thiên Huế."
                  : "All modules adhere strictly to dignity and informed consent: honoring artisans as culture bearers, bridging canonical primary sources with active craft foundries in Thừa Thiên Huế."}
              </p>
            </div>

            {/* Quick Metrics Strip */}
            <div className="pt-2 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs border-t border-[var(--rbpc-divider-subtle)]">
              <div className="space-y-0.5">
                <span className="text-[11px] text-[var(--rbpc-muted)] uppercase tracking-wider block">
                  {locale === "vi" ? "Chặng học tập" : "Curriculum Phases"}
                </span>
                <span className="font-mono text-base font-bold text-[var(--rbpc-ink)]">
                  4 {locale === "vi" ? "chặng liên hoàn" : "phases"}
                </span>
              </div>

              <div className="space-y-0.5">
                <span className="text-[11px] text-[var(--rbpc-muted)] uppercase tracking-wider block">
                  {locale === "vi" ? "Bài học cốt lõi" : "Core Modules"}
                </span>
                <span className="font-mono text-base font-bold text-[var(--rbpc-primary)]">
                  {stats.total} {locale === "vi" ? "chuyên đề" : "modules"}
                </span>
              </div>

              <div className="space-y-0.5">
                <span className="text-[11px] text-[var(--rbpc-muted)] uppercase tracking-wider block">
                  {locale === "vi" ? "Nguồn thư tịch đối chiếu" : "Source Citations"}
                </span>
                <span className="font-mono text-base font-bold text-[var(--rbpc-highlight)]">
                  {stats.totalCitations}+ {locale === "vi" ? "văn bản" : "verified sources"}
                </span>
              </div>

              <div className="space-y-0.5">
                <span className="text-[11px] text-[var(--rbpc-muted)] uppercase tracking-wider block">
                  {locale === "vi" ? "Lộ trình tương lai" : "Future Accredited"}
                </span>
                <span className="font-mono text-base font-bold text-purple-700 dark:text-purple-400">
                  2027–2028 {locale === "vi" ? "đề án" : "roadmap"}
                </span>
              </div>
            </div>
          </RbpcCard>
        </section>

        {/* ===================================================================
            4. 4-Phase Progression Visual Flow
            =================================================================== */}
        <section aria-labelledby="pathway-flow-heading" className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 id="pathway-flow-heading" className="font-serif text-xl sm:text-2xl font-bold text-[var(--rbpc-ink)]">
              {locale === "vi"
                ? "Khung 4 Chặng Tiến Trình Học Tập"
                : "4-Phase Progression Framework"}
            </h2>
            <span className="text-xs text-[var(--rbpc-muted)]">
              {locale === "vi" ? "Tuần tự từ sử liệu đến thực nghiệm" : "Sequential from archives to practice"}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Phase 1 Card */}
            <div className="rounded-xl border border-blue-700/20 bg-blue-500/5 p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-blue-600 text-white font-mono text-xs font-bold">
                  1
                </span>
                <BookOpen className="h-4 w-4 text-blue-700 dark:text-blue-400" aria-hidden="true" />
              </div>
              <h3 className="font-serif text-sm font-bold text-[var(--rbpc-ink)]">
                {locale === "vi" ? "Nền tảng Thư tịch" : "Archival Foundation"}
              </h3>
              <p className="text-xs text-[var(--rbpc-muted)] leading-relaxed">
                {locale === "vi"
                  ? "Khảo cứu sử liệu Khâm Định và Châu bản triều Nguyễn làm điểm tựa học thuật."
                  : "Imperial Annals & court decrees establishing epistemological grounding."}
              </p>
            </div>

            {/* Phase 2 Card */}
            <div className="rounded-xl border border-teal-700/20 bg-teal-500/5 p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-teal-600 text-white font-mono text-xs font-bold">
                  2
                </span>
                <Box className="h-4 w-4 text-teal-700 dark:text-teal-400" aria-hidden="true" />
              </div>
              <h3 className="font-serif text-sm font-bold text-[var(--rbpc-ink)]">
                {locale === "vi" ? "Tương tác 3D & Bản đúc" : "Interactive 3D Twins"}
              </h3>
              <p className="text-xs text-[var(--rbpc-muted)] leading-relaxed">
                {locale === "vi"
                  ? "Quan sát 162 bản đúc nổi trên Cửu Đỉnh qua mô hình WebGL 3D trực quan."
                  : "Explore 162 relief inscriptions via responsive WebGL 3D digital twins."}
              </p>
            </div>

            {/* Phase 3 Card */}
            <div className="rounded-xl border border-amber-700/20 bg-amber-500/5 p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-amber-600 text-white font-mono text-xs font-bold">
                  3
                </span>
                <Hammer className="h-4 w-4 text-amber-700 dark:text-amber-400" aria-hidden="true" />
              </div>
              <h3 className="font-serif text-sm font-bold text-[var(--rbpc-ink)]">
                {locale === "vi" ? "Thực địa & Nghệ nhân" : "Maker Masterclass"}
              </h3>
              <p className="text-xs text-[var(--rbpc-muted)] leading-relaxed">
                {locale === "vi"
                  ? "Kết nối xưởng đúc đồng Phường Đúc & Pháp lam với người thợ truyền thống."
                  : "Direct field encounters and loams with living master craft practitioners."}
              </p>
            </div>

            {/* Phase 4 Card */}
            <div className="rounded-xl border border-purple-700/20 bg-purple-500/5 p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-purple-600 text-white font-mono text-xs font-bold">
                  4
                </span>
                <GraduationCap className="h-4 w-4 text-purple-700 dark:text-purple-400" aria-hidden="true" />
              </div>
              <h3 className="font-serif text-sm font-bold text-[var(--rbpc-ink)]">
                {locale === "vi" ? "Khung Chứng chỉ 2027" : "Curriculum Roadmap"}
              </h3>
              <p className="text-xs text-[var(--rbpc-muted)] leading-relaxed">
                {locale === "vi"
                  ? "Đề án chứng chỉ mở kết hợp bảo tàng, trường học và địa phương sau 2026."
                  : "Accredited open micro-credentials linking schools, museums, and guilds."}
              </p>
            </div>
          </div>
        </section>

        {/* ===================================================================
            5. Phase & Audience Filter Controls
            =================================================================== */}
        <section aria-labelledby="filter-heading" className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--rbpc-divider)] pb-3">
            {/* Phase Filter Tabs */}
            <div
              role="tablist"
              aria-label="Roadmap Phase Filters"
              className="flex flex-wrap gap-1.5"
            >
              {PHASE_FILTERS.map((pf) => {
                const Icon = pf.icon;
                const isSelected = activePhase === pf.id;
                return (
                  <button
                    key={pf.id}
                    type="button"
                    role="tab"
                    aria-selected={isSelected}
                    onClick={() => setActivePhase(pf.id)}
                    className={cn(
                      "inline-flex min-h-[44px] items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all select-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)]",
                      isSelected
                        ? "bg-[var(--rbpc-primary)] text-white shadow-xs"
                        : "border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] text-[var(--rbpc-ink)] hover:border-[var(--rbpc-primary-border)]"
                    )}
                  >
                    <Icon className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                    <span>{locale === "vi" ? pf.labelVi : pf.labelEn}</span>
                  </button>
                );
              })}
            </div>

            {/* Target Audience Dropdown */}
            <div className="flex items-center gap-2 shrink-0">
              <label
                htmlFor="learn-audience-select"
                className="text-xs font-semibold text-[var(--rbpc-muted)] flex items-center gap-1"
              >
                <Users className="h-3.5 w-3.5" aria-hidden="true" />
                <span>{locale === "vi" ? "Đối tượng:" : "Audience:"}</span>
              </label>
              <select
                id="learn-audience-select"
                value={audienceFilter}
                onChange={(e) =>
                  setAudienceFilter(
                    e.target.value as "all" | "visitor" | "student" | "educator"
                  )
                }
                className="rbpc-select text-xs min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)]"
              >
                <option value="all">
                  {locale === "vi" ? "Tất cả đối tượng" : "All Audiences"}
                </option>
                <option value="visitor">
                  {locale === "vi" ? "Khách tham quan" : "Visitors"}
                </option>
                <option value="student">
                  {locale === "vi" ? "Học sinh & Sinh viên" : "Students"}
                </option>
                <option value="educator">
                  {locale === "vi" ? "Nhà giáo dục" : "Educators"}
                </option>
              </select>
            </div>
          </div>
        </section>

        {/* ===================================================================
            6. Educational Pathway Modules Grid
            =================================================================== */}
        <section aria-labelledby="modules-heading" className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 id="modules-heading" className="font-serif text-xl sm:text-2xl font-bold text-[var(--rbpc-ink)]">
              {locale === "vi" ? "Danh Mục Chuyên Đề Bài Học" : "Curriculum Modules"}
            </h2>
            <span className="text-xs font-mono text-[var(--rbpc-muted)]">
              {locale === "vi"
                ? `Hiển thị ${filteredModules.length}/${LEARN_PATHWAY_MODULES.length} bài học`
                : `Showing ${filteredModules.length} of ${LEARN_PATHWAY_MODULES.length} modules`}
            </span>
          </div>

          {filteredModules.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {filteredModules.map((module) => {
                // Determine direct route link for card
                let customHref: string | undefined = undefined;
                if (module.linked3DArtefactSlug) {
                  customHref = `/cuu-dinh/${module.linked3DArtefactSlug}`;
                } else if (module.roadmapPhase === "P3_MAKER_MASTERCLASS") {
                  customHref = "/rbpc/inquiries?experience=workshop-duc-dong-phuong-duc";
                } else if (module.roadmapPhase === "P1_HERITAGE_BASELINE") {
                  customHref = "/sources";
                }

                return (
                  <LearnRoadmapCard
                    key={module.id}
                    module={module}
                    locale={locale}
                    href={customHref}
                    onSelectModule={(mod) => setSelectedModule(mod)}
                  />
                );
              })}
            </div>
          ) : (
            <div className="rounded-2xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-12 text-center space-y-3">
              <Layers className="h-10 w-10 text-[var(--rbpc-muted)] mx-auto" aria-hidden="true" />
              <h3 className="font-serif text-lg font-bold text-[var(--rbpc-ink)]">
                {locale === "vi"
                  ? "Không tìm thấy chuyên đề phù hợp bộ lọc"
                  : "No modules found matching active filters"}
              </h3>
              <p className="text-xs text-[var(--rbpc-muted)] max-w-md mx-auto">
                {locale === "vi"
                  ? "Vui lòng chọn lại chặng học tập hoặc thiết lập lại đối tượng người học để xem danh sách đầy đủ."
                  : "Please select a different phase or clear the target audience filter to see all modules."}
              </p>
              <RbpcButton
                variant="secondary"
                size="sm"
                onClick={() => {
                  setActivePhase("all");
                  setAudienceFilter("all");
                }}
              >
                <span>{locale === "vi" ? "Đặt lại bộ lọc" : "Reset Filters"}</span>
              </RbpcButton>
            </div>
          )}
        </section>

        {/* ===================================================================
            7. Cross-Platform Bridge Footer (Explore & Partner Links)
            =================================================================== */}
        <section aria-labelledby="bridge-heading" className="pt-6">
          <RbpcCard elevation="surface" padding="responsive" className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[var(--rbpc-divider-subtle)] pb-4">
              <div>
                <h3 id="bridge-heading" className="font-serif text-lg sm:text-xl font-bold text-[var(--rbpc-ink)]">
                  {locale === "vi"
                    ? "Kết Nối Xuyên Suốt Hệ Thống LƯU NIÊN"
                    : "Interconnected Across the LƯU NIÊN Ecosystem"}
                </h3>
                <p className="text-xs text-[var(--rbpc-muted)]">
                  {locale === "vi"
                    ? "Từ trang học tập, bạn có thể dễ dàng chuyển sang trải nghiệm 3D chi tiết hoặc đăng ký giao lưu trực tiếp cùng nghệ nhân."
                    : "Seamlessly navigate between 3D artefacts, archival sources, and in-person artisan workshop inquiries."}
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <RbpcButton asChild variant="primary" size="md">
                  <Link href="/cuu-dinh">
                    <Box className="h-4 w-4 mr-1.5" aria-hidden="true" />
                    <span>{locale === "vi" ? "Khám phá 3D Cửu Đỉnh" : "Explore 3D Cửu Đỉnh"}</span>
                  </Link>
                </RbpcButton>

                <RbpcButton asChild variant="secondary" size="md">
                  <Link href="/rbpc/inquiries">
                    <Calendar className="h-4 w-4 mr-1.5" aria-hidden="true" />
                    <span>{locale === "vi" ? "Yêu cầu lịch trải nghiệm" : "Experience Inquiries"}</span>
                  </Link>
                </RbpcButton>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs text-[var(--rbpc-ink-subtle)] leading-relaxed">
              <div className="space-y-1">
                <strong className="block text-[var(--rbpc-ink)] font-semibold flex items-center gap-1.5">
                  <Library className="h-3.5 w-3.5 text-[var(--rbpc-primary)]" />
                  <span>{locale === "vi" ? "Thư tịch chính thống" : "Primary Sources"}</span>
                </strong>
                <p>
                  {locale === "vi"
                    ? "Mỗi bài học đều trích dẫn chính xác tập, trang và chỉ dụ từ Khâm Định Đại Nam Hội Điển Sự Lệ và Châu bản triều Nguyễn."
                    : "Every lesson cites exact volume, page, and court decrees from the Imperial Annals and Nguyen Dynasty Vermilion Records."}
                </p>
              </div>

              <div className="space-y-1">
                <strong className="block text-[var(--rbpc-ink)] font-semibold flex items-center gap-1.5">
                  <Box className="h-3.5 w-3.5 text-[var(--rbpc-highlight)]" />
                  <span>{locale === "vi" ? "Bản số hóa 3D trung thực" : "True-to-Scale 3D Twins"}</span>
                </strong>
                <p>
                  {locale === "vi"
                    ? "Không sử dụng mô hình tưởng tượng: Dữ liệu hình học và bản đúc nổi bám sát nguyên bản 9 đỉnh đồng đặt trước Thế Miếu."
                    : "Geometric and relief data strictly reproduces the authentic physical Nine Dynastic Urns preserved at the Imperial Citadel."}
                </p>
              </div>

              <div className="space-y-1">
                <strong className="block text-[var(--rbpc-ink)] font-semibold flex items-center gap-1.5">
                  <Hammer className="h-3.5 w-3.5 text-amber-700 dark:text-amber-400" />
                  <span>{locale === "vi" ? "Nghệ nhân chủ thể" : "Artisans as Cultural Subjects"}</span>
                </strong>
                <p>
                  {locale === "vi"
                    ? "Nghệ nhân được tôn vinh với đầy đủ thâm niên, dòng họ và văn bản đồng thuận minh bạch, tuyệt đối không thương mại hóa sai lệch."
                    : "Master artisans are documented with verified lineages and informed consent, shielded from exploitative commercialization."}
                </p>
              </div>
            </div>
          </RbpcCard>
        </section>

        {/* ===================================================================
            8. Module Detail Modal (When user clicks module card)
            =================================================================== */}
        {selectedModule && (
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="module-modal-title"
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs"
            onClick={() => setSelectedModule(null)}
          >
            <div
              className="relative w-full max-w-xl rounded-2xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-6 sm:p-8 shadow-[var(--rbpc-shadow-lg)] space-y-6 max-h-[90vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Close Button */}
              <button
                type="button"
                onClick={() => setSelectedModule(null)}
                className="absolute right-4 top-4 inline-flex min-h-[44px] min-w-[44px] items-center justify-center rounded-lg border border-[var(--rbpc-divider-subtle)] text-[var(--rbpc-muted)] hover:text-[var(--rbpc-ink)] hover:bg-[var(--rbpc-surface-muted)] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)]"
                aria-label={copy.cta.close}
              >
                <X className="h-5 w-5" aria-hidden="true" />
              </button>

              <div className="space-y-2 pr-8">
                <span className="inline-flex items-center gap-1.5 rounded-full border border-blue-700/30 bg-blue-500/10 px-2.5 py-0.5 text-xs font-semibold text-blue-900 dark:text-blue-300">
                  <GraduationCap className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>
                    {selectedModule.roadmapPhase === "P1_HERITAGE_BASELINE" &&
                      (locale === "vi" ? "Chặng 1: Thư tịch Hoàng gia" : "Phase 1: Archives")}
                    {selectedModule.roadmapPhase === "P2_INTERACTIVE_3D" &&
                      (locale === "vi" ? "Chặng 2: Tương tác 3D" : "Phase 2: 3D Metallurgy")}
                    {selectedModule.roadmapPhase === "P3_MAKER_MASTERCLASS" &&
                      (locale === "vi" ? "Chặng 3: Thực địa Nghệ nhân" : "Phase 3: Masterclass")}
                    {selectedModule.roadmapPhase === "P4_ACCREDITED_CURRICULUM" &&
                      (locale === "vi" ? "Chặng 4: Lộ trình 2027–2028" : "Phase 4: Curriculum")}
                  </span>
                </span>

                <h3 id="module-modal-title" className="font-serif text-xl sm:text-2xl font-bold text-[var(--rbpc-ink)]">
                  {selectedModule.title[locale] || selectedModule.title.vi}
                </h3>
              </div>

              {/* Description */}
              <p className="text-sm text-[var(--rbpc-ink-subtle)] leading-relaxed">
                {selectedModule.description[locale] || selectedModule.description.vi}
              </p>

              {/* Metadata */}
              <div className="grid grid-cols-2 gap-3 text-xs p-3 rounded-xl bg-[var(--rbpc-surface-muted)] border border-[var(--rbpc-divider-subtle)]">
                <div>
                  <span className="text-[var(--rbpc-muted)] block text-[11px]">
                    {locale === "vi" ? "Niên đại lịch sử:" : "Historical Period:"}
                  </span>
                  <span className="font-semibold text-[var(--rbpc-ink)]">
                    {selectedModule.historicalPeriod}
                  </span>
                </div>
                <div>
                  <span className="text-[var(--rbpc-muted)] block text-[11px]">
                    {locale === "vi" ? "Nguồn thư tịch đối chiếu:" : "Source Citations:"}
                  </span>
                  <span className="font-semibold text-[var(--rbpc-primary)] font-mono">
                    {selectedModule.sourceCitationsCount} {locale === "vi" ? "văn bản" : "sources"}
                  </span>
                </div>
              </div>

              {/* Objectives List */}
              {selectedModule.learningObjectives && selectedModule.learningObjectives.length > 0 && (
                <div className="space-y-2">
                  <span className="block text-xs font-semibold uppercase tracking-wider text-[var(--rbpc-muted)]">
                    {locale === "vi" ? "Mục tiêu bài học:" : "Learning Objectives:"}
                  </span>
                  <ul className="space-y-2 text-xs sm:text-sm text-[var(--rbpc-ink)]">
                    {selectedModule.learningObjectives.map((obj, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <CheckCircle2 className="h-4 w-4 text-[var(--rbpc-primary)] shrink-0 mt-0.5" aria-hidden="true" />
                        <span>{obj[locale] || obj.vi}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Action Buttons */}
              <div className="pt-4 border-t border-[var(--rbpc-divider-subtle)] flex flex-col sm:flex-row items-center justify-between gap-3">
                <RbpcButton
                  type="button"
                  variant="secondary"
                  size="md"
                  className="w-full sm:w-auto"
                  onClick={() => setSelectedModule(null)}
                >
                  <span>{locale === "vi" ? "Đóng cửa sổ" : "Close"}</span>
                </RbpcButton>

                {selectedModule.linked3DArtefactSlug && (
                  <RbpcButton asChild variant="primary" size="md" className="w-full sm:w-auto">
                    <Link href={`/cuu-dinh/${selectedModule.linked3DArtefactSlug}`}>
                      <Box className="h-4 w-4 mr-1.5" aria-hidden="true" />
                      <span>
                        {locale === "vi" ? "Mở mô hình 3D tương tác" : "Launch 3D Viewer"}
                      </span>
                    </Link>
                  </RbpcButton>
                )}

                {selectedModule.roadmapPhase === "P3_MAKER_MASTERCLASS" && (
                  <RbpcButton asChild variant="primary" size="md" className="w-full sm:w-auto">
                    <Link href="/rbpc/inquiries?experience=workshop-duc-dong-phuong-duc">
                      <Calendar className="h-4 w-4 mr-1.5" aria-hidden="true" />
                      <span>
                        {locale === "vi" ? "Đăng ký yêu cầu xưởng nghề" : "Request Workshop"}
                      </span>
                    </Link>
                  </RbpcButton>
                )}

                {selectedModule.roadmapPhase === "P1_HERITAGE_BASELINE" && (
                  <RbpcButton asChild variant="primary" size="md" className="w-full sm:w-auto">
                    <Link href="/sources">
                      <Library className="h-4 w-4 mr-1.5" aria-hidden="true" />
                      <span>
                        {locale === "vi" ? "Tra cứu thư tịch gốc" : "View Sources"}
                      </span>
                    </Link>
                  </RbpcButton>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function LearnPage() {
  return (
    <Suspense
      fallback={
        <div className="rbpc-theme min-h-screen bg-[var(--rbpc-bg)] flex items-center justify-center p-8">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--rbpc-primary)] border-t-transparent" />
        </div>
      }
    >
      <LearnPageContent />
    </Suspense>
  );
}
