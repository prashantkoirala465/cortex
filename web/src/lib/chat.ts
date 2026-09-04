import type { AuthFetch } from "@/context/auth-context";
import type { NoteRef } from "@/lib/graph";

export type ChatTurn = {
  role: "user" | "assistant";
  content: string;
};

export type ChatResponse = {
  answer: string;
  sources: NoteRef[];
};

export function sendChatMessage(authFetch: AuthFetch, question: string, history: ChatTurn[]) {
  return authFetch("/chat", {
    method: "POST",
    body: JSON.stringify({ question, history }),
  }) as Promise<ChatResponse>;
}
