import Link from "next/link";
import {
  ArrowRight,
  BookOpen,
  Crown,
  Landmark,
  Map,
  Sparkles,
  Trophy,
} from "lucide-react";

const DINH_NAMES = [
  "Cao Đỉnh",
  "Nhân Đỉnh",
  "Chương Đỉnh",
  "Anh Đỉnh",
  "Nghi Đỉnh",
  "Thuần Đỉnh",
  "Tuyên Đỉnh",
  "Dụ Đỉnh",
  "Huyền Đỉnh",
];

const FEATURE_ITEMS = [
  {
    title: "Mô hình 3D sống động",
    description:
      "Quan sát hoa văn theo từng lớp phù điêu, xoay nhìn 360° và khám phá chất liệu đồng cổ.",
    icon: Landmark,
  },
  {
    title: "Bài học ngắn, giàu chiều sâu",
    description:
      "Mỗi họa tiết có bối cảnh lịch sử, biểu tượng và câu chuyện văn hóa được dẫn dắt mạch lạc.",
    icon: BookOpen,
  },
  {
    title: "Gamification giữ nhịp",
    description:
      "Quest theo tuần, bảng xếp hạng và streak giúp học viên quay lại liên tục.",
    icon: Trophy,
  },
];

const JOURNEY_STEPS = [
  {
    title: "Khởi động với 9 đỉnh",
    description:
      "Khám phá từng đỉnh, ghi chú nhanh những biểu tượng tiêu biểu.",
  },
  {
    title: "Thu thập họa tiết",
    description:
      "Lưu lại motif yêu thích, ghép nối ý nghĩa lịch sử và truyền thuyết.",
  },
  {
    title: "Thử thách theo lớp",
    description:
      "Hoàn thành quiz, nhận điểm XP và mở khóa nội dung mới.",
  },
  {
    title: "Chia sẻ di sản",
    description:
      "Chia sẻ tiến độ với bạn học, giữ nhịp học tập dài hạn.",
  },
];

export default function CuuDinhLanding() {
  return (
    <main className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-[-30%] h-[520px] w-[520px] -translate-x-1/2 rounded-full bg-primary/20 blur-[120px]" />
        <div className="absolute right-[-10%] top-[10%] h-[380px] w-[380px] rounded-full bg-amber-500/20 blur-[140px]" />
        <div className="absolute bottom-[-20%] left-[10%] h-[360px] w-[360px] rounded-full bg-red-500/10 blur-[120px]" />
        <div className="pattern-van-may absolute inset-0 opacity-20" />
      </div>

      <section className="relative px-6 py-20 sm:py-24 lg:py-28">
        <div className="mx-auto grid max-w-6xl gap-12 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-2 text-xs font-semibold uppercase tracking-wider text-primary">
              <Sparkles className="h-4 w-4" />
              Di sản triều Nguyễn
            </div>
            <h1 className="font-display text-4xl font-bold leading-tight text-foreground sm:text-5xl lg:text-6xl">
              Cửu Đỉnh –
              <span className="block bg-gradient-to-r from-primary via-amber-300 to-orange-400 bg-clip-text text-transparent">
                Bản đồ ký ức bằng đồng
              </span>
            </h1>
            <p className="text-base text-muted-foreground sm:text-lg">
              Chín chiếc đỉnh đồng tại Thế Miếu là bách khoa thư bằng hình ảnh
              về văn hóa, địa lý và khát vọng vương triều. Lưu Niên Sử Kí đưa
              bạn bước vào hành trình học tập số hóa, nơi mỗi họa tiết đều kể
              một câu chuyện.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/login"
                className="inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground shadow-lg transition hover:bg-primary/90"
              >
                Bắt đầu học
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/explore"
                className="inline-flex items-center gap-2 rounded-full border border-border bg-background/80 px-6 py-3 text-sm font-semibold text-foreground transition hover:bg-muted"
              >
                Xem mô hình 3D
              </Link>
            </div>
            <div className="flex flex-wrap gap-6 text-xs text-muted-foreground">
              <span className="inline-flex items-center gap-2">
                <Crown className="h-4 w-4 text-primary" />
                9 đỉnh – 9 biểu tượng quyền lực
              </span>
              <span className="inline-flex items-center gap-2">
                <Map className="h-4 w-4 text-primary" />
                162 hình tượng khắc nổi
              </span>
            </div>
          </div>

          <div className="relative">
            <div className="absolute inset-0 rounded-[28px] border border-primary/30 bg-gradient-to-br from-primary/10 via-background/30 to-background/80" />
            <div className="relative rounded-[28px] border border-border bg-card/80 p-6 shadow-xl backdrop-blur">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-widest text-muted-foreground">
                    Bộ sưu tập Cửu Đỉnh
                  </p>
                  <h2 className="mt-2 font-display text-2xl font-semibold text-foreground">
                    9 chiếc đỉnh đồng
                  </h2>
                </div>
                <div className="rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
                  1836
                </div>
              </div>
              <div className="mt-6 grid grid-cols-3 gap-3">
                {DINH_NAMES.map((name, index) => (
                  <div
                    key={name}
                    className="rounded-xl border border-border bg-background/70 px-3 py-4 text-center"
                  >
                    <div className="text-lg font-semibold text-primary">
                      {index + 1}
                    </div>
                    <div className="mt-1 text-xs font-medium text-foreground">
                      {name}
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-6 rounded-2xl border border-border bg-background/60 p-4 text-sm text-muted-foreground">
                Mỗi đỉnh là một câu chuyện về đất nước: sông núi, lễ hội, hệ sinh
                thái và vũ khí – kết nối quá khứ với hiện tại.
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="relative border-t border-border/60 bg-card/40 px-6 py-20">
        <div className="mx-auto max-w-6xl">
          <div className="flex flex-wrap items-end justify-between gap-6">
            <div>
              <p className="text-xs uppercase tracking-widest text-primary">
                Trải nghiệm học tập
              </p>
              <h2 className="mt-2 font-display text-3xl font-semibold text-foreground">
                Học di sản như một hành trình khám phá
              </h2>
            </div>
            <p className="max-w-xl text-sm text-muted-foreground">
              Thiết kế học tập kết hợp 3D, storytelling và gamification giúp học
              viên quay lại mỗi tuần để hoàn thành mục tiêu.
            </p>
          </div>
          <div className="mt-10 grid gap-6 md:grid-cols-3">
            {FEATURE_ITEMS.map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.title}
                  className="group rounded-3xl border border-border bg-background/70 p-6 shadow-lg transition hover:-translate-y-1 hover:border-primary/40"
                >
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/15 text-primary">
                    <Icon className="h-6 w-6" />
                  </div>
                  <h3 className="mt-4 font-display text-lg font-semibold text-foreground">
                    {item.title}
                  </h3>
                  <p className="mt-2 text-sm text-muted-foreground">
                    {item.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <section className="relative px-6 py-20">
        <div className="mx-auto max-w-6xl">
          <div className="grid gap-10 lg:grid-cols-[0.9fr_1.1fr]">
            <div className="space-y-6">
              <p className="text-xs uppercase tracking-widest text-primary">
                Hành trình học tập
              </p>
              <h2 className="font-display text-3xl font-semibold text-foreground">
                Giữ nhịp học đều mỗi tuần
              </h2>
              <p className="text-sm text-muted-foreground">
                Lộ trình được thiết kế theo KPI giữ chân: học nhanh – ghi nhớ
                sâu – quay lại thường xuyên.
              </p>
              <Link
                href="/login"
                className="inline-flex items-center gap-2 rounded-full border border-primary/40 px-5 py-2 text-sm font-semibold text-primary transition hover:bg-primary/10"
              >
                Vào lớp học
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
            <div className="grid gap-4">
              {JOURNEY_STEPS.map((step, index) => (
                <div
                  key={step.title}
                  className="flex gap-4 rounded-2xl border border-border bg-card/70 p-5"
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-full border border-primary/40 bg-primary/10 text-sm font-semibold text-primary">
                    {index + 1}
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-foreground">
                      {step.title}
                    </h3>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {step.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="relative border-t border-border/60 px-6 py-20">
        <div className="mx-auto flex max-w-5xl flex-col items-center gap-6 rounded-[32px] border border-primary/30 bg-gradient-to-br from-primary/10 via-background/50 to-background/90 px-6 py-12 text-center">
          <h2 className="font-display text-3xl font-semibold text-foreground">
            Sẵn sàng khám phá Cửu Đỉnh?
          </h2>
          <p className="max-w-2xl text-sm text-muted-foreground">
            Tham gia Lưu Niên Sử Kí để trải nghiệm di sản số hóa, nơi mỗi biểu
            tượng đều có câu chuyện và thử thách riêng.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link
              href="/login"
              className="inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground shadow-lg transition hover:bg-primary/90"
            >
              Bắt đầu ngay
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/explore"
              className="inline-flex items-center gap-2 rounded-full border border-border bg-background/70 px-6 py-3 text-sm font-semibold text-foreground transition hover:bg-muted"
            >
              Xem thư viện 3D
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
