"use client";

import { useEffect, useState } from "react";

const STORAGE_KEY = "luuniensuki-theme";

function getInitialTheme() {
  if (typeof window === "undefined") return "dark";
  const saved = window.localStorage.getItem(STORAGE_KEY);
  if (saved === "light" || saved === "dark") return saved;
  return window.matchMedia?.("(prefers-color-scheme: light)")?.matches
    ? "light"
    : "dark";
}

function applyTheme(theme) {
  const root = document.documentElement;
  root.classList.toggle("dark", theme === "dark");
  root.dataset.theme = theme;
}

export default function ThemeProvider({ children }) {
  const [theme, setTheme] = useState("dark");

  useEffect(() => {
    const initialTheme = getInitialTheme();
    setTheme(initialTheme);
    applyTheme(initialTheme);
  }, []);

  useEffect(() => {
    window.__setLuuniensukiTheme = (nextTheme) => {
      const resolved = nextTheme === "light" ? "light" : "dark";
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
