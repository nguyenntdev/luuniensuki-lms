import type { Metadata } from "next";
import Link from "next/link";
import {
  BookOpen,
  Camera,
  FileCheck,
  Scale,
  ShieldCheck,
  Building2,
  ExternalLink,
  MapPin,
  Layers,
  Scroll,
} from "lucide-react";

import ImperialHeader from "@/components/imperial/shell/ImperialHeader";
import { fetchPublicSources } from "@/lib/imperial/map-api";
import { Badge } from "@/components/ui/badge";

export const metadata: Metadata = {
  title: "Mục lục nguồn tư liệu & Sổ bộ quyền sở hữu | Lưu Niên — Đại Nội Huế",
  description:
    "Công khai danh mục sử liệu gốc, ảnh lưu trữ thế kỷ 20, dữ liệu không ảnh viễn thám và tuyên bố bản quyền giáo dục phi thương mại (Fair-Use) của dự án Lưu Niên — Đại Nội Huế.",
  openGraph: {
    title: "Mục lục nguồn tư liệu & Bản quyền giáo dục | Đại Nội Huế",
    description:
      "Minh bạch học thuật: chính sử triều Nguyễn (Đại Nam Thực Lục, Hội Điển Sự Lệ), kho ảnh EFEO, Albert Kahn và không ảnh số hóa.",
    type: "website",
  },
};

export default async function PublicSourcesPage() {
  const sources = await fetchPublicSources();

  const chronicles = sources.filter((s) => s.category === "chronicle");
  const photos = sources.filter((s) => s.category === "archival_photo");
  const remoteSensing = sources.filter((s) => s.category === "remote_sensing");
  const reports = sources.filter((s) => s.category === "conservation_report" || s.category === "monograph");

  return (
    <div className="min-h-screen bg-background flex flex-col selection:bg-primary/20 selection:text-primary">
      <ImperialHeader />

      <main className="flex-1">
        {/* Hero banner */}
        <div className="border-b border-border/70 bg-gradient-to-b from-card/80 to-background py-10 md:py-14">
          <div className="mx-auto max-w-5xl px-4 sm:px-6 space-y-4">
            <div className="flex items-center gap-2 text-primary font-bold text-xs uppercase tracking-widest">
              <Scale className="h-4 w-4" />
              <span>Minh bạch học thuật & Sổ bộ bản quyền di sản</span>
            </div>
            <h1 className="font-display text-3xl font-extrabold tracking-tight text-foreground md:text-4xl">
              Nguồn tư liệu & Quyền sở hữu trí tuệ
            </h1>
            <p className="max-w-3xl text-sm leading-relaxed text-muted-foreground md:text-base">
              Mọi khẳng định không gian, mốc thời gian và hình ảnh trong hệ thống Lưu Niên — Đại Nội Huế đều được dẫn nguồn từ các văn bản chính sử, kho ảnh tư liệu quốc tế và dữ liệu viễn thám đã được cấp phép hoặc sử dụng hợp pháp theo nguyên tắc giáo dục phi thương mại.
            </p>

            <div className="flex flex-wrap gap-3 pt-2">
              <Badge variant="secondary" className="gap-1.5 py-1 text-xs">
                <Scroll className="h-3.5 w-3.5 text-primary" />
                {chronicles.length} Bộ Quốc sử & Địa chí
              </Badge>
              <Badge variant="secondary" className="gap-1.5 py-1 text-xs">
                <Camera className="h-3.5 w-3.5 text-primary" />
                {photos.length} Kho ảnh lưu trữ
              </Badge>
              <Badge variant="secondary" className="gap-1.5 py-1 text-xs">
                <Layers className="h-3.5 w-3.5 text-primary" />
                {remoteSensing.length} Dữ liệu viễn thám
              </Badge>
              <Badge variant="secondary" className="gap-1.5 py-1 text-xs">
                <Building2 className="h-3.5 w-3.5 text-primary" />
                {reports.length} Hồ sơ di sản & Khảo cứu
              </Badge>
            </div>
          </div>
        </div>

        {/* Content body */}
        <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 space-y-12">
          {/* Legal statement box */}
          <section className="rounded-2xl border border-primary/30 bg-primary/5 p-6 md:p-8 space-y-4">
            <div className="flex items-center gap-2 text-primary font-bold text-sm uppercase tracking-wider">
              <ShieldCheck className="h-5 w-5" />
              <span>Cam kết đạo đức nghiên cứu & Cơ sở pháp lý giáo dục</span>
            </div>
            <div className="space-y-3 text-xs leading-relaxed text-foreground/90 md:text-sm text-justify">
              <p>
                Dự án học tập số hóa <strong>Lưu Niên — Đại Nội Huế</strong> tuân thủ nghiêm ngặt <strong>Luật Sở hữu trí tuệ Việt Nam</strong> (Điều 25: <em>Các trường hợp sử dụng tác phẩm đã công bố không phải xin phép, không phải trả tiền nhuận bút</em> nhằm mục đích giảng dạy và nghiên cứu khoa học phi thương mại).
              </p>
              <p>
                Các ảnh tư liệu lịch sử đầu thế kỷ 20 từ <strong>Viện Viễn Đông Bác Cổ (EFEO)</strong> và <strong>Bảo tàng Albert Kahn</strong> thuộc phạm vi công cộng (Public Domain) hoặc được chia sẻ theo các giấy phép văn hóa mở (Open Heritage / CC BY-NC-SA). Toàn bộ trích đoạn sử liệu đều ghi nhận chính xác quyền tác giả lịch sử của Quốc Sử Quán và Nội các triều Nguyễn.
              </p>
            </div>
          </section>

          {/* Group 1: Primary Chronicles */}
          <section className="space-y-6">
            <div className="border-b border-border/70 pb-3">
              <h2 className="font-display text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
                <Scroll className="h-5 w-5 text-primary" />
                <span>1. Quốc sử, Điển chế & Địa chí triều Nguyễn (Primary Chronicles & Geography)</span>
              </h2>
              <p className="text-xs text-muted-foreground mt-1">
                Các bộ biên niên sử, điển chế pháp quy và địa chí gốc do Quốc Sử Quán và Nội các triều Nguyễn trực tiếp biên soạn (Đại Nam Thực Lục, Khâm Định Hội Điển Sự Lệ, Đồng Khánh Địa Dư Chí, Đại Nam Nhất Thống Chí, Châu Bản).
              </p>
            </div>

            <div className="space-y-4">
              {chronicles.map((src) => (
                <div
                  key={src.id}
                  className="rounded-xl border border-border/80 bg-card p-5 shadow-sm space-y-3"
                >
                  <div className="flex flex-wrap items-start justify-between gap-2 border-b border-border/50 pb-2.5">
                    <div>
                      <div className="flex items-baseline gap-2">
                        <h3 className="font-display text-base font-bold text-foreground">
                          {src.title_vi}
                        </h3>
                        {src.original_title && (
                          <span className="font-serif text-sm font-semibold text-primary/80">
                            {src.original_title}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        Tác giả / Cơ quan: <strong>{src.authors}</strong> ({src.year_or_period})
                      </p>
                    </div>
                    <Badge variant="outline" className="font-mono text-[11px]">
                      {src.license_type}
                    </Badge>
                  </div>

                  <p className="text-xs leading-relaxed text-foreground/85">
                    {src.description_vi}
                  </p>

                  <div className="rounded-lg bg-secondary/40 p-3 text-xs space-y-1">
                    <div>
                      <strong>Cơ quan lưu giữ:</strong> {src.holding_institution} ({src.archive_ref || "Bản in khắc"})
                    </div>
                    <div>
                      <strong>Chủ sở hữu quyền:</strong> {src.rights_holder}
                    </div>
                    <div>
                      <strong>Căn cứ giáo dục:</strong> {src.fair_use_justification}
                    </div>
                  </div>

                  {src.sample_monuments.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1.5 pt-1 text-xs text-muted-foreground">
                      <span className="font-medium">Ứng dụng tại các di tích:</span>
                      {src.sample_monuments.map((m) => (
                        <Link
                          key={m}
                          href={`/dai-noi/cong-trinh/${m}`}
                          className="rounded bg-primary/10 px-2 py-0.5 text-[11px] font-semibold text-primary hover:underline"
                        >
                          {m}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>

          {/* Group 2: Archival Photographic Repositories */}
          <section className="space-y-6">
            <div className="border-b border-border/70 pb-3">
              <h2 className="font-display text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
                <Camera className="h-5 w-5 text-primary" />
                <span>2. Kho ảnh tư liệu & Dân tộc học đầu thế kỷ 20</span>
              </h2>
              <p className="text-xs text-muted-foreground mt-1">
                Chứng cứ nhiếp ảnh khách quan về hình thái kiến trúc Đại Nội trước các biến cố chiến tranh.
              </p>
            </div>

            <div className="space-y-4">
              {photos.map((src) => (
                <div
                  key={src.id}
                  className="rounded-xl border border-border/80 bg-card p-5 shadow-sm space-y-3"
                >
                  <div className="flex flex-wrap items-start justify-between gap-2 border-b border-border/50 pb-2.5">
                    <div>
                      <h3 className="font-display text-base font-bold text-foreground">
                        {src.title_vi}
                      </h3>
                      {src.original_title && (
                        <p className="text-xs italic text-muted-foreground">
                          {src.original_title} • {src.authors} ({src.year_or_period})
                        </p>
                      )}
                    </div>
                    <Badge variant="outline" className="font-mono text-[11px] text-emerald-600 border-emerald-500/30 bg-emerald-500/10">
                      {src.license_type}
                    </Badge>
                  </div>

                  <p className="text-xs leading-relaxed text-foreground/85">
                    {src.description_vi}
                  </p>

                  <div className="rounded-lg bg-secondary/40 p-3 text-xs space-y-1">
                    <div>
                      <strong>Cơ quan lưu giữ:</strong> {src.holding_institution} ({src.archive_ref})
                    </div>
                    <div>
                      <strong>Bản quyền & Sử dụng:</strong> {src.rights_holder}
                    </div>
                    <div>
                      <strong>Tuyên bố Fair-Use:</strong> {src.fair_use_justification}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Group 3: Remote Sensing & Conservation Reports */}
          <section className="space-y-6">
            <div className="border-b border-border/70 pb-3">
              <h2 className="font-display text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
                <Layers className="h-5 w-5 text-primary" />
                <span>3. Báo cáo Khoa học Bảo tồn, Tập san Khảo cứu (BAVH) & Dữ liệu Viễn thám</span>
              </h2>
              <p className="text-xs text-muted-foreground mt-1">
                Công trình khảo cứu của Hội Đô Thành Hiếu Cổ (BAVH), hồ sơ Di sản Thế giới UNESCO #678, báo cáo khảo cổ học Hoàng Thành và dữ liệu viễn thám chuẩn hóa UV [0, 1].
              </p>
            </div>

            <div className="space-y-4">
              {[...remoteSensing, ...reports].map((src) => (
                <div
                  key={src.id}
                  className="rounded-xl border border-border/80 bg-card p-5 shadow-sm space-y-3"
                >
                  <div className="flex flex-wrap items-start justify-between gap-2 border-b border-border/50 pb-2.5">
                    <div>
                      <h3 className="font-display text-base font-bold text-foreground">
                        {src.title_vi}
                      </h3>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {src.authors} • Niên đại: {src.year_or_period}
                      </p>
                    </div>
                    <Badge variant="outline" className="font-mono text-[11px]">
                      {src.license_type}
                    </Badge>
                  </div>

                  <p className="text-xs leading-relaxed text-foreground/85">
                    {src.description_vi}
                  </p>

                  <div className="rounded-lg bg-secondary/40 p-3 text-xs space-y-1">
                    <div>
                      <strong>Cơ quan:</strong> {src.holding_institution}
                    </div>
                    <div>
                      <strong>Quyền sở hữu:</strong> {src.rights_holder}
                    </div>
                    <div>
                      <strong>Mục đích:</strong> {src.fair_use_justification}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border/60 bg-card/50 py-8 text-center text-xs text-muted-foreground">
        <div className="mx-auto max-w-5xl px-4 space-y-2">
          <p className="font-semibold text-foreground/80">
            Lưu Niên — Sổ bộ nguồn tư liệu học tập Đại Nội Huế
          </p>
          <div className="pt-2 flex justify-center gap-4 text-primary">
            <Link href="/dai-noi" className="hover:underline">Bản đồ không ảnh</Link>
            <span>•</span>
            <Link href="/dai-noi/cong-trinh/ngo-mon" className="hover:underline">Hồ sơ Ngọ Môn mẫu</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
