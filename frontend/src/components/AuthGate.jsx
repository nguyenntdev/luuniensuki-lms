"use client";

import { Suspense, useEffect, useMemo, useRef } from "react";
import { usePathname, useRouter } from "next/navigation";

import { useAuthStore } from "@/stores/authStore";

const PUBLIC_PATH_PREFIXES = ["/login", "/register"];

function isPublicPath(pathname) {
    if (!pathname) return false;
    return PUBLIC_PATH_PREFIXES.some(
        (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
    );
}

function AuthGateInner({ children }) {
    const router = useRouter();
    const pathname = usePathname();

    const status = useAuthStore((s) => s.status);
    const bootstrap = useAuthStore((s) => s.bootstrap);

    const isPublic = useMemo(() => isPublicPath(pathname), [pathname]);
    const isChecking = status === "checking";
    const isAuthed = status === "authed";

    const lastRedirectTargetRef = useRef(null);
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

export default function AuthGate({ children }) {
    return (
        <Suspense fallback={null}>
            <AuthGateInner>{children}</AuthGateInner>
        </Suspense>
    );
}
