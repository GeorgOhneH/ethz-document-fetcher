import logging.config
import os
import sys
from multiprocessing import freeze_support

import colorama

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import gui.main_window
from gui.startup_tasks import run_startup_tasks
from gui.application import Application
from gui.constants import ASSETS_PATH
from core.constants import IS_FROZEN, VERSION
from core.utils import get_app_data_path
from settings.logger import setup_logger


try:
    from PyQt5.QtWinExtras import QtWin
    app_id = 'ethz-document-fetcher.ethz-document-fetcher'
    QtWin.setCurrentProcessExplicitAppUserModelID(app_id)
except ImportError:
    pass

logger = logging.getLogger(__name__)


def default_sys_except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


def log_and_exit_except_hook(cls, exception, traceback):
    logger.critical("Unhandled Exception", exc_info=exception)
    sys.exit(1)


if __name__ == "__main__":
    freeze_support()

    colorama.init()

    if IS_FROZEN:
        sys.excepthook = log_and_exit_except_hook
    else:
        sys.excepthook = default_sys_except_hook

    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.RoundPreferFloor)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = Application(sys.argv)

    setup_logger(app.behavior_settings.loglevel)

    logger.debug(f"Current Version: {VERSION}")
    logger.debug(f"AppData Path: {get_app_data_path()}")

    app.set_current_setting_theme()

    app.setWindowIcon(QIcon(os.path.join(ASSETS_PATH, "logo", "logo.ico")))

    main_window = gui.main_window.MainWindow()
    main_window.show()

    run_startup_tasks(app.download_settings)

    sys.exit(app.exec_())
