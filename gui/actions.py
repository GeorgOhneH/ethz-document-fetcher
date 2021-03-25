import logging

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

logger = logging.getLogger(__name__)


class Actions(QObject):
    def __init__(self):
        super().__init__()
        self.exit_app = QAction("&Exit")
        self.exit_app.setShortcut("Ctrl+Q")
        self.exit_app.setStatusTip("Exit application")

        self.run = QAction("&Run All")
        self.run.setShortcut("Ctrl+X")

        self.run_checked = QAction("&Run Selected")

        self.stop = QAction("&Stop")
        self.stop.setShortcut("Ctrl+C")

        self.select_all = QAction("&Select All")
        self.select_none = QAction("&Select None")

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

        self.info_position_group = QActionGroup(self)
        self.info_position_group.addAction(self.info_position_bottom)
        self.info_position_group.addAction(self.info_position_right)

        self.logger = QAction("Logger")
        self.logger.setCheckable(True)