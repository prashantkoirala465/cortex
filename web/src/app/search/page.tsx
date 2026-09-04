"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";
import { NavBar } from "@/components/nav-bar";
import { useAuth } from "@/context/auth-context";
import { useRequireAuth } from "@/hooks/use-require-auth";
import { searchNotes, type SearchResult } from "@/lib/search";

export default function SearchPage() {
  const { user, isLoading } = useRequireAuth();
  const { authFetch } = useAuth();

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[] | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setIsSearching(true);
    try {
      setResults(await searchNotes(authFetch, query.trim()));
    } finally {
      setIsSearching(false);
    }
  }

  if (isLoading || !user) return null;

  return (
    <div className="flex flex-1 flex-col">
      <NavBar />
      <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-4 px-4 py-8">
        <h1 className="text-lg font-semibold">Search your notes</h1>

        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="What are you looking for?"
            autoFocus
            className="flex-1 rounded border border-black/15 px-3 py-2 text-sm outline-none focus:border-black/40 dark:border-white/20 dark:focus:border-white/40"
          />
          <button
            type="submit"
            disabled={isSearching || !query.trim()}
            className="rounded bg-foreground px-4 py-2 text-sm font-medium text-background disabled:opacity-50"
          >
            {isSearching ? "..." : "Search"}
          </button>
        </form>

        <p className="text-xs text-black/40 dark:text-white/40">
          Semantic search — matches by meaning, not just keywords, so it can take a moment.
        </p>

        {results !== null && results.length === 0 && (
          <p className="text-sm text-black/50 dark:text-white/50">No matching notes found.</p>
        )}

        <ul className="flex flex-col divide-y divide-black/10 dark:divide-white/10">
          {results?.map((result) => (
            <li key={result.note_id}>
              <Link
                href={`/notes/${result.note_id}`}
                className="flex flex-col gap-1 py-3 hover:opacity-70"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{result.title || "Untitled"}</span>
                  <span className="text-xs text-black/40 dark:text-white/40">
                    {Math.round(result.score * 100)}% match
                  </span>
                </div>
                <p className="line-clamp-2 text-sm text-black/60 dark:text-white/60">
                  {result.snippet}
                </p>
              </Link>
            </li>
          ))}
        </ul>
      </main>
    </div>
  );
}
