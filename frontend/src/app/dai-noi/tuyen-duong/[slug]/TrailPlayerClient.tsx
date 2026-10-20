"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import Image from "next/image";
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock,
  Compass,
  ExternalLink,
  Eye,
  FileText,
  Footprints,
  GraduationCap,
  HelpCircle,
  Laptop,
  Layers,
  MapPin,
  Maximize2,
  RotateCcw,
  Route,
  Send,
  ShieldAlert,
  Sparkles,
  Target,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ImperialTrail, StudentSubmission } from "@/lib/imperial/map-types";
import StudentSubmissionModal from "@/components/imperial/dossier/StudentSubmissionModal";
import { loadStudentSubmissions } from "@/lib/imperial/submissions-api";
import { RouteHeroSection } from "@/components/imperial/route/RouteHeroSection";
import { RouteJourneyStrip } from "@/components/imperial/route/RouteJourneyStrip";
import { StopImageGallery } from "@/components/imperial/route/StopImageGallery";
import { RouteOnboardingGuide } from "@/components/imperial/route/RouteOnboardingGuide";
import { ImageGapReportModal } from "@/components/imperial/route/ImageGapReportModal";

interface TrailPlayerClientProps {
  trail: ImperialTrail;
}

export default function TrailPlayerClient({ trail }: TrailPlayerClientProps) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isVirtualFieldwork, setIsVirtualFieldwork] = useState(true);
  const [isSubmissionModalOpen, setIsSubmissionModalOpen] = useState(false);
  const [completedStops, setCompletedStops] = useState<number[]>([]);
  const [isGuideOpen, setIsGuideOpen] = useState(false);
  const [isImageReportOpen, setIsImageReportOpen] = useState(false);

  const currentStop = trail.stops[currentStepIndex] || trail.stops[0];
  const progressPercent = Math.round(((currentStepIndex + 1) / trail.stops.length) * 100);

  // Check if current stop has a saved submission in storage
  const [savedSubmissions, setSavedSubmissions] = useState<StudentSubmission[]>(() => {
    return loadStudentSubmissions();
  });

  const completedStopsCount = useMemo(() => {
    const doneSet = new Set(completedStops);
    savedSubmissions.forEach((s) => {
      const idx = trail.stops.findIndex((stop) => stop.monument_slug === s.monument_slug);
      if (idx !== -1) doneSet.add(idx);
    });
    return doneSet.size;
  }, [completedStops, savedSubmissions, trail.stops]);

  // First-time onboarding trigger
  React.useEffect(() => {
    try {
      const dismissed = localStorage.getItem("luuniensuki_route_onboarding_dismissed");
      if (!dismissed) {
        setIsGuideOpen(true);
        localStorage.setItem("luuniensuki_route_onboarding_dismissed", "true");
      }
    } catch {}
  }, []);

  const currentStopSubmission = useMemo(() => {
    return savedSubmissions.find(
      (s) =>
        s.monument_slug === currentStop.monument_slug ||
        (s.trail_slug === trail.slug && s.monument_slug === currentStop.monument_slug),
    );
  }, [savedSubmissions, currentStop.monument_slug, trail.slug]);

  const handleNextStep = () => {
    if (currentStepIndex < trail.stops.length - 1) {
      setCurrentStepIndex((prev) => prev + 1);
    }
  };

  const handlePrevStep = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex((prev) => prev - 1);
    }
  };

  const handleSubmissionSuccess = (newSub: StudentSubmission) => {
    setSavedSubmissions((prev) => [newSub, ...prev]);
    if (!completedStops.includes(currentStepIndex)) {
      setCompletedStops((prev) => [...prev, currentStepIndex]);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Top Navigation & Stepper Header */}
      <header className="sticky top-14 z-30 border-b border-border/70 bg-card/95 backdrop-blur-md">
        <div className="mx-auto max-w-7xl px-4 lg:px-8 py-3 space-y-3">
          {/* Breadcrumb & Actions */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-xs">
              <Button asChild variant="ghost" size="sm" className="h-8 gap-1.5 px-2 text-muted-foreground hover:text-foreground">
                <Link href="/dai-noi/tuyen-duong">
                  <ArrowLeft className="h-4 w-4" />
                  <span>Danh sách tuyến</span>
                </Link>
              </Button>
              <span className="text-muted-foreground/40">/</span>
              <span className="font-semibold text-foreground truncate max-w-xs sm:max-w-md">
                {trail.title}
              </span>
            </div>

            {/* Mode Switch: Real Fieldwork vs Virtual Classroom Fieldwork */}
            <div className="flex items-center gap-2">
              <div className="flex items-center rounded-xl border border-border/70 bg-secondary/50 p-1">
                <button
                  type="button"
                  onClick={() => setIsVirtualFieldwork(false)}
                  className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-semibold transition-colors ${
                    !isVirtualFieldwork
                      ? "bg-background text-foreground shadow-xs"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Footprints className="h-3.5 w-3.5 text-primary" />
                  <span className="hidden sm:inline">Thực địa hiện trường</span>
                  <span className="sm:hidden">Hiện trường</span>
                </button>
                <button
                  type="button"
                  onClick={() => setIsVirtualFieldwork(true)}
                  className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-semibold transition-colors ${
                    isVirtualFieldwork
                      ? "bg-primary text-primary-foreground shadow-xs"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Laptop className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Thực địa ảo / Lớp học</span>
                  <span className="sm:hidden">Khảo sát ảo</span>
                </button>
              </div>

              <Button asChild variant="outline" size="sm" className="h-8 text-xs gap-1 hidden md:flex">
                <Link href="/dai-noi/giao-vien">
                  <GraduationCap className="h-3.5 w-3.5 text-primary" />
                  <span>Chấm bài (GV)</span>
                </Link>
              </Button>
            </div>
          </div>

          {/* Stepper Tabs Bar */}
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2 overflow-x-auto pb-1 max-w-full scrollbar-thin">
              {trail.stops.map((stop, idx) => {
                const isActive = idx === currentStepIndex;
                const isDone = completedStops.includes(idx) || savedSubmissions.some((s) => s.monument_slug === stop.monument_slug);

                return (
                  <button
                    key={stop.monument_slug}
                    type="button"
                    onClick={() => setCurrentStepIndex(idx)}
                    className={`flex items-center gap-2 whitespace-nowrap rounded-xl px-3 py-1.5 text-xs font-semibold transition-all border ${
                      isActive
                        ? "border-primary bg-primary/10 text-primary ring-2 ring-primary/20"
                        : isDone
                        ? "border-emerald-500/30 bg-emerald-500/5 text-emerald-700 dark:text-emerald-400"
                        : "border-border/60 bg-background/50 text-muted-foreground hover:bg-secondary/70 hover:text-foreground"
                    }`}
                  >
                    <span
                      className={`flex h-5 w-5 items-center justify-center rounded-full text-[11px] font-bold ${
                        isActive
                          ? "bg-primary text-primary-foreground"
                          : isDone
                          ? "bg-emerald-600 text-white"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {isDone ? <CheckCircle2 className="h-3.5 w-3.5" /> : idx + 1}
                    </span>
                    <span>{stop.monument_name_vi}</span>
                  </button>
                );
              })}
            </div>

            <div className="hidden lg:flex items-center gap-2 text-xs font-mono text-muted-foreground shrink-0">
              <span>Trạm {currentStepIndex + 1}/{trail.stops.length}</span>
              <span className="w-16 h-2 rounded-full bg-secondary overflow-hidden">
                <span
                  className="block h-full bg-primary transition-all duration-300"
                  style={{ width: `${progressPercent}%` }}
                />
              </span>
              <span>{progressPercent}%</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Learning Workspace */}
      <main className="flex-1 mx-auto max-w-7xl w-full px-4 py-6 lg:px-8">
        {/* Visual Hero Section */}
        <RouteHeroSection
          trail={trail}
          completedStopsCount={completedStopsCount}
          onOpenGuide={() => setIsGuideOpen(true)}
          onOpenImageReport={() => setIsImageReportOpen(true)}
        />

        {/* Route Journey Strip with Image Thumbnails */}
        <RouteJourneyStrip
          stops={trail.stops}
          currentIndex={currentStepIndex}
          completedStops={completedStops}
          savedSubmissionsSlugs={savedSubmissions.map((s) => s.monument_slug).filter((slug): slug is string => Boolean(slug))}
          onSelectStop={(idx) => setCurrentStepIndex(idx)}
          className="mb-8"
        />

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
          {/* LEFT COLUMN: Stop Image Gallery & Aerial Map Locator (lg:col-span-5) */}
          <div className="space-y-6 lg:col-span-5">
            {/* Visual Heritage Stop Gallery (with hotspots and missing image notice) */}
            <StopImageGallery
              monumentSlug={currentStop.monument_slug}
              monumentNameVi={currentStop.monument_name_vi}
              onOpenReportModal={() => setIsImageReportOpen(true)}
            />

            {/* Aerial Map Stop Locator */}
            <Card className="overflow-hidden border border-border/80 bg-card rounded-2xl shadow-xs">
              <CardHeader className="p-4 pb-2 bg-secondary/20 border-b border-border/50 flex flex-row items-center justify-between">
                <div className="flex items-center gap-2">
                  <Compass className="h-4 w-4 text-primary" />
                  <span className="font-serif text-sm font-bold text-foreground">
                    Định vị tọa độ trên Bản đồ không ảnh
                  </span>
                </div>
                <Badge variant="outline" className="text-[11px] font-mono border-primary/30">
                  U: {(currentStop.u * 100).toFixed(1)}% • V: {(currentStop.v * 100).toFixed(1)}%
                </Badge>
              </CardHeader>

              <CardContent className="p-0">
                {/* Aerial Map Canvas Container */}
                <div className="relative aspect-4/3 w-full bg-stone-950 overflow-hidden select-none">
                  <Image
                    src="/assets/imperial/maps/dai-noi-aerial-v1.webp"
                    alt="Bản đồ không ảnh Đại Nội Huế"
                    fill
                    sizes="(max-width: 1024px) 100vw, 40vw"
                    className="object-cover opacity-90 transition-transform duration-500"
                    priority
                  />

                  {/* SVG connecting route line between trail stops */}
                  <svg className="absolute inset-0 h-full w-full pointer-events-none z-10">
                    <polyline
                      points={trail.stops
                        .map((s) => `${s.u * 100}%,${s.v * 100}%`)
                        .join(" ")}
                      fill="none"
                      stroke="rgba(217, 119, 6, 0.6)"
                      strokeWidth="2.5"
                      strokeDasharray="4 3"
                    />
                  </svg>

                  {/* Markers for all stops on trail */}
                  {trail.stops.map((stop, sIdx) => {
                    const isStopActive = sIdx === currentStepIndex;
                    const isStopDone = completedStops.includes(sIdx);

                    return (
                      <button
                        key={stop.monument_slug}
                        type="button"
                        onClick={() => setCurrentStepIndex(sIdx)}
                        style={{
                          left: `${stop.u * 100}%`,
                          top: `${stop.v * 100}%`,
                          transform: "translate(-50%, -50%)",
                        }}
                        className="absolute z-20 group focus:outline-none"
                        title={`Trạm ${sIdx + 1}: ${stop.monument_name_vi}`}
                      >
                        {/* Pulsing ring for active stop */}
                        {isStopActive && (
                          <span className="absolute -inset-2 rounded-full bg-amber-500/30 animate-ping pointer-events-none" />
                        )}

                        <div
                          className={`flex items-center justify-center rounded-full border-2 transition-transform duration-200 ${
                            isStopActive
                              ? "h-8 w-8 bg-amber-500 border-white text-stone-950 font-bold shadow-lg scale-110 ring-4 ring-amber-500/40"
                              : isStopDone
                              ? "h-6 w-6 bg-emerald-600 border-white text-white font-semibold shadow-md"
                              : "h-6 w-6 bg-stone-900/90 border-amber-400/80 text-amber-300 font-medium hover:scale-110"
                          }`}
                        >
                          <span className="text-xs">{sIdx + 1}</span>
                        </div>

                        {/* Hover/Active label */}
                        <div
                          className={`absolute top-full mt-1 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-md px-2 py-0.5 text-[10px] font-bold shadow-md transition-opacity pointer-events-none ${
                            isStopActive
                              ? "opacity-100 bg-amber-500 text-stone-950 z-30"
                              : "opacity-0 group-hover:opacity-100 bg-stone-900/95 text-stone-100 border border-stone-700 z-20"
                          }`}
                        >
                          {stop.monument_name_vi}
                        </div>
                      </button>
                    );
                  })}

                  {/* Active stop overlay badge */}
                  <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between rounded-lg bg-stone-900/80 backdrop-blur-md px-3 py-1.5 text-xs text-stone-200 border border-stone-700/60 z-20">
                    <span className="font-semibold text-amber-400">
                      Trạm {currentStepIndex + 1}: {currentStop.monument_name_vi}
                    </span>
                    <Link
                      href={`/dai-noi?focus=${currentStop.monument_slug}`}
                      className="text-[11px] text-amber-300 hover:underline flex items-center gap-1"
                    >
                      <span>Mở bản đồ lớn</span>
                      <ExternalLink className="h-3 w-3" />
                    </Link>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Virtual Fieldwork Panel (when active or always accessible) */}
            <Card className="border border-border/80 bg-card rounded-2xl overflow-hidden space-y-0">
              <CardHeader className="p-4 bg-secondary/15 border-b border-border/50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Laptop className="h-4 w-4 text-primary" />
                    <CardTitle className="text-sm font-bold font-serif text-foreground">
                      Tư liệu Thực địa Ảo (Virtual Fieldwork)
                    </CardTitle>
                  </div>
                  <Badge variant="outline" className="text-[10px]">
                    Lớp học từ xa
                  </Badge>
                </div>
              </CardHeader>

              <CardContent className="p-4 space-y-4">
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {currentStop.virtual_fieldwork.overview_text}
                </p>

                {/* Archival Evidence Clues */}
                <div className="rounded-xl border border-primary/20 bg-primary/5 p-3.5 space-y-2">
                  <span className="text-[11px] font-bold uppercase tracking-wide text-primary flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5" />
                    Dấu vết lịch sử cần nhận diện tại hiện trường:
                  </span>
                  <ul className="space-y-1.5 text-xs text-muted-foreground">
                    {currentStop.virtual_fieldwork.historical_clues.map((clue, cIdx) => (
                      <li key={cIdx} className="flex items-start gap-2">
                        <span className="h-1.5 w-1.5 rounded-full bg-primary mt-1.5 shrink-0" />
                        <span>{clue}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="pt-1 flex items-center justify-between text-xs text-muted-foreground">
                  <span className="text-[11px]">Cố đô Huế • UNESCO 1993</span>
                  <Link
                    href={`/dai-noi/cong-trinh/${currentStop.monument_slug}`}
                    className="inline-flex items-center gap-1 font-semibold text-primary hover:underline"
                  >
                    <span>Xem Hồ sơ Di tích đầy đủ</span>
                    <ExternalLink className="h-3.5 w-3.5" />
                  </Link>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* RIGHT COLUMN: Pedagogical Inquiry Workstation (lg:col-span-7) */}
          <div className="space-y-6 lg:col-span-7">
            {/* Monument & Inquiry Header Card */}
            <Card className="border-2 border-primary/30 bg-card rounded-2xl overflow-hidden shadow-sm">
              <CardHeader className="p-6 pb-4 bg-secondary/20 border-b border-border/60 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <Badge className="bg-primary/10 text-primary border-primary/25 font-semibold text-xs">
                    Trạm dừng số {currentStepIndex + 1} / {trail.stops.length}
                  </Badge>
                  <Link
                    href={`/dai-noi/cong-trinh/${currentStop.monument_slug}`}
                    className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
                  >
                    <span>Tra cứu hồ sơ 7 mục</span>
                    <ExternalLink className="h-3.5 w-3.5" />
                  </Link>
                </div>

                <div>
                  <div className="flex items-baseline gap-2.5">
                    <h2 className="font-serif text-2xl font-bold tracking-tight text-foreground md:text-3xl">
                      {currentStop.monument_name_vi}
                    </h2>
                  </div>
                  <p className="text-xs font-medium text-muted-foreground mt-0.5">
                    {currentStop.title}
                  </p>
                </div>
              </CardHeader>

              <CardContent className="p-6 space-y-6">
                {/* Driving Inquiry Question Box */}
                <div className="rounded-2xl border border-primary/30 bg-primary/5 p-5 space-y-2.5">
                  <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-primary">
                    <HelpCircle className="h-4 w-4" />
                    <span>Câu hỏi định hướng phát vấn (Driving Inquiry Question):</span>
                  </div>
                  <p className="font-serif text-lg font-bold text-foreground leading-snug md:text-xl">
                    &ldquo;{currentStop.inquiry_question}&rdquo;
                  </p>
                </div>

                {/* Step Prompt */}
                <div className="space-y-2">
                  <h3 className="text-xs font-bold uppercase tracking-wide text-foreground flex items-center gap-1.5">
                    <Target className="h-3.5 w-3.5 text-primary" />
                    <span>Đề dẫn khảo sát hiện trường:</span>
                  </h3>
                  <p className="text-sm leading-relaxed text-muted-foreground bg-secondary/20 p-4 rounded-xl border border-border/60">
                    {currentStop.step_prompt}
                  </p>
                </div>

                {/* Required Primary Sources to Observe */}
                <div className="space-y-3">
                  <h3 className="text-xs font-bold uppercase tracking-wide text-foreground flex items-center gap-1.5">
                    <BookOpen className="h-3.5 w-3.5 text-primary" />
                    <span>Tư liệu lịch sử gốc bắt buộc quan sát & trích dẫn:</span>
                  </h3>

                  <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                    {currentStop.required_sources.map((src, idx) => (
                      <div
                        key={idx}
                        className="rounded-xl border border-border/80 bg-background p-3.5 text-xs space-y-1.5 hover:border-primary/40 transition-colors shadow-2xs"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-foreground line-clamp-1">
                            {src.title}
                          </span>
                          <Badge variant="secondary" className="text-[10px] uppercase font-mono">
                            {src.type === "chronicle" ? "Chính sử" : src.type === "archival_photo" ? "Ảnh tư liệu" : "Văn khắc"}
                          </Badge>
                        </div>
                        <p className="text-[11px] text-muted-foreground leading-relaxed italic">
                          &ldquo;{src.citation}&rdquo;
                        </p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Observation Points Checklist */}
                <div className="space-y-2.5">
                  <h3 className="text-xs font-bold uppercase tracking-wide text-foreground flex items-center gap-1.5">
                    <Eye className="h-3.5 w-3.5 text-primary" />
                    <span>Các điểm quan sát thực địa cốt lõi:</span>
                  </h3>
                  <div className="space-y-1.5">
                    {currentStop.observation_points.map((pt, pIdx) => (
                      <div
                        key={pIdx}
                        className="flex items-start gap-2.5 rounded-lg border border-border/60 bg-secondary/15 p-2.5 text-xs text-foreground"
                      >
                        <CheckCircle2 className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        <span className="leading-relaxed">{pt}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Embedded Inquiry Task & Submission Action */}
                <div className="rounded-2xl border-2 border-dashed border-primary/40 bg-secondary/20 p-5 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <GraduationCap className="h-5 w-5 text-primary" />
                      <span className="font-serif text-base font-bold text-foreground">
                        Nhiệm vụ kết luận khảo sát (M-E-E)
                      </span>
                    </div>
                    <Badge variant="outline" className="text-[11px] font-semibold border-primary/30">
                      Rubric S1-S4 • 12 Điểm
                    </Badge>
                  </div>

                  <p className="text-xs text-muted-foreground leading-relaxed">
                    <strong>Yêu cầu:</strong> {currentStop.task_prompt}
                  </p>

                  {/* Submission status feedback card if already submitted */}
                  {currentStopSubmission ? (
                    <div className="rounded-xl border border-emerald-500/40 bg-emerald-500/10 p-4 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-emerald-800 dark:text-emerald-300 flex items-center gap-1.5">
                          <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                          Đã nộp bài làm khảo sát cho trạm này!
                        </span>
                        {currentStopSubmission.status === "graded" && (
                          <Badge className="bg-emerald-600 text-white text-[11px]">
                            Điểm: {currentStopSubmission.scores?.total}/12 ({currentStopSubmission.scores?.normalized_10}/10)
                          </Badge>
                        )}
                      </div>

                      <p className="text-xs text-foreground italic border-l-2 border-emerald-500 pl-2">
                        &ldquo;{currentStopSubmission.claim}&rdquo;
                      </p>

                      <div className="flex justify-end pt-1">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setIsSubmissionModalOpen(true)}
                          className="text-xs h-7 border-emerald-500/40 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-500/20"
                        >
                          Cập nhật / Xem bài nộp
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <Button
                      onClick={() => setIsSubmissionModalOpen(true)}
                      className="w-full gap-2 font-semibold py-5 text-sm shadow-md"
                    >
                      <Send className="h-4 w-4" />
                      <span>Làm bài & Nộp kết luận khảo sát M-E-E</span>
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Bottom Step Controller */}
            <div className="flex items-center justify-between gap-4 pt-2">
              <Button
                variant="outline"
                onClick={handlePrevStep}
                disabled={currentStepIndex === 0}
                className="gap-2 text-xs font-semibold"
              >
                <ChevronLeft className="h-4 w-4" />
                <span>Trạm trước</span>
              </Button>

              <span className="text-xs text-muted-foreground font-mono">
                {currentStepIndex + 1} / {trail.stops.length}
              </span>

              {currentStepIndex < trail.stops.length - 1 ? (
                <Button
                  onClick={handleNextStep}
                  className="gap-2 text-xs font-semibold"
                >
                  <span>Trạm tiếp theo</span>
                  <ChevronRight className="h-4 w-4" />
                </Button>
              ) : (
                <Button
                  asChild
                  className="gap-2 text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white"
                >
                  <Link href="/dai-noi/tuyen-duong">
                    <CheckCircle2 className="h-4 w-4" />
                    <span>Hoàn thành tuyến học</span>
                  </Link>
                </Button>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Student Submission Modal */}
      <StudentSubmissionModal
        open={isSubmissionModalOpen}
        onOpenChange={setIsSubmissionModalOpen}
        monumentSlug={currentStop.monument_slug}
        monumentName={currentStop.monument_name_vi}
        trailSlug={trail.slug}
        trailTitle={trail.title}
        taskPrompt={currentStop.task_prompt}
        expectedEvidence={currentStop.expected_evidence}
        availableSources={currentStop.required_sources.map((s) => ({
          title: s.title,
          citation: s.citation,
        }))}
        onSuccess={handleSubmissionSuccess}
      />

      {/* Onboarding Guide for First-time Learners */}
      <RouteOnboardingGuide
        isOpen={isGuideOpen}
        onClose={() => setIsGuideOpen(false)}
        trailTitle={trail.title}
      />

      {/* Image Completeness & Gap Audit Report Modal */}
      <ImageGapReportModal
        isOpen={isImageReportOpen}
        onClose={() => setIsImageReportOpen(false)}
      />
    </div>
  );
}
