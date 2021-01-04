import logging

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from pyupdater.client import Client

from core.client_config import ClientConfig
from core.constants import VERSION, PYU_VERSION
from core.utils import get_latest_version, user_statistics
from settings import advanced_settings

logger = logging.getLogger(__name__)

DOWNLOAD_RELEASE_URL = "https://github.com/GeorgOhneH/ethz-document-fetcher/releases/latest"


def run_startup_tasks(site_settings):
    send_user_stats = SendUserStats(site_settings.username)
    QThreadPool.globalInstance().start(send_user_stats)
    if advanced_settings.check_for_updates:
        mutex = QMutex()
        cond = QWaitCondition()
        check_for_update = Update(mutex=mutex, cond=cond)
        QThreadPool.globalInstance().start(check_for_update)

        check_for_update.signals.ask_for_permission.connect(
            lambda latest_version: ask_update_pop_up(latest_version, check_for_update))


def ask_update_pop_up(latest_version, check_for_update):
    try:
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

        check_for_update.allowed_download = True
    finally:
        check_for_update.cond.wakeAll()


class Signals(QObject):
    ask_for_permission = pyqtSignal(str)


class Update(QRunnable):
    signals = Signals()

    def __init__(self, mutex, cond):
        super().__init__()
        self.mutex = mutex
        self.cond = cond
        self.allowed_download = False

    def run(self):
        client = Client(ClientConfig())
        client.refresh()

        app_update = client.update_check(ClientConfig.APP_NAME, PYU_VERSION)

        if app_update is None:
            return

        try:
            latest_version = get_latest_version()
        except Exception as e:
            logger.warning(f"Could not get release data. Error {e}")
            return

        if latest_version == VERSION:
            return

        app_update.download()

        self.signals.ask_for_permission.emit(latest_version)

        self.mutex.lock()
        try:
            self.cond.wait(self.mutex)
        finally:
            self.mutex.unlock()

        if not self.allowed_download:
            logger.debug("Updated declined")
            return

        if app_update.is_downloaded():
            logger.debug("Update: Extract and Restart")
            app_update.extract_restart()


class SendUserStats(QRunnable):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def run(self):
        user_statistics(self.name)
