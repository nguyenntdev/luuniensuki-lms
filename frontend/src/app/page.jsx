import Link from "next/link";

export default function HomePage() {
  return (
    <main className="flex min-h-[90vh] flex-col items-center justify-center bg-background px-6 text-center pb-24">
      <div className="max-w-4xl space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700">
        
        {/* Icon */}
        <div className="mx-auto flex h-24 w-24 items-center justify-center rounded-3xl bg-gradient-to-br from-primary/20 to-bronze/10 shadow-xl shadow-primary/10 mb-8 transform rotate-3 hover:rotate-6 transition-transform duration-500 border border-primary/20">
           <span className="text-5xl">🏛️</span>
        </div>

        {/* Hero Title */}
        <h1 className="text-5xl font-display font-extrabold tracking-tight sm:text-7xl md:text-8xl">
          <span className="text-gradient-gold drop-shadow-sm">
            Lưu Niên Sử Kí
          </span>
        </h1>

        {/* Subtitle */}
        <p className="mx-auto max-w-2xl text-lg text-muted-foreground md:text-xl leading-relaxed font-medium">
          Khám phá di sản Việt Nam qua trò chơi. <br className="hidden sm:block"/>
          Khám phá <span className="text-primary font-semibold">Cửu Đỉnh Triều Nguyễn</span>, mở khóa các họa tiết cổ xưa, và làm chủ lịch sử triều Nguyễn.
        </p>

        {/* CTAs */}
        <div className="flex flex-col items-center justify-center gap-4 sm:flex-row sm:gap-6 pt-8">
          <Link
            href="/explore"
            className="group relative inline-flex h-14 w-full min-w-[220px] items-center justify-center overflow-hidden rounded-2xl bg-primary px-8 font-bold text-primary-foreground transition-all duration-300 hover:bg-primary/90 hover:scale-105 hover:shadow-xl hover:shadow-primary/20 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 sm:w-auto"
          >
            <span className="mr-2 text-xl">🚀</span> Bắt Đầu Học
          </Link>

          <Link
            href="/collection"
            className="group inline-flex h-14 w-full min-w-[220px] items-center justify-center rounded-2xl border-2 border-border bg-card px-8 font-bold text-foreground transition-all duration-300 hover:border-primary/50 hover:bg-muted hover:scale-105 focus:outline-none focus:ring-2 focus:ring-border focus:ring-offset-2 sm:w-auto"
          >
            <span className="mr-2 text-xl">📚</span> Xem Bộ Sưu Tập
          </Link>
        </div>

        {/* Stats */}
        <div className="pt-16 grid grid-cols-3 gap-4 border-t border-border mt-12">
            <div className="p-4 rounded-2xl hover:bg-muted transition-colors">
                <div className="font-display tabular-nums font-extrabold text-3xl text-bronze">9</div>
                <div className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mt-1">Cửu Đỉnh</div>
            </div>
             <div className="p-4 rounded-2xl hover:bg-muted transition-colors">
                <div className="font-display tabular-nums font-extrabold text-3xl text-primary">162</div>
                <div className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mt-1">Họa Tiết</div>
            </div>
             <div className="p-4 rounded-2xl hover:bg-muted transition-colors">
                <div className="font-display font-extrabold text-3xl text-success">∞</div>
                <div className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mt-1">Lịch Sử</div>
            </div>
        </div>
      </div>
    </main>
  );
}
