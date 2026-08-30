from flyin.utils.colors import colorize, get_color_code, hex_to_ansi, RESET


def test_get_color_code() -> None:
    assert get_color_code("red") == "\033[31m"
    assert get_color_code("GREEN") == "\033[32m"
    assert get_color_code("orange") == "\033[38;5;214m"
    assert get_color_code(None) == ""
    assert get_color_code("unknown_color") == ""


def test_hex_to_ansi() -> None:
    assert hex_to_ansi("#FF0000") == "\033[38;2;255;0;0m"
    assert hex_to_ansi("00FF00") == "\033[38;2;0;255;0m"
    assert hex_to_ansi("invalid") == ""


def test_colorize() -> None:
    colored = colorize("start", "green")
    assert colored == f"\033[32mstart{RESET}"

    uncolored = colorize("start", None)
    assert uncolored == "start"

    unknown = colorize("start", "nonexistent")
    assert unknown == "start"
