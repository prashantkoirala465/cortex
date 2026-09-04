"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";
import { friendlyErrorMessage } from "@/components/error-banner";
import { NavBar } from "@/components/nav-bar";
import { useAuth } from "@/context/auth-context";
import { useRequireAuth } from "@/hooks/use-require-auth";
import { sendChatMessage, type ChatTurn } from "@/lib/chat";
import type { NoteRef } from "@/lib/graph";

type DisplayMessage = ChatTurn & { sources?: NoteRef[]; isError?: boolean };

export default function ChatPage() {
  const { user, isLoading } = useRequireAuth();
  const { authFetch } = useAuth();

  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [isSending, setIsSending] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const q = question.trim();
    if (!q || isSending) return;

    const history: ChatTurn[] = messages.map(({ role, content }) => ({ role, content }));
    setMessages((prev) => [...prev, { role: "user", content: q }]);
    setQuestion("");
    setIsSending(true);
    try {
      const response = await sendChatMessage(authFetch, q, history);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.answer, sources: response.sources },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: friendlyErrorMessage(err), isError: true },
      ]);
    } finally {
      setIsSending(false);
    }
  }

  if (isLoading || !user) return null;

  return (
    <div className="flex flex-1 flex-col">
      <NavBar />
      <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-4 px-4 py-8">
        <h1 className="text-lg font-semibold">Ask your notes</h1>

        {messages.length === 0 && (
          <p className="text-sm text-black/50 dark:text-white/50">
            Ask a question and I&apos;ll answer using only what&apos;s in your notes, with links
            back to the ones I used.
          </p>
        )}

        <div className="flex flex-1 flex-col gap-4 overflow-y-auto">
          {messages.map((message, i) => (
            <div
              key={i}
              className={`flex flex-col gap-1 ${message.role === "user" ? "items-end" : "items-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                  message.isError
                    ? "bg-red-600/10 text-red-600 dark:text-red-400"
                    : message.role === "user"
                      ? "bg-foreground text-background"
                      : "bg-black/5 dark:bg-white/10"
                }`}
              >
                {message.content}
              </div>
              {message.sources && message.sources.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {message.sources.map((source) => (
                    <Link
                      key={source.id}
                      href={`/notes/${source.id}`}
                      className="rounded-full border border-black/15 px-2 py-0.5 text-xs text-black/60 hover:opacity-70 dark:border-white/20 dark:text-white/60"
                    >
                      {source.title || "Untitled"}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          ))}
          {isSending && (
            <div className="max-w-[85%] rounded-lg bg-black/5 px-3 py-2 text-sm text-black/40 dark:bg-white/10 dark:text-white/40">
              Thinking...
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask something..."
            className="flex-1 rounded border border-black/15 px-3 py-2 text-sm outline-none focus:border-black/40 dark:border-white/20 dark:focus:border-white/40"
          />
          <button
            type="submit"
            disabled={isSending || !question.trim()}
            className="rounded bg-foreground px-4 py-2 text-sm font-medium text-background disabled:opacity-50"
          >
            {isSending ? "..." : "Ask"}
          </button>
        </form>
      </main>
    </div>
  );
}
