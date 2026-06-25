
from pathlib import Path
from typing import Dict, List, Tuple, Set

from flyin.model import Zone, Metadata, ZoneType, Connection, Graph
from flyin.utils import ParseError


class MapParser:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.nb_drones: int | None = None
        self.zones: Dict[str, Zone] = dict()
        self.unique_connections: Set[Tuple[str, str]] = set()
        self.connections: List[Connection] = list()
        self.start_zone: str | None = None
        self.end_zone: str | None = None

    def parse(self) -> None:

        handlers = {
                    "nb_drones": self._parse_nb_drones,
                    "start_hub": self._parse_start_hub,
                    "end_hub": self._parse_end_hub,
                    "hub": self._parse_hub,
                    "connection": self._parse_connection,
                }


        with self.path.open("r", encoding="utf-8", buffering=1 << 16) as f:

            for line_number, raw in enumerate(f, start=1):

                line = raw.strip()
                
                rest, sep, comment = line.partition('#')

                if sep:
                    line = rest.strip()
                
                if len(line) == 0:
                    continue
                

                key, sep, value = line.partition(':')

                if not sep:
                    raise ParseError(line_number, f"Line should start with: '<key>:' but got {line}")

                key = key.strip()
                value = value.strip()

                handler = handlers.get(key)

                if not handler:
                    raise ParseError(line_number, f"Unknown directive: {line}")
                
                handler(value, line_number)

        self._validate_final_state()

        return Graph(
            self.nb_drones,
            list(self.zones.values()),
            self.connections,
            self.start_zone,
            self.end_zone
        )
        
    def _parse_nb_drones(self, value: str, line_number: int) -> None:

        if self.nb_drones:
            raise ParseError(line_number, "nb_drones already declared")

        try:
            self.nb_drones = int(value)
        except (ValueError, ParseError):
            raise ParseError(line_number, f"nb_drones must be a positive number! we got: '{value}'")

        if self.nb_drones <= 0:
            raise ParseError(line_number, f"nb_drones must be a positive number! we got: '{value}'")
    
    def _parse_start_hub(self, value: str, line_number: int) -> None:

        if self.start_zone:
            raise ParseError(line_number, "There must be exactly one start_hub zone!")

        self.start_zone = self._parse_zone(value, line_number)
        self.zones[self.start_zone.name] = self.start_zone
        

    def _parse_end_hub(self, value: str, line_number: int) -> None:

        if self.end_zone:
            raise ParseError(line_number, "There must be exactly one end_hub zone!")

        self.end_zone = self._parse_zone(value, line_number)
        self.zones[self.end_zone.name] = self.end_zone

    def _parse_hub(self, value: str, line_number: int) -> None:

        zone = self._parse_zone(value, line_number)
        self.zones[zone.name] = zone

    def _parse_connection(self, line: str, line_number: int) -> None:

        connection = Connection()

        # case when metadata exist
        start, end = line.find('['), line.find(']')

        if start != -1:

            if end == -1:
                raise ParseError(
                    line_number,
                    "Invalid metadata! Bracket not closed"
                )

            meta_str = line[start + 1: end].strip()

            key, sep, value = meta_str.partition('=')

            key = key.strip()
            value = value.strip()

            if not sep:
                raise ParseError(
                    line_number,
                    f"Invalid metadata! expected 'key=value' but got {meta_str}"
                )

            if key != 'max_link_capacity':
                raise ParseError(
                    line_number,
                    f"Invalid key in connection metadata: '{key}'!"
                )

            try:
                connection.max_link_capacity = int(value)
            except ValueError:
                raise ParseError(
                    line_number,
                    f"max_link_capacity must be an integer but got: '{value.strip()}'!"
                )

            line = line[:start]

        zone1, sep, zone2 = line.partition('-')

        if not sep:
            raise ParseError(
                line_number,
                f"Expected 'connection: <name1>-<name2>' but got: '{line}'"
            )

        zone1, zone2 = zone1.strip(), zone2.strip()

        if '-' in zone1 or '-' in zone2:

            raise ParseError(
                line_number,
                "The connection syntax forbids dashes in zone names!"
            )

        if zone1 not in self.zones:

            raise ParseError(line_number, f"{zone1} not in zones!")

        if zone2 not in self.zones:

            raise ParseError(line_number, f"{zone2} not in zones!")

        if (zone1, zone2) in self.unique_connections or (zone2, zone1) in self.unique_connections:

            raise ParseError(
                line_number,
                "Connection already exist!"
            )
        connection.zone1 = zone1
        connection.zone2 = zone2
        self.connections.append(connection)

        self.unique_connections.add((zone1, zone2))

    def _parse_zone(self, line: str, line_number: int) -> "Zone":
        
        # Parse name, coords and metadata
        metadata = Metadata()

        start = line.find('[')

        if start != -1:

            metadata = self._parse_zone_metadata(line, line_number)

            line = line[:start].strip()

        line_split = line.split()

        if len(line_split) != 3:

            raise ParseError(
                line_number,
                "Invalid number of zone parameters expected "
                f"but got {len(line.split())}"
            )

        name, x, y = line_split

        if '-' in name:

            raise ParseError(
                line_number,
                "Zone names can use any valid characters but dashes and spaces!"
                )

        if name in self.zones:

            raise ParseError(
                line_number,
                "Each zone must have a unique name!"
            )

        try:

            x, y = int(x), int(y)

        except ValueError:

            raise ParseError(
                line_number,
                "Each zone must have valid integer coordinates!"
            )

        zone = Zone(
            name = name,
            x=x,
            y=y,
            metadata=metadata
        )
        return zone
    
    def _parse_zone_metadata(self, line: str, line_number: int) -> "Metadata":

        start = line.find('[')
        end = line.find(']')

        if start == -1 or end == -1:
            raise ParseError(line_number, "Invalid metadata! use brackets.")

        meta_str = line[start + 1: end].strip()

        metadata = Metadata()

        zone_type_handler = {
            'normal': ZoneType.NORMAL,
            'blocked': ZoneType.BLOCKED,
            'restricted': ZoneType.RESTRICTED,
            'priority': ZoneType.PRIORITY
        }

        for element in  meta_str.split():

            key, sep, value = element.partition('=')

            if not sep:
                raise ParseError(
                    line_number,
                    f"Invalid metadata! expected 'key=value' but got {element}"
                )

            if key == 'zone':
                metadata.zone_type = zone_type_handler.get(value)

                if not metadata.zone_type:

                    raise ParseError(
                        line_number,
                        f"Invalid zone type: {value}!"
                    )

                if value == 'restricted':
                    metadata.cost = 2
                    
            elif key == 'color':

                if len(value) == 0:

                    raise ParseError(
                        line_number,
                        f"Color must be a single word but got: {value}"
                    )

                metadata.color = value
            
            elif key == 'max_drones':

                try:

                    metadata.max_drones = int(value)

                except ValueError:

                    raise ParseError(
                        line_number,
                        f"max_drones must be an integer but got: {value}!"
                    )
            else:

                raise ParseError(
                    line_number,
                    f"Invalid key in metadata: {key}!"
                )
        
        return metadata

    def _validate_final_state(self) -> None:

        if self.nb_drones is None:

            raise ParseError(0, "Missing nb_drones")

        if self.start_zone is None:

            raise ParseError(0, "Missing start_hub")

        if self.end_zone is None:

            raise ParseError(0, "Missing end_hub")

    def print_start_zone(self) -> None:
        print('-' * 100)
        print("Start Zone:")
        print("name:", self.start_zone.name)
        print("x:", self.start_zone.x)
        print("y:", self.start_zone.y)
        print("zone type:", self.start_zone.metadata.zone_type)
        print("color:", self.start_zone.metadata.color)
        print("max drones:", self.start_zone.metadata.max_drones)

    def print_end_zone(self) -> None:
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

    def print_connections(self):
        print('-' * 100)
        for con in self.connections:
            print()
            print("Zone 1:", con.zone1)
            print("Zone 2:", con.zone2)
            print("max_link_capacity:", con.max_link_capacity)
            print()