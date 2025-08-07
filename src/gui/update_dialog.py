from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class UpdateDialog(QDialog):
    """Dialog for checking for updates and displaying update progress."""

    check_for_updates = Signal()
    perform_update = Signal()
    cancel_update = Signal()

    def __init__(self, current_version, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aktualizacja Cabplanner")
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setMinimumWidth(450)
        self.setMinimumHeight(180)
        self.setModal(True)

        self.current_version = current_version
        self._setup_ui()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Version info section
        self.version_label = QLabel(f"Aktualna wersja: v{self.current_version}")
        self.version_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setBold(True)
        self.version_label.setFont(font)
        layout.addWidget(self.version_label)

        # Status section
        self.status_label = QLabel("Sprawdzanie aktualizacji...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setVisible(False)  # Hidden initially
        layout.addWidget(self.progress_bar)

        # Buttons
        button_layout = QHBoxLayout()

        self.check_button = QPushButton("Sprawdź aktualizacje")
        self.check_button.clicked.connect(self.check_for_updates.emit)
        button_layout.addWidget(self.check_button)

        self.update_button = QPushButton("Aktualizuj teraz")
        self.update_button.clicked.connect(self.perform_update.emit)
        self.update_button.setEnabled(False)  # Disabled initially
        self.update_button.setVisible(False)  # Hidden initially
        button_layout.addWidget(self.update_button)

        self.cancel_button = QPushButton("Anuluj")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def update_available(self, current_version, latest_version):
        """Update UI to show that an update is available."""
        self.version_label.setText(f"Aktualna wersja: v{current_version}")
        self.status_label.setText(f"Dostępna nowa wersja: v{latest_version}")
        self.update_button.setEnabled(True)
        self.update_button.setVisible(True)
        self.check_button.setVisible(False)
        self.progress_bar.setVisible(False)

    def no_update_available(self):
        """Update UI to show that no update is available."""
        self.status_label.setText("Masz najnowszą wersję programu.")
        self.check_button.setEnabled(True)
        self.update_button.setVisible(False)
        self.progress_bar.setVisible(False)

    def update_check_failed(self, error_message):
        """Update UI to show that the update check failed."""
        self.status_label.setText("Nie udało się sprawdzić aktualizacji.")
        QMessageBox.warning(
            self,
            "Błąd sprawdzania aktualizacji",
            f"Nie można sprawdzić aktualizacji: {error_message}",
        )
        self.check_button.setEnabled(True)
        self.update_button.setVisible(False)
        self.progress_bar.setVisible(False)

    def update_started(self):
        """Update UI to show that the update process has started."""
        self.status_label.setText("Pobieranie aktualizacji...")
        self.check_button.setEnabled(False)
        self.check_button.setVisible(False)
        self.update_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

    def update_progress(self, percent):
        """Update the progress bar."""
        self.progress_bar.setValue(percent)

        # Update status text based on progress
        if percent < 50:
            self.status_label.setText("Pobieranie aktualizacji...")
        elif percent < 70:
            self.status_label.setText("Rozpakowywanie aktualizacji...")
        elif percent < 90:
            self.status_label.setText("Instalowanie aktualizacji...")
        else:
            self.status_label.setText("Finalizowanie aktualizacji...")

    def update_completed(self):
        """Update UI to show that the update has completed."""
        self.status_label.setText("Aktualizacja zakończona! Restartowanie aplikacji...")
        self.progress_bar.setValue(100)
        self.cancel_button.setEnabled(False)

    def update_failed(self, error_message):
        """Update UI to show that the update failed."""
        self.status_label.setText("Aktualizacja nie powiodła się.")
        self.progress_bar.setVisible(False)
        self.check_button.setEnabled(True)
        self.check_button.setVisible(True)
        self.update_button.setVisible(False)
        self.cancel_button.setEnabled(True)

        QMessageBox.critical(
            self,
            "Błąd aktualizacji",
            f"Proces aktualizacji nie powiódł się: {error_message}",
        )
