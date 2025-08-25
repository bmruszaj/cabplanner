"""
Cabinet sorting domain logic.

Single source of truth for cabinet ordering rules.
"""

from typing import Iterable, List, Optional, Set
from src.db_schema.orm_models import ProjectCabinet


def sort_cabinets(cabinets: Iterable[ProjectCabinet]) -> List[ProjectCabinet]:
    """
    Sort cabinets using deterministic ordering rules.

    Rules:
    1. Cabinets with sequence_number come first, sorted numerically
    2. Cabinets without sequence_number get 999 and come last
    3. Tie-breaker is always cabinet.id for deterministic results

    Args:
        cabinets: Iterable of ProjectCabinet objects

    Returns:
        List of cabinets sorted according to business rules
    """
    return sorted(cabinets, key=lambda c: (c.sequence_number or 999, c.id))


def validate_sequence_unique(cabinets: Iterable[ProjectCabinet]) -> List[str]:
    """
    Validate that sequence numbers are unique across cabinets.

    Args:
        cabinets: Iterable of ProjectCabinet objects

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    sequence_numbers: Set[Optional[int]] = set()
    duplicates: Set[Optional[int]] = set()

    for cabinet in cabinets:
        seq = cabinet.sequence_number
        if seq is not None and seq in sequence_numbers:
            duplicates.add(seq)
        if seq is not None:
            sequence_numbers.add(seq)

    for duplicate_seq in duplicates:
        errors.append(
            f"Sekwencja {duplicate_seq} jest używana przez więcej niż jedną szafę"
        )

    return errors


def get_next_available_sequence(cabinets: Iterable[ProjectCabinet]) -> int:
    """
    Get the next available sequence number for a new cabinet.

    Args:
        cabinets: Iterable of ProjectCabinet objects

    Returns:
        Next available sequence number
    """
    used_sequences = {
        c.sequence_number for c in cabinets if c.sequence_number is not None
    }

    if not used_sequences:
        return 1

    # Find the first gap or return max + 1
    for i in range(1, max(used_sequences) + 2):
        if i not in used_sequences:
            return i

    return max(used_sequences) + 1
