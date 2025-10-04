"""
Custom Cabinet Dialog for creating cabinets with formula-based part calculations.

This dialog allows users to create custom cabinets by specifying a template name
and dimensions, then automatically calculates all parts using the formula engine.
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
    """Model for displaying calculated cabinet parts in a table view"""

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
                return part.part_name
            elif col == 1:
                return f"{part.width_mm} × {part.height_mm}"
            elif col == 2:
                return part.pieces
            elif col == 3:
                return part.material or "-"
            elif col == 4:
                thickness = part.thickness_mm
                return f"{thickness}mm" if thickness else "-"
            elif col == 5:
                return part.wrapping or "-"

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


class CustomCabinetDialog(QDialog):
    """Dialog for creating custom cabinets with formula-based calculations."""

    sig_cabinet_created = Signal(object)  # Emitted when cabinet is created

    def __init__(self, formula_service, project_service, project, parent=None):
        super().__init__(parent)
        self.formula_service = formula_service
        self.project_service = project_service
        self.project = project
        self.calculated_parts = []

        self.setWindowTitle("Dodaj niestandardową szafkę")
        self.resize(900, 700)

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
        header_label = QLabel("Dodaj niestandardową szafkę")
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

        # Calculated parts tab
        self.parts_tab = self._create_parts_tab()
        self.tab_widget.addTab(self.parts_tab, get_icon("parts"), "Obliczone części")

        layout.addWidget(self.tab_widget)

        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)

        buttons_layout.addStretch()

        self.cancel_button = QPushButton("Anuluj")
        self.cancel_button.setIcon(get_icon("cancel"))
        buttons_layout.addWidget(self.cancel_button)

        self.calculate_button = QPushButton("Oblicz części")
        self.calculate_button.setIcon(get_icon("calculate"))
        buttons_layout.addWidget(self.calculate_button)

        self.create_button = QPushButton("Utwórz szafkę")
        self.create_button.setIcon(get_icon("add"))
        self.create_button.setDefault(True)
        self.create_button.setEnabled(False)
        buttons_layout.addWidget(self.create_button)

        layout.addLayout(buttons_layout)

    def _create_basic_info_tab(self):
        """Create the basic information tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Template information group
        template_group = QGroupBox("Szablon szafki")
        template_layout = QFormLayout(template_group)
        template_layout.setSpacing(16)

        # Template name
        self.template_name_edit = QLineEdit()
        self.template_name_edit.setPlaceholderText("np. D60, G40S3, DNZ110...")
        template_layout.addRow("Nazwa szablonu*:", self.template_name_edit)

        # Template category info
        self.category_label = QLabel("Kategoria: -")
        self.category_label.setStyleSheet("color: #666; font-style: italic;")
        template_layout.addRow("Kategoria:", self.category_label)

        layout.addWidget(template_group)

        # Dimensions group
        dimensions_group = QGroupBox("Wymiary (mm)")
        dimensions_layout = QFormLayout(dimensions_group)
        dimensions_layout.setSpacing(16)

        # Width
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(100, 2000)
        self.width_spinbox.setSuffix(" mm")
        self.width_spinbox.setValue(600)
        self.width_spinbox.setSpecialValueText("Auto")
        dimensions_layout.addRow("Szerokość:", self.width_spinbox)

        # Height
        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(100, 3000)
        self.height_spinbox.setSuffix(" mm")
        self.height_spinbox.setValue(720)
        self.height_spinbox.setSpecialValueText("Auto")
        dimensions_layout.addRow("Wysokość:", self.height_spinbox)

        # Depth
        self.depth_spinbox = QSpinBox()
        self.depth_spinbox.setRange(100, 1000)
        self.depth_spinbox.setSuffix(" mm")
        self.depth_spinbox.setValue(560)
        self.depth_spinbox.setSpecialValueText("Auto")
        dimensions_layout.addRow("Głębokość:", self.depth_spinbox)

        layout.addWidget(dimensions_group)

        # Kitchen type group
        kitchen_group = QGroupBox("Typ kuchni")
        kitchen_layout = QFormLayout(kitchen_group)
        kitchen_layout.setSpacing(16)

        # Kitchen type
        self.kitchen_type_combo = QComboBox()
        self.kitchen_type_combo.addItems(["LOFT", "PARIS", "WINO", "MODERN"])
        kitchen_layout.addRow("Typ kuchni:", self.kitchen_type_combo)

        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setPlaceholderText("Opis szafki...")
        kitchen_layout.addRow("Opis:", self.description_edit)

        layout.addWidget(kitchen_group)

        # Info section
        info_label = QLabel(
            "💡 Wskazówka: Wymiary można zostawić jako 'Auto' - zostaną obliczone na podstawie nazwy szablonu.\n"
            "Nazwy szablonów: D* (dolne), G* (górne), N* (nadstawki), DNZ* (narożne/niestandardowe)\n"
            "Przykłady: D60, G40S3, DNZ110"
        )
        info_label.setStyleSheet(
            "color: #666; font-size: 11px; padding: 8px; background-color: #f8f9fa; border-radius: 4px;"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        layout.addStretch()

        return widget

    def _create_parts_tab(self):
        """Create the calculated parts tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header_layout = QHBoxLayout()

        header_label = QLabel("Obliczone części szafki")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_layout.addWidget(header_label)

        header_layout.addStretch()

        # Refresh button
        self.refresh_parts_btn = QPushButton("Odśwież")
        self.refresh_parts_btn.setIcon(get_icon("refresh"))
        self.refresh_parts_btn.clicked.connect(self._calculate_parts)
        header_layout.addWidget(self.refresh_parts_btn)

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
        self.parts_table.setMinimumHeight(400)

        # Set up model
        self.parts_model = PartsTableModel(self.calculated_parts)
        self.parts_table.setModel(self.parts_model)

        layout.addWidget(self.parts_table)

        # Info label
        self.parts_info_label = QLabel(
            "Kliknij 'Oblicz części' aby wygenerować części na podstawie szablonu"
        )
        self.parts_info_label.setStyleSheet("color: #666; font-style: italic;")
        self.parts_info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.parts_info_label)

        return widget

    def _setup_connections(self):
        """Setup signal connections."""
        # Buttons
        self.cancel_button.clicked.connect(self.reject)
        self.calculate_button.clicked.connect(self._calculate_parts)
        self.create_button.clicked.connect(self._create_cabinet)

        # Auto-update category when template name changes
        self.template_name_edit.textChanged.connect(self._update_category)

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
                padding: 8px;
                min-height: 20px;
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
                padding: 8px 16px;
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

    def _update_category(self):
        """Update the category label based on template name."""
        template_name = self.template_name_edit.text().strip()
        if template_name:
            category = self.formula_service.detect_category(template_name)
            category_names = {
                "D": "Dolne (podstawowe)",
                "G": "Górne",
                "N": "Nadstawki",
                "DNZ": "Narożne/Niestandardowe",
                "UNKNOWN": "Nieznana",
            }
            category_name = category_names.get(category, "Nieznana")
            self.category_label.setText(f"Kategoria: {category_name}")
        else:
            self.category_label.setText("Kategoria: -")

    def _calculate_parts(self):
        """Calculate parts using the formula service."""
        try:
            # Get template name
            template_name = self.template_name_edit.text().strip()
            if not template_name:
                QMessageBox.warning(self, "Błąd", "Nazwa szablonu jest wymagana.")
                self.template_name_edit.setFocus()
                return

            # Check if template exists
            if not self.formula_service.template_exists(template_name):
                QMessageBox.warning(
                    self,
                    "Błąd",
                    f"Szablon '{template_name}' nie istnieje w bazie danych.\n\n"
                    f"Sprawdź pisownię lub wybierz istniejący szablon.",
                )
                self.template_name_edit.setFocus()
                return

            # Get dimensions (use None for auto-calculated values)
            width = (
                self.width_spinbox.value() if self.width_spinbox.value() > 0 else None
            )
            height = (
                self.height_spinbox.value() if self.height_spinbox.value() > 0 else None
            )
            depth = (
                self.depth_spinbox.value() if self.depth_spinbox.value() > 0 else None
            )

            # Calculate parts
            self.calculated_parts = self.formula_service.compute_parts(
                template_name, width, height, depth
            )

            # Update the table
            self.parts_model.update_parts(self.calculated_parts)
            self._update_parts_info()

            # Enable create button
            self.create_button.setEnabled(True)

            # Show success message
            QMessageBox.information(
                self,
                "Sukces",
                f"Obliczono {len(self.calculated_parts)} części dla szablonu '{template_name}'",
            )

        except ValueError as e:
            QMessageBox.warning(self, "Błąd walidacji", str(e))
        except Exception as e:
            QMessageBox.critical(
                self, "Błąd", f"Nie udało się obliczyć części:\n{str(e)}"
            )

    def _update_parts_info(self):
        """Update parts info label."""
        count = len(self.calculated_parts)
        if count == 0:
            self.parts_info_label.setText(
                "Kliknij 'Oblicz części' aby wygenerować części na podstawie szablonu"
            )
        else:
            self.parts_info_label.setText(f"Obliczono {count} części")

    def _create_cabinet(self):
        """Create the cabinet with calculated parts."""
        if not self.calculated_parts:
            QMessageBox.warning(self, "Błąd", "Najpierw oblicz części szafki.")
            return

        # Validate basic info
        template_name = self.template_name_edit.text().strip()
        if not template_name:
            QMessageBox.warning(self, "Błąd", "Nazwa szablonu jest wymagana.")
            self.template_name_edit.setFocus()
            return

        # Check if template exists
        if not self.formula_service.template_exists(template_name):
            QMessageBox.warning(
                self,
                "Błąd",
                f"Szablon '{template_name}' nie istnieje w bazie danych.\n\n"
                f"Sprawdź pisownię lub wybierz istniejący szablon.",
            )
            self.template_name_edit.setFocus()
            return

        try:
            # Get dimensions
            width = (
                self.width_spinbox.value() if self.width_spinbox.value() > 0 else None
            )
            height = (
                self.height_spinbox.value() if self.height_spinbox.value() > 0 else None
            )
            depth = (
                self.depth_spinbox.value() if self.depth_spinbox.value() > 0 else None
            )

            # Calculate final dimensions
            constants = self.formula_service.get_constants()
            category = self.formula_service.detect_category(template_name)
            W, H, D = self.formula_service.fill_defaults_from_template(
                template_name, category, width, height, depth, constants
            )

            # Prepare parts data for the snapshot
            parts_data = [
                {
                    "part_name": part.part_name,
                    "width_mm": part.width_mm,
                    "height_mm": part.height_mm,
                    "pieces": part.pieces,
                    "material": part.material,
                    "thickness_mm": part.thickness_mm,
                    "wrapping": part.wrapping,
                    "comments": part.comments,
                }
                for part in self.calculated_parts
            ]

            # Prepare calculation context
            calc_context = {
                "template_name": template_name,
                "input_dimensions": {"width": width, "height": height, "depth": depth},
                "final_dimensions": {"width": W, "height": H, "depth": D},
                "constants": constants,
                "category": category,
                "kitchen_type": self.kitchen_type_combo.currentText(),
                "description": self.description_edit.toPlainText().strip(),
                "created_via": "CustomCabinetDialog",
            }

            # Get next sequence number
            sequence_number = self.project_service.get_next_cabinet_sequence(
                self.project.id
            )

            # Create the cabinet using ProjectService
            cabinet = self.project_service.add_custom_cabinet(
                project_id=self.project.id,
                sequence_number=sequence_number,
                body_color="#ffffff",  # Default colors - can be changed later
                front_color="#ffffff",
                handle_type="Standardowy",  # Default handle
                quantity=1,
                custom_parts=parts_data,
                custom_accessories=[],  # No accessories initially
                calc_context=calc_context,
            )

            QMessageBox.information(
                self,
                "Sukces",
                f"Szafka '{template_name}' została utworzona!\n\n"
                f"Wymiary: {W}×{H}×{D}mm\n"
                f"Liczba części: {len(self.calculated_parts)}\n"
                f"Numer sekwencyjny: {sequence_number}",
            )

            # Emit signal with the created cabinet
            self.sig_cabinet_created.emit(cabinet)
            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self, "Błąd", f"Nie udało się utworzyć szafki:\n{str(e)}"
            )

    def get_cabinet_data(self):
        """Get the calculated cabinet data."""
        return getattr(self, "cabinet_data", None)
