from typing import Any, Dict, Union

Number = Union[int, float]


class FormulaEngine:
    """
    Simple engine that applies a uniform base_offset to any numeric input dimension.
    """

    def __init__(self, base_offset_mm: float):
        self.base_offset = base_offset_mm

    def compute(self, dims: Dict[str, Any]) -> Dict[str, Any]:
        """
        Given a dict of arbitrary keys to values, return a new dict where:
        - numeric values (int or float) have base_offset added
        - non-numeric values are passed through unchanged
        """
        result: Dict[str, Any] = {}
        for key, value in dims.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                result[key] = value + self.base_offset
            else:
                result[key] = value
        return result
