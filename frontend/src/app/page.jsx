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
  Compass,
  Crown,
  Eye,
  FileText,
  Flame,
  Globe,
  Globe2,
  GraduationCap,
  Heart,
  History,
  Info,
  Landmark,
  Layers,
  Library,
  Map as MapIcon,
  MapPin,
  Maximize2,
  Medal,
  Milestone,
  Mountain,
  Network,
  RotateCcw,
  Scale,
  Scroll,
  ScrollText,
  Search,
  Share2,
  Shield,
  ShieldCheck,
  Sparkles,
  Star,
  TreePine,
  Trophy,
  UserCheck,
  UserRound,
  Users,
  Video,
  Volume2,
  Waves,
  ZoomIn,
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

const CATEGORY_TABS = [
  { id: "all", label: "Tất cả (162)", icon: Layers },
  { id: "dia_ly", label: "Địa lý & Núi sông biển", icon: Mountain, match: ["dia_ly", "son", "giang", "ha", "hai", "quan", "khau", "bien"] },
  { id: "dong_vat", label: "Động vật & Linh thú", icon: Flame, match: ["dong_vat", "linh_thu", "thu", "dieu", "ngu", "long", "ho", "tuong", "ma"] },
  { id: "thao_moc", label: "Thảo mộc & Nông sản", icon: TreePine, match: ["thao_moc", "nong_nghiep", "moc", "hoa", "qua", "dau", "canh", "nhu", "que"] },
  { id: "vo_bi", label: "Vũ khí & Võ bị", icon: ShieldCheck, match: ["vo_bi", "phao", "thuong", "dao", "no", "hoa"] },
  { id: "giao_thuong", label: "Giao thương & Thuyền bè", icon: Waves, match: ["giao_thuong", "thuyen", "dinh", "xa"] },
  { id: "thien_van", label: "Thiên văn & Vũ trụ", icon: Globe2, match: ["thien_van", "nhat", "nguyet", "tinh", "dau", "van", "phong", "loi", "hong", "vu"] },
];

const URN_PROFILES = [
  {
    slug: "cao-dinh",
    nameVi: "Cao Đỉnh",
    hanNom: "高",
    emperor: "Thế Tổ Cao Hoàng Đế (Gia Long)",
    position: "Trung vị (Chính giữa)",
    weight: "2.603 kg",
    height: "2,50 m",
    highlights: ["Rồng (Long)", "Đông Hải (Biển Đông)", "Kênh Vĩnh Tế", "Núi Thiên Tôn", "Trầm Hương"],
    colorBadge: "from-amber-500/20 to-primary/10",
  },
  {
    slug: "nhan-dinh",
    nameVi: "Nhân Đỉnh",
    hanNom: "仁",
    emperor: "Thánh Tổ Nhân Hoàng Đế (Minh Mạng)",
    position: "Tả nhất (Trái thứ nhất)",
    weight: "2.515 kg",
    height: "2,31 m",
    highlights: ["Kỳ Lân", "Nam Hải (Biển Nam)", "Sông Hương", "Núi Ngự Bình", "Cây Ngô Đồng"],
    colorBadge: "from-emerald-500/20 to-accent/10",
  },
  {
    slug: "chuong-dinh",
    nameVi: "Chương Đỉnh",
    hanNom: "章",
    emperor: "Hiến Tổ Chương Hoàng Đế (Thiệu Trị)",
    position: "Hữu nhất (Phải thứ nhất)",
    weight: "2.060 kg",
    height: "2,30 m",
    highlights: ["Linh Quy", "Tây Hải (Vịnh Thái Lan)", "Sông Gianh", "Núi Kim Phụng", "Mông Đồng Thuyền"],
    colorBadge: "from-blue-500/20 to-sky-500/10",
  },
  {
    slug: "anh-dinh",
    nameVi: "Anh Đỉnh",
    hanNom: "英",
    emperor: "Dực Tông Anh Hoàng Đế (Tự Đức)",
    position: "Tả nhị (Trái thứ hai)",
    weight: "2.595 kg",
    height: "2,31 m",
    highlights: ["Nghê thần", "Sao Bắc Đẩu", "Sông Mã", "Sông Lô", "Núi Hồng Lĩnh"],
    colorBadge: "from-purple-500/20 to-indigo-500/10",
  },
  {
    slug: "nghi-dinh",
    nameVi: "Nghị Đỉnh",
    hanNom: "毅",
    emperor: "Cung Tông Nghị Hoàng Đế (Dục Đức)",
    position: "Hữu nhị (Phải thứ hai)",
    weight: "2.593 kg",
    height: "2,31 m",
    highlights: ["Voi (Tượng)", "Bạch Đằng Giang", "Cửa Thuận An", "Quảng Bình Quan", "Gỗ Đàn Mộc"],
    colorBadge: "from-rose-500/20 to-red-500/10",
  },
  {
    slug: "thuan-dinh",
    nameVi: "Thuần Đỉnh",
    hanNom: "純",
    emperor: "Cảnh Tông Thuần Hoàng Đế (Đồng Khánh)",
    position: "Tả tam (Trái thứ ba)",
    weight: "2.383 kg",
    height: "2,32 m",
    highlights: ["Lý Ngưu (Trâu rừng)", "Sông Thạch Hãn", "Cửa Cần Giờ", "Núi Tản Viên", "Cá Leo Núi"],
    colorBadge: "from-orange-500/20 to-amber-500/10",
  },
  {
    slug: "tuyen-dinh",
    nameVi: "Tuyên Đỉnh",
    hanNom: "宣",
    emperor: "Hoằng Tông Tuyên Hoàng Đế (Khải Định)",
    position: "Hữu tam (Phải thứ ba)",
    weight: "2.064 kg",
    height: "2,31 m",
    highlights: ["Heo rừng (Thỉ)", "Sông Hồng (Nhĩ Hà)", "Sông Lam", "Mũi Đại Lãnh", "Tổ Yến"],
    colorBadge: "from-teal-500/20 to-cyan-500/10",
  },
  {
    slug: "du-dinh",
    nameVi: "Dụ Đỉnh",
    hanNom: "裕",
    emperor: "Tượng trưng sự thịnh vượng & trù phú",
    position: "Tả tứ (Trái ngoài cùng)",
    weight: "2.016 kg",
    height: "2,34 m",
    highlights: ["Dê (Dương)", "Sông Vệ", "Cửa Hàn (Đà Nẵng)", "Đèo Hải Vân", "Cây Tùng"],
    colorBadge: "from-lime-500/20 to-emerald-500/10",
  },
  {
    slug: "huyen-dinh",
    nameVi: "Huyền Đỉnh",
    hanNom: "玄",
    emperor: "Tượng trưng sự uy nghiêm & thâm viễn",
    position: "Hữu tứ (Phải ngoài cùng)",
    weight: "1.935 kg",
    height: "2,31 m",
    highlights: ["Trăn gấm (Mãng Xà)", "Tiền Giang & Hậu Giang", "Sông Thao", "Đèo Hoành Sơn", "Hoa Lan"],
    colorBadge: "from-slate-500/20 to-zinc-500/10",
  },
];

const SOLUTION_CARDS = [
  {
    step: "01",
    icon: Boxes,
    title: "Mô Hình 3D Đa Chiều (Digital Twin)",
    desc: "Tái hiện chính xác 9 đỉnh đồng và 162 họa tiết nổi trong không gian 3D tương tác. Phóng to, xoay 360 độ và dò tìm điểm chạm lịch sử.",
    href: "/urns/cao-dinh",
    cta: "Trải nghiệm 3D",
    gradient: "from-amber-500/15 via-primary/5 to-transparent",
    accentColor: "text-amber-500",
  },
  {
    step: "02",
    icon: MapPin,
    title: "Bản Đồ Giang Sơn & Hải Cương",
    desc: "Tọa độ vệ tinh WGS84 cho toàn bộ danh sơn, đại giang, hải khẩu và ba vùng biển Đông Hải, Nam Hải, Tây Hải được khắc trên đỉnh.",
    href: "/map",
    cta: "Mở bản đồ di sản",
    gradient: "from-emerald-500/15 via-accent/5 to-transparent",
    accentColor: "text-emerald-500",
  },
  {
    step: "03",
    icon: Bot,
    title: "Trợ Giảng Lịch Sử AI Chuẩn Nguồn",
    desc: "Hệ thống AI đối chiếu ngữ liệu thời gian thực, tuyệt đối không bịa đặt nguồn, trích dẫn chuẩn xác theo Đại Nam Thực Lục và Hội Điển.",
    href: "/ai",
    cta: "Hỏi đáp cùng Cô giáo AI",
    gradient: "from-blue-500/15 via-sky-500/5 to-transparent",
    accentColor: "text-blue-500",
  },
  {
    step: "04",
    icon: GraduationCap,
    title: "Hệ Thống Luyện Tập & Chứng Chỉ",
    desc: "Trắc nghiệm di sản thông minh, lộ trình tích lũy điểm kinh nghiệm (XP), bảng vàng xếp hạng và chứng chỉ hoàn thành học phần.",
    href: "/practice",
    cta: "Vào luyện tập ngay",
    gradient: "from-purple-500/15 via-indigo-500/5 to-transparent",
    accentColor: "text-purple-500",
  },
];

const TUTOR_PROMPTS = [
  "Vì sao vua Minh Mạng chuẩn chỉ cho đúc Cửu Đỉnh vào năm 1835?",
  "Hình tượng Đông Hải và Nam Hải trên Cửu Đỉnh khẳng định chủ quyền ra sao?",
  "Những loại thảo mộc, gỗ quý và cây lương thực nào được chạm khắc trên 9 đỉnh?",
  "Sông Bạch Đằng và Quảng Bình Quan nằm ở vị trí nào trên Cửu Đỉnh?",
];

const PRIMARY_BIBLIO_SOURCES = [
  {
    title: "Đại Nam Thực Lục",
    author: "Quốc Sử Quán triều Nguyễn",
    edition: "Chính biên, Đệ nhị kỷ (Quyển 162, 165, 175)",
    role: "Chính sử biên niên ghi chép tường tận quá trình chuẩn chỉ, bản vẽ và lễ khánh thành đặt đỉnh.",
  },
  {
    title: "Khâm Định Đại Nam Hội Điển Sự Lệ",
    author: "Nội Các triều Nguyễn",
    edition: "Bộ Công & Bộ Lễ biên soạn",
    role: "Quy định điển chế, khối lượng đồng, kích thước khuôn đúc và thứ tự sắp đặt 9 đỉnh trước sân Thế Miếu.",
  },
  {
    title: "Đại Nam Nhất Thống Chí",
    author: "Quốc Sử Quán triều Nguyễn",
    edition: "Bộ địa chí quốc gia hoàn bị",
    role: "Khảo cứu cặn kẽ từng danh lam thắng cảnh, sông ngòi, đèo ải và cương giới hải đảo khắc trên Cửu Đỉnh.",
  },
  {
    title: "Hồ Sơ Đề Cử UNESCO MOWCAP",
    author: "Ủy Ban Quốc Gia UNESCO Việt Nam",
    edition: "Ký ức Thế giới Châu Á - Thái Bình Dương",
    role: "Bảo chứng giá trị tư liệu độc bản, kỹ thuật đúc đồng đỉnh cao và tính toàn vẹn di sản nhân loại.",
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
      title: "Lưu Niên Sử Kí — Chạm Công Nghệ, Mở Trang Sử Vàng | Cửu Đỉnh Triều Nguyễn",
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
          listHistoryEntities({ entityType: "relief", limit: 36 }),
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

  const activeUrn = useMemo(() => {
    return URN_PROFILES.find((u) => u.slug === selectedUrnSlug) || URN_PROFILES[0];
  }, [selectedUrnSlug]);

  return (
    <main className="min-h-screen overflow-x-hidden bg-background text-foreground" id="main-content">
      {/* ========================================================================= */}
      {/* 1. CINEMATIC HERO SECTION                                                 */}
      {/* ========================================================================= */}
      <section className="relative min-h-[92vh] flex items-center justify-center overflow-hidden py-16 md:py-24">
        {/* Imperial Gold Ambient Glow Background */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 bg-gradient-to-b from-primary/10 via-background/60 to-background"
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] rounded-full bg-primary/15 blur-[140px] opacity-70"
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute bottom-10 right-10 w-[500px] h-[500px] rounded-full bg-accent/10 blur-[130px] opacity-40"
        />

        <div className="container mx-auto px-4 sm:px-6 relative z-10">
          <div className="max-w-5xl mx-auto text-center">
            {/* UNESCO Tag */}
            <div className="inline-flex items-center gap-2.5 rounded-full border border-primary/40 bg-primary/10 px-4 py-2 text-xs md:text-sm font-semibold text-primary backdrop-blur-md shadow-sm mb-6 animate-fade-in">
              <Landmark className="h-4 w-4 text-primary" aria-hidden="true" />
              <span>Di sản Tư liệu Ký ức Thế giới (UNESCO MOWCAP) · Hoàng thành Huế</span>
            </div>

            {/* Grand Title */}
            <h1 className="font-serif text-4xl sm:text-6xl md:text-7xl lg:text-8xl font-black tracking-tight headline-tracking mb-4">
              <span className="text-gradient-gold glow-gold">Lưu Niên Sử Kí</span>
            </h1>

            <p className="font-serif text-2xl sm:text-3xl md:text-4xl italic text-foreground/90 font-medium mb-6">
              Chạm Công Nghệ, Mở Trang Sử Vàng
            </p>

            <p className="text-base sm:text-lg md:text-xl text-muted-foreground leading-relaxed max-w-3xl mx-auto mb-10 text-pretty">
              Khám phá <strong className="text-foreground font-semibold">Cửu Đỉnh</strong> – bảo vật Hoàng cung triều Nguyễn
              với công nghệ mô hình 3D đa chiều, bản đồ định vị WGS84, pho bách khoa toàn thư 162 họa tiết và Trợ giảng Lịch sử AI có dẫn nguồn chính sử.
            </p>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center justify-center gap-4 mb-14">
              <Link
                href="/urns/cao-dinh"
                className="inline-flex min-h-12 items-center justify-center gap-2.5 rounded-xl bg-gradient-to-r from-primary via-amber-500 to-primary px-7 py-3.5 text-base font-bold text-primary-foreground shadow-lg shadow-primary/25 transition-all duration-300 hover:scale-105 hover:shadow-primary/40 focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
              >
                <Boxes className="h-5 w-5" aria-hidden="true" />
                Khám phá Cửu Đỉnh 3D
                <ArrowRight className="h-5 w-5" aria-hidden="true" />
              </Link>

              <Link
                href="/atlas"
                className="inline-flex min-h-12 items-center justify-center gap-2.5 rounded-xl border border-primary/40 bg-card/80 px-6 py-3.5 text-base font-bold text-foreground backdrop-blur-md transition-all duration-300 hover:border-primary hover:bg-secondary hover:text-primary focus-visible:ring-2 focus-visible:ring-primary"
              >
                <Layers className="h-5 w-5 text-primary" aria-hidden="true" />
                Atlas 162 Họa Tiết
              </Link>

              <Link
                href="/map"
                className="inline-flex min-h-12 items-center justify-center gap-2.5 rounded-xl border border-border/80 bg-card/50 px-5 py-3.5 text-base font-semibold text-muted-foreground transition hover:border-border hover:bg-card hover:text-foreground focus-visible:ring-2 focus-visible:ring-primary"
              >
                <MapIcon className="h-5 w-5 text-accent" aria-hidden="true" />
                Bản đồ Giang Sơn
              </Link>

              <Link
                href="/vr360"
                className="inline-flex min-h-12 items-center justify-center gap-2.5 rounded-xl border border-border/80 bg-card/50 px-5 py-3.5 text-base font-semibold text-muted-foreground transition hover:border-border hover:bg-card hover:text-foreground focus-visible:ring-2 focus-visible:ring-primary"
              >
                <Compass className="h-5 w-5 text-amber-500" aria-hidden="true" />
                VR 360° Thế Miếu
              </Link>
            </div>

            {/* Impressive Counter Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
              <div className="p-5 rounded-2xl bg-card/60 border border-border/70 backdrop-blur-md hover:border-primary/50 transition duration-300">
                <div className="text-3xl md:text-4xl font-extrabold text-primary mb-1">9</div>
                <div className="text-xs md:text-sm text-muted-foreground font-medium">Đỉnh đồng báu vật</div>
              </div>
              <div className="p-5 rounded-2xl bg-card/60 border border-border/70 backdrop-blur-md hover:border-primary/50 transition duration-300">
                <div className="text-3xl md:text-4xl font-extrabold text-foreground mb-1">162</div>
                <div className="text-xs md:text-sm text-muted-foreground font-medium">Họa tiết chạm khắc</div>
              </div>
              <div className="p-5 rounded-2xl bg-card/60 border border-border/70 backdrop-blur-md hover:border-primary/50 transition duration-300">
                <div className="text-3xl md:text-4xl font-extrabold text-accent mb-1">100%</div>
                <div className="text-xs md:text-sm text-muted-foreground font-medium">Khảo chứng Hán-Nôm</div>
              </div>
              <div className="p-5 rounded-2xl bg-card/60 border border-border/70 backdrop-blur-md hover:border-primary/50 transition duration-300">
                <div className="text-3xl md:text-4xl font-extrabold text-foreground mb-1">1835</div>
                <div className="text-xs md:text-sm text-muted-foreground font-medium">Năm ban chỉ đúc đỉnh</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Verification Disclaimer */}
      <div className="container mx-auto px-4 sm:px-6 my-6">
        <VerificationNote />
      </div>

      {error ? (
        <div className="container mx-auto px-4 sm:px-6 my-4">
          <div role="alert" className="rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
            Không tải được một số dữ liệu lịch sử: {error}
          </div>
        </div>
      ) : null}

      {/* ========================================================================= */}
      {/* 2. PROBLEM & CONTEXT SECTION (From luuniensuki.pages.dev inspiration)     */}
      {/* ========================================================================= */}
      <section className="relative py-20 md:py-28 overflow-hidden">
        <div className="container mx-auto px-4 sm:px-6 relative z-10">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            {/* Left Column: Imperial Arched Frame */}
            <div className="relative flex justify-center">
              <div className="relative max-w-md w-full">
                {/* Rotating decorative gold rings */}
                <div className="absolute -inset-4 border border-primary/30 rounded-t-full rounded-b-2xl transform rotate-1 scale-[1.02] pointer-events-none" />
                <div className="absolute -inset-4 border border-primary/15 rounded-t-full rounded-b-2xl transform -rotate-1 scale-[1.04] pointer-events-none" />

                <div className="relative rounded-t-full rounded-b-2xl overflow-hidden shadow-2xl border border-primary/30 aspect-[3/4] bg-card group">
                  <div className="absolute inset-0 bg-gradient-to-t from-background via-black/30 to-transparent z-10 opacity-90" />
                  
                  {/* Decorative engraving silhouette backdrop */}
                  <div className="flex h-full w-full items-center justify-center p-8 text-center bg-secondary/40">
                    <div className="flex flex-col items-center gap-4">
                      <span className="font-serif text-7xl font-bold text-gradient-gold glow-gold">Cửu Đỉnh</span>
                      <p className="font-serif text-lg italic text-bronze-accent max-w-xs">
                        Pho bách khoa toàn thư bằng đồng của giang sơn Đại Nam
                      </p>
                    </div>
                  </div>

                  {/* Floating Museum Caption Card */}
                  <div className="absolute bottom-6 left-6 right-6 p-5 bg-background/85 backdrop-blur-md border border-primary/30 rounded-2xl z-20">
                    <div className="flex items-start gap-3.5">
                      <Scroll className="w-6 h-6 text-primary shrink-0 mt-0.5" />
                      <div>
                        <h4 className="font-serif font-bold text-base text-primary mb-1">
                          Đại Nam Nhất Thống
                        </h4>
                        <p className="text-xs text-muted-foreground leading-relaxed">
                          162 bức phù điêu khắc họa trọn vẹn hồn sông núi, sinh quyển và cương thổ Đại Nam từ Ải Nam Quan đến Mũi Cà Mau và Biển Đông.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Narrative Copy */}
            <div className="space-y-6">
              <div className="inline-flex items-center gap-2 text-primary font-bold tracking-widest uppercase text-xs border-b border-primary/30 pb-2">
                <Info className="w-4 h-4" />
                <span>Thực trạng & Thách thức bảo tồn</span>
              </div>

              <h2 className="font-serif text-3xl sm:text-4xl md:text-5xl font-bold leading-tight">
                Khoảng cách thế hệ & <br />
                <span className="text-gradient-gold glow-gold">Nghệ thuật đúc đồng 187 năm</span>
              </h2>

              <div className="space-y-4 text-base md:text-lg text-muted-foreground leading-relaxed">
                <p>
                  Trải qua gần hai thế kỷ chịu đựng thời tiết khắc nghiệt và chiến tranh, các hoa văn chạm nổi trên chín chiếc đỉnh đồng tại Thế Miếu đối mặt với nguy cơ mài mòn, phai mờ thông điệp lịch sử.
                </p>
                <p>
                  Chữ Hán-Nôm cổ cùng cách thức trưng bày tĩnh tại bảo tàng khiến thế hệ trẻ và công chúng quốc tế gặp không ít rào cản khi muốn tiếp cận, giải mã ý nghĩa sâu xa của từng họa tiết.
                </p>
                <blockquote className="border-l-4 border-primary pl-5 py-2 italic text-foreground text-lg md:text-xl font-serif">
                  "Lịch sử không hề khô khan, chỉ là chúng ta chưa tìm thấy chiếc cầu nối công nghệ thích hợp để chạm vào chiều sâu văn hóa dân tộc."
                </blockquote>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 3. SOLUTION ECOSYSTEM (Hệ Sinh Thái Lưu Niên Sử Kí)                        */}
      {/* ========================================================================= */}
      <section className="relative py-20 md:py-28 overflow-hidden bg-secondary/30 border-y border-border/60">
        <div className="container mx-auto px-4 sm:px-6 relative z-10">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <div className="inline-flex items-center gap-2 bg-primary/10 px-4 py-1.5 rounded-full text-xs font-semibold text-primary uppercase tracking-wider mb-4">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Giải pháp số toàn diện</span>
            </div>
            <h2 className="font-serif text-3xl sm:text-5xl font-bold mb-4">
              Hệ Sinh Thái <span className="text-gradient-gold glow-gold">Lưu Niên Sử Kí</span>
            </h2>
            <p className="text-base sm:text-lg text-muted-foreground">
              Tích hợp công nghệ số hiện đại để giải phóng di sản khỏi khuôn khổ bảo tàng tĩnh, đưa lịch sử đến gần hơn với mọi người.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {SOLUTION_CARDS.map((card) => {
              const Icon = card.icon;
              return (
                <Link
                  key={card.step}
                  href={card.href}
                  className="group relative p-7 rounded-2xl bg-card/70 border border-border/70 backdrop-blur-md hover:border-primary/50 transition-all duration-300 hover:-translate-y-1.5 hover:shadow-xl flex flex-col justify-between"
                >
                  <div className="absolute top-4 right-4 font-serif text-4xl font-black text-foreground/10 group-hover:text-primary/20 transition-colors">
                    {card.step}
                  </div>

                  <div>
                    <div className="mb-5 inline-flex p-3.5 rounded-xl bg-primary/10 group-hover:bg-primary/20 transition-colors text-primary">
                      <Icon className="w-6 h-6" />
                    </div>
                    <h3 className="font-serif font-bold text-xl mb-3 text-foreground group-hover:text-primary transition-colors">
                      {card.title}
                    </h3>
                    <p className="text-xs md:text-sm text-muted-foreground leading-relaxed mb-6">
                      {card.desc}
                    </p>
                  </div>

                  <div className="flex items-center gap-1.5 text-xs font-bold text-primary">
                    <span>{card.cta}</span>
                    <ArrowRight className="w-3.5 h-3.5 transition group-hover:translate-x-1" />
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 4. THE NINE DYNASTIC URNS MASTER SECTION                                 */}
      {/* ========================================================================= */}
      <section className="relative py-20 md:py-28 overflow-hidden">
        <div className="container mx-auto px-4 sm:px-6 relative z-10">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
            <div>
              <div className="inline-flex items-center gap-2 text-primary font-bold tracking-widest uppercase text-xs border-b border-primary/30 pb-2 mb-3">
                <Crown className="w-4 h-4" />
                <span>Chín Chiếc Đỉnh Đồng Báu Vật</span>
              </div>
              <h2 className="font-serif text-3xl sm:text-5xl font-bold">
                Cửu Đỉnh — <span className="text-gradient-gold">Chín Báu Vật Hoàng Cung</span>
              </h2>
            </div>
            <Link
              href="/cuu-dinh"
              className="inline-flex items-center gap-2 text-sm font-semibold text-primary hover:underline self-start md:self-auto"
            >
              Mở toàn bộ danh mục 9 Đỉnh
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {/* Urn Selector Tabs */}
          <div className="grid grid-cols-3 sm:grid-cols-9 gap-2 mb-8">
            {URN_PROFILES.map((urn) => {
              const isSelected = urn.slug === selectedUrnSlug;
              return (
                <button
                  key={urn.slug}
                  type="button"
                  onClick={() => setSelectedUrnSlug(urn.slug)}
                  className={cn(
                    "flex flex-col items-center gap-1.5 p-3 rounded-xl border transition-all duration-200 focus-visible:ring-2 focus-visible:ring-primary",
                    isSelected
                      ? "border-primary bg-primary/15 text-primary shadow-md shadow-primary/20 scale-105"
                      : "border-border/70 bg-card/50 text-muted-foreground hover:border-primary/40 hover:bg-secondary hover:text-foreground",
                  )}
                >
                  <span className="font-serif text-2xl font-bold">{urn.hanNom}</span>
                  <span className="text-xs font-semibold">{urn.nameVi.split(" ")[0]}</span>
                </button>
              );
            })}
          </div>

          {/* Spotlight Detailed Card for Selected Urn */}
          <div className="heritage-surface rounded-2xl border border-border/80 p-6 sm:p-8 md:p-10 shadow-2xl backdrop-blur-xl">
            <div className="grid lg:grid-cols-[1.1fr_0.9fr] gap-8 items-center">
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/15 font-serif text-xl font-bold text-primary ring-1 ring-primary/30">
                    {activeUrn.hanNom}
                  </span>
                  <div>
                    <h3 className="font-serif text-2xl sm:text-3xl font-bold text-foreground">
                      {activeUrn.nameVi} ({activeUrn.hanNom})
                    </h3>
                    <p className="text-xs sm:text-sm text-muted-foreground">{activeUrn.position}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 text-xs sm:text-sm mb-6 p-4 rounded-xl bg-secondary/40 border border-border/60">
                  <div>
                    <span className="text-muted-foreground">Phụng thờ miếu hiệu:</span>
                    <p className="font-bold text-foreground mt-0.5">{activeUrn.emperor}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Thông số kỹ thuật:</span>
                    <p className="font-bold text-foreground mt-0.5">Khối lượng: {activeUrn.weight} · Cao: {activeUrn.height}</p>
                  </div>
                </div>

                <div className="mb-6">
                  <span className="text-xs font-bold uppercase tracking-wider text-bronze-accent">
                    18 Họa tiết nổi tiêu biểu trên đỉnh:
                  </span>
                  <div className="mt-2.5 flex flex-wrap gap-2">
                    {activeUrn.highlights.map((h) => (
                      <span
                        key={h}
                        className="rounded-lg bg-card/90 px-3 py-1.5 text-xs font-medium text-foreground ring-1 ring-border/80 shadow-sm"
                      >
                        {h}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="flex flex-wrap gap-3">
                  <Link
                    href={`/urns/${selectedUrnSlug}`}
                    className="inline-flex min-h-10 items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-xs font-semibold text-primary-foreground shadow-md shadow-primary/20 transition hover:bg-primary/90"
                  >
                    <Boxes className="w-4 h-4" />
                    Xem mô hình 3D {activeUrn.nameVi}
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>

                  <Link
                    href={`/cuu-dinh/${selectedUrnSlug}`}
                    className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-border bg-secondary/60 px-4 py-2.5 text-xs font-semibold text-foreground transition hover:bg-secondary"
                  >
                    Tìm hiểu toàn bộ 18 hình đúc
                  </Link>
                </div>
              </div>

              {/* Urn Visual Art Panel */}
              <div className="relative flex aspect-[4/3] flex-col items-center justify-center rounded-2xl border border-border/80 bg-gradient-to-br from-secondary/60 via-card/70 to-background p-8 text-center shadow-inner">
                <div className="font-serif text-6xl md:text-8xl font-black text-gradient-gold glow-gold mb-3">
                  {activeUrn.hanNom}
                </div>
                <div className="font-serif text-xl font-bold text-foreground mb-1">{activeUrn.nameVi}</div>
                <p className="text-xs text-muted-foreground max-w-xs">{activeUrn.emperor}</p>
                <div className="mt-4 inline-flex items-center gap-1.5 text-[11px] font-semibold text-primary bg-primary/10 px-3 py-1 rounded-full">
                  <Boxes className="w-3 h-3" />
                  18 hình khắc nổi bằng đồng tinh xảo
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 5. ATLAS 162 MOTIF SPECTRUM                                               */}
      {/* ========================================================================= */}
      <section className="relative py-20 md:py-28 overflow-hidden bg-secondary/20 border-y border-border/60">
        <div className="container mx-auto px-4 sm:px-6 relative z-10">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8">
            <div>
              <div className="inline-flex items-center gap-2 text-primary font-bold tracking-widest uppercase text-xs border-b border-primary/30 pb-2 mb-3">
                <Layers className="w-4 h-4" />
                <span>Pho Bách Khoa Toàn Thư Bằng Đồng</span>
              </div>
              <h2 className="font-serif text-3xl sm:text-5xl font-bold">
                Atlas 162 Họa Tiết — <span className="text-gradient-gold">Hồn Non Sông Gấm Vóc</span>
              </h2>
            </div>
            <Link
              href="/atlas"
              className="inline-flex items-center gap-2 text-sm font-semibold text-primary hover:underline self-start md:self-auto"
            >
              Xem ma trận đầy đủ
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {/* Category Filter Pills */}
          <div className="flex flex-wrap items-center gap-2 mb-8 pb-4 border-b border-border/60">
            {CATEGORY_TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeCategory === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveCategory(tab.id)}
                  className={cn(
                    "inline-flex items-center gap-1.5 rounded-xl px-4 py-2.5 text-xs font-semibold transition-all focus-visible:ring-2 focus-visible:ring-primary",
                    isActive
                      ? "bg-primary text-primary-foreground shadow-md shadow-primary/25 scale-105"
                      : "border border-border/70 bg-card/60 text-muted-foreground hover:bg-secondary hover:text-foreground",
                  )}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Reliefs Cards Showcase */}
          {loading ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {[...Array(12)].map((_, i) => (
                <div key={i} className="rounded-2xl border border-border/70 bg-card/60 p-4">
                  <Skeleton className="aspect-[4/3] w-full rounded-xl" />
                  <Skeleton className="mt-3 h-4 w-3/4" />
                  <Skeleton className="mt-2 h-3 w-1/2" />
                </div>
              ))}
            </div>
          ) : filteredReliefs.length > 0 ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
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
                    className="focus-card group flex flex-col overflow-hidden rounded-2xl border border-border/70 bg-card/70 p-3.5 transition-all duration-300 hover:-translate-y-1.5 hover:border-primary/50 hover:shadow-xl focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    <div className="relative aspect-[4/3] w-full overflow-hidden rounded-xl bg-secondary/50 mb-3">
                      {thumb ? (
                        <img
                          src={thumb}
                          alt={name}
                          loading="lazy"
                          decoding="async"
                          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
                        />
                      ) : (
                        <div className="flex h-full w-full flex-col items-center justify-center gap-1 text-muted-foreground p-2">
                          {hanNom ? (
                            <span className="font-serif text-3xl font-bold text-bronze-accent transition group-hover:scale-110">
                              {hanNom}
                            </span>
                          ) : (
                            <span className="font-serif text-xl text-bronze-accent">#{num || "·"}</span>
                          )}
                        </div>
                      )}

                      {/* Number Badge */}
                      {num ? (
                        <span className="absolute left-2 top-2 rounded-md bg-black/70 px-1.5 py-0.5 text-[10px] font-bold text-white backdrop-blur-sm">
                          #{num}
                        </span>
                      ) : null}

                      {/* Han Nom Glyph Overlay */}
                      {thumb && hanNom ? (
                        <span className="absolute bottom-2 right-2 rounded-md bg-background/90 px-1.5 py-0.5 font-serif text-xs font-bold text-primary backdrop-blur-sm shadow-sm">
                          {hanNom}
                        </span>
                      ) : null}
                    </div>

                    <div className="flex flex-1 flex-col justify-between">
                      <div>
                        <h4 className="line-clamp-1 text-xs sm:text-sm font-bold text-foreground group-hover:text-primary transition-colors">
                          {name}
                        </h4>
                        <p className="mt-0.5 text-[11px] text-muted-foreground truncate">
                          {urnNameFromSlug(urnSlug)}
                        </p>
                      </div>

                      {relief.summary_vi ? (
                        <p className="mt-2 line-clamp-2 text-[10px] sm:text-[11px] leading-relaxed text-muted-foreground/80">
                          {relief.summary_vi}
                        </p>
                      ) : null}
                    </div>
                  </Link>
                );
              })}
            </div>
          ) : (
            <div className="rounded-2xl border border-dashed border-border/80 bg-card/40 py-12 text-center text-sm text-muted-foreground">
              Không tìm thấy phù điêu nào trong nhóm này.
            </div>
          )}
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 6. PRIMARY HISTORICAL SOURCES & EPISTEMIC STANDARDS                       */}
      {/* ========================================================================= */}
      <section className="relative py-20 md:py-28 overflow-hidden">
        <div className="container mx-auto px-4 sm:px-6 relative z-10">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            <div>
              <div className="inline-flex items-center gap-2 text-primary font-bold tracking-widest uppercase text-xs border-b border-primary/30 pb-2 mb-4">
                <Library className="w-4 h-4" />
                <span>Bảo chứng thư tịch chính sử</span>
              </div>

              <h2 className="font-serif text-3xl sm:text-4xl md:text-5xl font-bold leading-tight mb-6">
                Mọi Nhận Định Đều Được <br />
                <span className="text-gradient-gold glow-gold">Khảo Chứng Sử Liệu Chính Thống</span>
              </h2>

              <p className="text-base md:text-lg text-muted-foreground leading-relaxed mb-8">
                Khác biệt lớn nhất của Lưu Niên Sử Kí là tính xác thực học thuật: từng sự kiện, từng họa tiết đúc nổi đều trích dẫn chính xác tập, quyển, trang từ quốc sử triều Nguyễn và hồ sơ đệ cử UNESCO.
              </p>

              <Link
                href="/sources"
                className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-primary px-6 py-3 text-sm font-bold text-primary-foreground shadow-lg shadow-primary/20 transition hover:bg-primary/90"
              >
                <Library className="w-4 h-4" />
                Tra cứu Thư viện Nguồn
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            {/* 4 Primary Sources Cards */}
            <div className="grid sm:grid-cols-2 gap-4">
              {PRIMARY_BIBLIO_SOURCES.map((src) => (
                <div
                  key={src.title}
                  className="p-5 rounded-2xl bg-card/70 border border-border/70 backdrop-blur-md hover:border-primary/50 transition duration-300 flex flex-col justify-between"
                >
                  <div>
                    <span className="inline-flex items-center gap-1 text-[11px] font-bold text-accent uppercase tracking-wider mb-2">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      Chính sử chuẩn xác
                    </span>
                    <h3 className="font-serif font-bold text-lg text-foreground mb-1">
                      {src.title}
                    </h3>
                    <p className="text-xs font-medium text-primary mb-2.5">
                      {src.author} · {src.edition}
                    </p>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {src.role}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 7. AI HISTORY TUTOR (Cô Giáo AI Có Dẫn Nguồn)                             */}
      {/* ========================================================================= */}
      <section className="relative py-20 md:py-28 overflow-hidden bg-secondary/30 border-y border-border/60">
        <div className="container mx-auto px-4 sm:px-6 relative z-10">
          <div className="heritage-hero rounded-3xl border border-primary/30 p-8 sm:p-12 md:p-14">
            <div className="grid lg:grid-cols-[1.1fr_0.9fr] gap-10 items-center">
              <div>
                <div className="inline-flex items-center gap-2 rounded-full border border-primary/40 bg-primary/10 px-4 py-1.5 text-xs font-semibold text-primary mb-4">
                  <Bot className="w-4 h-4" />
                  <span>Trợ giảng AI RAG chuẩn sử liệu</span>
                </div>

                <h2 className="font-serif text-3xl sm:text-5xl font-bold mb-4 leading-tight">
                  Hỏi Đáp Lịch Sử Cùng <br />
                  <span className="text-gradient-gold glow-gold">Cô Giáo AI Có Trích Dẫn</span>
                </h2>

                <p className="text-base sm:text-lg text-muted-foreground leading-relaxed mb-8">
                  Hệ thống AI được huấn luyện trên kho tư liệu chính sử đã được số hóa. Mọi câu trả lời đều đính kèm trích dẫn nguồn, chương mục, đảm bảo tính chuẩn xác và không tạo thông tin sai lệch.
                </p>

                <div className="flex flex-wrap gap-4">
                  <Link
                    href="/ai"
                    className="inline-flex min-h-11 items-center gap-2.5 rounded-xl bg-primary px-6 py-3 text-sm font-bold text-primary-foreground shadow-lg shadow-primary/20 transition hover:bg-primary/90"
                  >
                    <Sparkles className="w-4 h-4" />
                    Trò chuyện cùng Cô giáo AI
                    <ArrowRight className="w-4 h-4" />
                  </Link>

                  <Link
                    href="/practice"
                    className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-border bg-secondary/80 px-5 py-3 text-sm font-semibold text-foreground transition hover:bg-secondary"
                  >
                    Luyện tập trắc nghiệm
                  </Link>
                </div>
              </div>

              {/* Sample Prompts Cards */}
              <div className="flex flex-col gap-3 rounded-2xl border border-border/80 bg-card/80 p-6 backdrop-blur-md">
                <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">
                  Gợi ý câu hỏi có thể hỏi ngay:
                </span>
                {TUTOR_PROMPTS.map((prompt) => (
                  <Link
                    key={prompt}
                    href={`/ai?q=${encodeURIComponent(prompt)}`}
                    className="group flex items-center justify-between rounded-xl border border-border/70 bg-secondary/40 p-3.5 text-xs sm:text-sm text-foreground transition hover:border-primary/50 hover:bg-secondary hover:text-primary"
                  >
                    <span className="line-clamp-1">{prompt}</span>
                    <ArrowRight className="w-4 h-4 shrink-0 transition group-hover:translate-x-1" />
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 8. VISION & INSPIRING QUOTE (From luuniensuki.pages.dev inspiration)       */}
      {/* ========================================================================= */}
      <section className="relative py-24 md:py-32 overflow-hidden flex items-center justify-center">
        <div className="container mx-auto px-4 sm:px-6 relative z-10 text-center max-w-4xl">
          <div className="mb-6" aria-hidden="true">
            <svg className="w-12 h-12 sm:w-16 sm:h-16 mx-auto text-primary/30" fill="currentColor" viewBox="0 0 24 24">
              <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.433.917-3.996 3.638-3.996 5.849h3.983v10h-9.983z" />
            </svg>
          </div>

          <h2 className="font-serif text-3xl sm:text-4xl md:text-6xl font-bold mb-8 leading-tight">
            Chạm Vào Di Sản — <br />
            <span className="text-gradient-gold glow-gold">Đánh Thức Niềm Tự Hào Dân Tộc</span>
          </h2>

          <p className="text-base sm:text-lg md:text-xl text-muted-foreground leading-relaxed max-w-2xl mx-auto mb-10">
            Lưu Niên Sử Kí kiến tạo hành trình đưa bảo vật quốc gia vượt khỏi không gian vật lý, trao truyền tri thức lịch sử và lòng yêu nước đến thế hệ mai sau bằng sức mạnh của công nghệ hiện đại.
          </p>

          <div className="flex items-center justify-center gap-3" aria-hidden="true">
            <div className="h-px w-20 bg-gradient-to-r from-transparent to-primary/50" />
            <div className="w-2.5 h-2.5 rounded-full bg-primary animate-glow-pulse" />
            <div className="h-px w-20 bg-gradient-to-l from-transparent to-primary/50" />
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 9. FREE PARTICIPATION CALL TO ACTION                                      */}
      {/* ========================================================================= */}
      <section className="relative py-16 md:py-24 overflow-hidden">
        <div className="container mx-auto px-4 sm:px-6 relative z-10">
          <div className="heritage-surface rounded-3xl border border-border/80 p-8 sm:p-14 text-center max-w-4xl mx-auto shadow-2xl">
            <span className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 border border-primary/30 text-primary mb-6">
              <GraduationCap className="h-8 w-8" aria-hidden="true" />
            </span>

            <h2 className="font-serif text-3xl sm:text-5xl font-bold text-foreground mb-4">
              Bắt Đầu Hành Trình Học Tập Di Sản Miễn Phí
            </h2>

            <p className="text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto mb-8 leading-relaxed">
              Mở cửa tra cứu và học tập hoàn toàn miễn phí cho tất cả mọi người. Tạo tài khoản để lưu lại hành trình học tập, mở khóa huy hiệu và lưu trữ bộ sưu tập của riêng bạn.
            </p>

            <div className="flex flex-wrap justify-center gap-4 mb-8">
              <Link
                href="/practice"
                className="inline-flex min-h-12 items-center justify-center gap-2.5 rounded-xl bg-gradient-to-r from-primary via-amber-500 to-primary px-8 py-3.5 text-base font-bold text-primary-foreground shadow-lg shadow-primary/25 transition hover:scale-105"
              >
                <Compass className="w-5 h-5" />
                Bắt đầu học ngay
                <ArrowRight className="w-5 h-5" />
              </Link>

              <Link
                href={isAuthed ? "/dashboard" : "/login"}
                className="inline-flex min-h-12 items-center justify-center gap-2.5 rounded-xl border border-border bg-secondary/80 px-7 py-3.5 text-base font-semibold text-foreground transition hover:bg-secondary"
              >
                <UserRound className="w-5 h-5 text-primary" />
                {isAuthed ? "Vào bảng học tập của tôi" : "Đăng ký / Đăng nhập tài khoản"}
              </Link>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-6 text-xs text-muted-foreground">
              <span className="inline-flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-accent" />
                Không bắt buộc đăng nhập để tra cứu
              </span>
              <span className="inline-flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-accent" />
                100% Khảo chứng sử liệu có nguồn gốc
              </span>
              <span className="inline-flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-accent" />
                Tương thích mọi thiết bị di động & máy tính
              </span>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
