"""
Input validation helpers for cabinet editor forms.
"""

import re
from typing import Union

# Regex for hex color validation
HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")


def is_nonempty(text: str) -> bool:
    """Check if text is not empty or whitespace-only."""
    return bool(text and text.strip())


def is_hex_color(text: str) -> bool:
    """Check if text is a valid hex color."""
    return bool(HEX_RE.match(text))


def validate_dimension(value: Union[int, float]) -> bool:
    """Check if dimension value is valid (non-negative)."""
    return value >= 0


def validate_quantity(value: int) -> bool:
    """Check if quantity is valid (positive)."""
    return value > 0


def validate_sequence(value: int) -> bool:
    """Check if sequence number is valid (positive)."""
    return value > 0


def format_dimensions(width: float, height: float, depth: float) -> str:
    """Format dimensions for display."""
    if width and height and depth:
        return f"{int(width)}×{int(height)}×{int(depth)} mm"
    return "—"


def parse_tags(text: str) -> list[str]:
    """Parse comma-separated tags into a list."""
    if not text or not text.strip():
        return []
    return [tag.strip() for tag in text.split(",") if tag.strip()]


def format_tags(tags: list[str]) -> str:
    """Format tags list into comma-separated string."""
    return ", ".join(tags) if tags else ""
