"""
Client Sidebar widget for inline editable client information.

This widget provides a compact sidebar for editing client details with immediate save functionality.
"""

from __future__ import annotations

import logging
from typing import Dict, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QGroupBox,
    QScrollArea,
    QPushButton,
    QHBoxLayout,
)

from ..constants import (
    COLORS,
    SIDEBAR_DEFAULT_WIDTH,
)

logger = logging.getLogger(__name__)


class ClientSidebar(QWidget):
    """
    Sidebar widget for client information editing.

    Features:
    - Inline editing with save/cancel buttons
    - Client contact details form
    - Data validation and state management
    - Compact, scrollable layout
    """

    # Signals
    sig_save = Signal(dict)  # Updated client data

    def __init__(self, parent=None):
        """
        Initialize the client sidebar.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setFixedWidth(SIDEBAR_DEFAULT_WIDTH)

        self._original_data = {}
        self._is_busy = False

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the sidebar UI."""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS["sidebar_background"]};
                border-left: 1px solid {COLORS["border"]};
            }}
        """)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = QLabel("Client Information")
        header.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS["sidebar_header"]};
                color: {COLORS["text_primary"]};
                font-weight: bold;
                font-size: 14px;
                padding: 12px 16px;
                border-bottom: 1px solid {COLORS["border"]};
            }}
        """)
        main_layout.addWidget(header)

        # Scroll area for form
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")

        # Form container
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(16, 16, 16, 16)
        form_layout.setSpacing(16)

        # Client details form
        self._create_client_form(form_layout)

        # Buttons
        self._create_buttons(form_layout)

        form_layout.addStretch()

        scroll_area.setWidget(form_container)
        main_layout.addWidget(scroll_area)

    def _create_client_form(self, layout: QVBoxLayout) -> None:
        """Create the client information form."""
        # Client details group
        client_group = QGroupBox("Contact Details")
        client_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {COLORS["border"]};
                border-radius: 4px;
                margin-top: 6px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
                color: {COLORS["text_primary"]};
            }}
        """)

        client_form = QFormLayout(client_group)
        client_form.setSpacing(8)

        # Client name
        self.client_name_edit = QLineEdit()
        self.client_name_edit.setPlaceholderText("Enter client name")
        self._style_line_edit(self.client_name_edit)
        client_form.addRow("Nazwa:", self.client_name_edit)

        # Client address (multi-line)
        self.client_address_edit = QTextEdit()
        self.client_address_edit.setPlaceholderText("Enter client address")
        self.client_address_edit.setMaximumHeight(80)
        self._style_text_edit(self.client_address_edit)
        client_form.addRow("Adres:", self.client_address_edit)

        # Client phone
        self.client_phone_edit = QLineEdit()
        self.client_phone_edit.setPlaceholderText("Phone number")
        self._style_line_edit(self.client_phone_edit)
        client_form.addRow("Telefon:", self.client_phone_edit)

        # Client email
        self.client_email_edit = QLineEdit()
        self.client_email_edit.setPlaceholderText("Email address")
        self._style_line_edit(self.client_email_edit)
        client_form.addRow("Email:", self.client_email_edit)

        layout.addWidget(client_group)

    def _create_buttons(self, layout: QVBoxLayout) -> None:
        """Create save/cancel buttons."""
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)

        # Save button
        self.save_btn = QPushButton("Zapisz")
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["button_primary"]};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS["button_hover"]};
            }}
            QPushButton:pressed {{
                background-color: {COLORS["button_pressed"]};
            }}
            QPushButton:disabled {{
                background-color: {COLORS["disabled"]};
                color: {COLORS["text_disabled"]};
            }}
        """)
        buttons_layout.addWidget(self.save_btn)

        # Cancel button
        self.cancel_btn = QPushButton("Anuluj")
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["button_secondary"]};
                color: {COLORS["text_primary"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS["button_hover"]};
            }}
            QPushButton:pressed {{
                background-color: {COLORS["button_pressed"]};
            }}
            QPushButton:disabled {{
                background-color: {COLORS["disabled"]};
                color: {COLORS["text_disabled"]};
            }}
        """)
        buttons_layout.addWidget(self.cancel_btn)

        layout.addLayout(buttons_layout)

    def _style_line_edit(self, edit: QLineEdit) -> None:
        """Apply consistent styling to line edits."""
        edit.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {COLORS["border"]};
                border-radius: 3px;
                padding: 6px 8px;
                font-size: 12px;
                background-color: white;
            }}
            QLineEdit:focus {{
                border-color: {COLORS["accent"]};
            }}
            QLineEdit:disabled {{
                background-color: {COLORS["disabled"]};
                color: {COLORS["text_disabled"]};
            }}
        """)

    def _style_text_edit(self, edit: QTextEdit) -> None:
        """Apply consistent styling to text edits."""
        edit.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {COLORS["border"]};
                border-radius: 3px;
                padding: 6px 8px;
                font-size: 12px;
                background-color: white;
            }}
            QTextEdit:focus {{
                border-color: {COLORS["accent"]};
            }}
            QTextEdit:disabled {{
                background-color: {COLORS["disabled"]};
                color: {COLORS["text_disabled"]};
            }}
        """)

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        self.save_btn.clicked.connect(self._on_save_clicked)
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)

        # Enable save button when data changes
        self.client_name_edit.textChanged.connect(self._on_data_changed)
        self.client_address_edit.textChanged.connect(self._on_data_changed)
        self.client_phone_edit.textChanged.connect(self._on_data_changed)
        self.client_email_edit.textChanged.connect(self._on_data_changed)

    def _on_data_changed(self) -> None:
        """Handle data changes to update button states."""
        if not self._is_busy:
            current_data = self.get_data()
            has_changes = current_data != self._original_data
            self.save_btn.setEnabled(has_changes)
            self.cancel_btn.setEnabled(has_changes)

    def _on_save_clicked(self) -> None:
        """Handle save button click."""
        if self._is_busy:
            return

        data = self.get_data()
        self._original_data = data.copy()
        self.sig_save.emit(data)

        # Disable buttons after save
        self.save_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)

        logger.debug("Client data save requested")

    def _on_cancel_clicked(self) -> None:
        """Handle cancel button click - reset to original data."""
        if self._is_busy:
            return

        self.load(self._original_data)
        logger.debug("Client data changes cancelled")

    def load(self, data: Dict[str, Any]) -> None:
        """
        Load client data into the form.

        Args:
            data: Client data dictionary
        """
        self._original_data = data.copy()

        # Load form fields
        self.client_name_edit.setText(data.get("client_name", ""))
        self.client_address_edit.setPlainText(data.get("client_address", ""))
        self.client_phone_edit.setText(data.get("client_phone", ""))
        self.client_email_edit.setText(data.get("client_email", ""))

        # Reset button states
        self.save_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)

        logger.debug("Loaded client data into form")

    def get_data(self) -> Dict[str, Any]:
        """
        Get the current form data.

        Returns:
            Dictionary containing current form data
        """
        return {
            "client_name": self.client_name_edit.text().strip(),
            "client_address": self.client_address_edit.toPlainText().strip(),
            "client_phone": self.client_phone_edit.text().strip(),
            "client_email": self.client_email_edit.text().strip(),
        }

    def set_busy(self, busy: bool) -> None:
        """
        Set the busy state (disable/enable form).

        Args:
            busy: Whether the form should be in busy state
        """
        self._is_busy = busy

        # Disable/enable all inputs
        self.client_name_edit.setEnabled(not busy)
        self.client_address_edit.setEnabled(not busy)
        self.client_phone_edit.setEnabled(not busy)
        self.client_email_edit.setEnabled(not busy)
        self.save_btn.setEnabled(not busy and self.save_btn.isEnabled())
        self.cancel_btn.setEnabled(not busy and self.cancel_btn.isEnabled())

    def set_client_info(self, client_name: str, project_info: str) -> None:
        """
        Set basic client information (backward compatibility).

        Args:
            client_name: The client name to display
            project_info: Additional project information
        """
        data = {
            "client_name": client_name or "",
            "client_address": project_info or "",
            "client_phone": "",
            "client_email": "",
        }
        self.load(data)
