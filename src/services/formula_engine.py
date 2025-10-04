from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict

from src.services.formula_constants_service import FormulaConstantsService


@dataclass
class CalculatedPart:
    part_name: str
    height_mm: int
    width_mm: int
    pieces: int
    material: str
    thickness_mm: int
    wrapping: str
    comments: str


class FormulaEngine:
    def __init__(self, formula_service: FormulaConstantsService):
        self.formula_service = formula_service
        self._constants_cache: Dict[str, float] = {}

    def _get_constant(self, key: str, default: float = 0.0) -> float:
        """Get a formula constant, with caching for performance."""
        if key not in self._constants_cache:
            fc = self.formula_service.get(key)
            self._constants_cache[key] = fc.value if fc else default
        return self._constants_cache[key]

    def calculate_lower_cabinet_parts(
        self, width_mm: int, height_mm: int, depth_mm: int
    ) -> List[CalculatedPart]:
        """Calculate parts for a lower cabinet based on dimensions."""
        parts = []

        # Get constants
        board_mm = self._get_constant("defaults.board_mm", 18)
        edge_mm = self._get_constant("defaults.edge_mm", 2)
        self._get_constant("defaults.edge_body_mm", 0.8)
        hdf_mm = self._get_constant("defaults.hdf_mm", 3)
        hdf_clearance = self._get_constant("clearance.hdf_mm", 5)
        front_gap = self._get_constant("lower.front_gap_mm", 7)

        # Wieniec dolny (bottom rail)
        parts.append(
            CalculatedPart(
                part_name="wieniec dolny",
                height_mm=board_mm,
                width_mm=width_mm,
                pieces=1,
                material="PLYTA",
                thickness_mm=board_mm,
                wrapping="D",
                comments="",
            )
        )

        # Boki (side panels)
        parts.append(
            CalculatedPart(
                part_name="boki",
                height_mm=height_mm - board_mm,  # Height minus bottom rail
                width_mm=depth_mm,
                pieces=2,
                material="PLYTA",
                thickness_mm=board_mm,
                wrapping="DKK",
                comments="",
            )
        )

        # Listwy (rails)
        parts.append(
            CalculatedPart(
                part_name="listwy",
                height_mm=board_mm,
                width_mm=width_mm - 2 * board_mm,  # Width minus side panels
                pieces=2,
                material="PLYTA",
                thickness_mm=board_mm,
                wrapping="D",
                comments="",
            )
        )

        # Półka (shelf) - optional, could be 0 height if no shelf
        shelf_height = 0  # No shelf by default
        if shelf_height > 0:
            parts.append(
                CalculatedPart(
                    part_name="półka",
                    height_mm=shelf_height,
                    width_mm=width_mm - 2 * board_mm,
                    pieces=1,
                    material="PLYTA",
                    thickness_mm=board_mm,
                    wrapping="K",
                    comments="",
                )
            )

        # Front (door)
        front_height = height_mm - front_gap
        front_width = width_mm - 2 * edge_mm
        parts.append(
            CalculatedPart(
                part_name="front",
                height_mm=front_height,
                width_mm=front_width,
                pieces=1,
                material="FRONT",
                thickness_mm=board_mm,
                wrapping="DDKK",
                comments="",
            )
        )

        # HDF (back panel)
        hdf_height = height_mm - board_mm - hdf_clearance
        hdf_width = width_mm - hdf_clearance
        parts.append(
            CalculatedPart(
                part_name="HDF",
                height_mm=hdf_height,
                width_mm=hdf_width,
                pieces=1,
                material="HDF",
                thickness_mm=hdf_mm,
                wrapping="",
                comments="",
            )
        )

        return parts

    def calculate_upper_cabinet_parts(
        self, width_mm: int, height_mm: int, depth_mm: int
    ) -> List[CalculatedPart]:
        """Calculate parts for an upper cabinet based on dimensions."""
        parts = []

        # Get constants
        board_mm = self._get_constant("defaults.board_mm", 18)
        edge_mm = self._get_constant("defaults.edge_mm", 2)
        edge_body_mm = self._get_constant("defaults.edge_body_mm", 0.8)
        hdf_mm = self._get_constant("defaults.hdf_mm", 3)
        hdf_clearance = self._get_constant("clearance.hdf_mm", 5)
        front_gap = self._get_constant("upper.front_gap_mm", 4)
        groove_pos = self._get_constant("upper.groove_pos_mm", 282)
        groove_depth = self._get_constant("upper.groove_depth_mm", 12)

        # Wieniec dolny i górny (top and bottom rails)
        parts.append(
            CalculatedPart(
                part_name="wieniec dolny i górny",
                height_mm=board_mm,
                width_mm=width_mm,
                pieces=2,
                material="PLYTA",
                thickness_mm=board_mm,
                wrapping="K",
                comments="",
            )
        )

        # Boki (side panels with HDF groove)
        parts.append(
            CalculatedPart(
                part_name="boki",
                height_mm=height_mm - 2 * board_mm,  # Height minus top and bottom rails
                width_mm=depth_mm,
                pieces=2,
                material="PLYTA",
                thickness_mm=board_mm,
                wrapping="DKK",
                comments=f"pcv {edge_body_mm} frez na hdf {groove_pos} od przodu gł.{groove_depth}",
            )
        )

        # Półka (shelf)
        parts.append(
            CalculatedPart(
                part_name="półka",
                height_mm=board_mm,
                width_mm=width_mm - 2 * board_mm,
                pieces=1,
                material="PLYTA",
                thickness_mm=board_mm,
                wrapping="K",
                comments="",
            )
        )

        # Front (door)
        front_height = height_mm - front_gap
        front_width = width_mm - 2 * edge_mm
        parts.append(
            CalculatedPart(
                part_name="front słoje poziomo",
                height_mm=front_height,
                width_mm=front_width,
                pieces=1,
                material="FRONT",
                thickness_mm=board_mm,
                wrapping="DDKK",
                comments="",
            )
        )

        # HDF (back panel)
        hdf_height = height_mm - 2 * board_mm - hdf_clearance
        hdf_width = width_mm - hdf_clearance
        parts.append(
            CalculatedPart(
                part_name="HDF",
                height_mm=hdf_height,
                width_mm=hdf_width,
                pieces=1,
                material="HDF",
                thickness_mm=hdf_mm,
                wrapping="",
                comments="",
            )
        )

        return parts

    def calculate_drawer_parts(
        self, width_mm: int, height_mm: int, depth_mm: int
    ) -> List[CalculatedPart]:
        """Calculate parts for a drawer based on dimensions."""
        parts = []

        # Get constants
        board_mm = self._get_constant("defaults.board_mm", 18)
        self._get_constant("defaults.edge_mm", 2)
        self._get_constant("defaults.edge_body_mm", 0.8)
        self._get_constant("defaults.hdf_mm", 3)

        # Drawer-specific constants
        bottom_width = self._get_constant("drawers.comfortbox.bottom_width_mm", 495)
        self._get_constant("drawers.comfortbox.runner_offset_mm", 75)
        back_width_offset = self._get_constant(
            "drawers.comfortbox.back_width_offset_mm", 89
        )
        back_height = self._get_constant("drawers.comfortbox.back_height_mm", 70)
        front_side_edge = self._get_constant("drawers.front_side_edge_mm", 2)

        # Front (drawer front)
        front_width = width_mm - 2 * front_side_edge
        parts.append(
            CalculatedPart(
                part_name="front",
                height_mm=height_mm,
                width_mm=front_width,
                pieces=1,
                material="FRONT",
                thickness_mm=board_mm,
                wrapping="DDKK",
                comments="",
            )
        )

        # Boki (side panels)
        parts.append(
            CalculatedPart(
                part_name="boki",
                height_mm=height_mm - board_mm,  # Height minus bottom
                width_mm=depth_mm,
                pieces=2,
                material="PLYTA",
                thickness_mm=board_mm,
                wrapping="DKK",
                comments="",
            )
        )

        # Dno (bottom)
        parts.append(
            CalculatedPart(
                part_name="dno",
                height_mm=board_mm,
                width_mm=min(bottom_width, width_mm - 2 * board_mm),
                pieces=1,
                material="PLYTA",
                thickness_mm=board_mm,
                wrapping="K",
                comments="",
            )
        )

        # Tyl (back panel)
        back_width = width_mm - back_width_offset - 2 * board_mm
        parts.append(
            CalculatedPart(
                part_name="tyl",
                height_mm=back_height,
                width_mm=back_width,
                pieces=1,
                material="PLYTA",
                thickness_mm=board_mm,
                wrapping="K",
                comments="",
            )
        )

        return parts

    def calculate_cabinet_parts(
        self, cabinet_type: str, width_mm: int, height_mm: int, depth_mm: int
    ) -> List[CalculatedPart]:
        """Main method to calculate parts based on cabinet type and dimensions."""
        if cabinet_type.lower() in ["lower", "dolna", "szafka dolna"]:
            return self.calculate_lower_cabinet_parts(width_mm, height_mm, depth_mm)
        elif cabinet_type.lower() in ["upper", "górna", "szafka górna"]:
            return self.calculate_upper_cabinet_parts(width_mm, height_mm, depth_mm)
        elif cabinet_type.lower() in ["drawer", "szuflada"]:
            return self.calculate_drawer_parts(width_mm, height_mm, depth_mm)
        else:
            raise ValueError(f"Unknown cabinet type: {cabinet_type}")

    def clear_cache(self):
        """Clear the constants cache."""
        self._constants_cache.clear()
