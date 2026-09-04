import type { AuthFetch } from "@/context/auth-context";

export type SearchResult = {
  note_id: string;
  title: string;
  snippet: string;
  score: number;
};

export function searchNotes(authFetch: AuthFetch, query: string) {
  const params = new URLSearchParams({ q: query });
  return authFetch(`/search?${params.toString()}`) as Promise<SearchResult[]>;
}
