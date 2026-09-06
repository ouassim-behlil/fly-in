from __future__ import annotations

from typing import Dict

RESET = "\033[0m"
BOLD = "\033[1m"

COLOR_MAP: Dict[str, str] = {
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "purple": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "gray": "\033[90m",
    "grey": "\033[90m",
    "bright_red": "\033[91m",
    "bright_green": "\033[92m",
    "bright_yellow": "\033[93m",
    "bright_blue": "\033[94m",
    "bright_magenta": "\033[95m",
    "bright_cyan": "\033[96m",
    "bright_white": "\033[97m",
    "orange": "\033[38;5;214m",
    "pink": "\033[38;5;218m",
    "gold": "\033[38;5;220m",
    "lime": "\033[38;5;118m",
    "violet": "\033[38;5;177m",
    "brown": "\033[38;5;130m",
    "teal": "\033[38;5;30m",
    "maroon": "\033[38;2;176;48;96m",
    "darkred": "\033[38;2;178;34;34m",
    "crimson": "\033[38;2;220;20;60m",
}


def hex_to_ansi(hex_code: str) -> str:
    """Convert hex color string (#RRGGBB or RRGGBB) to ANSI 24-bit code."""
    hex_str = hex_code.lstrip("#")
    if len(hex_str) == 6:
        try:
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
            return f"\033[38;2;{r};{g};{b}m"
        except ValueError:
            pass
    return ""


def get_color_code(color: str | None) -> str:
    """Get ANSI escape code for a given color name or hex code."""
    if not color:
        return ""
    color_lower = color.lower().strip()
    if color_lower in COLOR_MAP:
        return COLOR_MAP[color_lower]
    if color_lower.startswith("#") or (
        len(color_lower) == 6
        and all(c in "0123456789abcdef" for c in color_lower)
    ):
        code = hex_to_ansi(color_lower)
        if code:
            return code
    return ""


def colorize(text: str, color: str | None, bold: bool = False) -> str:
    """Colorize text with ANSI escape codes."""
    code = get_color_code(color)
    prefix = f"{BOLD}{code}" if bold else code
    if not prefix:
        return text
    return f"{prefix}{text}{RESET}"
