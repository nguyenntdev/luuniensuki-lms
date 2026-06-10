import { Toaster } from "react-hot-toast";
import FloatingNavbar from "@/components/FloatingNavbar";
import CommandPalette from "@/components/CommandPalette";
import ClientBodyWrapper from "@/components/ClientBodyWrapper";
import AuthGate from "@/components/AuthGate";
import StartingPathGate from "@/components/StartingPathGate";
import NetworkStatusIndicator from "@/components/NetworkStatusIndicator";
import ThemeProvider from "@/components/ThemeProvider";
import { XpCelebrationProvider } from "@/lib/xpCelebrationContext";
import BadgeUnlockProvider from "@/components/badges/BadgeUnlockProvider";
import "./globals.css";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://lms.histolab.icu";
const SITE_NAME = "Lưu Niên Sử Kí";
const SITE_DESCRIPTION =
    "Nền tảng học di sản Cửu Đỉnh triều Nguyễn qua mô hình 3D, lớp học cùng Cô giáo AI, trắc nghiệm và tham quan ảo 360°.";

export const metadata = {
    metadataBase: new URL(SITE_URL),
    title: {
        default: `${SITE_NAME} — Học di sản Cửu Đỉnh`,
        template: `%s — ${SITE_NAME}`,
    },
    description: SITE_DESCRIPTION,
    applicationName: SITE_NAME,
    keywords: [
        "Cửu Đỉnh",
        "triều Nguyễn",
        "di sản Huế",
        "học di sản",
        "3D",
        "Lưu Niên Sử Kí",
    ],
    manifest: "/manifest.webmanifest",
    icons: {
        icon: [{ url: "/favicon.svg", type: "image/svg+xml" }],
        shortcut: ["/favicon.ico"],
        apple: [{ url: "/favicon.svg" }],
    },
    openGraph: {
        type: "website",
        locale: "vi_VN",
        url: SITE_URL,
        siteName: SITE_NAME,
        title: `${SITE_NAME} — Học di sản Cửu Đỉnh`,
        description: SITE_DESCRIPTION,
    },
    twitter: {
        card: "summary",
        title: `${SITE_NAME} — Học di sản Cửu Đỉnh`,
        description: SITE_DESCRIPTION,
    },
    robots: { index: true, follow: true },
};

export const viewport = {
    themeColor: "#0b0f17",
    colorScheme: "dark",
};

export default function RootLayout({ children }) {
    return (
        <html lang="vi" className="dark" suppressHydrationWarning>
            <body className="min-h-dvh bg-background text-foreground">
                <a href="#main-content" className="skip-link">
                    Bỏ qua điều hướng
                </a>
                <ThemeProvider>
                    <NetworkStatusIndicator>
                        <ClientBodyWrapper>
                            <AuthGate>
                                <XpCelebrationProvider>
                                    <BadgeUnlockProvider>
                                        <FloatingNavbar />
                                        <CommandPalette />
                                        <StartingPathGate />
                                        <Toaster position="top-center" reverseOrder={false} />
                                        <div id="main-content">{children}</div>
                                    </BadgeUnlockProvider>
                                </XpCelebrationProvider>
                            </AuthGate>
                        </ClientBodyWrapper>
                    </NetworkStatusIndicator>
                </ThemeProvider>
            </body>
        </html>
    );
}
