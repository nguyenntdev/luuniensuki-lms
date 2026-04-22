import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const ACCESS_COOKIE_NAME =
    process.env.ACCESS_COOKIE_NAME || "luuniensuki_access";
const REFRESH_COOKIE_NAME =
    process.env.REFRESH_COOKIE_NAME || "luuniensuki_refresh";

const PUBLIC_PATH_PREFIXES = ["/login", "/register"];
const PUBLIC_FILE_PATHS = [
    "/favicon.ico",
    "/robots.txt",
    "/sitemap.xml",
    "/manifest.json",
];

export function middleware(request: NextRequest) {
    const { pathname, search } = request.nextUrl;

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
        const pagePath = `/${parts.join("/")}`.replace(/\\.json$/, "") || "/";
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

    if (accessCookie || refreshCookie) {
        return NextResponse.next();
    }

    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = "/login";
    loginUrl.searchParams.set("returnUrl", `${pathname}${search}`);
    return NextResponse.redirect(loginUrl);
}

export const config = {
    matcher: ["/((?!_next/static|_next/image).*)"],
};
