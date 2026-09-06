from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path
from typing import List, Tuple

from flyin import MapParser, InfeasibleMapError
from flyin.utils import colorize
from flyin.model import Graph, Zone, ZoneType


from .dinic import Dinic
from .time_expanded_graph import TimeExpandedGraph, TimeExpandedNode


class Solver:
    """Find the minimum number of turns needed to route all drones."""

    def __init__(self, graph: Graph):
        self.graph: Graph = graph
        self.last_paths: List[List[Zone]] = []
        self._zone_lookup = {zone.name: zone for zone in graph.zones}

    @classmethod
    def from_map(cls, path: str | Path) -> "Solver":
        parser = MapParser(Path(path))
        return cls(parser.parse())

    def is_feasible(self) -> bool:
        """
        Check if there is a traversable path from start_zone to end_zone.
        Blocked zones (ZoneType.BLOCKED) cannot be traversed.
        """
        start = self.graph.start_zone
        end = self.graph.end_zone

        if not start or not end:
            return False

        if (
            start.metadata.zone_type == ZoneType.BLOCKED
            or end.metadata.zone_type == ZoneType.BLOCKED
        ):
            return False

        if self.graph.nb_drones <= 0:
            return False

        # Build adjacency graph for unblocked connections
        adj: dict[str, list[str]] = defaultdict(list)
        for conn in self.graph.connections:
            if not conn.zone1 or not conn.zone2 or conn.max_link_capacity <= 0:
                continue

            z1 = self._zone_lookup.get(conn.zone1)
            z2 = self._zone_lookup.get(conn.zone2)

            if not z1 or not z2:
                continue

            if (
                z1.metadata.zone_type == ZoneType.BLOCKED
                or z2.metadata.zone_type == ZoneType.BLOCKED
            ):
                continue

            adj[conn.zone1].append(conn.zone2)
            adj[conn.zone2].append(conn.zone1)

        # BFS from start to end
        queue = deque([start.name])
        visited: set[str] = {start.name}

        while queue:
            curr = queue.popleft()
            if curr == end.name:
                return True

            for neighbor in adj[curr]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return False

    def check_feasibility(self) -> None:
        """
        Validate that the map is feasible before solving.
        Raises InfeasibleMapError if no traversable path exists.
        """
        if not self.is_feasible():
            s_name = self.graph.start_zone.name
            e_name = self.graph.end_zone.name
            raise InfeasibleMapError(
                f"No feasible path exists between start hub '{s_name}' "
                f"and end hub '{e_name}'."
            )

    def max_deliverable(self, turns: int) -> int:
        if turns <= 0:
            raise ValueError("turns must be a positive integer")

        teg = TimeExpandedGraph(self.graph, turns)
        teg.build(turns)
        return Dinic(teg).max_flow(teg.source, teg.sink)

    def can_deliver_all(self, turns: int) -> bool:
        return self.max_deliverable(turns) >= self.graph.nb_drones

    def solve(self, max_turns: int = 10000) -> Tuple[int, List[List[Zone]]]:
        """
        Return the minimum turn count required to route all drones.

        Raises InfeasibleMapError if no feasible solution is possible.
        Raises ValueError if no solution is found up to max_turns.
        """
        if max_turns <= 0:
            raise ValueError("max_turns must be a positive integer")

        self.check_feasibility()

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

        self.last_paths = self._extract_paths_per_drone(
            best_teg, self.graph.nb_drones, best_turns
        )
        return best_turns, self.last_paths

    def _extract_paths_per_drone(
        self, teg: TimeExpandedGraph, nb_drones: int, turns: int
    ) -> List[List[Zone]]:

        paths: List[List[Zone]] = []

        for _ in range(nb_drones):
            flow_path = self._consume_unit_flow_path(teg)
            if not flow_path:
                break

            turn_to_zone: dict[int, Zone] = {}
            for node in flow_path:
                assert node.zone_name is not None, "Zone name is None"
                if node.zone_name.startswith("__") or not node.is_in:
                    continue

                zone = self._zone_lookup.get(node.zone_name)
                assert zone is not None, "Zone is not set"
                turn_to_zone[node.turn] = zone

            if not turn_to_zone:
                raise ValueError(
                    "Failed to extract a turn-based path for a drone."
                )

            timeline: List[Zone] = []
            current = self.graph.start_zone
            for turn in range(turns + 1):
                if turn in turn_to_zone:
                    current = turn_to_zone[turn]
                timeline.append(current)

            paths.append(timeline)

        if len(paths) != nb_drones:
            raise ValueError(
                "Failed to extract all drone paths from the computed max flow."
            )

        return paths

    def _consume_unit_flow_path(
        self, teg: TimeExpandedGraph
    ) -> List[TimeExpandedNode]:
        def dfs(
            node: TimeExpandedNode, path: List[TimeExpandedNode]
        ) -> List[TimeExpandedNode]:
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
            names = [colorize(z.name, z.metadata.color) for z in path]
            print(f"Drone {i}: {' -> '.join(names)}")

    def print_output(
        self,
        paths: List[List[Zone]],
        turns: int,
        use_color: bool = True
    ) -> None:
        outputs: List[List[str]] = [[] for _ in range(turns)]

        def fmt_zone(z: Zone) -> str:
            if not use_color:
                return z.name
            return colorize(z.name, z.metadata.color)

        for i, path in enumerate(paths, start=1):
            # Process per drone to place restricted-zone travel over two turns:
            # departure turn: Dk-src-restricted, next turn: Dk-restricted.
            for t in range(1, min(turns + 1, len(path))):
                prev_zone = path[t - 1]
                curr_zone = path[t]

                if curr_zone.name == prev_zone.name:
                    continue

                if curr_zone.metadata.zone_type == ZoneType.RESTRICTED:
                    if t - 1 >= 1:
                        p_name = fmt_zone(prev_zone)
                        c_name = fmt_zone(curr_zone)
                        token = f"D{i}-{p_name}-{c_name}"
                        outputs[t - 2].append(token)
                    outputs[t - 1].append(f"D{i}-{fmt_zone(curr_zone)}")
                    continue

                outputs[t - 1].append(f"D{i}-{fmt_zone(curr_zone)}")

        for turn_output in outputs:
            print(f"{' '.join(turn_output)}")
