import argparse
from pathlib import Path

from flyin import ParseError, InfeasibleMapError
from flyin.algorithm import Solver


def main() -> None:
    # Set up argparse to handle command-line arguments
    parser = argparse.ArgumentParser(
        description="Parse and run the Fly-in drone simulation."
    )
    parser.add_argument(
        "map_file",
        nargs="?",
        default="map.txt",
        help="Path to the map file (defaults to 'test_map.txt' if omitted)"
    )

    args = parser.parse_args()
    path = Path(args.map_file)

    try:
        solver = Solver.from_map(path)
        turns, paths = solver.solve()
        solver.print_output(paths, turns)

    except ParseError as e:
        print(f"Error: {e}")
    except InfeasibleMapError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Error: {e}")
    except FileNotFoundError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()