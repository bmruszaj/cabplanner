"""
Constants for project details package.

This module defines UI tokens, sizes, shadows, and styling constants for consistent
theming across the project details interface. All visual tokens are centralized here
to ensure harmonization with the main window design.
"""

from __future__ import annotations

from PySide6.QtCore import QSize

# =============================================================================
# CORE UI TOKENS - SINGLE SOURCE OF TRUTH
# =============================================================================

# Icon Sizes (harmonized with main window)
ICON_SIZE = QSize(24, 24)
SMALL_ICON_SIZE = QSize(16, 16)
LARGE_ICON_SIZE = QSize(32, 32)
BANNER_ICON_SIZE = QSize(20, 20)

# Content Margins and Spacing (harmonized with main window)
CONTENT_MARGINS = (12, 12, 12, 12)  # left, top, right, bottom
LAYOUT_SPACING = 8
SECTION_SPACING = 16
WIDGET_SPACING = 4

# Card Design Tokens
CARD_MIN_W = 320
CARD_MIN_H = 180
CARD_RADIUS = 12
CARD_SHADOW_BLUR = 8
CARD_SHADOW_OFFSET = (0, 2)
CARD_SHADOW_COLOR = "rgba(0, 0, 0, 0.1)"

# Component Dimensions
HEADER_HEIGHT = 60
TOOLBAR_HEIGHT = 40
SIDEBAR_MIN_WIDTH = 250
SIDEBAR_MAX_WIDTH = 300
SIDEBAR_DEFAULT_WIDTH = 280

# Elevation and Shadow System (stylesheet-friendly)
ELEVATION_SHADOW = {
    "low": {"blur": 4, "offset": (0, 1), "color": "rgba(0, 0, 0, 0.08)"},
    "medium": {"blur": 8, "offset": (0, 2), "color": "rgba(0, 0, 0, 0.12)"},
    "high": {"blur": 16, "offset": (0, 4), "color": "rgba(0, 0, 0, 0.16)"},
}

# Border Radius System
RADIUS = {"small": 4, "medium": 8, "large": 12, "xlarge": 16}

# =============================================================================
# COLOR SYSTEM - HARMONIZED WITH MAIN WINDOW
# =============================================================================

COLORS = {
    # Primary colors
    "primary": "#0078d4",
    "accent": "#0078d4",
    # Background colors
    "background": "#ffffff",
    "surface": "#f8f9fa",
    "sidebar_background": "#f8f9fa",
    "sidebar_header": "#e9ecef",
    "card_background": "#ffffff",
    "selected": "#e3f2fd",
    "hover": "#f5f5f5",
    # Text colors
    "text_primary": "#212529",
    "text_secondary": "#6c757d",
    "text_disabled": "#adb5bd",
    "text_on_primary": "#ffffff",
    # Button colors
    "button_primary": "#0078d4",
    "button_secondary": "#f8f9fa",
    "button_hover": "#106ebe",
    "button_pressed": "#005a9e",
    "button_text": "#ffffff",
    # Border colors
    "border": "#dee2e6",
    "border_focus": "#0078d4",
    "border_hover": "#bdc4cd",
    # State colors
    "success": "#107c10",
    "warning": "#ff8c00",
    "error": "#d13438",
    "info": "#0078d4",
    "disabled": "#f1f3f4",  # Light gray for disabled elements
    # Shadow colors
    "shadow_light": "rgba(0, 0, 0, 0.05)",
    "shadow_medium": "rgba(0, 0, 0, 0.1)",
    "shadow_dark": "rgba(0, 0, 0, 0.15)",
}

# =============================================================================
# BANNER DESIGN TOKENS
# =============================================================================

BANNER_COLORS = {
    "success": {"background": "#d4edda", "border": "#c3e6cb", "text": "#155724"},
    "info": {"background": "#d1ecf1", "border": "#bee5eb", "text": "#0c5460"},
    "warning": {"background": "#fff3cd", "border": "#ffeaa7", "text": "#856404"},
    "error": {"background": "#f8d7da", "border": "#f5c6cb", "text": "#721c24"},
}

# =============================================================================
# INTERACTION STATES
# =============================================================================

# Focus and Hover States
FOCUS_RING = {"width": 2, "color": COLORS["border_focus"], "offset": 2}

HOVER_TRANSITION = {"duration": "150ms", "easing": "ease-in-out"}

# Button States
BUTTON_STATES = {
    "normal": {
        "background": COLORS["button_primary"],
        "border": COLORS["button_primary"],
        "text": COLORS["button_text"],
    },
    "hover": {
        "background": COLORS["button_hover"],
        "border": COLORS["button_hover"],
        "text": COLORS["button_text"],
    },
    "pressed": {
        "background": COLORS["button_pressed"],
        "border": COLORS["button_pressed"],
        "text": COLORS["button_text"],
    },
    "focus": {
        "background": COLORS["button_primary"],
        "border": COLORS["button_primary"],
        "text": COLORS["button_text"],
        "outline": f"2px solid {COLORS['border_focus']}",
        "outline_offset": "2px",
    },
}

# Card States
CARD_STATES = {
    "normal": {
        "background": COLORS["card_background"],
        "border": COLORS["border"],
        "shadow": ELEVATION_SHADOW["low"],
    },
    "hover": {
        "background": COLORS["card_background"],
        "border": COLORS["border_hover"],
        "shadow": ELEVATION_SHADOW["medium"],
    },
    "selected": {
        "background": COLORS["selected"],
        "border": COLORS["border_focus"],
        "shadow": ELEVATION_SHADOW["medium"],
    },
    "focus": {
        "background": COLORS["card_background"],
        "border": COLORS["border_focus"],
        "shadow": ELEVATION_SHADOW["medium"],
        "outline": f"2px solid {COLORS['border_focus']}",
        "outline_offset": "2px",
    },
}

# =============================================================================
# KEYBOARD SHORTCUTS
# =============================================================================

SHORTCUTS = {
    "search_focus": "Ctrl+F",
    "view_cards": "Ctrl+1",
    "view_table": "Ctrl+2",
    "delete": "Delete",
    "edit": "F2",
    "accept": "Return",
    "duplicate": "Ctrl+D",
    "select_all": "Ctrl+A",
    "save": "Ctrl+S",
    "export": "Ctrl+E",
    "print": "Ctrl+P",
}

# =============================================================================
# LEGACY COMPATIBILITY CONSTANTS
# =============================================================================

# Legacy card constants (updated with new tokens)
CARD_WIDTH = CARD_MIN_W
CARD_HEIGHT = CARD_MIN_H
CARD_IMAGE_WIDTH = 150
CARD_IMAGE_HEIGHT = 100
CARD_SPACING = LAYOUT_SPACING
CARD_MARGIN = CONTENT_MARGINS[0]

# Legacy padding constants (mapped to new tokens)
STANDARD_PADDING = LAYOUT_SPACING
LARGE_PADDING = SECTION_SPACING
SMALL_PADDING = WIDGET_SPACING
CONTENT_SPACING = LAYOUT_SPACING

# Legacy icon sizes (mapped to new tokens)
SMALL_ICON_SIZE_INT = 16
MEDIUM_ICON_SIZE = 24
LARGE_ICON_SIZE_INT = 32

# Legacy color constants (mapped to new color system)
PRIMARY_COLOR = COLORS["primary"]
PRIMARY_HOVER_COLOR = COLORS["button_hover"]
SUCCESS_COLOR = COLORS["success"]
WARNING_COLOR = COLORS["warning"]
ERROR_COLOR = COLORS["error"]
INFO_COLOR = COLORS["info"]

BACKGROUND_COLOR = COLORS["background"]
LIGHT_BACKGROUND_COLOR = COLORS["surface"]
CARD_BACKGROUND_COLOR = COLORS["card_background"]
SELECTED_BACKGROUND_COLOR = COLORS["selected"]
HOVER_BACKGROUND_COLOR = COLORS["hover"]

BORDER_COLOR = COLORS["border"]
SELECTED_BORDER_COLOR = COLORS["border_focus"]
FOCUS_BORDER_COLOR = COLORS["border_focus"]
SEPARATOR_COLOR = COLORS["border"]

PRIMARY_TEXT_COLOR = COLORS["text_primary"]
SECONDARY_TEXT_COLOR = COLORS["text_secondary"]
DISABLED_TEXT_COLOR = COLORS["text_disabled"]
PLACEHOLDER_TEXT_COLOR = COLORS["text_secondary"]

# Legacy banner colors (mapped to new banner system)
SUCCESS_BANNER_BG = BANNER_COLORS["success"]["background"]
SUCCESS_BANNER_BORDER = BANNER_COLORS["success"]["border"]
SUCCESS_BANNER_TEXT = BANNER_COLORS["success"]["text"]

INFO_BANNER_BG = BANNER_COLORS["info"]["background"]
INFO_BANNER_BORDER = BANNER_COLORS["info"]["border"]
INFO_BANNER_TEXT = BANNER_COLORS["info"]["text"]

WARNING_BANNER_BG = BANNER_COLORS["warning"]["background"]
WARNING_BANNER_BORDER = BANNER_COLORS["warning"]["border"]
WARNING_BANNER_TEXT = BANNER_COLORS["warning"]["text"]

ERROR_BANNER_BG = BANNER_COLORS["error"]["background"]
ERROR_BANNER_BORDER = BANNER_COLORS["error"]["border"]
ERROR_BANNER_TEXT = BANNER_COLORS["error"]["text"]

# =============================================================================
# REMAINING APPLICATION CONSTANTS
# =============================================================================

# Font Sizes (points)
TITLE_FONT_SIZE = 16
SUBTITLE_FONT_SIZE = 14
BODY_FONT_SIZE = 10
CAPTION_FONT_SIZE = 9
ICON_FONT_SIZE = 48  # For emoji icons in empty states

# Table Constants
TABLE_ROW_HEIGHT = 32
TABLE_HEADER_HEIGHT = 28
TABLE_MIN_COLUMN_WIDTH = 60
TABLE_DEFAULT_COLUMN_WIDTHS = {
    "sequence_number": 60,
    "type_name": 150,
    "body_color": 120,
    "front_color": 120,
    "handle_type": 120,
    "quantity": 80,
    "is_custom": 100,
}

# Animation and Timing
BANNER_AUTO_HIDE_DURATION = 5000  # milliseconds
ERROR_BANNER_AUTO_HIDE_DURATION = 8000  # milliseconds
AUTO_SAVE_DELAY = 1000  # milliseconds
SEARCH_DEBOUNCE_DELAY = 300  # milliseconds

# File and Export Constants
MAX_RECENT_SEARCHES = 10
DEFAULT_EXPORT_FORMAT = "pdf"
SUPPORTED_EXPORT_FORMATS = ["pdf", "excel", "html"]
TEMP_FILE_PREFIX = "cabplanner_"

# View Mode Constants
VIEW_MODE_CARDS = "cards"
VIEW_MODE_TABLE = "table"
DEFAULT_VIEW_MODE = VIEW_MODE_CARDS

# Validation Constants
MIN_CABINET_QUANTITY = 1
MAX_CABINET_QUANTITY = 999
MIN_PHONE_DIGITS = 7
MAX_SEARCH_LENGTH = 100

# CSS Class Names
CSS_HEADER_BAR = "header_bar"
CSS_TOOLBAR = "toolbar"
CSS_CABINET_CARD = "cabinet_card"
CSS_CARD_FRAME = "card_frame"
CSS_BANNER = "banner"
CSS_EMPTY_STATE = "empty_state"
CSS_SIDEBAR = "sidebar"

# Settings Keys (for QSettings)
SETTINGS_PREFIX = "project_details"
SETTING_GEOMETRY = "geometry"
SETTING_SPLITTER_STATE = "splitter_state"
SETTING_VIEW_MODE = "view_mode"
SETTING_SIDEBAR_VISIBLE = "sidebar_visible"
SETTING_TABLE_HEADER = "table_header"
SETTING_RECENT_SEARCHES = "recent_searches"
SETTING_SELECTED_CABINETS = "selected_cabinets"
SETTING_ACTIVE_TAB = "active_tab"

# Dialog Button Box
BUTTON_BOX_SPACING = 8
BUTTON_MIN_WIDTH = 80

# Status Messages
MSG_CHANGES_SAVED = "Zmiany zostały zapisane pomyślnie."
MSG_PROJECT_EXPORTED = "Projekt został wyeksportowany."
MSG_PROJECT_PRINTED = "Projekt został wysłany do drukarki."
MSG_CABINET_ADDED = "Szafka została dodana do projektu."
MSG_CABINET_DELETED = "Szafka została usunięta z projektu."
MSG_CABINET_DUPLICATED = "Szafka została zduplikowana."
MSG_NO_CABINETS = "Brak szafek w projekcie"
MSG_NO_SEARCH_RESULTS = "Brak wyników wyszukiwania"
MSG_UNSAVED_CHANGES = "Masz niezapisane zmiany. Czy chcesz je odrzucić?"

# Error Messages
ERR_SAVE_FAILED = "Błąd podczas zapisywania zmian"
ERR_EXPORT_FAILED = "Błąd podczas eksportu projektu"
ERR_PRINT_FAILED = "Błąd podczas drukowania"
ERR_LOAD_FAILED = "Błąd podczas ładowania danych"
ERR_INVALID_QUANTITY = "Nieprawidłowa ilość"
ERR_INVALID_PHONE = "Nieprawidłowy numer telefonu"
ERR_INVALID_EMAIL = "Nieprawidłowy adres email"

# Tooltips
TOOLTIP_ADD_CATALOG = "Dodaj szafkę z katalogu typów"
TOOLTIP_ADD_CUSTOM = "Dodaj niestandardową szafkę"
TOOLTIP_EXPORT = "Eksportuj projekt do pliku"
TOOLTIP_PRINT = "Drukuj szczegóły projektu"
TOOLTIP_VIEW_CARDS = "Widok kart"
TOOLTIP_VIEW_TABLE = "Widok tabeli"
TOOLTIP_EDIT_CABINET = "Edytuj szafkę"
TOOLTIP_DUPLICATE_CABINET = "Duplikuj szafkę"
TOOLTIP_DELETE_CABINET = "Usuń szafkę"

# Regular Expressions
PHONE_PATTERN = r"^[\d\s\+\-\(\)]+$"
EMAIL_PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

# Feature Flags (for future development)
FEATURE_DRAG_DROP_REORDER = True
FEATURE_BULK_EDIT = True
FEATURE_EXPORT_EXCEL = True
FEATURE_PRINT_PREVIEW = True
FEATURE_AUTO_SAVE = True

# Development/Debug Constants
DEBUG_CARD_BORDERS = False
DEBUG_LAYOUT_COLORS = False
DEBUG_LOG_ACTIONS = True

# =============================================================================
# STYLESHEET GENERATION HELPERS
# =============================================================================


def get_shadow_css(elevation: str = "medium") -> str:
    """
    Generate Qt-compatible shadow alternative styling.

    Since Qt doesn't support CSS box-shadow, this returns empty string.
    Shadow effects are achieved through borders and background gradients instead.

    Args:
        elevation: One of "low", "medium", "high" (kept for API compatibility)

    Returns:
        Empty string (Qt doesn't support box-shadow)
    """
    # Qt doesn't support box-shadow, so return empty string
    # Visual depth is achieved through borders and background colors instead
    return ""


def get_rounded_css(radius: str = "medium") -> str:
    """
    Generate CSS border-radius property for the given radius size.

    Args:
        radius: One of "small", "medium", "large", "xlarge" or custom value

    Returns:
        CSS border-radius property string
    """
    if radius in RADIUS:
        radius_value = RADIUS[radius]
    else:
        radius_value = radius
    return f"border-radius: {radius_value}px;"


def get_card_style(state: str = "normal") -> str:
    """
    Generate complete CSS for card styling based on state.

    Args:
        state: One of "normal", "hover", "selected", "focus"

    Returns:
        Complete CSS string for card styling
    """
    card_state = CARD_STATES.get(state, CARD_STATES["normal"])

    css = f"""
    background-color: {card_state["background"]};
    border: 1px solid {card_state["border"]};
    {get_rounded_css("large")}
    {get_shadow_css(card_state.get("shadow", ELEVATION_SHADOW["low"])["blur"] // 4)}
    """

    if "outline" in card_state:
        css += f"\noutline: {card_state['outline']};"
        if "outline_offset" in card_state:
            css += f"\noutline-offset: {card_state.get('outline_offset', '2px')};"

    return css.strip()


def get_button_style(state: str = "normal") -> str:
    """
    Generate complete CSS for button styling based on state.

    Args:
        state: One of "normal", "hover", "pressed", "focus"

    Returns:
        Complete CSS string for button styling
    """
    button_state = BUTTON_STATES.get(state, BUTTON_STATES["normal"])

    css = f"""
    background-color: {button_state["background"]};
    border: 1px solid {button_state["border"]};
    color: {button_state["text"]};
    {get_rounded_css("small")}
    padding: {LAYOUT_SPACING}px {SECTION_SPACING}px;
    """

    if "outline" in button_state:
        css += f"\noutline: {button_state['outline']};"
        if "outline_offset" in button_state:
            css += f"\noutline-offset: {button_state.get('outline_offset', '2px')};"

    return css.strip()


def get_banner_style(banner_type: str = "info") -> str:
    """
    Generate complete CSS for banner styling based on type.

    Args:
        banner_type: One of "success", "info", "warning", "error"

    Returns:
        Complete CSS string for banner styling
    """
    banner_colors = BANNER_COLORS.get(banner_type, BANNER_COLORS["info"])

    return f"""
    background-color: {banner_colors["background"]};
    border: 1px solid {banner_colors["border"]};
    color: {banner_colors["text"]};
    {get_rounded_css("small")}
    padding: {LAYOUT_SPACING}px {CONTENT_MARGINS[0]}px;
    margin: {WIDGET_SPACING}px 0px;
    """.strip()


# =============================================================================
# COMPLETE COMPONENT STYLESHEETS
# =============================================================================

# Header Bar Stylesheet
HEADER_STYLESHEET = f"""
QWidget#{CSS_HEADER_BAR} {{
    background-color: {COLORS["surface"]};
    border-bottom: 1px solid {COLORS["border"]};
    {get_rounded_css("small")}
    {get_shadow_css("low")}
}}
"""

# Sidebar Stylesheet
SIDEBAR_STYLESHEET = f"""
QWidget#{CSS_SIDEBAR} {{
    background-color: {COLORS["sidebar_background"]};
    border-right: 1px solid {COLORS["border"]};
    {get_rounded_css("medium")}
    {get_shadow_css("low")}
}}
"""

# Cabinet Card Stylesheet
CARD_STYLESHEET = f"""
QWidget.{CSS_CABINET_CARD} {{
    {get_card_style("normal")}
    min-width: {CARD_MIN_W}px;
    min-height: {CARD_MIN_H}px;
}}

QWidget.{CSS_CABINET_CARD}:hover {{
    {get_card_style("hover")}
}}

QWidget.{CSS_CABINET_CARD}[selected="true"] {{
    {get_card_style("selected")}
}}

QWidget.{CSS_CABINET_CARD}:focus {{
    {get_card_style("focus")}
}}
"""

# Banner Stylesheet
BANNER_STYLESHEET = f"""
QWidget.{CSS_BANNER}[bannerType="success"] {{
    {get_banner_style("success")}
}}

QWidget.{CSS_BANNER}[bannerType="info"] {{
    {get_banner_style("info")}
}}

QWidget.{CSS_BANNER}[bannerType="warning"] {{
    {get_banner_style("warning")}
}}

QWidget.{CSS_BANNER}[bannerType="error"] {{
    {get_banner_style("error")}
}}
"""

# Button Stylesheet
BUTTON_STYLESHEET = f"""
QPushButton {{
    {get_button_style("normal")}
    min-width: {BUTTON_MIN_WIDTH}px;
    font-weight: 500;
}}

QPushButton:hover {{
    {get_button_style("hover")}
}}

QPushButton:pressed {{
    {get_button_style("pressed")}
}}

QPushButton:focus {{
    {get_button_style("focus")}
}}

QPushButton:disabled {{
    background-color: {COLORS["surface"]};
    color: {COLORS["text_disabled"]};
    border: 1px solid {COLORS["border"]};
}}
"""
