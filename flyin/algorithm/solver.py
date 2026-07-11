from __future__ import annotations


from pathlib import Path
from typing import List, Tuple

from flyin import MapParser
from flyin.model import Graph, Zone

from .dinic import Dinic
from .time_expanded_graph import TimeExpandedGraph, TimeExpandedNode


class Solver:
    """Find the minimum number of turns needed to route all drones."""

    def __init__(self, graph: Graph):
        self.graph: Graph = graph
        self.last_paths: List[List[Zone]] = []

    @classmethod
    def from_map(cls, path: str | Path) -> "Solver":
        parser = MapParser(Path(path))
        return cls(parser.parse())

    def max_deliverable(self, turns: int) -> int:
        if turns <= 0:
            raise ValueError("turns must be a positive integer")

        teg = TimeExpandedGraph(self.graph, turns)
        teg.build(turns)
        return Dinic(teg).max_flow(teg.source, teg.sink)

    def can_deliver_all(self, turns: int) -> bool:
        return self.max_deliverable(turns) >= self.graph.nb_drones

    def solve(self, max_turns: int = 100) -> Tuple[int, List[List[Zone]]]:
        """
        Return the minimum turn count required to route all drones.

        Raises ValueError if no feasible solution is found up to max_turns.
        """
        if max_turns <= 0:
            raise ValueError("max_turns must be a positive integer")

        # The time-expanded graph includes the initial state at t=0, so an
        # external "N turns" simulation requires N+1 time layers.
        cache: dict[int, tuple[int, TimeExpandedGraph]] = {}

        def evaluate(turns: int) -> tuple[int, TimeExpandedGraph]:
            if turns in cache:
                return cache[turns]

            layers = turns + 1
            teg = TimeExpandedGraph(self.graph, layers)
            teg.build(layers)
            max_flow = Dinic(teg).max_flow(teg.source, teg.sink)
            cache[turns] = (max_flow, teg)
            return max_flow, teg

        low, high = 1, max_turns
        best_turns: int | None = None
        best_teg: TimeExpandedGraph | None = None

        while low <= high:
            turns = (low + high) // 2
            max_flow, teg = evaluate(turns)

            if max_flow >= self.graph.nb_drones:
                best_turns = turns
                best_teg = teg
                high = turns - 1
            else:
                low = turns + 1

        if best_turns is None:
            raise ValueError(
                f"No feasible solution found up to {max_turns} turns "
                f"for {self.graph.nb_drones} drones."
            )

        if best_teg is None:
            _, best_teg = evaluate(best_turns)

        self.last_paths = self._extract_paths_per_drone(best_teg, self.graph.nb_drones)
        self._print_paths(self.last_paths)
        return best_turns, self.last_paths


    def _extract_paths_per_drone(
        self, teg: TimeExpandedGraph, nb_drones: int
    ) -> List[List[Zone]]:

        paths: List[List[Zone]] = []

        for _ in range(nb_drones):
            flow_path = self._consume_unit_flow_path(teg)
            if not flow_path:
                break

            zone_path: List[Zone] = []
            for node in flow_path:

                assert node.zone_name is not None, "Zone name is None"
                if node.zone_name.startswith("__") or not node.is_in:
                    continue

                zone: Zone | None = None
                for z in self.graph.zones:
                    if z.name == node.zone_name:
                        zone = z
                        break
                
                
                assert zone is not None, "Zone is not set"
                if not zone_path or zone_path[-1].name != zone.name:
                    zone_path.append(zone)
            paths.append(zone_path)

        if len(paths) != nb_drones:
            raise ValueError(
                "Failed to extract all drone paths from the computed max flow."
            )

        return paths

    def _consume_unit_flow_path(self, teg: TimeExpandedGraph) -> List[TimeExpandedNode]:
        def dfs(node: TimeExpandedNode, path: List[TimeExpandedNode]) -> List[TimeExpandedNode]:
            if node == teg.sink:
                return path

            for edge in teg.get_edges(node):
                if edge.flow <= 0:
                    continue
                if edge.dst in path:
                    continue

                found = dfs(edge.dst, path + [edge.dst])
                if found:
                    edge.flow -= 1
                    assert edge.reverse is not None
                    edge.reverse.flow += 1
                    return found

            return []

        return dfs(teg.source, [teg.source])

    def _print_paths(self, paths: List[List[Zone]]) -> None:
        for i, path in enumerate(paths, start=1):
            print(f"Drone {i}: {' -> '.join([z.name for z in path])}")