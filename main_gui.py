import logging.config
import os
import sys
from multiprocessing import freeze_support

freeze_support()

import colorama

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import gui.main_window
from gui.application import Application
from gui.constants import ASSETS_PATH
from core.constants import IS_FROZEN, VERSION
from settings.logger import setup_logger
from settings import advanced_settings


try:
    from PyQt5.QtWinExtras import QtWin
    app_id = 'ethz-document-fetcher.ethz-document-fetcher'
    QtWin.setCurrentProcessExplicitAppUserModelID(app_id)
except ImportError:
    pass

colorama.init()

logger = logging.getLogger(__name__)


def default_sys_except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


def log_and_exit_except_hook(cls, exception, traceback):
    logger.critical("Unhandled Exception", exc_info=exception)
    sys.exit(1)


if __name__ == "__main__":
    setup_logger()

    if not IS_FROZEN and advanced_settings.loglevel == "DEBUG":
        sys.excepthook = default_sys_except_hook
    else:
        sys.excepthook = log_and_exit_except_hook

    logger.debug(f"Current Version: {VERSION}")

    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.RoundPreferFloor)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = Application(sys.argv)

    app.setWindowIcon(QIcon(os.path.join(ASSETS_PATH, "logo", "logo.ico")))

    main_window = gui.main_window.MainWindow()
    main_window.show()

    sys.exit(app.exec_())
