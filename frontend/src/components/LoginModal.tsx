"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";
import { X } from "lucide-react";

import { useAuthStore } from "@/stores/authStore";
import type { AuthSessionResponse } from "@/types/api";

interface LoginModalProps {
  isOpen: boolean;
  onClose?: () => void;
  onSuccess?: (res: AuthSessionResponse | null) => void;
}

export default function LoginModal({ isOpen, onClose, onSuccess }: LoginModalProps) {
  const authLogin = useAuthStore((s) => s.login);
  const authRegister = useAuthStore((s) => s.register);
  const loading = useAuthStore((s) => s.loading);
  const error = useAuthStore((s) => s.error);

  const [mode, setMode] = useState<"login" | "register">("login");
  const isRegister = mode === "register";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");

  const emailInputRef = useRef<HTMLInputElement>(null);
  const displayNameInputRef = useRef<HTMLInputElement>(null);

  const submitLabel = useMemo(() => (isRegister ? "Tạo tài khoản" : "Đăng nhập"), [isRegister]);

  useEffect(() => {
    if (!isOpen) return;

    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = prevOverflow;
    };
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose?.();
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isOpen, onClose]);

  useEffect(() => {
    if (!isOpen) return;
    const node = isRegister ? displayNameInputRef.current : emailInputRef.current;
    node?.focus?.();
  }, [isOpen, isRegister]);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (loading) return;

    try {
      const res = isRegister
        ? await authRegister({ email, password, displayName })
        : await authLogin({ email, password });

      onSuccess?.(res);
    } catch {
      // Errors are surfaced via the auth store `error` state.
    }
  }

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100]">
      <div
        className="fixed inset-0 bg-background/80 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      <div className="fixed inset-0 overflow-y-auto">
        <div className="flex min-h-full items-center justify-center px-4 py-6">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="login-modal-title"
            aria-describedby="login-modal-description"
            className="relative w-full max-w-md overflow-hidden rounded-3xl border border-border bg-card/90 backdrop-blur-xl shadow-elegant"
          >
            <div className="absolute -top-16 -right-16 h-56 w-56 rounded-full bg-primary/10 blur-3xl pointer-events-none" />
            <div className="absolute -bottom-20 -left-20 h-64 w-64 rounded-full bg-bronze/10 blur-3xl pointer-events-none" />

            <div className="relative p-6 sm:p-8">
              <button
                type="button"
                onClick={onClose}
                className="absolute right-4 top-4 inline-flex h-9 w-9 items-center justify-center rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted/40 transition-colors focus-ring"
                aria-label="Đóng"
              >
                <X className="h-4 w-4" aria-hidden="true" />
              </button>

              <h2 id="login-modal-title" className="text-2xl font-display font-semibold">
                Lưu Niên Sử Kí
              </h2>
              <p id="login-modal-description" className="mt-1 text-sm text-muted-foreground text-vietnamese">
                Đăng nhập để lưu tiến trình và tiếp tục học.
              </p>

              <div role="tablist" aria-label="Chế độ xác thực" className="mt-6 flex rounded-lg bg-muted p-1">
                <button
                  type="button"
                  role="tab"
                  id="modal-tab-login"
                  aria-selected={!isRegister}
                  aria-controls="modal-auth-form"
                  onClick={() => setMode("login")}
                  className={[
                    "flex-1 rounded-md px-3 py-2 text-sm transition-colors focus-ring",
                    !isRegister ? "bg-background shadow-sm" : "text-muted-foreground hover:bg-background/50",
                  ].join(" ")}
                >
                  Đăng nhập
                </button>
                <button
                  type="button"
                  role="tab"
                  id="modal-tab-register"
                  aria-selected={isRegister}
                  aria-controls="modal-auth-form"
                  onClick={() => setMode("register")}
                  className={[
                    "flex-1 rounded-md px-3 py-2 text-sm transition-colors focus-ring",
                    isRegister ? "bg-background shadow-sm" : "text-muted-foreground hover:bg-background/50",
                  ].join(" ")}
                >
                  Đăng ký
                </button>
              </div>

              <form id="modal-auth-form" role="tabpanel" aria-labelledby={isRegister ? "modal-tab-register" : "modal-tab-login"} onSubmit={onSubmit} className="mt-6 space-y-4 rounded-xl bg-card border border-border p-6">
                {isRegister ? (
                  <label className="block">
                    <span className="text-xs text-muted-foreground">Tên hiển thị</span>
                    <input
                      ref={displayNameInputRef}
                      value={displayName}
                      onChange={(e) => setDisplayName(e.target.value)}
                      className="mt-1 w-full rounded-lg bg-input px-3 py-2 text-sm outline-none ring-1 ring-border focus:ring-2 focus:ring-primary"
                      placeholder="Sử Quan Tập Sự"
                      required
                    />
                  </label>
                ) : null}

                <label className="block">
                  <span className="text-xs text-muted-foreground">Email</span>
                  <input
                    ref={emailInputRef}
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="mt-1 w-full rounded-lg bg-input px-3 py-2 text-sm outline-none ring-1 ring-border focus:ring-2 focus:ring-primary"
                    placeholder="you@example.com"
                    required
                  />
                </label>

                <label className="block">
                  <span className="text-xs text-muted-foreground">Mật khẩu</span>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="mt-1 w-full rounded-lg bg-input px-3 py-2 text-sm outline-none ring-1 ring-border focus:ring-2 focus:ring-primary"
                    placeholder="••••••••"
                    minLength={isRegister ? 8 : 1}
                    required
                  />
                  {isRegister ? <p className="mt-2 text-xs text-muted-foreground">Tối thiểu 8 ký tự.</p> : null}
                </label>

                {error ? (
                  <div className="rounded-lg bg-destructive/15 px-3 py-2 text-sm text-destructive-foreground">
                    {error}
                  </div>
                ) : null}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60 transition-colors focus-ring"
                >
                  {loading ? "Vui lòng đợi..." : submitLabel}
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
