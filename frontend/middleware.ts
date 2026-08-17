import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { jwtVerify } from "jose";
import { PUBLIC_PATH_PREFIXES, PUBLIC_FILE_PATHS } from "@/lib/publicPaths";

const ACCESS_COOKIE_NAME =
    process.env.ACCESS_COOKIE_NAME || "luuniensuki_access";
const REFRESH_COOKIE_NAME =
    process.env.REFRESH_COOKIE_NAME || "luuniensuki_refresh";

// Shared signing secret. This MUST be exposed to the middleware (Edge) env as
// `JWT_SECRET_KEY` for token-validity verification. It is the same secret the
// backend uses to sign access tokens. When it is not configured, the guard
// falls back to the legacy cookie-presence check (see below).
const JWT_SECRET = process.env.JWT_SECRET_KEY;

// Lazily-built, cached signing key. Built once per worker.
let cachedKey: Uint8Array | null = null;
function getSigningKey(secret: string): Uint8Array {
    if (cachedKey === null) {
        cachedKey = new TextEncoder().encode(secret);
    }
    return cachedKey;
}

// Warn at most once if the secret is not available to the Edge runtime so the
// app degrades to presence-checking instead of hard-breaking.
let warnedMissingSecret = false;
function warnMissingSecretOnce(): void {
    if (!warnedMissingSecret) {
        warnedMissingSecret = true;
        console.warn(
            "[middleware] JWT_SECRET_KEY is not configured for the Edge runtime; " +
                "falling back to cookie-presence route guard. Set JWT_SECRET_KEY " +
                "to enable token-validity verification.",
        );
    }
}

// Verify the access token's signature and expiry (jwtVerify enforces `exp`
// automatically) and confirm it is an access token. Returns true only when the
// token is structurally valid, correctly signed, unexpired, and of type
// "access".
async function isAccessTokenValid(
    token: string,
    secret: string,
): Promise<boolean> {
    try {
        const { payload } = await jwtVerify(token, getSigningKey(secret));
        return payload.type === "access";
    } catch {
        return false;
    }
}

// Strip a trailing ".json" suffix from a Next.js `/_next/data` page path.
// The anchored `$` ensures only a real trailing suffix is removed
// (e.g. "/cao-dinh.json" -> "/cao-dinh"), never an interior ".json" occurrence
// (e.g. "/a.json.b" is left untouched). Exported as a pure helper so the fixed
// regex (`/\.json$/`, not the broken `/\\.json$/`) is unit-testable.
export function stripJsonSuffix(pagePath: string): string {
    return pagePath.replace(/\.json$/, "");
}

function redirectToLogin(request: NextRequest): NextResponse {
    const { pathname, search } = request.nextUrl;
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = "/login";
    loginUrl.searchParams.set("returnUrl", `${pathname}${search}`);
    return NextResponse.redirect(loginUrl);
}

export async function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl;

    if (
        pathname.startsWith("/_next/static") ||
        pathname.startsWith("/_next/image") ||
        pathname.startsWith("/assets") ||
        pathname.startsWith("/fonts") ||
        pathname.startsWith("/images") ||
        pathname.startsWith("/icons") ||
        PUBLIC_FILE_PATHS.includes(pathname)
    ) {
        return NextResponse.next();
    }

    if (pathname.startsWith("/_next/data")) {
        const parts = pathname.split("/").slice(4);
        const pagePath = stripJsonSuffix(`/${parts.join("/")}`) || "/";
        if (
            PUBLIC_PATH_PREFIXES.some(
                (prefix) =>
                    pagePath === prefix || pagePath.startsWith(`${prefix}/`),
            )
        ) {
            return NextResponse.next();
        }
    }

    if (
        PUBLIC_PATH_PREFIXES.some(
            (prefix) =>
                pathname === prefix || pathname.startsWith(`${prefix}/`),
        )
    ) {
        return NextResponse.next();
    }

    const accessCookie = request.cookies.get(ACCESS_COOKIE_NAME)?.value;
    const refreshCookie = request.cookies.get(REFRESH_COOKIE_NAME)?.value;

    // Fallback path: if the secret is not exposed to the Edge runtime, degrade
    // to the legacy presence check so the app does not hard-break.
    if (!JWT_SECRET) {
        warnMissingSecretOnce();
        if (accessCookie || refreshCookie) {
            return NextResponse.next();
        }
        return redirectToLogin(request);
    }

    // Token-validity guard (defense-in-depth; the API is the true enforcement
    // point). Allow when the access token is valid; otherwise allow through if
    // a refresh cookie exists so the client api layer can attempt a refresh.
    if (accessCookie && (await isAccessTokenValid(accessCookie, JWT_SECRET))) {
        return NextResponse.next();
    }

    if (refreshCookie) {
        return NextResponse.next();
    }

    return redirectToLogin(request);
}

export const config = {
    matcher: ["/((?!_next/static|_next/image).*)"],
};
