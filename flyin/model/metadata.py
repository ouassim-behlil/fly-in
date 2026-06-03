from dataclasses import dataclass
from enum import Enum


class ZoneType(str, Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"

@dataclass
class Metadata:
	zone: ZoneType = ZoneType.NORMAL
	color: str = None
	max_drones: int = 1