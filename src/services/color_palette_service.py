"""
Color palette service.

Provides persistence and lookup for cabinet colors (system + user-defined).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db_schema.orm_models import CabinetColor
from src.services.color_dictionary_snapshot import SYSTEM_COLOR_SNAPSHOT

HEX_RE = re.compile(r"^#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$")


class ColorPaletteService:
    """Business logic for the cabinet color dictionary."""

    def __init__(self, db_session: Session):
        self.db = db_session

    @staticmethod
    def _normalize_name(name: str) -> str:
        return " ".join((name or "").strip().split()).casefold()

    @staticmethod
    def _canonical_name(name: str) -> str:
        return " ".join((name or "").strip().split())

    @staticmethod
    def _normalize_hex(hex_code: str) -> str:
        value = (hex_code or "").strip().upper()
        if not HEX_RE.match(value):
            raise ValueError("Nieprawidłowy kolor HEX. Użyj formatu #RRGGBB lub #RGB.")
        if len(value) == 4:
            value = "#" + value[1] * 2 + value[2] * 2 + value[3] * 2
        return value

    @staticmethod
    def _is_hex(value: str) -> bool:
        return bool(HEX_RE.match((value or "").strip()))

    @staticmethod
    def _static_hex_lookup(color_name: str) -> Optional[str]:
        from src.gui.constants.colors import COLOR_MAP

        if color_name in COLOR_MAP:
            return COLOR_MAP[color_name]

        normalized = " ".join((color_name or "").strip().split()).casefold()
        for key, hex_code in COLOR_MAP.items():
            if key.casefold() == normalized:
                return hex_code
        return None

    def ensure_seeded(self) -> None:
        """
        Ensure system dictionary rows are present.
        Idempotent and safe to call at startup.
        """
        existing = set(
            self.db.scalars(
                select(CabinetColor.normalized_name).where(
                    CabinetColor.source == "system"
                )
            ).all()
        )
        pending = []

        for name, hex_code in SYSTEM_COLOR_SNAPSHOT:
            canonical = self._canonical_name(name)
            normalized = self._normalize_name(canonical)
            if not canonical or not normalized or normalized in existing:
                continue
            pending.append(
                CabinetColor(
                    name=canonical,
                    normalized_name=normalized,
                    hex_code=self._normalize_hex(hex_code),
                    source="system",
                    usage_count=0,
                    is_active=True,
                )
            )
            existing.add(normalized)

        if pending:
            self.db.add_all(pending)
            self.db.commit()

    def list_recent(self, limit: int = 12) -> list[str]:
        """Return recently used color names sorted by latest usage."""
        if limit <= 0:
            return []

        stmt = (
            select(CabinetColor.name)
            .where(
                CabinetColor.is_active.is_(True),
                CabinetColor.usage_count > 0,
            )
            .order_by(
                CabinetColor.last_used_at.desc(),
                CabinetColor.usage_count.desc(),
                CabinetColor.name.asc(),
            )
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def list_searchable_names(self) -> list[str]:
        """Return all active color names for completer/search."""
        stmt = (
            select(CabinetColor.name)
            .where(CabinetColor.is_active.is_(True))
            .order_by(CabinetColor.source.asc(), CabinetColor.name.asc())
        )
        return list(self.db.scalars(stmt).all())

    def resolve_hex(self, color_name: str) -> Optional[str]:
        """
        Resolve a user-visible color name to HEX.

        Returns:
            #RRGGBB for known names/valid hex input, otherwise None.
        """
        value = (color_name or "").strip()
        if not value:
            return None

        if self._is_hex(value):
            return self._normalize_hex(value)

        normalized = self._normalize_name(value)
        row = self.db.scalar(
            select(CabinetColor.hex_code).where(
                CabinetColor.normalized_name == normalized,
                CabinetColor.is_active.is_(True),
            )
        )
        if row:
            return row

        return self._static_hex_lookup(value)

    def add_user_color(self, name: str, hex_code: str) -> CabinetColor:
        """Create a user-defined color entry."""
        canonical = self._canonical_name(name)
        if not canonical:
            raise ValueError("Nazwa koloru jest wymagana.")

        normalized = self._normalize_name(canonical)
        normalized_hex = self._normalize_hex(hex_code)

        existing = self.db.scalar(
            select(CabinetColor).where(CabinetColor.normalized_name == normalized)
        )
        if existing:
            raise ValueError(f"Kolor '{existing.name}' już istnieje.")

        color = CabinetColor(
            name=canonical,
            normalized_name=normalized,
            hex_code=normalized_hex,
            source="user",
            usage_count=0,
            is_active=True,
        )
        self.db.add(color)
        self.db.commit()
        self.db.refresh(color)
        return color

    def mark_used(self, color_name: str) -> Optional[CabinetColor]:
        """Increment usage stats for a color name. Unknown names are ignored."""
        canonical = self._canonical_name(color_name)
        if not canonical:
            return None

        normalized = self._normalize_name(canonical)
        color = self.db.scalar(
            select(CabinetColor).where(
                CabinetColor.normalized_name == normalized,
                CabinetColor.is_active.is_(True),
            )
        )

        if not color:
            fallback_hex = self._static_hex_lookup(canonical)
            if not fallback_hex:
                return None
            color = CabinetColor(
                name=canonical,
                normalized_name=normalized,
                hex_code=self._normalize_hex(fallback_hex),
                source="user",
                usage_count=0,
                is_active=True,
            )
            self.db.add(color)

        color.usage_count = (color.usage_count or 0) + 1
        color.last_used_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(color)
        return color

    def sync_runtime_color_map(self) -> dict[str, str]:
        """Push DB colors to runtime GUI color map used by chips/previews."""
        from src.gui.constants.colors import register_runtime_colors

        rows = self.db.scalars(
            select(CabinetColor).where(CabinetColor.is_active.is_(True))
        ).all()
        mapping = {row.name: row.hex_code for row in rows}
        register_runtime_colors(mapping)
        return mapping
