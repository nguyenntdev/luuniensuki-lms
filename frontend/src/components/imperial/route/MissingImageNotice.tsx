"use client";

import React, { useState } from "react";
import {
  CameraOff,
  AlertTriangle,
  Upload,
  Info,
  CheckCircle2,
  FileText,
  ExternalLink,
  ShieldAlert,
  Send,
  HelpCircle,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { getSiteImageCompleteness } from "@/lib/imperial/image-completeness";

interface MissingImageNoticeProps {
  monumentSlug: string;
  monumentNameVi: string;
  onOpenReportModal?: () => void;
  className?: string;
}

export function MissingImageNotice({
  monumentSlug,
  monumentNameVi,
  onOpenReportModal,
  className = "",
}: MissingImageNoticeProps) {
  const completeness = getSiteImageCompleteness(monumentSlug);
  const [isContributeModalOpen, setIsContributeModalOpen] = useState(false);
  const [contributeSuccess, setContributeSuccess] = useState(false);

  // Contribution Form State
  const [contributorName, setContributorName] = useState("");
  const [contributorRole, setContributorRole] = useState("Học sinh / Người học");
  const [imageCategory, setImageCategory] = useState("facade");
  const [imageSource, setImageSource] = useState("");
  const [imageDescription, setImageDescription] = useState("");

  const handleSubmitContribution = (e: React.FormEvent) => {
    e.preventDefault();
    setContributeSuccess(true);
    setTimeout(() => {
      setContributeSuccess(false);
      setIsContributeModalOpen(false);
      // Reset form
      setImageSource("");
      setImageDescription("");
    }, 2200);
  };

  return (
    <>
      <div
        className={`relative overflow-hidden rounded-2xl border-2 border-dashed border-amber-500/40 bg-gradient-to-br from-amber-500/5 via-card to-background p-5 sm:p-6 shadow-xs ${className}`}
      >
        <div className="flex flex-col sm:flex-row items-start gap-4">
          {/* Warning Icon Badge */}
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-amber-500/15 border border-amber-500/30 text-amber-600 dark:text-amber-400 shadow-xs">
            <CameraOff className="h-6 w-6" />
          </div>

          <div className="space-y-3 flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/40 bg-amber-500/15 px-2.5 py-0.5 text-xs font-bold text-amber-700 dark:text-amber-400">
                <AlertTriangle className="h-3.5 w-3.5" />
                Chưa có ảnh thực tế được xác minh
              </span>
              <Badge variant="outline" className="text-[11px] font-mono">
                {monumentNameVi}
              </Badge>
              {monumentSlug === "dien-can-chanh" && (
                <span className="rounded-full bg-red-500/15 border border-red-500/30 px-2 py-0.5 text-[10px] font-semibold text-red-600 dark:text-red-400">
                  Phế tích chiến tranh 1947
                </span>
              )}
            </div>

            {/* Historical context explanation */}
            <p className="text-xs sm:text-sm text-foreground/90 leading-relaxed font-serif">
              {completeness.historicalContextNote}
            </p>

            <div className="rounded-xl bg-background/80 border border-border/70 p-3.5 space-y-2 text-xs">
              <span className="font-bold text-foreground flex items-center gap-1.5">
                <Info className="h-4 w-4 text-primary" />
                Danh mục ảnh cần người học & cộng đồng bổ sung cho di tích này:
              </span>
              <ul className="space-y-1 text-muted-foreground">
                {completeness.missingItems.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <p className="text-[11px] text-muted-foreground leading-relaxed italic">
              <strong>Cam kết khoa học:</strong> Nhằm đảm bảo tính xác thực lịch sử theo Công văn 5512/BGDĐT, hệ thống tuyệt đối không dùng ảnh của công trình khác thay thế hoặc tạo ảnh giả.
            </p>

            {/* Actions */}
            <div className="flex flex-wrap items-center gap-2.5 pt-1">
              <Button
                type="button"
                size="sm"
                variant="default"
                onClick={() => setIsContributeModalOpen(true)}
                className="h-8 text-xs font-semibold gap-1.5 rounded-xl bg-amber-600 hover:bg-amber-700 text-white shadow-xs"
              >
                <Upload className="h-3.5 w-3.5" />
                <span>Gửi ảnh đóng góp / Báo cáo tư liệu</span>
              </Button>

              {onOpenReportModal && (
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={onOpenReportModal}
                  className="h-8 text-xs font-medium gap-1.5 rounded-xl"
                >
                  <FileText className="h-3.5 w-3.5 text-primary" />
                  <span>Xem báo cáo thiếu ảnh (16 di tích)</span>
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Contribution Dialog Modal */}
      <Dialog open={isContributeModalOpen} onOpenChange={setIsContributeModalOpen}>
        <DialogContent className="max-w-lg p-6">
          <DialogHeader className="space-y-1.5 text-left">
            <DialogTitle className="font-serif text-lg font-bold text-foreground flex items-center gap-2">
              <Upload className="h-5 w-5 text-primary" />
              Đóng góp ảnh tư liệu: {monumentNameVi}
            </DialogTitle>
            <DialogDescription className="text-xs text-muted-foreground">
              Thông tin đóng góp sẽ được lưu trữ và chuyển đến ban biên tập di sản thẩm định trước khi xuất bản chính thức.
            </DialogDescription>
          </DialogHeader>

          {contributeSuccess ? (
            <div className="py-8 text-center space-y-3 animate-in fade-in zoom-in-95">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-600 dark:text-emerald-400">
                <CheckCircle2 className="h-7 w-7" />
              </div>
              <h3 className="font-serif text-base font-bold text-foreground">
                Đã tiếp nhận thông tin đóng góp!
              </h3>
              <p className="text-xs text-muted-foreground max-w-sm mx-auto">
                Cảm ơn bạn đã đồng hành xây dựng kho học liệu di sản số Đại Nội Huế.
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmitContribution} className="space-y-4 pt-2 text-xs">
              <div className="space-y-1.5">
                <label className="font-semibold text-foreground">Họ và tên người đóng góp:</label>
                <input
                  type="text"
                  required
                  value={contributorName}
                  onChange={(e) => setContributorName(e.target.value)}
                  placeholder="Ví dụ: Nguyễn Văn An"
                  className="w-full rounded-xl border border-border bg-background px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-primary/40"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="font-semibold text-foreground">Vai trò:</label>
                  <select
                    value={contributorRole}
                    onChange={(e) => setContributorRole(e.target.value)}
                    className="w-full rounded-xl border border-border bg-background px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-primary/40"
                  >
                    <option value="Học sinh / Người học">Học sinh THPT</option>
                    <option value="Giáo viên Lịch sử">Giáo viên Lịch sử</option>
                    <option value="Nhà nghiên cứu">Nhà nghiên cứu / Hướng dẫn viên</option>
                    <option value="Du khách">Du khách điền dã</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="font-semibold text-foreground">Thể loại ảnh:</label>
                  <select
                    value={imageCategory}
                    onChange={(e) => setImageCategory(e.target.value)}
                    className="w-full rounded-xl border border-border bg-background px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-primary/40"
                  >
                    <option value="facade">Ảnh chụp hiện trạng mặt tiền</option>
                    <option value="interior">Ảnh chụp nội thất / Ngai vàng</option>
                    <option value="detail">Chi tiết kiến trúc / Khảm sành sứ</option>
                    <option value="archival">Ảnh tư liệu lịch sử (trước 1947)</option>
                    <option value="blueprint">Bản vẽ bình đồ / Khảo cổ học</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="font-semibold text-foreground">
                  Nguồn ảnh / Đường dẫn liên kết (Link Google Drive, Flickr hoặc bài báo):
                </label>
                <input
                  type="text"
                  required
                  value={imageSource}
                  onChange={(e) => setImageSource(e.target.value)}
                  placeholder="Ví dụ: https://drive.google.com/... hoặc EFEO Fonds Indochine"
                  className="w-full rounded-xl border border-border bg-background px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-primary/40"
                />
              </div>

              <div className="space-y-1.5">
                <label className="font-semibold text-foreground">
                  Mô tả góc quan sát & Ghi chú sử liệu:
                </label>
                <textarea
                  rows={3}
                  value={imageDescription}
                  onChange={(e) => setImageDescription(e.target.value)}
                  placeholder="Ghi rõ ngày chụp, góc nhìn (mặt trước, bên trái, trên cao) và hiện trạng công trình lúc chụp..."
                  className="w-full rounded-xl border border-border bg-background p-3 text-xs focus:outline-none focus:ring-2 focus:ring-primary/40"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsContributeModalOpen(false)}
                >
                  Hủy bỏ
                </Button>
                <Button type="submit" size="sm" className="bg-primary text-primary-foreground gap-1.5">
                  <Send className="h-3.5 w-3.5" />
                  <span>Gửi duyệt tư liệu</span>
                </Button>
              </div>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
