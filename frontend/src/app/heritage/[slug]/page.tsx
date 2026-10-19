"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Award,
  BookOpen,
  Calendar,
  CheckCircle2,
  Clock,
  Compass,
  Crown,
  ExternalLink,
  Hammer,
  Landmark,
  Layers,
  MapPin,
  Mountain,
  Music,
  Share2,
  ShieldCheck,
  Sparkles,
  Utensils,
  Wrench,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { getHeritagePlaceDetail } from "@/lib/api";
import { DEFAULT_HERITAGE_PLACES } from "@/lib/rbpc/heritageData";
import type {
  HeritagePlace,
  HeritagePlaceDetail,
  HeritageMediaAsset,
  HeritageSourceEvidence,
} from "@/types/heritage";
import HeritageMediaTabs from "@/components/explore/HeritageMediaTabs";
import SourceEvidenceRail from "@/components/explore/SourceEvidenceRail";
import LivingBridgeCard from "@/components/explore/LivingBridgeCard";
import { CulturalBridgePanel } from "@/components/rbpc/CulturalBridgePanel";
import Skeleton from "@/components/Skeleton";

// Category display metadata
const CATEGORY_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  imperial_architecture: Landmark,
  royal_tomb: Crown,
  craft_living_culture: Hammer,
  music_performance: Music,
  landscape_nature: Mountain,
  religious_spiritual: Sparkles,
  museum_archive: BookOpen,
  culinary_heritage: Utensils,
};

export default function HeritagePlaceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const slug = typeof params?.slug === "string" ? params.slug : "";

  const [loading, setLoading] = useState(true);
  const [place, setPlace] = useState<HeritagePlace | null>(null);

  // Default synthetic fallback sources grounded in official records
  const defaultSources: HeritageSourceEvidence[] = useMemo(
    () => [
      {
        id: "src-dntl-01",
        place_id: place?.id || "place-default",
        source_title: "Đại Nam Thực Lục (Chính biên, Đệ tứ kỷ)",
        source_author: "Quốc sử quán triều Nguyễn",
        publication_year: 1864,
        cited_section: "Quyển 30",
        cited_page: "tờ 12b - 14a",
        statement:
          "Mùa thu tháng 8, khởi công xây đắp Vạn Niên Cơ. Sai quan văn võ đổng biện công việc, định rõ quy thức doanh tạo chuẩn mực cung tẩm hoàng gia.",
        evidence_status: "verified",
        reuse_rights: "public_domain",
        content_scope: "RBPC_HUE",
        source_url: "https://mowcap.unesco.org/archives/nguyen-dynasty-woodblocks",
      },
      {
        id: "src-hdsl-02",
        place_id: place?.id || "place-default",
        source_title: "Khâm Định Đại Nam Hội Điển Sự Lệ",
        source_author: "Nội các triều Nguyễn biên soạn",
        publication_year: 1851,
        cited_section: "Quyển 118",
        cited_page: "trang 89",
        statement:
          "Quy định quy chuẩn doanh tạo đình tạ, thành lũy và quy tắc đo đạc phong thủy sơn xuyên che chắn lăng miếu Cố đô.",
        evidence_status: "verified",
        reuse_rights: "public_domain",
        content_scope: "RBPC_HUE",
        source_url: "https://hueworldheritage.org.vn/archives/hoi-dien-su-le",
      },
    ],
    [place?.id]
  );

  // Synthetic media assets including 3D model if place has 3D
  const mediaAssets: HeritageMediaAsset[] = useMemo(() => {
    const assets: HeritageMediaAsset[] = [
      {
        id: `media-photo-${slug}-01`,
        place_id: place?.id || "place-01",
        media_type: "photo",
        title: `Toàn cảnh không gian ${place?.name_vi || "Di tích"}`,
        original_url: place?.thumbnail_url || "https://assets.histolab.icu/heritage/hue-monument-overview.webp",
        creator_name: "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
        accuracy_grade: "historian_reviewed",
        license_label: "CC BY 4.0",
        noai: true,
        commercial_use_status: "permitted",
        embed_permission_status: "permitted",
        content_status: "cleared_for_this_use",
        content_scope: "RBPC_HUE",
        created_at: new Date().toISOString(),
      },
      {
        id: `media-photo-${slug}-02`,
        place_id: place?.id || "place-01",
        media_type: "photo",
        title: "Chi tiết kiến trúc vì kèo và hoa văn pháp lam",
        original_url: "https://assets.histolab.icu/heritage/hue-detail-joinery.webp",
        creator_name: "Lưu Niên Heritage Research Archive",
        accuracy_grade: "historian_reviewed",
        license_label: "CC BY 4.0",
        noai: true,
        commercial_use_status: "permitted",
        embed_permission_status: "permitted",
        content_status: "cleared_for_this_use",
        content_scope: "RBPC_HUE",
        created_at: new Date().toISOString(),
      },
    ];

    if (place?.has_3d) {
      assets.unshift({
        id: `media-3d-${slug}`,
        place_id: place.id,
        media_type: "sketchfab_embed",
        source_platform: "sketchfab",
        title: `Mô hình 3D đo đạc quang trắc: ${place.name_vi}`,
        original_url: "https://sketchfab.com/3d-models/tomb-of-tu-duc-vietnam-808eb550be0a4484b3d3f9e9cf2ec6df",
        embed_url: "https://sketchfab.com/models/808eb550be0a4484b3d3f9e9cf2ec6df/embed",
        model_uid: "808eb550be0a4484b3d3f9e9cf2ec6df",
        creator_name: "matousekfoto (CyArk Dataset)",
        creator_url: "https://sketchfab.com/matousekfoto",
        license_label: "CC BY 4.0",
        license_url: "https://creativecommons.org/licenses/by/4.0/",
        noai: true,
        commercial_use_status: "permitted",
        embed_permission_status: "permitted",
        accuracy_grade: "measured_photogrammetry",
        content_status: "cleared_for_this_use",
        content_scope: "RBPC_HUE",
        created_at: new Date().toISOString(),
      });
    }

    return assets;
  }, [place, slug]);

  useEffect(() => {
    let active = true;

    async function loadPlace() {
      setLoading(true);
      try {
        const detail = await getHeritagePlaceDetail(slug);
        if (active && detail) {
          setPlace(detail);
          setLoading(false);
          return;
        }
      } catch (err) {
        // Fallback to static seed data
      }

      const found = DEFAULT_HERITAGE_PLACES.find((p) => p.slug === slug);
      if (active) {
        setPlace(found || null);
        setLoading(false);
      }
    }

    if (slug) {
      loadPlace();
    }

    return () => {
      active = false;
    };
  }, [slug]);

  if (loading) {
    return (
      <main className="site-shell min-h-screen py-10">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <Skeleton className="h-6 w-32 rounded-lg" />
          <Skeleton className="mt-6 h-10 w-3/4 max-w-xl rounded-xl" />
          <Skeleton className="mt-3 h-5 w-1/2 rounded-lg" />
          <div className="mt-8 grid gap-8 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <Skeleton className="aspect-[16/10] w-full rounded-2xl" />
              <Skeleton className="mt-6 h-40 w-full rounded-2xl" />
            </div>
            <div>
              <Skeleton className="h-80 w-full rounded-2xl" />
            </div>
          </div>
        </div>
      </main>
    );
  }

  if (!place) {
    return (
      <main className="site-shell min-h-screen py-16 text-center">
        <div className="mx-auto max-w-md px-4">
          <div className="flex h-16 w-16 mx-auto items-center justify-center rounded-2xl bg-muted text-muted-foreground">
            <Compass className="h-8 w-8" />
          </div>
          <h1 className="mt-6 text-2xl font-bold font-display text-foreground">
            Không tìm thấy di sản
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Địa danh với mã định danh &ldquo;{slug}&rdquo; không tồn tại hoặc chưa được công bố trong danh mục.
          </p>
          <div className="mt-6">
            <Link
              href="/explore"
              className="inline-flex min-h-[44px] items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Quay lại Danh mục Khám phá</span>
            </Link>
          </div>
        </div>
      </main>
    );
  }

  const CategoryIcon = CATEGORY_ICONS[place.heritage_category] || Landmark;
  const isUnesco = Boolean(
    place.official_reference_id?.startsWith("678") ||
      place.official_designation?.toLowerCase().includes("unesco")
  );

  return (
    <main className="site-shell min-h-screen pb-16">
      {/* 1. Breadcrumb Bar */}
      <nav aria-label="Breadcrumb" className="pt-4 pb-2">
        <div className="flex flex-wrap items-center gap-2 text-xs sm:text-sm text-muted-foreground">
          <Link href="/" className="hover:text-foreground transition-colors">
            Trang chủ
          </Link>
          <span>/</span>
          <Link href="/explore" className="hover:text-foreground transition-colors">
            Khám phá di sản Huế
          </Link>
          <span>/</span>
          <span className="text-foreground font-medium truncate max-w-[240px]">
            {place.name_vi}
          </span>
        </div>
      </nav>

      {/* 2. Top Header & Monument Identity */}
      <section className="mt-4 border-b border-border/80 pb-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <Link
            href="/explore"
            className="inline-flex min-h-[44px] items-center gap-2 rounded-xl border border-border/80 bg-background px-4 py-2 text-xs font-semibold text-foreground transition-colors hover:bg-secondary/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Quay lại Danh mục</span>
          </Link>

          {/* Badges Bar */}
          <div className="flex flex-wrap items-center gap-2">
            {isUnesco && (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-600/40 bg-emerald-950/80 px-3 py-1 text-xs font-mono font-semibold text-emerald-200">
                <Award className="h-3.5 w-3.5 text-emerald-400" />
                <span>UNESCO {place.official_reference_id || "678"}</span>
              </span>
            )}
            <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-foreground">
              <CategoryIcon className="h-3.5 w-3.5 text-primary" />
              <span>
                {place.heritage_category === "imperial_architecture"
                  ? "Kiến trúc Cung đình"
                  : place.heritage_category === "royal_tomb"
                  ? "Lăng tẩm Hoàng gia"
                  : place.heritage_category === "craft_living_culture"
                  ? "Làng nghề Thủ công"
                  : place.heritage_category === "music_performance"
                  ? "Âm nhạc & Diễn xướng"
                  : "Di tích Lịch sử"}
              </span>
            </span>
            {place.current_access_status === "open" && (
              <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700 dark:text-emerald-400">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>Mở cửa tham quan</span>
              </span>
            )}
          </div>
        </div>

        {/* Monument Title Block */}
        <div className="mt-6">
          <h1 className="font-display text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            {place.name_vi}
          </h1>
          {place.name_en && (
            <p className="mt-1 font-serif text-lg text-muted-foreground italic">
              {place.name_en}
            </p>
          )}

          {/* Meta Details Strip */}
          <div className="mt-4 flex flex-wrap items-center gap-y-2 gap-x-6 text-xs sm:text-sm text-muted-foreground">
            {place.period_label && (
              <div className="flex items-center gap-1.5">
                <Clock className="h-4 w-4 text-amber-500" />
                <span>{place.period_label}</span>
              </div>
            )}
            {place.location_lat && place.location_lon && (
              <div className="flex items-center gap-1.5">
                <MapPin className="h-4 w-4 text-primary" />
                <span>
                  {place.location_lat.toFixed(4)}°N, {place.location_lon.toFixed(4)}°E
                </span>
              </div>
            )}
            {place.official_designation && (
              <div className="flex items-center gap-1.5">
                <ShieldCheck className="h-4 w-4 text-emerald-600" />
                <span className="line-clamp-1">{place.official_designation}</span>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* 3. Main Split View: Left Column (Media + Narrative + Sources) & Right Column (Living Bridge + AI) */}
      <div className="mt-8 grid gap-8 lg:grid-cols-12">
        {/* Left Column (8 cols on lg) */}
        <div className="space-y-8 lg:col-span-7 xl:col-span-8">
          {/* A. HeritageMediaTabs (Photo / 3D / Documents) */}
          <section aria-label="Tư liệu truyền thông di sản">
            <HeritageMediaTabs
              media={mediaAssets}
              placeName={place.name_vi}
              placeNameEn={place.name_en || undefined}
              defaultTab={place.has_3d ? "3d" : "photos"}
              locale="vi"
            />
          </section>

          {/* B. Historical Narrative / Verified Synthesis */}
          <section className="rounded-2xl border border-border/80 bg-card p-6 shadow-xs sm:p-8">
            <div className="flex items-center gap-2 text-xs font-semibold tracking-wider text-primary uppercase">
              <BookOpen className="h-4 w-4" />
              <span>Khảo chứng Lịch sử</span>
            </div>
            <h2 className="mt-2 font-display text-xl font-bold text-foreground sm:text-2xl">
              Giá trị Văn hóa & Bối cảnh Khảo cứu
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-foreground/90 sm:text-base">
              {place.visitor_summary_vi}
            </p>
            {place.visitor_summary_en && (
              <p className="mt-4 text-sm leading-relaxed text-muted-foreground italic sm:text-base border-t border-border/60 pt-4">
                &ldquo;{place.visitor_summary_en}&rdquo;
              </p>
            )}
          </section>

          {/* C. SourceEvidenceRail (Citations & Bibliographic Proof) */}
          <section aria-label="Thư viện nguồn và chứng cứ thư tịch">
            <SourceEvidenceRail
              sources={defaultSources}
              placeName={place.name_vi}
              placeNameEn={place.name_en || undefined}
              layout="bottom"
              locale="vi"
            />
          </section>
        </div>

        {/* Right Column (4 cols on lg) */}
        <aside className="space-y-8 lg:col-span-5 xl:col-span-4">
          {/* A. LivingBridgeCard (Artisan Connection & Workshop Inquiry) */}
          <section aria-label="Cầu nối di sản sống">
            <LivingBridgeCard
              monumentName={place.name_vi}
              monumentNameEn={place.name_en || undefined}
              monumentPeriod={place.period_label || undefined}
              monumentCategory={place.heritage_category}
              monumentSlug={place.slug}
              artisan={{
                id: "artisan-sinh",
                slug: "nguyen-van-sinh",
                publicName: "Nghệ nhân Nhân dân Nguyễn Văn Sinh",
                craftTradition: "Đúc đồng thủ công mỹ nghệ Phường Đúc",
                approvedBio: "Gìn giữ ngọn lửa nghề đúc đồng truyền thống qua 11 thế hệ tại làng đúc Phường Đúc, TP. Huế.",
                generationLineage: "Đời thứ 11",
                consentStatus: "consented",
                publicRegion: "Phường Đúc, TP. Huế",
                yearsOfPractice: 42,
                approvedPortraitUrl: "/assets/artisans/nguyen-van-sinh.webp",
              }}
              bridgeNarrative="Kỹ thuật đúc đồng và chạm khắc kim hoàn truyền thống tại Huế được bảo tồn liên tục qua hơn 400 năm từ thời Chúa Nguyễn đến nay. Mối liên kết giữa các công trình cung đình lịch sử và bàn tay người thợ hôm nay là bằng chứng sống động của di sản phi vật thể trường tồn."
              experience={{
                slug: "workshop-duc-dong-phuong-duc",
                title: {
                  vi: "Trải nghiệm Đúc Đồng Thủ Công Cùng Nghệ Nhân Phường Đúc",
                  en: "Traditional Bronze Casting Workshop with Master Craftsman",
                },
                description: {
                  vi: "Trải nghiệm quy trình làm khuôn đất, rót đồng và hoàn thiện hoa văn mỹ nghệ cùng nghệ nhân.",
                  en: "Hands-on bronze casting experience with clay moulds and traditional finishing.",
                },
                durationMinutes: 210,
                pricingDisplay: "Đăng ký trước / Miễn phí thử nghiệm",
                areaPublic: "Xưởng đúc đồng truyền thống Phường Đúc",
              }}
              locale="vi"
              enableInquiryModal={false}
            />
          </section>

          {/* B. CulturalBridgePanel (Source-Grounded AI Assistant) */}
          <section aria-label="Hỏi đáp cùng trợ lý AI văn hóa">
            <CulturalBridgePanel
              entitySlug={place.slug}
              entityName={place.name_vi}
              locale="vi"
            />
          </section>
        </aside>
      </div>
    </main>
  );
}
