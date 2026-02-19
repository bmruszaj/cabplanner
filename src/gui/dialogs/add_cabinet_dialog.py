"""
Dialog for adding new cabinets to the catalog.

This dialog provides a comprehensive interface for creating new cabinet types
with parts and accessories.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QGroupBox,
    QTabWidget,
    QMessageBox,
    QTextEdit,
    QTableView,
    QHeaderView,
    QAbstractItemView,
    QWidget,
)
from PySide6.QtCore import Qt, Signal, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QFont

from src.gui.resources.resources import get_icon
from src.gui.resources.styles import get_theme, PRIMARY
from src.gui.dialogs.accessory_edit_dialog import AccessoryEditDialog
from src.gui.dialogs.part_edit_dialog import PartEditDialog


class PartsTableModel(QAbstractTableModel):
    """Model for displaying cabinet parts in a table view"""

    def __init__(self, parts, parent=None):
        super().__init__(parent)
        self.parts = parts
        self.headers = [
            "Nazwa",
            "Wymiary (mm)",
            "Ilość",
            "Materiał",
            "Okleina",
        ]

    def rowCount(self, parent=QModelIndex()):
        return len(self.parts)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            part = self.parts[index.row()]
            col = index.column()

            if col == 0:
                return part.get("part_name", "")
            elif col == 1:
                width = part.get("width_mm", 0)
                height = part.get("height_mm", 0)
                return f"{width} × {height}"
            elif col == 2:
                return part.get("pieces", 1)
            elif col == 3:
                return part.get("material", "") or "-"
            elif col == 4:
                return part.get("wrapping", "") or "-"

        elif role == Qt.TextAlignmentRole:
            col = index.column()
            if col in [1, 2]:  # Dimensions, quantity
                return Qt.AlignCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None

    def update_parts(self, parts):
        self.beginResetModel()
        self.parts = parts
        self.endResetModel()

    def get_part_at_row(self, row):
        if 0 <= row < len(self.parts):
            return self.parts[row]
        return None


class AccessoriesTableModel(QAbstractTableModel):
    """Model for displaying cabinet accessories in a table view"""

    def __init__(self, accessories, parent=None):
        super().__init__(parent)
        self.accessories = accessories
        self.headers = ["Nazwa", "Ilość"]

    def rowCount(self, parent=QModelIndex()):
        return len(self.accessories)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            accessory = self.accessories[index.row()]
            col = index.column()

            if col == 0:
                return accessory.get("name", "")
            elif col == 1:
                return accessory.get("count", 1)

        elif role == Qt.TextAlignmentRole:
            col = index.column()
            if col == 1:  # Quantity
                return Qt.AlignCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None

    def update_accessories(self, accessories):
        self.beginResetModel()
        self.accessories = accessories
        self.endResetModel()

    def get_accessory_at_row(self, row):
        if 0 <= row < len(self.accessories):
            return self.accessories[row]
        return None


class AddCabinetDialog(QDialog):
    """Dialog for adding new cabinets to the catalog."""

    sig_cabinet_created = Signal(object)  # Emitted when cabinet is created

    def __init__(
        self,
        catalog_service,
        accessory_service,
        parent=None,
        is_dark_mode: bool = False,
    ):
        super().__init__(parent)
        self.catalog_service = catalog_service
        self.accessory_service = accessory_service
        self.is_dark_mode = is_dark_mode

        self.parts = []
        self.accessories = []

        self.setWindowTitle("Dodaj nową szafkę do katalogu")
        self.resize(800, 600)

        self._setup_ui()
        self._setup_connections()
        self._apply_styles()
        self.setModal(True)

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header_label = QLabel("Dodaj nową szafkę do katalogu")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)

        # Main content area with tabs
        self.tab_widget = QTabWidget()

        # Basic info tab
        self.basic_info_tab = self._create_basic_info_tab()
        self.tab_widget.addTab(
            self.basic_info_tab, get_icon("catalog"), "Podstawowe informacje"
        )

        # Parts tab
        self.parts_tab = self._create_parts_tab()
        self.tab_widget.addTab(self.parts_tab, get_icon("parts"), "Części")

        # Accessories tab
        self.accessories_tab = self._create_accessories_tab()
        self.tab_widget.addTab(
            self.accessories_tab, get_icon("accessories"), "Akcesoria"
        )

        layout.addWidget(self.tab_widget)

        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)

        buttons_layout.addStretch()

        self.cancel_button = QPushButton("Anuluj")
        self.cancel_button.setIcon(get_icon("cancel"))
        buttons_layout.addWidget(self.cancel_button)

        self.create_button = QPushButton("Utwórz szafkę")
        self.create_button.setIcon(get_icon("add"))
        self.create_button.setDefault(True)
        buttons_layout.addWidget(self.create_button)

        layout.addLayout(buttons_layout)

    def _create_basic_info_tab(self):
        """Create the basic information tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Basic information group
        basic_group = QGroupBox("Podstawowe informacje")
        basic_layout = QFormLayout(basic_group)
        basic_layout.setSpacing(12)

        # Cabinet name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("np. Szafka podblatowa 600mm")
        basic_layout.addRow("Nazwa szafki*:", self.name_edit)

        # Kitchen type
        self.kitchen_type_combo = QComboBox()
        self.kitchen_type_combo.addItems(["LOFT", "PARIS", "WINO", "MODERN"])
        basic_layout.addRow("Typ kuchni*:", self.kitchen_type_combo)

        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setPlaceholderText("Opis szafki...")
        basic_layout.addRow("Opis:", self.description_edit)

        layout.addWidget(basic_group)
        layout.addStretch()

        return widget

    def _create_parts_tab(self):
        """Create the parts tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header_layout = QHBoxLayout()

        header_label = QLabel("Części szafki")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_layout.addWidget(header_label)

        header_layout.addStretch()

        # Buttons
        self.add_part_btn = QPushButton("Dodaj część")
        self.add_part_btn.setIcon(get_icon("add"))
        self.add_part_btn.clicked.connect(self._add_part)
        header_layout.addWidget(self.add_part_btn)

        self.edit_part_btn = QPushButton("Edytuj")
        self.edit_part_btn.setIcon(get_icon("edit"))
        self.edit_part_btn.clicked.connect(self._edit_part)
        self.edit_part_btn.setEnabled(False)
        header_layout.addWidget(self.edit_part_btn)

        self.delete_part_btn = QPushButton("Usuń")
        self.delete_part_btn.setIcon(get_icon("remove"))
        self.delete_part_btn.clicked.connect(self._delete_part)
        self.delete_part_btn.setEnabled(False)
        header_layout.addWidget(self.delete_part_btn)

        layout.addLayout(header_layout)

        # Parts table
        self.parts_table = QTableView()
        self.parts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.parts_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.parts_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Interactive
        )
        self.parts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.parts_table.setAlternatingRowColors(True)
        self.parts_table.setSortingEnabled(True)
        self.parts_table.verticalHeader().setVisible(False)
        self.parts_table.setMinimumHeight(300)

        # Set up model
        self.parts_model = PartsTableModel(self.parts)
        self.parts_table.setModel(self.parts_model)

        layout.addWidget(self.parts_table)

        # Info label
        self.parts_info_label = QLabel("Dodaj części do szafki")
        info_color = "#B0B0B0" if self.is_dark_mode else "#666666"
        self.parts_info_label.setStyleSheet(f"color: {info_color}; font-style: italic;")
        self.parts_info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.parts_info_label)

        return widget

    def _create_accessories_tab(self):
        """Create the accessories tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header_layout = QHBoxLayout()

        header_label = QLabel("Akcesoria szafki")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_layout.addWidget(header_label)

        header_layout.addStretch()

        # Buttons
        self.add_accessory_btn = QPushButton("Dodaj akcesorium")
        self.add_accessory_btn.setIcon(get_icon("add"))
        self.add_accessory_btn.clicked.connect(self._add_accessory)
        header_layout.addWidget(self.add_accessory_btn)

        self.edit_accessory_btn = QPushButton("Edytuj")
        self.edit_accessory_btn.setIcon(get_icon("edit"))
        self.edit_accessory_btn.clicked.connect(self._edit_accessory)
        self.edit_accessory_btn.setEnabled(False)
        header_layout.addWidget(self.edit_accessory_btn)

        self.delete_accessory_btn = QPushButton("Usuń")
        self.delete_accessory_btn.setIcon(get_icon("remove"))
        self.delete_accessory_btn.clicked.connect(self._delete_accessory)
        self.delete_accessory_btn.setEnabled(False)
        header_layout.addWidget(self.delete_accessory_btn)

        layout.addLayout(header_layout)

        # Accessories table
        self.accessories_table = QTableView()
        self.accessories_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.accessories_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.accessories_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Interactive
        )
        self.accessories_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )
        self.accessories_table.setAlternatingRowColors(True)
        self.accessories_table.setSortingEnabled(True)
        self.accessories_table.verticalHeader().setVisible(False)
        self.accessories_table.setMinimumHeight(300)

        # Set up model
        self.accessories_model = AccessoriesTableModel(self.accessories)
        self.accessories_table.setModel(self.accessories_model)

        layout.addWidget(self.accessories_table)

        # Info label
        self.accessories_info_label = QLabel("Dodaj akcesoria do szafki")
        info_color = "#B0B0B0" if self.is_dark_mode else "#666666"
        self.accessories_info_label.setStyleSheet(
            f"color: {info_color}; font-style: italic;"
        )
        self.accessories_info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.accessories_info_label)

        return widget

    def _setup_connections(self):
        """Setup signal connections."""
        # Connect selection models
        self.parts_table.selectionModel().selectionChanged.connect(
            self._on_parts_selection_changed
        )
        self.accessories_table.selectionModel().selectionChanged.connect(
            self._on_accessories_selection_changed
        )

        # Buttons
        self.cancel_button.clicked.connect(self.reject)
        self.create_button.clicked.connect(self._create_cabinet)

    def _apply_styles(self):
        """Apply visual styling."""
        dialog_bg = "#2A2A2A" if self.is_dark_mode else "#F8F9FA"
        panel_bg = "#333333" if self.is_dark_mode else "#FFFFFF"
        panel_border = "#4A4A4A" if self.is_dark_mode else "#E0E0E0"
        input_bg = "#333333" if self.is_dark_mode else "#FFFFFF"
        input_border = "#5A5A5A" if self.is_dark_mode else "#DDDDDD"
        text_color = "#E0E0E0" if self.is_dark_mode else "#333333"
        disabled_bg = "#555555" if self.is_dark_mode else "#CCCCCC"
        disabled_text = "#9A9A9A" if self.is_dark_mode else "#666666"
        tab_bg = "#2F2F2F" if self.is_dark_mode else "#F5F5F5"
        tab_hover = "#3A3A3A" if self.is_dark_mode else "#E8E8E8"

        self.setStyleSheet(
            get_theme(self.is_dark_mode)
            + f"""
            QDialog {{
                background-color: {dialog_bg};
            }}
            QGroupBox {{
                font-weight: bold;
                font-size: 10pt;
                border: 2px solid {panel_border};
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px 0 6px;
                background-color: {panel_bg};
                color: {text_color};
            }}
            QLineEdit, QSpinBox, QComboBox, QTextEdit {{
                padding: 6px;
                border: 1px solid {input_border};
                border-radius: 4px;
                background-color: {input_bg};
                color: {text_color};
            }}
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus {{
                border-color: {PRIMARY};
            }}
            QPushButton {{
                background-color: {PRIMARY};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 9pt;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY};
                opacity: 0.9;
            }}
            QPushButton:disabled {{
                background-color: {disabled_bg};
                color: {disabled_text};
            }}
            QTabWidget::pane {{
                border: 1px solid {panel_border};
                border-radius: 8px;
                background-color: {panel_bg};
                margin-top: -1px;
            }}
            QTabWidget QTabBar::tab {{
                background-color: {tab_bg};
                color: {text_color};
                border: 1px solid {input_border};
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                margin-right: 2px;
                font-size: 9pt;
            }}
            QTabWidget QTabBar::tab:selected {{
                background-color: {panel_bg};
                color: {text_color};
                border-bottom: 1px solid {panel_bg};
            }}
            QTabWidget QTabBar::tab:hover:!selected {{
                background-color: {tab_hover};
                color: {text_color};
            }}
        """
        )

    def _on_parts_selection_changed(self):
        """Handle parts table selection changes."""
        has_selection = len(self.parts_table.selectionModel().selectedRows()) > 0
        self.edit_part_btn.setEnabled(has_selection)
        self.delete_part_btn.setEnabled(has_selection)

    def _on_accessories_selection_changed(self):
        """Handle accessories table selection changes."""
        has_selection = len(self.accessories_table.selectionModel().selectedRows()) > 0
        self.edit_accessory_btn.setEnabled(has_selection)
        self.delete_accessory_btn.setEnabled(has_selection)

    def _add_part(self):
        """Add a new part."""
        dialog = PartEditDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.parts.append(dialog.part_data)
            self.parts_model.update_parts(self.parts)
            self._update_parts_info()

    def _edit_part(self):
        """Edit the selected part."""
        current_row = self.parts_table.currentIndex().row()
        if current_row < 0:
            return

        part = self.parts_model.get_part_at_row(current_row)
        if part:
            dialog = PartEditDialog(part, parent=self)
            if dialog.exec() == QDialog.Accepted:
                self.parts[current_row] = dialog.part_data
                self.parts_model.update_parts(self.parts)

    def _delete_part(self):
        """Delete the selected part."""
        current_row = self.parts_table.currentIndex().row()
        if current_row < 0:
            return

        part = self.parts_model.get_part_at_row(current_row)
        if part:
            reply = QMessageBox.question(
                self,
                "Potwierdź usunięcie",
                f"Czy na pewno chcesz usunąć część '{part.get('part_name', '')}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                del self.parts[current_row]
                self.parts_model.update_parts(self.parts)
                self._update_parts_info()

    def _get_existing_accessory_names(self):
        """Get list of existing accessory names for uniqueness validation."""
        return [acc.get("name", "") for acc in self.accessories if acc.get("name")]

    def _add_accessory(self):
        """Add a new accessory."""
        existing_names = self._get_existing_accessory_names()
        dialog = AccessoryEditDialog(
            existing_names=existing_names,
            accessory_service=self.accessory_service,
            parent=self,
        )
        if dialog.exec() == QDialog.Accepted:
            self.accessories.append(dialog.accessory_data)
            self.accessories_model.update_accessories(self.accessories)
            self._update_accessories_info()

    def _edit_accessory(self):
        """Edit the selected accessory."""
        current_row = self.accessories_table.currentIndex().row()
        if current_row < 0:
            return

        accessory = self.accessories_model.get_accessory_at_row(current_row)
        if accessory:
            existing_names = self._get_existing_accessory_names()
            dialog = AccessoryEditDialog(
                accessory=accessory,
                existing_names=existing_names,
                accessory_service=self.accessory_service,
                parent=self,
            )
            if dialog.exec() == QDialog.Accepted:
                self.accessories[current_row] = dialog.accessory_data
                self.accessories_model.update_accessories(self.accessories)

    def _delete_accessory(self):
        """Delete the selected accessory."""
        current_row = self.accessories_table.currentIndex().row()
        if current_row < 0:
            return

        accessory = self.accessories_model.get_accessory_at_row(current_row)
        if accessory:
            reply = QMessageBox.question(
                self,
                "Potwierdź usunięcie",
                f"Czy na pewno chcesz usunąć akcesorium '{accessory.get('name', '')}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                del self.accessories[current_row]
                self.accessories_model.update_accessories(self.accessories)
                self._update_accessories_info()

    def _update_parts_info(self):
        """Update parts info label."""
        count = len(self.parts)
        if count == 0:
            self.parts_info_label.setText("Dodaj części do szafki")
        else:
            self.parts_info_label.setText(f"Dodano {count} części")

    def _update_accessories_info(self):
        """Update accessories info label."""
        count = len(self.accessories)
        if count == 0:
            self.accessories_info_label.setText("Dodaj akcesoria do szafki")
        else:
            self.accessories_info_label.setText(f"Dodano {count} akcesoriów")

    def get_cabinet_data(self):
        """Get cabinet data for project addition."""
        # Validate basic info
        name = self.name_edit.text().strip()
        if not name:
            raise ValueError("Nazwa szafki jest wymagana.")

        kitchen_type = self.kitchen_type_combo.currentText()
        description = self.description_edit.toPlainText().strip()

        # Calculate dimensions from parts
        width = height = depth = 0
        if self.parts:
            for part in self.parts:
                width = max(width, part.get("width_mm", 0))
                height = max(height, part.get("height_mm", 0))

        # Set depth based on kitchen type
        depth = 560 if kitchen_type in ["LOFT", "PARIS", "WINO"] else 320

        # Create cabinet data for project
        cabinet_data = {
            "name": name,
            "kitchen_type": kitchen_type,
            "description": description,
            "width": width,
            "height": height,
            "depth": depth,
            "front_color": "#ffffff",  # Default colors
            "body_color": "#ffffff",
            "quantity": 1,
            "parts": self.parts.copy(),
            "accessories": self.accessories.copy(),
        }

        return cabinet_data

    def _create_cabinet(self):
        """Create the cabinet with parts and accessories."""
        # Validate basic info
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Błąd", "Nazwa szafki jest wymagana.")
            self.name_edit.setFocus()
            return

        kitchen_type = self.kitchen_type_combo.currentText()
        self.description_edit.toPlainText().strip()

        try:
            # Check if name already exists
            existing_cabinets = self.catalog_service.list_types()
            for cabinet in existing_cabinets:
                if cabinet.name.lower() == name.lower():
                    QMessageBox.warning(
                        self,
                        "Błąd",
                        f"Szafka o nazwie '{name}' już istnieje w katalogu.\n"
                        "Proszę wybrać inną nazwę.",
                    )
                    self.name_edit.setFocus()
                    return

            # Create cabinet type
            cabinet_data = {
                "name": name,
                "kitchen_type": kitchen_type,
            }

            cabinet_type = self.catalog_service.create_type(cabinet_data)

            # Add parts
            for part_data in self.parts:
                self.catalog_service.cabinet_type_service.add_part(
                    cabinet_type_id=cabinet_type.id,
                    part_name=part_data.get("part_name", ""),
                    height_mm=part_data.get("height_mm", 0),
                    width_mm=part_data.get("width_mm", 0),
                    pieces=part_data.get("pieces", 1),
                    material=part_data.get("material"),
                    wrapping=part_data.get("wrapping"),
                    comments=part_data.get("comments"),
                )

            # Add accessories to cabinet template
            for accessory_data in self.accessories:
                self.catalog_service.cabinet_type_service.add_accessory_by_name(
                    cabinet_type_id=cabinet_type.id,
                    name=accessory_data["name"],
                    count=accessory_data.get("count", 1),
                )

            QMessageBox.information(
                self,
                "Sukces",
                f"Szafka '{name}' została pomyślnie dodana do katalogu!\n\n"
                f"Dodano {len(self.parts)} części i {len(self.accessories)} akcesoriów.",
            )

            self.sig_cabinet_created.emit(cabinet_type)
            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self, "Błąd", f"Nie udało się utworzyć szafki:\n{str(e)}"
            )
