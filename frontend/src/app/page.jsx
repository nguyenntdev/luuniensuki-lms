"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Bot,
  Boxes,
  CheckCircle2,
  ChevronRight,
  Compass,
  FileText,
  Flame,
  Globe2,
  GraduationCap,
  History,
  Info,
  Landmark,
  Layers,
  Library,
  Map as MapIcon,
  MapPin,
  Maximize2,
  Milestone,
  Mountain,
  Network,
  Scale,
  ScrollText,
  Search,
  Share2,
  ShieldCheck,
  Sparkles,
  TreePine,
  Trophy,
  UserCheck,
  UserRound,
  Waves,
} from "lucide-react";

import { useAuthStore } from "@/stores/authStore";
import {
  listHistoryCollections,
  listHistoryEntities,
  listHistoryStories,
} from "@/lib/api";
import {
  asCollectionList,
  asEntityList,
  asStoryList,
  entityName,
  entityTypeLabel,
  KNOWN_URNS,
  listTotal,
  reliefNumberFromSlug,
  urnNameFromSlug,
  urnSlugFromReliefSlug,
} from "@/lib/history";
import { setPageMeta } from "@/lib/seo";
import { cn } from "@/lib/utils";
import Skeleton from "@/components/Skeleton";
import EpistemicLabel from "@/components/history/EpistemicLabel";
import SectionHeading from "@/components/history/SectionHeading";
import VerificationNote from "@/components/history/VerificationNote";

const RELIEF_PREVIEW_LIMIT = 24;

const CATEGORY_TABS = [
  { id: "all", label: "Tất cả (162)", icon: Layers },
  { id: "dia_ly", label: "Địa lý & Núi sông biển", icon: Mountain, match: ["dia_ly", "son", "giang", "ha", "hai", "quan", "khau", "bien"] },
  { id: "dong_vat", label: "Động vật & Linh thú", icon: Flame, match: ["dong_vat", "linh_thu", "thu", "dieu", "ngu", "long", "ho", "tuong", "ma"] },
  { id: "thao_moc", label: "Thảo mộc & Nông sản", icon: TreePine, match: ["thao_moc", "nong_nghiep", "moc", "hoa", "qua", "dau", "canh", "nhu", "que"] },
  { id: "vo_bi", label: "Vũ khí & Võ bị", icon: ShieldCheck, match: ["vo_bi", "phao", "thuong", "dao", "no", "hoa"] },
  { id: "giao_thuong", label: "Giao thương & Thuyền bè", icon: Waves, match: ["giao_thuong", "thuyen", "dinh", "xa"] },
  { id: "thien_van", label: "Thiên văn & Vũ trụ", icon: Globe2, match: ["thien_van", "nhat", "nguyet", "tinh", "dau", "van", "phong", "loi", "hong", "vu"] },
];

const URN_HERITAGE_PROFILES = [
  {
    slug: "cao-dinh",
    nameVi: "Cao Đỉnh",
    hanNom: "高",
    emperor: "Thế Tổ Cao Hoàng Đế (Gia Long)",
    position: "Chính giữa (Trung vị)",
    weight: "2.603 kg",
    height: "2,50 m",
    highlights: ["Rồng (Long)", "Đông Hải (Biển Đông)", "Kênh Vĩnh Tế", "Núi Thiên Tôn", "Trầm Hương"],
    color: "from-amber-500/20 via-primary/10 to-transparent",
  },
  {
    slug: "nhan-dinh",
    nameVi: "Nhân Đỉnh",
    hanNom: "仁",
    emperor: "Thánh Tổ Nhân Hoàng Đế (Minh Mạng)",
    position: "Tả nhất (Bên trái thứ nhất)",
    weight: "2.515 kg",
    height: "2,31 m",
    highlights: ["Kỳ Lân", "Nam Hải (Biển Nam)", "Sông Hương", "Núi Ngự Bình", "Cây Ngô Đồng"],
    color: "from-emerald-500/20 via-accent/10 to-transparent",
  },
  {
    slug: "chuong-dinh",
    nameVi: "Chương Đỉnh",
    hanNom: "章",
    emperor: "Hiến Tổ Chương Hoàng Đế (Thiệu Trị)",
    position: "Hữu nhất (Bên phải thứ nhất)",
    weight: "2.060 kg",
    height: "2,30 m",
    highlights: ["Linh Quy (Rùa thần)", "Tây Hải (Vịnh Thái Lan)", "Sông Gianh", "Núi Kim Phụng", "Mông Đồng Thuyền"],
    color: "from-blue-500/20 via-sky-500/10 to-transparent",
  },
  {
    slug: "anh-dinh",
    nameVi: "Anh Đỉnh",
    hanNom: "英",
    emperor: "Dực Tông Anh Hoàng Đế (Tự Đức)",
    position: "Tả nhị (Bên trái thứ hai)",
    weight: "2.595 kg",
    height: "2,31 m",
    highlights: ["Nghê thần", "Sao Bắc Đẩu", "Sông Mã", "Sông Lô", "Núi Hồng Lĩnh"],
    color: "from-purple-500/20 via-indigo-500/10 to-transparent",
  },
  {
    slug: "nghi-dinh",
    nameVi: "Nghị Đỉnh",
    hanNom: "毅",
    emperor: "Cung Tông Nghị Hoàng Đế (Dục Đức)",
    position: "Hữu nhị (Bên phải thứ hai)",
    weight: "2.593 kg",
    height: "2,31 m",
    highlights: ["Voi (Tượng)", "Bạch Đằng Giang", "Cửa Thuận An", "Quảng Bình Quan", "Gỗ Đàn Mộc"],
    color: "from-red-500/20 via-rose-500/10 to-transparent",
  },
  {
    slug: "thuan-dinh",
    nameVi: "Thuần Đỉnh",
    hanNom: "純",
    emperor: "Cảnh Tông Thuần Hoàng Đế (Đồng Khánh)",
    position: "Tả tam (Bên trái thứ ba)",
    weight: "2.383 kg",
    height: "2,32 m",
    highlights: ["Lý Ngưu (Trâu rừng)", "Sông Thạch Hãn", "Cửa Cần Giờ", "Núi Tản Viên", "Cá Leo Núi"],
    color: "from-orange-500/20 via-amber-500/10 to-transparent",
  },
  {
    slug: "tuyen-dinh",
    nameVi: "Tuyên Đỉnh",
    hanNom: "宣",
    emperor: "Hoằng Tông Tuyên Hoàng Đế (Khải Định)",
    position: "Hữu tam (Bên phải thứ ba)",
    weight: "2.064 kg",
    height: "2,31 m",
    highlights: ["Heo rừng (Thỉ)", "Sông Hồng (Nhĩ Hà)", "Sông Lam", "Mũi Đại Lãnh", "Tổ Yến"],
    color: "from-cyan-500/20 via-teal-500/10 to-transparent",
  },
  {
    slug: "du-dinh",
    nameVi: "Dụ Đỉnh",
    hanNom: "裕",
    emperor: "Tượng trưng cho sự trù phú và thịnh vượng",
    position: "Tả tứ (Bên trái ngoài cùng)",
    weight: "2.016 kg",
    height: "2,34 m",
    highlights: ["Dê (Dương)", "Sông Vệ", "Cửa Hàn (Đà Nẵng)", "Đèo Hải Vân", "Cây Tùng"],
    color: "from-lime-500/20 via-emerald-500/10 to-transparent",
  },
  {
    slug: "huyen-dinh",
    nameVi: "Huyền Đỉnh",
    hanNom: "玄",
    emperor: "Tượng trưng cho sự uy nghiêm và thâm viễn",
    position: "Hữu tứ (Bên phải ngoài cùng)",
    weight: "1.935 kg",
    height: "2,31 m",
    highlights: ["Trăn gấm (Mãng Xà)", "Tiền Giang & Hậu Giang", "Sông Thao", "Đèo Hoành Sơn", "Hoa Lan"],
    color: "from-slate-500/20 via-zinc-500/10 to-transparent",
  },
];

const TUTOR_SAMPLE_PROMPTS = [
  "Vì sao vua Minh Mạng chọn đúc Cửu Đỉnh vào năm 1835?",
  "Hình tượng Đông Hải và Nam Hải trên Cửu Đỉnh khẳng định chủ quyền ra sao?",
  "Có bao nhiêu loài cây thảo mộc và dược liệu quý được chạm khắc trên 9 đỉnh?",
  "Sông Bạch Đằng và Quảng Bình Quan được đặt ở vị trí nào trên Cửu Đỉnh?",
];

const EPISTEMIC_CARDS = [
  {
    label: "Được nguồn xác nhận (Documented)",
    tone: "documented",
    source: "Đại Nam Thực Lục & Khâm Định Hội Điển",
    description: "Nhận định đối chiếu 100% chính xác từ châu bản, văn khắc và quốc sử triều Nguyễn.",
  },
  {
    label: "Diễn giải học thuật (Interpretation)",
    tone: "interpretation",
    source: "Nghiên cứu của các học giả chuyên gia",
    description: "Phân tích ngữ nghĩa biểu tượng, nghệ thuật đúc đồng và tư tưởng địa chính trị vương triều.",
  },
  {
    label: "Ký ức & Truyền ngôn (Traditional Account)",
    tone: "traditional",
    source: "Dân gian & Giai thoại cung đình",
    description: "Các câu chuyện lưu truyền về thợ đúc đồng Phường Đúc và sự kiện khánh thành Cửu Đỉnh.",
  },
  {
    label: "Đang kiểm chứng (Needs Source Review)",
    tone: "uncertain",
    source: "Nội dung kế thừa đang tra cứu",
    description: "Được gắn nhãn minh bạch; không đưa vào hệ thống câu hỏi thẩm định cho đến khi đủ nguồn.",
  },
];

export default function HomePage() {
  const status = useAuthStore((s) => s.status);
  const isAuthed = status === "authed";

  const [urns, setUrns] = useState([]);
  const [reliefs, setReliefs] = useState([]);
  const [reliefTotal, setReliefTotal] = useState(null);
  const [stories, setStories] = useState([]);
  const [collections, setCollections] = useState([]);
  const [activeCategory, setActiveCategory] = useState("all");
  const [selectedUrnSlug, setSelectedUrnSlug] = useState("cao-dinh");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setPageMeta({
      title: "Lưu Niên Sử Kí — Cửu Đỉnh Triều Nguyễn & Bách Khoa Thư Di Sản",
      description:
        "Bách khoa toàn thư di sản Cửu Đỉnh triều Nguyễn tại Hoàng thành Huế. 162 họa tiết đúc nổi, mô hình 3D tương tác, bản đồ địa lý WGS84 và trợ giảng AI có dẫn nguồn chính sử.",
      path: "/",
    });
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const [urnRes, reliefRes, storyRes, collRes] = await Promise.allSettled([
          listHistoryEntities({ entityType: "urn", limit: 20 }),
          listHistoryEntities({ entityType: "relief", limit: RELIEF_PREVIEW_LIMIT }),
          listHistoryStories({ featuredOnly: false }),
          listHistoryCollections({ limit: 6 }),
        ]);

        if (cancelled) return;

        if (urnRes.status === "fulfilled") {
          setUrns(asEntityList(urnRes.value));
        }
        if (reliefRes.status === "fulfilled") {
          setReliefs(asEntityList(reliefRes.value));
          setReliefTotal(listTotal(reliefRes.value));
        }
        if (storyRes.status === "fulfilled") {
          setStories(asStoryList(storyRes.value));
        }
        if (collRes.status === "fulfilled") {
          setCollections(asCollectionList(collRes.value));
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadData();
    return () => {
      cancelled = true;
    };
  }, []);

  // Filter relief preview cards based on active category tab
  const filteredReliefs = useMemo(() => {
    if (activeCategory === "all") return reliefs;
    const activeTab = CATEGORY_TABS.find((t) => t.id === activeCategory);
    if (!activeTab || !activeTab.match) return reliefs;

    return reliefs.filter((relief) => {
      const summary = String(relief.summary_vi || relief.summary || "").toLowerCase();
      const name = String(relief.name_vi || relief.slug || "").toLowerCase();
      return activeTab.match?.some((keyword) => summary.includes(keyword) || name.includes(keyword));
    });
  }, [reliefs, activeCategory]);

  const activeUrnProfile = useMemo(() => {
    return URN_HERITAGE_PROFILES.find((u) => u.slug === selectedUrnSlug) || URN_HERITAGE_PROFILES[0];
  }, [selectedUrnSlug]);

  return (
    <main className="site-shell pb-24" id="main-content">
      {/* ========================================================================= */}
      {/* 1. HERO SECTION — High Impact Museum Presentation                         */}
      {/* ========================================================================= */}
      <section
        className="heritage-hero relative overflow-hidden p-6 sm:p-8 md:p-12 lg:p-14"
        aria-labelledby="hero-main-heading"
      >
        {/* Subtle decorative imperial glow backdrop */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -right-24 -top-24 h-96 w-96 rounded-full bg-primary/10 blur-3xl"
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -bottom-24 -left-24 h-96 w-96 rounded-full bg-accent/10 blur-3xl"
        />

        <div className="relative grid gap-10 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
          <div>
            {/* UNESCO & Imperial Badge */}
            <div className="inline-flex flex-wrap items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3.5 py-1.5 text-xs font-semibold text-primary backdrop-blur-md">
              <Landmark className="h-3.5 w-3.5" aria-hidden="true" />
              <span>Di sản Tư liệu Ký ức Thế giới (UNESCO MOWCAP) · Hoàng thành Huế</span>
            </div>

            <h1
              id="hero-main-heading"
              className="mt-5 font-serif text-4xl font-extrabold tracking-tight text-foreground text-balance sm:text-5xl md:text-6xl"
            >
              Cửu Đỉnh Triều Nguyễn
            </h1>

            <p className="mt-3 font-serif text-xl font-medium italic text-bronze-accent sm:text-2xl">
              Bách khoa toàn thư bằng đồng của giang sơn Đại Nam
            </p>

            <p className="mt-5 max-w-2xl text-base leading-relaxed text-muted-foreground text-pretty sm:text-lg">
              Đúc từ năm 1835 đến 1837 dưới triều vua Minh Mạng, chín chiếc đỉnh đồng sừng sững tại sân Thế Miếu
              khắc ghi trọn vẹn 162 hình tượng về núi sông cương vực, muôn loài sinh vật, cây trái trù phú,
              vũ khí phòng vệ và ba vùng biển đảo thiêng liêng của Tổ quốc.
            </p>

            {/* Action CTAs */}
            <div className="mt-8 flex flex-wrap items-center gap-3.5">
              <Link
                href="/atlas"
                className="inline-flex min-h-11 items-center justify-center gap-2.5 rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/20 transition-all hover:bg-primary/90 hover:shadow-primary/30 focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background"
              >
                <Layers className="h-4 w-4" aria-hidden="true" />
                Khám phá 162 Phù điêu
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </Link>

              <Link
                href="/urns/cao-dinh"
                className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-border bg-secondary/80 px-5 py-3 text-sm font-semibold text-foreground backdrop-blur-md transition hover:border-primary/40 hover:bg-secondary focus-visible:ring-2 focus-visible:ring-primary"
              >
                <Boxes className="h-4 w-4 text-primary" aria-hidden="true" />
                Xem Cửu Đỉnh 3D
              </Link>

              <Link
                href="/map"
                className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-border/70 bg-card/60 px-4 py-3 text-sm font-medium text-muted-foreground transition hover:border-border hover:bg-card hover:text-foreground focus-visible:ring-2 focus-visible:ring-primary"
              >
                <MapIcon className="h-4 w-4 text-accent" aria-hidden="true" />
                Bản đồ địa lý
              </Link>
            </div>

            {/* Stat Counters */}
            <div className="mt-10 grid grid-cols-2 gap-3 sm:grid-cols-4 sm:gap-4">
              <div className="heritage-stat rounded-lg border border-border/60 bg-card/50 p-3.5">
                <div className="font-display text-2xl font-bold tabular-nums text-primary">9</div>
                <div className="mt-0.5 text-xs text-muted-foreground">Đỉnh đồng báu vật</div>
              </div>
              <div className="heritage-stat rounded-lg border border-border/60 bg-card/50 p-3.5">
                <div className="font-display text-2xl font-bold tabular-nums text-foreground">
                  {reliefTotal ?? 162}
                </div>
                <div className="mt-0.5 text-xs text-muted-foreground">Họa tiết chạm nổi</div>
              </div>
              <div className="heritage-stat rounded-lg border border-border/60 bg-card/50 p-3.5">
                <div className="font-display text-2xl font-bold tabular-nums text-accent">100%</div>
                <div className="mt-0.5 text-xs text-muted-foreground">Khảo chứng Hán-Nôm</div>
              </div>
              <div className="heritage-stat rounded-lg border border-border/60 bg-card/50 p-3.5">
                <div className="font-display text-2xl font-bold tabular-nums text-foreground">WGS84</div>
                <div className="mt-0.5 text-xs text-muted-foreground">Tọa độ không gian</div>
              </div>
            </div>
          </div>

          {/* Right Column: 9-Urn Interactive Showcase Card */}
          <div className="heritage-surface relative flex flex-col rounded-2xl border border-border/80 p-6 shadow-2xl backdrop-blur-xl md:p-8">
            <div className="flex items-center justify-between border-b border-border/60 pb-4">
              <div className="flex items-center gap-2">
                <span className="flex h-7 w-7 items-center justify-center rounded-md bg-primary/10 font-serif text-sm font-bold text-primary">
                  {activeUrnProfile.hanNom}
                </span>
                <div>
                  <h3 className="font-display text-base font-bold text-foreground">
                    {activeUrnProfile.nameVi} ({activeUrnProfile.hanNom})
                  </h3>
                  <p className="text-xs text-muted-foreground">{activeUrnProfile.position}</p>
                </div>
              </div>

              <Link
                href={`/cuu-dinh/${activeUrnProfile.slug}`}
                className="inline-flex items-center gap-1 text-xs font-semibold text-primary transition hover:underline"
              >
                Chi tiết đỉnh
                <ArrowUpRight className="h-3.5 w-3.5" aria-hidden="true" />
              </Link>
            </div>

            {/* Active Urn Spotlight */}
            <div className="mt-5 rounded-xl border border-border/50 bg-secondary/30 p-4">
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-muted-foreground">Phụng thờ miếu hiệu:</span>
                  <p className="font-medium text-foreground">{activeUrnProfile.emperor}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Khối lượng & Chiều cao:</span>
                  <p className="font-medium text-foreground">
                    {activeUrnProfile.weight} · {activeUrnProfile.height}
                  </p>
                </div>
              </div>

              <div className="mt-3.5 border-t border-border/40 pt-3">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-bronze-accent">
                  Họa tiết tiêu biểu khắc trên thân:
                </span>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {activeUrnProfile.highlights.map((item) => (
                    <span
                      key={item}
                      className="rounded-md bg-card/90 px-2.5 py-1 text-xs font-medium text-foreground ring-1 ring-border/80"
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Interactive Urn Selector Grid (Click to switch spotlight) */}
            <div className="mt-6">
              <span className="text-xs font-semibold text-muted-foreground">
                Chọn đỉnh để xem thông số & họa tiết:
              </span>
              <div className="mt-3 grid grid-cols-3 gap-2 sm:grid-cols-9">
                {URN_HERITAGE_PROFILES.map((urn) => {
                  const isSelected = urn.slug === selectedUrnSlug;
                  return (
                    <button
                      key={urn.slug}
                      type="button"
                      onClick={() => setSelectedUrnSlug(urn.slug)}
                      className={cn(
                        "group flex flex-col items-center gap-1 rounded-lg border p-2 text-center transition-all focus-visible:ring-2 focus-visible:ring-primary",
                        isSelected
                          ? "border-primary bg-primary/15 text-primary shadow-sm shadow-primary/20"
                          : "border-border/60 bg-card/40 text-muted-foreground hover:border-primary/40 hover:bg-secondary hover:text-foreground",
                      )}
                    >
                      <span className="font-serif text-base font-bold transition group-hover:scale-110">
                        {urn.hanNom}
                      </span>
                      <span className="text-[10px] font-medium leading-tight">{urn.nameVi.split(" ")[0]}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Quick 3D Launcher Footer */}
            <div className="mt-6 flex items-center justify-between border-t border-border/60 pt-4">
              <span className="text-xs text-muted-foreground">Mô hình không gian 3D tương tác:</span>
              <Link
                href={`/urns/${selectedUrnSlug}`}
                className="inline-flex items-center gap-1.5 rounded-md bg-primary/10 px-3 py-1.5 text-xs font-semibold text-primary transition hover:bg-primary/20"
              >
                <Boxes className="h-3.5 w-3.5" aria-hidden="true" />
                Mở 3D {activeUrnProfile.nameVi}
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Verification & Epistemic Disclaimer */}
      <div className="mt-6">
        <VerificationNote />
      </div>

      {error ? (
        <div
          role="alert"
          className="mt-6 rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive"
        >
          Không tải được một số dữ liệu lịch sử: {error}
        </div>
      ) : null}

      {/* ========================================================================= */}
      {/* 2. ATLAS 162 — Category Spectrum & Interactive Visual Gallery             */}
      {/* ========================================================================= */}
      <section className="mt-16" aria-labelledby="atlas-section-heading">
        <div className="heritage-surface p-6 sm:p-8 md:p-10">
          <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
            <SectionHeading
              kicker="Atlas Di Sản"
              title="162 Hình Đúc — Pho Bách Khoa Toàn Thư Bằng Đồng"
              lead="Toàn cảnh cương thổ, sản vật và văn hóa Đại Nam qua 162 phù điêu khắc nổi. Tra cứu chuẩn xác chữ Hán-Nôm, tọa độ địa lý và nguồn chính sử tương ứng."
            />
            <Link
              href="/atlas"
              className="inline-flex shrink-0 items-center gap-2 text-sm font-semibold text-primary hover:underline"
            >
              Mở toàn bộ Atlas 162
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
          </div>

          {/* Category Filter Tabs */}
          <div className="mt-8 flex flex-wrap items-center gap-2 border-b border-border/60 pb-4">
            {CATEGORY_TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeCategory === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveCategory(tab.id)}
                  className={cn(
                    "inline-flex items-center gap-1.5 rounded-lg px-3.5 py-2 text-xs font-semibold transition-all focus-visible:ring-2 focus-visible:ring-primary",
                    isActive
                      ? "bg-primary text-primary-foreground shadow-md shadow-primary/20"
                      : "border border-border/60 bg-secondary/40 text-muted-foreground hover:bg-secondary hover:text-foreground",
                  )}
                >
                  <Icon className="h-3.5 w-3.5" aria-hidden="true" />
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Reliefs Grid */}
          {loading ? (
            <div className="mt-6 grid grid-cols-2 gap-3.5 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
              {[...Array(12)].map((_, i) => (
                <div key={i} className="overflow-hidden rounded-xl border border-border/70 bg-card/60">
                  <Skeleton className="aspect-[4/3] w-full" />
                  <div className="p-3">
                    <Skeleton className="h-3 w-3/4" />
                    <Skeleton className="mt-2 h-2.5 w-1/2" />
                  </div>
                </div>
              ))}
            </div>
          ) : filteredReliefs.length > 0 ? (
            <div className="mt-6 grid grid-cols-2 gap-3.5 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
              {filteredReliefs.slice(0, 18).map((relief) => {
                const name = entityName(relief);
                const urnSlug = relief.urn_slug || urnSlugFromReliefSlug(relief.slug);
                const num = reliefNumberFromSlug(relief.slug);
                const hanNom = relief.name_han_nom || relief.han_nom;
                const thumb = relief.thumbnail_url;

                return (
                  <Link
                    key={relief.slug || relief.id}
                    href={`/atlas/${urnSlug}/${relief.slug}`}
                    className="focus-card group flex flex-col overflow-hidden rounded-xl border border-border/70 bg-card/70 transition-all duration-200 hover:-translate-y-1 hover:border-primary/40 hover:shadow-lg focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    <div className="relative aspect-[4/3] w-full overflow-hidden bg-secondary/50">
                      {thumb ? (
                        <img
                          src={thumb}
                          alt={name}
                          loading="lazy"
                          decoding="async"
                          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                        />
                      ) : (
                        <div className="flex h-full w-full flex-col items-center justify-center gap-1 text-muted-foreground">
                          {hanNom ? (
                            <span className="font-serif text-2xl font-bold text-bronze-accent transition group-hover:scale-110">
                              {hanNom}
                            </span>
                          ) : (
                            <span className="font-serif text-xl text-bronze-accent">#{num || "·"}</span>
                          )}
                          <span className="text-[10px] uppercase tracking-wider text-muted-foreground/80">
                            {urnNameFromSlug(urnSlug)}
                          </span>
                        </div>
                      )}

                      {/* Number Badge */}
                      {num ? (
                        <span className="absolute left-2 top-2 rounded-md bg-ink/80 px-1.5 py-0.5 text-[10px] font-bold tabular-nums text-paper backdrop-blur-sm">
                          #{num}
                        </span>
                      ) : null}

                      {/* Han Nom Glyph Overlay if thumb exists */}
                      {thumb && hanNom ? (
                        <span className="absolute bottom-2 right-2 rounded-md bg-background/85 px-1.5 py-0.5 font-serif text-xs font-bold text-primary backdrop-blur-sm">
                          {hanNom}
                        </span>
                      ) : null}
                    </div>

                    <div className="flex flex-1 flex-col justify-between p-3">
                      <div>
                        <p className="line-clamp-1 text-xs font-semibold text-foreground group-hover:text-primary">
                          {name}
                        </p>
                        <p className="mt-0.5 truncate text-[11px] text-muted-foreground">
                          {urnNameFromSlug(urnSlug)}
                        </p>
                      </div>
                      {relief.summary_vi ? (
                        <p className="mt-1.5 line-clamp-2 text-[10px] leading-relaxed text-muted-foreground/90">
                          {relief.summary_vi}
                        </p>
                      ) : null}
                    </div>
                  </Link>
                );
              })}
            </div>
          ) : (
            <div className="mt-8 rounded-xl border border-dashed border-border/80 bg-card/40 py-12 text-center text-sm text-muted-foreground">
              Không tìm thấy phù điêu nào trong nhóm này.
            </div>
          )}

          {/* Bottom Bar with Atlas CTA */}
          <div className="mt-8 flex flex-wrap items-center justify-between gap-4 border-t border-border/60 pt-5">
            <p className="flex items-center gap-2 text-xs text-muted-foreground">
              <Layers className="h-4 w-4 text-bronze-accent" aria-hidden="true" />
              Đầy đủ 162 phù điêu với nguồn trích đoạn và vị trí 3D trên thân đỉnh
            </p>
            <Link
              href="/atlas"
              className="inline-flex items-center gap-2 rounded-lg bg-primary/10 px-4 py-2 text-xs font-semibold text-primary transition hover:bg-primary/20"
            >
              Mở bản đồ ma trận Atlas 162
              <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
            </Link>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 3. FEATURED STORIES & THEMATIC COLLECTIONS                                */}
      {/* ========================================================================= */}
      {(stories.length > 0 || collections.length > 0) && (
        <section className="mt-16" aria-labelledby="curated-content-heading">
          <SectionHeading
            kicker="Nghiên Cứu & Chuyên Đề"
            title="Câu Chuyện & Tuyển Tập Di Sản Tuyển Chọn"
            lead="Những bài nghiên cứu chuyên sâu về bối cảnh đúc đỉnh, chủ quyền hải cương và các bộ sưu tập di sản theo chủ đề thực vật, danh thắng, vũ khí."
          />

          <div className="mt-8 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {stories.map((story) => (
              <Link
                key={story.slug || story.id}
                href={`/stories/${story.slug}`}
                className="heritage-card focus-card group flex flex-col overflow-hidden rounded-2xl border border-border/70 p-6 transition-all duration-200 hover:-translate-y-1 hover:border-primary/40 focus-visible:ring-2 focus-visible:ring-primary"
              >
                <div className="flex items-center justify-between text-xs text-primary">
                  <span className="inline-flex items-center gap-1.5 font-semibold uppercase tracking-wider">
                    <BookOpen className="h-3.5 w-3.5" aria-hidden="true" />
                    Câu chuyện di sản
                  </span>
                  {story.featured ? (
                    <span className="rounded-full bg-primary/15 px-2 py-0.5 text-[10px] font-bold uppercase text-primary">
                      Nổi bật
                    </span>
                  ) : null}
                </div>

                <h3 className="mt-3 font-serif text-lg font-bold text-foreground transition group-hover:text-primary">
                  {story.title_vi}
                </h3>

                {story.summary_vi ? (
                  <p className="mt-2.5 line-clamp-3 text-xs leading-relaxed text-muted-foreground">
                    {story.summary_vi}
                  </p>
                ) : null}

                <div className="mt-auto flex items-center justify-between border-t border-border/50 pt-4 text-xs font-semibold text-primary">
                  <span>Đọc bài viết</span>
                  <ArrowRight className="h-3.5 w-3.5 transition group-hover:translate-x-1" aria-hidden="true" />
                </div>
              </Link>
            ))}

            {collections.map((coll) => (
              <Link
                key={coll.slug || coll.id}
                href={`/collections/${coll.slug}`}
                className="heritage-card focus-card group flex flex-col overflow-hidden rounded-2xl border border-border/70 p-6 transition-all duration-200 hover:-translate-y-1 hover:border-primary/40 focus-visible:ring-2 focus-visible:ring-primary"
              >
                <div className="flex items-center justify-between text-xs text-accent">
                  <span className="inline-flex items-center gap-1.5 font-semibold uppercase tracking-wider">
                    <Library className="h-3.5 w-3.5" aria-hidden="true" />
                    Bộ sưu tập tuyển chọn
                  </span>
                </div>

                <h3 className="mt-3 font-serif text-lg font-bold text-foreground transition group-hover:text-accent">
                  {coll.title_vi}
                </h3>

                {coll.description_vi ? (
                  <p className="mt-2.5 line-clamp-3 text-xs leading-relaxed text-muted-foreground">
                    {coll.description_vi}
                  </p>
                ) : null}

                <div className="mt-auto flex items-center justify-between border-t border-border/50 pt-4 text-xs font-semibold text-accent">
                  <span>Khám phá tuyển tập</span>
                  <ArrowRight className="h-3.5 w-3.5 transition group-hover:translate-x-1" aria-hidden="true" />
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* ========================================================================= */}
      {/* 4. FOUR PILLARS OF DISCOVERY — Space, Time, Network, 360                   */}
      {/* ========================================================================= */}
      <section className="mt-16" aria-labelledby="discovery-pillars-heading">
        <SectionHeading
          kicker="Không Gian & Thời Gian"
          title="Bốn Lối Vào Di Sản Cửu Đỉnh"
          lead="Tiếp cận pho sử liệu bằng đồng đa chiều: từ tọa độ địa lý WGS84, trục thời gian lịch sử triều Nguyễn, mạng lưới liên kết tri thức đến chuyến tham quan thực tế ảo 360°."
        />

        <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <Link
            href="/map"
            className="focus-card group flex flex-col gap-4 rounded-2xl border border-border/70 bg-card/60 p-6 transition-all duration-200 hover:-translate-y-1 hover:border-primary/40 focus-visible:ring-2 focus-visible:ring-primary"
          >
            <span className="flex h-12 w-12 items-center justify-center rounded-xl border border-emerald-500/30 bg-emerald-500/10 text-emerald-500">
              <MapPin className="h-6 w-6" aria-hidden="true" />
            </span>
            <div>
              <h3 className="font-display text-base font-bold text-foreground">Bản Đồ Giang Sơn</h3>
              <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                Tra cứu các danh sơn, đại giang, hải khẩu và ba vùng biển Đông Hải, Nam Hải, Tây Hải trên bản đồ
                tọa độ vệ tinh.
              </p>
            </div>
            <span className="mt-auto inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-500">
              Mở bản đồ di sản
              <ArrowRight className="h-3.5 w-3.5 transition group-hover:translate-x-1" aria-hidden="true" />
            </span>
          </Link>

          <Link
            href="/timeline"
            className="focus-card group flex flex-col gap-4 rounded-2xl border border-border/70 bg-card/60 p-6 transition-all duration-200 hover:-translate-y-1 hover:border-primary/40 focus-visible:ring-2 focus-visible:ring-primary"
          >
            <span className="flex h-12 w-12 items-center justify-center rounded-xl border border-blue-500/30 bg-blue-500/10 text-blue-500">
              <History className="h-6 w-6" aria-hidden="true" />
            </span>
            <div>
              <h3 className="font-display text-base font-bold text-foreground">Dòng Thời Gian</h3>
              <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                Khám phá bối cảnh lịch sử triều Nguyễn từ năm 1802 đến 1945, các dấu mốc ban chỉ và hành trình đúc
                Cửu Đỉnh.
              </p>
            </div>
            <span className="mt-auto inline-flex items-center gap-1.5 text-xs font-semibold text-blue-500">
              Xem dòng thời gian
              <ArrowRight className="h-3.5 w-3.5 transition group-hover:translate-x-1" aria-hidden="true" />
            </span>
          </Link>

          <Link
            href="/explore/connections"
            className="focus-card group flex flex-col gap-4 rounded-2xl border border-border/70 bg-card/60 p-6 transition-all duration-200 hover:-translate-y-1 hover:border-primary/40 focus-visible:ring-2 focus-visible:ring-primary"
          >
            <span className="flex h-12 w-12 items-center justify-center rounded-xl border border-purple-500/30 bg-purple-500/10 text-purple-500">
              <Network className="h-6 w-6" aria-hidden="true" />
            </span>
            <div>
              <h3 className="font-display text-base font-bold text-foreground">Mạng Lưới Tri Thức</h3>
              <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                Liên kết thực thể dạng đồ thị: gắn kết 9 đỉnh, 162 phù điêu, nhân vật lịch sử và các trích dẫn
                thư tịch.
              </p>
            </div>
            <span className="mt-auto inline-flex items-center gap-1.5 text-xs font-semibold text-purple-500">
              Khám phá đồ thị liên kết
              <ArrowRight className="h-3.5 w-3.5 transition group-hover:translate-x-1" aria-hidden="true" />
            </span>
          </Link>

          <Link
            href="/vr360"
            className="focus-card group flex flex-col gap-4 rounded-2xl border border-border/70 bg-card/60 p-6 transition-all duration-200 hover:-translate-y-1 hover:border-primary/40 focus-visible:ring-2 focus-visible:ring-primary"
          >
            <span className="flex h-12 w-12 items-center justify-center rounded-xl border border-amber-500/30 bg-amber-500/10 text-amber-500">
              <Compass className="h-6 w-6" aria-hidden="true" />
            </span>
            <div>
              <h3 className="font-display text-base font-bold text-foreground">Thực Tế Ảo VR 360°</h3>
              <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                Tham quan toàn cảnh sân Thế Miếu và Hoàng thành Huế qua không gian ảnh toàn cảnh 360 độ độ phân
                giải cao.
              </p>
            </div>
            <span className="mt-auto inline-flex items-center gap-1.5 text-xs font-semibold text-amber-500">
              Trải nghiệm VR 360°
              <ArrowRight className="h-3.5 w-3.5 transition group-hover:translate-x-1" aria-hidden="true" />
            </span>
          </Link>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 5. 3D DIGITAL TWIN INSTRUMENT SHOWCASE                                   */}
      {/* ========================================================================= */}
      <section className="mt-16" aria-labelledby="three-d-section-heading">
        <div className="heritage-surface overflow-hidden rounded-2xl border border-border/80 p-6 sm:p-8 md:p-10">
          <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
                <Boxes className="h-3.5 w-3.5" aria-hidden="true" />
                Công cụ nghiên cứu không gian số
              </div>

              <h2
                id="three-d-section-heading"
                className="mt-4 font-display text-2xl font-bold tracking-tight text-foreground sm:text-3xl"
              >
                Cửu Đỉnh Trong Không Gian Ba Chiều (3D)
              </h2>

              <p className="mt-4 text-sm leading-relaxed text-muted-foreground sm:text-base">
                Trình xem 3D không chỉ là công nghệ hiển thị mà là công cụ trực quan hóa hiện vật di sản:
                xoay 360 độ quanh thân đỉnh, phóng to chi tiết từng nét chạm khắc nổi, dò tìm tọa độ điểm nóng
                (hotspots) và đối chiếu trực tiếp với bản dịch Hán-Nôm.
              </p>

              <div className="mt-6 flex flex-wrap gap-3">
                <Link
                  href="/urns/cao-dinh"
                  className="inline-flex min-h-10 items-center justify-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-xs font-semibold text-primary-foreground shadow-md shadow-primary/20 transition hover:bg-primary/90 focus-visible:ring-2 focus-visible:ring-primary"
                >
                  <Boxes className="h-4 w-4" aria-hidden="true" />
                  Mở Trình Xem 3D Cao Đỉnh
                  <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
                </Link>
                <Link
                  href="/cuu-dinh"
                  className="inline-flex min-h-10 items-center justify-center gap-2 rounded-lg border border-border bg-secondary/60 px-4 py-2.5 text-xs font-semibold text-foreground transition hover:bg-secondary focus-visible:ring-2 focus-visible:ring-primary"
                >
                  Danh mục 9 Đỉnh
                </Link>
              </div>

              <div className="mt-8 grid grid-cols-3 gap-3 border-t border-border/60 pt-5 text-xs">
                <div>
                  <span className="font-semibold text-foreground">Xoay & Zoom 3D</span>
                  <p className="mt-0.5 text-muted-foreground">Tương tác cảm ứng & chuột mượt mà</p>
                </div>
                <div>
                  <span className="font-semibold text-foreground">17 Hotspots / Đỉnh</span>
                  <p className="mt-0.5 text-muted-foreground">Định vị chính xác từng họa tiết</p>
                </div>
                <div>
                  <span className="font-semibold text-foreground">Chuẩn WCAG 2.2</span>
                  <p className="mt-0.5 text-muted-foreground">Hỗ trợ đọc văn bản thay thế</p>
                </div>
              </div>
            </div>

            {/* 3D Visual Poster */}
            <div className="relative flex aspect-[4/3] flex-col items-center justify-center rounded-xl border border-border/70 bg-secondary/30 p-6 text-center">
              <div
                aria-hidden="true"
                className="pointer-events-none absolute inset-0 rounded-xl bg-radial-gradient from-primary/10 via-transparent to-transparent opacity-60"
              />
              <Boxes className="h-16 w-16 text-primary/80" aria-hidden="true" />
              <div className="mt-4 font-serif text-lg font-bold text-foreground">CAO-DINH-v1.glb</div>
              <p className="mt-1 max-w-xs text-xs text-muted-foreground">
                Mô hình giải phẫu 3D 17 phù điêu trên Cao Đỉnh sẵn sàng tương tác trực tiếp trên trình duyệt
              </p>
              <Link
                href="/urns/cao-dinh"
                className="mt-5 inline-flex items-center gap-1.5 rounded-lg border border-primary/40 bg-primary/10 px-4 py-2 text-xs font-semibold text-primary transition hover:bg-primary hover:text-primary-foreground"
              >
                Khám phá ngay
                <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 6. PRIMARY SOURCES & RIGOROUS EPISTEMIC GOVERNANCE                        */}
      {/* ========================================================================= */}
      <section className="mt-16" aria-labelledby="epistemic-section-heading">
        <div className="heritage-surface p-6 sm:p-8 md:p-10">
          <div className="grid gap-10 lg:grid-cols-[1fr_1.1fr]">
            <div>
              <SectionHeading
                kicker="Tiêu Chuẩn Giám Định"
                title="Mọi Nhận Định Đều Gắn Liền Với Thư Tịch Chính Sử"
                lead="Chúng tôi áp dụng nguyên tắc giám định tri thức nghiêm ngặt: mọi nhận định lịch sử đều trích dẫn tập, quyển, trang từ chính sử và hồ sơ di sản quốc tế. Tuyệt đối không tạo dựng nguồn giả mạo."
              />

              <div className="mt-6 flex flex-col gap-3">
                <div className="rounded-lg border border-border/60 bg-card/60 p-4 text-xs leading-relaxed text-muted-foreground">
                  <span className="font-semibold text-foreground">5 Bộ Thư Tịch Nền Tảng:</span>
                  <ul className="mt-2 list-disc space-y-1 pl-4">
                    <li>Đại Nam Thực Lục (Chính biên, Đệ nhị kỷ)</li>
                    <li>Khâm Định Đại Nam Hội Điển Sự Lệ (Bộ Công & Lễ)</li>
                    <li>Đại Nam Nhất Thống Chí (Quốc Sử Quán)</li>
                    <li>Đồng Khánh Địa Dư Chí</li>
                    <li>Hồ sơ Đề cử Di sản Ký ức Thế giới UNESCO MOWCAP</li>
                  </ul>
                </div>

                <Link
                  href="/sources"
                  className="inline-flex min-h-10 items-center gap-2 self-start rounded-lg bg-primary px-4 py-2.5 text-xs font-semibold text-primary-foreground transition hover:bg-primary/90 focus-visible:ring-2 focus-visible:ring-primary"
                >
                  <Library className="h-4 w-4" aria-hidden="true" />
                  Tra Cứu Thư Viện Nguồn
                </Link>
              </div>
            </div>

            {/* Epistemic Class Explanation Cards */}
            <div className="grid content-start gap-3">
              {EPISTEMIC_CARDS.map((card) => (
                <div
                  key={card.label}
                  className="flex flex-col gap-2 rounded-xl border border-border/70 bg-card/60 p-4 transition hover:border-primary/40"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-foreground">{card.label}</span>
                    <span className="text-[10px] text-muted-foreground">{card.source}</span>
                  </div>
                  <p className="text-xs leading-relaxed text-muted-foreground">{card.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 7. AI HISTORY TUTOR WITH STRICT CITATION GROUNDING                        */}
      {/* ========================================================================= */}
      <section className="mt-16" aria-labelledby="ai-tutor-section-heading">
        <div className="heritage-hero rounded-2xl border border-primary/30 p-6 sm:p-8 md:p-10">
          <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-primary/40 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
                <Bot className="h-3.5 w-3.5" aria-hidden="true" />
                Trợ giảng Lịch sử AI RAG có dẫn nguồn
              </div>

              <h2
                id="ai-tutor-section-heading"
                className="mt-4 font-display text-2xl font-bold tracking-tight text-foreground sm:text-3xl"
              >
                Hỏi Đáp Lịch Sử Cùng Cô Giáo AI Có Trích Dẫn
              </h2>

              <p className="mt-3 text-sm leading-relaxed text-muted-foreground sm:text-base">
                Trợ giảng AI được xây dựng trên hệ thống truy xuất dữ liệu tăng cường (RAG) từ kho dữ liệu
                chính sử. Mọi câu trả lời đều đi kèm trích dẫn văn bản, mức độ tin cậy và không tạo thông tin
                sai lệch.
              </p>

              <div className="mt-6 flex flex-wrap gap-3">
                <Link
                  href="/ai"
                  className="inline-flex min-h-10 items-center justify-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-xs font-semibold text-primary-foreground shadow-md shadow-primary/20 transition hover:bg-primary/90 focus-visible:ring-2 focus-visible:ring-primary"
                >
                  <Sparkles className="h-4 w-4" aria-hidden="true" />
                  Mở Trợ Giảng Lịch Sử
                </Link>
                <Link
                  href="/practice"
                  className="inline-flex min-h-10 items-center justify-center gap-2 rounded-lg border border-border bg-secondary/60 px-4 py-2.5 text-xs font-semibold text-foreground transition hover:bg-secondary focus-visible:ring-2 focus-visible:ring-primary"
                >
                  Luyện tập trắc nghiệm
                </Link>
              </div>
            </div>

            {/* Prompt Suggestion Cards */}
            <div className="flex flex-col gap-2.5 rounded-xl border border-border/70 bg-card/60 p-5">
              <span className="text-xs font-semibold text-muted-foreground">
                Câu hỏi gợi ý có thể hỏi ngay:
              </span>
              {TUTOR_SAMPLE_PROMPTS.map((prompt) => (
                <Link
                  key={prompt}
                  href={`/ai?q=${encodeURIComponent(prompt)}`}
                  className="group flex items-center justify-between rounded-lg border border-border/60 bg-secondary/40 p-3 text-xs text-foreground transition hover:border-primary/40 hover:bg-secondary hover:text-primary"
                >
                  <span className="line-clamp-1">{prompt}</span>
                  <ArrowRight className="h-3.5 w-3.5 shrink-0 transition group-hover:translate-x-0.5" />
                </Link>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 8. FREE LEARNING ECOSYSTEM & CALL TO ACTION                               */}
      {/* ========================================================================= */}
      <section className="mt-16" aria-labelledby="learn-cta-heading">
        <div className="heritage-surface flex flex-col items-center rounded-2xl border border-border/80 p-8 text-center sm:p-12">
          <span className="flex h-14 w-14 items-center justify-center rounded-2xl border border-primary/30 bg-primary/10 text-primary">
            <GraduationCap className="h-7 w-7" aria-hidden="true" />
          </span>

          <h2
            id="learn-cta-heading"
            className="mt-5 font-serif text-2xl font-bold tracking-tight text-foreground sm:text-4xl"
          >
            Bắt Đầu Hành Trình Khám Phá Di Sản Miễn Phí
          </h2>

          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground sm:text-base">
            Mở cửa hoàn toàn miễn phí cho học sinh, sinh viên, giáo viên và những người yêu mến lịch sử Việt Nam.
            Tạo tài khoản để lưu giữ tiến độ học tập, huy hiệu và bộ sưu tập của riêng bạn.
          </p>

          <div className="mt-8 flex flex-wrap justify-center gap-3.5">
            <Link
              href="/practice"
              className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/20 transition hover:bg-primary/90 focus-visible:ring-2 focus-visible:ring-primary"
            >
              <Compass className="h-4 w-4" aria-hidden="true" />
              Bắt đầu luyện tập ngay
            </Link>

            <Link
              href={isAuthed ? "/dashboard" : "/login"}
              className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-border bg-secondary/80 px-6 py-3 text-sm font-semibold text-foreground transition hover:bg-secondary focus-visible:ring-2 focus-visible:ring-primary"
            >
              <UserRound className="h-4 w-4 text-primary" aria-hidden="true" />
              {isAuthed ? "Vào bảng học tập của tôi" : "Đăng ký / Đăng nhập tài khoản"}
            </Link>
          </div>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-6 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-accent" />
              Không bắt buộc đăng nhập để tra cứu
            </span>
            <span className="inline-flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-accent" />
              Dữ liệu chuẩn xác có dẫn nguồn
            </span>
            <span className="inline-flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-accent" />
              Tương thích mọi thiết bị di động & máy tính
            </span>
          </div>
        </div>
      </section>
    </main>
  );
}
