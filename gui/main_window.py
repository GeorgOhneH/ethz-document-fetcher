import logging
import os

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from gui.controller import CentralWidget
from gui.constants import ROOT_PATH

logger = logging.getLogger(__name__)


class Actions(object):
    def __init__(self):
        self.exit_app = QAction("&Exit")
        self.exit_app.setShortcut("Ctrl+Q")
        self.exit_app.setStatusTip("Exit application")
        self.exit_app.triggered.connect(qApp.quit)

        self.run = QAction("&Run")
        self.run.setShortcut("Ctrl+X")

        self.stop = QAction("&Stop")
        self.stop.setShortcut("Ctrl+C")

        self.settings = QAction("&Settings")
        self.settings.setShortcut("Ctrl+Alt+S")

        self.open_file = QAction("&Open...")
        self.open_file.setShortcut("Ctrl+O")

        self.edit_file = QAction("&Edit")
        self.edit_file.setShortcut("Ctrl+E")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.actions = Actions()
        self.central_widget = CentralWidget(self.actions, parent=self)

        self.statusBar()
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")

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
        run_menu.addAction(self.actions.stop)
        self.setWindowTitle('eth document fetcher')
        self.setCentralWidget(self.central_widget)
        self.read_settings()
        self.show()

    def init_menu(self, menu, path):
        for file_name in os.listdir(path):
            sub_path = os.path.join(path, file_name)
            if not os.path.isfile(sub_path):
                sub_menu = menu.addMenu(file_name)
                self.init_menu(sub_menu, sub_path)
            elif ".yml" in file_name:
                action = menu.addAction(str(file_name))
                action.triggered.connect(lambda checked, file_path=sub_path:
                                         self.central_widget.open_file(checked, file_path))

    def closeEvent(self, event):
        self.central_widget.clean_up()
        settings = QSettings("eth-document-fetcher", "eth-document-fetcher")
        settings.setValue("mainWindow/geometry", self.saveGeometry())
        settings.setValue("mainWindow/windowState", self.saveState())
        super(MainWindow, self).closeEvent(event)

    def read_settings(self):
        settings = QSettings("eth-document-fetcher", "eth-document-fetcher")
        if settings.value("mainWindow/geometry") is not None:
            self.restoreGeometry(settings.value("mainWindow/geometry"))
        if settings.value("mainWindow/windowState") is not None:
            self.restoreState(settings.value("mainWindow/windowState"))


