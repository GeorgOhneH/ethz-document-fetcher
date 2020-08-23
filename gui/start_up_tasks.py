import logging
import os
import time

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from core.constants import VERSION
from core.utils import get_latest_version, user_statistics
from settings import global_settings

logger = logging.getLogger(__name__)


DOWNLOAD_RELEASE_URL = "https://github.com/GeorgOhneH/ethz-document-fetcher/releases/latest"


class StartUpController(QWidget):
    def __init__(self, parent, site_settings):
        super().__init__(parent=parent)
        send_user_stats = SendUserStats(site_settings.username)
        QThreadPool.globalInstance().start(send_user_stats)
        if global_settings.check_for_updates:
            check_for_update = CheckForUpdate()
            QThreadPool.globalInstance().start(check_for_update)

            check_for_update.signals.finished.connect(self.show_update_pop_up)

    def show_update_pop_up(self, latest_version):
        if latest_version == VERSION:
            return

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowTitle("A new Version is available")
        msg_box.setText(f"Version {latest_version[1:]} is available.\n"
                        f"Do you want to download it?\n"
                        f"(This will open a website)")
        msg_box.addButton(QMessageBox.Cancel)
        download_button = msg_box.addButton("Download", QMessageBox.AcceptRole)

        msg_box.setDefaultButton(download_button)

        msg_box.exec()

        if msg_box.clickedButton() != download_button:
            return

        QDesktopServices.openUrl(QUrl(DOWNLOAD_RELEASE_URL))


class Signals(QObject):
    finished = pyqtSignal(str)


class CheckForUpdate(QRunnable):
    signals = Signals()

    def run(self):
        try:
            latest_version = get_latest_version()
            self.signals.finished.emit(latest_version)
            return
        except Exception as e:
            logger.warning(f"Could not get release data. Error {e}")
            self.signals.finished.emit(VERSION)


class SendUserStats(QRunnable):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def run(self):
        user_statistics(self.name)
