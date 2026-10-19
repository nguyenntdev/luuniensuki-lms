"use client";

import React from "react";
import Link from "next/link";
import {
  BookOpen,
  Box,
  Hammer,
  GraduationCap,
  Clock,
  Library,
  Layers,
  ChevronRight,
  ExternalLink,
  CheckCircle2,
  Calendar,
  Sparkles,
} from "lucide-react";
import type {
  LearnPathwayModule,
  LearnRoadmapPhase,
  LearnModuleStatus,
  RbpcLocale,
  LocalizedField,
} from "@/types/rbpc";
import { getRbpcCopy } from "@/lib/rbpc/copy";
import { cn } from "@/lib/utils";
import { RbpcCard } from "./RbpcCard";
import { RbpcButton } from "./RbpcButton";

export interface LearnRoadmapCardProps {
  /** Educational pathway module data conforming to LearnPathwayModule */
  module: LearnPathwayModule;
  /** Active UI locale (defaults to "vi") */
  locale?: RbpcLocale;
  /** Additional custom class names */
  className?: string;
  /** Optional click handler when user selects the module card */
  onSelectModule?: (module: LearnPathwayModule) => void;
  /** Custom destination href */
  href?: string;
}

/**
 * Safely resolves LocalizedField.
 */
function resolveLocalized(
  field: LocalizedField | string | undefined,
  locale: RbpcLocale = "vi",
  fallback = ""
): string {
  if (!field) return fallback;
  if (typeof field === "string") return field;
  if (locale === "en" && field.en && field.en.trim().length > 0) {
    return field.en;
  }
  return field.vi || field.en || fallback;
}

interface PhaseConfig {
  phaseLabelVi: string;
  phaseLabelEn: string;
  icon: React.ComponentType<{ className?: string }>;
  accentColor: string;
}

const PHASE_CONFIG: Record<LearnRoadmapPhase, PhaseConfig> = {
  P1_HERITAGE_BASELINE: {
    phaseLabelVi: "Chặng 1: Nền tảng Thư tịch Hoàng gia",
    phaseLabelEn: "Phase 1: Imperial Archival Foundation",
    icon: BookOpen,
    accentColor: "border-blue-700/30 bg-blue-500/10 text-blue-900 dark:text-blue-300",
  },
  P2_INTERACTIVE_3D: {
    phaseLabelVi: "Chặng 2: Tương tác 3D & Bản đúc nổi",
    phaseLabelEn: "Phase 2: Interactive 3D Metallurgy",
    icon: Box,
    accentColor: "border-teal-700/30 bg-teal-500/10 text-teal-900 dark:text-teal-300",
  },
  P3_MAKER_MASTERCLASS: {
    phaseLabelVi: "Chặng 3: Trải nghiệm Thực địa & Nghệ nhân",
    phaseLabelEn: "Phase 3: Living Maker Masterclass",
    icon: Hammer,
    accentColor: "border-amber-700/30 bg-amber-500/10 text-amber-900 dark:text-amber-300",
  },
  P4_ACCREDITED_CURRICULUM: {
    phaseLabelVi: "Chặng 4: Lộ trình Chứng chỉ Học tập (2027–2028)",
    phaseLabelEn: "Phase 4: Accredited Curriculum Roadmap",
    icon: GraduationCap,
    accentColor: "border-purple-700/30 bg-purple-500/10 text-purple-900 dark:text-purple-300",
  },
};

interface StatusConfig {
  labelVi: string;
  labelEn: string;
  badgeClass: string;
}

const STATUS_CONFIG: Record<LearnModuleStatus, StatusConfig> = {
  available_in_repo: {
    labelVi: "Có sẵn trong hệ thống",
    labelEn: "Available in Repository",
    badgeClass: "border-emerald-700/30 bg-emerald-500/10 text-emerald-900 dark:text-emerald-300",
  },
  prototype: {
    labelVi: "Bản mẫu thử nghiệm",
    labelEn: "Interactive Prototype",
    badgeClass: "border-amber-700/30 bg-amber-500/10 text-amber-900 dark:text-amber-300",
  },
  roadmap_phase_2: {
    labelVi: "Lộ trình 2027–2028",
    labelEn: "Roadmap 2027–2028",
    badgeClass: "border-stone-300 bg-stone-100 text-stone-700 dark:border-stone-700 dark:bg-stone-800 dark:text-stone-300",
  },
};

function formatAudience(
  audience: "visitor" | "student" | "educator",
  locale: RbpcLocale
): string {
  switch (audience) {
    case "visitor":
      return locale === "vi" ? "Khách tham quan" : "Visitor";
    case "student":
      return locale === "vi" ? "Học sinh & Sinh viên" : "Student";
    case "educator":
      return locale === "vi" ? "Nhà giáo dục" : "Educator";
    default:
      return audience;
  }
}

/**
 * LearnRoadmapCard Component
 *
 * Implements Master Spec §7.1, §7.2 & CREATE_LEARN_SPEC.md requirements:
 * 1. Educational bridge connecting historical research and Cửu Đỉnh 3D lessons to future roadmap
 * 2. 4-Phase taxonomy: Baseline Archive -> Interactive 3D -> Living Masterclass -> Accredited Curriculum
 * 3. Module availability status badges (available_in_repo, prototype, roadmap_phase_2)
 * 4. Technical metadata: historical period, source citations count, estimated duration
 * 5. Direct links to Cửu Đỉnh 3D model viewer and living artisan profiles
 */
export function LearnRoadmapCard({
  module,
  locale = "vi",
  className,
  onSelectModule,
  href,
}: LearnRoadmapCardProps) {
  const copy = getRbpcCopy(locale);

  const phase = PHASE_CONFIG[module.roadmapPhase] || PHASE_CONFIG.P1_HERITAGE_BASELINE;
  const PhaseIcon = phase.icon;
  const phaseLabel = locale === "vi" ? phase.phaseLabelVi : phase.phaseLabelEn;

  const status = STATUS_CONFIG[module.status] || STATUS_CONFIG.available_in_repo;
  const statusLabel = locale === "vi" ? status.labelVi : status.labelEn;

  const titleText = resolveLocalized(module.title, locale);
  const descriptionText = resolveLocalized(module.description, locale);
  const audienceLabel = formatAudience(module.targetAudience, locale);

  // Destination Link calculation
  let defaultHref = `/learn/${module.slug}`;
  if (module.linked3DArtefactSlug && module.status === "available_in_repo") {
    defaultHref = `/cuu-dinh/${module.linked3DArtefactSlug}`;
  }
  const destinationHref = href || defaultHref;

  const handleCardClick = (e: React.MouseEvent) => {
    if (onSelectModule) {
      e.preventDefault();
      onSelectModule(module);
    }
  };

  // CTA label determination
  let ctaText = locale === "vi" ? "Bắt đầu bài học" : "Start Learning";
  if (module.linked3DArtefactSlug && module.status === "available_in_repo") {
    ctaText = locale === "vi" ? "Khám phá chi tiết 3D" : "Explore 3D Artefact";
  } else if (module.status === "prototype") {
    ctaText = locale === "vi" ? "Xem bản mẫu tương tác" : "View Interactive Prototype";
  } else if (module.status === "roadmap_phase_2") {
    ctaText = locale === "vi" ? "Xem đề án học tập" : "View Curriculum Proposal";
  }

  return (
    <article
      className={cn(
        "group relative flex flex-col justify-between overflow-hidden rounded-2xl border border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] shadow-[var(--rbpc-shadow-sm)] transition-all duration-300 hover:border-[var(--rbpc-primary-border)] hover:shadow-[var(--rbpc-shadow-md)]",
        className
      )}
    >
      {/* =====================================================================
          1. Header & Phase Taxonomy Badges
          ===================================================================== */}
      <div className="p-6">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
          {/* Phase Badge */}
          <span
            className={cn(
              "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold shadow-xs",
              phase.accentColor
            )}
          >
            <PhaseIcon className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            <span className="line-clamp-1">{phaseLabel}</span>
          </span>

          {/* Module Availability Status Badge */}
          <span
            className={cn(
              "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-medium",
              status.badgeClass
            )}
          >
            {module.status === "available_in_repo" && (
              <CheckCircle2 className="h-3 w-3 text-emerald-600" aria-hidden="true" />
            )}
            {module.status === "prototype" && (
              <Sparkles className="h-3 w-3 text-amber-600" aria-hidden="true" />
            )}
            {module.status === "roadmap_phase_2" && (
              <Calendar className="h-3 w-3 text-stone-500" aria-hidden="true" />
            )}
            <span>{statusLabel}</span>
          </span>
        </div>

        {/* Module Title */}
        <Link
          href={destinationHref}
          onClick={handleCardClick}
          className="group/title block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus)] rounded-sm"
        >
          <h3 className="font-serif text-xl sm:text-2xl font-bold tracking-tight text-[var(--rbpc-ink)] leading-snug transition-colors group-hover/title:text-[var(--rbpc-primary)]">
            {titleText}
          </h3>
        </Link>

        {/* Historical Period & Target Audience Meta Chips */}
        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-[var(--rbpc-muted)]">
          {module.historicalPeriod && (
            <span className="inline-flex items-center gap-1 rounded-md bg-[var(--rbpc-bg)] px-2 py-0.5 font-medium border border-[var(--rbpc-divider-subtle)]">
              <Clock className="h-3 w-3 text-[var(--rbpc-primary)]" aria-hidden="true" />
              <span>{module.historicalPeriod}</span>
            </span>
          )}

          <span className="inline-flex items-center gap-1 rounded-md bg-[var(--rbpc-bg)] px-2 py-0.5 font-medium border border-[var(--rbpc-divider-subtle)]">
            <GraduationCap className="h-3 w-3 text-[var(--rbpc-highlight)]" aria-hidden="true" />
            <span>{audienceLabel}</span>
          </span>

          {module.estimatedMinutes > 0 && (
            <span className="font-mono text-[11px]">
              {module.estimatedMinutes} {locale === "vi" ? "phút" : "mins"}
            </span>
          )}
        </div>

        {/* Short Narrative Description */}
        {descriptionText && (
          <p className="mt-3.5 text-sm text-[var(--rbpc-ink-subtle)] leading-[var(--rbpc-lh-body)] line-clamp-3">
            {descriptionText}
          </p>
        )}

        {/* Learning Objectives Preview (if present) */}
        {module.learningObjectives && module.learningObjectives.length > 0 && (
          <div className="mt-4 pt-3 border-t border-[var(--rbpc-divider-subtle)]">
            <span className="block text-[11px] font-semibold uppercase tracking-wider text-[var(--rbpc-muted)] mb-1.5">
              {locale === "vi" ? "Mục tiêu bài học:" : "Key Learning Objectives:"}
            </span>
            <ul className="space-y-1 text-xs text-[var(--rbpc-ink-subtle)]">
              {module.learningObjectives.slice(0, 2).map((obj, idx) => (
                <li key={idx} className="flex items-start gap-1.5">
                  <span className="text-[var(--rbpc-primary)] font-bold shrink-0 mt-0.5">•</span>
                  <span className="line-clamp-1">{resolveLocalized(obj, locale)}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Bridges & Linkages (Cửu Đỉnh 3D Artefact or Artisan - Min 44px Touch Targets) */}
        <div className="mt-4 flex flex-wrap gap-2">
          {module.linked3DArtefactSlug && (
            <Link
              href={`/cuu-dinh/${module.linked3DArtefactSlug}`}
              className="inline-flex min-h-[44px] items-center gap-1.5 rounded-lg border border-[var(--rbpc-primary-border)] bg-[var(--rbpc-primary-subtle)] px-3 py-2 text-xs font-semibold text-[var(--rbpc-primary)] hover:bg-[var(--rbpc-primary)] hover:text-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2"
              title={locale === "vi" ? "Mở mô hình 3D Cửu Đỉnh" : "Open 3D Artefact Model"}
            >
              <Box className="h-3.5 w-3.5" aria-hidden="true" />
              <span>
                {locale === "vi"
                  ? `Mô hình 3D: ${module.linked3DArtefactSlug}`
                  : `3D Artefact: ${module.linked3DArtefactSlug}`}
              </span>
            </Link>
          )}

          {module.linkedCreatorSlug && (
            <Link
              href={`/people/${module.linkedCreatorSlug}`}
              className="inline-flex min-h-[44px] items-center gap-1.5 rounded-lg border border-[var(--rbpc-highlight-border)] bg-[var(--rbpc-highlight-subtle)] px-3 py-2 text-xs font-semibold text-[var(--rbpc-highlight)] hover:bg-[var(--rbpc-highlight)] hover:text-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2"
              title={locale === "vi" ? "Xem hồ sơ nghệ nhân" : "View Artisan Profile"}
            >
              <Hammer className="h-3.5 w-3.5" aria-hidden="true" />
              <span>
                {locale === "vi"
                  ? `Nghệ nhân: ${module.linkedCreatorSlug}`
                  : `Maker: ${module.linkedCreatorSlug}`}
              </span>
            </Link>
          )}
        </div>
      </div>

      {/* =====================================================================
          2. Citations Metadata & Action CTA
          ===================================================================== */}
      <div className="border-t border-[var(--rbpc-divider)] bg-[var(--rbpc-surface)] p-6 pt-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Source Citations Count */}
        <div className="flex items-center gap-1.5 text-xs text-[var(--rbpc-muted)]">
          <Library className="h-4 w-4 text-[var(--rbpc-primary)]" aria-hidden="true" />
          <span>
            {locale === "vi"
              ? `${module.sourceCitationsCount} nguồn thư tịch đối chiếu`
              : `${module.sourceCitationsCount} verified sources`}
          </span>
        </div>

        {/* Action Button */}
        <RbpcButton
          asChild
          variant={module.status === "available_in_repo" ? "primary" : "secondary"}
          size="md"
          className="w-full sm:w-auto"
        >
          <Link href={destinationHref} onClick={handleCardClick}>
            <span>{ctaText}</span>
            <ChevronRight className="h-4 w-4 transition-transform group-hover:translate-x-1" aria-hidden="true" />
          </Link>
        </RbpcButton>
      </div>
    </article>
  );
}

LearnRoadmapCard.displayName = "LearnRoadmapCard";
