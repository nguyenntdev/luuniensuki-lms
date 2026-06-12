"use client";

import { useEffect, useState } from "react";
import type { ReactNode } from "react";

type Theme = "light" | "dark";

declare global {
  interface Window {
    __setLuuniensukiTheme?: (nextTheme: string) => void;
    __getLuuniensukiTheme?: () => Theme;
  }
}

const STORAGE_KEY = "luuniensuki-theme";

function getInitialTheme(): Theme {
  if (typeof window === "undefined") return "dark";
  const saved = window.localStorage.getItem(STORAGE_KEY);
  if (saved === "light" || saved === "dark") return saved;
  return window.matchMedia?.("(prefers-color-scheme: light)")?.matches
    ? "light"
    : "dark";
}

function applyTheme(theme: Theme): void {
  const root = document.documentElement;
  root.classList.toggle("dark", theme === "dark");
  root.dataset.theme = theme;
}

interface ThemeProviderProps {
  children: ReactNode;
}

export default function ThemeProvider({ children }: ThemeProviderProps) {
  const [theme, setTheme] = useState<Theme>("dark");

  useEffect(() => {
    const initialTheme = getInitialTheme();
    setTheme(initialTheme);
    applyTheme(initialTheme);
  }, []);

  useEffect(() => {
    window.__setLuuniensukiTheme = (nextTheme: string) => {
      const resolved: Theme = nextTheme === "light" ? "light" : "dark";
      window.localStorage.setItem(STORAGE_KEY, resolved);
      setTheme(resolved);
      applyTheme(resolved);
    };
    window.__getLuuniensukiTheme = () => theme;

    return () => {
      delete window.__setLuuniensukiTheme;
      delete window.__getLuuniensukiTheme;
    };
  }, [theme]);

  return children;
}
