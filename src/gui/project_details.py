"""
Modern project details view with improved UI/UX design.
"""

import logging
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QPushButton,
    QTableView,
    QCheckBox,
    QTextEdit,
    QDialogButtonBox,
    QMessageBox,
    QHeaderView,
    QAbstractItemView,
    QLabel,
    QFrame,
    QSplitter,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QScrollArea,
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSize

from sqlalchemy.orm import Session

from src.db_schema.orm_models import Project
from src.services.project_service import ProjectService
from src.services.report_generator import ReportGenerator
from src.gui.resources.resources import get_icon

# Configure logging
logger = logging.getLogger(__name__)


class CabinetTableModel(QAbstractTableModel):
    """Model for displaying project cabinets in a table view"""

    def __init__(self, cabinets, session=None, parent=None):
        super().__init__(parent)
        self.cabinets = cabinets
        self.session = session
        self.headers = [
            "Lp.",
            "Typ",
            "Kolor korpusu",
            "Kolor frontu",
            "Rodzaj uchwytu",
            "Ilość",
            "Niestandardowy",
        ]

    def rowCount(self, parent=QModelIndex()):
        return len(self.cabinets)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            cabinet = self.cabinets[index.row()]
            col = index.column()

            if col == 0:
                return cabinet.sequence_number
            elif col == 1:
                return (
                    cabinet.cabinet_type.nazwa
                    if cabinet.cabinet_type
                    else "Niestandardowy"
                )
            elif col == 2:
                return cabinet.body_color
            elif col == 3:
                return cabinet.front_color
            elif col == 4:
                return cabinet.handle_type
            elif col == 5:
                return cabinet.quantity
            elif col == 6:
                return "Tak" if not cabinet.type_id else "Nie"

        elif role == Qt.TextAlignmentRole:
            col = index.column()
            if col in [0, 5]:  # Sequence number and quantity
                return Qt.AlignCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        return None

    def flags(self, index):
        # Make the sequence number column editable
        if index.column() == 0:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole and index.column() == 0:
            try:
                # Convert to int and validate
                seq_number = int(value)
                if seq_number <= 0:
                    return False

                # Update the sequence number
                cabinet = self.cabinets[index.row()]
                cabinet.sequence_number = seq_number

                # Save the change to the database
                if self.session:
                    from src.services.project_service import ProjectService

                    ProjectService(self.session).update_cabinet(
                        cabinet.id, sequence_number=seq_number
                    )

                # Signal that data has changed
                self.dataChanged.emit(index, index)
                return True
            except (ValueError, TypeError):
                return False
        return False

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None

    def update_cabinets(self, cabinets):
        self.beginResetModel()
        self.cabinets = cabinets
        self.endResetModel()

    def get_cabinet_at_row(self, row):
        if 0 <= row < len(self.cabinets):
            return self.cabinets[row]
        return None


class AccessoryTableModel(QAbstractTableModel):
    """Model for displaying cabinet accessories in a table view"""

    def __init__(self, accessories=None, parent=None):
        super().__init__(parent)
        self.accessories = accessories or []
        self.headers = ["Nazwa", "SKU", "Ilość"]

    def rowCount(self, parent=QModelIndex()):
        return len(self.accessories)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            link = self.accessories[index.row()]
            col = index.column()

            if col == 0:
                return link.accessory.name
            elif col == 1:
                return link.accessory.sku
            elif col == 2:
                return link.count

        elif role == Qt.TextAlignmentRole:
            col = index.column()
            if col == 2:  # Count column
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


class ProjectDetailsView(QDialog):
    """Modern dialog for viewing and editing project details"""

    def __init__(self, db_session: Session, project: Project, parent=None):
        super().__init__(parent)
        self.session = db_session
        self.project = project
        self.project_service = ProjectService(self.session)
        self.report_generator = ReportGenerator(db_session=self.session)

        # Store the original state for comparison
        self.original_blaty = project.blaty
        self.original_cokoly = project.cokoly
        self.original_uwagi = project.uwagi
        self.original_blaty_note = project.blaty_note
        self.original_cokoly_note = project.cokoly_note
        self.original_uwagi_note = project.uwagi_note

        self.init_ui()
        self.load_project_data()
        self.load_cabinets()
        self.setup_connections()

    def init_ui(self):
        """Initialize the UI components"""
        self.setWindowTitle(f"Projekt: {self.project.name}")
        self.resize(1000, 700)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Project header
        self.create_project_header()
        main_layout.addWidget(self.header_frame)

        # Splitter for main content area
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setChildrenCollapsible(False)

        # Create tabs
        self.tabs = QTabWidget()

        # Cabinets tab
        self.cabinets_tab = QWidget()
        self.setup_cabinets_tab()
        self.tabs.addTab(self.cabinets_tab, "Szafki")

        # Accessories tab
        self.accessories_tab = QWidget()
        self.setup_accessories_tab()
        self.tabs.addTab(self.accessories_tab, "Akcesoria")

        # Notes tab (renamed from Flags tab)
        self.notes_tab = QWidget()
        self.setup_notes_tab()
        self.tabs.addTab(self.notes_tab, "Uwagi i notatki")

        # Add tabs to the main area (left side of splitter)
        main_splitter.addWidget(self.tabs)

        # Add sidebar with project summary (right side of splitter)
        self.sidebar = self.create_sidebar()
        main_splitter.addWidget(self.sidebar)

        # Set default split ratio (70/30)
        main_splitter.setSizes([700, 300])

        main_layout.addWidget(main_splitter)

        # Button box at the bottom
        self.create_button_box()
        main_layout.addWidget(self.button_box)

    def create_project_header(self):
        """Create the project header with basic information"""
        self.header_frame = QFrame()
        self.header_frame.setObjectName("projectHeader")
        self.header_frame.setProperty("class", "card")

        header_layout = QHBoxLayout(self.header_frame)

        # Project title and info
        info_layout = QVBoxLayout()

        title_label = QLabel(f"<h2>{self.project.name}</h2>")
        info_layout.addWidget(title_label)

        details_layout = QHBoxLayout()
        details_layout.setSpacing(20)

        # Order number
        order_label = QLabel(f"<b>Numer zamówienia:</b> {self.project.order_number}")
        details_layout.addWidget(order_label)

        # Kitchen type
        kitchen_label = QLabel(f"<b>Typ kuchni:</b> {self.project.kitchen_type}")
        details_layout.addWidget(kitchen_label)

        # Created date
        created_label = QLabel(
            f"<b>Data utworzenia:</b> {self.project.created_at.strftime('%Y-%m-%d')}"
        )
        details_layout.addWidget(created_label)

        info_layout.addLayout(details_layout)
        header_layout.addLayout(info_layout)

        # Actions
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)

        self.export_btn = QPushButton()
        self.export_btn.setIcon(get_icon("export"))
        self.export_btn.setToolTip("Eksportuj do Word")
        self.export_btn.setIconSize(QSize(24, 24))
        self.export_btn.clicked.connect(self.export_to_word)
        actions_layout.addWidget(self.export_btn)

        self.print_btn = QPushButton()
        self.print_btn.setIcon(get_icon("print"))
        self.print_btn.setToolTip("Drukuj")
        self.print_btn.setIconSize(QSize(24, 24))
        self.print_btn.clicked.connect(self.print_document)
        actions_layout.addWidget(self.print_btn)

        header_layout.addLayout(actions_layout)

    def setup_cabinets_tab(self):
        """Setup the cabinets tab UI"""
        layout = QVBoxLayout(self.cabinets_tab)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(12)

        # Toolbar with cabinet actions
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 0)

        # Add cabinet button
        self.add_cabinet_btn = QPushButton("Dodaj z listy")
        self.add_cabinet_btn.setIcon(get_icon("catalog"))
        self.add_cabinet_btn.clicked.connect(self.show_add_cabinet_dialog)
        toolbar_layout.addWidget(self.add_cabinet_btn)

        # Add ad-hoc cabinet button
        self.add_adhoc_btn = QPushButton("Dodaj niestandardową")
        self.add_adhoc_btn.setIcon(get_icon("add"))
        self.add_adhoc_btn.clicked.connect(self.show_adhoc_cabinet_dialog)
        toolbar_layout.addWidget(self.add_adhoc_btn)

        toolbar_layout.addStretch()

        # Edit cabinet button
        self.edit_cabinet_btn = QPushButton("Edytuj")
        self.edit_cabinet_btn.setIcon(get_icon("edit"))
        self.edit_cabinet_btn.setProperty("class", "secondary")
        self.edit_cabinet_btn.clicked.connect(self.edit_selected_cabinet)
        toolbar_layout.addWidget(self.edit_cabinet_btn)

        # Delete cabinet button
        self.delete_cabinet_btn = QPushButton("Usuń")
        self.delete_cabinet_btn.setIcon(get_icon("remove"))
        self.delete_cabinet_btn.setProperty("class", "danger")
        self.delete_cabinet_btn.clicked.connect(self.delete_selected_cabinet)
        toolbar_layout.addWidget(self.delete_cabinet_btn)

        layout.addLayout(toolbar_layout)

        # Cabinets table view
        self.cabinets_table = QTableView()
        self.cabinets_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cabinets_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.cabinets_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Interactive
        )
        self.cabinets_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )
        self.cabinets_table.setAlternatingRowColors(True)
        self.cabinets_table.setSortingEnabled(True)
        self.cabinets_table.verticalHeader().setVisible(False)

        # Connect double click to edit with special handling for LP column
        self.cabinets_table.doubleClicked.connect(self.on_table_double_clicked)

        layout.addWidget(self.cabinets_table)

    def on_table_double_clicked(self, index):
        """Handle double-click on table cells, ignoring the LP column for edit"""
        if index.column() != 0:  # Skip the LP column (column 0)
            self.edit_selected_cabinet()

    def setup_accessories_tab(self):
        """Setup the accessories tab UI"""
        layout = QVBoxLayout(self.accessories_tab)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(12)

        # Instructions label
        instructions = QLabel(
            "Zarządzaj akcesoriami dla wybranej szafki. "
            "Wybierz szafkę z listy, aby zobaczyć jej akcesoria."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Cabinet selector
        cab_selector_layout = QHBoxLayout()
        cab_selector_layout.addWidget(QLabel("Wybrana szafka:"))

        self.cabinet_selector = QComboBox()
        self.cabinet_selector.setMinimumWidth(300)
        self.cabinet_selector.currentIndexChanged.connect(self.on_cabinet_selected)
        cab_selector_layout.addWidget(self.cabinet_selector)
        cab_selector_layout.addStretch()

        layout.addLayout(cab_selector_layout)

        # Accessory table view
        self.accessories_table = QTableView()
        self.accessories_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.accessories_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.accessories_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.accessories_table.setAlternatingRowColors(True)
        self.accessories_table.verticalHeader().setVisible(False)

        # Set up the model
        self.accessories_model = AccessoryTableModel()
        self.accessories_table.setModel(self.accessories_model)

        layout.addWidget(self.accessories_table)

        # Action buttons for accessories
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.add_accessory_btn = QPushButton("Dodaj akcesorium")
        self.add_accessory_btn.setIcon(get_icon("add"))
        self.add_accessory_btn.clicked.connect(self.add_accessory)
        buttons_layout.addWidget(self.add_accessory_btn)

        self.edit_accessory_btn = QPushButton("Edytuj")
        self.edit_accessory_btn.setIcon(get_icon("edit"))
        self.edit_accessory_btn.setProperty("class", "secondary")
        self.edit_accessory_btn.clicked.connect(self.edit_accessory)
        buttons_layout.addWidget(self.edit_accessory_btn)

        self.remove_accessory_btn = QPushButton("Usuń")
        self.remove_accessory_btn.setIcon(get_icon("remove"))
        self.remove_accessory_btn.setProperty("class", "danger")
        self.remove_accessory_btn.clicked.connect(self.remove_accessory)
        buttons_layout.addWidget(self.remove_accessory_btn)

        layout.addLayout(buttons_layout)

    def setup_notes_tab(self):
        """Setup the notes tab UI"""
        layout = QVBoxLayout(self.notes_tab)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(15)

        # Create scroll area to handle overflow
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        notes_container = QWidget()
        notes_layout = QVBoxLayout(notes_container)
        notes_layout.setContentsMargins(0, 0, 0, 0)
        notes_layout.setSpacing(20)

        # Blaty (countertops) section
        blaty_group = QGroupBox("Informacje o blatach")
        blaty_layout = QVBoxLayout(blaty_group)

        self.blaty_check = QCheckBox("Blaty")
        self.blaty_check.toggled.connect(self.toggle_blaty_note)
        blaty_layout.addWidget(self.blaty_check)

        self.blaty_note_edit = QTextEdit()
        self.blaty_note_edit.setPlaceholderText(
            "Wprowadź szczegółowe informacje o blatach kuchennych..."
        )
        self.blaty_note_edit.setVisible(False)
        self.blaty_note_edit.setMinimumHeight(120)
        blaty_layout.addWidget(self.blaty_note_edit)

        notes_layout.addWidget(blaty_group)

        # Cokoły (plinths) section
        cokoly_group = QGroupBox("Informacje o cokołach")
        cokoly_layout = QVBoxLayout(cokoly_group)

        self.cokoly_check = QCheckBox("Cokoły")
        self.cokoly_check.toggled.connect(self.toggle_cokoly_note)
        cokoly_layout.addWidget(self.cokoly_check)

        self.cokoly_note_edit = QTextEdit()
        self.cokoly_note_edit.setPlaceholderText(
            "Wprowadź szczegółowe informacje o cokołach..."
        )
        self.cokoly_note_edit.setVisible(False)
        self.cokoly_note_edit.setMinimumHeight(120)
        cokoly_layout.addWidget(self.cokoly_note_edit)

        notes_layout.addWidget(cokoly_group)

        # Uwagi (notes) section
        uwagi_group = QGroupBox("Dodatkowe uwagi")
        uwagi_layout = QVBoxLayout(uwagi_group)

        self.uwagi_check = QCheckBox("Uwagi dodatkowe")
        self.uwagi_check.toggled.connect(self.toggle_uwagi_note)
        uwagi_layout.addWidget(self.uwagi_check)

        self.uwagi_note_edit = QTextEdit()
        self.uwagi_note_edit.setPlaceholderText(
            "Wprowadź dodatkowe uwagi i informacje..."
        )
        self.uwagi_note_edit.setVisible(False)
        self.uwagi_note_edit.setMinimumHeight(120)
        uwagi_layout.addWidget(self.uwagi_note_edit)

        notes_layout.addWidget(uwagi_group)

        # Add stretch to keep everything at the top
        notes_layout.addStretch()

        scroll_area.setWidget(notes_container)
        layout.addWidget(scroll_area)

    def create_sidebar(self):
        """Create the sidebar with project summary"""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setProperty("class", "card")
        sidebar.setMinimumWidth(280)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(15)

        # Client information section
        client_group = QGroupBox("Informacje o kliencie")
        client_layout = QFormLayout(client_group)
        client_layout.setSpacing(8)

        client_name = QLabel(self.project.client_name or "Nie podano")
        client_layout.addRow("Nazwa:", client_name)

        client_address = QLabel(self.project.client_address or "Nie podano")
        client_address.setWordWrap(True)
        client_layout.addRow("Adres:", client_address)

        client_phone = QLabel(self.project.client_phone or "Nie podano")
        client_layout.addRow("Telefon:", client_phone)

        client_email = QLabel(self.project.client_email or "Nie podano")
        client_layout.addRow("Email:", client_email)

        sidebar_layout.addWidget(client_group)

        # Project statistics
        stats_group = QGroupBox("Statystyki projektu")
        stats_layout = QVBoxLayout(stats_group)

        self.cabinets_count_label = QLabel("Liczba szafek: 0")
        stats_layout.addWidget(self.cabinets_count_label)

        self.accessories_count_label = QLabel("Liczba akcesoriów: 0")
        stats_layout.addWidget(self.accessories_count_label)

        self.last_updated_label = QLabel(
            f"Ostatnia aktualizacja: {self.project.updated_at.strftime('%Y-%m-%d %H:%M')}"
        )
        stats_layout.addWidget(self.last_updated_label)

        sidebar_layout.addWidget(stats_group)
        sidebar_layout.addStretch()

        return sidebar

    def create_button_box(self):
        """Create the button box at the bottom"""
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )

        # Export button already in the header, so we don't need it here

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def setup_connections(self):
        """Set up signal-slot connections"""
        pass

    def load_project_data(self):
        """Load project data into the form"""
        # Load flags and notes
        self.blaty_check.setChecked(self.project.blaty)
        self.cokoly_check.setChecked(self.project.cokoly)
        self.uwagi_check.setChecked(self.project.uwagi)

        # Load notes text if available
        if self.project.blaty_note:
            self.blaty_note_edit.setText(self.project.blaty_note)
        if self.project.cokoly_note:
            self.cokoly_note_edit.setText(self.project.cokoly_note)
        if self.project.uwagi_note:
            self.uwagi_note_edit.setText(self.project.uwagi_note)

        # Make note fields visible based on checkbox states
        self.toggle_blaty_note(self.project.blaty)
        self.toggle_cokoly_note(self.project.cokoly)
        self.toggle_uwagi_note(self.project.uwagi)

    def load_cabinets(self):
        """Load cabinets for the project into the table view"""
        cabinets = self.project_service.list_cabinets(self.project.id)

        # Update cabinet count in sidebar
        self.cabinets_count_label.setText(f"Liczba szafek: {len(cabinets)}")

        # Create or update model for table
        if not hasattr(self, "cabinet_model"):
            self.cabinet_model = CabinetTableModel(cabinets, self.session)
            self.cabinets_table.setModel(self.cabinet_model)

            # Set column widths
            self.cabinets_table.setColumnWidth(0, 60)  # Lp.
            self.cabinets_table.setColumnWidth(2, 120)  # Body color
            self.cabinets_table.setColumnWidth(3, 120)  # Front color
            self.cabinets_table.setColumnWidth(4, 120)  # Handle type
            self.cabinets_table.setColumnWidth(5, 60)  # Quantity
            self.cabinets_table.setColumnWidth(6, 100)  # Custom
        else:
            self.cabinet_model.update_cabinets(cabinets)

        # Update cabinet selector for accessories tab
        self.cabinet_selector.clear()
        for cab in cabinets:
            cabinet_name = f"{cab.sequence_number}. {cab.cabinet_type.nazwa if cab.cabinet_type else 'Niestandardowa'}"
            self.cabinet_selector.addItem(cabinet_name, cab.id)

        # Count total accessories
        total_accessories = sum(
            len(cab.accessories) for cab in cabinets if hasattr(cab, "accessories")
        )
        self.accessories_count_label.setText(f"Liczba akcesoriów: {total_accessories}")

    def toggle_blaty_note(self, checked):
        """Show/hide blaty note field based on checkbox state"""
        self.blaty_note_edit.setVisible(checked)

    def toggle_cokoly_note(self, checked):
        """Show/hide cokoly note field based on checkbox state"""
        self.cokoly_note_edit.setVisible(checked)

    def toggle_uwagi_note(self, checked):
        """Show/hide uwagi note field based on checkbox state"""
        self.uwagi_note_edit.setVisible(checked)

    def on_cabinet_selected(self, index):
        """Handle cabinet selection in the accessories tab"""
        if index < 0:
            self.accessories_model.update_accessories([])
            return

        cab_id = self.cabinet_selector.itemData(index)
        if cab_id:
            cabinet = self.project_service.get_cabinet(cab_id)
            if cabinet and hasattr(cabinet, "accessories"):
                self.accessories_model.update_accessories(cabinet.accessories)

    def show_add_cabinet_dialog(self):
        """Show dialog to add a cabinet from catalog"""
        from src.gui.add_cabinet_dialog import AddCabinetDialog

        dialog = AddCabinetDialog(self.session, self.project, parent=self)
        if dialog.exec():
            # Refresh cabinet list
            self.load_cabinets()

    def show_adhoc_cabinet_dialog(self):
        """Show dialog to add a custom cabinet"""
        from src.gui.adhoc_cabinet_dialog import AdhocCabinetDialog

        dialog = AdhocCabinetDialog(self.session, self.project, parent=self)
        if dialog.exec():
            # Refresh cabinet list
            self.load_cabinets()

    def edit_selected_cabinet(self):
        """Edit the selected cabinet"""
        selected_indexes = self.cabinets_table.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.information(
                self, "Wybierz szafkę", "Proszę wybrać szafkę do edycji."
            )
            return

        row = selected_indexes[0].row()
        cabinet = self.cabinet_model.get_cabinet_at_row(row)

        if cabinet:
            if cabinet.type_id:  # Catalog cabinet
                from src.gui.add_cabinet_dialog import AddCabinetDialog

                dialog = AddCabinetDialog(
                    self.session, self.project, cabinet_id=cabinet.id, parent=self
                )
            else:  # Ad-hoc cabinet
                from src.gui.adhoc_cabinet_dialog import AdhocCabinetDialog

                dialog = AdhocCabinetDialog(
                    self.session, self.project, cabinet_id=cabinet.id, parent=self
                )

            if dialog.exec():
                # Refresh cabinet list
                self.load_cabinets()

    def delete_selected_cabinet(self):
        """Delete the selected cabinet"""
        selected_indexes = self.cabinets_table.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.information(
                self, "Wybierz szafkę", "Proszę wybrać szafkę do usunięcia."
            )
            return

        row = selected_indexes[0].row()
        cabinet = self.cabinet_model.get_cabinet_at_row(row)

        if cabinet:
            reply = QMessageBox.question(
                self,
                "Potwierdzenie usunięcia",
                f"Czy na pewno chcesz usunąć szafkę #{cabinet.sequence_number}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                try:
                    # Delete cabinet and refresh list
                    self.project_service.delete_cabinet(cabinet.id)
                    self.load_cabinets()
                except Exception as e:
                    logger.error(f"Error deleting cabinet: {str(e)}")
                    QMessageBox.critical(
                        self, "Błąd", f"Nie udało się usunąć szafki: {str(e)}"
                    )

    def add_accessory(self):
        """Add an accessory to the selected cabinet"""
        index = self.cabinet_selector.currentIndex()
        if index < 0:
            QMessageBox.information(
                self, "Wybierz szafkę", "Proszę najpierw wybrać szafkę."
            )
            return

        cabinet_id = self.cabinet_selector.itemData(index)
        if cabinet_id:
            # Here you would open an accessory dialog
            QMessageBox.information(
                self,
                "Nie zaimplementowano",
                "Funkcja dodawania akcesoriów nie została jeszcze zaimplementowana.",
            )

    def edit_accessory(self):
        """Edit selected accessory"""
        QMessageBox.information(
            self,
            "Nie zaimplementowano",
            "Funkcja edycji akcesoriów nie została jeszcze zaimplementowana.",
        )

    def remove_accessory(self):
        """Remove selected accessory"""
        QMessageBox.information(
            self,
            "Nie zaimplementowano",
            "Funkcja usuwania akcesoriów nie została jeszcze zaimplementowana.",
        )

    def accept(self):
        """Handle dialog acceptance (Save button)"""
        try:
            # Update project flags and notes
            update_data = {
                "blaty": self.blaty_check.isChecked(),
                "cokoly": self.cokoly_check.isChecked(),
                "uwagi": self.uwagi_check.isChecked(),
                "blaty_note": self.blaty_note_edit.toPlainText()
                if self.blaty_check.isChecked()
                else None,
                "cokoly_note": self.cokoly_note_edit.toPlainText()
                if self.cokoly_check.isChecked()
                else None,
                "uwagi_note": self.uwagi_note_edit.toPlainText()
                if self.uwagi_check.isChecked()
                else None,
            }

            self.project_service.update_project(self.project.id, **update_data)
            super().accept()  # Close dialog with accept status

        except Exception as e:
            logger.error(f"Error saving project: {str(e)}")
            QMessageBox.critical(
                self, "Błąd zapisu", f"Wystąpił błąd podczas zapisywania: {str(e)}"
            )

    def export_to_word(self):
        """Export project to Word document"""
        try:
            output_path = self.report_generator.generate(self.project)

            # Open the document automatically
            from os import startfile

            startfile(output_path)

            QMessageBox.information(
                self, "Eksport zakończony", f"Raport został wygenerowany: {output_path}"
            )
        except Exception as e:
            logger.error(f"Error exporting to Word: {str(e)}")
            QMessageBox.critical(
                self,
                "Błąd eksportu",
                f"Nie udało się wygenerować raportu Word: {str(e)}",
            )

    def print_document(self):
        """Print the project's Word document"""
        try:
            output_path = self.report_generator.generate(self.project)

            # Open system print dialog
            from os import startfile

            startfile(output_path, "print")

        except Exception as e:
            logger.error(f"Error printing document: {str(e)}")
            QMessageBox.critical(
                self, "Błąd drukowania", f"Nie udało się wydrukować dokumentu: {str(e)}"
            )
