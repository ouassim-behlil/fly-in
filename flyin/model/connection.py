from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Connection:
    zone1: str
    zone2: str
    max_link_capacity: int = 1
