from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Connection:
    zone1: str | None = None
    zone2: str | None = None
    max_link_capacity: int = 1
