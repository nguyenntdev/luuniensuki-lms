"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Landmark, FileText, ArrowRight } from "lucide-react";
import { KNOWN_URNS, urnNameFromSlug } from "@/lib/history";

interface UrnAccessibleFallbackProps {
  urnSlug?: string;
  onReturnTo3D?: () => void;
  className?: string;
}

const URN_DETAILS: Record<
  string,
  {
    monarch: string;
    year: string;
    description: string;
    symbolism: string;
  }
> = {
  "cao-dinh": {
    monarch: "Thế Tổ Cao Hoàng Đế (Gia Long)",
    year: "1835 – 1837 (Năm Minh Mạng thứ 16-18)",
    description:
      "Cao Đỉnh đặt ở vị trí chính trung tâm trong Cửu Đỉnh, biểu trưng cho triều đại khai quốc. Cao 2,5m, nặng khoảng 2.600kg.",
    symbolism: "Chính thống, vững bền, trung tâm tối cao của quốc gia.",
  },
  "nhan-dinh": {
    monarch: "Thánh Tổ Nhân Hoàng Đế (Minh Mạng)",
    year: "1835 – 1837",
    description:
      "Nhân Đỉnh nằm bên tả (trái) Cao Đỉnh, tượng trưng cho lăng miếu Vua Minh Mạng và đức Nhân của bậc đế vương.",
    symbolism: "Lòng nhân từ, sự khoan hòa và tri thức mở mang.",
  },
  "chuong-dinh": {
    monarch: "Hiến Tổ Chương Hoàng Đế (Thiệu Trị)",
    year: "1835 – 1837",
    description:
      "Chương Đỉnh nằm bên hữu (phải) Cao Đỉnh, tượng trưng cho đức Hiền Chương và triều đại Vua Thiệu Trị.",
    symbolism: "Rạng rỡ, văn hiến, hòa bình và thịnh vượng.",
  },
  "anh-dinh": {
    monarch: "Dực Zông Anh Hoàng Đế (Tự Đức)",
    year: "1835 – 1837",
    description:
      "Anh Đỉnh tượng trưng cho Vua Tự Đức, thể hiện sự anh minh, tài trí và chí khí anh hùng.",
    symbolism: "Anh tài, quyết đoán, bảo vệ cương vực.",
  },
  "nghi-dinh": {
    monarch: "Cảnh Zông Nghị Hoàng Đế (Kiến Phúc)",
    year: "1835 – 1837",
    description:
      "Nghị Đỉnh tượng trưng cho Vua Kiến Phúc, biểu thị sự uy nghi, phép tắc và kỉ cương.",
    symbolism: "Pháp độ, chuẩn mực, sự tôn nghiêm.",
  },
  "thuan-dinh": {
    monarch: "Hựu Zông Thuần Hoàng Đế (Đồng Khánh)",
    year: "1835 – 1837",
    description:
      "Thuần Đỉnh tượng trưng cho Vua Đồng Khánh, biểu thị đức thuần hậu và sự gắn kết.",
    symbolism: "Thuần túy, chan hòa, thuận hòa đất trời.",
  },
  "tuyen-dinh": {
    monarch: "Hoằng Zông Tuyên Hoàng Đế (Khải Định)",
    year: "1835 – 1837",
    description:
      "Tuyên Đỉnh tượng trưng cho Vua Khải Định, biểu thị sự tuyên dương và lan tỏa công đức.",
    symbolism: "Tuyên bố, mở rộng, uy danh.",
  },
  "du-dinh": {
    monarch: "Hoàng Đế Dụ Đỉnh",
    year: "1835 – 1837",
    description:
      "Dụ Đỉnh nằm trên hàng đỉnh, biểu thị sự dư dật, sung túc và thái bình.",
    symbolism: "Phồn vinh, ấm no, thịnh vượng.",
  },
  "huyen-dinh": {
    monarch: "Hoàng Đế Huyền Đỉnh",
    year: "1835 – 1837",
    description:
      "Huyền Đỉnh tượng trưng cho sự huyền diệu, sâu xa và vi diệu của thiên nhiên và lịch sử.",
    symbolism: "Huyền vi, linh thiêng, thấu hiểu quy luật vạn vật.",
  },
};

export default function UrnAccessibleFallback({
  urnSlug = "cao-dinh",
  onReturnTo3D,
  className = "",
}: UrnAccessibleFallbackProps) {
  const [selectedUrn, setSelectedUrn] = useState<string>(urnSlug);
  const urnName = urnNameFromSlug(selectedUrn) || "Cao Đỉnh";
  const details = URN_DETAILS[selectedUrn] || URN_DETAILS["cao-dinh"];

  // Generate 17 relief representations for the active urn
  const reliefs = Array.from({ length: 17 }, (_, index) => {
    const numStr = String(index + 2).padStart(2, "0");
    const slug = `${selectedUrn}-${numStr}`;
    const tier = index < 6 ? "Hàng trên (Thượng)" : index < 12 ? "Hàng giữa (Trung)" : "Hàng dưới (Hạ)";
    return {
      num: numStr,
      slug,
      tier,
      href: `/atlas/${selectedUrn}/${slug}`,
    };
  });

  return (
    <section
      role="region"
      aria-label={`Mô tả văn bản thay thế 3D cho ${urnName}`}
      className={`rounded-2xl border border-border bg-card p-6 md:p-8 text-foreground ${className}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
            <Landmark className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Văn bản thay thế WCAG 2.2 AA (Non-WebGL / Screen Reader)</span>
          </div>
          <h2 className="mt-3 font-serif text-2xl font-bold tracking-tight md:text-3xl">
            {urnName} — Hồ Sơ Lịch Sử & Phù Điêu Văn Bản
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Toàn bộ thông tin mô hình 3D được thể hiện dưới dạng văn bản và bảng dữ liệu có thể truy cập bằng trình đọc màn hình.
          </p>
        </div>

        {onReturnTo3D ? (
          <button
            type="button"
            onClick={onReturnTo3D}
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 transition"
          >
            Quay lại Trình xem 3D
          </button>
        ) : null}
      </div>

      {/* Urn selector for screen readers */}
      <div className="mt-6">
        <label htmlFor="urn-select" className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
          Chọn Đỉnh để xem danh sách phù điêu:
        </label>
        <select
          id="urn-select"
          value={selectedUrn}
          onChange={(e) => setSelectedUrn(e.target.value)}
          className="w-full max-w-xs rounded-lg border border-border bg-secondary/40 px-3 py-2 text-sm font-medium text-foreground focus:ring-2 focus:ring-primary"
        >
          {KNOWN_URNS.map((u) => (
            <option key={u.slug} value={u.slug}>
              {u.nameVi} ({u.slug})
            </option>
          ))}
        </select>
      </div>

      {/* Structured Details */}
      <div className="mt-6 grid gap-4 rounded-xl border border-border/80 bg-secondary/30 p-5 md:grid-cols-2">
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-primary">Đức vua tượng trưng</h3>
          <p className="mt-1 font-serif text-base font-bold">{details.monarch}</p>
        </div>
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-primary">Thời gian đúc</h3>
          <p className="mt-1 text-sm">{details.year}</p>
        </div>
        <div className="md:col-span-2">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-primary">Mô tả tổng quan</h3>
          <p className="mt-1 text-sm leading-relaxed">{details.description}</p>
        </div>
        <div className="md:col-span-2">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-primary">Ý nghĩa biểu tượng</h3>
          <p className="mt-1 text-sm leading-relaxed">{details.symbolism}</p>
        </div>
      </div>

      {/* Accessible Table of 17 Reliefs */}
      <div className="mt-8">
        <h3 className="font-serif text-lg font-bold mb-3 flex items-center gap-2">
          <FileText className="h-5 w-5 text-primary" aria-hidden="true" />
          Danh sách 17 Phù điêu trên {urnName}
        </h3>
        <p className="text-xs text-muted-foreground mb-4" id={`relief-table-desc-${selectedUrn}`}>
          Bảng liệt kê 17 họa tiết đúc nổi (phù điêu) phân chia theo 3 tầng trên thân {urnName}.
        </p>

        <div className="overflow-x-auto rounded-xl border border-border">
          <table
            className="w-full text-left text-sm"
            aria-describedby={`relief-table-desc-${selectedUrn}`}
          >
            <caption className="sr-only">Bảng 17 phù điêu trên {urnName}</caption>
            <thead className="bg-secondary/60 text-xs font-semibold uppercase tracking-wider text-muted-foreground border-b border-border">
              <tr>
                <th scope="col" className="px-4 py-3">STT</th>
                <th scope="col" className="px-4 py-3">Mã phù điêu</th>
                <th scope="col" className="px-4 py-3">Tầng vị trí</th>
                <th scope="col" className="px-4 py-3">Chi tiết & Hồ sơ</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {reliefs.map((r) => (
                <tr key={r.slug} className="hover:bg-secondary/40 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs font-semibold text-muted-foreground">
                    {r.num}
                  </td>
                  <td className="px-4 py-3 font-medium text-foreground">
                    Phù điêu {r.slug}
                  </td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">
                    {r.tier}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={r.href}
                      className="inline-flex items-center gap-1.5 text-xs font-semibold text-primary hover:underline focus-visible:ring-2 focus-visible:ring-ring rounded px-1 py-0.5"
                    >
                      <span>Xem hồ sơ di sản</span>
                      <ArrowRight className="h-3 w-3" aria-hidden="true" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
