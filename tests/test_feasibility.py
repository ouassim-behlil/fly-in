import pytest
from pathlib import Path

from flyin.algorithm import Solver
from flyin.utils import InfeasibleMapError


def create_solver_from_text(tmp_path: Path, content: str) -> Solver:
    map_file = tmp_path / "map.txt"
    map_file.write_text(content, encoding="utf-8")
    return Solver.from_map(map_file)


def test_feasibility_blocked_single_path(tmp_path: Path) -> None:
    content = """
    nb_drones: 4
    start_hub: start 0 0 [color=green]
    hub: bottleneck 1 0 [color=orange max_drones=2]
    hub: wide_area 2 0 [color=blue max_drones=1 zone=blocked]
    end_hub: goal 3 0 [color=red]

    connection: start-bottleneck [max_link_capacity=4]
    connection: bottleneck-wide_area [max_link_capacity=4]
    connection: wide_area-goal [max_link_capacity=4]
    """
    solver = create_solver_from_text(tmp_path, content)
    assert not solver.is_feasible()
    with pytest.raises(InfeasibleMapError, match="No feasible path exists"):
        solver.check_feasibility()
    with pytest.raises(InfeasibleMapError, match="No feasible path exists"):
        solver.solve()


def test_feasibility_blocked_with_alternative_unblocked_path(
    tmp_path: Path
) -> None:
    content = """
    nb_drones: 2
    start_hub: start 0 0
    hub: blocked_zone 1 1 [zone=blocked]
    hub: detour 1 -1
    end_hub: goal 2 0

    connection: start-blocked_zone
    connection: blocked_zone-goal
    connection: start-detour
    connection: detour-goal
    """
    solver = create_solver_from_text(tmp_path, content)
    assert solver.is_feasible()
    turns, paths = solver.solve()
    assert turns > 0
    assert len(paths) == 2


def test_feasibility_all_paths_blocked(tmp_path: Path) -> None:
    content = """
    nb_drones: 3
    start_hub: start 0 0
    hub: path1 1 1 [zone=blocked]
    hub: path2 1 -1 [zone=blocked]
    end_hub: goal 2 0

    connection: start-path1
    connection: path1-goal
    connection: start-path2
    connection: path2-goal
    """
    solver = create_solver_from_text(tmp_path, content)
    assert not solver.is_feasible()
    with pytest.raises(InfeasibleMapError):
        solver.solve()
