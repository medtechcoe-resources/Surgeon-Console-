import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QStackedWidget, QScrollArea)
from PyQt6.QtCore import Qt

from theme_manager import ThemeManager

from widgets.header import Header
from widgets.nav_tabs import NavBar
from widgets.patient_sidebar import PatientSidebar
from widgets.status_bar import StatusBar

from screens.preop_planning import PreopPlanningScreen
from screens.live_video import LiveVideoScreen
from screens.live_control import LiveControlScreen
from screens.settings import SettingsScreen


class AetherConsole(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AETHER SURGICAL ROBOTIC CONSOLE — REV 4.2")
        self.resize(3440, 1440)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header (contains E-Stop + theme toggle inline)
        self.header = Header()
        root.addWidget(self.header)

        # Nav tabs
        self.nav = NavBar()
        root.addWidget(self.nav)

        # Content area: left sidebar + stacked screens
        content_wrap = QWidget()
        content_h = QHBoxLayout(content_wrap)
        content_h.setContentsMargins(20, 0, 20, 0)
        content_h.setSpacing(16)

        self.sidebar = PatientSidebar()
        content_h.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.preop = PreopPlanningScreen()
        self.live_video = LiveVideoScreen()
        self.live_control = LiveControlScreen()
        self.settings = SettingsScreen()

        for screen in (self.preop, self.live_video, self.live_control,
                       self.settings):
            scroller = QScrollArea()
            scroller.setWidgetResizable(True)
            scroller.setFrameShape(QScrollArea.Shape.NoFrame)
            scroller.setWidget(screen)
            self.stack.addWidget(scroller)

        content_h.addWidget(self.stack, 1)
        root.addWidget(content_wrap, 1)

        # Status bar
        self.status_bar_widget = StatusBar()
        root.addWidget(self.status_bar_widget)

        # Wire up navigation
        self.nav.tab_changed.connect(self.stack.setCurrentIndex)

        # Wire theme toggle (header.theme_btn is a _ThemeButton that repaints itself;
        # ThemeManager broadcasts the change to all subscribed widgets)
        self.header.theme_btn.clicked.connect(ThemeManager.instance().toggle)


def main():
    app = QApplication(sys.argv)

    # Apply saved theme before any windows open
    tm = ThemeManager.instance()
    tm.apply_initial()

    window = AetherConsole()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
