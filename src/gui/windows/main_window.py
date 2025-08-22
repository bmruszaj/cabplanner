# src/gui/windows/main_window.py
import logging
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow,
)
from PySide6.QtCore import QTimer

from sqlalchemy.orm import Session

from src.services.project_service import ProjectService
from src.services.report_generator import ReportGenerator
from src.services.settings_service import SettingsService
from src.services.updater_service import UpdaterService

# Import refactored components
from ..widgets.project_card import ProjectCard
from ..widgets.loading_overlay import LoadingOverlay

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main window of the Cabplanner application"""

    def __init__(self, db_session: Session):
        super().__init__()
        self.session = db_session
        self._last_clicked_project: Optional[object] = None
        self._selected_card_widget: Optional[ProjectCard] = None
        self._loading_overlay: Optional[LoadingOverlay] = None
        self._current_search_text = ""  # UX: Persist search text
        self._current_filter_type = ""  # UX: Persist filter type

        self.project_service = ProjectService(db_session)
        self.report_generator = ReportGenerator(db_session=db_session)
        self.settings_service = SettingsService(db_session)
        self.updater_service = UpdaterService(parent=self)
        self.is_dark_mode = self.settings_service.get_setting_value("dark_mode", False)

        # UX: Search debounce timer for better performance
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(250)
        self._search_timer.timeout.connect(self._apply_search_filter)

        self._build_main_window()
        self._setup_shortcuts()
        self.setup_connections()

        # UX: Initialize viewport width tracking
        QTimer.singleShot(0, self._initialize_viewport_tracking)

        self.load_projects()
        self._setup_update_check()

    # The rest of the methods will be copied from the original file
    # This is just the beginning structure
