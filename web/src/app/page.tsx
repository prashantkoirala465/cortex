"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { NavBar } from "@/components/nav-bar";
import { useAuth } from "@/context/auth-context";
import { useRequireAuth } from "@/hooks/use-require-auth";
import { createNote, EMPTY_DOC, listNotes, type Note } from "@/lib/notes";

function formatUpdatedAt(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export default function Home() {
  const { user, isLoading } = useRequireAuth();
  const { authFetch } = useAuth();
  const router = useRouter();

  const [notes, setNotes] = useState<Note[] | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    if (!user) return;
    (async () => {
      setNotes(await listNotes(authFetch));
    })();
  }, [user, authFetch]);

  async function handleNewNote() {
    setIsCreating(true);
    try {
      const note = await createNote(authFetch, { title: "", content: EMPTY_DOC });
      router.push(`/notes/${note.id}`);
    } finally {
      setIsCreating(false);
    }
  }

  if (isLoading || !user) return null;

  return (
    <div className="flex flex-1 flex-col">
      <NavBar />
      <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-4 px-4 py-8">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-semibold">Your notes</h1>
          <button
            onClick={handleNewNote}
            disabled={isCreating}
            className="rounded bg-foreground px-3 py-1.5 text-sm font-medium text-background disabled:opacity-50"
          >
            {isCreating ? "..." : "+ New note"}
          </button>
        </div>

        {notes === null && <p className="text-sm text-black/50 dark:text-white/50">Loading...</p>}

        {notes?.length === 0 && (
          <p className="text-sm text-black/50 dark:text-white/50">
            No notes yet — create your first one above.
          </p>
        )}

        <ul className="flex flex-col divide-y divide-black/10 dark:divide-white/10">
          {notes?.map((note) => (
            <li key={note.id}>
              <Link
                href={`/notes/${note.id}`}
                className="flex flex-col gap-0.5 py-3 hover:opacity-70"
              >
                <span className="font-medium">{note.title || "Untitled"}</span>
                <span className="text-xs text-black/50 dark:text-white/50">
                  Updated {formatUpdatedAt(note.updated_at)}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </main>
    </div>
  );
}
