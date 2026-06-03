from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Drone:
    id: int
    current_zone: str
