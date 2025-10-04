"""
Formula Service for calculating cabinet parts based on template names and constants.

This service implements the formula-based sizing system for custom cabinets,
calculating part dimensions from template names, user dimensions, and constants.
"""

from typing import Dict, List, Optional, Tuple
import re
from dataclasses import dataclass

from src.db_schema.orm_models import FormulaConstant


@dataclass
class PartPlan:
    """Represents a calculated part with all necessary information."""

    part_name: str
    height_mm: int
    width_mm: int
    pieces: int
    material: str
    thickness_mm: Optional[int]
    wrapping: Optional[str]
    comments: Optional[str]


class FormulaService:
    """Service for calculating cabinet parts using formulas and constants."""

    def __init__(self, session):
        self.session = session
        self._constants_cache = None

    def get_constants(self) -> Dict[str, float]:
        """Get all formula constants as a dictionary."""
        if self._constants_cache is None:
            constants = self.session.query(FormulaConstant).all()
            self._constants_cache = {c.key: float(c.value) for c in constants}
        return self._constants_cache.copy()

    def refresh_constants(self):
        """Refresh the constants cache."""
        self._constants_cache = None

    def template_exists(self, template_name: str) -> bool:
        """Check if a template exists in the database."""
        from src.db_schema.orm_models import CabinetTemplate

        template = (
            self.session.query(CabinetTemplate)
            .filter(CabinetTemplate.nazwa == template_name.strip())
            .first()
        )
        return template is not None

    def detect_category(self, template_name: str) -> str:
        """Detect cabinet category from template name."""
        name = template_name.upper().strip()

        if name.startswith("DNZ"):
            return "DNZ"  # narożne/niestandard
        elif name.startswith("D"):
            return "D"  # dolne (base)
        elif name.startswith("G"):
            return "G"  # górne (upper)
        elif name.startswith("N"):
            return "N"  # nadstawki (tops)
        else:
            return "UNKNOWN"

    def extract_width_from_name(self, template_name: str) -> Optional[int]:
        """Extract width from template name (e.g., D60 -> 600, G40S3 -> 400)."""
        # Remove spaces and letters, keep digits
        digits = re.findall(r"\d+", template_name)
        if digits:
            return int(digits[0]) * 10  # Convert to mm (60 -> 600mm)
        return None

    def fill_defaults_from_template(
        self,
        template_name: str,
        category: str,
        user_W: Optional[int],
        user_H: Optional[int],
        user_D: Optional[int],
        constants: Dict[str, float],
    ) -> Tuple[int, int, int]:
        """Fill missing dimensions with defaults based on template category."""
        C = constants

        # Extract width from template name if not provided
        if user_W is None:
            user_W = self.extract_width_from_name(template_name)
            if user_W is None:
                user_W = 600  # Default fallback

        # Set height and depth based on category
        if user_H is None:
            if category == "D":
                user_H = int(C.get("base_height", 720))
            elif category == "G":
                user_H = int(C.get("upper_height", 720))
            elif category in ["N", "DNZ"]:
                user_H = int(C.get("tall_height", 2020))
            else:
                user_H = 720

        if user_D is None:
            if category == "D":
                user_D = int(C.get("base_depth", 560))
            elif category == "G":
                user_D = int(C.get("upper_depth", 300))
            elif category in ["N", "DNZ"]:
                user_D = int(C.get("tall_depth", 560))
            else:
                user_D = 560

        return user_W, user_H, user_D

    def compute_parts(
        self,
        template_name: str,
        user_W: Optional[int] = None,
        user_H: Optional[int] = None,
        user_D: Optional[int] = None,
    ) -> List[PartPlan]:
        """Compute all parts for a cabinet based on template name and dimensions."""
        constants = self.get_constants()
        category = self.detect_category(template_name)
        W, H, D = self.fill_defaults_from_template(
            template_name, category, user_W, user_H, user_D, constants
        )

        # Common thickness values
        t = int(constants.get("plyta_thickness", 18))
        t_hdf = int(constants.get("hdf_thickness", 3))

        # Gap values
        gaps = {
            "top": int(constants.get("front_gap_top", 2)),
            "bottom": int(constants.get("front_gap_bottom", 2)),
            "side": int(constants.get("front_gap_side", 2)),
        }

        # Build part plan
        plan = []
        plan.extend(self._parts_for_sides(W, H, D, t, t_hdf, constants))
        plan.extend(self._parts_for_top_bottom(W, H, D, t, t_hdf, constants))
        plan.extend(self._parts_for_rails(W, H, D, t, constants, template_name))
        plan.extend(
            self._parts_for_shelves(W, H, D, t, t_hdf, constants, template_name)
        )
        plan.extend(self._parts_for_back(W, H, D, t_hdf, constants, template_name))
        plan.extend(self._parts_for_fronts(W, H, D, gaps, constants, template_name))
        plan.extend(self._parts_special(template_name, W, H, D, constants))

        return self._normalize_parts(plan, constants)

    def _parts_for_sides(
        self, W: int, H: int, D: int, t: int, t_hdf: int, constants: Dict[str, float]
    ) -> List[PartPlan]:
        """Calculate side parts (boki)."""
        return [
            PartPlan(
                part_name="bok lewy",
                height_mm=H,
                width_mm=D - t_hdf,  # Assuming back is inset
                pieces=1,
                material="PLYTA",
                thickness_mm=t,
                wrapping=None,
                comments=None,
            ),
            PartPlan(
                part_name="bok prawy",
                height_mm=H,
                width_mm=D - t_hdf,
                pieces=1,
                material="PLYTA",
                thickness_mm=t,
                wrapping=None,
                comments=None,
            ),
        ]

    def _parts_for_top_bottom(
        self, W: int, H: int, D: int, t: int, t_hdf: int, constants: Dict[str, float]
    ) -> List[PartPlan]:
        """Calculate top and bottom parts (wieniec dolny, wieniec górny)."""
        return [
            PartPlan(
                part_name="wieniec dolny",
                height_mm=W - 2 * t,
                width_mm=D - t_hdf,
                pieces=1,
                material="PLYTA",
                thickness_mm=t,
                wrapping=None,
                comments=None,
            ),
            PartPlan(
                part_name="wieniec górny",
                height_mm=W - 2 * t,
                width_mm=D - t_hdf,
                pieces=1,
                material="PLYTA",
                thickness_mm=t,
                wrapping=None,
                comments=None,
            ),
        ]

    def _parts_for_rails(
        self,
        W: int,
        H: int,
        D: int,
        t: int,
        constants: Dict[str, float],
        template_name: str,
    ) -> List[PartPlan]:
        """Calculate rail parts (listwy)."""
        rail_height = int(constants.get("rail_height", 100))

        return [
            PartPlan(
                part_name="listwa",
                height_mm=rail_height,
                width_mm=W - 2 * t,
                pieces=2,
                material="PLYTA",
                thickness_mm=t,
                wrapping=None,
                comments=None,
            )
        ]

    def _parts_for_shelves(
        self,
        W: int,
        H: int,
        D: int,
        t: int,
        t_hdf: int,
        constants: Dict[str, float],
        template_name: str,
    ) -> List[PartPlan]:
        """Calculate shelf parts (półki)."""
        shelf_back_clear = int(constants.get("shelf_back_clear", 10))

        # Determine number of shelves based on template
        shelf_count = self._get_shelf_count(template_name)

        parts = []
        for i in range(shelf_count):
            part_name = "półka" if shelf_count == 1 else f"półka {i + 1}"
            parts.append(
                PartPlan(
                    part_name=part_name,
                    height_mm=W - 2 * t,
                    width_mm=D - shelf_back_clear - t_hdf,
                    pieces=1,
                    material="PLYTA",
                    thickness_mm=t,
                    wrapping=None,
                    comments=None,
                )
            )

        return parts

    def _parts_for_back(
        self,
        W: int,
        H: int,
        D: int,
        t_hdf: int,
        constants: Dict[str, float],
        template_name: str,
    ) -> List[PartPlan]:
        """Calculate back parts (HDF or board backs)."""
        back_play_h = int(constants.get("back_play_h", 0))
        back_play_w = int(constants.get("back_play_w", 0))

        return [
            PartPlan(
                part_name="HDF",
                height_mm=H - back_play_h,
                width_mm=W - back_play_w,
                pieces=1,
                material="HDF",
                thickness_mm=t_hdf,
                wrapping=None,
                comments=None,
            )
        ]

    def _parts_for_fronts(
        self,
        W: int,
        H: int,
        D: int,
        gaps: Dict[str, int],
        constants: Dict[str, float],
        template_name: str,
    ) -> List[PartPlan]:
        """Calculate front parts (fronts) including drawer stacks."""
        parts = []

        # Check for drawer stack indicators (S1, S2, S3)
        if "S1" in template_name:
            parts.extend(self._calculate_drawer_stack_1(W, H, gaps, constants))
        elif "S2" in template_name:
            parts.extend(self._calculate_drawer_stack_2(W, H, gaps, constants))
        elif "S3" in template_name:
            parts.extend(self._calculate_drawer_stack_3(W, H, gaps, constants))
        else:
            # Regular door front(s)
            parts.extend(self._calculate_regular_fronts(W, H, gaps, template_name))

        return parts

    def _calculate_drawer_stack_1(
        self, W: int, H: int, gaps: Dict[str, int], constants: Dict[str, float]
    ) -> List[PartPlan]:
        """Calculate S1 drawer stack (single drawer)."""
        drawer_h = int(constants.get("s1_drawer_h", 572))

        return [
            PartPlan(
                part_name="front szuflada",
                height_mm=drawer_h,
                width_mm=W - 2 * gaps["side"],
                pieces=1,
                material="FRONT",
                thickness_mm=None,
                wrapping=None,
                comments=None,
            )
        ]

    def _calculate_drawer_stack_2(
        self, W: int, H: int, gaps: Dict[str, int], constants: Dict[str, float]
    ) -> List[PartPlan]:
        """Calculate S2 drawer stack (two drawers)."""
        top_h = int(constants.get("s2_top_h", 141))
        bottom_h = int(constants.get("s2_bottom_h", 572))
        int(constants.get("drawer_inter_gap", 2))

        return [
            PartPlan(
                part_name="front szuflada górna",
                height_mm=top_h,
                width_mm=W - 2 * gaps["side"],
                pieces=1,
                material="FRONT",
                thickness_mm=None,
                wrapping=None,
                comments=None,
            ),
            PartPlan(
                part_name="front szuflada dolna",
                height_mm=bottom_h,
                width_mm=W - 2 * gaps["side"],
                pieces=1,
                material="FRONT",
                thickness_mm=None,
                wrapping=None,
                comments=None,
            ),
        ]

    def _calculate_drawer_stack_3(
        self, W: int, H: int, gaps: Dict[str, int], constants: Dict[str, float]
    ) -> List[PartPlan]:
        """Calculate S3 drawer stack (three drawers)."""
        top_h = int(constants.get("s3_top_h", 140))
        middle_h = int(constants.get("s3_middle_h", 283))
        bottom_h = int(constants.get("s3_bottom_h", 572))

        return [
            PartPlan(
                part_name="front szuflada górna",
                height_mm=top_h,
                width_mm=W - 2 * gaps["side"],
                pieces=1,
                material="FRONT",
                thickness_mm=None,
                wrapping=None,
                comments=None,
            ),
            PartPlan(
                part_name="front szuflada środkowa",
                height_mm=middle_h,
                width_mm=W - 2 * gaps["side"],
                pieces=1,
                material="FRONT",
                thickness_mm=None,
                wrapping=None,
                comments=None,
            ),
            PartPlan(
                part_name="front szuflada dolna",
                height_mm=bottom_h,
                width_mm=W - 2 * gaps["side"],
                pieces=1,
                material="FRONT",
                thickness_mm=None,
                wrapping=None,
                comments=None,
            ),
        ]

    def _calculate_regular_fronts(
        self, W: int, H: int, gaps: Dict[str, int], template_name: str
    ) -> List[PartPlan]:
        """Calculate regular door fronts (single or double doors)."""
        # Check for double door indicators
        if "2x" in template_name or "słoje pion" in template_name:
            # Two equal doors
            door_width = (W - 3 * gaps["side"]) // 2
            return [
                PartPlan(
                    part_name="front lewy",
                    height_mm=H - gaps["top"] - gaps["bottom"],
                    width_mm=door_width,
                    pieces=1,
                    material="FRONT",
                    thickness_mm=None,
                    wrapping=None,
                    comments=None,
                ),
                PartPlan(
                    part_name="front prawy",
                    height_mm=H - gaps["top"] - gaps["bottom"],
                    width_mm=door_width,
                    pieces=1,
                    material="FRONT",
                    thickness_mm=None,
                    wrapping=None,
                    comments=None,
                ),
            ]
        else:
            # Single door
            return [
                PartPlan(
                    part_name="front",
                    height_mm=H - gaps["top"] - gaps["bottom"],
                    width_mm=W - 2 * gaps["side"],
                    pieces=1,
                    material="FRONT",
                    thickness_mm=None,
                    wrapping=None,
                    comments=None,
                )
            ]

    def _parts_special(
        self, template_name: str, W: int, H: int, D: int, constants: Dict[str, float]
    ) -> List[PartPlan]:
        """Calculate special parts (blenda, witryna, etc.)."""
        parts = []

        # Handle special cases based on template name
        if "witryna" in template_name.lower():
            parts.append(
                PartPlan(
                    part_name="ramka alu",
                    height_mm=H,
                    width_mm=W,
                    pieces=1,
                    material="ALU",
                    thickness_mm=None,
                    wrapping=None,
                    comments="ramka alu",
                )
            )

        return parts

    def _get_shelf_count(self, template_name: str) -> int:
        """Get shelf count based on template name."""
        # Default to 1 shelf, can be extended with template-specific logic
        return 1

    def _normalize_parts(
        self, parts: List[PartPlan], constants: Dict[str, float]
    ) -> List[PartPlan]:
        """Normalize parts and apply validation."""
        min_cut = int(constants.get("min_cut_mm", 10))
        normalized = []

        for part in parts:
            # Round to integers
            part.height_mm = round(part.height_mm)
            part.width_mm = round(part.width_mm)

            # Validate minimum cut sizes
            if part.height_mm < min_cut or part.width_mm < min_cut:
                raise ValueError(
                    f"Part '{part.part_name}' too small: {part.width_mm}x{part.height_mm}mm "
                    f"(minimum {min_cut}mm)"
                )

            # Ensure positive values
            if part.height_mm <= 0 or part.width_mm <= 0:
                raise ValueError(
                    f"Part '{part.part_name}' has invalid dimensions: {part.width_mm}x{part.height_mm}mm"
                )

            normalized.append(part)

        return normalized

    def validate_dimensions(
        self, W: int, H: int, D: int, constants: Dict[str, float]
    ) -> List[str]:
        """Validate cabinet dimensions and return list of errors."""
        errors = []
        min_cut = int(constants.get("min_cut_mm", 10))

        if W < min_cut:
            errors.append(f"Width too small: {W}mm (minimum {min_cut}mm)")
        if H < min_cut:
            errors.append(f"Height too small: {H}mm (minimum {min_cut}mm)")
        if D < min_cut:
            errors.append(f"Depth too small: {D}mm (minimum {min_cut}mm)")

        return errors
