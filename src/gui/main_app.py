import sys
from PySide6.QtWidgets import QApplication
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.gui.main_window import MainWindow


class CabplannerApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Cabplanner")

        # Setup database connection
        self.engine = create_engine("sqlite:///../../cabplanner.db")
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

        # Create main window
        self.main_window = MainWindow(self.session)
        self.main_window.show()

    def exec(self):
        return self.app.exec()


def main():
    cabplanner = CabplannerApp()
    sys.exit(cabplanner.exec())


if __name__ == "__main__":
    main()
