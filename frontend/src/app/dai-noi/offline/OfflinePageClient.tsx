"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  WifiOff,
  Wifi,
  Printer,
  FileSpreadsheet,
  Download,
  BookOpen,
  MapPin,
  Stamp,
  Award,
  Layers,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import PrintWorksheetModal from "@/components/imperial/print/PrintWorksheetModal";
import { FALLBACK_SITES, FALLBACK_ZONES } from "@/lib/imperial/fallback-data";
import { usePassportProgress } from "@/lib/imperial/passport-storage";
import { cn } from "@/lib/utils";

export default function OfflinePageClient() {
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [isPrintModalOpen, setIsPrintModalOpen] = useState(false);
  const [isTeacherMode, setIsTeacherMode] = useState(false);
  const { unlockedCount, totalSeals } = usePassportProgress();

  useEffect(() => {
    if (typeof window !== "undefined") {
      setIsOnline(navigator.onLine);

      const handleOnline = () => setIsOnline(true);
      const handleOffline = () => setIsOnline(false);

      window.addEventListener("online", handleOnline);
      window.addEventListener("offline", handleOffline);

      return () => {
        window.removeEventListener("online", handleOnline);
        window.removeEventListener("offline", handleOffline);
      };
    }
  }, []);

  return (
    <div className="min-h-screen bg-background selection:bg-primary/20 selection:text-primary">
      <main className="mx-auto max-w-6xl w-full px-4 py-8 sm:px-6 space-y-8">
        {/* Network & Offline Status Banner */}
        <div
          className={cn(
            "rounded-2xl border p-4 sm:p-6 transition-all flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4",
            isOnline
              ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-950 dark:text-emerald-200"
              : "border-amber-500/40 bg-amber-500/15 text-amber-950 dark:text-amber-200",
          )}
        >
          <div className="flex items-center gap-3.5">
            <div
              className={cn(
                "flex h-12 w-12 shrink-0 items-center justify-center rounded-xl",
                isOnline
                  ? "bg-emerald-600 text-white"
                  : "bg-amber-600 text-white animate-pulse",
              )}
            >
              {isOnline ? <Wifi className="size-6" /> : <WifiOff className="size-6" />}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-serif text-lg sm:text-xl font-bold">
                  {isOnline ? "Hệ thống đang kết nối Trực tuyến" : "Chế độ Ngoại tuyến (Offline-First)"}
                </h1>
                <Badge
                  variant={isOnline ? "default" : "destructive"}
                  className="text-[11px] font-semibold uppercase tracking-wider"
                >
                  {isOnline ? "Online" : "Offline"}
                </Badge>
              </div>
              <p className="text-xs sm:text-sm opacity-85 mt-0.5">
                {isOnline
                  ? "Toàn bộ dữ liệu 16 công trình và phiếu học tập đã được lưu sẵn trong bộ nhớ đệm (Cache Storage). Bạn có thể học tập bình thường ngay cả khi mất sóng viễn thông tại Cố đô."
                  : "Bạn đang ở khu vực sóng yếu tại Hoàng thành. Tất cả dữ liệu tư liệu, hình ảnh và bài học đã lưu sẵn để bạn tiếp tục điền dã không gián đoạn."}
              </p>
            </div>
          </div>

          <div className="flex shrink-0 items-center gap-2 w-full sm:w-auto">
            <Button
              onClick={() => {
                setIsTeacherMode(false);
                setIsPrintModalOpen(true);
              }}
              className="gap-2 bg-primary text-primary-foreground text-xs font-semibold h-9 flex-1 sm:flex-initial"
            >
              <Printer className="size-4" />
              <span>Xuất phiếu in A4</span>
            </Button>
          </div>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Card 1: Printable Fieldwork Worksheet */}
          <Card className="border-border/80 bg-card hover:shadow-md transition-shadow">
            <CardContent className="p-6 space-y-4">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary border border-primary/20">
                <FileSpreadsheet className="size-5" />
              </div>
              <div className="space-y-1.5">
                <h2 className="font-serif text-lg font-bold text-foreground">
                  Phiếu Học Tập Thực Địa 4 Cột
                </h2>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Thiết kế chuẩn A4 ngang/dọc phục vụ nộp hồ sơ chuyên môn theo Công văn 5512/BGDĐT. Tích hợp bảng truy chứng M-E-E và mã QR định vị bản đồ số.
                </p>
              </div>
              <div className="pt-2 flex flex-col gap-2">
                <Button
                  onClick={() => {
                    setIsTeacherMode(false);
                    setIsPrintModalOpen(true);
                  }}
                  variant="outline"
                  className="w-full justify-center gap-2 text-xs font-semibold h-9"
                >
                  <Printer className="size-3.5 text-primary" />
                  <span>Phiếu học sinh (Trống)</span>
                </Button>
                <Button
                  onClick={() => {
                    setIsTeacherMode(true);
                    setIsPrintModalOpen(true);
                  }}
                  variant="ghost"
                  className="w-full justify-center gap-2 text-xs font-medium h-8 text-muted-foreground hover:text-foreground"
                >
                  <Sparkles className="size-3.5 text-amber-500" />
                  <span>Phiếu đáp án Giáo viên (Teacher Key)</span>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Card 2: Digital Heritage Passport */}
          <Card className="border-border/80 bg-card hover:shadow-md transition-shadow">
            <CardContent className="p-6 space-y-4">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                <Stamp className="size-5" />
              </div>
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <h2 className="font-serif text-lg font-bold text-foreground">
                    Hộ Chiếu Di Sản & Ấn Triện
                  </h2>
                  <Badge variant="outline" className="font-mono text-xs font-bold text-amber-600">
                    {unlockedCount}/{totalSeals}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Lưu trữ các dấu ấn triện hoàng triều đã đóng qua các trạm nghiên cứu di tích. Hoạt động offline hoàn toàn nhờ cơ chế lưu trữ IndexedDB/LocalStorage.
                </p>
              </div>
              <div className="pt-2">
                <Button asChild className="w-full justify-center gap-2 text-xs font-semibold h-9" variant="outline">
                  <Link href="/dai-noi/ho-chieu">
                    <Stamp className="size-3.5 text-amber-600" />
                    <span>Xem Sổ Hộ Chiếu ({unlockedCount}/{totalSeals})</span>
                  </Link>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Card 3: Certificate of Completion */}
          <Card className="border-border/80 bg-card hover:shadow-md transition-shadow">
            <CardContent className="p-6 space-y-4">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-red-600/10 text-red-600 dark:text-red-400 border border-red-600/20">
                <Award className="size-5" />
              </div>
              <div className="space-y-1.5">
                <h2 className="font-serif text-lg font-bold text-foreground">
                  Chứng Nhận Hoàng Triều
                </h2>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Bản Chứng nhận vinh danh Nhà Khảo Cứu Trẻ Di Sản Cố Đô Huế. Tích hợp hoa văn long vân triều Nguyễn, mộc son đỏ và mã xác thực trực tuyến.
                </p>
              </div>
              <div className="pt-2">
                <Button asChild className="w-full justify-center gap-2 text-xs font-semibold h-9" variant="outline">
                  <Link href="/dai-noi/chung-nhan">
                    <Award className="size-3.5 text-red-600" />
                    <span>Xem & Xuất Chứng Nhận</span>
                  </Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Offline Cache 16 Monuments Directory */}
        <div className="space-y-4 pt-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="font-serif text-xl sm:text-2xl font-bold text-foreground">
                Danh Mục 16 Công Trình Sẵn Sàng Ngoại Tuyến
              </h2>
              <p className="text-xs sm:text-sm text-muted-foreground">
                Tất cả hồ sơ di tích, trích đoạn sử liệu chính văn và câu hỏi nghiên cứu đều đọc trực tiếp từ bộ nhớ cục bộ.
              </p>
            </div>
            <Button asChild variant="outline" size="sm" className="gap-2 text-xs">
              <Link href="/dai-noi">
                <MapPin className="size-3.5 text-primary" />
                <span>Mở Bản Đồ Không Ảnh</span>
              </Link>
            </Button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {FALLBACK_SITES.map((site, index) => {
              const zone = FALLBACK_ZONES.find((z) => z.slug === site.zone_slug);
              return (
                <Link
                  key={site.id}
                  href={`/dai-noi/cong-trinh/${site.slug}`}
                  className="group block rounded-xl border border-border/80 bg-card p-4 transition-all hover:border-primary/50 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-md bg-secondary text-[11px] font-bold text-muted-foreground group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                      {index + 1}
                    </span>
                    <Badge variant="outline" className="text-[10px] font-normal text-muted-foreground">
                      {zone?.title_vi || "Đại Nội"}
                    </Badge>
                  </div>

                  <div className="mt-3 space-y-1">
                    <h3 className="font-serif text-sm font-bold text-foreground group-hover:text-primary transition-colors">
                      {site.name_vi}
                    </h3>
                    <p className="text-[11px] text-muted-foreground line-clamp-2 leading-relaxed">
                      {site.description_vi || site.historical_summary}
                    </p>
                  </div>

                  <div className="mt-3 flex items-center gap-1.5 text-[11px] font-semibold text-primary">
                    <span>Xem hồ sơ di tích</span>
                    <span className="transition-transform group-hover:translate-x-0.5">→</span>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Print Modal Dialog */}
        <PrintWorksheetModal
          open={isPrintModalOpen}
          onOpenChange={setIsPrintModalOpen}
          initialTeacherMode={isTeacherMode}
        />
      </main>
    </div>
  );
}
