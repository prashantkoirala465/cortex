"use client";

import type { JSONContent } from "@tiptap/react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { NavBar } from "@/components/nav-bar";
import { NoteEditor } from "@/components/note-editor";
import { useAuth } from "@/context/auth-context";
import { useRequireAuth } from "@/hooks/use-require-auth";
import { ApiError } from "@/lib/api";
import { deleteNote, EMPTY_DOC, getNote, updateNote, type Note } from "@/lib/notes";

type SaveStatus = "idle" | "saving" | "saved" | "error";

const AUTOSAVE_DELAY_MS = 800;

export default function NotePage() {
  const { id } = useParams<{ id: string }>();
  const { user, isLoading } = useRequireAuth();
  const { authFetch } = useAuth();
  const router = useRouter();

  const [note, setNote] = useState<Note | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState<JSONContent>(EMPTY_DOC);
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle");

  const hasLoadedRef = useRef(false);
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!user) return;
    (async () => {
      try {
        const loaded = await getNote(authFetch, id);
        setNote(loaded);
        setTitle(loaded.title);
        setContent(loaded.content);
        // deferred so the editor's content-sync effect (which fires from
        // this same state update) doesn't get mistaken for a real edit
        setTimeout(() => {
          hasLoadedRef.current = true;
        }, 0);
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) setNotFound(true);
        else throw err;
      }
    })();
  }, [authFetch, id, user]);

  const scheduleSave = useCallback(
    (nextTitle: string, nextContent: JSONContent) => {
      if (!hasLoadedRef.current) return;
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
      setSaveStatus("saving");
      saveTimerRef.current = setTimeout(async () => {
        try {
          await updateNote(authFetch, id, { title: nextTitle, content: nextContent });
          setSaveStatus("saved");
        } catch {
          setSaveStatus("error");
        }
      }, AUTOSAVE_DELAY_MS);
    },
    [authFetch, id],
  );

  function handleTitleChange(value: string) {
    setTitle(value);
    scheduleSave(value, content);
  }

  function handleContentChange(value: JSONContent) {
    setContent(value);
    scheduleSave(title, value);
  }

  async function handleDelete() {
    if (!confirm("Delete this note? This can't be undone.")) return;
    await deleteNote(authFetch, id);
    router.push("/");
  }

  if (isLoading || !user) return null;

  if (notFound) {
    return (
      <div className="flex flex-1 flex-col">
        <NavBar />
        <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col items-center justify-center gap-3 px-4 text-center">
          <p>Note not found.</p>
          <Link href="/" className="text-sm underline">
            Back to your notes
          </Link>
        </main>
      </div>
    );
  }

  if (!note) return null;

  return (
    <div className="flex flex-1 flex-col">
      <NavBar />
      <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-3 px-4 py-8">
        <div className="flex items-center justify-between">
          <Link href="/" className="text-sm text-black/50 hover:opacity-70 dark:text-white/50">
            ← Back
          </Link>
          <div className="flex items-center gap-3">
            <span className="text-xs text-black/40 dark:text-white/40">
              {saveStatus === "saving" && "Saving..."}
              {saveStatus === "saved" && "Saved"}
              {saveStatus === "error" && "Failed to save"}
            </span>
            <button onClick={handleDelete} className="text-xs text-red-600 dark:text-red-400">
              Delete
            </button>
          </div>
        </div>

        <input
          value={title}
          onChange={(e) => handleTitleChange(e.target.value)}
          placeholder="Untitled"
          className="border-none bg-transparent text-2xl font-semibold outline-none placeholder:text-black/30 dark:placeholder:text-white/30"
        />

        <NoteEditor content={content} onChange={handleContentChange} />
      </main>
    </div>
  );
}
