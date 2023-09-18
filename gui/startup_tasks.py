import logging

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import core.utils
import gui
from core.constants import VERSION, PYU_VERSION, IS_FROZEN

logger = logging.getLogger(__name__)

DOWNLOAD_RELEASE_URL = "https://github.com/GeorgOhneH/ethz-document-fetcher/releases/latest"


def run_startup_tasks(download_settings):
    background_tasks = BackgroundTasks(download_settings.username)
    QThreadPool.globalInstance().start(background_tasks)

    behavior_settings = gui.Application.instance().behavior_settings

    if behavior_settings.check_for_updates and IS_FROZEN:
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
        msg_box.setText(f"Version {latest_version[1:]} is available. (Current: {VERSION})\n"
                        f"Go to {DOWNLOAD_RELEASE_URL} to download the new release?")
        msg_box.addButton(QMessageBox.Cancel)
        install_button = msg_box.addButton("Ok", QMessageBox.AcceptRole)

        msg_box.setDefaultButton(install_button)

        msg_box.exec()

        if msg_box.clickedButton() != install_button:
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
        try:
            latest_version = core.utils.get_latest_version()
        except Exception as e:
            logger.warning(f"Could not get release data. Error {e}")
            return

        if latest_version == VERSION:
            return

        self.signals.ask_for_permission.emit(latest_version)

        self.mutex.lock()
        try:
            self.cond.wait(self.mutex)
        finally:
            self.mutex.unlock()

        if not self.allowed_download:
            logger.debug("Update declined")
            return


class BackgroundTasks(QRunnable):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def run(self):
        core.utils.remove_old_files()
        core.utils.user_statistics(self.name)