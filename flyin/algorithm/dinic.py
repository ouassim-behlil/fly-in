from __future__ import annotations
from typing import Dict
from collections import deque
import sys

from .time_expanded_graph import TimeExpandedGraph, TimeExpandedNode


class Dinic:
    """Dinic's maximum flow algorithm."""

    def __init__(self, graph: TimeExpandedGraph):
        self.graph = graph
        self.level: Dict[TimeExpandedNode, int] = {}
        self.it: Dict[TimeExpandedNode, int] = {}

    def bfs(self, source: TimeExpandedNode, sink: TimeExpandedNode) -> bool:
        """
        BFS to build the level graph.
        Returns True if sink is reachable from source.
        """
        self.level = {source: 0}
        queue = deque([source])

        while queue:
            u = queue.popleft()

            for edge in self.graph.get_edges(u):
                if edge.dst not in self.level and edge.residual_capacity() > 0:
                    self.level[edge.dst] = self.level[u] + 1

                    if edge.dst == sink:
                        return True

                    queue.append(edge.dst)

        return False

    def dfs(
        self,
        u: TimeExpandedNode,
        sink: TimeExpandedNode,
        pushed: int
    ) -> int:
        """
        DFS to find augmenting paths and push flow.
        Return total flow pushed from u to sink.
        """
        if u == sink:
            return pushed

        edges = self.graph.get_edges(u)

        while self.it.get(u, 0) < len(edges):
            idx = self.it.get(u, 0)
            edge = edges[idx]

            if (
                edge.dst in self.level
                and self.level[edge.dst] == self.level[u] + 1
                and edge.residual_capacity() > 0
            ):
                flow = self.dfs(
                    edge.dst, sink, min(pushed, edge.residual_capacity())
                )

                if flow > 0:
                    edge.flow += flow
                    assert edge.reverse is not None
                    edge.reverse.flow -= flow
                    return flow
            self.it[u] = idx + 1
        return 0

    def max_flow(
        self, source: TimeExpandedNode, sink: TimeExpandedNode
    ) -> int:
        """Compute maximum flow from source to sink."""
        total_flow = 0

        while self.bfs(source, sink):
            self.it = {}

            while True:
                pushed = self.dfs(source, sink, sys.maxsize)
                if pushed == 0:
                    break
                total_flow += pushed

        return total_flow
