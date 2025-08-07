from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtCore import QCoreApplication


class UpdateDialog(QDialog):
    """Dialog for checking for updates and displaying update progress."""

    check_for_updates = Signal()
    perform_update = Signal()
    cancel_update = Signal()

    def __init__(self, current_version, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Aktualizacja Cabplanner"))
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setMinimumWidth(450)
        self.setMinimumHeight(180)
        self.setModal(True)

        self.current_version = current_version
        self._setup_ui()
        self._setup_shortcuts()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Version info section
        self.version_label = QLabel(
            self.tr(f"Aktualna wersja: v{self.current_version}")
        )
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.version_label.setFont(QFont("", weight=QFont.Weight.Bold))
        layout.addWidget(self.version_label)

        # Status section
        self.status_label = QLabel(
            self.tr("Naciśnij przycisk, aby sprawdzić aktualizacje.")
        )
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Buttons
        button_layout = QHBoxLayout()

        self.check_button = QPushButton(self.tr("Sprawdź aktualizacje"))
        self.check_button.clicked.connect(self.check_for_updates.emit)
        button_layout.addWidget(self.check_button)

        self.update_button = QPushButton(self.tr("Aktualizuj teraz"))
        self.update_button.clicked.connect(self.perform_update.emit)
        self.update_button.setEnabled(False)
        self.update_button.setVisible(False)
        button_layout.addWidget(self.update_button)

        self.cancel_button = QPushButton(self.tr("Anuluj"))
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        layout.addStretch()

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts for the dialog."""
        # Alt+U for update (when update button is visible and enabled)
        self.update_shortcut = QShortcut(QKeySequence("Alt+U"), self)
        self.update_shortcut.activated.connect(self._on_update_shortcut)

        # Esc for cancel
        self.cancel_shortcut = QShortcut(QKeySequence("Esc"), self)
        self.cancel_shortcut.activated.connect(self._on_cancel_clicked)

    def _on_update_shortcut(self):
        """Handle Alt+U shortcut - trigger update if button is enabled and visible."""
        if self.update_button.isVisible() and self.update_button.isEnabled():
            self.perform_update.emit()

    def _on_cancel_clicked(self):
        self.cancel_update.emit()
        self.reject()

    def update_available(self, current_version, latest_version):
        """Show that an update is available."""
        self.version_label.setText(self.tr(f"Aktualna wersja: v{current_version}"))
        self.status_label.setText(self.tr(f"Dostępna nowa wersja: v{latest_version}"))
        self.check_button.setVisible(False)
        self.check_button.setEnabled(False)
        self.update_button.setVisible(True)
        self.update_button.setEnabled(True)
        self.progress_bar.setVisible(False)

    def no_update_available(self):
        """Show that no update is available."""
        self.status_label.setText(self.tr("Masz najnowszą wersję programu."))
        self.check_button.setVisible(True)
        self.check_button.setEnabled(True)
        self.update_button.setVisible(False)
        self.update_button.setEnabled(False)
        self.progress_bar.setVisible(False)

    def update_check_failed(self, error_message):
        """Show that the update check failed."""
        self.status_label.setText(self.tr("Nie udało się sprawdzić aktualizacji."))
        QMessageBox.warning(
            self,
            self.tr("Błąd sprawdzania aktualizacji"),
            self.tr(f"Nie można sprawdzić aktualizacji: {error_message}"),
        )
        self.check_button.setVisible(True)
        self.check_button.setEnabled(True)
        self.update_button.setVisible(False)
        self.update_button.setEnabled(False)
        self.progress_bar.setVisible(False)

    @Slot()
    def on_update_started(self):
        """Show that the update process has started."""
        # Disable the window close button mid-update
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        self.show()

        # Initialize UI state
        self.status_label.setText(self.tr("Przygotowywanie aktualizacji..."))
        self.check_button.setVisible(False)
        self.check_button.setEnabled(False)
        self.update_button.setVisible(False)
        self.update_button.setEnabled(False)
        self.cancel_button.setEnabled(False)

        # Show and reset progress bar
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        # Force UI update
        self.repaint()
        QCoreApplication.processEvents()

    @Slot(int)
    def on_update_progress(self, percent):
        """Update the progress bar and status text."""
        self.progress_bar.setValue(percent)

        # Update status based on progress
        if percent < 10:
            self.status_label.setText(self.tr("Przygotowywanie aktualizacji..."))
        elif percent < 70:
            self.status_label.setText(self.tr("Pobieranie aktualizacji..."))
        elif percent < 80:
            self.status_label.setText(self.tr("Rozpakowywanie aktualizacji..."))
        elif percent < 95:
            self.status_label.setText(self.tr("Instalowanie aktualizacji..."))
        else:
            self.status_label.setText(self.tr("Finalizowanie aktualizacji..."))

        # Force UI update
        self.repaint()
        QCoreApplication.processEvents()

    @Slot()
    def on_update_completed(self):
        """Show that the update has completed and will restart immediately."""
        self.progress_bar.setValue(100)
        self.status_label.setText(self.tr("Aktualizacja zakończona! Restartowanie aplikacji..."))
        self.cancel_button.setEnabled(False)

        # Force UI update
        self.repaint()
        QCoreApplication.processEvents()

    @Slot(str)
    def on_update_failed(self, error_message):
        """Show that the update failed."""
        self.status_label.setText(self.tr("Aktualizacja nie powiodła się."))
        self.progress_bar.setVisible(False)
        self.check_button.setVisible(True)
        self.check_button.setEnabled(True)
        self.update_button.setVisible(False)
        self.update_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        # Re-enable close button
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, True)
        self.show()
        QMessageBox.critical(
            self,
            self.tr("Błąd aktualizacji"),
            self.tr(f"Proces aktualizacji nie powiódł się: {error_message}"),
        )
