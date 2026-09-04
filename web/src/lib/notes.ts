import type { JSONContent } from "@tiptap/react";
import type { AuthFetch } from "@/context/auth-context";
import type { SearchResult } from "@/lib/search";

export type Note = {
  id: string;
  title: string;
  content: JSONContent;
  created_at: string;
  updated_at: string;
};

export const EMPTY_DOC: JSONContent = { type: "doc", content: [{ type: "paragraph" }] };

export function listNotes(authFetch: AuthFetch) {
  return authFetch("/notes") as Promise<Note[]>;
}

export function getNote(authFetch: AuthFetch, id: string) {
  return authFetch(`/notes/${id}`) as Promise<Note>;
}

export function createNote(authFetch: AuthFetch, body: { title?: string; content?: JSONContent }) {
  return authFetch("/notes", { method: "POST", body: JSON.stringify(body) }) as Promise<Note>;
}

export function updateNote(
  authFetch: AuthFetch,
  id: string,
  body: { title?: string; content?: JSONContent },
) {
  return authFetch(`/notes/${id}`, { method: "PATCH", body: JSON.stringify(body) }) as Promise<Note>;
}

export function deleteNote(authFetch: AuthFetch, id: string) {
  return authFetch(`/notes/${id}`, { method: "DELETE" }) as Promise<void>;
}

export function getRelatedNotes(authFetch: AuthFetch, id: string) {
  return authFetch(`/notes/${id}/related`) as Promise<SearchResult[]>;
}
