"use client";

import Link from "next/link";
import { GraduationCapIcon, LogOutIcon, UserIcon } from "lucide-react";

import { useAuthStore } from "@/stores/authStore";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export default function UserMenu() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  const displayName = user?.display_name || user?.email || "Tài khoản";
  const initial = displayName.trim().charAt(0).toUpperCase() || "U";

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          className="flex h-9 items-center gap-2 rounded-full border border-border/70 bg-secondary/40 p-1 pr-2 transition-colors hover:bg-secondary focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
          aria-label={`Mở menu tài khoản · ${displayName}`}
        >
          <Avatar className="size-7">
            {user?.avatar_url ? (
              <AvatarImage src={user.avatar_url} alt={displayName} />
            ) : null}
            <AvatarFallback>{initial}</AvatarFallback>
          </Avatar>
          <span className="hidden max-w-32 truncate text-xs font-semibold text-foreground lg:inline">
            {displayName}
          </span>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" sideOffset={8} className="w-56">
        <DropdownMenuLabel className="font-normal">
          <p className="truncate text-sm font-medium text-foreground">{displayName}</p>
          {user?.email ? (
            <p className="truncate text-xs font-normal text-muted-foreground">
              {user.email}
            </p>
          ) : null}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link href="/profile">
            <UserIcon aria-hidden="true" />
            Hồ sơ
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link href="/practice">
            <GraduationCapIcon aria-hidden="true" />
            Ôn tập
          </Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem variant="destructive" onClick={() => logout()}>
          <LogOutIcon aria-hidden="true" />
          Đăng xuất
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}