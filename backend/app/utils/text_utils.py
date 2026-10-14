"""Text cleaning helpers used before chunking."""

import re

_NULL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_WS_RE = re.compile(r"[ \t]+")


def clean_text(text: str) -> str:
    """Remove control characters and collapse horizontal whitespace."""
    text = _NULL_RE.sub("", text)
    text = _WS_RE.sub(" ", text)
    return text.strip("\n")


def is_blank(line: str) -> bool:
    return not line.strip()


def is_heading(line: str) -> bool:
    return line.lstrip().startswith("#")


def is_code_boundary(line: str) -> bool:
    """True for lines that start a new logical code unit (def/class/function)."""
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith(("def ", "class ", "async def ")):
        return True
    if stripped.startswith(("function ", "export function ", "export default function ")):
        return True
    if re.match(r"^(export\s+)?(const|let|var)\s+\w+\s*=\s*(\(|async)", stripped):
        return True
    if re.match(r"^(public|private|protected|internal|static)\s+\w+.*\(", stripped):
        return True
    return False
