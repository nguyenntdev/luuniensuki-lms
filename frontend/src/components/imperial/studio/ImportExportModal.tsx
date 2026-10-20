"use client";

import React, { useRef, useState } from "react";
import {
  AlertCircle,
  ArrowDownToLine,
  CheckCircle2,
  Copy,
  Download,
  FileCode,
  FileUp,
  RefreshCw,
  Upload,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  exportAnnotations,
  importAnnotations,
} from "@/lib/imperial/map-api";
import type {
  AnnotationExportPayload,
  ImperialMapAsset,
  ImportDryRunResult,
} from "@/lib/imperial/map-types";

export interface ImportExportModalProps {
  mapAsset: ImperialMapAsset;
  isOpen: boolean;
  onClose: () => void;
  onImportComplete: () => void;
}

export function ImportExportModal({
  mapAsset,
  isOpen,
  onClose,
  onImportComplete,
}: ImportExportModalProps) {
  const [activeTab, setActiveTab] = useState<"export" | "import">("export");
  const [exportData, setExportData] = useState<AnnotationExportPayload | null>(
    null,
  );
  const [loadingExport, setLoadingExport] = useState(false);

  // Import state
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [parsedImport, setParsedImport] =
    useState<AnnotationExportPayload | null>(null);
  const [dryRunResult, setDryRunResult] = useState<ImportDryRunResult | null>(
    null,
  );
  const [isExecutingDryRun, setIsExecutingDryRun] = useState(false);
  const [isExecutingFinalImport, setIsExecutingFinalImport] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);

  // Load export data on open or tab change
  const handleLoadExport = async () => {
    try {
      setLoadingExport(true);
      const data = await exportAnnotations(mapAsset.id);
      setExportData(data);
    } catch (err: unknown) {
      console.error("Export error:", err);
    } finally {
      setLoadingExport(false);
    }
  };

  const handleDownloadJSON = () => {
    if (!exportData) return;
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `imperial-annotations-${mapAsset.slug}-v${mapAsset.version}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setImportError(null);
    setDryRunResult(null);

    const reader = new FileReader();
    reader.onload = async (event) => {
      try {
        const text = event.target?.result as string;
        const parsed = JSON.parse(text) as AnnotationExportPayload;

        if (parsed.schema_version !== "imperial-annotations/1.0") {
          throw new Error(
            `Phiên bản sơ đồ không hợp lệ: ${parsed.schema_version}. Yêu cầu: imperial-annotations/1.0`,
          );
        }

        setParsedImport(parsed);

        // Auto execute dry-run check
        setIsExecutingDryRun(true);
        const dryRes = await importAnnotations(mapAsset.id, parsed, true);
        setDryRunResult(dryRes);
      } catch (err: unknown) {
        const msg =
          err instanceof Error
            ? err.message
            : "Tệp JSON không đúng định dạng.";
        setImportError(msg);
      } finally {
        setIsExecutingDryRun(false);
      }
    };
    reader.readAsText(file);
  };

  const handleExecuteFinalImport = async () => {
    if (!parsedImport) return;
    try {
      setIsExecutingFinalImport(true);
      setImportError(null);
      const res = await importAnnotations(mapAsset.id, parsedImport, false);
      if (res.valid) {
        onImportComplete();
        onClose();
      } else {
        setImportError(
          "Nhập dữ liệu không thành công. Kiểm tra danh sách lỗi bên dưới.",
        );
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Đã có lỗi xảy ra.";
      setImportError(msg);
    } finally {
      setIsExecutingFinalImport(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl bg-card/95 backdrop-blur-2xl border-border/80 p-6 rounded-3xl shadow-2xl">
        <DialogHeader className="text-left space-y-1">
          <DialogTitle className="text-xl font-bold font-serif text-foreground flex items-center gap-2">
            <FileCode className="w-5 h-5 text-primary" />
            <span>Nhập & Xuất dữ liệu điểm ghim bản đồ</span>
          </DialogTitle>
          <DialogDescription className="text-xs text-muted-foreground">
            Hỗ trợ sao lưu, phục hồi và di chuyển dữ liệu theo chuẩn sơ đồ{" "}
            <span className="font-mono text-primary">imperial-annotations/1.0</span>
          </DialogDescription>
        </DialogHeader>

        <Separator className="my-2 bg-border/60" />

        <Tabs
          value={activeTab}
          onValueChange={(v) => {
            setActiveTab(v as "export" | "import");
            if (v === "export" && !exportData) {
              handleLoadExport();
            }
          }}
          className="w-full"
        >
          <TabsList className="bg-secondary/70 h-10 p-1 rounded-xl w-full grid grid-cols-2">
            <TabsTrigger value="export" className="text-xs rounded-lg">
              <Download className="w-3.5 h-3.5 mr-1.5" />
              Xuất tệp JSON (Export)
            </TabsTrigger>
            <TabsTrigger value="import" className="text-xs rounded-lg">
              <Upload className="w-3.5 h-3.5 mr-1.5" />
              Nhập tệp JSON (Import)
            </TabsTrigger>
          </TabsList>

          {/* Export View */}
          <TabsContent value="export" className="mt-4 space-y-4 text-xs">
            <div className="p-4 rounded-2xl bg-secondary/40 border border-border/60 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-foreground">
                  Thông tin gói xuất bản
                </span>
                <Badge
                  variant="outline"
                  className="font-mono text-[10px] bg-primary/10 text-primary border-primary/20"
                >
                  imperial-annotations/1.0
                </Badge>
              </div>
              <p className="text-muted-foreground text-xs leading-relaxed">
                Tệp xuất ra bao gồm toàn bộ tọa độ UV chuẩn hóa, liên kết mã công trình, kiểu điểm ghim và trạng thái thẩm định vị trí khảo cổ.
              </p>
            </div>

            {loadingExport ? (
              <div className="p-8 text-center text-muted-foreground">
                Đang tạo gói dữ liệu JSON...
              </div>
            ) : exportData ? (
              <div className="space-y-3">
                <div className="max-h-48 overflow-y-auto p-3 rounded-xl bg-background/80 font-mono text-[11px] border border-border/60 text-foreground/80 no-scrollbar">
                  <pre>{JSON.stringify(exportData, null, 2)}</pre>
                </div>

                <div className="flex justify-end gap-2">
                  <Button
                    type="button"
                    size="sm"
                    onClick={handleDownloadJSON}
                    className="bg-primary text-primary-foreground font-semibold text-xs gap-1.5 shadow-md"
                  >
                    <ArrowDownToLine className="w-4 h-4" />
                    <span>Tải về tệp JSON</span>
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-center py-6">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleLoadExport}
                >
                  Tạo bản xuất JSON ngay
                </Button>
              </div>
            )}
          </TabsContent>

          {/* Import View */}
          <TabsContent value="import" className="mt-4 space-y-4 text-xs">
            <input
              ref={fileInputRef}
              type="file"
              accept=".json,application/json"
              onChange={handleFileUpload}
              className="hidden"
            />

            <div
              onClick={() => fileInputRef.current?.click()}
              className="p-8 rounded-2xl border-2 border-dashed border-border/80 hover:border-primary/60 bg-secondary/20 hover:bg-secondary/40 text-center cursor-pointer transition-colors space-y-2"
            >
              <FileUp className="w-8 h-8 text-muted-foreground mx-auto" />
              <div className="text-xs font-semibold text-foreground">
                Nhấp để chọn tệp JSON hoặc kéo thả vào đây
              </div>
              <p className="text-[11px] text-muted-foreground">
                Chỉ chấp nhận tệp JSON hợp lệ theo sơ đồ imperial-annotations/1.0
              </p>
            </div>

            {importError && (
              <div className="p-3 rounded-xl bg-destructive/10 border border-destructive/30 text-destructive text-xs flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{importError}</span>
              </div>
            )}

            {/* Dry Run Diff Preview */}
            {isExecutingDryRun && (
              <div className="p-4 text-center text-muted-foreground text-xs flex items-center justify-center gap-2">
                <RefreshCw className="w-4 h-4 animate-spin text-primary" />
                <span>Đang thực hiện kiểm tra thử nghiệm (Dry-Run)...</span>
              </div>
            )}

            {dryRunResult && (
              <div className="p-4 rounded-2xl bg-secondary/40 border border-border/60 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold text-foreground text-xs flex items-center gap-1.5">
                    {dryRunResult.valid ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-destructive" />
                    )}
                    <span>Kết quả kiểm định dữ liệu (Dry-Run Preview)</span>
                  </h4>
                  <Badge
                    variant="outline"
                    className={
                      dryRunResult.valid
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                        : "bg-destructive/10 text-destructive border-destructive/20"
                    }
                  >
                    {dryRunResult.valid ? "Hợp lệ để nhập" : "Phát hiện lỗi"}
                  </Badge>
                </div>

                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="p-2 rounded-xl bg-background/60 border border-border/50">
                    <span className="text-muted-foreground block text-[10px]">
                      Sẽ tạo mới
                    </span>
                    <span className="font-bold text-emerald-400 text-sm">
                      +{dryRunResult.created_count}
                    </span>
                  </div>
                  <div className="p-2 rounded-xl bg-background/60 border border-border/50">
                    <span className="text-muted-foreground block text-[10px]">
                      Sẽ cập nhật
                    </span>
                    <span className="font-bold text-amber-400 text-sm">
                      {dryRunResult.updated_count}
                    </span>
                  </div>
                  <div className="p-2 rounded-xl bg-background/60 border border-border/50">
                    <span className="text-muted-foreground block text-[10px]">
                      Tổng số điểm
                    </span>
                    <span className="font-bold text-foreground text-sm">
                      {dryRunResult.total_count}
                    </span>
                  </div>
                </div>

                {dryRunResult.issues && dryRunResult.issues.length > 0 && (
                  <div className="space-y-1">
                    <span className="font-semibold text-foreground text-[11px]">
                      Cảnh báo & Ghi chú kiểm tra:
                    </span>
                    <ul className="space-y-1 text-[11px] text-muted-foreground max-h-28 overflow-y-auto">
                      {dryRunResult.issues.map((issue, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <span
                            className={
                              issue.type === "error"
                                ? "text-destructive font-bold"
                                : "text-amber-400 font-bold"
                            }
                          >
                            •
                          </span>
                          <span>
                            {issue.message}
                            {issue.site_slug ? ` (${issue.site_slug})` : ""}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="pt-2 flex justify-end">
                  <Button
                    type="button"
                    size="sm"
                    disabled={!dryRunResult.valid || isExecutingFinalImport}
                    onClick={handleExecuteFinalImport}
                    className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs gap-1.5 shadow-md"
                  >
                    <Upload className="w-3.5 h-3.5" />
                    <span>
                      {isExecutingFinalImport
                        ? "Đang nhập..."
                        : "Xác nhận nhập nguyên tử"}
                    </span>
                  </Button>
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>

        <DialogFooter className="mt-2">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="text-xs text-muted-foreground"
          >
            Đóng
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
