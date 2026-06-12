"use client";

import { Suspense, useEffect, useMemo, useRef } from "react";
import type { ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";

import { useAuthStore } from "@/stores/authStore";

const PUBLIC_PATH_PREFIXES: string[] = ["/login", "/register"];

function isPublicPath(pathname: string | null): boolean {
    if (!pathname) return false;
    return PUBLIC_PATH_PREFIXES.some(
        (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
    );
}

interface AuthGateProps {
    children: ReactNode;
}

function AuthGateInner({ children }: AuthGateProps) {
    const router = useRouter();
    const pathname = usePathname();

    const status = useAuthStore((s) => s.status);
    const bootstrap = useAuthStore((s) => s.bootstrap);

    const isPublic = useMemo(() => isPublicPath(pathname), [pathname]);
    const isChecking = status === "checking";
    const isAuthed = status === "authed";

    const lastRedirectTargetRef = useRef<string | null>(null);
    const bootstrappedRef = useRef(false);

    useEffect(() => {
        if (bootstrappedRef.current) return;
        bootstrappedRef.current = true;
        bootstrap();
    }, [bootstrap]);

    useEffect(() => {
        if (isPublic || isChecking || isAuthed) {
            lastRedirectTargetRef.current = null;
            return;
        }

        const safePath = pathname || "/";
        const search =
            typeof window === "undefined" ? "" : window.location.search || "";
        const returnUrl = `${safePath}${search}`;
        const target = `/login?returnUrl=${encodeURIComponent(returnUrl)}`;

        if (lastRedirectTargetRef.current === target) return;
        lastRedirectTargetRef.current = target;
        router.replace(target);
    }, [isAuthed, isChecking, isPublic, pathname, router]);

    if (isPublic) return children;
    if (isChecking) return null;
    if (!isAuthed) return null;

    return children;
}

export default function AuthGate({ children }: AuthGateProps) {
    return (
        <Suspense fallback={null}>
            <AuthGateInner>{children}</AuthGateInner>
        </Suspense>
    );
}
