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
    QSpinBox,
    QPushButton,
    QGroupBox,
    QTabWidget,
    QMessageBox,
    QDialogButtonBox,
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
            "Grubość",
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
                thickness = part.get("thickness_mm", 0)
                return f"{thickness}mm" if thickness else "-"
            elif col == 5:
                return part.get("wrapping", "") or "-"

        elif role == Qt.TextAlignmentRole:
            col = index.column()
            if col in [1, 2, 4]:  # Dimensions, quantity, thickness
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
        self.headers = ["Nazwa", "SKU", "Ilość"]

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
                return accessory.get("sku", "")
            elif col == 2:
                return accessory.get("count", 1)

        elif role == Qt.TextAlignmentRole:
            col = index.column()
            if col == 2:  # Quantity
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


class PartEditDialog(QDialog):
    """Dialog for editing a cabinet part"""

    def __init__(self, part=None, parent=None):
        super().__init__(parent)
        self.part = part
        self.is_edit_mode = part is not None

        self.setWindowTitle("Edytuj część" if self.is_edit_mode else "Nowa część")
        self.resize(400, 500)

        self._setup_ui()
        self._setup_connections()

        if self.is_edit_mode:
            self._load_part_data()

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Basic information group
        basic_group = QGroupBox("Podstawowe informacje")
        basic_layout = QFormLayout(basic_group)
        basic_layout.setSpacing(12)

        # Part name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("np. bok lewy, front, półka...")
        basic_layout.addRow("Nazwa części*:", self.name_edit)

        # Dimensions
        dimensions_layout = QHBoxLayout()

        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(0, 5000)
        self.width_spinbox.setSuffix(" mm")
        self.width_spinbox.setValue(600)
        dimensions_layout.addWidget(QLabel("Szerokość:"))
        dimensions_layout.addWidget(self.width_spinbox)

        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(0, 5000)
        self.height_spinbox.setSuffix(" mm")
        self.height_spinbox.setValue(720)
        dimensions_layout.addWidget(QLabel("Wysokość:"))
        dimensions_layout.addWidget(self.height_spinbox)

        basic_layout.addRow("Wymiary:", dimensions_layout)

        # Quantity
        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setRange(1, 100)
        self.quantity_spinbox.setValue(1)
        basic_layout.addRow("Ilość:", self.quantity_spinbox)

        layout.addWidget(basic_group)

        # Material information group
        material_group = QGroupBox("Informacje o materiale")
        material_layout = QFormLayout(material_group)
        material_layout.setSpacing(12)

        # Material type
        self.material_combo = QComboBox()
        self.material_combo.addItems(["PLYTA", "HDF", "FRONT", "INNE"])
        self.material_combo.setEditable(True)
        material_layout.addRow("Materiał:", self.material_combo)

        # Thickness
        self.thickness_spinbox = QSpinBox()
        self.thickness_spinbox.setRange(0, 100)
        self.thickness_spinbox.setSuffix(" mm")
        self.thickness_spinbox.setValue(18)
        material_layout.addRow("Grubość:", self.thickness_spinbox)

        # Wrapping
        self.wrapping_edit = QLineEdit()
        self.wrapping_edit.setPlaceholderText("np. D, K, DDKK...")
        material_layout.addRow("Okleina:", self.wrapping_edit)

        layout.addWidget(material_group)

        # Comments group
        comments_group = QGroupBox("Uwagi")
        comments_layout = QVBoxLayout(comments_group)

        self.comments_edit = QTextEdit()
        self.comments_edit.setMaximumHeight(80)
        self.comments_edit.setPlaceholderText("Dodatkowe uwagi dotyczące części...")
        comments_layout.addWidget(self.comments_edit)

        layout.addWidget(comments_group)

        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _setup_connections(self):
        """Setup signal connections."""
        pass

    def _load_part_data(self):
        """Load part data into the form."""
        if not self.part:
            return

        self.name_edit.setText(self.part.get("part_name", ""))
        self.width_spinbox.setValue(self.part.get("width_mm", 0))
        self.height_spinbox.setValue(self.part.get("height_mm", 0))
        self.quantity_spinbox.setValue(self.part.get("pieces", 1))

        material = self.part.get("material", "")
        if material:
            index = self.material_combo.findText(material)
            if index >= 0:
                self.material_combo.setCurrentIndex(index)
            else:
                self.material_combo.setCurrentText(material)

        self.thickness_spinbox.setValue(self.part.get("thickness_mm", 0))
        self.wrapping_edit.setText(self.part.get("wrapping", ""))
        self.comments_edit.setPlainText(self.part.get("comments", ""))

    def accept(self):
        """Handle dialog acceptance."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Błąd", "Nazwa części jest wymagana.")
            self.name_edit.setFocus()
            return

        # Create part data
        self.part_data = {
            "part_name": name,
            "width_mm": self.width_spinbox.value(),
            "height_mm": self.height_spinbox.value(),
            "pieces": self.quantity_spinbox.value(),
            "material": self.material_combo.currentText() or None,
            "thickness_mm": self.thickness_spinbox.value() or None,
            "wrapping": self.wrapping_edit.text().strip() or None,
            "comments": self.comments_edit.toPlainText().strip() or None,
        }

        super().accept()


class AccessoryEditDialog(QDialog):
    """Dialog for editing an accessory"""

    def __init__(self, accessory=None, parent=None):
        super().__init__(parent)
        self.accessory = accessory
        self.is_edit_mode = accessory is not None

        self.setWindowTitle(
            "Edytuj akcesorium" if self.is_edit_mode else "Nowe akcesorium"
        )
        self.resize(400, 300)

        self._setup_ui()
        self._setup_connections()

        if self.is_edit_mode:
            self._load_accessory_data()

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Accessory information group
        accessory_group = QGroupBox("Informacje o akcesorium")
        accessory_layout = QFormLayout(accessory_group)
        accessory_layout.setSpacing(12)

        # Accessory name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("np. Uchwyt standardowy...")
        accessory_layout.addRow("Nazwa akcesorium*:", self.name_edit)

        # SKU
        self.sku_edit = QLineEdit()
        self.sku_edit.setPlaceholderText("np. UCH-001...")
        accessory_layout.addRow("SKU*:", self.sku_edit)

        # Quantity
        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setRange(1, 100)
        self.quantity_spinbox.setValue(1)
        accessory_layout.addRow("Ilość:", self.quantity_spinbox)

        layout.addWidget(accessory_group)

        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _setup_connections(self):
        """Setup signal connections."""
        pass

    def _load_accessory_data(self):
        """Load accessory data into the form."""
        if not self.accessory:
            return

        self.name_edit.setText(self.accessory.get("name", ""))
        self.sku_edit.setText(self.accessory.get("sku", ""))
        self.quantity_spinbox.setValue(self.accessory.get("count", 1))

    def accept(self):
        """Handle dialog acceptance."""
        name = self.name_edit.text().strip()
        sku = self.sku_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "Błąd", "Nazwa akcesorium jest wymagana.")
            self.name_edit.setFocus()
            return

        if not sku:
            QMessageBox.warning(self, "Błąd", "SKU jest wymagane.")
            self.sku_edit.setFocus()
            return

        # Create accessory data
        self.accessory_data = {
            "name": name,
            "sku": sku,
            "count": self.quantity_spinbox.value(),
        }

        super().accept()


class AddCabinetDialog(QDialog):
    """Dialog for adding new cabinets to the catalog."""

    sig_cabinet_created = Signal(object)  # Emitted when cabinet is created

    def __init__(self, catalog_service, accessory_service, parent=None):
        super().__init__(parent)
        self.catalog_service = catalog_service
        self.accessory_service = accessory_service

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
        self.parts_info_label.setStyleSheet("color: #666; font-style: italic;")
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
        self.accessories_info_label.setStyleSheet("color: #666; font-style: italic;")
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
        get_theme()

        self.setStyleSheet(f"""
            QDialog {{
                background-color: #f8f9fa;
            }}
            QGroupBox {{
                font-weight: bold;
                font-size: 10pt;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px 0 6px;
                background-color: white;
            }}
            QLineEdit, QSpinBox, QComboBox, QTextEdit {{
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
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
                background-color: #cccccc;
                color: #666666;
            }}
            QTabWidget::pane {{
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                margin-top: -1px;
            }}
            QTabWidget QTabBar::tab {{
                background-color: #f5f5f5;
                color: #333333;
                border: 1px solid #ddd;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                margin-right: 2px;
                font-size: 9pt;
            }}
            QTabWidget QTabBar::tab:selected {{
                background-color: white;
                color: #333333;
                border-bottom: 1px solid white;
            }}
            QTabWidget QTabBar::tab:hover:!selected {{
                background-color: #e8e8e8;
                color: #333333;
            }}
        """)

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

    def _add_accessory(self):
        """Add a new accessory."""
        dialog = AccessoryEditDialog(parent=self)
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
            dialog = AccessoryEditDialog(accessory, parent=self)
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
                    thickness_mm=part_data.get("thickness_mm"),
                    wrapping=part_data.get("wrapping"),
                    comments=part_data.get("comments"),
                )

            # Add accessories (create them first if they don't exist)
            for accessory_data in self.accessories:
                # Get or create accessory
                self.accessory_service.get_or_create(
                    name=accessory_data["name"], sku=accessory_data["sku"]
                )

                # Note: We can't add accessories to cabinet types directly in the current schema
                # They would need to be added when the cabinet is used in a project
                # For now, we'll just create the accessories in the catalog

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
