// Shared public (no-login) path prefixes for the History-First rebuild.
// Spec HP-04 / IA-002: core historical reading and exploration MUST be
// accessible without authentication. Kept in one module so the middleware
// (Edge), AuthGate and StartingPathGate stay in sync.
export const PUBLIC_PATH_PREFIXES: string[] = [
  "/",
  "/login",
  "/register",
  // History-first public surface
  "/cuu-dinh",
  "/atlas",
  "/map",
  "/timeline",
  "/stories",
  "/sources",
  "/practice",
  "/compare",
  "/explore",
];

export const PUBLIC_FILE_PATHS: string[] = [
  "/favicon.ico",
  "/robots.txt",
  "/sitemap.xml",
  "/manifest.json",
  "/manifest.webmanifest",
  "/favicon.svg",
];

export function isPublicPath(pathname: string | null | undefined): boolean {
  if (!pathname) return false;
  if (pathname === "/") return true;
  return PUBLIC_PATH_PREFIXES.some(
    (prefix) => prefix !== "/" && (pathname === prefix || pathname.startsWith(`${prefix}/`)),
  );
}
