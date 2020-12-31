import logging.config
import os
import sys
from multiprocessing import freeze_support

freeze_support()

import colorama

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

try:
    from PyQt5.QtWinExtras import QtWin

    myappid = 'eth-document-fetcher.eth-document-fetcher'
    QtWin.setCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass

import gui.main_window
from gui.constants import ASSETS_PATH
from core.constants import IS_FROZEN
from settings.logger import setup_logger
from settings import advanced_settings, gui_settings

colorama.init()

setup_logger()
logger = logging.getLogger(__name__)


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == "__main__":
    if not IS_FROZEN and advanced_settings.loglevel == "DEBUG":
        sys.excepthook = except_hook

    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.RoundPreferFloor)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)

    # app.setStyle('Fusion')

    # darkPalette = QPalette()
    #
    # # base
    # darkPalette.setColor(QPalette.WindowText, QColor(180, 180, 180))
    # darkPalette.setColor(QPalette.Button, QColor(53, 53, 53))
    # darkPalette.setColor(QPalette.Light, QColor(180, 180, 180))
    # darkPalette.setColor(QPalette.Midlight, QColor(90, 90, 90))
    # darkPalette.setColor(QPalette.Dark, QColor(35, 35, 35))
    # darkPalette.setColor(QPalette.Text, QColor(180, 180, 180))
    # darkPalette.setColor(QPalette.BrightText, QColor(180, 180, 180))
    # darkPalette.setColor(QPalette.ButtonText, QColor(180, 180, 180))
    # darkPalette.setColor(QPalette.Base, QColor(42, 42, 42))
    # darkPalette.setColor(QPalette.Window, QColor(53, 53, 53))
    # darkPalette.setColor(QPalette.Shadow, QColor(20, 20, 20))
    # darkPalette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    # darkPalette.setColor(QPalette.HighlightedText, QColor(180, 180, 180))
    # darkPalette.setColor(QPalette.Link, QColor(56, 252, 196))
    # darkPalette.setColor(QPalette.AlternateBase, QColor(66, 66, 66))
    # darkPalette.setColor(QPalette.ToolTipBase, QColor(53, 53, 53))
    # darkPalette.setColor(QPalette.ToolTipText, QColor(180, 180, 180))
    #
    # # disabled
    # darkPalette.setColor(QPalette.Disabled, QPalette.WindowText,
    #                      QColor(127, 127, 127))
    # darkPalette.setColor(QPalette.Disabled, QPalette.Text,
    #                      QColor(127, 127, 127))
    # darkPalette.setColor(QPalette.Disabled, QPalette.ButtonText,
    #                      QColor(127, 127, 127))
    # darkPalette.setColor(QPalette.Disabled, QPalette.Highlight,
    #                      QColor(80, 80, 80))
    # darkPalette.setColor(QPalette.Disabled, QPalette.HighlightedText,
    #                      QColor(127, 127, 127))
    #
    # app.setPalette(darkPalette)

    app.setWindowIcon(QIcon(os.path.join(ASSETS_PATH, "logo", "logo.ico")))

    main_window = gui.main_window.MainWindow()
    main_window.show()

    sys.exit(app.exec_())
