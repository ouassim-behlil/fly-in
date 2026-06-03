from dataclasses import dataclass
from .metadata import Metadata


@dataclass
class Zone:
    name: str
    x: int
    y: int
    metadata: "Metadata"
