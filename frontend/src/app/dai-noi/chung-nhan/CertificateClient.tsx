"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  Award,
  ChevronLeft,
  Copy,
  Printer,
  Sparkles,
  ShieldCheck,
  Edit3,
  Share2,
  CheckCircle2,
  ExternalLink,
  Lock,
  Download,
  Scroll,
} from "lucide-react";
import toast from "react-hot-toast";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuthStore } from "@/stores/authStore";

import { CertificateFrame } from "@/components/imperial/certificate/CertificateFrame";
import { OfficialProjectSeal } from "@/components/imperial/certificate/OfficialProjectSeal";
import { VerificationQr } from "@/components/imperial/certificate/VerificationQr";
import { ZoneScoreBreakdown } from "@/components/imperial/certificate/ZoneScoreBreakdown";
import { CertificateCustomizeModal } from "@/components/imperial/certificate/CertificateCustomizeModal";
import { RoyalSealStamp } from "@/components/imperial/passport/RoyalSealStamp";

import {
  getHonorsTitle,
  getZoneBreakdown,
  loadSavedCertificate,
  saveCertificateData,
  buildCertificateUrl,
  createDefaultCertificate,
  type CertificateData,
} from "@/lib/imperial/certificate-utils";
import {
  PASSPORT_SEALS,
  getPassportProgress,
  type PassportProgress,
} from "@/lib/imperial/passport-storage";
import { cn } from "@/lib/utils";

export default function CertificateClient() {
  const searchParams = useSearchParams();
  const user = useAuthStore((s) => s.user);

  // Core Certificate Data state
  const [certData, setCertData] = useState<CertificateData>(() =>
    createDefaultCertificate("Nguyễn Hoàng Minh"),
  );
  const [isCustomizeOpen, setIsCustomizeOpen] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);
  const [isMounted, setIsMounted] = useState<boolean>(false);
  const [isVerifiedMode, setIsVerifiedMode] = useState<boolean>(false);

  // Initialize from URL params or local storage
  useEffect(() => {
    setIsMounted(true);

    const paramId = searchParams.get("id");
    const paramName = searchParams.get("name");
    const paramSchool = searchParams.get("school");
    const paramSeals = searchParams.get("seals");
    const paramVerify = searchParams.get("verify") === "1";

    if (paramVerify) {
      setIsVerifiedMode(true);
    }

    if (paramId && paramName) {
      // Reconstructed from shared URL
      const sealCount = paramSeals ? parseInt(paramSeals, 10) : 16;
      const validCount = Math.max(0, Math.min(16, isNaN(sealCount) ? 16 : sealCount));
      const loaded: CertificateData = {
        id: paramId,
        studentName: paramName,
        schoolName: paramSchool || "Trường THPT Chuyên Quốc Học Huế",
        issueDate: "Huế, năm 2026",
        unlockedSiteSlugs: PASSPORT_SEALS.slice(0, validCount).map((s) => s.slug),
        totalScore: validCount * 100,
      };
      setCertData(loaded);
    } else {
      // Normal flow: load from local storage
      const loaded = loadSavedCertificate(user?.display_name || user?.username);
      setCertData(loaded);
    }
  }, [searchParams, user]);

  // Derived calculations
  const sealCount = certData.unlockedSiteSlugs.length;
  const honors = useMemo(() => getHonorsTitle(sealCount), [sealCount]);
  const zonesBreakdown = useMemo(
    () => getZoneBreakdown(certData.unlockedSiteSlugs),
    [certData.unlockedSiteSlugs],
  );

  // Verification URL encoded in QR Code
  const verificationUrl = useMemo(() => {
    if (typeof window === "undefined") {
      return `https://lms.histolab.icu/dai-noi/chung-nhan?id=${certData.id}&verify=1`;
    }
    return buildCertificateUrl(window.location.origin, certData, true);
  }, [certData]);

  // Actions
  const handlePrint = useCallback(() => {
    if (typeof window !== "undefined") {
      window.print();
    }
  }, []);

  const handleShareLink = useCallback(async () => {
    if (typeof window === "undefined") return;

    const shareUrl = buildCertificateUrl(window.location.origin, certData);

    try {
      if (navigator.share) {
        await navigator.share({
          title: `Chứng Nhận Di Sản Hoàng Thành Huế — ${certData.studentName}`,
          text: `Chứng nhận khảo cứu di sản Cố đô Huế đạt danh hiệu "${honors.title}" với ${sealCount}/16 ấn triện son hoàng triều!`,
          url: shareUrl,
        });
        toast.success("Đã mở chia sẻ thành tích!");
        return;
      }

      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      toast.success("Đã sao chép liên kết chứng nhận vào bộ nhớ tạm!");
      setTimeout(() => setCopied(false), 2500);
    } catch {
      // Fallback copy
      try {
        await navigator.clipboard.writeText(shareUrl);
        setCopied(true);
        toast.success("Đã sao chép liên kết chứng nhận!");
        setTimeout(() => setCopied(false), 2500);
      } catch {
        toast.error("Không thể sao chép liên kết.");
      }
    }
  }, [certData, honors.title, sealCount]);

  const handleSaveCustomization = useCallback((updated: CertificateData) => {
    setCertData(updated);
    saveCertificateData(updated);
    toast.success("Đã cập nhật thông tin chứng nhận!");
  }, []);

  // If client is loading
  if (!isMounted) {
    return (
      <div className="min-h-screen bg-[#F7F2E8] flex items-center justify-center p-6">
        <div className="flex flex-col items-center gap-3">
          <div className="size-10 animate-spin rounded-full border-2 border-amber-600 border-t-transparent" />
          <span className="font-serif text-sm font-semibold text-amber-900">
            Đang tải Chứng Nhận Hoàng Triều...
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F7F2E8] dark:bg-[#15120E] text-[#2A241D] py-6 sm:py-8 px-3 sm:px-6 transition-colors selection:bg-[#A62B2B]/20">
      {/* Top Banner & Action Toolbar (Hidden during print) */}
      <div className="mx-auto max-w-5xl space-y-4 mb-6 print:hidden">
        {/* Verification Alert Banner if scanned via QR code */}
        {isVerifiedMode && (
          <div className="rounded-xl border border-emerald-500/40 bg-emerald-500/10 p-3.5 flex items-center justify-between gap-3 text-emerald-950 dark:text-emerald-200">
            <div className="flex items-center gap-2.5 text-xs sm:text-sm font-medium">
              <ShieldCheck className="size-5 text-emerald-600 shrink-0" />
              <span>
                <strong>Xác thực điện tử hợp lệ:</strong> Chứng chỉ chính thức
                được thẩm định bởi Ban Quản lý Di sản Lưu Niên & Trung tâm Bảo
                tồn Di tích Cố đô Huế.
              </span>
            </div>
            <Badge
              variant="outline"
              className="border-emerald-600/50 bg-emerald-600/15 text-emerald-700 dark:text-emerald-300 font-mono text-[10px] shrink-0"
            >
              MÃ HỢP LỆ
            </Badge>
          </div>
        )}

        {/* Toolbar Header */}
        <div className="flex flex-wrap items-center justify-between gap-3 bg-card/70 backdrop-blur-md border border-border/80 rounded-2xl p-3.5 sm:p-4 shadow-sm">
          <div className="flex items-center gap-2">
            <Link
              href="/dai-noi/ho-chieu"
              className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground font-medium transition-colors"
            >
              <ChevronLeft className="size-4" />
              <span>Sổ Hộ Chiếu</span>
            </Link>
            <span className="text-muted-foreground/40">•</span>
            <div className="flex items-center gap-1.5 text-xs text-foreground font-bold">
              <Award className="size-4 text-amber-600" />
              <span className="hidden sm:inline">Giấy Chứng Nhận Khảo Cứu</span>
              <span className="sm:hidden">Chứng Nhận</span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsCustomizeOpen(true)}
              className="h-8 text-xs gap-1.5 border-border/80 shadow-sm"
              title="Chỉnh sửa tên học sinh và trường lớp"
            >
              <Edit3 className="size-3.5" />
              <span>Tùy Chỉnh</span>
            </Button>

            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleShareLink}
              className="h-8 text-xs gap-1.5 border-border/80 shadow-sm"
              title="Sao chép link chia sẻ chứng nhận"
            >
              <Share2 className="size-3.5" />
              <span>{copied ? "Đã chép link!" : "Chia Sẻ"}</span>
            </Button>

            <Button
              type="button"
              size="sm"
              onClick={handlePrint}
              className="h-8 text-xs gap-1.5 bg-[#A62B2B] hover:bg-[#8B1E1E] text-white font-bold shadow-md"
              title="In ra giấy A4 khổ ngang hoặc lưu dưới dạng PDF"
            >
              <Printer className="size-3.5" />
              <span>Tải Về / In Chứng Nhận</span>
            </Button>
          </div>
        </div>
      </div>

      {/* =========================================================================
          PRINTABLE & VISUAL ROYAL CERTIFICATE (A4 Landscape Frame)
         ========================================================================= */}
      <div className="mx-auto max-w-[1040px] certificate-print-root">
        <CertificateFrame
          id="royal-heritage-certificate"
          className="certificate-landscape-canvas"
        >
          {/* Certificate Inner Header (Long Vân Sắc Phong) */}
          <div className="flex flex-col items-center text-center space-y-1 sm:space-y-1.5 pt-2 sm:pt-4">
            <div className="flex items-center gap-2">
              <span className="h-px w-8 sm:w-16 bg-[#C68A2C]/60" />
              <p className="font-serif text-[10px] sm:text-xs md:text-sm font-bold uppercase tracking-[0.25em] text-[#A62B2B]">
                LƯU NIÊN — ĐẠI NỘI HUẾ
              </p>
              <span className="h-px w-8 sm:w-16 bg-[#C68A2C]/60" />
            </div>

            <h1 className="font-serif text-2xl sm:text-4xl md:text-5xl font-black text-[#A62B2B] tracking-wide pt-1 leading-tight">
              CHỨNG NHẬN KHẢO CỨU DI SẢN
            </h1>

            <p className="font-serif italic text-[11px] sm:text-xs md:text-sm text-[#675C4E] max-w-2xl px-2">
              Vinh danh thành tích điền dã, giải mã kiến trúc và thu thập ấn
              triện son di sản Cố Đô Huế
            </p>
          </div>

          {/* Student Recipient Presentation */}
          <div className="flex flex-col items-center text-center my-auto py-3 sm:py-5 space-y-1.5 sm:space-y-2">
            <span className="font-serif text-[11px] sm:text-xs uppercase tracking-widest text-[#675C4E]">
              Trân trọng tuyên dương học sinh:
            </span>

            <h2 className="font-serif text-2xl sm:text-4xl md:text-[2.75rem] font-black text-[#2A241D] tracking-wide leading-none pb-1 border-b-2 border-[#C68A2C] px-6 sm:px-12">
              {certData.studentName}
            </h2>

            <p className="font-serif text-xs sm:text-sm md:text-base font-semibold text-[#675C4E] pt-1">
              Đơn vị: {certData.schoolName}
            </p>

            {/* Awarded Honors Title Card */}
            <div className="mt-2.5 sm:mt-3 px-5 sm:px-8 py-2 sm:py-2.5 rounded-full border border-[#C68A2C]/50 bg-[#FAF4E6]/90 shadow-sm flex items-center gap-2 sm:gap-3">
              <span className="text-[10px] sm:text-xs font-serif uppercase tracking-widest text-[#A62B2B] font-bold">
                Danh Hiệu:
              </span>
              <span className="font-serif text-base sm:text-xl md:text-2xl font-black text-[#A62B2B]">
                {honors.title}
              </span>
              <span className="text-xs text-[#C68A2C] hidden md:inline">✦</span>
              <span className="font-serif text-[11px] text-[#675C4E] italic hidden md:inline">
                {honors.epigraphVi}
              </span>
            </div>
          </div>

          {/* 4 Spatial Zones Seal Count Breakdown */}
          <div className="my-2 sm:my-3">
            <ZoneScoreBreakdown
              zones={zonesBreakdown}
              totalScore={certData.totalScore || sealCount * 100}
              totalSeals={PASSPORT_SEALS.length}
              unlockedCount={sealCount}
              compact={false}
            />
          </div>

          {/* Sắc Phong Kim Bảo & Ngự Tỷ của các phân khu hoàn thành */}
          {zonesBreakdown.some((z) => z.isCompleted) && (
            <div className="my-1.5 flex flex-wrap items-center justify-center gap-3 sm:gap-5 print:my-1">
              {zonesBreakdown
                .filter((z) => z.isCompleted)
                .map((z) => {
                  const isKimBao =
                    z.zoneSlug === "central-ceremonial-axis" ||
                    z.zoneSlug === "purple-forbidden-city";
                  return (
                    <div
                      key={z.zoneSlug}
                      className="flex items-center gap-2 bg-[#FAF4E6]/90 border border-[#C68A2C]/40 rounded-lg px-2.5 py-1 shadow-xs"
                    >
                      <RoyalSealStamp
                        zoneSlug={z.zoneSlug}
                        status="unlocked"
                        size={40}
                        showLabel={false}
                      />
                      <div className="text-left text-[9px] font-serif leading-tight">
                        <span className="font-bold text-[#A62B2B] block">
                          {isKimBao ? "Kim Bảo Sắc Phong" : "Ngự Tỷ Sắc Phong"}
                        </span>
                        <span className="text-[#675C4E]">{z.zoneTitleVi}</span>
                      </div>
                    </div>
                  );
                })}

              {sealCount === 16 && (
                <div className="flex items-center gap-2 bg-gradient-to-r from-amber-100 to-amber-50 border-2 border-amber-500/70 rounded-lg px-3 py-1 shadow-sm">
                  <RoyalSealStamp
                    isGrandSeal={true}
                    status="unlocked"
                    size={42}
                    showLabel={false}
                  />
                  <div className="text-left text-[9px] font-serif leading-tight">
                    <span className="font-bold text-[#7f1d1d] block">
                      Đại Kim Bảo Truyền Quốc
                    </span>
                    <span className="text-amber-900 font-semibold">
                      Đại Nam Hoàng Đế Chi Bảo
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Certificate Footer / Authentication Block */}
          <div className="mt-auto pt-2 sm:pt-3 border-t border-[#C68A2C]/30 flex flex-wrap items-end justify-between gap-3 text-xs">
            {/* Left: Verification QR Code & Serial */}
            <div className="flex items-center gap-2">
              <VerificationQr
                certificateId={certData.id}
                verificationUrl={verificationUrl}
                size={68}
                showDetails={true}
              />
            </div>

            {/* Right: Date of Issuance & Official Project Seal */}
            <div className="flex items-center gap-3 sm:gap-6 text-right">
              <div className="flex flex-col items-end justify-center space-y-0.5">
                <span className="font-serif italic text-[11px] sm:text-xs text-[#675C4E]">
                  {certData.issueDate}
                </span>
                <span className="font-serif font-bold text-xs sm:text-sm text-[#A62B2B] uppercase tracking-wider">
                  HỘI ĐỒNG THẨM ĐỊNH DI SẢN
                </span>
                <span className="text-[9px] text-[#675C4E]">
                  Dự án Khảo cứu Lịch sử Triều Nguyễn — Lưu Niên
                </span>
              </div>

              {/* Official Royal Cinnabar Seal Stamp */}
              <OfficialProjectSeal size="md" />
            </div>
          </div>
        </CertificateFrame>
      </div>

      {/* Customize Name & Seals Modal */}
      <CertificateCustomizeModal
        open={isCustomizeOpen}
        onOpenChange={setIsCustomizeOpen}
        data={certData}
        onSave={handleSaveCustomization}
      />
    </div>
  );
}
