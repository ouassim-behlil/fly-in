from pathlib import Path

from flyin.parser.map_parser import MapParser
from flyin.utils.errors import ParseError


def main() -> None:
    path = Path("test_map.txt")
    try:
        parser = MapParser(path)
        parser.parse()
        print("Map parsed successfully.")
        parser.print_start_zone()
        parser.print_end_zone()
        parser.print_hub_zones()
    except ParseError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
