"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/context/auth-context";

export default function Home() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) router.replace("/login");
  }, [isLoading, user, router]);

  if (isLoading || !user) return null;

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-4 px-4 text-center">
      <p className="text-sm text-black/60 dark:text-white/60">Signed in as {user.email}</p>
      <button
        onClick={() => logout()}
        className="rounded border border-black/15 px-3 py-1.5 text-sm dark:border-white/20"
      >
        Log out
      </button>
    </div>
  );
}
