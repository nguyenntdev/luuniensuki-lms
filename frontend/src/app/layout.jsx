import { Toaster } from "react-hot-toast";
import FloatingNavbar from "@/components/FloatingNavbar";
import ClientBodyWrapper from "@/components/ClientBodyWrapper";
import AuthGate from "@/components/AuthGate";
import StartingPathGate from "@/components/StartingPathGate";
import "./globals.css";

export const metadata = {
    title: "Lưu Niên Sử Kí",
    description: "Gamified Heritage Exploration Platform",
};

export default function RootLayout({ children }) {
    return (
        <html lang="vi">
            <body className="min-h-dvh bg-background text-foreground">
                <ClientBodyWrapper>
                    <AuthGate>
                        <FloatingNavbar />
                        <StartingPathGate />
                        <Toaster position="top-center" reverseOrder={false} />
                        {children}
                    </AuthGate>
                </ClientBodyWrapper>
            </body>
        </html>
    );
}
