class ParseError(Exception):
    def __init__(self, line: int, message: str) -> None:
        super().__init__(f"[Line {line}] {message}")
        self.line = line
