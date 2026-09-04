"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";

export function NavBar() {
  const { user, logout } = useAuth();
  const router = useRouter();

  return (
    <header className="flex items-center justify-between border-b border-black/10 px-6 py-3 dark:border-white/10">
      <Link href="/" className="text-sm font-semibold">
        Cortex
      </Link>
      {user && (
        <div className="flex items-center gap-3 text-sm text-black/60 dark:text-white/60">
          <span>{user.email}</span>
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
