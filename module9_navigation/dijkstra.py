"""
Module 9 — Dijkstra Shortest Path
===================================
Implements Dijkstra's algorithm for indoor navigation between parking
zones and the driver's destination (elevator, exit, staircase, etc.).

Usage:
    from module9_navigation.dijkstra import ParkingGraph
    g = ParkingGraph()
    g.load_default_layout()
    path, cost = g.find_path("A3", "EXIT_NORTH")
"""

import heapq
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Graph
# ──────────────────────────────────────────────

class ParkingGraph:
    """
    Weighted undirected graph representing a multi-zone parking lot.
    Nodes  = parking slots, waypoints, entrances, exits, elevators, etc.
    Edges  = walkable paths with distance (metres) as weight.
    """

    def __init__(self):
        # adjacency: {node: [(neighbour, weight), ...]}
        self._adj: dict[str, list[tuple[str, float]]] = {}
        # node metadata: {node: {"type": "slot"|"exit"|"elevator"|..., "level": int, ...}}
        self._meta: dict[str, dict] = {}

    # ── Graph Building ──────────────────────────────────────────────────

    def add_node(self, node_id: str, node_type: str = "slot", level: int = 1, **kwargs):
        """Register a node (slot, exit, elevator, staircase, …)."""
        if node_id not in self._adj:
            self._adj[node_id] = []
        self._meta[node_id] = {"type": node_type, "level": level, **kwargs}

    def add_edge(self, u: str, v: str, weight: float = 1.0):
        """Add undirected weighted edge between nodes u and v."""
        self.add_node(u)
        self.add_node(v)
        self._adj[u].append((v, weight))
        self._adj[v].append((u, weight))

    def node_meta(self, node_id: str) -> dict:
        return self._meta.get(node_id, {})

    # ── Pathfinding ─────────────────────────────────────────────────────

    def find_path(
        self,
        source: str,
        target: str,
        avoid: Optional[list[str]] = None,
    ) -> tuple[list[str], float]:
        """
        Dijkstra shortest path from source → target.

        Args:
            source  : Starting node ID (e.g. "A3")
            target  : Destination node ID (e.g. "EXIT_NORTH")
            avoid   : List of node IDs to exclude (e.g. blocked passages)

        Returns:
            (path, total_cost) where path is list of node IDs.
            If no path exists: ([], float("inf"))
        """
        if source not in self._adj:
            logger.error(f"Source node '{source}' not in graph.")
            return [], float("inf")
        if target not in self._adj:
            logger.error(f"Target node '{target}' not in graph.")
            return [], float("inf")

        blocked = set(avoid or [])

        dist   = {node: float("inf") for node in self._adj}
        prev   = {node: None         for node in self._adj}
        dist[source] = 0.0

        # Min-heap: (cost, node)
        heap = [(0.0, source)]

        while heap:
            cost, u = heapq.heappop(heap)

            if cost > dist[u]:
                continue

            if u == target:
                break

            for v, w in self._adj.get(u, []):
                if v in blocked:
                    continue
                new_cost = dist[u] + w
                if new_cost < dist[v]:
                    dist[v] = new_cost
                    prev[v] = u
                    heapq.heappush(heap, (new_cost, v))

        if dist[target] == float("inf"):
            logger.warning(f"No path found: {source} → {target}")
            return [], float("inf")

        # Reconstruct path
        path = []
        node = target
        while node is not None:
            path.append(node)
            node = prev[node]
        path.reverse()

        logger.info(f"Path: {' → '.join(path)} | Cost: {dist[target]:.1f}m")
        return path, round(dist[target], 2)

    def nearest_exit(self, source: str) -> tuple[Optional[str], float]:
        """Find the nearest exit node from a given source."""
        exits = [n for n, meta in self._meta.items() if meta.get("type") == "exit"]
        if not exits:
            return None, float("inf")
        best_exit, best_cost = None, float("inf")
        for exit_node in exits:
            _, cost = self.find_path(source, exit_node)
            if cost < best_cost:
                best_cost = cost
                best_exit = exit_node
        return best_exit, best_cost

    def nearest_elevator(self, source: str) -> tuple[Optional[str], float]:
        """Find the nearest elevator from a given source slot."""
        elevators = [n for n, meta in self._meta.items() if meta.get("type") == "elevator"]
        if not elevators:
            return None, float("inf")
        best, best_cost = None, float("inf")
        for elev in elevators:
            _, cost = self.find_path(source, elev)
            if cost < best_cost:
                best_cost = cost
                best = elev
        return best, best_cost

    # ── Serialization ────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "nodes": list(self._adj.keys()),
            "metadata": self._meta,
            "edges": [
                {"from": u, "to": v, "weight": w}
                for u, neighbours in self._adj.items()
                for v, w in neighbours
                if u < v  # Avoid duplicating undirected edges
            ],
        }

    def load_from_dict(self, data: dict):
        """Re-hydrate graph from serialised dict."""
        for edge in data.get("edges", []):
            self.add_edge(edge["from"], edge["to"], edge["weight"])
        for node_id, meta in data.get("metadata", {}).items():
            self._meta[node_id] = meta

    # ── Default Layout ───────────────────────────────────────────────────

    def load_default_layout(self):
        """
        Load a sample 2-level parking lot with Zones A, B, C and key
        waypoints (exits, elevators, EV bays).
        Distances are in metres (approximate walking distances).
        """
        # Level 1 — Zone A (slots A1–A10)
        for i in range(1, 11):
            self.add_node(f"A{i}", node_type="slot", level=1, zone="A")
        for i in range(1, 10):
            self.add_edge(f"A{i}", f"A{i+1}", weight=5.0)

        # Level 1 — Zone B (slots B1–B10)
        for i in range(1, 11):
            self.add_node(f"B{i}", node_type="slot", level=1, zone="B")
        for i in range(1, 10):
            self.add_edge(f"B{i}", f"B{i+1}", weight=5.0)

        # Cross-lane A ↔ B
        self.add_edge("A5", "B5", weight=8.0)
        self.add_edge("A1", "B1", weight=8.0)
        self.add_edge("A10", "B10", weight=8.0)

        # Level 1 exits & elevator
        self.add_node("EXIT_NORTH", node_type="exit", level=1)
        self.add_node("EXIT_SOUTH", node_type="exit", level=1)
        self.add_node("ELEVATOR_1", node_type="elevator", level=1)
        self.add_node("RECEPTION", node_type="waypoint", level=1)

        self.add_edge("A1",        "EXIT_NORTH", weight=12.0)
        self.add_edge("A10",       "EXIT_SOUTH", weight=15.0)
        self.add_edge("B1",        "EXIT_NORTH", weight=20.0)
        self.add_edge("B10",       "EXIT_SOUTH", weight=10.0)
        self.add_edge("A5",        "ELEVATOR_1", weight=6.0)
        self.add_edge("B5",        "ELEVATOR_1", weight=14.0)
        self.add_edge("EXIT_NORTH","RECEPTION",  weight=5.0)

        # Level 2 — Zone C (EV slots C1–C5)
        for i in range(1, 6):
            self.add_node(f"C{i}", node_type="slot", level=2, zone="C", is_ev=True)
        for i in range(1, 5):
            self.add_edge(f"C{i}", f"C{i+1}", weight=5.0)

        self.add_node("ELEVATOR_2", node_type="elevator", level=2)
        self.add_node("EXIT_LEVEL2", node_type="exit", level=2)

        self.add_edge("ELEVATOR_1", "ELEVATOR_2", weight=3.0)  # Elevator travel
        self.add_edge("C1",         "ELEVATOR_2", weight=8.0)
        self.add_edge("C5",         "EXIT_LEVEL2", weight=10.0)

        logger.info("Default 2-level parking graph loaded.")


# ──────────────────────────────────────────────
# CLI Demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    graph = ParkingGraph()
    graph.load_default_layout()

    # Find path from slot A7 to north exit
    path, cost = graph.find_path("A7", "EXIT_NORTH")
    print(f"A7 → EXIT_NORTH : {' → '.join(path)} ({cost}m)")

    # Find path from EV slot C3 to exit
    path2, cost2 = graph.find_path("C3", "EXIT_NORTH")
    print(f"C3 → EXIT_NORTH : {' → '.join(path2)} ({cost2}m)")

    # Nearest exit from B8
    exit_node, exit_cost = graph.nearest_exit("B8")
    print(f"Nearest exit from B8 : {exit_node} ({exit_cost}m)")

    print("\nGraph summary:", graph.to_dict()["edges"][:5], "...")
