"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";

export function NavBar() {
  const { user, logout } = useAuth();
  const router = useRouter();

  return (
    <header className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 border-b border-black/10 px-4 py-3 sm:px-6 dark:border-white/10">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
        <Link href="/" className="text-sm font-semibold">
          Cortex
        </Link>
        {user && (
          <>
            <Link href="/" className="text-sm text-black/60 hover:opacity-70 dark:text-white/60">
              Notes
            </Link>
            <Link href="/graph" className="text-sm text-black/60 hover:opacity-70 dark:text-white/60">
              Graph
            </Link>
            <Link href="/search" className="text-sm text-black/60 hover:opacity-70 dark:text-white/60">
              Search
            </Link>
            <Link href="/chat" className="text-sm text-black/60 hover:opacity-70 dark:text-white/60">
              Ask
            </Link>
          </>
        )}
      </div>
      {user && (
        <div className="flex items-center gap-3 text-sm text-black/60 dark:text-white/60">
          <span className="hidden sm:inline">{user.email}</span>
          <button
            onClick={async () => {
              await logout();
              router.push("/login");
            }}
            className="rounded border border-black/15 px-2 py-1 dark:border-white/20"
          >
            Log out
          </button>
        </div>
      )}
    </header>
  );
}
