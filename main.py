from pathlib import Path

from flyin import MapParser, ParseError
from flyin.router import MultiAgentRouter


def main() -> None:
    path = Path("test_map.txt")
    parser = MapParser(path)
    try:
        parser.parse()
        parser.print_connections()
    except ParseError as e:
        print(f"Error: {e}")

    router = MultiAgentRouter(
        zones=parser.zones,
        connections=parser.connections,
        start_zone=parser.start_zone,
        end_zone=parser.end_zone
    )
    zone = parser.start_zone
    print(
        "Distance from",
        zone.name,
        f"to {parser.end_zone.name} is:",
        router._distance_to_end_hub(parser.start_zone)
    )


if __name__ == "__main__":
    main()
