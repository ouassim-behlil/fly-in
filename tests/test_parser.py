from pathlib import Path
import pytest

from flyin.utils import ParseError

from flyin.model import ZoneType
from flyin.parser import MapParser


def create_and_parse(tmp_path: Path, content: str) -> MapParser:
    """Helper to write content to a temp file and parse it."""
    map_file = tmp_path / "test_map.txt"
    map_file.write_text(content, encoding="utf-8")
    parser = MapParser(map_file)
    parser.parse()
    return parser


def test_valid_map_fully_featured(tmp_path: Path) -> None:
    content = """
    nb_drones: 5
    # This is a comment
    start_hub: start_zone 0 0 [color=green max_drones=10]
    end_hub: end_zone 10 10 [color=yellow]
    hub: a 5 5 [zone=restricted color=red max_drones=2]
    hub: b 6 6 [[zone=priority]]
    connection: start_zone-a [max_link_capacity=2]
    connection: a-b
    connection: b-end_zone
    """
    parser = create_and_parse(tmp_path, content)

    assert parser.nb_drones == 5
    assert len(parser.zones) == 4
    assert len(parser.connections) == 3

    assert parser.start_zone is not None
    assert parser.end_zone is not None
    assert parser.start_zone.metadata.max_drones == parser.nb_drones
    assert parser.end_zone.metadata.max_drones == parser.nb_drones

    zone_a = parser.zones["a"]
    assert zone_a.metadata.zone_type == ZoneType.RESTRICTED
    assert zone_a.metadata.max_drones == 2
    assert zone_a.metadata.cost == 2

    zone_b = parser.zones["b"]
    assert zone_b.metadata.zone_type == ZoneType.PRIORITY
    assert zone_b.metadata.max_drones == 1
    assert zone_b.metadata.cost == 1

    assert parser.connections[0].max_link_capacity == 2
    assert parser.connections[1].max_link_capacity == 1


def test_nb_drones_must_be_first(tmp_path: Path) -> None:
    content = """
    start_hub: start_zone 0 0
    nb_drones: 5
    """
    with pytest.raises(
        ParseError, match="first directive must be 'nb_drones'"
    ):
        create_and_parse(tmp_path, content)


@pytest.mark.parametrize("invalid_drones", ["0", "-5", "five"])
def test_nb_drones_invalid_values(
    tmp_path: Path, invalid_drones: str
) -> None:
    content = f"""
    nb_drones: {invalid_drones}
    start_hub: s 0 0
    end_hub: e 1 1
    connection: s-e
    """
    match_str = "integer" if invalid_drones == "five" else "must be positive"
    with pytest.raises(ParseError, match=match_str):
        create_and_parse(tmp_path, content)


def test_missing_start_or_end_hub(tmp_path: Path) -> None:
    content = """
    nb_drones: 5
    start_hub: s 0 0
    """
    with pytest.raises(ParseError, match="Missing end_hub declaration"):
        create_and_parse(tmp_path, content)


def test_duplicate_start_hub(tmp_path: Path) -> None:
    content = """
    nb_drones: 5
    start_hub: s1 0 0
    start_hub: s2 1 1
    end_hub: e 2 2
    """
    with pytest.raises(ParseError, match="exactly one start_hub"):
        create_and_parse(tmp_path, content)


def test_duplicate_zone_name(tmp_path: Path) -> None:
    content = """
    nb_drones: 5
    start_hub: zone1 0 0
    hub: zone1 1 1
    end_hub: e 2 2
    """
    with pytest.raises(ParseError, match="already exists"):
        create_and_parse(tmp_path, content)


@pytest.mark.parametrize("invalid_name", ["bad-name", "bad name"])
def test_invalid_zone_names(tmp_path: Path, invalid_name: str) -> None:
    content = f"""
    nb_drones: 5
    start_hub: {invalid_name} 0 0
    end_hub: e 1 1
    """
    with pytest.raises(ParseError):
        create_and_parse(tmp_path, content)


def test_zone_name_with_space_fails_parameter_count(
    tmp_path: Path
) -> None:
    content = """
    nb_drones: 5
    start_hub: bad name 0 0
    """
    with pytest.raises(ParseError, match="Invalid number of zone parameters"):
        create_and_parse(tmp_path, content)


def test_invalid_zone_coordinates(tmp_path: Path) -> None:
    content = """
    nb_drones: 5
    start_hub: s A 0
    """
    with pytest.raises(ParseError, match="coordinates must be integers"):
        create_and_parse(tmp_path, content)


def test_invalid_zone_type(tmp_path: Path) -> None:
    content = """
    nb_drones: 5
    start_hub: s 0 0 [zone=alien]
    """
    with pytest.raises(ParseError, match="Invalid zone type"):
        create_and_parse(tmp_path, content)


def test_malformed_brackets(tmp_path: Path) -> None:
    content = """
    nb_drones: 5
    start_hub: s 0 0 ]color=red[
    """
    with pytest.raises(ParseError, match="Brackets not correctly closed"):
        create_and_parse(tmp_path, content)


@pytest.mark.parametrize("invalid_metadata", [
    "[zone=normal [color=red]]",
    "[zone=normal] [color=red]"
])
def test_multiple_or_malformed_nested_brackets_fail(
    tmp_path: Path, invalid_metadata: str
) -> None:
    content = f"""
    nb_drones: 5
    start_hub: s 0 0
    end_hub: e 1 1
    hub: h 2 2 {invalid_metadata}
    connection: s-h
    connection: h-e
    """
    with pytest.raises(ParseError):
        create_and_parse(tmp_path, content)


def test_negative_max_drones(tmp_path: Path) -> None:
    content = """
    nb_drones: 5
    start_hub: s 0 0
    end_hub: e 1 1
    hub: h 2 2 [max_drones=0]
    """
    with pytest.raises(ParseError, match="positive integer"):
        create_and_parse(tmp_path, content)


def test_connection_zones_do_not_exist(tmp_path: Path) -> None:
    content = """
    nb_drones: 5
    start_hub: s 0 0
    end_hub: e 1 1
    connection: s-ghost
    """
    with pytest.raises(ParseError, match="do not exist"):
        create_and_parse(tmp_path, content)


def test_duplicate_connections_reversed(tmp_path: Path) -> None:
    content = """
    nb_drones: 5
    start_hub: s 0 0
    end_hub: e 1 1
    connection: s-e
    connection: e-s
    """
    with pytest.raises(ParseError, match="Connection already exists"):
        create_and_parse(tmp_path, content)


def test_invalid_connection_metadata_key(tmp_path: Path) -> None:
    content = """
    nb_drones: 5
    start_hub: s 0 0
    end_hub: e 1 1
    connection: s-e [color=red]
    """
    with pytest.raises(ParseError, match="Invalid connection metadata"):
        create_and_parse(tmp_path, content)


def test_disconnected_graph(tmp_path: Path) -> None:
    content = """
    nb_drones: 5
    start_hub: s 0 0
    end_hub: e 1 1
    hub: isolated 2 2
    connection: s-e
    """
    with pytest.raises(ParseError, match="Disconnected map"):
        create_and_parse(tmp_path, content)
