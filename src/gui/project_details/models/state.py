"""
Project Details State Management.

This module provides QSettings wrapper for managing persistent state
like splitter positions, column widths, view modes, etc.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from PySide6.QtCore import QSettings, QByteArray
from PySide6.QtWidgets import QSplitter, QTableView

logger = logging.getLogger(__name__)


class UiState:
    """
    UI State management wrapper around QSettings("Cabplanner","Cabplanner").

    Provides convenient methods for saving/restoring UI state like:
    - Splitter positions
    - Table column widths
    - View modes
    - Selected tabs

    All keys are stored under "project_details/*" prefix.
    """

    def __init__(self):
        """Initialize UI state management with Cabplanner settings."""
        self.settings = QSettings("Cabplanner", "Cabplanner")
        self.prefix = "project_details"

        logger.debug("Initialized UiState with Cabplanner settings")

    def _key(self, name: str) -> str:
        """Create a prefixed settings key."""
        return f"{self.prefix}/{name}"

    def save_splitter(self, key: str, splitter: QSplitter) -> None:
        """
        Save splitter state.

        Args:
            key: Settings key for this splitter
            splitter: QSplitter widget to save state from
        """
        if splitter:
            state = splitter.saveState()
            self.settings.setValue(self._key(f"splitter_{key}"), state)
            logger.debug(f"Saved splitter state: {key}")

    def restore_splitter(self, key: str, splitter: QSplitter) -> None:
        """
        Restore splitter state.

        Args:
            key: Settings key for this splitter
            splitter: QSplitter widget to restore state to
        """
        if splitter:
            state = self.settings.value(self._key(f"splitter_{key}"))
            if state:
                splitter.restoreState(state)
                logger.debug(f"Restored splitter state: {key}")

    def save_column_widths(self, key: str, table: QTableView) -> None:
        """
        Save table column widths.

        Args:
            key: Settings key for this table
            table: QTableView widget to save column widths from
        """
        if table and table.horizontalHeader():
            header_state = table.horizontalHeader().saveState()
            self.settings.setValue(self._key(f"columns_{key}"), header_state)
            logger.debug(f"Saved column widths: {key}")

    def restore_column_widths(self, key: str, table: QTableView) -> None:
        """
        Restore table column widths.

        Args:
            key: Settings key for this table
            table: QTableView widget to restore column widths to
        """
        if table and table.horizontalHeader():
            header_state = self.settings.value(self._key(f"columns_{key}"))
            if header_state:
                table.horizontalHeader().restoreState(header_state)
                logger.debug(f"Restored column widths: {key}")

    def get_view_mode(self, default: str = "cards") -> str:
        """
        Get saved view mode.

        Args:
            default: Default view mode if none saved

        Returns:
            View mode string ("cards" or "table")
        """
        return self.settings.value(self._key("view_mode"), default)

    def set_view_mode(self, mode: str) -> None:
        """
        Save view mode.

        Args:
            mode: View mode to save ("cards" or "table")
        """
        self.settings.setValue(self._key("view_mode"), mode)
        logger.debug(f"Saved view mode: {mode}")

    def get_selected_tab(self) -> int:
        """
        Get saved selected tab index.

        Returns:
            Tab index (0-based)
        """
        return self.settings.value(self._key("selected_tab"), 0)

    def set_selected_tab(self, idx: int) -> None:
        """
        Save selected tab index.

        Args:
            idx: Tab index to save (0-based)
        """
        self.settings.setValue(self._key("selected_tab"), idx)
        logger.debug(f"Saved selected tab: {idx}")


class ProjectDetailsState:
    """
    State management for project details dialog.

    Manages persistent settings like:
    - Window geometry and splitter positions
    - Table column widths and sort order
    - View mode preferences (cards vs table)
    - Filter and search settings
    """

    def __init__(self, settings_prefix: str = "project_details"):
        """
        Initialize state management.

        Args:
            settings_prefix: Prefix for settings keys
        """
        self.settings = QSettings()
        self.prefix = settings_prefix

        logger.debug(f"Initialized ProjectDetailsState with prefix: {settings_prefix}")

    def _key(self, name: str) -> str:
        """Create a prefixed settings key."""
        return f"{self.prefix}/{name}"

    # Window geometry and layout
    def save_geometry(self, geometry: QByteArray) -> None:
        """Save window geometry."""
        self.settings.setValue(self._key("geometry"), geometry)
        logger.debug("Saved window geometry")

    def restore_geometry(self) -> Optional[QByteArray]:
        """Restore window geometry."""
        return self.settings.value(self._key("geometry"))

    def save_splitter_state(self, splitter_name: str, state: QByteArray) -> None:
        """
        Save splitter state.

        Args:
            splitter_name: Name of the splitter
            state: Splitter state data
        """
        self.settings.setValue(self._key(f"splitter_{splitter_name}"), state)
        logger.debug(f"Saved splitter state: {splitter_name}")

    def restore_splitter_state(self, splitter_name: str) -> Optional[QByteArray]:
        """
        Restore splitter state.

        Args:
            splitter_name: Name of the splitter

        Returns:
            Splitter state data or None
        """
        return self.settings.value(self._key(f"splitter_{splitter_name}"))

    # Table view settings
    def save_table_header_state(self, header_state: QByteArray) -> None:
        """Save table header state (column widths, order, etc.)."""
        self.settings.setValue(self._key("table_header"), header_state)
        logger.debug("Saved table header state")

    def restore_table_header_state(self) -> Optional[QByteArray]:
        """Restore table header state."""
        return self.settings.value(self._key("table_header"))

    def save_table_sort(self, column: int, order: str) -> None:
        """
        Save table sort settings.

        Args:
            column: Sort column index
            order: Sort order ("asc" or "desc")
        """
        self.settings.setValue(self._key("table_sort_column"), column)
        self.settings.setValue(self._key("table_sort_order"), order)
        logger.debug(f"Saved table sort: column {column}, order {order}")

    def restore_table_sort(self) -> tuple[Optional[int], Optional[str]]:
        """
        Restore table sort settings.

        Returns:
            Tuple of (column, order) or (None, None)
        """
        column = self.settings.value(self._key("table_sort_column"))
        order = self.settings.value(self._key("table_sort_order"))

        if column is not None:
            try:
                column = int(column)
            except (ValueError, TypeError):
                column = None

        return column, order

    # View preferences
    def save_view_mode(self, mode: str) -> None:
        """
        Save preferred view mode.

        Args:
            mode: "cards" or "table"
        """
        self.settings.setValue(self._key("view_mode"), mode)
        logger.debug(f"Saved view mode: {mode}")

    def restore_view_mode(self, default: str = "cards") -> str:
        """
        Restore preferred view mode.

        Args:
            default: Default view mode if none saved

        Returns:
            View mode string
        """
        return self.settings.value(self._key("view_mode"), default)

    def save_sidebar_visible(self, visible: bool) -> None:
        """Save sidebar visibility state."""
        self.settings.setValue(self._key("sidebar_visible"), visible)
        logger.debug(f"Saved sidebar visibility: {visible}")

    def restore_sidebar_visible(self, default: bool = True) -> bool:
        """
        Restore sidebar visibility state.

        Args:
            default: Default visibility if none saved

        Returns:
            Visibility state
        """
        value = self.settings.value(self._key("sidebar_visible"), default)
        return bool(value) if value is not None else default

    # Filter and search settings
    def save_last_search(self, search_text: str) -> None:
        """Save last search text."""
        if search_text.strip():
            # Save to recent searches list
            recent = self.get_recent_searches()
            if search_text in recent:
                recent.remove(search_text)
            recent.insert(0, search_text)
            recent = recent[:10]  # Keep only last 10

            self.settings.setValue(self._key("recent_searches"), recent)
            logger.debug(f"Saved recent search: {search_text}")

    def get_recent_searches(self) -> list[str]:
        """Get list of recent search terms."""
        return self.settings.value(self._key("recent_searches"), []) or []

    def clear_recent_searches(self) -> None:
        """Clear recent search history."""
        self.settings.remove(self._key("recent_searches"))
        logger.debug("Cleared recent searches")

    def save_filter_settings(self, filters: Dict[str, Any]) -> None:
        """
        Save filter settings.

        Args:
            filters: Dictionary of filter settings
        """
        for filter_name, filter_value in filters.items():
            self.settings.setValue(self._key(f"filter_{filter_name}"), filter_value)

        logger.debug(f"Saved filter settings: {list(filters.keys())}")

    def restore_filter_settings(self) -> Dict[str, Any]:
        """
        Restore filter settings.

        Returns:
            Dictionary of filter settings
        """
        filters = {}

        # Common filter types
        filter_keys = ["type", "color", "handle_type", "show_custom"]

        for key in filter_keys:
            value = self.settings.value(self._key(f"filter_{key}"))
            if value is not None:
                filters[key] = value

        return filters

    # Tab and selection settings
    def save_active_tab(self, tab_index: int) -> None:
        """Save active tab index."""
        self.settings.setValue(self._key("active_tab"), tab_index)
        logger.debug(f"Saved active tab: {tab_index}")

    def restore_active_tab(self, default: int = 0) -> int:
        """
        Restore active tab index.

        Args:
            default: Default tab index

        Returns:
            Tab index
        """
        value = self.settings.value(self._key("active_tab"), default)
        try:
            return int(value) if value is not None else default
        except (ValueError, TypeError):
            return default

    def save_selected_cabinets(self, cabinet_ids: list[int]) -> None:
        """
        Save selected cabinet IDs.

        Args:
            cabinet_ids: List of selected cabinet IDs
        """
        self.settings.setValue(self._key("selected_cabinets"), cabinet_ids)
        logger.debug(f"Saved {len(cabinet_ids)} selected cabinets")

    def restore_selected_cabinets(self) -> list[int]:
        """
        Restore selected cabinet IDs.

        Returns:
            List of cabinet IDs
        """
        saved_ids = self.settings.value(self._key("selected_cabinets"), [])
        if saved_ids:
            try:
                return [int(id_) for id_ in saved_ids]
            except (ValueError, TypeError):
                pass
        return []

    # General utility methods
    def clear_all_settings(self) -> None:
        """Clear all project details settings."""
        # Get all keys with our prefix
        self.settings.beginGroup(self.prefix)
        keys = self.settings.allKeys()
        self.settings.endGroup()

        # Remove all prefixed keys
        for key in keys:
            self.settings.remove(self._key(key))

        logger.debug("Cleared all project details settings")

    def export_settings(self) -> Dict[str, Any]:
        """
        Export all settings to a dictionary.

        Returns:
            Dictionary of all settings
        """
        settings_dict = {}

        self.settings.beginGroup(self.prefix)
        keys = self.settings.allKeys()
        for key in keys:
            settings_dict[key] = self.settings.value(key)
        self.settings.endGroup()

        logger.debug(f"Exported {len(settings_dict)} settings")
        return settings_dict

    def import_settings(self, settings_dict: Dict[str, Any]) -> None:
        """
        Import settings from a dictionary.

        Args:
            settings_dict: Dictionary of settings to import
        """
        for key, value in settings_dict.items():
            self.settings.setValue(self._key(key), value)

        logger.debug(f"Imported {len(settings_dict)} settings")

    def has_saved_state(self) -> bool:
        """Check if any state has been saved."""
        self.settings.beginGroup(self.prefix)
        has_keys = len(self.settings.allKeys()) > 0
        self.settings.endGroup()

        return has_keys
