from typing import List, Dict
import heapq
import sys

from flyin import (
    Connection,
    Drone,
    Zone,
    ZoneType
)

class MultiAgentRouter:

    def __init__(
        self,
        zones: Dict[str, Zone],
        connections: List[Connection],
        start_zone: Zone,
        end_zone: Zone
    ) -> None:
        self.zones = zones
        self.connections = connections
        self.end_zone = end_zone
        self.start_zone = start_zone

    def _adja(self, zone: str) -> Dict[str, int]:

        adjacent_zones = dict()

        for conn in self.connections:

            if zone == conn.zone1:
                adj = self.zones[conn.zone2]
            elif zone == conn.zone2:
                adj = self.zones[conn.zone1]

            else:
                continue

            adjacent_zones[adj.name] = adj.metadata.cost

        return adjacent_zones

    def _shortest_path(self, from_zone: Zone) -> List[str]:

        pq = list()
        dist = dict()
        parent = dict()

        parent[from_zone.name] = None

        heapq.heappush(pq, (0, from_zone.name))
        dist[from_zone.name] = 0
        while pq:
            d, u = heapq.heappop(pq)

            if u == self.end_zone.name:

                path = list()

                while u is not None:
                    path.append(u)
                    u = parent[u]

                return path[::-1]

            if d > dist.get(u, sys.maxsize):
                continue

            for v, w in self._adja(u).items():

                new_dist = dist[u] + w
                old_dist = dist.get(v, sys.maxsize)
                if new_dist < old_dist:
                    dist[v] = new_dist
                    heapq.heappush(pq, (new_dist, v))
                    parent[v] = u

                elif (
                    new_dist == old_dist
                    and self.zones[u].metadata.zone_type == ZoneType.PRIORITY
                ):
                    parent[v] = u

        return list()

