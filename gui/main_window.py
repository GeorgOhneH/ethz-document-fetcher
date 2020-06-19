import logging

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from gui.controller import CentralWidget

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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.actions = Actions()
        self.statusBar()
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction(self.actions.exit_app)
        run_menu = menu_bar.addMenu("&Run")
        run_menu.addAction(self.actions.run)
        run_menu.addAction(self.actions.stop)
        self.setWindowTitle('thread test')
        self.central_widget = CentralWidget(self.actions, parent=self)
        self.setCentralWidget(self.central_widget)
        self.read_settings()
        self.show()

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


