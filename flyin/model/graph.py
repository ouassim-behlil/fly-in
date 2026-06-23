from dataclasses import dataclass
from typing import List

from .connection import Connection
from .drone import Drone
from .zone import Zone


@dataclass
class Graph:

	nb_drones: int
	zones: List[Zone]
	connections: List[Connection]
	start_zone: Zone
	end_zone: Zone
