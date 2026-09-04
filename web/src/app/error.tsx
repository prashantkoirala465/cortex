"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-3 px-4 text-center">
      <p className="text-sm">Something went wrong.</p>
      <button
        onClick={reset}
        className="rounded border border-black/15 px-3 py-1.5 text-sm dark:border-white/20"
      >
        Try again
      </button>
    </div>
  );
}
