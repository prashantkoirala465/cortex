import { describe, expect, it } from "vitest";
import { computeGraphLayout } from "@/lib/graph-layout";

describe("computeGraphLayout", () => {
  it("returns a position for every node", () => {
    const positions = computeGraphLayout(["a", "b", "c"], [{ source: "a", target: "b" }]);
    expect(Object.keys(positions).sort()).toEqual(["a", "b", "c"]);
  });

  it("produces finite coordinates", () => {
    const positions = computeGraphLayout(["a", "b"], [{ source: "a", target: "b" }]);
    for (const pos of Object.values(positions)) {
      expect(Number.isFinite(pos.x)).toBe(true);
      expect(Number.isFinite(pos.y)).toBe(true);
    }
  });

  it("handles an empty graph without throwing", () => {
    expect(computeGraphLayout([], [])).toEqual({});
  });

  it("handles a node with no edges", () => {
    const positions = computeGraphLayout(["lonely"], []);
    expect(positions.lonely).toBeDefined();
  });

  it("spaces connected nodes apart rather than stacking them at the origin", () => {
    const positions = computeGraphLayout(["a", "b"], [{ source: "a", target: "b" }]);
    const dx = positions.a.x - positions.b.x;
    const dy = positions.a.y - positions.b.y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    expect(distance).toBeGreaterThan(10);
  });
});
