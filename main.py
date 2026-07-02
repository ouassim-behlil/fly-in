from pathlib import Path
import time

from flyin import MapParser, ParseError
from flyin.algorithm import TimeExpandedGraph, Dinic


def main() -> None:
    path = Path("test_map.txt")
    parser = MapParser(path)
    try:
        start = time.perf_counter()
        graph = parser.parse()
        elapsed = time.perf_counter() - start
        print(f"Parsed in {elapsed:.6f}s")
        parser.print_connections()
        teg = TimeExpandedGraph(graph, 10)
        teg.build(10)
        dinic = Dinic(teg)
        print(dinic.max_flow(teg.source, teg.sink))

    except ParseError as e:
        print(f"Error: {e}")




if __name__ == "__main__":
    main()
