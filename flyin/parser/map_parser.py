from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from flyin import Zone
from flyin import Metadata, ZoneType
from flyin import Connection
from flyin.utils.errors import ParseError


class MapParser:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.nb_drones: int | None = None
        self.zones: Dict[str, Zone] = dict()
        self.connections: List[Connection] = list()
        self.start_zone: str | None = None
        self.end_zone: str | None = None

    def parse(self) -> None:
        with self.path.open("r", encoding="utf-8") as f:
            for line_number, raw in enumerate(f, start=1):
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                # TODO: dispatch to specific handlers
                if line.startswith("nb_drones:"):
                    self._parse_nb_drones(line, line_number)
                elif line.startswith("start_hub:"):
                    self._parse_start_hub(line, line_number)
                elif line.startswith("end_hub:"):
                    self._parse_end_hub(line, line_number)
                elif line.startswith("hub:"):
                    self._parse_hub(line, line_number)
                elif line.startswith("connection:"):
                    self._parse_connection(line, line_number)
                else:
                    raise ParseError(line_number, f"Unknown directive: {line}")

        self._validate_final_state()

    def _parse_nb_drones(self, line: str, line_number: int) -> None:
        try:
            _, value = line.split(":", 1)
            self.nb_drones = int(value.strip())
        except ValueError:
            raise ParseError(line_number, f"nb_drones must be a positive number! we got: '{value.strip()}'")

        if self.nb_drones <= 0:
                raise ParseError(
                    line_number,
                    f"nb_drones must be a positive number! we got {self.nb_drones}"
                )
    
    def _parse_start_hub(self, line: str, line_number: int) -> None:
        # TODO: parse name, coords, metadata
        if self.start_zone:
            raise ParseError(line_number, "There must be exactly one start_hub zone!")

        self.start_zone = self._parse_zone(line, line_number)
        

    def _parse_end_hub(self, line: str, line_number: int) -> None:
        if self.end_zone:
            raise ParseError(line_number, "There must be exactly one end_hub zone!")

        self.end_zone = self._parse_zone(line, line_number)

    def _parse_hub(self, line: str, line_number: int) -> None:
        zone = self._parse_zone(line, line_number)
        self.zones[zone.name] = zone

    def _parse_connection(self, line: str, line_number: int) -> None:
        # TODO: parse connection + metadata
        pass

    def _parse_zone(self, line: str, line_number: int) -> "Zone":
        
        # Parse name, coords and metadata
        if '[' in line:
            if len(line.split()) != 5:
                raise ParseError(
                    line_number,
                    f"Invalid number of parameters expected 5 but got {len(line.split())}"
                )
            try:
                _, name, x, y, _ = line.split(maxsplit=4)
            except ValueError:
                raise ParseError(line_number, "Invalid zone!")

            metadata = self._parse_zone_metadata(line, line_number)

        else:
            if len(line.split()) != 4:
                raise ParseError(
                    line_number,
                    f"Invalid number of parameters expected 4 but got {len(line.split())}"
                )
            metadata = Metadata()
            try:
                _, name, x, y = line.split(maxsplit=3)
            except ValueError:
                raise ParseError(line_number, "Invalid zone!")

        if any([restricted in name for restricted in ['-', ' ']]):
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

        meta_str = line[start + 1: end]
        metadata = Metadata()
        for element in  meta_str.strip().split():
            try:
                key, value = element.split(sep='=', maxsplit=1)
            except ValueError:
                raise ParseError(
                    line_number,
                    f"Invalid metadata! expected 'key=value' but got {element}"
                )

            if key == 'zone':
                if value == 'normal':
                    metadata.zone = ZoneType.NORMAL
                elif value == 'blocked':
                    metadata.zone = ZoneType.BLOCKED
                elif value == 'restricted':
                    metadata.zone = ZoneType.RESTRICTED
                elif value == 'priority':
                    metadata.zone = ZoneType.PRIORITY
                else:
                    raise ParseError(
                        line_number,
                        f"Invalid zone type: {value}!"
                    )
            elif key == 'color':
                if len(value.split()) != 1:
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
        # if self.end_zone is None:
        #     raise ParseError(0, "Missing end_hub")

    def print_start_zone(self) -> None:
        print()
        print("Start Zone:")
        print("name:", self.start_zone.name)
        print("x:", self.start_zone.x)
        print("y:", self.start_zone.y)
        print("zone type:", self.start_zone.metadata.zone)
        print("color:", self.start_zone.metadata.color)
        print("max drones:", self.start_zone.metadata.max_drones)

    def print_end_zone(self) -> None:
        print()
        print("Start Zone:")
        print("name:", self.end_zone.name)
        print("x:", self.end_zone.x)
        print("y:", self.end_zone.y)
        print("zone type:", self.end_zone.metadata.zone)
        print("color:", self.end_zone.metadata.color)
        print("max drones:", self.end_zone.metadata.max_drones)

    def print_hub_zones(self) -> None:
        for zone in self.zones.values():
            print()
            print("Hub Zone:")
            print("name:", zone.name)
            print("x:", zone.x)
            print("y:", zone.y)
            print("zone type:", zone.metadata.zone)
            print("color:", zone.metadata.color)
            print("max drones:", zone.metadata.max_drones)