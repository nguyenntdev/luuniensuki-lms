import type { Metadata } from "next";
import { FunnelDashboardClient } from "./FunnelDashboardClient";

export const metadata: Metadata = {
  title: "Truth-Level Funnel Dashboard | Phễu Chuyển Đổi Phân Tầng Sự Thật",
  description:
    "Bảng điều khiển phễu chuyển đổi 5 giai đoạn phân tầng chặt chẽ theo cấp độ sự thật: Thực tế ghi nhận (OBSERVED), Giả thuyết mô hình (HYPOTHESIS), và Mục tiêu dự phóng (FORECAST).",
};

export const dynamic = "force-dynamic";

export default function FunnelDashboardPage() {
  return <FunnelDashboardClient />;
}
