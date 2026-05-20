import CertificateVerify from "@/components/trails/CertificateVerify";

export const metadata = {
  title: "Xác thực chứng chỉ — Lưu Niên Sử Kí",
};

export const dynamic = "force-dynamic";

export default function VerifyPage({ params }) {
  return (
    <main className="min-h-screen bg-background text-foreground px-6 py-10">
      <CertificateVerify hash={params.hash} />
    </main>
  );
}
