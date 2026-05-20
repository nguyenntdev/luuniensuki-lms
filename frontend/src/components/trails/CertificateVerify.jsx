"use client";

import { useEffect, useState } from "react";
import { verifyTrailCertificate } from "@/lib/api";

export default function CertificateVerify({ hash }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    verifyTrailCertificate(hash)
      .then(setData)
      .catch((err) => setError(err?.message || "Chứng chỉ không hợp lệ"));
  }, [hash]);

  if (error) {
    return (
      <section
        className="mx-auto max-w-xl rounded-lg border border-destructive bg-card p-6"
        role="alert"
      >
        <h1 className="text-2xl font-bold text-destructive">
          Chứng chỉ không tìm thấy
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">{error}</p>
      </section>
    );
  }

  if (!data) {
    return (
      <p className="text-sm text-muted-foreground" role="status">
        Đang xác thực…
      </p>
    );
  }

  return (
    <section className="mx-auto max-w-xl rounded-lg border border-primary bg-card p-8 text-center shadow">
      <h1 className="text-3xl font-bold tracking-tight">Chứng chỉ hợp lệ</h1>
      <p className="mt-4 text-lg">
        <strong>{data.user_display_name}</strong>
      </p>
      <p className="mt-1 text-sm text-muted-foreground">đã hoàn thành</p>
      <p className="mt-2 text-xl font-semibold">{data.trail_title}</p>
      <p className="mt-3 text-xs text-muted-foreground">
        Cấp ngày {new Date(data.issued_at).toLocaleDateString("vi-VN")}
      </p>
      <p className="mt-4 break-all text-[10px] text-muted-foreground/80">
        Mã: {hash}
      </p>
    </section>
  );
}
