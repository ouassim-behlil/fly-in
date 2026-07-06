from pathlib import Path
import time

from flyin import ParseError
from flyin.algorithm import Solver


def main() -> None:
    path = Path("test_map.txt")
    try:
        start = time.perf_counter()
        solver = Solver.from_map(path)
        turns = solver.solve()
        elapsed = time.perf_counter() - start
        print(f"Solved in {elapsed:.6f}s")
        print(f"Minimum turns for {path}: {turns}")

    except ParseError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Error: {e}")




if __name__ == "__main__":
    main()
