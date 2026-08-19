"use client";

import { useEffect, useState } from "react";
import { MoonIcon, SunIcon } from "lucide-react";

import { cn } from "@/lib/utils";

type Theme = "dark" | "light";

export default function ThemeToggle({ className }: { className?: string }) {
  const [theme, setTheme] = useState<Theme>("dark");

  useEffect(() => {
    setTheme(window.__getLuuniensukiTheme?.() || "dark");
  }, []);

  function toggle() {
    const next: Theme = theme === "dark" ? "light" : "dark";
    setTheme(next);
    window.__setLuuniensukiTheme?.(next);
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={theme === "dark" ? "Bật giao diện sáng" : "Bật giao diện tối"}
      className={cn(
        "inline-flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
        className,
      )}
    >
      {theme === "dark" ? (
        <SunIcon className="h-4 w-4" aria-hidden="true" />
      ) : (
        <MoonIcon className="h-4 w-4" aria-hidden="true" />
      )}
    </button>
  );
}