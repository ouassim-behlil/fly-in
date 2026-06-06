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
            if zone == conn.zone1 or zone == conn.zone2:

                adj = self.zones[conn.zone1]
                if zone == conn.zone1:
                    adj = self.zones[conn.zone2]

                if adj.metadata.zone_type == ZoneType.BLOCKED:
                    continue

                adjacent_zones[adj.name] = self.zones[conn.zone2].metadata.cost

        return adjacent_zones

    def _distance_to_end_hub(self, from_zone: Zone) -> int:
        pq = list()
        dist = dict()

        heapq.heappush(pq, (0, self.end_zone.name))
        dist[self.end_zone.name] = 0
        while pq:
            d, u = heapq.heappop(pq)

            if d > dist.get(u, sys.maxsize):
                continue

            for v, w in self._adja(u).items():
                if dist.get(u, sys.maxsize) + w < dist.get(v, sys.maxsize):
                    dist[v] = dist.get(u, sys.maxsize) + w
                    heapq.heappush(pq, (dist[v], v))

        return dist.get(from_zone.name, sys.maxsize)
