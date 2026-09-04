"use client";

import { Background, Controls, ReactFlow, type Edge, type Node } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ErrorBanner, friendlyErrorMessage } from "@/components/error-banner";
import { NavBar } from "@/components/nav-bar";
import { useAuth } from "@/context/auth-context";
import { useRequireAuth } from "@/hooks/use-require-auth";
import { computeGraphLayout } from "@/lib/graph-layout";
import { getGraph, type Graph, type GraphNode } from "@/lib/graph";

export default function GraphPage() {
  const { user, isLoading } = useRequireAuth();
  const { authFetch } = useAuth();
  const router = useRouter();

  const [graph, setGraph] = useState<Graph | null>(null);
  const [selected, setSelected] = useState<GraphNode | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    (async () => {
      try {
        setGraph(await getGraph(authFetch));
        setError(null);
      } catch (err) {
        setError(friendlyErrorMessage(err));
      }
    })();
  }, [user, authFetch]);

  const refresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      setGraph(await getGraph(authFetch));
      setSelected(null);
      setError(null);
    } catch (err) {
      setError(friendlyErrorMessage(err));
    } finally {
      setIsRefreshing(false);
    }
  }, [authFetch]);

  const { nodes, edges } = useMemo<{ nodes: Node[]; edges: Edge[] }>(() => {
    if (!graph || graph.nodes.length === 0) return { nodes: [], edges: [] };

    const degree: Record<string, number> = {};
    for (const edge of graph.edges) {
      degree[edge.source] = (degree[edge.source] ?? 0) + 1;
      degree[edge.target] = (degree[edge.target] ?? 0) + 1;
    }

    const positions = computeGraphLayout(
      graph.nodes.map((n) => n.id),
      graph.edges.map((e) => ({ source: e.source, target: e.target })),
    );

    const flowNodes: Node[] = graph.nodes.map((n) => {
      const weight = (degree[n.id] ?? 0) + n.notes.length;
      const size = Math.min(170, 72 + weight * 14);
      return {
        id: n.id,
        position: positions[n.id] ?? { x: 0, y: 0 },
        data: { label: n.name },
        style: {
          width: size,
          textAlign: "center",
          fontSize: 12,
          borderRadius: 999,
          background: "var(--background)",
          color: "var(--foreground)",
          borderColor: "var(--foreground)",
        },
      };
    });

    const flowEdges: Edge[] = graph.edges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      label: e.label,
      labelStyle: { fontSize: 10 },
      style: { stroke: "var(--foreground)", opacity: 0.4 },
    }));

    return { nodes: flowNodes, edges: flowEdges };
  }, [graph]);

  if (isLoading || !user) return null;

  return (
    <div className="flex flex-1 flex-col">
      <NavBar />
      <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-4 px-4 py-8">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-semibold">Knowledge graph</h1>
          <button
            onClick={() => refresh()}
            disabled={isRefreshing}
            className="rounded border border-black/15 px-3 py-1.5 text-sm disabled:opacity-50 dark:border-white/20"
          >
            {isRefreshing ? "..." : "Refresh"}
          </button>
        </div>

        {error && <ErrorBanner message={error} onRetry={refresh} />}

        {graph && graph.nodes.length === 0 && (
          <p className="text-sm text-black/50 dark:text-white/50">
            Nothing here yet — write and save a few notes, give the background worker a moment to
            process them, then refresh.
          </p>
        )}

        <div className="flex gap-4">
          <div
            className="flex-1 overflow-hidden rounded border border-black/10 dark:border-white/10"
            style={{ height: "70vh" }}
          >
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodeClick={(_, node) => {
                const found = graph?.nodes.find((n) => n.id === node.id) ?? null;
                setSelected(found);
              }}
              onEdgeClick={(_, edge) => {
                const ge = graph?.edges.find((e) => e.id === edge.id);
                if (ge) router.push(`/notes/${ge.note_id}`);
              }}
              fitView
            >
              <Background />
              <Controls />
            </ReactFlow>
          </div>

          {selected && (
            <aside className="w-64 shrink-0 rounded border border-black/10 p-4 dark:border-white/10">
              <h2 className="font-medium">{selected.name}</h2>
              {selected.type && (
                <p className="text-xs text-black/50 dark:text-white/50">{selected.type}</p>
              )}
              <p className="mt-3 text-xs font-medium text-black/60 dark:text-white/60">
                Mentioned in
              </p>
              <ul className="mt-1 flex flex-col gap-1">
                {selected.notes.map((note) => (
                  <li key={note.id}>
                    <Link href={`/notes/${note.id}`} className="text-sm underline">
                      {note.title || "Untitled"}
                    </Link>
                  </li>
                ))}
              </ul>
            </aside>
          )}
        </div>
      </main>
    </div>
  );
}
