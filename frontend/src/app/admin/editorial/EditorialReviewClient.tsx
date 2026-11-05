"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  Bot,
  Check,
  CheckCircle2,
  Clock,
  ExternalLink,
  Eye,
  FileCheck2,
  FileText,
  Filter,
  HelpCircle,
  History,
  Lock,
  RefreshCw,
  Scale,
  Search,
  Shield,
  ShieldAlert,
  ShieldCheck,
  UserCheck,
  X,
  XCircle,
} from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/stores/authStore";

interface QueueItem {
  id: string;
  item_type: "claim" | "entity" | "source";
  title: string;
  statement_en?: string;
  entity_id?: string;
  entity_slug?: string;
  entity_name?: string;
  status: string;
  confidence?: string;
  origin?: string;
  is_ai_draft: boolean;
  author_id?: string;
  author_email?: string;
  author_name?: string;
  reviewer_id?: string;
  has_eligible_source: boolean;
  source_count: number;
  rights_status?: string;
  rights_cleared: boolean;
  is_disputed: boolean;
  review_notes?: string;
  created_at?: string;
  updated_at?: string;
}

interface QueueSummary {
  pending_review_count: number;
  internal_review_count: number;
  disputed_count: number;
  needs_source_count: number;
  needs_rights_count: number;
  ai_draft_count: number;
  verified_count: number;
}

interface DisputeItem {
  dispute_id: number;
  resource_type: string;
  resource_id: string;
  resource_title: string;
  dispute_reason?: string;
  disputed_by_id?: string;
  disputed_by_email?: string;
  status: "active" | "resolved" | "upheld";
  resolution_notes?: string;
  resolved_by_id?: string;
  created_at?: string;
}

const EDITORIAL_ROLES = ["admin", "super_admin", "staff", "teacher"];

export function EditorialReviewClient() {
  const user = useAuthStore((s) => s.user);
  const authStatus = useAuthStore((s) => s.status);

  const [activeTab, setActiveTab] = useState<"queue" | "disputes" | "rights">("queue");
  const [items, setItems] = useState<QueueItem[]>([]);
  const [summary, setSummary] = useState<QueueSummary>({
    pending_review_count: 0,
    internal_review_count: 0,
    disputed_count: 0,
    needs_source_count: 0,
    needs_rights_count: 0,
    ai_draft_count: 0,
    verified_count: 0,
  });
  const [disputes, setDisputes] = useState<DisputeItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Review Modal State
  const [selectedItem, setSelectedItem] = useState<QueueItem | null>(null);
  const [reviewAction, setReviewAction] = useState<string>("verify");
  const [reviewNotes, setReviewNotes] = useState<string>("");
  const [actionSubmitting, setActionSubmitting] = useState<boolean>(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // Dispute Resolve State
  const [selectedDispute, setSelectedDispute] = useState<DisputeItem | null>(null);
  const [disputeResolution, setDisputeResolution] = useState<"resolved" | "upheld">("resolved");
  const [disputeNotes, setDisputeNotes] = useState<string>("");
  const [disputeSubmitting, setDisputeSubmitting] = useState<boolean>(false);

  // Rights Sign-off State
  const [rightsTargetId, setRightsTargetId] = useState<string>("");
  const [rightsResourceType, setRightsResourceType] = useState<string>("source");
  const [rightsStatusInput, setRightsStatusInput] = useState<string>("cleared");
  const [rightsOwnerInput, setRightsOwnerInput] = useState<string>("Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)");
  const [rightsLicenseInput, setRightsLicenseInput] = useState<string>("CC BY 4.0 / Educational Fair Use");
  const [rightsLegalBasis, setRightsLegalBasis] = useState<string>("Public Domain (1835 Imperial Relic)");
  const [rightsNotes, setRightsNotes] = useState<string>("");
  const [rightsSubmitting, setRightsSubmitting] = useState<boolean>(false);

  const isStaff = Boolean(user?.role && EDITORIAL_ROLES.includes(user.role));

  const fetchQueue = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (statusFilter !== "all") params.set("status", statusFilter);
      if (typeFilter !== "all") params.set("item_type", typeFilter);
      if (searchQuery.trim()) params.set("search", searchQuery.trim());

      const res = await fetch(`/api/v1/admin/editorial/queue?${params.toString()}`);
      if (!res.ok) {
        if (res.status === 403) {
          throw new Error("Tài khoản của bạn không có quyền truy cập hàng đợi biên tập (Yêu cầu vai trò Teacher / Staff / Admin).");
        }
        throw new Error(`Lỗi kết nối hệ thống biên tập (${res.status})`);
      }
      const data = await res.json();
      setItems(data.items || []);
      if (data.summary) setSummary(data.summary);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Lỗi không xác định");
    } finally {
      setLoading(false);
    }
  }, [statusFilter, typeFilter, searchQuery]);

  const fetchDisputes = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/admin/editorial/disputes");
      if (res.ok) {
        const data = await res.json();
        setDisputes(data.items || []);
      }
    } catch {
      // Ignored in background fetch
    }
  }, []);

  useEffect(() => {
    if (isStaff) {
      fetchQueue();
      fetchDisputes();
    }
  }, [isStaff, fetchQueue, fetchDisputes]);

  const handleReviewSubmit = async () => {
    if (!selectedItem) return;
    setActionSubmitting(true);
    setActionError(null);

    try {
      const res = await fetch("/api/v1/admin/editorial/review", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          item_type: selectedItem.item_type,
          item_id: selectedItem.id,
          action: reviewAction,
          notes: reviewNotes.trim() || undefined,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        const errMsg = data.error?.message || data.detail || "Không thể thực hiện phê duyệt.";
        throw new Error(errMsg);
      }

      setSuccessBanner(`Đã cập nhật trạng thái mục sang '${data.new_status}' qua thao tác '${data.action}'.`);
      setSelectedItem(null);
      setReviewNotes("");
      fetchQueue();
      fetchDisputes();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : "Lỗi xử lý kiểm duyệt.");
    } finally {
      setActionSubmitting(false);
    }
  };

  const handleDisputeResolveSubmit = async () => {
    if (!selectedDispute) return;
    setDisputeSubmitting(true);
    setError(null);

    try {
      const res = await fetch("/api/v1/admin/editorial/disputes/resolve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          item_type: selectedDispute.resource_type,
          item_id: selectedDispute.resource_id,
          resolution: disputeResolution,
          resolution_notes: disputeNotes.trim(),
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error?.message || data.detail || "Không thể giải quyết tranh chấp.");
      }

      setSuccessBanner(`Tranh chấp đã được ${disputeResolution === "resolved" ? "hòa giải & mở khóa" : "giữ nguyên bảo lưu"} thành công.`);
      setSelectedDispute(null);
      setDisputeNotes("");
      fetchQueue();
      fetchDisputes();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Lỗi giải quyết tranh chấp.");
    } finally {
      setDisputeSubmitting(false);
    }
  };

  const handleRightsSignoffSubmit = async () => {
    if (!rightsTargetId) return;
    setRightsSubmitting(true);
    setError(null);

    try {
      const res = await fetch("/api/v1/admin/editorial/rights-signoff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resource_type: rightsResourceType,
          resource_id: rightsTargetId,
          rights_status: rightsStatusInput,
          rights_owner: rightsOwnerInput,
          license: rightsLicenseInput,
          legal_basis: rightsLegalBasis,
          notes: rightsNotes,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error?.message || data.detail || "Không thể ký duyệt bản quyền.");
      }

      setSuccessBanner(`Đã ký duyệt bản quyền '${rightsStatusInput}' cho tài nguyên số thành công.`);
      setRightsTargetId("");
      setRightsNotes("");
      fetchQueue();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Lỗi ký duyệt bản quyền.");
    } finally {
      setRightsSubmitting(false);
    }
  };

  if (authStatus === "checking") {
    return (
      <div className="flex h-96 items-center justify-center">
        <RefreshCw className="h-8 w-8 animate-spin text-amber-500" />
      </div>
    );
  }

  if (!isStaff) {
    return (
      <div className="mx-auto max-w-4xl p-8">
        <Alert variant="destructive">
          <ShieldAlert className="h-5 w-5" />
          <AlertTitle>Truy cập bị từ chối (403 Forbidden)</AlertTitle>
          <AlertDescription>
            Hàng đợi kiểm duyệt P09–P10 chỉ dành cho Biên tập viên nhân văn, Giáo viên chuyên môn và Quản trị viên hệ thống. Người học và khách không thể xem hoặc duyệt nội dung.
          </AlertDescription>
        </Alert>
        <div className="mt-4">
          <Link href="/admin">
            <Button variant="outline">
              <ArrowLeft className="mr-2 h-4 w-4" /> Quay lại trang quản trị
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 px-4 py-8 text-slate-100 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8 flex flex-col justify-between gap-4 border-b border-slate-800 pb-6 md:flex-row md:items-center">
        <div>
          <div className="flex items-center gap-2">
            <Link href="/admin" className="text-sm text-slate-400 hover:text-slate-200">
              Quản trị
            </Link>
            <span className="text-slate-600">/</span>
            <span className="text-sm text-amber-400">Kiểm duyệt P09–P10</span>
          </div>
          <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-100 sm:text-3xl">
            Hàng đợi Biên tập Nhân văn & Kiểm duyệt Sử liệu
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Quy trình phê duyệt nghiên cứu P09–P10: Tách bạch Tác giả/Người duyệt (4-Eyes Rule), Sổ cái tranh chấp, Ký duyệt bản quyền.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Badge variant="outline" className="border-emerald-600 bg-emerald-950/60 px-3 py-1.5 text-xs text-emerald-300">
            <ShieldCheck className="mr-1.5 h-3.5 w-3.5 text-emerald-400" />
            4-Eyes Rule Kích hoạt
          </Badge>
          <Button onClick={() => fetchQueue()} variant="outline" size="sm" className="border-slate-700 bg-slate-900 text-slate-200 hover:bg-slate-800">
            <RefreshCw className="mr-2 h-4 w-4" /> Làm mới
          </Button>
        </div>
      </div>

      {/* Success Banner */}
      {successBanner && (
        <Alert className="mb-6 border-emerald-600 bg-emerald-950/50 text-emerald-200">
          <CheckCircle2 className="h-5 w-5 text-emerald-400" />
          <AlertTitle>Thành công</AlertTitle>
          <AlertDescription className="flex items-center justify-between">
            <span>{successBanner}</span>
            <Button variant="ghost" size="sm" onClick={() => setSuccessBanner(null)} className="h-6 w-6 p-0 text-emerald-400 hover:bg-emerald-900">
              <X className="h-4 w-4" />
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-5 w-5" />
          <AlertTitle>Lỗi</AlertTitle>
          <AlertDescription className="flex items-center justify-between">
            <span>{error}</span>
            <Button variant="ghost" size="sm" onClick={() => setError(null)} className="h-6 w-6 p-0 text-white">
              <X className="h-4 w-4" />
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Summary KPI Cards */}
      <div className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        <Card className="border-slate-800 bg-slate-900/60">
          <CardHeader className="p-4 pb-2">
            <CardDescription className="text-xs text-slate-400">Chờ duyệt</CardDescription>
            <CardTitle className="text-2xl font-bold text-amber-400">{summary.pending_review_count}</CardTitle>
          </CardHeader>
        </Card>
        <Card className="border-slate-800 bg-slate-900/60">
          <CardHeader className="p-4 pb-2">
            <CardDescription className="text-xs text-slate-400">Đang bình duyệt</CardDescription>
            <CardTitle className="text-2xl font-bold text-blue-400">{summary.internal_review_count}</CardTitle>
          </CardHeader>
        </Card>
        <Card className="border-slate-800 bg-slate-900/60">
          <CardHeader className="p-4 pb-2">
            <CardDescription className="text-xs text-slate-400">Tranh chấp sử học</CardDescription>
            <CardTitle className="text-2xl font-bold text-rose-400">{summary.disputed_count}</CardTitle>
          </CardHeader>
        </Card>
        <Card className="border-slate-800 bg-slate-900/60">
          <CardHeader className="p-4 pb-2">
            <CardDescription className="text-xs text-slate-400">Thiếu nguồn</CardDescription>
            <CardTitle className="text-2xl font-bold text-amber-300">{summary.needs_source_count}</CardTitle>
          </CardHeader>
        </Card>
        <Card className="border-slate-800 bg-slate-900/60">
          <CardHeader className="p-4 pb-2">
            <CardDescription className="text-xs text-slate-400">Bản thảo AI</CardDescription>
            <CardTitle className="text-2xl font-bold text-purple-400">{summary.ai_draft_count}</CardTitle>
          </CardHeader>
        </Card>
        <Card className="border-slate-800 bg-slate-900/60">
          <CardHeader className="p-4 pb-2">
            <CardDescription className="text-xs text-slate-400">Đã xác thực</CardDescription>
            <CardTitle className="text-2xl font-bold text-emerald-400">{summary.verified_count}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Main Tabs */}
      <div className="mb-6 flex border-b border-slate-800">
        <button
          onClick={() => setActiveTab("queue")}
          className={`flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === "queue"
              ? "border-amber-500 text-amber-400"
              : "border-transparent text-slate-400 hover:border-slate-700 hover:text-slate-200"
          }`}
        >
          <FileText className="h-4 w-4" />
          Hàng đợi kiểm duyệt ({items.length})
        </button>
        <button
          onClick={() => setActiveTab("disputes")}
          className={`flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === "disputes"
              ? "border-rose-500 text-rose-400"
              : "border-transparent text-slate-400 hover:border-slate-700 hover:text-slate-200"
          }`}
        >
          <Scale className="h-4 w-4" />
          Sổ cái tranh chấp ({disputes.length})
        </button>
        <button
          onClick={() => setActiveTab("rights")}
          className={`flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === "rights"
              ? "border-emerald-500 text-emerald-400"
              : "border-transparent text-slate-400 hover:border-slate-700 hover:text-slate-200"
          }`}
        >
          <FileCheck2 className="h-4 w-4" />
          Ký duyệt bản quyền
        </button>
      </div>

      {/* TAB 1: Review Queue */}
      {activeTab === "queue" && (
        <div>
          {/* Filters Bar */}
          <div className="mb-6 flex flex-wrap items-center gap-3 rounded-lg border border-slate-800 bg-slate-900/40 p-4">
            <div className="relative min-w-[200px] flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
              <Input
                placeholder="Tìm kiếm nội dung khẳng định, tên thực thể..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="border-slate-700 bg-slate-900 pl-9 text-sm text-slate-100"
              />
            </div>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200 focus:outline-none"
            >
              <option value="all">Tất cả trạng thái</option>
              <option value="pending_review">Chờ duyệt (Draft + Internal)</option>
              <option value="internal_review">Đang bình duyệt (Internal Review)</option>
              <option value="verified">Đã xác thực (Verified)</option>
              <option value="disputed">Tranh chấp (Disputed)</option>
              <option value="draft">Bản nháp (Draft)</option>
            </select>

            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200 focus:outline-none"
            >
              <option value="all">Tất cả loại hình</option>
              <option value="claim">Khẳng định sử học (Claim)</option>
              <option value="entity">Thực thể di sản (Entity)</option>
            </select>
          </div>

          {/* Queue Items */}
          {loading ? (
            <div className="flex h-64 items-center justify-center">
              <RefreshCw className="h-6 w-6 animate-spin text-amber-500" />
              <span className="ml-3 text-sm text-slate-400">Đang tải hàng đợi kiểm duyệt...</span>
            </div>
          ) : items.length === 0 ? (
            <Card className="border-slate-800 bg-slate-900/30 text-center">
              <CardContent className="p-12">
                <CheckCircle2 className="mx-auto h-12 w-12 text-slate-600" />
                <h3 className="mt-4 text-lg font-medium text-slate-200">Không có mục nào trong hàng đợi</h3>
                <p className="mt-1 text-sm text-slate-400">Tất cả bản thảo và khẳng định đã được xử lý hoặc không khớp với bộ lọc.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {items.map((item) => {
                const isAuthor = user && item.author_id && user.id === item.author_id;

                return (
                  <Card key={`${item.item_type}-${item.id}`} className="border-slate-800 bg-slate-900/50 hover:border-slate-700">
                    <CardContent className="p-6">
                      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-start">
                        <div className="flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <Badge variant="outline" className="border-slate-700 text-xs font-mono uppercase text-slate-300">
                              {item.item_type}
                            </Badge>

                            {item.is_ai_draft ? (
                              <Badge className="border-purple-600 bg-purple-950/80 text-xs text-purple-300">
                                <Bot className="mr-1 h-3 w-3" /> Bản thảo AI (Cần người duyệt)
                              </Badge>
                            ) : (
                              <Badge className="border-blue-600 bg-blue-950/80 text-xs text-blue-300">
                                <UserCheck className="mr-1 h-3 w-3" /> Biên soạn nhân văn
                              </Badge>
                            )}

                            <Badge
                              className={`text-xs ${
                                item.status === "published"
                                  ? "border-emerald-600 bg-emerald-950/80 text-emerald-300"
                                  : item.status === "verified"
                                  ? "border-blue-600 bg-blue-950/80 text-blue-300"
                                  : item.status === "disputed"
                                  ? "border-rose-600 bg-rose-950/80 text-rose-300"
                                  : item.status === "internal_review"
                                  ? "border-amber-600 bg-amber-950/80 text-amber-300"
                                  : "border-slate-700 bg-slate-800 text-slate-300"
                              }`}
                            >
                              {item.status}
                            </Badge>

                            {item.is_disputed && (
                              <Badge variant="destructive" className="text-xs">
                                <AlertTriangle className="mr-1 h-3 w-3" /> Tranh chấp
                              </Badge>
                            )}
                          </div>

                          <h3 className="mt-3 text-base font-semibold text-slate-100">{item.title}</h3>

                          {item.statement_en && (
                            <p className="mt-1 text-sm italic text-slate-400">{item.statement_en}</p>
                          )}

                          <div className="mt-4 flex flex-wrap items-center gap-4 text-xs text-slate-400">
                            {item.entity_name && (
                              <span>
                                Thực thể: <strong className="text-slate-200">{item.entity_name}</strong>
                              </span>
                            )}
                            <span>
                              Tác giả:{" "}
                              <strong className={isAuthor ? "text-amber-400" : "text-slate-200"}>
                                {item.author_name || item.author_email || item.author_id || "Khuyết danh"}
                              </strong>
                              {isAuthor && " (Bạn)"}
                            </span>
                            <span>
                              Nguồn chứng minh:{" "}
                              <strong className={item.has_eligible_source ? "text-emerald-400" : "text-amber-400"}>
                                {item.source_count} nguồn {item.has_eligible_source ? "(Hợp lệ)" : "(Chưa có nguồn hỗ trợ)"}
                              </strong>
                            </span>
                            <span>
                              Bản quyền:{" "}
                              <strong className={item.rights_cleared ? "text-emerald-400" : "text-amber-400"}>
                                {item.rights_status || "Chưa xác minh"}
                              </strong>
                            </span>
                          </div>

                          {isAuthor && (
                            <div className="mt-3 flex items-center gap-1.5 text-xs text-amber-400">
                              <Lock className="h-3.5 w-3.5" />
                              <span>
                                Nguyên tắc 4 Mắt: Bạn là tác giả của bản ghi này. Một biên tập viên hoặc chuyên gia khác phải độc lập thẩm định trước khi Xác thực hoặc Xuất bản.
                              </span>
                            </div>
                          )}
                        </div>

                        {/* Action Buttons */}
                        <div className="flex flex-wrap items-center gap-2">
                          <Button
                            size="sm"
                            variant="default"
                            onClick={() => {
                              setSelectedItem(item);
                              setReviewAction(item.status === "draft" ? "submit_for_review" : item.status === "internal_review" ? "verify" : "publish");
                              setReviewNotes("");
                              setActionError(null);
                            }}
                            className="bg-amber-600 text-white hover:bg-amber-500"
                          >
                            <Eye className="mr-1.5 h-4 w-4" /> Thẩm định & Duyệt
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Dispute Resolution Ledger */}
      {activeTab === "disputes" && (
        <div>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-100">Sổ cái Tranh chấp Sử liệu (P09-A09 Reconciliation Ledger)</h2>
            <Badge variant="outline" className="border-rose-700 text-rose-300">
              {disputes.filter((d) => d.status === "active").length} tranh chấp đang chờ hòa giải
            </Badge>
          </div>

          {disputes.length === 0 ? (
            <Card className="border-slate-800 bg-slate-900/30 text-center">
              <CardContent className="p-12">
                <CheckCircle2 className="mx-auto h-12 w-12 text-slate-600" />
                <h3 className="mt-4 text-lg font-medium text-slate-200">Không có tranh chấp nào được ghi nhận</h3>
                <p className="mt-1 text-sm text-slate-400">Tất cả các khẳng định hiện tại đều đồng thuận với nguồn tư liệu đã kiểm tra.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {disputes.map((disp) => (
                <Card key={disp.dispute_id} className="border-slate-800 bg-slate-900/50">
                  <CardContent className="p-5">
                    <div className="flex flex-col justify-between gap-4 md:flex-row md:items-start">
                      <div>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="uppercase text-xs font-mono">
                            {disp.resource_type}
                          </Badge>
                          <Badge
                            className={
                              disp.status === "active"
                                ? "bg-rose-950 text-rose-300 border-rose-700"
                                : "bg-emerald-950 text-emerald-300 border-emerald-700"
                            }
                          >
                            {disp.status === "active" ? "Đang tranh chấp" : `Đã giải quyết (${disp.status})`}
                          </Badge>
                          <span className="text-xs text-slate-500 font-mono">#ID {disp.dispute_id}</span>
                        </div>

                        <h4 className="mt-2 text-sm font-semibold text-slate-200">{disp.resource_title}</h4>
                        <p className="mt-1 text-xs text-rose-300">
                          <strong>Lý do tranh chấp:</strong> {disp.dispute_reason || "Khuyết ghi chú"}
                        </p>

                        {disp.resolution_notes && (
                          <p className="mt-2 text-xs text-emerald-400">
                            <strong>Ghi chú hòa giải:</strong> {disp.resolution_notes}
                          </p>
                        )}
                      </div>

                      {disp.status === "active" && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedDispute(disp);
                            setDisputeResolution("resolved");
                            setDisputeNotes("");
                          }}
                          className="border-rose-700 text-rose-300 hover:bg-rose-950"
                        >
                          Hòa giải tranh chấp
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: Rights Sign-off */}
      {activeTab === "rights" && (
        <div className="max-w-2xl">
          <Card className="border-slate-800 bg-slate-900/60">
            <CardHeader>
              <CardTitle className="text-lg text-slate-100">Ký duyệt Bản quyền & Cấp phép (P09-A05 Rights Sign-off)</CardTitle>
              <CardDescription className="text-xs text-slate-400">
                Xác thực quyền sử dụng, cơ sở pháp lý và điều kiện hiển thị công khai cho tài liệu lưu trữ, bản dập 2D hoặc mô hình 3D.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-xs font-medium text-slate-300">Loại tài nguyên</label>
                <select
                  value={rightsResourceType}
                  onChange={(e) => setRightsResourceType(e.target.value)}
                  className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200"
                >
                  <option value="source">Tài liệu tham khảo / Thư mục (Source)</option>
                  <option value="asset">Tệp tư liệu / Bản dập / Mô hình 3D (Asset)</option>
                  <option value="claim">Khẳng định sử học (Claim)</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300">Mã định danh tài nguyên (UUID)</label>
                <Input
                  placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
                  value={rightsTargetId}
                  onChange={(e) => setRightsTargetId(e.target.value)}
                  className="mt-1 border-slate-700 bg-slate-900 text-sm font-mono"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300">Trạng thái bản quyền</label>
                <select
                  value={rightsStatusInput}
                  onChange={(e) => setRightsStatusInput(e.target.value)}
                  className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200"
                >
                  <option value="cleared">Đã cấp phép đầy đủ (cleared)</option>
                  <option value="verified">Đã kiểm duyệt (verified)</option>
                  <option value="public_domain">Thuộc phạm vi công cộng (public_domain)</option>
                  <option value="restricted">Bị hạn chế bản quyền (restricted)</option>
                  <option value="revoked">Đã rút lại cấp phép (revoked)</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300">Chủ sở hữu quyền (Rights Owner)</label>
                <Input
                  value={rightsOwnerInput}
                  onChange={(e) => setRightsOwnerInput(e.target.value)}
                  className="mt-1 border-slate-700 bg-slate-900 text-sm"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300">Giấy phép (License)</label>
                <Input
                  value={rightsLicenseInput}
                  onChange={(e) => setRightsLicenseInput(e.target.value)}
                  className="mt-1 border-slate-700 bg-slate-900 text-sm"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300">Cơ sở pháp lý / Trích lục</label>
                <Input
                  value={rightsLegalBasis}
                  onChange={(e) => setRightsLegalBasis(e.target.value)}
                  className="mt-1 border-slate-700 bg-slate-900 text-sm"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300">Ghi chú thẩm định pháp lý</label>
                <textarea
                  rows={3}
                  value={rightsNotes}
                  onChange={(e) => setRightsNotes(e.target.value)}
                  placeholder="Ghi chú xác nhận tư cách pháp lý..."
                  className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 p-2 text-sm text-slate-200"
                />
              </div>

              <Button
                onClick={handleRightsSignoffSubmit}
                disabled={!rightsTargetId || rightsSubmitting}
                className="w-full bg-emerald-600 text-white hover:bg-emerald-500"
              >
                {rightsSubmitting ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <FileCheck2 className="mr-2 h-4 w-4" />}
                Ký duyệt Bản quyền
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Review Modal */}
      {selectedItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="w-full max-w-xl rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-lg font-bold text-slate-100">Thẩm định Sử liệu & Phê duyệt</h3>
              <button onClick={() => setSelectedItem(null)} className="text-slate-400 hover:text-slate-200">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mt-4 space-y-4">
              <div>
                <span className="text-xs uppercase text-slate-500">Nội dung khẳng định</span>
                <p className="mt-1 text-sm font-medium text-slate-200">{selectedItem.title}</p>
                {selectedItem.statement_en && (
                  <p className="mt-0.5 text-xs italic text-slate-400">{selectedItem.statement_en}</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs text-slate-400">
                <div>
                  <span className="text-slate-500">Trạng thái hiện tại:</span> <strong className="text-slate-200">{selectedItem.status}</strong>
                </div>
                <div>
                  <span className="text-slate-500">Số nguồn chứng minh:</span> <strong className="text-slate-200">{selectedItem.source_count}</strong>
                </div>
              </div>

              {/* 4-Eyes Check Warning */}
              {user && selectedItem.author_id && user.id === selectedItem.author_id && (
                <Alert className="border-amber-700 bg-amber-950/40 text-amber-300">
                  <ShieldAlert className="h-4 w-4 text-amber-400" />
                  <AlertTitle className="text-xs font-bold">Ràng buộc Tách bạch Tác giả / Người duyệt (4-Eyes Rule)</AlertTitle>
                  <AlertDescription className="text-xs">
                    Bạn đã tạo bản ghi này. API kiểm duyệt sẽ từ chối nếu bạn cố tự phê duyệt hoặc xuất bản bản thảo của chính mình.
                  </AlertDescription>
                </Alert>
              )}

              {actionError && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription className="text-xs">{actionError}</AlertDescription>
                </Alert>
              )}

              <div>
                <label className="text-xs font-medium text-slate-300">Hành động kiểm duyệt</label>
                <select
                  value={reviewAction}
                  onChange={(e) => setReviewAction(e.target.value)}
                  className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200"
                >
                  <option value="verify">Xác thực học thuật (Verify - Yêu cầu nguồn & người duyệt độc lập)</option>
                  <option value="publish">Xuất bản công khai (Publish - Đưa vào Atlas & Bài học)</option>
                  <option value="submit_for_review">Đưa vào bình duyệt nội bộ (Submit for review)</option>
                  <option value="reject">Từ chối / Yêu cầu chỉnh sửa (Reject)</option>
                  <option value="flag_dispute">Gắn cờ tranh chấp học thuật (Flag Dispute)</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300">
                  Ghi chú thẩm định & Căn cứ phê duyệt <span className="text-rose-400">*</span>
                </label>
                <textarea
                  rows={3}
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="Nêu rõ chứng cứ, số trang tư liệu sử học hoặc lý do chấp thuận / từ chối..."
                  className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 p-2 text-sm text-slate-200"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button variant="ghost" size="sm" onClick={() => setSelectedItem(null)} className="text-slate-400">
                  Hủy
                </Button>
                <Button
                  size="sm"
                  onClick={handleReviewSubmit}
                  disabled={actionSubmitting || (!reviewNotes.trim() && ["verify", "publish", "reject", "flag_dispute"].includes(reviewAction))}
                  className="bg-amber-600 text-white hover:bg-amber-500"
                >
                  {actionSubmitting ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <Check className="mr-2 h-4 w-4" />}
                  Xác nhận hành động
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Dispute Modal */}
      {selectedDispute && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="w-full max-w-lg rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-lg font-bold text-slate-100">Hòa giải Tranh chấp Sử học</h3>
              <button onClick={() => setSelectedDispute(null)} className="text-slate-400 hover:text-slate-200">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mt-4 space-y-4">
              <div>
                <span className="text-xs uppercase text-slate-500">Mục tranh chấp</span>
                <p className="mt-1 text-sm font-medium text-slate-200">{selectedDispute.resource_title}</p>
                <p className="mt-1 text-xs text-rose-300">Lý do: {selectedDispute.dispute_reason}</p>
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300">Quyết định hòa giải</label>
                <select
                  value={disputeResolution}
                  onChange={(e) => setDisputeResolution(e.target.value as "resolved" | "upheld")}
                  className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200"
                >
                  <option value="resolved">Hòa giải & Phục hồi về Bản nháp (Resolved)</option>
                  <option value="upheld">Giữ nguyên trạng thái Tranh chấp (Upheld)</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300">
                  Ghi chú kết luận hòa giải <span className="text-rose-400">*</span>
                </label>
                <textarea
                  rows={3}
                  value={disputeNotes}
                  onChange={(e) => setDisputeNotes(e.target.value)}
                  placeholder="Ghi nhận căn cứ giải quyết tranh chấp theo tư liệu hoặc kết luận của hội đồng..."
                  className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 p-2 text-sm text-slate-200"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button variant="ghost" size="sm" onClick={() => setSelectedDispute(null)} className="text-slate-400">
                  Hủy
                </Button>
                <Button
                  size="sm"
                  onClick={handleDisputeResolveSubmit}
                  disabled={disputeSubmitting || !disputeNotes.trim()}
                  className="bg-rose-600 text-white hover:bg-rose-500"
                >
                  {disputeSubmitting ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <Scale className="mr-2 h-4 w-4" />}
                  Lưu quyết định
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
