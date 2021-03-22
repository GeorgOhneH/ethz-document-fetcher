import logging.config
import os
import sys
from multiprocessing import freeze_support

import colorama
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import core.utils
import gui
from core.constants import APP_NAME
from core.constants import IS_FROZEN, VERSION
from gui.constants import ASSETS_PATH, TUTORIAL_URL
from settings.logger import setup_logger

try:
    from PyQt5.QtWinExtras import QtWin

    app_id = f"{APP_NAME}.{APP_NAME}"
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
    app = gui.Application(sys.argv)

    setup_logger(app.behavior_settings.loglevel)

    logger.debug(f"Current Version: {VERSION}")
    logger.debug(f"AppData Path: {core.utils.get_app_data_path()}")

    app.set_current_setting_theme()

    app.setWindowIcon(QIcon(os.path.join(ASSETS_PATH, "logo", "logo.ico")))

    main_window = gui.MainWindow()
    main_window.show()

    sys.exit(app.exec_())
