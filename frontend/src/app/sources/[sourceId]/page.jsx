"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  BookOpen,
  ExternalLink,
  Library,
  ScrollText,
} from "lucide-react";

import { getHistorySource } from "@/lib/api";
import {
  sourceRightsLabel,
  sourceTypeLabel,
  verificationStatusLabel,
} from "@/lib/history";
import Skeleton from "@/components/Skeleton";
import SectionHeading from "@/components/history/SectionHeading";
import VerificationNote from "@/components/history/VerificationNote";
import { Badge } from "@/components/ui/badge";

function MetaRow({
  label,
  value,
  href,
}) {
  if (!value) return null;
  return (
    <div className="flex flex-wrap items-baseline gap-2 py-1.5">
      <dt className="w-36 shrink-0 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </dt>
      <dd className="min-w-0 flex-1 text-sm text-foreground">
        {href ? (
          <a
            href={href}
            target={href.startsWith("http") ? "_blank" : undefined}
            rel={href.startsWith("http") ? "noreferrer" : undefined}
            className="inline-flex items-center gap-1 font-medium text-primary hover:underline"
          >
            {value}
            {href.startsWith("http") ? (
              <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
            ) : null}
          </a>
        ) : (
          value
        )}
      </dd>
    </div>
  );
}

export default function SourceDetailPage() {
  const params = useParams();
  const sourceId = useMemo(
    () => (typeof params?.sourceId === "string" ? params.sourceId : ""),
    [params],
  );

  const [source, setSource] = useState(null);
  const [notFound, setNotFound] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!sourceId) return;
    document.title = `Nguồn #${sourceId} — Thư viện nguồn · Lưu Niên Sử Kí`;
  }, [sourceId]);

  useEffect(() => {
    if (!sourceId) return;
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      setNotFound(false);
      try {
        let res;
        try {
          res = await getHistorySource(sourceId);
        } catch (err) {
          if (cancelled) return;
          if (
            err?.status === 404 ||
            (err instanceof Error && /404|not found/i.test(err.message))
          ) {
            setNotFound(true);
            return;
          }
          throw err;
        }
        if (cancelled || !res) return;
        setSource(res);
      } catch (err) {
        if (!cancelled)
          setError(err instanceof Error ? err.message : String(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [sourceId]);

  if (!sourceId) return null;

  if (loading) {
    return (
      <main className="site-shell" aria-busy="true">
        <div className="heritage-hero p-6 md:p-8">
          <Skeleton className="h-8 w-1/2" />
          <Skeleton className="mt-3 h-4 w-1/3" />
        </div>
        <div className="mt-5 space-y-3">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      </main>
    );
  }

  if (notFound || !source) {
    return (
      <main className="site-shell">
        <section className="heritage-surface mx-auto max-w-xl p-8 text-center">
          <h1 className="font-display text-2xl font-bold text-foreground">
            Không tìm thấy nguồn này
          </h1>
          <p className="mt-3 text-sm leading-6 text-muted-foreground">
            Không có dữ liệu nào cho nguồn “{sourceId}” trên máy chủ lịch sử.
          </p>
          <Link
            href="/sources"
            className="mt-6 inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
          >
            Về thư viện nguồn
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        </section>
      </main>
    );
  }

  const title = source.title || `Nguồn #${sourceId}`;
  const rightsLabel = sourceRightsLabel(source.rights_status);
  const citation =
    source.citation_text ||
    [source.author_text, title, source.publisher, source.publication_year]
      .filter(Boolean)
      .join(", ");

  return (
    <main className="site-shell">
      <section className="heritage-hero p-6 md:p-9">
        <div className="relative max-w-4xl">
          <div className="flex flex-wrap items-center gap-2">
            <span className="heritage-chip">
              <Library className="h-4 w-4" aria-hidden="true" />
              Nguồn sử liệu
            </span>
            <Badge variant="outline">
              {sourceTypeLabel(source.source_type)}
            </Badge>
            {source.verification_status ? (
              <Badge variant="secondary">
                {verificationStatusLabel(source.verification_status)}
              </Badge>
            ) : null}
          </div>
          <h1 className="mt-5 font-display text-3xl font-bold tracking-tight text-foreground md:text-4xl">
            {title}
          </h1>
          {source.subtitle ? (
            <p className="mt-2 text-lg text-muted-foreground">{source.subtitle}</p>
          ) : null}
          {source.author_text ? (
            <p className="mt-3 text-sm text-muted-foreground">
              {source.author_text}
              {source.publication_year
                ? ` · ${String(source.publication_year)}`
                : ""}
            </p>
          ) : null}
        </div>
      </section>

      <div className="mt-5">
        <VerificationNote />
      </div>

      {error ? (
        <div
          role="alert"
          className="mt-5 rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive"
        >
          Có lỗi khi tải dữ liệu: {error}
        </div>
      ) : null}

      <div className="mt-8 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        {/* Bibliographic metadata */}
        <section>
          <SectionHeading
            kicker="Thư mục"
            title="Thông tin thư mục"
          />
          <dl className="mt-6 rounded-lg border border-border bg-card/60 px-5 py-4">
            <MetaRow label="Tác giả" value={source.author_text} />
            <MetaRow label="Biên tập" value={source.editor_text} />
            <MetaRow label="Nhà xuất bản" value={source.publisher} />
            <MetaRow
              label="Năm xuất bản"
              value={
                source.publication_year != null
                  ? String(source.publication_year)
                  : source.publication_date
              }
            />
            <MetaRow label="Tập / Số" value={source.volume} />
            <MetaRow label="Số phát hành" value={source.issue} />
            <MetaRow label="Trang" value={source.pages} />
            <MetaRow label="Ấn bản" value={source.edition} />
            <MetaRow label="ISBN" value={source.isbn} />
            <MetaRow label="ISSN" value={source.issn} />
            <MetaRow label="DOI" value={source.doi} href={source.doi ? `https://doi.org/${source.doi}` : null} />
            <MetaRow
              label="Liên kết"
              value={source.url || source.archive_url}
              href={source.url || source.archive_url}
            />
            <MetaRow label="Ngôn ngữ" value={source.language} />
          </dl>
        </section>

        {/* Rights / access + citation */}
        <section className="space-y-5">
          <div className="rounded-lg border border-border bg-card/60 p-6">
            <h2 className="font-display text-lg font-semibold text-foreground">
              Quyền và truy cập
            </h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              {rightsLabel || "Trạng thái quyền chưa được ghi nhận."}
              {source.license ? ` · Giấy phép: ${source.license}` : ""}
            </p>
            {source.attribution_text ? (
              <p className="mt-3 text-xs text-muted-foreground">
                Ghi công: {source.attribution_text}
              </p>
            ) : null}
          </div>

          <div className="rounded-lg border border-primary/20 bg-primary/5 p-6">
            <h2 className="font-display text-lg font-semibold text-foreground">
              Trích dẫn đề nghị
            </h2>
            <blockquote className="mt-3 border-l-2 border-primary/40 pl-4 text-sm italic leading-7 text-foreground/85">
              {citation || "Chưa có trích dẫn được chuẩn bị cho nguồn này."}
            </blockquote>
            {source.citation_text ? null : (
              <p className="mt-3 text-xs text-muted-foreground">
                Trích dẫn trên được tạo từ các trường hiện có — sẽ được chỉnh sửa
                khi có đủ thư mục.
              </p>
            )}
          </div>

          <div className="rounded-lg border border-dashed border-border/70 bg-card/45 p-6">
            <h2 className="flex items-center gap-2 font-display text-lg font-semibold text-foreground">
              <ScrollText className="h-4 w-4 text-primary" aria-hidden="true" />
              Nhận định gắn với nguồn
            </h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Nguồn đang được liên kết với các nhận định trong quá trình kiểm
              chứng. Khi hoàn tất, danh sách nhận định sẽ xuất hiện tại đây.
            </p>
            <Link
              href="/atlas"
              className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-primary hover:underline"
            >
              <BookOpen className="h-4 w-4" aria-hidden="true" />
              Tìm nhận định trong Atlas
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}