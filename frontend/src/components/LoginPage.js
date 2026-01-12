"use client";

import { Suspense, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { useAuthStore } from "@/stores/authStore";

function LoginForm() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const returnUrl = searchParams.get("returnUrl");
    const redirectPath = useMemo(() => {
        if (!returnUrl) return null;
        const trimmed = returnUrl.trim();
        if (!trimmed.startsWith("/") || trimmed.startsWith("//")) return null;
        if (trimmed.startsWith("/login")) return null;
        return trimmed;
    }, [returnUrl]);
    const authLogin = useAuthStore((s) => s.login);
    const authRegister = useAuthStore((s) => s.register);
    const loading = useAuthStore((s) => s.loading);
    const error = useAuthStore((s) => s.error);

    const [mode, setMode] = useState("login"); // "login" | "register"
    const isRegister = mode === "register";

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [displayName, setDisplayName] = useState("");

    const submitLabel = useMemo(
        () => (isRegister ? "Tạo tài khoản" : "Đăng nhập"),
        [isRegister],
    );

    async function onSubmit(e) {
        e.preventDefault();
        if (loading) return;

        try {
            if (isRegister) {
                await authRegister({ email, password, displayName });
            } else {
                await authLogin({ email, password });
            }
            router.replace(redirectPath || "/dashboard");
        } catch {
            // Auth store already sets `error` for display.
        }
    }

    return (
        <div className="flex min-h-dvh flex-col items-center justify-center bg-background px-6 py-10 text-foreground">
            <div className="w-full max-w-md">
                <h1 className="text-2xl font-display font-semibold">
                    Lưu Niên Sử Kí
                </h1>
                <p className="mt-1 text-sm text-muted-foreground">
                    Đăng nhập để lưu tiến trình và xây dựng bộ sưu tập của bạn.
                </p>

                <div className="mt-6 flex rounded-lg bg-muted p-1">
                    <button
                        type="button"
                        onClick={() => setMode("login")}
                        className={[
                            "flex-1 rounded-md px-3 py-2 text-sm",
                            !isRegister
                                ? "bg-background shadow-sm"
                                : "text-muted-foreground hover:bg-background/50",
                        ].join(" ")}
                    >
                        Đăng nhập
                    </button>
                    <button
                        type="button"
                        onClick={() => setMode("register")}
                        className={[
                            "flex-1 rounded-md px-3 py-2 text-sm",
                            isRegister
                                ? "bg-background shadow-sm"
                                : "text-muted-foreground hover:bg-background/50",
                        ].join(" ")}
                    >
                        Đăng ký
                    </button>
                </div>

                <form
                    onSubmit={onSubmit}
                    className="mt-6 space-y-4 rounded-xl bg-card border border-border p-6"
                >
                    {isRegister ? (
                        <label className="block">
                            <span className="text-xs text-muted-foreground">
                                Tên hiển thị
                            </span>
                            <input
                                value={displayName}
                                onChange={(e) => setDisplayName(e.target.value)}
                                className="mt-1 w-full rounded-lg bg-input px-3 py-2 text-sm outline-none ring-1 ring-border focus:ring-2 focus:ring-primary"
                                placeholder="Sử Quan Tập Sự"
                                required
                            />
                        </label>
                    ) : null}

                    <label className="block">
                        <span className="text-xs text-muted-foreground">
                            Địa chỉ email
                        </span>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="mt-1 w-full rounded-lg bg-input px-3 py-2 text-sm outline-none ring-1 ring-border focus:ring-2 focus:ring-primary"
                            placeholder="you@example.com"
                            required
                        />
                    </label>

                    <label className="block">
                        <span className="text-xs text-muted-foreground">
                            Mật khẩu
                        </span>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="mt-1 w-full rounded-lg bg-input px-3 py-2 text-sm outline-none ring-1 ring-border focus:ring-2 focus:ring-primary"
                            placeholder="••••••••"
                            minLength={isRegister ? 8 : 1}
                            required
                        />
                        {isRegister ? (
                            <p className="mt-2 text-xs text-muted-foreground">
                                Tối thiểu 8 ký tự.
                            </p>
                        ) : null}
                    </label>

                    {error ? (
                        <div className="rounded-lg bg-destructive/15 px-3 py-2 text-sm text-destructive-foreground">
                            {error}
                        </div>
                    ) : null}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
                    >
                        {loading ? "Vui lòng đợi…" : submitLabel}
                    </button>
                </form>

                <p className="mt-6 text-xs text-muted-foreground">
                    API:{" "}
                    <span className="font-mono">
                        {process.env.NEXT_PUBLIC_API_BASE_URL || "same-origin"}
                    </span>
                </p>
            </div>
        </div>
    );
}

export default function LoginPage() {
    return (
        <Suspense fallback={<div className="min-h-dvh bg-background" />}>
            <LoginForm />
        </Suspense>
    );
}
