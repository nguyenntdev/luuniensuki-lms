// Shell visibility — single source of truth for routes where the global
// header / mobile bottom navigation are hidden (mirrors the routes the legacy
// FloatingNavbar suppressed).
export function isShellRoute(
  pathname: string | null | undefined,
): boolean {
  const p = pathname ?? "";
  if (p === "/login" || p === "/register") return false;
  if (/^\/motif\/[^/]+\/quiz/.test(p)) return false;
  if (/^\/urns\/[^/]+$/.test(p)) return false;
  if (/^\/urns\/[^/]+\/exam(\/.*)?$/.test(p)) return false;
  if (/^\/live\/[^/]+$/.test(p)) return false;
  return true;
}