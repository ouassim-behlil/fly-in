from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Connection:
    zone1: str = None
    zone2: str = None
    max_link_capacity: int = 1
