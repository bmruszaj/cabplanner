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
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex

from sqlalchemy.orm import Session

from src.db_schema.orm_models import Project
from src.services.project_service import ProjectService
from src.services.report_generator import ReportGenerator


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
                from src.services.project_service import ProjectService
                if self.session:
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


class ProjectDetailsView(QDialog):
    """Dialog for viewing and editing project details"""

    def __init__(self, db_session: Session, project: Project, parent=None):
        super().__init__(parent)
        self.session = db_session
        self.project = project
        self.project_service = ProjectService(self.session)
        self.report_generator = ReportGenerator(self.session)

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

    def init_ui(self):
        """Initialize the UI components"""
        self.setWindowTitle(f"Projekt: {self.project.name}")
        self.resize(900, 700)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Create tabs
        self.tabs = QTabWidget()
        self.cabinets_tab = QWidget()
        self.flags_tab = QWidget()
        self.tabs.addTab(self.cabinets_tab, "Szafki")
        self.tabs.addTab(self.flags_tab, "Flagi i uwagi")

        # Setup cabinets tab
        self.setup_cabinets_tab()

        # Setup flags tab
        self.setup_flags_tab()

        main_layout.addWidget(self.tabs)

        # Button box at the bottom
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)

        # Add export button
        self.export_button = button_box.addButton(
            "Eksportuj do Word", QDialogButtonBox.ActionRole
        )
        self.export_button.clicked.connect(self.export_to_word)

        # Add print button
        self.print_button = button_box.addButton("Drukuj", QDialogButtonBox.ActionRole)
        self.print_button.clicked.connect(self.print_document)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def setup_cabinets_tab(self):
        """Setup the cabinets tab UI"""
        layout = QVBoxLayout(self.cabinets_tab)

        # Buttons for cabinet operations
        btn_layout = QHBoxLayout()

        self.add_cabinet_btn = QPushButton("Dodaj z listy")
        self.add_cabinet_btn.clicked.connect(self.show_add_cabinet_dialog)
        btn_layout.addWidget(self.add_cabinet_btn)

        self.add_adhoc_btn = QPushButton("Dodaj niestandardową")
        self.add_adhoc_btn.clicked.connect(self.show_adhoc_cabinet_dialog)
        btn_layout.addWidget(self.add_adhoc_btn)

        self.edit_cabinet_btn = QPushButton("Edytuj")
        self.edit_cabinet_btn.clicked.connect(self.edit_selected_cabinet)
        btn_layout.addWidget(self.edit_cabinet_btn)

        self.delete_cabinet_btn = QPushButton("Usuń")
        self.delete_cabinet_btn.clicked.connect(self.delete_selected_cabinet)
        btn_layout.addWidget(self.delete_cabinet_btn)

        layout.addLayout(btn_layout)

        # Cabinets table view
        self.cabinets_table = QTableView()
        self.cabinets_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cabinets_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.cabinets_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )
        # Only connect double-click for non-LP columns
        self.cabinets_table.doubleClicked.disconnect() if hasattr(self.cabinets_table, 'doubleClicked') else None
        self.cabinets_table.doubleClicked.connect(self.on_table_double_clicked)
        layout.addWidget(self.cabinets_table)

    def on_table_double_clicked(self, index):
        """Handle double-click on table cells, ignoring the LP column"""
        if index.column() != 0:  # Skip the LP column (column 0)
            self.edit_selected_cabinet()

    def setup_flags_tab(self):
        """Setup the flags and notes tab UI"""
        layout = QVBoxLayout(self.flags_tab)

        # Blaty (countertops) section
        self.blaty_check = QCheckBox("Blaty")
        self.blaty_check.toggled.connect(self.toggle_blaty_note)
        layout.addWidget(self.blaty_check)

        self.blaty_note_edit = QTextEdit()
        self.blaty_note_edit.setPlaceholderText("Informacje o blatach...")
        self.blaty_note_edit.setVisible(False)  # Hidden by default
        layout.addWidget(self.blaty_note_edit)

        # Cokoły (plinths) section
        self.cokoly_check = QCheckBox("Cokoły")
        self.cokoly_check.toggled.connect(self.toggle_cokoly_note)
        layout.addWidget(self.cokoly_check)

        self.cokoly_note_edit = QTextEdit()
        self.cokoly_note_edit.setPlaceholderText("Informacje o cokołach...")
        self.cokoly_note_edit.setVisible(False)  # Hidden by default
        layout.addWidget(self.cokoly_note_edit)

        # Uwagi (notes) section
        self.uwagi_check = QCheckBox("Uwagi")
        self.uwagi_check.toggled.connect(self.toggle_uwagi_note)
        layout.addWidget(self.uwagi_check)

        self.uwagi_note_edit = QTextEdit()
        self.uwagi_note_edit.setPlaceholderText("Dodatkowe uwagi...")
        self.uwagi_note_edit.setVisible(False)  # Hidden by default
        layout.addWidget(self.uwagi_note_edit)

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

        # Create or update model
        if not hasattr(self, "cabinet_model"):
            self.cabinet_model = CabinetTableModel(cabinets, self.session)
            self.cabinets_table.setModel(self.cabinet_model)
        else:
            self.cabinet_model.update_cabinets(cabinets)

    def toggle_blaty_note(self, checked):
        """Show/hide blaty note field based on checkbox state"""
        self.blaty_note_edit.setVisible(checked)

    def toggle_cokoly_note(self, checked):
        """Show/hide cokoly note field based on checkbox state"""
        self.cokoly_note_edit.setVisible(checked)

    def toggle_uwagi_note(self, checked):
        """Show/hide uwagi note field based on checkbox state"""
        self.uwagi_note_edit.setVisible(checked)

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
                    QMessageBox.critical(
                        self, "Błąd", f"Nie udało się usunąć szafki: {str(e)}"
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
            QMessageBox.critical(
                self, "Błąd drukowania", f"Nie udało się wydrukować dokumentu: {str(e)}"
            )
