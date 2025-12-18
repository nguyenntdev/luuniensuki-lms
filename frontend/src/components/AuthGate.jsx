"use client";

import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import { useAuthStore } from "@/stores/authStore";

const PUBLIC_PATH_PREFIXES = ["/login", "/register"];

function isPublicPath(pathname) {
  if (!pathname) return false;
  return PUBLIC_PATH_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
}

function AuthGateInner({ children }) {
  const router = useRouter();
  const pathname = usePathname();

  const accessToken = useAuthStore((s) => s.accessToken);

  const isPublic = useMemo(() => isPublicPath(pathname), [pathname]);
  const hasToken = Boolean(accessToken);

  const [hasHydrated, setHasHydrated] = useState(() => useAuthStore.persist?.hasHydrated?.() ?? true);

  useEffect(() => {
    if (!useAuthStore.persist?.onFinishHydration) return;

    setHasHydrated(useAuthStore.persist.hasHydrated());
    return useAuthStore.persist.onFinishHydration(() => setHasHydrated(true));
  }, []);

  const lastRedirectTargetRef = useRef(null);

  useEffect(() => {
    if (isPublic || !hasHydrated || hasToken) {
      lastRedirectTargetRef.current = null;
      return;
    }

    const safePath = pathname || "/";
    const search = typeof window === "undefined" ? "" : window.location.search || "";
    const returnUrl = `${safePath}${search}`;
    const target = `/login?returnUrl=${encodeURIComponent(returnUrl)}`;

    if (lastRedirectTargetRef.current === target) return;
    lastRedirectTargetRef.current = target;
    router.replace(target);
  }, [hasHydrated, hasToken, isPublic, pathname, router]);

  if (isPublic) return children;
  if (!hasHydrated) return null;
  if (!hasToken) return null;

  return children;
}

export default function AuthGate({ children }) {
  return (
    <Suspense fallback={null}>
      <AuthGateInner>{children}</AuthGateInner>
    </Suspense>
  );
}
