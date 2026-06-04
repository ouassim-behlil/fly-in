from pathlib import Path

from flyin import MapParser, ParseError


def main() -> None:
    path = Path("test_map.txt")
    try:
        parser = MapParser(path)
        parser.parse()
        parser.print_connections()
    except ParseError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
