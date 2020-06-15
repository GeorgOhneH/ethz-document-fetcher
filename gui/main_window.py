from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import traceback
import time
import yaml
import asyncio
from pprint import pprint
import logging
import traceback
import sys
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
        self.show()

    def closeEvent(self, event):
        self.central_widget.clean_up()
        super(MainWindow, self).closeEvent(event)


