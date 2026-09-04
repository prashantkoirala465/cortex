import { forceCenter, forceCollide, forceLink, forceManyBody, forceSimulation } from "d3-force";

type SimNode = { id: string; x?: number; y?: number };

/** Runs a d3-force simulation to completion (synchronously, no animation)
 * and returns each node's resting position. React Flow doesn't lay nodes
 * out on its own - it just renders wherever you tell it to. */
export function computeGraphLayout(
  nodeIds: string[],
  links: { source: string; target: string }[],
): Record<string, { x: number; y: number }> {
  const nodes: SimNode[] = nodeIds.map((id) => ({ id }));

  const simulation = forceSimulation(nodes)
    .force(
      "link",
      forceLink(links)
        .id((d) => (d as SimNode).id)
        .distance(140),
    )
    .force("charge", forceManyBody().strength(-350))
    .force("center", forceCenter(0, 0))
    .force("collide", forceCollide(70))
    .stop();

  for (let i = 0; i < 300; i++) simulation.tick();

  const positions: Record<string, { x: number; y: number }> = {};
  for (const node of nodes) {
    positions[node.id] = { x: node.x ?? 0, y: node.y ?? 0 };
  }
  return positions;
}
