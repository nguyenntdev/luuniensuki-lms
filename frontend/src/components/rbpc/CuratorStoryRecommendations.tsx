"use client";

import React, { useState, useEffect } from "react";
import { Sparkles, ArrowRight, ShieldCheck, Compass, Store } from "lucide-react";
import { RbpcCard, RbpcCardHeader, RbpcCardTitle, RbpcCardContent } from "./RbpcCard";
import { RbpcButton } from "./RbpcButton";
import { getRbpcCopy, type RbpcSupportedVisitorLocale } from "@/lib/rbpc/copy";
import { fetchCuratorStoryRecommendationsApi } from "@/lib/rbpc/inquiries";
import type { CuratorStoryRecommendation } from "@/types/rbpc";

export interface CuratorStoryRecommendationsProps {
  storySlug?: string;
  objectSlug?: string;
  locale?: RbpcSupportedVisitorLocale | "vi" | "en";
  className?: string;
  onSelectStory?: (storySlug: string) => void;
  onExploreWorkshop?: (experienceSlug: string) => void;
  initialRecommendations?: CuratorStoryRecommendation[];
  maxDisplay?: number;
}

export function CuratorStoryRecommendations({
  storySlug,
  objectSlug,
  locale = "vi",
  className = "",
  onSelectStory,
  onExploreWorkshop,
  initialRecommendations,
  maxDisplay = 3,
}: CuratorStoryRecommendationsProps) {
  const [recommendations, setRecommendations] = useState<CuratorStoryRecommendation[]>(
    initialRecommendations || []
  );
  const [loading, setLoading] = useState(false);
  const isEn = locale === "en";

  useEffect(() => {
    if (initialRecommendations && initialRecommendations.length > 0) {
      setRecommendations(initialRecommendations);
      return;
    }

    if (!storySlug) return;

    let cancelled = false;
    async function loadRecs() {
      setLoading(true);
      try {
        const res = await fetchCuratorStoryRecommendationsApi(storySlug!, locale, maxDisplay);
        if (!cancelled && res?.recommendations) {
          setRecommendations(res.recommendations);
        }
      } catch (err) {
        if (!cancelled) {
          // Fail-closed: hide recommendations rather than showing unverified content
          setRecommendations([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadRecs();
    return () => {
      cancelled = true;
    };
  }, [storySlug, locale, maxDisplay, initialRecommendations]);

  // Negative abuse: if no verified recommendations exist, return null
  if (!recommendations || recommendations.length === 0) {
    return null;
  }

  const itemsToRender = recommendations.slice(0, maxDisplay);

  return (
    <RbpcCard
      className={`curator-story-recommendations border-line bg-surface/50 ${className}`}
      data-testid="curator-story-recommendations"
    >
      <RbpcCardHeader className="border-b border-line/60 pb-3">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Compass className="h-4 w-4" />
            </span>
            <div>
              <RbpcCardTitle className="text-sm font-serif font-bold text-ink sm:text-base">
                {isEn ? "Curator-Controlled Story Recommendations" : "Gợi ý Hành trình Giám tuyển"}
              </RbpcCardTitle>
              <p className="text-[11px] text-muted">
                {isEn
                  ? "Rule-based object & craft workshop linkages verified from archival sources"
                  : "Mối liên kết hiện vật & xưởng nghề truyền thống đã qua thẩm định"}
              </p>
            </div>
          </div>
          <span className="inline-flex items-center gap-1 rounded border border-primary/20 bg-primary/5 px-2 py-0.5 text-[10px] font-semibold text-primary uppercase tracking-wider">
            <ShieldCheck className="h-3 w-3" />
            {isEn ? "Verified Heritage Link" : "Liên kết thẩm định"}
          </span>
        </div>
      </RbpcCardHeader>

      <RbpcCardContent className="space-y-4 pt-4">
        <div className="grid gap-3 sm:grid-cols-1">
          {itemsToRender.map((rec, idx) => (
            <div
              key={rec.story_slug || idx}
              className="rounded-lg border border-line bg-white p-3.5 shadow-xs transition-colors hover:border-primary/40"
              data-testid={`curator-rec-item-${rec.story_slug}`}
            >
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                <div className="space-y-1.5 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-rice px-2 py-0.5 text-[10px] font-semibold text-ink/80">
                      {rec.category || "Di sản Huế"}
                    </span>
                    <span className="text-[11px] text-muted">
                      {rec.reading_time_minutes} {isEn ? "min read" : "phút đọc"}
                    </span>
                  </div>

                  <h4 className="font-serif text-sm font-bold text-ink">
                    <button
                      type="button"
                      onClick={() => onSelectStory && onSelectStory(rec.story_slug)}
                      className="text-left hover:text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] rounded-xs"
                    >
                      {rec.title}
                    </button>
                  </h4>

                  <p className="text-xs text-ink/80 line-clamp-2 leading-relaxed">
                    {rec.approved_summary || rec.intro}
                  </p>

                  {/* Justification note */}
                  <p className="text-[11px] italic text-muted/90 border-l-2 border-primary/40 pl-2 mt-1">
                    {rec.historical_justification}
                  </p>

                  {/* Workshop Linkage with Artisan Dignity Note */}
                  {rec.workshop && (
                    <div className="mt-2.5 rounded-md border border-primary/20 bg-primary/5 p-2.5">
                      <div className="flex items-center gap-1.5 text-primary text-xs font-semibold">
                        <Store className="h-3.5 w-3.5" />
                        <span>{rec.workshop.experience_title}</span>
                      </div>
                      <p className="text-[11px] text-ink/90 mt-0.5">
                        {isEn ? "Master Artisan:" : "Nghệ nhân:"}{" "}
                        <span className="font-medium">{rec.workshop.creator_name}</span>{" "}
                        ({rec.workshop.craft_tradition})
                      </p>
                      <p className="text-[10px] text-muted mt-1 italic">
                        * {rec.workshop.artisan_dignity_note}
                      </p>
                      {onExploreWorkshop && (
                        <div className="mt-2">
                          <RbpcButton
                            variant="secondary"
                            size="sm"
                            className="min-h-[36px] text-xs"
                            onClick={() => onExploreWorkshop(rec.workshop!.experience_slug)}
                          >
                            <span className="flex items-center gap-1">
                              {isEn ? "View Workshop" : "Xem xưởng nghề"}
                              <ArrowRight className="h-3 w-3" />
                            </span>
                          </RbpcButton>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className="shrink-0 flex items-center sm:self-center">
                  <RbpcButton
                    variant="primary"
                    size="sm"
                    className="min-h-[44px] text-xs w-full sm:w-auto"
                    onClick={() => onSelectStory && onSelectStory(rec.story_slug)}
                  >
                    <span className="flex items-center gap-1">
                      {isEn ? "Read Story" : "Khám phá truyện"}
                      <ArrowRight className="h-3 w-3" />
                    </span>
                  </RbpcButton>
                </div>
              </div>
            </div>
          ))}
        </div>
      </RbpcCardContent>
    </RbpcCard>
  );
}

CuratorStoryRecommendations.displayName = "CuratorStoryRecommendations";
