from pathlib import Path

from flyin import ParseError
from flyin.algorithm import Solver


def main() -> None:
    path = Path("test_map.txt")
    try:
        solver = Solver.from_map(path)
        turns, paths = solver.solve()
        print(f"Minimum turns for {path}: {turns}")
        solver.print_output(paths, turns)
    except ParseError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Error: {e}")




if __name__ == "__main__":
    main()
