export function getLoginUrl(returnPath?: string | null): string {
  const normalizedReturnPath =
    typeof returnPath === "string" && returnPath.length > 0 ? returnPath : "/";
  return `/login?returnUrl=${encodeURIComponent(normalizedReturnPath)}`;
}
