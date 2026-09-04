import type { AuthFetch } from "@/context/auth-context";

export type NoteRef = {
  id: string;
  title: string;
};

export type GraphNode = {
  id: string;
  name: string;
  type: string | null;
  notes: NoteRef[];
};

export type GraphEdge = {
  id: string;
  source: string;
  target: string;
  label: string;
  note_id: string;
};

export type Graph = {
  nodes: GraphNode[];
  edges: GraphEdge[];
};

export function getGraph(authFetch: AuthFetch) {
  return authFetch("/graph") as Promise<Graph>;
}
