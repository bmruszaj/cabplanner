from PySide6.QtWidgets import (
    QMainWindow,
    QTableView,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QPushButton,
    QStatusBar,
    QToolBar,
    QMessageBox,
    QHeaderView,
    QAbstractItemView,
    QMenu,
    QMenuBar,
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, Signal
from PySide6.QtGui import QAction, QIcon
from pathlib import Path
import logging

from sqlalchemy.orm import Session

from src.services.project_service import ProjectService
from src.services.report_generator import ReportGenerator
from src.gui.project_dialog import ProjectDialog
from src.gui.project_details import ProjectDetailsView
from src.gui.settings_dialog import SettingsDialog
from src.gui.cabinet_catalog_window import CabinetCatalogWindow

# Configure logging
logger = logging.getLogger(__name__)


class ProjectTableModel(QAbstractTableModel):
    """Model for displaying projects in a table view"""

    def __init__(self, projects, parent=None):
        super().__init__(parent)
        self.projects = projects
        self.headers = [
            "Numer zamówienia",
            "Nazwa",
            "Typ kuchni",
            "Klient",
            "Data utworzenia",
        ]

    def rowCount(self, parent=QModelIndex()):
        return len(self.projects)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            project = self.projects[index.row()]
            col = index.column()

            if col == 0:
                return project.order_number
            elif col == 1:
                return project.name
            elif col == 2:
                return project.kitchen_type
            elif col == 3:
                return project.client_name or ""
            elif col == 4:
                return project.created_at.strftime("%Y-%m-%d %H:%M")

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None

    def update_projects(self, projects):
        self.beginResetModel()
        self.projects = projects
        self.endResetModel()

    def get_project_at_row(self, row):
        if 0 <= row < len(self.projects):
            return self.projects[row]
        return None


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self, db_session: Session):
        super().__init__()
        logger.info("Initializing MainWindow")

        # Store the session and initialize services
        self.session = db_session
        self.project_service = ProjectService(self.session)

        # Initialize report generator with appropriate paths
        self.setup_report_generator()

        # Initialize UI components
        self.init_ui()

        # Load data from database
        self.load_projects()

        logger.info("MainWindow initialization complete")

    def setup_report_generator(self):
        """Setup report generator with correct paths"""
        try:
            # Get application directory for logo paths
            app_dir = Path(__file__).resolve().parent.parent.parent
            program_logo_path = app_dir / "program_logo.png"
            company_logo_path = app_dir / "company_logo.png"

            # Check if logo files exist
            program_logo = program_logo_path if program_logo_path.exists() else None
            company_logo = company_logo_path if company_logo_path.exists() else None

            if program_logo is None:
                logger.warning(f"Program logo not found at: {program_logo_path}")
            if company_logo is None:
                logger.warning(f"Company logo not found at: {company_logo_path}")

            # Initialize report generator with session for data access
            self.report_generator = ReportGenerator(
                program_logo_path=program_logo,
                company_logo_path=company_logo,
                db_session=self.session,
            )
            logger.debug("ReportGenerator initialized successfully")
        except Exception as e:
            logger.error(f"Error setting up report generator: {str(e)}")
            # Create a basic report generator without logos as fallback
            self.report_generator = ReportGenerator(db_session=self.session)

    def init_ui(self):
        self.setWindowTitle("Cabplanner")
        self.setMinimumSize(800, 600)

        # Central widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Create toolbar
        self.toolbar = QToolBar("Główny pasek narzędzi")
        self.addToolBar(self.toolbar)

        # Create toolbar actions
        self.new_project_action = QAction("Nowy projekt", self)
        self.new_project_action.triggered.connect(self.show_new_project_dialog)
        self.toolbar.addAction(self.new_project_action)

        self.delete_project_action = QAction("Usuń projekt", self)
        self.delete_project_action.triggered.connect(self.delete_selected_project)
        self.toolbar.addAction(self.delete_project_action)

        self.export_word_action = QAction("Eksportuj do Word", self)
        self.export_word_action.triggered.connect(self.export_to_word)
        self.toolbar.addAction(self.export_word_action)

        self.print_action = QAction("Drukuj", self)
        self.print_action.triggered.connect(self.print_document)
        self.toolbar.addAction(self.print_action)

        # Create projects table view
        self.projects_table = QTableView()
        self.projects_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.projects_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.projects_table.doubleClicked.connect(self.open_project_details)

        # Make columns stretch to fill the available space
        self.projects_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )

        main_layout.addWidget(self.projects_table)

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Create menu bar
        menubar = QMenuBar()
        self.setMenuBar(menubar)

        # File menu
        file_menu = QMenu("Plik", self)
        menubar.addMenu(file_menu)

        file_menu.addAction(self.new_project_action)
        file_menu.addAction(self.delete_project_action)
        file_menu.addSeparator()
        file_menu.addAction("Ustawienia", self.open_settings_dialog)
        file_menu.addSeparator()
        file_menu.addAction("Wyjście", self.close)

        # Projects menu
        projects_menu = QMenu("Projekty", self)
        menubar.addMenu(projects_menu)

        projects_menu.addAction(self.export_word_action)
        projects_menu.addAction(self.print_action)

        # Cabinet menu
        cabinet_menu = QMenu("Szafki", self)
        menubar.addMenu(cabinet_menu)

        cabinet_menu.addAction("Zarządzaj szafkami", self.open_cabinet_catalog)

    def load_projects(self):
        """Load projects from the database and display them"""
        try:
            logger.debug("Loading projects from database")
            projects = self.project_service.list_projects()
            logger.debug(f"Loaded {len(projects)} projects")

            # Create or update model
            if not hasattr(self, "project_model"):
                self.project_model = ProjectTableModel(projects)
                self.projects_table.setModel(self.project_model)
            else:
                self.project_model.update_projects(projects)

            # Update status bar
            self.status_bar.showMessage(f"Załadowano {len(projects)} projektów")
        except Exception as e:
            logger.error(f"Error loading projects: {str(e)}")
            self.status_bar.showMessage("Błąd wczytywania projektów")
            QMessageBox.critical(
                self, "Błąd", f"Nie udało się wczytać projektów: {str(e)}"
            )

    def show_new_project_dialog(self):
        """Show dialog for creating a new project"""
        try:
            logger.debug("Opening new project dialog")
            dialog = ProjectDialog(self.session, parent=self)
            if dialog.exec():
                logger.info("New project created, refreshing project list")
                self.load_projects()
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            QMessageBox.critical(self, "Błąd", f"Nie udało się utworzyć projektu: {str(e)}")

    def delete_selected_project(self):
        """Delete the selected project"""
        selected_indexes = self.projects_table.selectionModel().selectedRows()
        if not selected_indexes:
            logger.debug("No project selected for deletion")
            QMessageBox.information(
                self, "Wybierz projekt", "Proszę wybrać projekt do usunięcia."
            )
            return

        row = selected_indexes[0].row()
        project = self.project_model.get_project_at_row(row)

        if project:
            try:
                logger.debug(f"Confirming deletion of project ID: {project.id}")
                reply = QMessageBox.question(
                    self,
                    "Potwierdzenie usunięcia",
                    f"Czy na pewno chcesz usunąć projekt '{project.name}'?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )

                if reply == QMessageBox.Yes:
                    logger.info(f"Deleting project ID: {project.id}")
                    success = self.project_service.delete_project(project.id)
                    if success:
                        logger.info(f"Project ID: {project.id} deleted successfully")
                        self.load_projects()
                        self.status_bar.showMessage(f"Projekt '{project.name}' został usunięty")
                    else:
                        logger.warning(f"Failed to delete project ID: {project.id}")
                        QMessageBox.critical(
                            self, "Błąd usuwania", "Nie udało się usunąć projektu."
                        )
            except Exception as e:
                logger.error(f"Error deleting project: {str(e)}")
                QMessageBox.critical(
                    self,
                    "Błąd",
                    f"Wystąpił błąd podczas usuwania projektu: {str(e)}",
                )

    def open_project_details(self, index):
        """Open the project details view for the selected project"""
        try:
            row = index.row()
            project = self.project_model.get_project_at_row(row)

            if project:
                logger.debug(f"Opening details for project ID: {project.id}")
                details_view = ProjectDetailsView(self.session, project, parent=self)
                if details_view.exec():
                    logger.debug("Project details updated, refreshing project list")
                    self.load_projects()
        except Exception as e:
            logger.error(f"Error opening project details: {str(e)}")
            QMessageBox.critical(
                self, "Błąd", f"Nie udało się otworzyć szczegółów projektu: {str(e)}"
            )

    def export_to_word(self):
        """Export selected project to Word document"""
        selected_indexes = self.projects_table.selectionModel().selectedRows()
        if not selected_indexes:
            logger.debug("No project selected for export")
            QMessageBox.information(self, "Wybierz projekt", "Proszę wybrać projekt do eksportu.")
            return

        row = selected_indexes[0].row()
        project = self.project_model.get_project_at_row(row)

        if project:
            try:
                logger.info(f"Exporting project ID: {project.id} to Word")

                # Ensure reports directory exists
                Path("documents/reports").mkdir(parents=True, exist_ok=True)

                # Generate report using service
                output_path = self.report_generator.generate(project)

                logger.info(f"Report generated at: {output_path}")
                self.status_bar.showMessage(f"Raport został wygenerowany: {output_path}")

                # Open the document automatically
                from os import startfile

                startfile(output_path)
            except Exception as e:
                logger.error(f"Error exporting to Word: {str(e)}", exc_info=True)
                QMessageBox.critical(
                    self,
                    "Błąd eksportu",
                    f"Nie udało się wygenerować raportu Word: {str(e)}",
                )

    def print_document(self):
        """Print the selected project's Word document"""
        selected_indexes = self.projects_table.selectionModel().selectedRows()
        if not selected_indexes:
            logger.debug("No project selected for printing")
            QMessageBox.information(self, "Wybierz projekt", "Proszę wybrać projekt do wydrukowania.")
            return

        row = selected_indexes[0].row()
        project = self.project_model.get_project_at_row(row)

        if project:
            try:
                logger.info(f"Printing project ID: {project.id}")

                # Generate report without opening it
                output_path = self.report_generator.generate(project, auto_open=False)

                # Send to printer
                from os import startfile

                startfile(output_path, "print")

                logger.info(f"Print job sent for project ID: {project.id}")
                self.status_bar.showMessage(f"Wysłano do druku: {project.name}")
            except Exception as e:
                logger.error(f"Error printing document: {str(e)}", exc_info=True)
                QMessageBox.critical(
                    self,
                    "Błąd drukowania",
                    f"Nie udało się wydrukować dokumentu: {str(e)}",
                )

    def open_settings_dialog(self):
        """Open the settings dialog"""
        try:
            logger.debug("Opening settings dialog")
            dialog = SettingsDialog(self.session, parent=self)
            dialog.exec()

            # Reload report generator to apply new settings (like logos)
            self.setup_report_generator()
        except Exception as e:
            logger.error(f"Error opening settings dialog: {str(e)}")
            QMessageBox.critical(self, "Błąd", f"Nie udało się otworzyć ustawień: {str(e)}")

    def open_cabinet_catalog(self):
        """Open the cabinet catalog window"""
        try:
            logger.debug("Opening cabinet catalog window")
            catalog_window = CabinetCatalogWindow(self.session, parent=self)
            catalog_window.show()
        except Exception as e:
            logger.error(f"Error opening cabinet catalog: {str(e)}")
            QMessageBox.critical(
                self, "Błąd", f"Nie udało się otworzyć katalogu szafek: {str(e)}"
            )
