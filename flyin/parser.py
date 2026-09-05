from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
from collections.abc import Callable
from collections import defaultdict, deque
from sys import maxsize

from flyin.model import Zone, Metadata, ZoneType, Connection, Graph
from flyin.utils import ParseError


class MapParser:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.nb_drones: Optional[int] = None
        self.zones: Dict[str, Zone] = {}
        self.unique_connections: Set[Tuple[str, str]] = set()
        self.connections: List[Connection] = []
        self.start_zone: Optional[Zone] = None
        self.end_zone: Optional[Zone] = None
        self.used_coordinates: Set[Tuple[int, int]] = set()

    def parse(self) -> Graph:
        handlers: Dict[str, Callable[[str, int], None]] = {
            "nb_drones": self._parse_nb_drones,
            "start_hub": self._parse_start_hub,
            "end_hub": self._parse_end_hub,
            "hub": self._parse_hub,
            "connection": self._parse_connection,
        }

        try:
            f_obj = self.path.open("r", encoding="utf-8", buffering=1 << 16)
        except FileNotFoundError:
            raise ParseError(
                0,
                f"File not found: '{self.path}'"
            )
        except PermissionError:
            raise ParseError(
                0,
                f"Permission denied: cannot open file '{self.path}'"
            )
        except OSError as e:
            raise ParseError(
                0,
                f"Cannot open file '{self.path}': {e}"
            )

        with f_obj as f:
            for line_number, raw in enumerate(f, start=1):
                line = raw.partition('#')[0].strip()

                if not line:
                    continue

                key, sep, value = line.partition(':')
                if not sep:
                    raise ParseError(
                        line_number,
                        f"Line should start with: '<key>:' but got {line}"
                    )

                key, value = key.strip(), value.strip()
                handler = handlers.get(key)

                if not handler:
                    raise ParseError(line_number, f"Unknown directive: {line}")

                if self.nb_drones is None and key != "nb_drones":
                    raise ParseError(
                        line_number,
                        "The first directive must be 'nb_drones'!"
                    )

                handler(value, line_number)

        self._validate_final_state()
        assert self.end_zone is not None
        assert self.nb_drones is not None
        assert self.start_zone is not None
        return Graph(
            self.nb_drones,
            list(self.zones.values()),
            self.connections,
            self.start_zone,
            self.end_zone
        )

    def _parse_nb_drones(self, value: str, line_number: int) -> None:
        if self.nb_drones is not None:
            raise ParseError(line_number, "nb_drones already declared")

        try:
            self.nb_drones = int(value)
        except ValueError:
            raise ParseError(
                line_number,
                f"nb_drones must be a positive integer! we got: '{value}'"
            )

        if self.nb_drones <= 0:
            raise ParseError(
                line_number,
                f"nb_drones must be positive! we got: '{value}'"
            )

    def _parse_start_hub(self, value: str, line_number: int) -> None:
        if self.start_zone:
            raise ParseError(
                line_number,
                "There must be exactly one start_hub zone!"
            )

        self.start_zone = self._parse_zone(value, line_number)

        if self.start_zone.metadata.zone_type == ZoneType.BLOCKED:
            self.start_zone.metadata.zone_type = ZoneType.NORMAL
            self.start_zone.metadata.cost = 1

        if self.nb_drones is not None:
            self.start_zone.metadata.max_drones = self.nb_drones
        else:
            self.start_zone.metadata.max_drones = maxsize

        self.zones[self.start_zone.name] = self.start_zone

    def _parse_end_hub(self, value: str, line_number: int) -> None:
        if self.end_zone:
            raise ParseError(
                line_number,
                "There must be exactly one end_hub zone!"
            )

        self.end_zone = self._parse_zone(value, line_number)

        if self.nb_drones is not None:
            self.end_zone.metadata.max_drones = self.nb_drones
        else:
            self.end_zone.metadata.max_drones = maxsize

        self.zones[self.end_zone.name] = self.end_zone

    def _parse_hub(self, value: str, line_number: int) -> None:
        zone = self._parse_zone(value, line_number)
        self.zones[zone.name] = zone

    def _parse_connection(self, line: str, line_number: int) -> None:
        connection = Connection()
        connection.max_link_capacity = 1

        start = -1
        idx = line.rfind('[')
        while idx != -1:
            if idx == 0 or line[idx - 1].isspace():
                start = idx
                break
            idx = line.rfind('[', 0, idx)

        end = -1
        if start != -1:
            end = line.rfind(']')
            if end < start:
                end = -1

        if start != -1 or end != -1:
            if start == -1 or end == -1 or end < start:
                raise ParseError(
                    line_number,
                    "Invalid metadata! Brackets not correctly closed."
                )

            meta_raw = line[start: end + 1]
            if meta_raw.count('[') != meta_raw.count(']'):
                raise ParseError(
                    line_number,
                    "Invalid metadata! Unbalanced brackets."
                )

            inner_content = line[start + 1: end]
            if '][' in inner_content or '] [' in inner_content:
                raise ParseError(
                    line_number,
                    "Invalid metadata! Adjacent or multiple "
                    "separate bracket groups are not allowed."
                )

            after_bracket = line[end + 1:].partition('#')[0].strip()
            if after_bracket:
                raise ParseError(
                    line_number,
                    f"Unexpected content after metadata brackets: "
                    f"'{after_bracket}'"
                )

            meta_str = inner_content.strip('[] ')
            if not meta_str:
                raise ParseError(
                    line_number,
                    "Metadata brackets must not be empty; "
                    "provide at least one key=value entry."
                )

            seen_keys: Set[str] = set()
            for element in meta_str.split():
                key, sep, value = element.partition('=')
                if not sep or key.strip() != 'max_link_capacity':
                    raise ParseError(
                        line_number,
                        f"Invalid connection metadata: '{element}'"
                    )

                if key in seen_keys:
                    raise ParseError(
                        line_number,
                        f"Duplicate metadata key '{key}' in connection."
                    )
                seen_keys.add(key)

                try:
                    capacity = int(value.strip())
                    if capacity <= 0:
                        raise ValueError
                    connection.max_link_capacity = capacity
                except ValueError:
                    raise ParseError(
                        line_number,
                        f"max_link_capacity must be a positive integer, "
                        f"got: '{value}'!"
                    )

            line = line[:start].strip()

        zone1, sep, zone2 = line.partition('-')
        if not sep:
            raise ParseError(
                line_number,
                f"Expected 'connection: <name1>-<name2>' but got: '{line}'"
            )

        zone1, zone2 = zone1.strip(), zone2.strip()

        if '-' in zone1 or '-' in zone2 or ' ' in zone1 or ' ' in zone2:
            raise ParseError(
                line_number,
                "Connection syntax forbids dashes and spaces in zone names!"
            )

        if zone1 not in self.zones or zone2 not in self.zones:
            raise ParseError(
                line_number,
                f"One or both zones in connection '{zone1}-{zone2}' "
                "do not exist!"
            )

        if zone1 == zone2:
            raise ParseError(
                line_number,
                f"A zone cannot be connected to itself: '{zone1}'"
            )

        if ((zone1, zone2) in self.unique_connections or
                (zone2, zone1) in self.unique_connections):
            raise ParseError(line_number, "Connection already exists!")

        connection.zone1 = zone1
        connection.zone2 = zone2
        self.connections.append(connection)
        self.unique_connections.add((zone1, zone2))

    def _parse_zone(self, line: str, line_number: int) -> "Zone":
        start = -1
        idx = line.rfind('[')
        while idx != -1:
            if idx == 0 or line[idx - 1].isspace():
                start = idx
                break
            idx = line.rfind('[', 0, idx)

        end = -1
        if start != -1:
            end = line.rfind(']')
            if end < start:
                end = -1

        if start != -1 or end != -1:
            if start == -1 or end == -1 or end < start:
                raise ParseError(
                    line_number,
                    "Invalid metadata! Brackets not correctly closed."
                )

            meta_raw = line[start: end + 1]
            if meta_raw.count('[') != meta_raw.count(']'):
                raise ParseError(
                    line_number,
                    "Invalid metadata! Unbalanced brackets."
                )

            inner_content = line[start + 1: end]
            if '][' in inner_content or '] [' in inner_content:
                raise ParseError(
                    line_number,
                    "Invalid metadata! Adjacent or multiple "
                    "separate bracket groups are not allowed."
                )

            after_bracket = line[end + 1:].partition('#')[0].strip()
            if after_bracket:
                raise ParseError(
                    line_number,
                    f"Unexpected content after metadata brackets: "
                    f"'{after_bracket}'"
                )

            meta_str = inner_content.strip('[] ')
            if not meta_str:
                raise ParseError(
                    line_number,
                    "Metadata brackets must not be empty; "
                    "provide at least one key=value entry."
                )

            metadata = self._parse_zone_metadata(meta_str, line_number)
            line = line[:start].strip()
        else:
            metadata = Metadata()
            metadata.zone_type = ZoneType.NORMAL
            metadata.max_drones = 1
            metadata.cost = 1

        line_split = line.split()
        if len(line_split) != 3:
            raise ParseError(
                line_number,
                f"Invalid number of zone parameters, expected 3 "
                f"but got {len(line_split)}"
            )

        name, _x, _y = line_split

        if '-' in name:
            raise ParseError(
                line_number,
                "Zone names cannot contain the '-' character!"
            )

        if any(c.isspace() for c in name):
            raise ParseError(
                line_number,
                "Zone names cannot contain whitespace!"
            )

        if name in self.zones:
            raise ParseError(
                line_number, f"Zone name '{name}' already exists!"
            )

        try:
            x, y = int(_x), int(_y)
        except ValueError:
            raise ParseError(line_number, "Zone coordinates must be integers!")

        coords = (x, y)
        if coords in self.used_coordinates:
            raise ParseError(
                line_number,
                f"Coordinates ({x}, {y}) are already used by another zone!"
            )
        self.used_coordinates.add(coords)

        return Zone(name=name, x=x, y=y, metadata=metadata)

    def _parse_zone_metadata(
        self, meta_str: str, line_number: int
    ) -> "Metadata":
        metadata = Metadata()
        metadata.zone_type = ZoneType.NORMAL
        metadata.max_drones = 1
        metadata.cost = 1

        zone_type_map: Dict[str, ZoneType] = {
            'normal': ZoneType.NORMAL,
            'blocked': ZoneType.BLOCKED,
            'restricted': ZoneType.RESTRICTED,
            'priority': ZoneType.PRIORITY
        }

        seen_keys: Set[str] = set()
        for element in meta_str.split():
            key, sep, value = element.partition('=')
            if not sep:
                raise ParseError(
                    line_number,
                    f"Invalid metadata element: '{element}'"
                )

            if key in seen_keys:
                raise ParseError(
                    line_number,
                    f"Duplicate metadata key '{key}' in zone."
                )
            seen_keys.add(key)

            if key == 'zone':
                if value not in zone_type_map:
                    raise ParseError(
                        line_number,
                        f"Invalid zone type: '{value}'!"
                    )
                metadata.zone_type = zone_type_map[value]
                if metadata.zone_type == ZoneType.RESTRICTED:
                    metadata.cost = 2
            elif key == 'color':
                if not value:
                    raise ParseError(line_number, "Color cannot be empty!")
                metadata.color = value
            elif key == 'max_drones':
                try:
                    capacity = int(value)
                    if capacity <= 0:
                        raise ValueError
                    metadata.max_drones = capacity
                except ValueError:
                    raise ParseError(
                        line_number,
                        f"max_drones must be a positive integer, "
                        f"got: '{value}'!"
                    )
            else:
                raise ParseError(
                    line_number, f"Invalid metadata key: '{key}'!"
                )

        return metadata

    def check_connectivity(self) -> bool:
        if not self.start_zone:
            return False

        g: Dict[str, List[str]] = defaultdict(list)
        for u, v in self.unique_connections:
            g[u].append(v)
            g[v].append(u)

        start: str = self.start_zone.name
        queue = deque([start])
        visited: Set[str] = {start}

        while queue:
            zone = queue.popleft()
            for neighbor in g[zone]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return len(visited) == len(self.zones)

    def _validate_final_state(self) -> None:
        if self.nb_drones is None:
            raise ParseError(0, "Missing nb_drones declaration")
        if self.start_zone is None:
            raise ParseError(0, "Missing start_hub declaration")
        if self.end_zone is None:
            raise ParseError(0, "Missing end_hub declaration")

        if self.start_zone and self.nb_drones is not None:
            self.start_zone.metadata.max_drones = self.nb_drones
        if self.end_zone and self.nb_drones is not None:
            self.end_zone.metadata.max_drones = self.nb_drones

        if not self.check_connectivity():
            raise ParseError(
                0,
                "Disconnected map: some zones cannot be reached."
            )

    def print_start_zone(self) -> None:
        assert self.start_zone is not None, "Start zone not set"
        print('-' * 100)
        print("Start Zone:")
        print("name:", self.start_zone.name)
        print("x:", self.start_zone.x)
        print("y:", self.start_zone.y)
        print("zone type:", self.start_zone.metadata.zone_type)
        print("color:", self.start_zone.metadata.color)
        print("max drones:", self.start_zone.metadata.max_drones)

    def print_end_zone(self) -> None:
        assert self.end_zone is not None, "End zone not set"
        print('-' * 100)
        print("End Zone:")
        print("name:", self.end_zone.name)
        print("x:", self.end_zone.x)
        print("y:", self.end_zone.y)
        print("zone type:", self.end_zone.metadata.zone_type)
        print("color:", self.end_zone.metadata.color)
        print("max drones:", self.end_zone.metadata.max_drones)

    def print_hub_zones(self) -> None:
        print("Hub Zones:" + '-' * 50)
        for zone in self.zones.values():
            print()
            print("name:", zone.name)
            print("x:", zone.x)
            print("y:", zone.y)
            print("zone type:", zone.metadata.zone_type)
            print("color:", zone.metadata.color)
            print("max drones:", zone.metadata.max_drones)

    def print_connections(self) -> None:
        print('-' * 100)
        for con in self.connections:
            print()
            print("Zone 1:", con.zone1)
            print("Zone 2:", con.zone2)
            print("max_link_capacity:", con.max_link_capacity)
            print()
