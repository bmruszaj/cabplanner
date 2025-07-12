# main_window.py

import sys
import os
from pathlib import Path

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTableView,
    QToolBar,
    QStatusBar,
    QDialog,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDialogButtonBox,
    QMessageBox,
)

from src.services.project_service import ProjectService
from src.services.report_generator import ReportGenerator

# Allowed kitchen‐type codes as per your Project ORM
KITCHEN_TYPES = ["LOFT", "PARIS", "WINO"]


class ProjectTableModel(QAbstractTableModel):
    HEADERS = [
        "Numer zamówienia",
        "Nazwa projektu",
        "Typ kuchni",
        "Klient",
        "Utworzono",
    ]

    def __init__(self, projects=None):
        super().__init__()
        self._projects = projects or []

    def update_projects(self, projects):
        self.beginResetModel()
        self._projects = projects
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._projects)

    def columnCount(self, parent=QModelIndex()):
        return len(self.HEADERS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        proj = self._projects[index.row()]
        col = index.column()
        if col == 0:
            return proj.order_number
        elif col == 1:
            return proj.name
        elif col == 2:
            return proj.kitchen_type
        elif col == 3:
            return proj.client_name
        elif col == 4:
            return proj.created_at.strftime("%Y-%m-%d %H:%M")
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.HEADERS[section]
        return super().headerData(section, orientation, role)


class NewProjectDialog(QDialog):
    def __init__(self, parent, project_service: ProjectService):
        super().__init__(parent)
        self.setWindowTitle("Nowy projekt")
        self.project_service = project_service
        self.project = None

        form = QFormLayout(self)

        self.order_edit = QLineEdit()
        form.addRow("Numer zamówienia:", self.order_edit)

        self.name_edit = QLineEdit()
        form.addRow("Nazwa projektu:", self.name_edit)

        # Use fixed kitchen‐type codes
        self.kitchen_type_combo = QComboBox()
        self.kitchen_type_combo.addItems(KITCHEN_TYPES)
        form.addRow("Typ kuchni:", self.kitchen_type_combo)

        self.client_edit = QLineEdit()
        form.addRow("Klient:", self.client_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _on_accept(self):
        order = self.order_edit.text().strip()
        name = self.name_edit.text().strip()
        ktype = self.kitchen_type_combo.currentText().strip()
        client = self.client_edit.text().strip()

        if not all([order, name, ktype, client]):
            QMessageBox.warning(
                self, "Błąd walidacji", "Proszę wypełnić wszystkie pola."
            )
            return

        try:
            project = self.project_service.create_project(
                order_number=order, name=name, kitchen_type=ktype, client_name=client
            )
            self.project = project
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się utworzyć projektu:\n{e}")


class MainWindow(QMainWindow):
    def __init__(
        self, project_service: ProjectService, report_generator: ReportGenerator
    ):
        super().__init__()
        self.setWindowTitle("Cabplanner")
        self.resize(800, 600)

        self.project_service = project_service
        self.report_generator = report_generator

        # Central project list
        self.table = QTableView()
        self.model = ProjectTableModel()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.setCentralWidget(self.table)

        # Toolbar with actions
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        add_act = QAction("Nowy projekt", self)
        add_act.triggered.connect(self.on_add_project)
        toolbar.addAction(add_act)

        del_act = QAction("Usuń projekt", self)
        del_act.triggered.connect(self.on_delete_project)
        toolbar.addAction(del_act)

        exp_act = QAction("Eksportuj do Word", self)
        exp_act.triggered.connect(self.on_export_to_word)
        toolbar.addAction(exp_act)

        print_act = QAction("Drukuj", self)
        print_act.triggered.connect(self.on_print)
        toolbar.addAction(print_act)

        # Status bar for messages
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # React to selection changes
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)

        # Initial load
        self.load_projects()

    def load_projects(self):
        projects = self.project_service.list_projects()
        self.model.update_projects(projects)
        msg = f"Załadowano {len(projects)} projektów" if projects else "Brak projektów"
        self.status.showMessage(msg)

    def get_selected_project(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        return self.model._projects[rows[0].row()]

    def on_selection_changed(self, selected, deselected):
        proj = self.get_selected_project()
        if proj:
            self.status.showMessage(f"Wybrano projekt: {proj.name}")
        else:
            self.status.showMessage("Brak wybranego projektu")

    def on_add_project(self):
        dlg = NewProjectDialog(self, self.project_service)
        if dlg.exec() == QDialog.Accepted and dlg.project:
            self.load_projects()
            self.status.showMessage(f"Dodano projekt: {dlg.project.name}")

    def on_delete_project(self):
        proj = self.get_selected_project()
        if not proj:
            QMessageBox.information(
                self, "Brak projektu", "Nie wybrano projektu do usunięcia."
            )
            return
        resp = QMessageBox.question(
            self,
            "Usuń projekt",
            f"Czy na pewno chcesz usunąć projekt '{proj.name}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            self.project_service.delete_project(proj.id)
            self.load_projects()

    def on_export_to_word(self):
        proj = self.get_selected_project()
        if not proj:
            QMessageBox.information(
                self, "Brak projektu", "Nie wybrano projektu do eksportu."
            )
            return
        try:
            path = self.report_generator.generate(proj)
            QMessageBox.information(
                self, "Eksport zakończony", f"Raport zapisano do:\n{path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Błąd eksportu", f"Nie udało się wyeksportować projektu:\n{e}"
            )

    def on_print(self):
        proj = self.get_selected_project()
        if not proj:
            QMessageBox.information(
                self, "Brak projektu", "Nie wybrano projektu do wydruku."
            )
            return
        try:
            path = self.report_generator.generate(proj, auto_open=False)
            os.startfile(path, "print")
        except Exception as e:
            QMessageBox.critical(
                self, "Błąd drukowania", f"Nie udało się wydrukować projektu:\n{e}"
            )


if __name__ == "__main__":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    DATABASE_PATH = Path(__file__).resolve().parent.parent.parent / "cabplanner.db"
    engine = create_engine(f"sqlite:///{DATABASE_PATH}", echo=False)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    project_service = ProjectService(session)
    report_generator = ReportGenerator()

    app = QApplication(sys.argv)
    window = MainWindow(project_service, report_generator)
    window.show()
    sys.exit(app.exec())
