import logging
import os

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from core.constants import VERSION
from gui.constants import ROOT_PATH
from gui.controller import CentralWidget
from gui.startup_tasks import run_startup_tasks

logger = logging.getLogger(__name__)


class Actions(object):
    def __init__(self, parent):
        self.exit_app = QAction("&Exit")
        self.exit_app.setShortcut("Ctrl+Q")
        self.exit_app.setStatusTip("Exit application")
        self.exit_app.triggered.connect(qApp.quit)

        self.run = QAction("&Run All")
        self.run.setShortcut("Ctrl+X")

        self.run_checked = QAction("&Run Selected")

        self.stop = QAction("&Stop")
        self.stop.setShortcut("Ctrl+C")

        self.settings = QAction("&Settings")
        self.settings.setShortcut("Ctrl+S")

        self.open_file = QAction("&Open...")
        self.open_file.setShortcut("Ctrl+O")

        self.edit_file = QAction("&Edit")
        self.edit_file.setShortcut("Ctrl+E")

        self.new_file = QAction("&New")
        self.new_file.setShortcut("Ctrl+N")

        self.info_position_bottom = QAction("Bottom")
        self.info_position_bottom.setCheckable(True)
        self.info_position_right = QAction("Right")
        self.info_position_right.setCheckable(True)

        self.info_position_group = QActionGroup(parent)
        self.info_position_group.addAction(self.info_position_bottom)
        self.info_position_group.addAction(self.info_position_right)

        self.logger = QAction("Logger")
        self.logger.setCheckable(True)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.actions = Actions(self)
        self.central_widget = CentralWidget(self.actions, parent=self)

        self.statusBar()
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")

        file_menu.addAction(self.actions.new_file)

        file_menu.addAction(self.actions.edit_file)

        file_menu.addAction(self.actions.open_file)

        open_presets = file_menu.addMenu("Open &Presets")

        self.init_menu(open_presets, os.path.join(ROOT_PATH, "templates"))

        file_menu.addSeparator()
        file_menu.addAction(self.actions.settings)
        file_menu.addSeparator()
        file_menu.addAction(self.actions.exit_app)
        run_menu = menu_bar.addMenu("&Run")
        run_menu.addAction(self.actions.run)
        run_menu.addAction(self.actions.run_checked)
        run_menu.addAction(self.actions.stop)

        view_menu = menu_bar.addMenu("&View")
        info_position_menu = view_menu.addMenu("Info Tab Position")
        info_position_menu.addAction(self.actions.info_position_bottom)
        info_position_menu.addAction(self.actions.info_position_right)

        view_menu.addAction(self.actions.logger)

        self.setWindowTitle(f"eth-document-fetcher {VERSION}")
        self.setCentralWidget(self.central_widget)

        self.read_settings()

        run_startup_tasks(self.central_widget.site_settings)

    def init_menu(self, menu, path):
        for file_name in os.listdir(path):
            sub_path = os.path.join(path, file_name)
            if not os.path.isfile(sub_path):
                sub_menu = menu.addMenu(file_name)
                self.init_menu(sub_menu, sub_path)
            elif ".yml" in file_name:
                action = menu.addAction(str(file_name))
                action.triggered.connect(lambda checked, file_path=sub_path:
                                         self.central_widget.open_file(file_path=file_path))

    def closeEvent(self, event):
        settings = QSettings("eth-document-fetcher", "eth-document-fetcher")
        settings.setValue("mainWindow/geometry", self.saveGeometry())
        settings.setValue("mainWindow/windowState", self.saveState())
        self.central_widget.clean_up()
        self.central_widget.thread.finished.connect(qApp.quit)
        if not self.central_widget.thread.isRunning():
            event.accept()
        else:
            event.ignore()
            QTimer.singleShot(100, lambda: self._force_quit_prompt())

    def _force_quit_prompt(self):
        r = QMessageBox.question(self,
                                 "Are you sure?",
                                 "Force Quit",
                                 QMessageBox.Yes | QMessageBox.No)
        if r == QMessageBox.Yes:
            qApp.quit()
        else:
            self.central_widget.thread.finished.disconnect(qApp.quit)

    def read_settings(self):
        settings = QSettings("eth-document-fetcher", "eth-document-fetcher")
        if settings.value("mainWindow/geometry") is not None:
            self.restoreGeometry(settings.value("mainWindow/geometry"))
        if settings.value("mainWindow/windowState") is not None:
            self.restoreState(settings.value("mainWindow/windowState"))
