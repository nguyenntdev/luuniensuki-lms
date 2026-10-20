"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  BookOpen,
  Calendar,
  Camera,
  Compass,
  FileText,
  GraduationCap,
  History,
  Layers,
  MapPin,
  Share2,
  Printer,
  Check,
} from "lucide-react";

import ImperialHeader from "@/components/imperial/shell/ImperialHeader";
import MonumentHero from "@/components/imperial/dossier/MonumentHero";
import GuidingQuestionCard from "@/components/imperial/dossier/GuidingQuestionCard";
import TimelineStatusSection from "@/components/imperial/dossier/TimelineStatusSection";
import HistoricalImagerySection from "@/components/imperial/dossier/HistoricalImagerySection";
import ClaimsEvidenceList from "@/components/imperial/dossier/ClaimsEvidenceList";
import PedagogicalTaskCard from "@/components/imperial/dossier/PedagogicalTaskCard";
import SpatialConnectionsNav from "@/components/imperial/dossier/SpatialConnectionsNav";
import ImperialAiAssistant from "@/components/imperial/ai/ImperialAiAssistant";
import { MediaHotspotViewer } from "@/components/imperial/media/MediaHotspotViewer";
import { HeritageDetectiveWidget } from "@/components/imperial/detective/HeritageDetectiveWidget";
import { FALLBACK_CLUES } from "@/lib/imperial/v51-api";
import { Button } from "@/components/ui/button";
import type { SiteDossierData } from "@/lib/imperial/map-types";
import { fetchSiteLearningMedia } from "@/lib/imperial/v51-api";
import type { ImperialLearningMedia } from "@/lib/imperial/v51-types";

interface MonumentDossierClientProps {
  initialData: SiteDossierData;
  initialLearningMedia?: ImperialLearningMedia[];
}

export default function MonumentDossierClient({
  initialData,
  initialLearningMedia,
}: MonumentDossierClientProps) {
  const [data] = useState<SiteDossierData>(initialData);
  const {
    site,
    zone,
    timeline,
    imagery,
    claims,
    guiding_question,
    task,
    rubrics,
    connections,
    annotation,
  } = data;

  const [copiedLink, setCopiedLink] = useState(false);
  const [mediaList, setMediaList] = useState<ImperialLearningMedia[]>(
    initialLearningMedia || [],
  );
  const [activeMedia, setActiveMedia] = useState<ImperialLearningMedia | null>(
    initialLearningMedia?.[0] || null,
  );

  useEffect(() => {
    if ((!mediaList || mediaList.length === 0) && site.slug) {
      let isMounted = true;
      fetchSiteLearningMedia(site.slug).then((res) => {
        if (isMounted && res.length > 0) {
          setMediaList(res);
          setActiveMedia(res[0]);
        }
      });
      return () => {
        isMounted = false;
      };
    }
  }, [site.slug, mediaList]);

  const handleShare = () => {
    if (typeof window !== "undefined") {
      navigator.clipboard.writeText(window.location.href);
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2000);
    }
  };

  const handlePrint = () => {
    if (typeof window !== "undefined") {
      window.print();
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col selection:bg-primary/20 selection:text-primary">
      {/* Universal Imperial City Header */}
      <ImperialHeader />

      <main className="flex-1">
        {/* Sticky Sub-Header with Action Toolbar */}
        <div className="sticky top-14 z-30 border-b border-border/60 bg-background/95 backdrop-blur-md">
          <div className="mx-auto flex h-12 max-w-6xl items-center justify-between px-4 sm:px-6">
            <div className="flex items-center gap-2 truncate">
              <span className="font-display font-bold text-sm text-foreground truncate">
                {site.name_vi}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handlePrint}
                className="h-8 text-xs gap-1.5 text-muted-foreground hover:text-foreground hidden sm:flex"
              >
                <Printer className="h-3.5 w-3.5" />
                In hồ sơ
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={handleShare}
                className="h-8 text-xs gap-1.5"
              >
                {copiedLink ? (
                  <>
                    <Check className="h-3.5 w-3.5 text-emerald-600" />
                    Đã sao chép
                  </>
                ) : (
                  <>
                    <Share2 className="h-3.5 w-3.5" />
                    Chia sẻ
                  </>
                )}
              </Button>

              <Link href={`/dai-noi?focus=${site.slug}`}>
                <Button size="sm" className="h-8 text-xs gap-1.5">
                  <MapPin className="h-3.5 w-3.5" />
                  Xem trên bản đồ
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* 7-Section Pedagogical Monument Dossier */}
        <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 space-y-10">
          {/* Section 1: Monument Hero & Spatial Identity */}
          <MonumentHero
            site={site}
            zone={zone}
            annotation={annotation}
          />

          {/* Heritage Detective Clue Banner (SPEC V5.1) */}
          {(() => {
            const siteClue =
              FALLBACK_CLUES.find((c) => c.target_slug === site.slug) ||
              FALLBACK_CLUES[0];
            return (
              <HeritageDetectiveWidget
                clue={siteClue}
                currentSiteSlug={site.slug}
                currentSiteId={site.id}
              />
            );
          })()}

          {/* Section 2: Guiding Inquiry Question & Vetted Summary */}
          <GuidingQuestionCard
            question={guiding_question}
            historicalSummary={site.historical_summary}
            learningLevel={site.learning_level}
            monumentName={site.name_vi}
          />

          {/* Section 3: Timeline of Construction, Transformation & Restoration */}
          <TimelineStatusSection
            timeline={timeline}
            monumentName={site.name_vi}
          />

          {/* Section 4: Historical Imagery & Architectural Evidence */}
          <HistoricalImagerySection
            imagery={imagery}
            monumentName={site.name_vi}
          />

          {/* Section 4.5: Khám phá chi tiết & Điển tích mỹ thuật (V5.1 Media Hotspot Viewer) */}
          {activeMedia && (
            <section className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border/60 pb-3">
                <div>
                  <h2 className="text-xl sm:text-2xl font-serif font-bold text-foreground flex items-center gap-2">
                    <Layers className="w-5 h-5 text-primary" />
                    Khám phá chi tiết & Điển tích mỹ thuật
                  </h2>
                  <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
                    Quan sát trực quan 2D/360° với các điểm ghim UV và giải mã điển tích, triết lý cung đình
                  </p>
                </div>
              </div>

              <MediaHotspotViewer
                media={activeMedia}
                availableMediaList={mediaList}
                onSelectMedia={(m) => setActiveMedia(m)}
              />
            </section>
          )}

          {/* Section 5: Claims & Primary Source Citations */}
          <ClaimsEvidenceList
            claims={claims}
            monumentName={site.name_vi}
          />

          {/* Section 6: Pedagogical Task & Rubric Guidelines */}
          <PedagogicalTaskCard
            task={task}
            rubrics={rubrics}
            monumentName={site.name_vi}
            monumentSlug={site.slug}
            availableSources={site.primary_sources?.map((s) => ({ title: s.source_title, citation: s.citation }))}
          />

          {/* Section 7: Spatial Connections along Ceremonial Axis */}
          <SpatialConnectionsNav
            connections={connections}
            currentSiteName={site.name_vi}
          />
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border/60 bg-card/50 py-8 text-center text-xs text-muted-foreground">
        <div className="mx-auto max-w-6xl px-4 space-y-2">
          <p className="font-semibold text-foreground/80">
            Lưu Niên — Bản đồ học tập di sản Đại Nội Huế
          </p>
          <p>
            Dữ liệu lịch sử đối chiếu từ Quốc Sử Quán triều Nguyễn • Quần thể Di tích Cố đô Huế (UNESCO 1993)
          </p>
          <div className="pt-2 flex justify-center gap-4 text-primary">
            <Link href="/dai-noi" className="hover:underline">Bản đồ không ảnh</Link>
            <span>•</span>
            <Link href="/dai-noi/nguon" className="hover:underline">Mục lục nguồn & Quyền sử dụng</Link>
          </div>
        </div>
      </footer>

      {/* Scope-Locked Cultural AI Tutor Assistant Widget */}
      <ImperialAiAssistant
        contextMonumentSlug={site.slug}
        contextMonumentName={site.name_vi}
      />
    </div>
  );
}
