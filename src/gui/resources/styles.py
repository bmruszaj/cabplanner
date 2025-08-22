"""
Styling system for the Cabplanner application.
This module provides modern styling for all UI elements.
"""

# --- Shared color constants (Teal palette) ---
PRIMARY = "#0A766C"      # accent / outlines / links
PRIMARY_LIGHT = "#2DD4BF"  # subtle tints/hover
PRIMARY_DARK = "#064E46"   # solid fills with white text

HOVER_GRAY = "#E0E0E0"
CARD_HOVER = "#EEEEEE"
BG_LIGHT = "#F5F5F5"
BG_LIGHT_ALT = "#FFFFFF"
BG_DARK = "#212121"
BG_DARK_ALT = "#2C2C2C"
BORDER_LIGHT = "#E0E0E0"
BORDER_MEDIUM = "#BDBDBD"
DISABLED_BG = "#B0BEC5"
DISABLED_TEXT = "#78909C"
TEXT_LIGHT = "#333333"
TEXT_DARK = "#E0E0E0"

# --- Common styles (applied in both themes) ---
COMMON_THEME = f"""
/* Primary buttons: keep brand color on hover/press */
QPushButton:hover {{
    background-color: {PRIMARY_DARK};
}}
QPushButton:pressed {{
    background-color: {PRIMARY_DARK};
}}

/* Toolbar button hover & pressed */
QToolBar QToolButton:hover {{
    background-color: {HOVER_GRAY};
}}
QToolBar QToolButton:pressed {{
    background-color: {HOVER_GRAY};
}}

/* Project card hover */
QFrame#projectCard:hover {{
    background: {CARD_HOVER};
}}

/* Row hover in tables */
QTableView::item:hover {{
    background-color: {HOVER_GRAY};
}}
"""

# --- Light theme ---
LIGHT_THEME = (
    COMMON_THEME
    + f"""
/* Global Styles */
QWidget {{
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 10pt;
    color: {TEXT_LIGHT};
    background-color: {BG_LIGHT};
}}

/* Main Window */
QMainWindow {{
    background-color: {BG_LIGHT};
}}

/* Status Bar */
QStatusBar {{
    background-color: {HOVER_GRAY};
    color: {TEXT_LIGHT};
    border-top: 1px solid {BORDER_LIGHT};
}}

/* Menu Bar */
QMenuBar {{
    background-color: {BG_LIGHT};
    border-bottom: 1px solid {BORDER_LIGHT};
}}
QMenuBar::item {{
    padding: 8px 12px;
}}
QMenuBar::item:selected {{
    background-color: {HOVER_GRAY};
    color: {TEXT_LIGHT};
}}
QMenu {{
    background-color: {BG_LIGHT_ALT};
    border: 1px solid {BORDER_LIGHT};
}}
QMenu::item {{
    padding: 6px 24px 6px 12px;
}}
QMenu::item:selected {{
    background-color: {PRIMARY};
    color: white;
}}

/* Tool Bar */
QToolBar {{
    background-color: {BG_LIGHT_ALT};
    border-bottom: 1px solid {BORDER_LIGHT};
    spacing: 8px;
    padding: 4px;
}}
QToolBar QToolButton {{
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 6px;
}}

/* Table Views */
QTableView {{
    background-color: {BG_LIGHT_ALT};
    alternate-background-color: {BG_LIGHT};
    border: 1px solid {BORDER_LIGHT};
    gridline-color: {BORDER_LIGHT};
    selection-background-color: {PRIMARY};
    selection-color: white;
}}
QHeaderView::section {{
    background-color: {BG_LIGHT};
    padding: 6px;
    border-right: 1px solid {BORDER_LIGHT};
    border-bottom: 1px solid {BORDER_LIGHT};
    font-weight: bold;
}}

/* Buttons */
QPushButton {{
    background-color: {PRIMARY};
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    min-width: 80px;
}}
QPushButton:disabled {{
    background-color: {DISABLED_BG};
    color: {DISABLED_TEXT};
}}

/* Secondary Buttons (property: class="secondary") */
QPushButton[class="secondary"] {{
    background-color: {BG_LIGHT_ALT};
    color: {PRIMARY};
    border: 1px solid {PRIMARY};
}}
QPushButton[class="secondary"]:hover {{
    background-color: {HOVER_GRAY};
}}
QPushButton[class="secondary"]:pressed {{
    background-color: {HOVER_GRAY};
}}

/* Danger Buttons (property: class="danger") */
QPushButton[class="danger"] {{
    background-color: #F44336;
    color: white;
}}
QPushButton[class="danger"]:hover {{
    background-color: #D32F2F;
}}
QPushButton[class="danger"]:pressed {{
    background-color: #B71C1C;
}}

/* Input Fields */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background-color: {BG_LIGHT_ALT};
    border: 1px solid {BORDER_MEDIUM};
    border-radius: 4px;
    padding: 6px;
    selection-background-color: {PRIMARY};
    selection-color: white;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border: 1px solid {PRIMARY};
}}

/* Checkboxes */
QCheckBox {{
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {BORDER_MEDIUM};
    border-radius: 3px;
    background-color: {BG_LIGHT_ALT};
}}
QCheckBox::indicator:hover {{
    border-color: {PRIMARY};
}}
QCheckBox::indicator:checked {{
    background-color: {PRIMARY};
    border-color: {PRIMARY};
    image: url(:/icons/check_white.png); /* ensure this resource exists */
}}

/* Checkable GroupBox indicator */
QGroupBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {BORDER_MEDIUM};
    border-radius: 3px;
    background-color: {BG_LIGHT_ALT};
    margin-right: 6px;
}}
QGroupBox::indicator:hover {{
    border-color: {PRIMARY};
}}
QGroupBox::indicator:checked {{
    background-color: {PRIMARY};
    border-color: {PRIMARY};
    image: url(:/icons/check_white.png);
}}

/* Tabs */
QTabWidget::pane {{
    border: 1px solid {BORDER_LIGHT};
    border-top: none;
}}
QTabBar::tab {{
    background-color: {BG_LIGHT_ALT};
    border: 1px solid {BORDER_LIGHT};
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 8px 16px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: {PRIMARY};
    color: white;
}}
QTabBar::tab:!selected {{
    margin-top: 2px;
}}

/* Scrollbars */
QScrollBar:vertical {{
    border: none;
    background-color: {BG_LIGHT};
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background-color: {BORDER_MEDIUM};
    border-radius: 5px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: #9E9E9E;
}}
QScrollBar:horizontal {{
    border: none;
    background-color: {BG_LIGHT};
    height: 10px;
}}
QScrollBar::handle:horizontal {{
    background-color: {BORDER_MEDIUM};
    border-radius: 5px;
    min-width: 20px;
}}
QScrollBar::handle:horizontal:hover {{
    background-color: #9E9E9E;
}}

/* Group Box */
QGroupBox {{
    border: 1px solid {BORDER_LIGHT};
    border-radius: 4px;
    margin-top: 16px;
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 5px;
}}

/* Dialogs & MessageBoxes */
QDialog, QMessageBox {{
    background-color: {BG_LIGHT_ALT};
}}

/* Card Style for widgets */
.card {{
    background-color: {BG_LIGHT_ALT};
    border-radius: 8px;
    border: 1px solid {BORDER_LIGHT};
}}
#projectCard {{
    padding: 16px;
    margin: 8px;
}}
/* Selected state */
QFrame#projectCard[selected="true"] {{
    background-color: #EEEEEE;
    border: 2px solid {PRIMARY};
}}

/* Dashboard widget */
#dashboardWidget {{
    background-color: {BG_LIGHT_ALT};
    border-radius: 8px;
    padding: 16px;
}}

/* Minimal primary-highlight validation */
QSpinBox[error="true"], QDoubleSpinBox[error="true"] {{
    border: 2px solid {PRIMARY};
    border-radius: 4px;
}}
QGroupBox[invalid="true"] {{
    border-left: 3px solid {PRIMARY};
}}
QGroupBox[invalid="true"]::title {{
    color: {PRIMARY};
    font-weight: 600;
}}
"""
)

# --- Dark theme ---
DARK_THEME = (
    COMMON_THEME
    + f"""
/* Global Styles */
QWidget {{
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 10pt;
    color: {TEXT_DARK};
    background-color: {BG_DARK};
}}

/* Main Window */
QMainWindow {{
    background-color: {BG_DARK};
}}

/* Status Bar */
QStatusBar {{
    background-color: #1A1A1A;
    color: {TEXT_DARK};
    border-top: 1px solid #333333;
}}

/* Menu Bar */
QMenuBar {{
    background-color: {BG_DARK};
    border-bottom: 1px solid #333333;
}}
QMenuBar::item {{
    padding: 8px 12px;
    background-color: transparent;
}}
QMenuBar::item:selected {{
    background-color: #333333;
    color: {TEXT_DARK};
}}
QMenu {{
    background-color: {BG_DARK_ALT};
    border: 1px solid #333333;
}}
QMenu::item {{
    padding: 6px 24px 6px 12px;
}}
QMenu::item:selected {{
    background-color: {PRIMARY};
    color: white;
}}

/* Tool Bar */
QToolBar {{
    background-color: {BG_DARK_ALT};
    border-bottom: 1px solid #333333;
    spacing: 8px;
    padding: 4px;
}}
QToolBar QToolButton {{
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 6px;
}}

/* Table Views */
QTableView {{
    background-color: {BG_DARK_ALT};
    alternate-background-color: #333333;
    border: 1px solid #424242;
    gridline-color: #424242;
    selection-background-color: {PRIMARY};
    selection-color: white;
}}
QHeaderView::section {{
    background-color: #333333;
    padding: 6px;
    border-right: 1px solid #424242;
    border-bottom: 1px solid #424242;
    font-weight: bold;
}}

/* Buttons */
QPushButton {{
    background-color: {PRIMARY};
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    min-width: 80px;
}}
QPushButton:disabled {{
    background-color: #424242;
    color: #757575;
}}

/* Secondary Buttons (property: class="secondary") */
QPushButton[class="secondary"] {{
    background-color: #333333;
    color: {PRIMARY};
    border: 1px solid {PRIMARY};
}}
QPushButton[class="secondary"]:hover {{
    background-color: #424242;
}}
QPushButton[class="secondary"]:pressed {{
    background-color: #424242;
}}

/* Danger Buttons (property: class="danger") */
QPushButton[class="danger"] {{
    background-color: #F44336;
    color: white;
}}
QPushButton[class="danger"]:hover {{
    background-color: #D32F2F;
}}
QPushButton[class="danger"]:pressed {{
    background-color: #B71C1C;
}}

/* Input Fields */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background-color: #333333;
    border: 1px solid #424242;
    border-radius: 4px;
    padding: 6px;
    selection-background-color: {PRIMARY};
    selection-color: white;
    color: {TEXT_DARK};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border: 1px solid {PRIMARY};
}}

/* Checkboxes */
QCheckBox {{
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid #424242;
    border-radius: 3px;
    background-color: #333333;
}}
QCheckBox::indicator:hover {{
    border-color: {PRIMARY};
}}
QCheckBox::indicator:checked {{
    background-color: {PRIMARY};
    border-color: {PRIMARY};
    image: url(:/icons/check_white.png);
}}

/* Checkable GroupBox indicator */
QGroupBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid #424242;
    border-radius: 3px;
    background-color: #333333;
    margin-right: 6px;
}}
QGroupBox::indicator:hover {{
    border-color: {PRIMARY};
}}
QGroupBox::indicator:checked {{
    background-color: {PRIMARY};
    border-color: {PRIMARY};
    image: url(:/icons/check_white.png);
}}

/* Tabs */
QTabWidget::pane {{
    border: 1px solid #424242;
    border-top: none;
}}
QTabBar::tab {{
    background-color: {BG_DARK_ALT};
    border: 1px solid #424242;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 8px 16px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: {PRIMARY};
    color: white;
}}
QTabBar::tab:!selected {{
    margin-top: 2px;
}}

/* Scrollbars */
QScrollBar:vertical {{
    border: none;
    background-color: {BG_DARK};
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background-color: #424242;
    border-radius: 5px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: #616161;
}}
QScrollBar:horizontal {{
    border: none;
    background-color: {BG_DARK};
    height: 10px;
}}
QScrollBar::handle:horizontal {{
    background-color: #424242;
    border-radius: 5px;
    min-width: 20px;
}}
QScrollBar::handle:horizontal:hover {{
    background-color: #616161;
}}

/* Group Box */
QGroupBox {{
    border: 1px solid #424242;
    border-radius: 4px;
    margin-top: 16px;
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 5px;
}}

/* Dialogs & MessageBoxes */
QDialog, QMessageBox {{
    background-color: {BG_DARK_ALT};
}}

/* Card Style for widgets */
.card {{
    background-color: {BG_DARK_ALT};
    border-radius: 8px;
    border: 1px solid #424242;
}}
#projectCard {{
    padding: 16px;
    margin: 8px;
}}
QFrame#projectCard[selected="true"] {{
    background-color: #333333;
    border: 2px solid {PRIMARY};
}}
#dashboardWidget {{
    background-color: {BG_DARK_ALT};
    border-radius: 8px;
    padding: 16px;
}}

/* Minimal primary-highlight validation */
QSpinBox[error="true"], QDoubleSpinBox[error="true"] {{
    border: 2px solid {PRIMARY};
    border-radius: 4px;
}}
QGroupBox[invalid="true"] {{
    border-left: 3px solid {PRIMARY};
}}
QGroupBox[invalid="true"]::title {{
    color: {PRIMARY};
    font-weight: 600;
}}
"""
)


def get_theme(is_dark_mode: bool = False) -> str:
    """Return the appropriate theme based on the mode."""
    return DARK_THEME if is_dark_mode else LIGHT_THEME
