"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import Link from "next/link";
import {
  Award,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  Compass,
  Copy,
  ExternalLink,
  FileCheck,
  FileText,
  HelpCircle,
  Info,
  Layers,
  Lock,
  MapPin,
  Maximize2,
  Printer,
  RotateCcw,
  Scroll,
  Share2,
  Sparkles,
  Unlock,
  UserCheck,
  X,
  Volume2,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useAuthStore } from "@/stores/authStore";
import {
  getPassportProgress,
  getUnlockedSealsMap,
  getSealDefinition,
  unlockSeal,
  resetPassport,
  unlockAllSealsDemo,
  unlockCertificateDemo,
  playStampSound,
  stampZoneSeal,
  getZoneRoyalSeal,
  stampGrandSeal,
  getGrandRoyalSeal,
  PASSPORT_SEALS,
  PASSPORT_ZONE_META,
  PASSPORT_ALL_BADGES,
  PASSPORT_STUDENT_KEY,
  type PassportSealDefinition,
  type PassportProgress,
  type SpatialZoneSlug,
  type UnlockedSealRecord,
} from "@/lib/imperial/passport-storage";
import { RoyalSealStamp } from "@/components/imperial/passport/RoyalSealStamp";
import { OfficialProjectSeal } from "@/components/imperial/certificate/OfficialProjectSeal";
import { cn } from "@/lib/utils";

type ActiveTab = "cover" | "all" | SpatialZoneSlug;

export default function PassportClient() {
  const user = useAuthStore((s) => s.user);

  // Passport Progress state
  const [progress, setProgress] = useState<PassportProgress>(getPassportProgress);
  const [unlockedMap, setUnlockedMap] = useState<Record<string, UnlockedSealRecord>>({});
  const [activeTab, setActiveTab] = useState<ActiveTab>("cover");

  // Student details
  const [studentName, setStudentName] = useState<string>("Nguyễn Văn An");
  const [studentClass, setStudentClass] = useState<string>("11 Sử — THPT Chuyên Quốc Học Huế");
  const [isEditingStudent, setIsEditingStudent] = useState<boolean>(false);

  // Selected Stamp Modal
  const [selectedSeal, setSelectedSeal] = useState<PassportSealDefinition | null>(null);
  const [isSealModalOpen, setIsSealModalOpen] = useState<boolean>(false);

  // Certificate Modal
  const [isCertificateOpen, setIsCertificateOpen] = useState<boolean>(false);
  const [copyCodeSuccess, setCopyCodeSuccess] = useState<boolean>(false);

  // Certificate Code identifier
  const certificateCode = useMemo(() => {
    return `LN-HN-2026-${Math.abs(
      studentName.split("").reduce((acc, c) => acc + c.charCodeAt(0), 108),
    )
      .toString(36)
      .toUpperCase()
      .padStart(4, "X")}-${progress.unlockedCount.toString().padStart(2, "0")}`;
  }, [studentName, progress.unlockedCount]);

  // Synchronize state and listen to seal unlock events
  const refreshProgress = useCallback(() => {
    const updated = getPassportProgress();
    setProgress(updated);
    setUnlockedMap(getUnlockedSealsMap());
  }, []);

  useEffect(() => {
    refreshProgress();

    // Load saved student name or user info
    if (typeof window !== "undefined") {
      const savedStudent = localStorage.getItem(PASSPORT_STUDENT_KEY);
      if (savedStudent) {
        try {
          const parsed = JSON.parse(savedStudent);
          if (parsed.name) setStudentName(parsed.name);
          if (parsed.class) setStudentClass(parsed.class);
        } catch {
          // ignore parsing error
        }
      } else if (user?.display_name || user?.username) {
        setStudentName(user.display_name || user.username || "Nguyễn Văn An");
      }
    }

    const handleSealEvent = () => {
      refreshProgress();
    };

    window.addEventListener("imperial-seal-unlocked", handleSealEvent);
    return () => {
      window.removeEventListener("imperial-seal-unlocked", handleSealEvent);
    };
  }, [user, refreshProgress]);

  const handleSaveStudent = () => {
    setIsEditingStudent(false);
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem(
          PASSPORT_STUDENT_KEY,
          JSON.stringify({ name: studentName.trim(), class: studentClass.trim() }),
        );
      } catch (err) {
        console.error("Failed to save student profile:", err);
      }
    }
  };

  const handleOpenSeal = (seal: PassportSealDefinition) => {
    setSelectedSeal(seal);
    setIsSealModalOpen(true);
  };

  const handlePrintCertificate = () => {
    if (typeof window !== "undefined") {
      window.print();
    }
  };

  const handleCopyCertCode = () => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(certificateCode);
      setCopyCodeSuccess(true);
      setTimeout(() => setCopyCodeSuccess(false), 2000);
    }
  };

  // Determine honorific title based on seals count
  const honoraryTitle = useMemo(() => {
    const count = progress.unlockedCount;
    if (count === 16) return "Đại Học Sĩ Khảo Cứu Di Sản Hoàng Thành Huế";
    if (count >= 12) return "Chuyên Viên Khảo Cứu Cung Đình Huế";
    if (count >= 8) return "Nhà Khảo Cứu Trẻ Hoàng Thành Huế";
    if (count >= 4) return "Học Giả Tập Sự Di Sản Cố Đô";
    return "Tập Sự Khảo Cứu Lịch Sử";
  }, [progress.unlockedCount]);

  return (
    <div className="min-h-screen bg-[#fcf9f2] dark:bg-[#120f0c] text-[#33261a] dark:text-[#ebdcc8] py-8 px-4 sm:px-6 lg:px-8 transition-colors">
      <div className="mx-auto max-w-5xl space-y-8">
        {/* Navigation Breadcrumb & Page Header */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#e2d5c2] dark:border-[#382b20] pb-4">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Link
              href="/dai-noi"
              className="hover:text-primary transition-colors flex items-center gap-1"
            >
              <Compass className="size-3.5" />
              <span>Đại Nội Huế</span>
            </Link>
            <span>/</span>
            <span className="font-semibold text-foreground">Hộ Chiếu Hoàng Gia</span>
          </div>

          <div className="flex items-center gap-2">
            {/* Certificate Quick Trigger */}
            <Button
              onClick={() => setIsCertificateOpen(true)}
              disabled={!progress.canExportCertificate}
              className={cn(
                "h-8 text-xs font-semibold gap-1.5 transition-all shadow-sm",
                progress.canExportCertificate
                  ? "bg-amber-600 hover:bg-amber-700 text-white shadow-amber-600/20 animate-pulse"
                  : "bg-muted text-muted-foreground cursor-not-allowed opacity-60",
              )}
            >
              <Award className="size-3.5" />
              <span>Xuất Chứng Nhận</span>
              {progress.canExportCertificate ? (
                <Sparkles className="size-3 text-amber-200" />
              ) : (
                <span className="text-[10px] opacity-75">
                  ({progress.unlockedCount}/{progress.minCertificateSeals})
                </span>
              )}
            </Button>

            <Link href="/dai-noi">
              <Button variant="outline" size="sm" className="h-8 text-xs gap-1">
                <span>Về Bản Đồ</span>
                <ChevronRight className="size-3" />
              </Button>
            </Link>
          </div>
        </div>

        {/* =========================================================================
            PARCHMENT BOOKLET CONTAINER
            Gold-embossed royal border, parchment paper hue, folded book structure
           ========================================================================= */}
        <div className="relative rounded-2xl border-4 border-[#d4af37]/80 bg-[#fdfaf3] dark:bg-[#191410] shadow-[0_12px_40px_-15px_rgba(74,48,20,0.35)] dark:shadow-[0_12px_40px_-15px_rgba(0,0,0,0.8)] overflow-hidden">
          {/* Ornate Imperial Gold Corner Accents */}
          <div className="absolute top-2 left-2 size-10 border-t-2 border-l-2 border-[#d4af37] pointer-events-none" />
          <div className="absolute top-2 right-2 size-10 border-t-2 border-r-2 border-[#d4af37] pointer-events-none" />
          <div className="absolute bottom-2 left-2 size-10 border-b-2 border-l-2 border-[#d4af37] pointer-events-none" />
          <div className="absolute bottom-2 right-2 size-10 border-b-2 border-r-2 border-[#d4af37] pointer-events-none" />

          {/* Golden dragon/phoenix emblem header banner */}
          <div className="bg-gradient-to-r from-[#991b1b] via-[#b91c1c] to-[#991b1b] text-amber-100 py-3 px-6 text-center shadow-inner relative border-b-2 border-[#d4af37]/70">
            <div className="flex items-center justify-center gap-3">
              <span className="text-amber-300 font-serif text-lg tracking-widest hidden sm:inline">
                ❖
              </span>
              <span className="font-serif uppercase tracking-[0.2em] font-black text-sm sm:text-base text-amber-200 drop-shadow-sm">
                Đại Nam Khảo Ký • Hoàng Triều Ngự Ấn
              </span>
              <span className="text-amber-300 font-serif text-lg tracking-widest hidden sm:inline">
                ❖
              </span>
            </div>
            <p className="text-[11px] text-amber-100/90 font-serif italic mt-0.5">
              Sổ Hộ Chiếu Di Sản Số & Ấn Triện Hoàng Cung — Lưu Niên Sử Kí
            </p>
          </div>

          {/* Royal Booklet Navigation Tabs */}
          <div className="flex flex-wrap items-center justify-center gap-1 p-2 sm:p-3 bg-[#f5eedf] dark:bg-[#201a14] border-b border-[#e2d5c2] dark:border-[#382b20]">
            <button
              onClick={() => setActiveTab("cover")}
              className={cn(
                "px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5",
                activeTab === "cover"
                  ? "bg-[#991b1b] text-white shadow-sm"
                  : "text-[#5c4430] dark:text-[#c4b5a3] hover:bg-[#ebdcc8] dark:hover:bg-[#2d241c]",
              )}
            >
              <Scroll className="size-3.5" />
              <span>Bìa Sổ Hoàng Gia</span>
            </button>

            <button
              onClick={() => setActiveTab("all")}
              className={cn(
                "px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5",
                activeTab === "all"
                  ? "bg-[#991b1b] text-white shadow-sm"
                  : "text-[#5c4430] dark:text-[#c4b5a3] hover:bg-[#ebdcc8] dark:hover:bg-[#2d241c]",
              )}
            >
              <Layers className="size-3.5" />
              <span>Tất cả 16 Ấn Triện</span>
              <span className="text-[10px] opacity-80">
                ({progress.unlockedCount}/16)
              </span>
            </button>

            {(
              [
                "central-ceremonial-axis",
                "ancestral-worship-space",
                "purple-forbidden-city",
                "royal-living-gardens",
              ] as SpatialZoneSlug[]
            ).map((zoneSlug) => {
              const zoneMeta = PASSPORT_ZONE_META[zoneSlug];
              const zoneProg = progress.zones.find((z) => z.zoneSlug === zoneSlug);
              const isActive = activeTab === zoneSlug;
              return (
                <button
                  key={zoneSlug}
                  onClick={() => setActiveTab(zoneSlug)}
                  className={cn(
                    "px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5",
                    isActive
                      ? "bg-[#991b1b] text-white shadow-sm"
                      : "text-[#5c4430] dark:text-[#c4b5a3] hover:bg-[#ebdcc8] dark:hover:bg-[#2d241c]",
                  )}
                >
                  <span>{zoneMeta.badgeIcon}</span>
                  <span className="hidden sm:inline">{zoneMeta.title}</span>
                  <span className="text-[10px] opacity-80">
                    ({zoneProg?.unlockedCount || 0}/{zoneProg?.totalSeals || 0})
                  </span>
                  {zoneProg?.isComplete && (
                    <CheckCircle2 className="size-3 text-amber-400" />
                  )}
                </button>
              );
            })}
          </div>

          {/* =========================================================================
              BOOKLET CONTENT SECTION
             ========================================================================= */}
          <div className="p-6 sm:p-8">
            {/* 1. COVER PAGE VIEW */}
            {activeTab === "cover" && (
              <div className="space-y-8 animate-in fade-in duration-300">
                {/* Royal Parchment Title Header */}
                <div className="text-center space-y-3 max-w-2xl mx-auto">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-amber-600/30 bg-amber-500/10 text-amber-800 dark:text-amber-300 text-xs font-semibold">
                    <Sparkles className="size-3.5" />
                    <span>Hồ Sơ Khảo Cứu Di Sản Cố Đô</span>
                  </div>

                  <h1 className="font-serif text-3xl sm:text-4xl font-extrabold text-[#7f1d1d] dark:text-[#f87171] tracking-wide">
                    HỘ CHIẾU DI SẢN ĐẠI NỘI HUẾ
                  </h1>

                  <p className="font-serif italic text-xs sm:text-sm text-muted-foreground leading-relaxed">
                    &ldquo;Khảo sát di tích, giải mã sử liệu chính biên và thu thập dấu triện hoàng gia chu sa qua từng bước chân khám phá Cố Đô.&rdquo;
                  </p>
                </div>

                {/* Student Profile Card (Gold-embossed border) */}
                <div className="rounded-xl border-2 border-[#d4af37]/70 bg-gradient-to-br from-[#faf4e6] to-[#f5ebd6] dark:from-[#221b14] dark:to-[#1a140f] p-5 sm:p-6 shadow-md relative">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="space-y-1">
                      <span className="text-[11px] font-bold uppercase tracking-wider text-amber-800 dark:text-amber-400 flex items-center gap-1.5">
                        <UserCheck className="size-3.5" />
                        Chủ nhân Hộ chiếu Hoàng gia:
                      </span>

                      {isEditingStudent ? (
                        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 pt-1">
                          <input
                            type="text"
                            value={studentName}
                            onChange={(e) => setStudentName(e.target.value)}
                            placeholder="Họ và tên học sinh"
                            className="rounded-md border border-[#d4af37] bg-background px-3 py-1.5 text-xs font-serif font-bold text-foreground w-48 sm:w-56 focus:outline-none focus:ring-1 focus:ring-primary"
                          />
                          <input
                            type="text"
                            value={studentClass}
                            onChange={(e) => setStudentClass(e.target.value)}
                            placeholder="Lớp / Trường"
                            className="rounded-md border border-[#d4af37] bg-background px-3 py-1.5 text-xs text-foreground w-56 sm:w-64 focus:outline-none focus:ring-1 focus:ring-primary"
                          />
                          <Button
                            size="sm"
                            onClick={handleSaveStudent}
                            className="h-7 text-xs bg-amber-700 hover:bg-amber-800 text-white font-semibold"
                          >
                            Lưu thông tin
                          </Button>
                        </div>
                      ) : (
                        <div className="flex items-baseline gap-3">
                          <h2 className="font-serif text-xl sm:text-2xl font-black text-foreground">
                            {studentName}
                          </h2>
                          <span className="text-xs text-muted-foreground">
                            ({studentClass})
                          </span>
                          <button
                            onClick={() => setIsEditingStudent(true)}
                            className="text-[11px] text-amber-700 dark:text-amber-400 hover:underline font-medium"
                          >
                            [Đổi tên]
                          </button>
                        </div>
                      )}

                      <div className="flex items-center gap-2 pt-1">
                        <Badge className="bg-[#991b1b] text-amber-100 text-[11px] font-serif py-0.5 px-2.5">
                          {honoraryTitle}
                        </Badge>
                        <span className="text-[11px] font-mono text-muted-foreground">
                          Mã định danh: {certificateCode}
                        </span>
                      </div>
                    </div>

                    {/* Quick Certificate Access */}
                    <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-center gap-2 pt-2 sm:pt-0 border-t sm:border-t-0 border-[#d4af37]/30">
                      <div className="text-right">
                        <span className="text-[11px] text-muted-foreground block">
                          Tiêu chuẩn cấp Chứng nhận:
                        </span>
                        <strong className="text-xs text-foreground font-semibold">
                          Tối thiểu 4/16 dấu triện
                        </strong>
                      </div>

                      <Link href="/dai-noi/chung-nhan">
                        <Button
                          disabled={!progress.canExportCertificate}
                          className={cn(
                            "text-xs h-8 gap-1.5 font-semibold",
                            progress.canExportCertificate
                              ? "bg-amber-700 hover:bg-amber-800 text-white shadow-sm"
                              : "bg-muted text-muted-foreground opacity-60",
                          )}
                        >
                          <Award className="size-3.5" />
                          <span>Xem Chứng Nhận</span>
                        </Button>
                      </Link>
                    </div>
                  </div>
                </div>

                {/* Progress Stats Display */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  {/* Total Collected */}
                  <div className="rounded-xl border border-[#e2d5c2] dark:border-[#382b20] bg-card p-4 sm:p-5 text-center space-y-1">
                    <span className="text-[11px] uppercase tracking-wider font-bold text-muted-foreground">
                      Số dấu triện thu thập
                    </span>
                    <div className="font-serif text-3xl sm:text-4xl font-extrabold text-[#991b1b] dark:text-[#f87171]">
                      {progress.unlockedCount}
                      <span className="text-base text-muted-foreground font-normal">
                        /16
                      </span>
                    </div>
                    <span className="text-xs font-semibold text-foreground">
                      Đã Khảo Cứu Hoàn Tất
                    </span>
                  </div>

                  {/* Percentage Bar */}
                  <div className="rounded-xl border border-[#e2d5c2] dark:border-[#382b20] bg-card p-4 sm:p-5 text-center space-y-2">
                    <span className="text-[11px] uppercase tracking-wider font-bold text-muted-foreground">
                      Tiến độ hộ chiếu
                    </span>
                    <div className="font-serif text-3xl sm:text-4xl font-extrabold text-amber-600 dark:text-amber-400">
                      {progress.percentage}%
                    </div>
                    <div className="w-full bg-secondary rounded-full h-2 overflow-hidden">
                      <div
                        className="bg-amber-600 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${progress.percentage}%` }}
                      />
                    </div>
                  </div>

                  {/* Badges Earned */}
                  <div className="rounded-xl border border-[#e2d5c2] dark:border-[#382b20] bg-card p-4 sm:p-5 text-center space-y-1">
                    <span className="text-[11px] uppercase tracking-wider font-bold text-muted-foreground">
                      Huy hiệu hoàng triều
                    </span>
                    <div className="font-serif text-3xl sm:text-4xl font-extrabold text-emerald-600 dark:text-emerald-400">
                      {progress.earnedBadges.length}
                      <span className="text-base text-muted-foreground font-normal">
                        /5
                      </span>
                    </div>
                    <span className="text-xs font-semibold text-foreground">
                      Huy Hiệu Vinh Danh
                    </span>
                  </div>
                </div>

                {/* 4 Spatial Zones Progress Quick Glance */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="font-serif font-bold text-base text-foreground flex items-center gap-2">
                      <Compass className="size-4 text-primary" />
                      <span>4 Phân Khu Không Gian Hoàng Thành Huế:</span>
                    </h3>
                    <span className="text-xs text-muted-foreground">
                      Bấm vào từng khu để xem trang đóng dấu
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {progress.zones.map((zone) => (
                      <div
                        key={zone.zoneSlug}
                        onClick={() => setActiveTab(zone.zoneSlug)}
                        className="rounded-xl border border-[#e2d5c2] dark:border-[#382b20] bg-card/60 hover:bg-card p-4 transition-all cursor-pointer flex items-center justify-between gap-4 group"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-2xl group-hover:scale-110 transition-transform">
                            {zone.badgeIcon}
                          </span>
                          <div>
                            <div className="flex items-center gap-1.5">
                              <h4 className="font-serif font-bold text-sm text-foreground group-hover:text-primary transition-colors">
                                {zone.zoneTitle}
                              </h4>
                              <span className="text-[11px] font-serif text-muted-foreground">
                                • {zone.zoneTitleHanNom}
                              </span>
                            </div>
                            <p className="text-[11px] text-muted-foreground line-clamp-1">
                              {zone.description}
                            </p>
                          </div>
                        </div>

                        <div className="text-right shrink-0">
                          <Badge
                            variant={zone.isComplete ? "default" : "outline"}
                            className={cn(
                              "text-xs font-mono",
                              zone.isComplete &&
                                "bg-emerald-600 hover:bg-emerald-700 text-white",
                            )}
                          >
                            {zone.unlockedCount}/{zone.totalSeals}
                          </Badge>
                          <span className="text-[10px] text-muted-foreground block pt-0.5">
                            {zone.percentage}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Cluster Completion Badges Showcase */}
                <div className="space-y-3 pt-2">
                  <h3 className="font-serif font-bold text-base text-foreground flex items-center gap-2">
                    <Award className="size-4 text-amber-600" />
                    <span>Huy Hiệu Danh Dự Cố Đô (5 Huy Hiệu):</span>
                  </h3>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {PASSPORT_ALL_BADGES.map((badge) => {
                      const isEarned = progress.earnedBadges.some(
                        (b) => b.id === badge.id,
                      );
                      return (
                        <div
                          key={badge.id}
                          className={cn(
                            "rounded-xl border p-3.5 transition-all flex items-start gap-3",
                            isEarned
                              ? "border-amber-500/40 bg-amber-500/10 shadow-sm"
                              : "border-border/50 bg-secondary/20 opacity-60",
                          )}
                        >
                          <div
                            className={cn(
                              "size-10 rounded-xl flex items-center justify-center text-xl shrink-0 border",
                              isEarned
                                ? "bg-amber-100 dark:bg-amber-950/40 border-amber-500/30 text-amber-700"
                                : "bg-muted border-border/40 text-muted-foreground grayscale",
                            )}
                          >
                            {badge.icon}
                          </div>

                          <div className="space-y-0.5 min-w-0 flex-1">
                            <div className="flex items-center justify-between gap-1">
                              <h4 className="font-serif font-bold text-xs text-foreground truncate">
                                {badge.name}
                              </h4>
                              {isEarned ? (
                                <Badge className="bg-emerald-600 text-white text-[9px] py-0 px-1.5 h-4">
                                  Đạt
                                </Badge>
                              ) : (
                                <Lock className="size-3 text-muted-foreground" />
                              )}
                            </div>
                            <span className="text-[10px] font-serif text-muted-foreground block">
                              {badge.titleHanNom}
                            </span>
                            <p className="text-[11px] text-muted-foreground leading-snug line-clamp-2">
                              {badge.description}
                            </p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Call to action */}
                <div className="flex flex-wrap items-center justify-center gap-3 pt-4 border-t border-[#e2d5c2] dark:border-[#382b20]">
                  <Button
                    onClick={() => setActiveTab("central-ceremonial-axis")}
                    className="font-serif font-bold bg-[#991b1b] hover:bg-[#7f1d1d] text-white gap-2"
                  >
                    <span>Lật Sổ Khảo Cứu Trục Trung Tâm</span>
                    <ChevronRight className="size-4" />
                  </Button>

                  <Button
                    variant="outline"
                    onClick={() => setActiveTab("all")}
                    className="font-semibold text-xs border-[#d4af37]"
                  >
                    Xem Toàn Bộ 16 Dấu Ấn Triện
                  </Button>
                </div>
              </div>
            )}

            {/* 2. ZONE PAGES & ALL SEALS VIEW */}
            {activeTab !== "cover" && (
              <div className="space-y-6 animate-in fade-in duration-300">
                {/* Zone Header Banner */}
                {activeTab !== "all" && (
                  <div className="space-y-4">
                    <div className="rounded-xl border border-[#d4af37]/60 bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent p-5 space-y-2">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">
                            {PASSPORT_ZONE_META[activeTab].badgeIcon}
                          </span>
                          <div>
                            <h2 className="font-serif text-xl sm:text-2xl font-black text-foreground">
                              {PASSPORT_ZONE_META[activeTab].title}
                            </h2>
                            <span className="text-xs font-serif text-muted-foreground">
                              {PASSPORT_ZONE_META[activeTab].titleHanNom}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          {progress.zones.find((z) => z.zoneSlug === activeTab)
                            ?.isComplete ? (
                            <Badge className="bg-emerald-600 text-white text-xs gap-1 py-1 px-3">
                              <CheckCircle2 className="size-3.5" />
                              <span>Đã hoàn thành toàn bộ dấu triện phân khu!</span>
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="text-xs">
                              Tiến độ:{" "}
                              {
                                progress.zones.find((z) => z.zoneSlug === activeTab)
                                  ?.unlockedCount
                              }
                              /
                              {
                                progress.zones.find((z) => z.zoneSlug === activeTab)
                                  ?.totalSeals
                              }
                            </Badge>
                          )}
                        </div>
                      </div>

                      <p className="text-xs sm:text-sm text-foreground/80 leading-relaxed font-serif">
                        {PASSPORT_ZONE_META[activeTab].description}
                      </p>
                    </div>

                    {/* UNIQUE ZONE ROYAL SEAL BANNER (Kim Bảo & Ngự Tỷ Motifs) */}
                    {(() => {
                      const zoneInfo = progress.zones.find((z) => z.zoneSlug === activeTab);
                      const zoneRoyalSeal = zoneInfo?.royalSeal || getZoneRoyalSeal(activeTab);
                      const isComplete = Boolean(zoneInfo?.isComplete);
                      const isStamped = Boolean(zoneInfo?.isZoneSealStamped || isComplete);
                      const motifName =
                        zoneRoyalSeal?.motif === "kim_bao" ? "Kim Bảo Hoàng Triều" : "Ngự Tỷ Hoàng Triều";

                      return (
                        <div
                          className={cn(
                            "rounded-2xl border-2 p-5 sm:p-6 transition-all shadow-sm flex flex-col md:flex-row items-center justify-between gap-6",
                            isComplete
                              ? "border-[#d4af37] bg-gradient-to-r from-amber-100/90 via-[#fefaf0] to-amber-50/80 dark:from-[#251e16] dark:via-[#1c1611] dark:to-[#221a13]"
                              : "border-border/60 bg-muted/20 opacity-80",
                          )}
                        >
                          <div className="flex flex-col sm:flex-row items-center gap-5 text-center sm:text-left">
                            <div className="shrink-0 p-1 rounded-xl bg-background/50 border border-[#d4af37]/40 shadow-inner">
                              <RoyalSealStamp
                                zoneSlug={activeTab}
                                status={isStamped ? "unlocked" : "locked"}
                                size="lg"
                                interactive={isComplete}
                                showDate={true}
                                onStampingComplete={() => {
                                  stampZoneSeal(activeTab);
                                  refreshProgress();
                                }}
                              />
                            </div>

                            <div className="space-y-1.5 max-w-lg">
                              <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
                                <Badge
                                  className={cn(
                                    "text-[10px] font-serif uppercase tracking-wider",
                                    zoneRoyalSeal?.motif === "kim_bao"
                                      ? "bg-amber-600 text-white"
                                      : "bg-emerald-700 text-white",
                                  )}
                                >
                                  {motifName}
                                </Badge>
                                <span className="text-xs font-serif italic text-muted-foreground">
                                  {zoneRoyalSeal?.historicalEra}
                                </span>
                              </div>

                              <h3 className="font-serif text-xl sm:text-2xl font-black text-[#7f1d1d] dark:text-[#f87171]">
                                {zoneRoyalSeal?.sealTextQuocNgu} ({zoneRoyalSeal?.sealTextHanNom})
                              </h3>

                              <p className="text-xs text-foreground/80 leading-relaxed font-serif">
                                {zoneRoyalSeal?.symbolDescriptionVi}
                              </p>

                              <div className="pt-1 text-[11px] font-medium text-muted-foreground">
                                {isComplete ? (
                                  <span className="text-emerald-700 dark:text-emerald-400 font-semibold flex items-center justify-center sm:justify-start gap-1">
                                    <CheckCircle2 className="size-3.5" />
                                    Đã sắc phong và lưu giữ ấn triện hoàng gia vào Hộ Chiếu!
                                  </span>
                                ) : (
                                  <span>
                                    Cần thu thập đủ {zoneInfo?.totalSeals} con dấu di tích trong phân khu để phong tặng ấn triện (Hiện tại: {zoneInfo?.unlockedCount}/{zoneInfo?.totalSeals}).
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>

                          {isComplete && (
                            <Button
                              onClick={() => {
                                stampZoneSeal(activeTab);
                                refreshProgress();
                              }}
                              className="shrink-0 font-serif font-bold text-xs gap-1.5 bg-[#991b1b] hover:bg-[#7f1d1d] text-white shadow-md"
                            >
                              <Sparkles className="size-3.5 text-amber-300" />
                              <span>Đóng Dấu {zoneRoyalSeal?.motif === "kim_bao" ? "Kim Bảo" : "Ngự Tỷ"}</span>
                            </Button>
                          )}
                        </div>
                      );
                    })()}
                  </div>
                )}

                {activeTab === "all" && (
                  <div className="space-y-4">
                    <div className="text-center space-y-1.5 pb-2">
                      <h2 className="font-serif text-2xl font-black text-foreground">
                        Bảng Ấn Triện Toàn Cảnh Đại Nội Huế
                      </h2>
                      <p className="text-xs text-muted-foreground">
                        Khảo sát 16 công trình trọng điểm. Bấm vào từng con dấu đã mở để xem chiến tích, hoặc bấm vào dấu khóa để nhận gợi ý câu hỏi.
                      </p>
                    </div>

                    {/* GRAND IMPERIAL SEAL DISPLAY (Đại Nam Hoàng Đế Chi Bảo) */}
                    {progress.unlockedCount === 16 && (
                      <div className="rounded-2xl border-3 border-[#d4af37] bg-gradient-to-r from-amber-500/15 via-[#fffdf5] to-amber-500/10 dark:from-[#2a2015] dark:via-[#1f1710] dark:to-[#241a12] p-6 shadow-xl flex flex-col md:flex-row items-center justify-between gap-6">
                        <div className="flex flex-col sm:flex-row items-center gap-5 text-center sm:text-left">
                          <div className="shrink-0 p-1.5 rounded-2xl bg-background/60 border-2 border-[#d4af37] shadow-lg">
                            <RoyalSealStamp
                              isGrandSeal={true}
                              status={progress.isGrandSealStamped ? "unlocked" : "locked"}
                              size="xl"
                              interactive={true}
                              showDate={true}
                              onStampingComplete={() => {
                                stampGrandSeal();
                                refreshProgress();
                              }}
                            />
                          </div>

                          <div className="space-y-1.5 max-w-xl">
                            <Badge className="bg-[#991b1b] text-amber-200 text-xs font-serif uppercase tracking-widest py-1 px-3">
                              ĐẠI KIM BẢO TRUYỀN QUỐC TỐI THƯỢNG
                            </Badge>
                            <h3 className="font-serif text-2xl sm:text-3xl font-black text-[#7f1d1d] dark:text-[#f87171]">
                              Đại Nam Hoàng Đế Chi Bảo (大南皇帝之寶)
                            </h3>
                            <p className="text-xs sm:text-sm text-foreground/85 leading-relaxed font-serif">
                              Bảo vật hoàng triều trấn quốc tối thượng, chứng nhận học sinh đã hoàn tất khảo sát toàn bộ 16 di tích kiến trúc lịch sử Đại Nội Huế với danh hiệu <strong>Bậc Thầy Khảo Cứu Cố Đô</strong>!
                            </p>
                            <div className="flex items-center gap-2 pt-1 text-xs text-emerald-700 dark:text-emerald-400 font-semibold">
                              <CheckCircle2 className="size-4" />
                              <span>Trọn bộ 16 ấn triện son và 4 Kim Bảo / Ngự Tỷ đã hoàn mãn!</span>
                            </div>
                          </div>
                        </div>

                        <Button
                          onClick={() => {
                            stampGrandSeal();
                            refreshProgress();
                          }}
                          className="shrink-0 font-serif font-bold bg-[#991b1b] hover:bg-[#7f1d1d] text-white shadow-lg gap-2 text-sm px-5 py-2.5 h-auto"
                        >
                          <Sparkles className="size-4 text-amber-300" />
                          <span>Đóng Đại Kim Bảo</span>
                        </Button>
                      </div>
                    )}
                  </div>
                )}

                {/* Grid of Imperial Stamps */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
                  {PASSPORT_SEALS.filter((seal) =>
                    activeTab === "all" ? true : seal.zoneSlug === activeTab,
                  ).map((seal) => {
                    const isUnlocked = Boolean(unlockedMap[seal.slug]);
                    const unlockData = unlockedMap[seal.slug];

                    // Subtle natural stamp tilt angle for authenticity
                    const rotationDeg = (seal.order % 5 - 2) * 0.75;

                    return (
                      <div
                        key={seal.slug}
                        onClick={() => handleOpenSeal(seal)}
                        className={cn(
                          "group relative rounded-2xl p-4 transition-all duration-300 cursor-pointer flex flex-col items-center justify-between text-center select-none",
                          isUnlocked
                            ? "border-2 border-red-700/60 bg-[#fffdfa] dark:bg-[#1f1714] shadow-md hover:shadow-lg hover:-translate-y-1 hover:border-red-600"
                            : "border-2 border-dashed border-stone-300 dark:border-stone-700 bg-stone-100/50 dark:bg-stone-900/30 hover:bg-stone-100 dark:hover:bg-stone-900/60",
                        )}
                      >
                        {/* Stamp Order Tag */}
                        <div className="w-full flex items-center justify-between text-[10px] text-muted-foreground mb-2">
                          <span className="font-mono">#{seal.order.toString().padStart(2, "0")}</span>
                          <span className="font-serif italic truncate max-w-[120px]">
                            {seal.zoneName}
                          </span>
                        </div>

                        {/* ROYAL VERMILION SEAL (Vector SVG RoyalSealStamp Engine) */}
                        <div className="my-2 transition-transform duration-300 group-hover:scale-105">
                          <RoyalSealStamp
                            monumentSlug={seal.slug}
                            status={isUnlocked ? "unlocked" : "locked"}
                            size="md"
                            rotationAngle={rotationDeg}
                          />
                        </div>

                        {/* Monument Name & Status Footer */}
                        <div className="w-full space-y-1 pt-1">
                          <h4 className="font-serif font-bold text-sm text-foreground group-hover:text-primary transition-colors">
                            {seal.name}
                          </h4>

                          {isUnlocked ? (
                            <div className="flex items-center justify-center gap-1 text-[11px] font-semibold text-red-700 dark:text-red-400">
                              <CheckCircle2 className="size-3" />
                              <span>Đã đóng ấn son</span>
                            </div>
                          ) : (
                            <div className="flex items-center justify-center gap-1 text-[11px] text-muted-foreground group-hover:text-primary transition-colors">
                              <HelpCircle className="size-3" />
                              <span>Bấm để xem gợi ý</span>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* =========================================================================
            DEVELOPER & DEMO TESTING CONTROLS (Non-intrusive bottom toolbar)
           ========================================================================= */}
        <div className="rounded-xl border border-border/70 bg-card/60 p-4 flex flex-wrap items-center justify-between gap-3 text-xs text-muted-foreground">
          <div className="flex items-center gap-2">
            <Sparkles className="size-4 text-amber-500" />
            <span>
              <strong>Bảng Thử Nghiệm Giảng Dạy:</strong> Dành cho giáo viên & học sinh kiểm thử quy trình đóng dấu và xuất chứng nhận.
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                unlockCertificateDemo();
                refreshProgress();
              }}
              className="h-7 text-xs"
            >
              Mở 4 dấu (Đủ điều kiện Chứng Nhận)
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                unlockAllSealsDemo();
                refreshProgress();
              }}
              className="h-7 text-xs text-amber-600 border-amber-500/40 hover:bg-amber-500/10"
            >
              Mở toàn bộ 16 dấu (Demo hoàn tất)
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                if (confirm("Em có chắc chắn muốn đặt lại toàn bộ Hộ Chiếu?")) {
                  resetPassport();
                  refreshProgress();
                }
              }}
              className="h-7 text-xs text-destructive hover:bg-destructive/10"
            >
              <RotateCcw className="size-3 mr-1" />
              <span>Đặt lại</span>
            </Button>
          </div>
        </div>
      </div>

      {/* =========================================================================
          MODAL 1: STAMP DETAILS & HINT INSPECTION
         ========================================================================= */}
      {selectedSeal && (
        <Dialog open={isSealModalOpen} onOpenChange={setIsSealModalOpen}>
          <DialogContent className="max-w-md sm:max-w-lg p-0 gap-0 border-2 border-[#d4af37]/60 bg-[#fffdfa] dark:bg-[#18130f] overflow-hidden">
            {/* Header */}
            <div className="p-6 pb-4 bg-gradient-to-b from-amber-500/10 to-transparent border-b border-border/60">
              <div className="flex items-center justify-between gap-2">
                <Badge
                  className={cn(
                    "text-xs font-serif font-bold py-0.5 px-2.5",
                    unlockedMap[selectedSeal.slug]
                      ? "bg-[#991b1b] text-white"
                      : "bg-muted text-muted-foreground",
                  )}
                >
                  {unlockedMap[selectedSeal.slug]
                    ? "ĐÃ ĐÓNG DẤU TRIỆN SON"
                    : "CHƯA KHẢO CỨU"}
                </Badge>
                <span className="text-xs text-muted-foreground font-mono">
                  Phân khu: {selectedSeal.zoneName}
                </span>
              </div>

              <DialogTitle className="mt-2 font-serif text-2xl font-black text-foreground">
                {selectedSeal.name}
              </DialogTitle>
              <DialogDescription className="text-xs text-muted-foreground mt-0.5">
                Ấn phẩm: <strong>{selectedSeal.sealTitle}</strong>
              </DialogDescription>
            </div>

            <div className="p-6 space-y-4">
              {/* Stamp Visual Banner with Authentic RoyalSealStamp */}
              <div className="flex flex-col items-center justify-center py-2">
                <RoyalSealStamp
                  monumentSlug={selectedSeal.slug}
                  status={unlockedMap[selectedSeal.slug] ? "unlocked" : "locked"}
                  size="lg"
                  interactive={!unlockedMap[selectedSeal.slug]}
                  showDate={true}
                  onStampingComplete={() => {
                    unlockSeal(selectedSeal.slug, "Khảo sát và đóng dấu tại Hộ Chiếu");
                    refreshProgress();
                  }}
                />
                {!unlockedMap[selectedSeal.slug] && (
                  <span className="text-[10px] text-muted-foreground mt-2 italic">
                    (Nhấp trực tiếp vào con dấu để thử nghiệm đóng dấu triện son)
                  </span>
                )}
              </div>

              {/* Status Details */}
              {unlockedMap[selectedSeal.slug] ? (
                <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3.5 text-xs text-emerald-950 dark:text-emerald-200 space-y-1">
                  <div className="flex items-center gap-2 font-bold">
                    <CheckCircle2 className="size-4 text-emerald-600 dark:text-emerald-400" />
                    <span>Chứng tích đã được lưu giữ vào Hộ Chiếu!</span>
                  </div>
                  <p className="opacity-90">
                    Thời gian đóng dấu:{" "}
                    <strong>
                      {new Date(
                        unlockedMap[selectedSeal.slug].unlockedAt,
                      ).toLocaleString("vi-VN")}
                    </strong>
                  </p>
                  {unlockedMap[selectedSeal.slug].reason && (
                    <p className="opacity-80">
                      Nội dung: {unlockedMap[selectedSeal.slug].reason}
                    </p>
                  )}
                </div>
              ) : (
                <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3.5 text-xs text-amber-950 dark:text-amber-200 space-y-1.5">
                  <div className="flex items-center gap-2 font-bold text-amber-900 dark:text-amber-300">
                    <HelpCircle className="size-4 text-amber-600" />
                    <span>Gợi ý cách mở khóa dấu triện:</span>
                  </div>
                  <p className="leading-relaxed">
                    {selectedSeal.unlockHint}
                  </p>
                </div>
              )}

              {/* Historical Summary */}
              <div className="space-y-1 text-xs">
                <span className="font-bold text-foreground uppercase tracking-wider text-[11px]">
                  Tóm lược lịch sử & quy mô:
                </span>
                <p className="text-muted-foreground leading-relaxed">
                  {selectedSeal.summary} (Xây dựng năm {selectedSeal.constructionYear}, niên hiệu {selectedSeal.reign}).
                </p>
              </div>

              {/* Guiding Question */}
              <div className="rounded-lg border border-border bg-secondary/30 p-3 text-xs space-y-1">
                <span className="font-semibold text-primary block">
                  Câu hỏi định hướng nghiên cứu:
                </span>
                <p className="italic font-serif text-foreground/90">
                  &ldquo;{selectedSeal.guidingQuestion}&rdquo;
                </p>
              </div>
            </div>

            <DialogFooter className="p-4 bg-secondary/20 border-t border-border flex flex-col sm:flex-row gap-2">
              <Link
                href={`/dai-noi/cong-trinh/${selectedSeal.slug}`}
                className="w-full sm:w-auto flex-1"
              >
                <Button className="w-full text-xs font-semibold gap-1.5 bg-primary text-primary-foreground">
                  <FileText className="size-3.5" />
                  <span>
                    {unlockedMap[selectedSeal.slug]
                      ? "Xem Hồ Sơ Di Tích"
                      : "Đến Khảo Sát & Giải Mã"}
                  </span>
                </Button>
              </Link>

              <Link
                href={`/dai-noi?site=${selectedSeal.slug}`}
                className="w-full sm:w-auto"
              >
                <Button variant="outline" className="w-full text-xs gap-1.5">
                  <MapPin className="size-3.5" />
                  <span>Định Vị Bản Đồ</span>
                </Button>
              </Link>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      {/* =========================================================================
          MODAL 2: ROYAL CERTIFICATE OF COMPLETION (A4 Landscape Layout)
         ========================================================================= */}
      <Dialog open={isCertificateOpen} onOpenChange={setIsCertificateOpen}>
        <DialogContent className="max-w-3xl max-h-[95vh] overflow-y-auto p-0 gap-0 border-4 border-[#d4af37] bg-[#fbf7ee] text-[#332211] shadow-2xl">
          {/* Certificate Action Top Bar */}
          <div className="p-3 bg-[#f3ecdc] border-b border-[#d4af37]/50 flex items-center justify-between gap-3 text-xs print:hidden">
            <span className="font-serif font-bold text-amber-900 flex items-center gap-1.5">
              <Award className="size-4 text-amber-700" />
              <span>Chứng Nhận Khảo Cứu Di Sản Cố Đô Huế</span>
            </span>

            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={handleCopyCertCode}
                className="h-7 text-xs gap-1 border-[#d4af37]"
              >
                <Copy className="size-3" />
                <span>{copyCodeSuccess ? "Đã chép!" : "Chép mã"}</span>
              </Button>

              <Button
                size="sm"
                onClick={handlePrintCertificate}
                className="h-7 text-xs gap-1.5 bg-amber-800 hover:bg-amber-900 text-white font-semibold"
              >
                <Printer className="size-3.5" />
                <span>In Chứng Nhận</span>
              </Button>
            </div>
          </div>

          {/* CERTIFICATE BODY (Ornate Royal Decree Style) */}
          <div className="p-8 sm:p-12 relative overflow-hidden text-center space-y-6">
            {/* Double Gold Decorative Border with Corner Ornaments */}
            <div className="absolute inset-4 sm:inset-6 border-2 border-[#b8860b] pointer-events-none rounded-lg" />
            <div className="absolute inset-5 sm:inset-7 border border-[#b8860b]/60 pointer-events-none rounded-md" />

            {/* Corner flourishes */}
            <div className="absolute top-6 left-6 text-xl text-[#b8860b] select-none pointer-events-none">
              ❖
            </div>
            <div className="absolute top-6 right-6 text-xl text-[#b8860b] select-none pointer-events-none">
              ❖
            </div>
            <div className="absolute bottom-6 left-6 text-xl text-[#b8860b] select-none pointer-events-none">
              ❖
            </div>
            <div className="absolute bottom-6 right-6 text-xl text-[#b8860b] select-none pointer-events-none">
              ❖
            </div>

            {/* Certificate Header */}
            <div className="space-y-1 relative z-10 pt-2">
              <p className="font-serif text-[11px] sm:text-xs font-bold uppercase tracking-[0.25em] text-[#8b4513]">
                Trung Tâm Bảo Tồn Di Tích Cố Đô Huế • Dự Án Lưu Niên Sử Kí
              </p>
              <h2 className="font-serif text-2xl sm:text-4xl font-extrabold text-[#7f1d1d] tracking-wider pt-2">
                CHỨNG NHẬN KHẢO CỨU DI SẢN
              </h2>
              <p className="font-serif italic text-xs text-[#8b4513]/80">
                Chứng thư ghi nhận thành tích nghiên cứu thực địa Hoàng Thành & Tử Cấm Thành Huế
              </p>
            </div>

            {/* Honoree Name & Class */}
            <div className="space-y-2 py-4 relative z-10">
              <span className="text-xs uppercase tracking-wider text-[#6b4226] block">
                Trân trọng vinh danh học sinh:
              </span>
              <h3 className="font-serif text-3xl sm:text-4xl font-black text-[#501e1e] underline decoration-[#d4af37] decoration-2 underline-offset-8">
                {studentName}
              </h3>
              <p className="font-serif text-sm font-semibold text-[#6b4226] pt-2">
                Đơn vị: {studentClass}
              </p>
            </div>

            {/* Awarded Title & Achievement */}
            <div className="rounded-xl border border-[#b8860b]/40 bg-[#f5eedf]/80 p-4 max-w-lg mx-auto text-center space-y-1.5 relative z-10">
              <span className="text-[11px] font-serif uppercase tracking-widest text-[#8b4513] block">
                Danh hiệu vinh tặng:
              </span>
              <h4 className="font-serif text-lg sm:text-xl font-black text-[#7f1d1d]">
                {honoraryTitle}
              </h4>
              <p className="text-xs text-[#4a2e1b] leading-relaxed">
                Đã hoàn thành khảo sát và đóng dấu{" "}
                <strong>{progress.unlockedCount}/16 ấn triện hoàng gia</strong> tại các phân khu Trục Trung Tâm, Không Gian Thờ Tự, Tử Cấm Thành và Cung Điển Hoàng Gia.
              </p>
            </div>

            {/* Seal & Verification Signature Block */}
            <div className="pt-4 flex flex-col sm:flex-row items-center justify-between gap-6 max-w-xl mx-auto relative z-10">
              {/* Verification Code */}
              <div className="text-left space-y-1">
                <span className="text-[10px] uppercase font-mono text-[#8b4513] block">
                  Mã số tra cứu:
                </span>
                <span className="font-mono font-bold text-xs bg-amber-900/10 px-2 py-1 rounded border border-[#b8860b]/30 block">
                  {certificateCode}
                </span>
                <span className="text-[10px] text-muted-foreground block">
                  Cấp ngày: {new Date().toLocaleDateString("vi-VN")}
                </span>
              </div>

              {/* Authentic Royal Seal Stamp */}
              <div className="flex flex-col items-center">
                <OfficialProjectSeal size="md" />
                <span className="text-[10px] font-serif text-[#8b4513] mt-1 italic">
                  Ấn giám Hội đồng Chuyên môn
                </span>
              </div>
            </div>
          </div>

          <DialogFooter className="p-4 bg-[#f3ecdc] border-t border-[#d4af37]/50 flex flex-wrap justify-between items-center gap-2 print:hidden">
            <span className="text-xs text-muted-foreground font-serif">
              Lưu Niên — Nền tảng học tập di sản số Hoàng Thành Huế
            </span>
            <div className="flex items-center gap-2">
              <Link href="/dai-noi/chung-nhan">
                <Button
                  variant="outline"
                  size="sm"
                  className="text-xs border-[#b8860b]/60 hover:bg-amber-100 dark:hover:bg-amber-950/40 gap-1 text-[#8b4513]"
                >
                  <ExternalLink className="size-3" />
                  <span>Mở Toàn Màn Hình</span>
                </Button>
              </Link>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsCertificateOpen(false)}
                className="text-xs"
              >
                Đóng
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
