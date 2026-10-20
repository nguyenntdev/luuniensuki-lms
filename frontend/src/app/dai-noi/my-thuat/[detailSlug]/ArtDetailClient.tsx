"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import {
  ArrowLeft,
  BookOpen,
  Calendar,
  Check,
  ChevronRight,
  ExternalLink,
  Eye,
  GraduationCap,
  History,
  Layers,
  MapPin,
  Maximize2,
  Printer,
  Share2,
  Sparkles,
} from "lucide-react";

import ImperialHeader from "@/components/imperial/shell/ImperialHeader";
import { ArtDetailCard } from "@/components/imperial/art-detail/ArtDetailCard";
import ImperialAiAssistant from "@/components/imperial/ai/ImperialAiAssistant";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { STORY_TYPE_METADATA, type ImperialArtDetail } from "@/lib/imperial/v51-types";

interface ArtDetailClientProps {
  detail: ImperialArtDetail;
  relatedDetails?: ImperialArtDetail[];
}

export default function ArtDetailClient({
  detail,
  relatedDetails = [],
}: ArtDetailClientProps) {
  const [copiedLink, setCopiedLink] = useState(false);
  const storyMeta = STORY_TYPE_METADATA[detail.story_type] || STORY_TYPE_METADATA.documented_event;

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
        {/* Breadcrumb & Action Toolbar */}
        <div className="border-b border-border/60 bg-muted/30">
          <div className="mx-auto flex h-12 max-w-6xl items-center justify-between px-4 sm:px-6">
            {/* Breadcrumb */}
            <nav
              aria-label="Breadcrumb"
              className="flex items-center space-x-1.5 text-xs text-muted-foreground truncate"
            >
              <Link
                href="/dai-noi"
                className="hover:text-foreground transition-colors"
              >
                Đại Nội Huế
              </Link>
              <ChevronRight className="w-3.5 h-3.5 shrink-0" />
              {detail.site_slug ? (
                <Link
                  href={`/dai-noi/cong-trinh/${detail.site_slug}`}
                  className="hover:text-foreground transition-colors truncate max-w-[120px] sm:max-w-xs"
                >
                  {detail.site_name_vi || "Hồ sơ công trình"}
                </Link>
              ) : (
                <span>Công trình</span>
              )}
              <ChevronRight className="w-3.5 h-3.5 shrink-0" />
              <span className="font-medium text-foreground truncate max-w-[150px] sm:max-w-sm">
                {detail.title}
              </span>
            </nav>

            {/* Actions */}
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handlePrint}
                className="h-8 text-xs gap-1.5 text-muted-foreground hover:text-foreground hidden sm:flex"
              >
                <Printer className="h-3.5 w-3.5" />
                In tư liệu
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

              {detail.site_slug && (
                <Link href={`/dai-noi/cong-trinh/${detail.site_slug}`}>
                  <Button size="sm" variant="secondary" className="h-8 text-xs gap-1.5">
                    <ArrowLeft className="h-3.5 w-3.5" />
                    Về công trình
                  </Button>
                </Link>
              )}
            </div>
          </div>
        </div>

        {/* Content Container */}
        <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 space-y-8">
          {/* Monument Context Header Banner */}
          <div className="rounded-xl border border-border/70 bg-card p-5 sm:p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 flex-wrap">
                <Badge variant="outline" className={`text-xs ${storyMeta.badgeColor}`}>
                  <Sparkles className="w-3 h-3 mr-1" />
                  {storyMeta.label}
                </Badge>
                {detail.site_name_vi && (
                  <Badge variant="secondary" className="text-xs">
                    Vị trí: {detail.site_name_vi}
                  </Badge>
                )}
              </div>
              <h1 className="text-2xl sm:text-3xl font-serif font-bold text-foreground tracking-tight">
                {detail.title}
              </h1>
              {detail.motif && (
                <p className="text-xs sm:text-sm text-muted-foreground">
                  Đồ án họa tiết: <span className="font-medium text-foreground">{detail.motif}</span>
                  {detail.material && ` • Chất liệu: ${detail.material}`}
                </p>
              )}
            </div>

            {detail.site_slug && (
              <div className="flex items-center gap-2 shrink-0">
                <Link href={`/dai-noi?focus=${detail.site_slug}`}>
                  <Button variant="outline" size="sm" className="h-9 text-xs gap-1.5">
                    <MapPin className="h-3.5 w-3.5 text-primary" />
                    Xem trên không ảnh
                  </Button>
                </Link>
              </div>
            )}
          </div>

          {/* High Resolution Image Feature (if image_url is available) */}
          {detail.image_url && (
            <div className="relative rounded-xl overflow-hidden border border-border/80 bg-black aspect-[16/9] max-h-[460px] shadow-md">
              <img
                src={detail.image_url}
                alt={detail.title}
                className="w-full h-full object-cover object-center"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-black/20 pointer-events-none" />
              <div className="absolute bottom-4 left-4 right-4 flex items-end justify-between text-white">
                <div>
                  <p className="font-serif font-semibold text-base sm:text-lg">{detail.title}</p>
                  <p className="text-xs text-white/80">{detail.site_name_vi || "Đại Nội Huế"}</p>
                </div>
              </div>
            </div>
          )}

          {/* Detailed 6-section Pedagogy & Story Card */}
          <ArtDetailCard detail={detail} showDeepLinkButton={false} />

          {/* Related Art Details of the Monument */}
          {relatedDetails.length > 0 && (
            <div className="pt-6 border-t border-border/60 space-y-4">
              <h3 className="font-serif font-bold text-lg text-foreground flex items-center gap-2">
                <Layers className="w-4 h-4 text-primary" />
                Các chi tiết mỹ thuật khác cùng công trình
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                {relatedDetails.map((rel) => (
                  <Link
                    key={rel.id}
                    href={`/dai-noi/my-thuat/${rel.slug}`}
                    className="group"
                  >
                    <Card className="h-full border-border/60 hover:border-primary/50 transition-colors bg-card/60">
                      <CardContent className="p-4 space-y-2">
                        <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                          <span className="capitalize">{rel.kind}</span>
                          <span>•</span>
                          <span className="truncate">{rel.site_name_vi}</span>
                        </div>
                        <h4 className="font-serif font-semibold text-sm text-foreground group-hover:text-primary transition-colors line-clamp-2">
                          {rel.title}
                        </h4>
                        {rel.motif && (
                          <p className="text-xs text-muted-foreground line-clamp-1">
                            {rel.motif}
                          </p>
                        )}
                      </CardContent>
                    </Card>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border/60 bg-card/50 py-8 text-center text-xs text-muted-foreground mt-12">
        <div className="mx-auto max-w-6xl px-4 space-y-2">
          <p className="font-semibold text-foreground/80">
            Lưu Niên — Khảo cứu mỹ thuật & điển tích Đại Nội Huế
          </p>
          <p>
            Dữ liệu đối chiếu từ Đại Nam Thực Lục Chính Biên & Khâm Định Đại Nam Hội Điển Sự Lệ
          </p>
          <div className="pt-2 flex justify-center gap-4 text-primary">
            <Link href="/dai-noi" className="hover:underline">Bản đồ không ảnh</Link>
            <span>•</span>
            <Link href="/dai-noi/nguon" className="hover:underline">Mục lục nguồn sử liệu</Link>
          </div>
        </div>
      </footer>

      {/* Scope-Locked Cultural AI Assistant */}
      <ImperialAiAssistant
        contextMonumentSlug={detail.site_slug || undefined}
        contextMonumentName={detail.site_name_vi || undefined}
      />
    </div>
  );
}
