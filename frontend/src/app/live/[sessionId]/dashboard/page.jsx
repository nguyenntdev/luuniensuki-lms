"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  FileJson2,
  FileSpreadsheet,
  MessageSquareText,
  RefreshCw,
  Timer,
  Users,
  Video,
} from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  exportLiveSessionTranscriptsCsv,
  exportLiveSessionTranscriptsJson,
  getLiveSessionDashboard,
} from "@/lib/api";

const SPEAKER_FILTERS = [
  { value: "all", label: "Tất cả vai trò" },
  { value: "host", label: "Chủ phòng" },
  { value: "learner", label: "Học viên" },
  { value: "ai_teacher", label: "Trợ giảng AI" },
];

function formatPercent(value, digits = 1) {
  return `${(Number(value || 0) * 100).toFixed(digits)}%`;
}

function formatFixed(value, digits = 2) {
  return Number(value || 0).toFixed(digits);
}

function formatDateTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleString("vi-VN");
}

function formatClockTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleTimeString("vi-VN");
}

function speakerLabel(value) {
  if (value === "host") return "Chủ phòng";
  if (value === "learner") return "Học viên";
  if (value === "ai_teacher") return "Trợ giảng AI";
  return value || "-";
}

function actionStatusTone(status) {
  const normalized = String(status || "").toLowerCase();
  if (normalized === "failed" || normalized === "error") return "destructive";
  if (normalized === "completed" || normalized === "success") return "secondary";
  return "outline";
}

export default function LiveSessionDashboardPage() {
  const params = useParams();
  const sessionId = String(params?.sessionId || "");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dashboard, setDashboard] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [speakerFilter, setSpeakerFilter] = useState("all");
  const [searchKeyword, setSearchKeyword] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      if (!sessionId) return;
      setLoading(true);
      setError("");

      try {
        const payload = await getLiveSessionDashboard({ sessionId });
        if (!cancelled) {
          setDashboard(payload || null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadDashboard();
    return () => {
      cancelled = true;
    };
  }, [reloadKey, sessionId]);

  const actions = useMemo(
    () => (Array.isArray(dashboard?.actions) ? dashboard.actions : []),
    [dashboard],
  );

  const transcripts = useMemo(
    () => (Array.isArray(dashboard?.transcripts) ? dashboard.transcripts : []),
    [dashboard],
  );

  const filteredTranscripts = useMemo(() => {
    const normalizedKeyword = String(searchKeyword || "").trim().toLowerCase();
    return transcripts
      .filter((item) => {
        if (speakerFilter !== "all" && item?.speaker_type !== speakerFilter) return false;
        if (!normalizedKeyword) return true;
        return String(item?.text || "").toLowerCase().includes(normalizedKeyword);
      })
      .slice(0, 120);
  }, [searchKeyword, speakerFilter, transcripts]);

  async function handleExportJson() {
    if (!sessionId) return;
    try {
      const data = await exportLiveSessionTranscriptsJson({ sessionId });
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `live-session-${sessionId}-transcripts.json`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function handleExportCsv() {
    if (!sessionId) return;
    try {
      const { blob } = await exportLiveSessionTranscriptsCsv({ sessionId });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `live-session-${sessionId}-transcripts.csv`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-7xl flex-col gap-4 bg-gradient-to-b from-slate-50 via-cyan-50/40 to-teal-50/40 px-4 py-6 text-zinc-900 dark:from-zinc-950 dark:via-zinc-900 dark:to-zinc-950 dark:text-zinc-100">
      <Card className="gap-4 border border-teal-200/80 bg-white/90 py-5 shadow-sm backdrop-blur dark:border-zinc-800 dark:bg-zinc-900/90">
        <CardHeader className="px-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="space-y-2">
              <CardTitle className="text-lg normal-case tracking-normal">
                Bảng điều khiển phiên học trực tiếp
              </CardTitle>
              <CardDescription className="flex items-center gap-2 text-xs">
                <Badge variant="outline">Phiên</Badge>
                <span className="font-mono text-[11px] text-muted-foreground">{sessionId || "-"}</span>
              </CardDescription>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setReloadKey((prev) => prev + 1)}
                className="rounded-md normal-case tracking-normal dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200"
              >
                <RefreshCw className="size-3.5" />
                Tải lại
              </Button>
              <Button
                asChild
                variant="outline"
                size="sm"
                className="rounded-md normal-case tracking-normal dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200"
              >
                <Link href={`/live/${sessionId}`}>
                  <Video className="size-3.5" />
                  Về phòng live
                </Link>
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportJson}
                className="rounded-md normal-case tracking-normal dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200"
              >
                <FileJson2 className="size-3.5" />
                Xuất JSON
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportCsv}
                className="rounded-md normal-case tracking-normal dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200"
              >
                <FileSpreadsheet className="size-3.5" />
                Xuất CSV
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {error ? (
        <Alert variant="destructive">
          <AlertTitle>Lỗi tải bảng điều khiển</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      {loading && !dashboard ? (
        <section className="grid gap-3 md:grid-cols-3">
          {[
            ["Đang tổng hợp tham dự", "Lấy số lượng học viên, vai trò và thời lượng vào phòng."],
            ["Đang đọc biên bản", "Chuẩn bị transcript, tin nhắn lớp học và tương tác AI."],
            ["Đang tính chất lượng", "Tổng hợp chi phí AI, độ trễ và điểm tương tác của phiên."],
          ].map(([title, description]) => (
            <Card key={title} className="border-border/70 bg-card/70 py-4">
              <CardHeader className="px-5">
                <CardTitle className="text-base normal-case tracking-normal">
                  {title}
                </CardTitle>
                <CardDescription>{description}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </section>
      ) : null}

      {dashboard ? (
        <Tabs defaultValue="tong-quan">
          <TabsList variant="line" className="w-full justify-start border-b border-border/60 p-0">
            <TabsTrigger value="tong-quan" className="normal-case tracking-normal">Tổng quan</TabsTrigger>
            <TabsTrigger value="hanh-dong" className="normal-case tracking-normal">Hành động phiên</TabsTrigger>
            <TabsTrigger value="transcript" className="normal-case tracking-normal">Biên bản</TabsTrigger>
          </TabsList>

          <TabsContent value="tong-quan" className="space-y-4 pt-2">
            <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              <Card className="gap-4 border border-teal-200/80 bg-teal-50/60 py-4 dark:border-teal-500/30 dark:bg-teal-500/10">
                <CardHeader className="px-5">
                  <CardDescription className="flex items-center gap-2">
                    <Users className="size-4" />
                    Tỷ lệ tham dự
                  </CardDescription>
                  <CardTitle className="text-2xl normal-case tracking-normal">
                    {formatPercent(dashboard?.metrics?.attendance?.attendance_rate, 0)}
                  </CardTitle>
                </CardHeader>
              </Card>

              <Card className="gap-4 border border-cyan-200/80 bg-cyan-50/60 py-4 dark:border-cyan-500/30 dark:bg-cyan-500/10">
                <CardHeader className="px-5">
                  <CardDescription className="flex items-center gap-2">
                    <Activity className="size-4" />
                    Điểm tương tác
                  </CardDescription>
                  <CardTitle className="text-2xl normal-case tracking-normal">
                    {formatFixed(dashboard?.metrics?.engagement?.interaction_score)}
                  </CardTitle>
                </CardHeader>
              </Card>

              <Card className="gap-4 border border-amber-200/80 bg-amber-50/60 py-4 dark:border-amber-500/30 dark:bg-amber-500/10">
                <CardHeader className="px-5">
                  <CardDescription className="flex items-center gap-2">
                    <Timer className="size-4" />
                    Chi phí AI
                  </CardDescription>
                  <CardTitle className="text-2xl normal-case tracking-normal">
                    {formatFixed(dashboard?.ai_cost?.total_usd, 3)} USD
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Trần phiên: {formatFixed(dashboard?.ai_cost?.ceiling_usd, 3)} USD
                  </CardDescription>
                </CardHeader>
              </Card>

              <Card className="gap-4 border border-sky-200/80 bg-sky-50/60 py-4 dark:border-sky-500/30 dark:bg-sky-500/10">
                <CardHeader className="px-5">
                  <CardDescription>Độ trễ p95</CardDescription>
                  <CardTitle className="text-2xl normal-case tracking-normal">
                    {formatFixed(dashboard?.observability?.p95_latency_ms, 0)} ms
                  </CardTitle>
                </CardHeader>
              </Card>

              <Card className="gap-4 border border-emerald-200/80 bg-emerald-50/60 py-4 dark:border-emerald-500/30 dark:bg-emerald-500/10">
                <CardHeader className="px-5">
                  <CardDescription>Tỷ lệ thành công</CardDescription>
                  <CardTitle className="text-2xl normal-case tracking-normal">
                    {formatPercent(dashboard?.observability?.success_rate)}
                  </CardTitle>
                </CardHeader>
              </Card>

              <Card className="gap-4 border border-rose-200/80 bg-rose-50/60 py-4 dark:border-rose-500/30 dark:bg-rose-500/10">
                <CardHeader className="px-5">
                  <CardDescription>Tỷ lệ lỗi rơi yêu cầu</CardDescription>
                  <CardTitle className="text-2xl normal-case tracking-normal">
                    {formatPercent(dashboard?.observability?.drop_rate)}
                  </CardTitle>
                </CardHeader>
              </Card>
            </section>

            <Card className="gap-4 border border-border/70 bg-white/90 py-4 dark:border-zinc-800 dark:bg-zinc-900/90">
              <CardHeader className="px-5">
                <CardTitle className="text-base normal-case tracking-normal">
                  Tóm tắt buổi học
                </CardTitle>
              </CardHeader>
              <CardContent className="px-5">
                <p className="whitespace-pre-wrap leading-relaxed text-muted-foreground">
                  {dashboard?.summary?.text || "Chưa có tóm tắt cho phiên học này."}
                </p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="hanh-dong" className="space-y-3 pt-2">
            <Card className="gap-4 border border-border/70 bg-white/90 py-4 dark:border-zinc-800 dark:bg-zinc-900/90">
              <CardHeader className="px-5">
                <CardTitle className="text-base normal-case tracking-normal">
                  Nhật ký hành động
                </CardTitle>
                <CardDescription>
                  Tổng số: <span className="font-medium text-foreground">{actions.length}</span>
                </CardDescription>
              </CardHeader>
              <CardContent className="px-5">
                {actions.length === 0 ? (
                  <p className="text-sm text-muted-foreground">Chưa có hành động nào trong phiên.</p>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Thời gian</TableHead>
                        <TableHead>Loại</TableHead>
                        <TableHead>Trạng thái</TableHead>
                        <TableHead>Nội dung</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {actions.slice(0, 80).map((action) => (
                        <TableRow key={action.id || `${action.type}-${action.created_at}`}>
                          <TableCell className="text-muted-foreground">
                            {formatDateTime(action.created_at)}
                          </TableCell>
                          <TableCell>{action.type || "-"}</TableCell>
                          <TableCell>
                            <Badge variant={actionStatusTone(action.status)}>
                              {action.status || "không rõ"}
                            </Badge>
                          </TableCell>
                          <TableCell className="max-w-[540px] truncate text-muted-foreground">
                            {action?.payload?.message || "-"}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="transcript" className="space-y-3 pt-2">
            <Card className="gap-4 border border-border/70 bg-white/90 py-4 dark:border-zinc-800 dark:bg-zinc-900/90">
              <CardHeader className="px-5">
                <CardTitle className="text-base normal-case tracking-normal">
                  Biên bản theo người nói
                </CardTitle>
                <CardDescription className="flex items-center gap-2">
                  <MessageSquareText className="size-4" />
                  Hiển thị tối đa {filteredTranscripts.length} bản ghi
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 px-5">
                <div className="flex flex-col gap-2 md:flex-row">
                  <Select value={speakerFilter} onValueChange={setSpeakerFilter}>
                    <SelectTrigger className="h-10 w-full rounded-md border border-zinc-300 px-2 md:w-[220px] dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200">
                      <SelectValue placeholder="Lọc theo vai trò" />
                    </SelectTrigger>
                    <SelectContent className="rounded-md border border-zinc-200 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100">
                      {SPEAKER_FILTERS.map((option) => (
                        <SelectItem key={option.value} value={option.value} className="rounded">
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  <Input
                    value={searchKeyword}
                    onChange={(event) => setSearchKeyword(event.target.value)}
                    placeholder="Tìm trong biên bản..."
                    className="h-10 w-full rounded-md border border-zinc-300 bg-white px-2 md:max-w-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                  />
                </div>

                {filteredTranscripts.length === 0 ? (
                  <p className="text-sm text-muted-foreground">Chưa có biên bản phù hợp bộ lọc.</p>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Người nói</TableHead>
                        <TableHead>Thời điểm</TableHead>
                        <TableHead>Nội dung</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredTranscripts.map((item) => (
                        <TableRow key={item.id || `${item.speaker_type}-${item.created_at}`}>
                          <TableCell>
                            <Badge variant="outline">{speakerLabel(item.speaker_type)}</Badge>
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {formatClockTime(item.created_at)}
                          </TableCell>
                          <TableCell className="max-w-[680px] whitespace-pre-wrap break-words text-muted-foreground">
                            {item.text || "-"}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      ) : null}
    </main>
  );
}
