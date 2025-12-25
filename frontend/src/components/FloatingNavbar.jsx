"use client";

import { useState, useEffect, useRef } from "react";
import {
    Menu,
    X,
    Globe,
    ChevronUp,
    Eye,
    Trophy,
    BookOpen,
    User,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuthStore } from "../stores/authStore";
// --- Local Utilities & Components ---

function cn(...classes) {
    return classes.filter(Boolean).join(" ");
}

const Button = ({ className, size, children, ...props }) => {
    const baseStyles =
        "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50";
    const variants = {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        sm: "h-9 rounded-md px-3",
    };

    // Minimal implementation matching the reference usage
    return (
        <button
            className={cn(
                baseStyles,
                variants.default,
                size === "sm" && variants.sm,
                className,
            )}
            {...props}
        >
            {children}
        </button>
    );
};

// --- I18n Setup ---

const languages = [
    { code: "vi", nativeName: "Tiếng Việt" },
    { code: "en", nativeName: "English" },
];

const translations = {
    vi: {
        "nav.dashboard": "Learning Hub",
        "nav.explore": "Khám Phá",
        "nav.collection": "Bộ Sưu Tập",
        "nav.achievements": "Thành Tích",
        "nav.profile": "Hồ Sơ",
        "nav.logout": "Đăng xuất",
        "nav.start": "Tiếp Tục Học",
    },
    en: {
        "nav.dashboard": "Learning Hub",
        "nav.explore": "Explore",
        "nav.collection": "Collection",
        "nav.achievements": "Achievements",
        "nav.profile": "Profile",
        "nav.logout": "Logout",
        "nav.start": "Continue Learning",
    },
};

export default function FloatingNavbar() {
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const [isLangDropdownOpen, setIsLangDropdownOpen] = useState(false);
    const [isUserDropdownOpen, setIsUserDropdownOpen] = useState(false);
    const [lang, setLang] = useState("vi");
    const pathname = usePathname();
    const isHomePage = pathname === "/";
    const isAuthPage = pathname === "/login" || pathname === "/register";
    const langDropdownRef = useRef(null);
    const userDropdownRef = useRef(null);

    const status = useAuthStore((s) => s.status);
    const user = useAuthStore((s) => s.user);
    const fetchMe = useAuthStore((s) => s.fetchMe);
    const logout = useAuthStore((s) => s.logout);

    const userDisplayName = user?.display_name || user?.email || "User";
    const userInitial = (userDisplayName || "U").trim().charAt(0).toUpperCase();

    const t = (key) => translations[lang][key] || key;

    useEffect(() => {
        if (isMobileMenuOpen) {
            document.body.style.overflow = "hidden";
        } else {
            document.body.style.overflow = "unset";
        }
        return () => {
            document.body.style.overflow = "unset";
        };
    }, [isMobileMenuOpen]);

    useEffect(() => {
        if (status === "authed" && !user) fetchMe();
    }, [status, user, fetchMe]);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (
                langDropdownRef.current &&
                !langDropdownRef.current.contains(event.target)
            ) {
                setIsLangDropdownOpen(false);
            }
            if (
                userDropdownRef.current &&
                !userDropdownRef.current.contains(event.target)
            ) {
                setIsUserDropdownOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () =>
            document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    useEffect(() => {
        setIsMobileMenuOpen(false);
        setIsLangDropdownOpen(false);
        setIsUserDropdownOpen(false);
    }, [pathname]);

    const scrollToSection = (id) => {
        const element = document.getElementById(id);
        element?.scrollIntoView({ behavior: "smooth", block: "start" });
        setIsMobileMenuOpen(false);
    };

    const primaryNavItems = [
        { icon: Globe, label: t("nav.dashboard"), link: "/dashboard" },
        { icon: Eye, label: t("nav.explore"), link: "/explore" },
        { icon: BookOpen, label: t("nav.collection"), link: "/collection" },
        { icon: Trophy, label: t("nav.achievements"), link: "/achievements" },
        { icon: User, label: t("nav.profile"), link: "/profile" },
    ];

    if (isAuthPage) return null;

    return (
        <>
            {/* Desktop floating nav */}
            <nav className="hidden md:flex fixed bottom-4 left-1/2 -translate-x-1/2 z-50 max-w-[95vw]">
                <div className="flex items-center gap-2 bg-background/90 backdrop-blur-xl border border-border/60 rounded-full px-3 py-2 shadow-[0_12px_35px_rgba(0,0,0,0.35)]">
                    <Link
                        href="/"
                        className="flex items-center gap-2 pr-2 border-r border-border/50 shrink-0"
                    >
                        <div className="leading-tight">
                            <p className="text-sm font-semibold text-foreground/90 font-serif tracking-tight whitespace-nowrap">
                                Lưu Niên Sử Kí
                            </p>
                        </div>
                    </Link>

                    <div className="flex items-center gap-0.5 overflow-x-auto scrollbar-hide">
                        {primaryNavItems.map((item) => {
                            const Icon = item.icon;
                            const content = (
                                <>
                                    {Icon && <Icon className="w-4 h-4" />}
                                    <span className="text-xs font-medium whitespace-nowrap">
                                        {item.label}
                                    </span>
                                </>
                            );

                            const baseClasses =
                                "inline-flex items-center gap-1.5 px-2 py-1.5 rounded-full text-primary hover:text-foreground hover:bg-primary/25 transition-all duration-200 shrink-0";

                            if (item.link && (!item.id || !isHomePage)) {
                                return (
                                    <Link
                                        key={item.label}
                                        href={item.link}
                                        className="shrink-0"
                                    >
                                        <button
                                            className={baseClasses}
                                            type="button"
                                        >
                                            {content}
                                        </button>
                                    </Link>
                                );
                            }

                            return (
                                <button
                                    key={item.label}
                                    onClick={() =>
                                        item.id && scrollToSection(item.id)
                                    }
                                    disabled={!isHomePage}
                                    className={`${baseClasses} ${!isHomePage && !item.link ? "opacity-60 cursor-not-allowed" : ""}`}
                                    type="button"
                                >
                                    {content}
                                </button>
                            );
                        })}
                    </div>

                    <div className="flex items-center gap-1.5 pl-2 border-l border-border/50 shrink-0">
                        {status === "authed" && (
                            <div className="relative" ref={userDropdownRef}>
                                <button
                                    onClick={() => {
                                        setIsUserDropdownOpen((prev) => !prev);
                                        setIsLangDropdownOpen(false);
                                    }}
                                    className="inline-flex items-center gap-1 px-2 py-1.5 rounded-full text-primary hover:bg-primary/10 transition-colors"
                                    type="button"
                                    aria-haspopup="menu"
                                    aria-expanded={isUserDropdownOpen}
                                >
                                    <span className="w-6 h-6 rounded-full overflow-hidden bg-primary/10 flex items-center justify-center shrink-0 border border-border/60">
                                        {user?.avatar_url ? (
                                            <img
                                                src={user.avatar_url}
                                                alt={userDisplayName}
                                                className="w-full h-full object-cover"
                                            />
                                        ) : (
                                            <span className="text-[11px] font-bold text-primary">
                                                {userInitial}
                                            </span>
                                        )}
                                    </span>
                                    <span className="text-xs font-semibold max-w-[120px] truncate">
                                        {userDisplayName}
                                    </span>
                                    <ChevronUp
                                        className={`w-3 h-3 transition-transform ${isUserDropdownOpen ? "rotate-180" : "rotate-0"}`}
                                    />
                                </button>
                                {isUserDropdownOpen && (
                                    <div className="absolute bottom-full right-0 mb-2 bg-background/95 backdrop-blur-lg border border-border rounded-xl shadow-lg py-1 min-w-[180px]">
                                        <div className="px-3 py-2">
                                            <p className="text-sm font-semibold text-foreground truncate">
                                                {userDisplayName}
                                            </p>
                                            {user?.email ? (
                                                <p className="text-xs text-muted-foreground truncate">
                                                    {user.email}
                                                </p>
                                            ) : null}
                                        </div>
                                        <div className="border-t border-border/60 my-1" />
                                        <button
                                            onClick={() => {
                                                logout();
                                                setIsUserDropdownOpen(false);
                                            }}
                                            className="w-full px-3 py-2 text-left text-sm hover:bg-primary/10 transition-colors text-foreground/80"
                                            type="button"
                                        >
                                            {t("nav.logout")}
                                        </button>
                                    </div>
                                )}
                            </div>
                        )}
                        <div className="relative" ref={langDropdownRef}>
                            <button
                                onClick={() =>
                                    setIsLangDropdownOpen((prev) => !prev)
                                }
                                className="inline-flex items-center gap-1 px-2 py-1.5 rounded-full text-primary hover:bg-primary/10 transition-colors"
                                type="button"
                                aria-haspopup="listbox"
                                aria-expanded={isLangDropdownOpen}
                            >
                                <Globe className="w-4 h-4" />
                                <span className="text-xs font-semibold uppercase">
                                    {lang}
                                </span>
                                <ChevronUp
                                    className={`w-3 h-3 transition-transform ${isLangDropdownOpen ? "rotate-180" : "rotate-0"}`}
                                />
                            </button>
                            {isLangDropdownOpen && (
                                <div className="absolute bottom-full right-0 mb-2 bg-background/95 backdrop-blur-lg border border-border rounded-xl shadow-lg py-1 min-w-[140px]">
                                    {languages.map((l) => (
                                        <button
                                            key={l.code}
                                            onClick={() => {
                                                setLang(l.code);
                                                setIsLangDropdownOpen(false);
                                            }}
                                            className={`w-full px-3 py-2 text-left text-sm hover:bg-primary/10 transition-colors flex items-center justify-between ${
                                                lang === l.code
                                                    ? "text-primary font-medium"
                                                    : "text-foreground/80"
                                            }`}
                                            type="button"
                                        >
                                            <span>{l.nativeName}</span>
                                            {lang === l.code && (
                                                <span className="text-primary">
                                                    *
                                                </span>
                                            )}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                        <Link href="/dashboard" className="shrink-0">
                            <Button
                                size="sm"
                                className="rounded-full bg-primary hover:bg-primary/90 hover:shadow-lg hover:shadow-primary/20 whitespace-nowrap text-xs px-3 py-1"
                            >
                                {t("nav.start")}
                            </Button>
                        </Link>
                    </div>
                </div>
            </nav>

            {/* Mobile compact nav */}
            <nav className="md:hidden fixed bottom-3 left-1/2 -translate-x-1/2 z-30 w-full max-w-md px-3">
                <div className="flex items-center gap-1 bg-background/95 backdrop-blur-lg border border-border rounded-full shadow-[0_10px_30px_rgba(0,0,0,0.35)] px-2 py-1.5">
                    {primaryNavItems.map((item) => {
                        const Icon = item.icon;
                        const content = (
                            <>
                                {Icon && <Icon className="w-5 h-5" />}
                                <span className="text-[11px] font-medium truncate">
                                    {item.label}
                                </span>
                            </>
                        );

                        if (item.link && (!item.id || !isHomePage)) {
                            return (
                                <Link
                                    key={item.label}
                                    href={item.link}
                                    className="flex-1 min-w-0"
                                    onClick={() => setIsMobileMenuOpen(false)}
                                >
                                    <button
                                        className="w-full flex flex-col items-center gap-1 px-2 py-1.5 text-primary/80 hover:text-primary transition-colors"
                                        type="button"
                                    >
                                        {content}
                                    </button>
                                </Link>
                            );
                        }

                        return (
                            <button
                                key={item.label}
                                onClick={() =>
                                    item.id && scrollToSection(item.id)
                                }
                                disabled={!isHomePage}
                                className="flex-1 min-w-0 flex flex-col items-center gap-1 px-2 py-1.5 text-primary/80 hover:text-primary transition-colors disabled:opacity-60"
                                type="button"
                            >
                                {content}
                            </button>
                        );
                    })}
                    <button
                        onClick={() => setIsMobileMenuOpen((prev) => !prev)}
                        className="flex flex-col items-center gap-1 px-2 py-1.5 text-primary/80 hover:text-primary transition-colors"
                        aria-label="More options"
                        type="button"
                    >
                        {isMobileMenuOpen ? (
                            <X className="w-5 h-5" />
                        ) : (
                            <Menu className="w-5 h-5" />
                        )}
                        <span className="text-[11px] font-medium">Menu</span>
                    </button>
                </div>
            </nav>

            {/* Mobile menu overlay */}
            {isMobileMenuOpen && (
                <div
                    className="fixed inset-0 bg-background/75 backdrop-blur-sm md:hidden z-40"
                    onClick={() => setIsMobileMenuOpen(false)}
                    aria-hidden="true"
                />
            )}

            {/* Mobile slide-up */}
            <div
                className={`md:hidden fixed bottom-0 left-0 right-0 z-50 transition-all duration-300 ${
                    isMobileMenuOpen
                        ? "translate-y-0 opacity-100"
                        : "translate-y-full opacity-0 pointer-events-none"
                }`}
                role="navigation"
                aria-label="Mobile navigation"
            >
                <div className="bg-background/95 backdrop-blur-xl border-t border-border rounded-t-3xl shadow-2xl p-5 space-y-5 max-h-[65vh] overflow-y-auto">
                    {status === "authed" && (
                        <div className="flex items-center justify-between gap-3 rounded-2xl border border-border/60 bg-background/60 px-4 py-3">
                            <div className="flex items-center gap-3 min-w-0">
                                <div className="w-10 h-10 rounded-full overflow-hidden bg-primary/10 flex items-center justify-center shrink-0 border border-border/60">
                                    {user?.avatar_url ? (
                                        <img
                                            src={user.avatar_url}
                                            alt={userDisplayName}
                                            className="w-full h-full object-cover"
                                        />
                                    ) : (
                                        <span className="text-sm font-bold text-primary">
                                            {userInitial}
                                        </span>
                                    )}
                                </div>
                                <div className="min-w-0">
                                    <p className="text-sm font-semibold text-foreground truncate">
                                        {userDisplayName}
                                    </p>
                                    {user?.email ? (
                                        <p className="text-xs text-muted-foreground truncate">
                                            {user.email}
                                        </p>
                                    ) : null}
                                </div>
                            </div>
                            <button
                                onClick={() => {
                                    logout();
                                    setIsMobileMenuOpen(false);
                                }}
                                className="text-xs font-semibold rounded-xl px-3 py-2 bg-muted/50 hover:bg-primary/10 transition-colors text-foreground/80"
                                type="button"
                            >
                                {t("nav.logout")}
                            </button>
                        </div>
                    )}
                    <div>
                        <p className="text-xs text-muted-foreground mb-3">
                            Language
                        </p>
                        <div className="grid grid-cols-4 gap-2">
                            {languages.map((l) => (
                                <button
                                    key={l.code}
                                    onClick={() => setLang(l.code)}
                                    className={`py-2.5 text-xs font-semibold rounded-xl transition-colors ${
                                        lang === l.code
                                            ? "bg-primary text-primary-foreground"
                                            : "bg-muted/50 text-foreground/70 hover:bg-primary/10"
                                    }`}
                                    type="button"
                                >
                                    {l.code.toUpperCase()}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Link
                            href="/dashboard"
                            className="block"
                            onClick={() => setIsMobileMenuOpen(false)}
                        >
                            <Button className="w-full bg-primary hover:bg-primary/90">
                                {t("nav.start")}
                            </Button>
                        </Link>
                    </div>
                </div>
            </div>
        </>
    );
}
