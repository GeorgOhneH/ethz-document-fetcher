import logging.config
import sys
import os
from multiprocessing import freeze_support
import encodings.idna  # This import is important, else aiohttp won't be able to work probably

freeze_support()

import colorama

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

try:
    # Include in try/except block if you're also targeting Mac/Linux
    from PyQt5.QtWinExtras import QtWin
    myappid = 'eth-document-fetcher.eth-document-fetcher'
    QtWin.setCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass

import gui.main_window
from gui.constants import ASSETS_PATH
from core.constants import IS_FROZEN
from settings.logger import LOGGER_CONFIG
from settings import global_settings

colorama.init()

logging.config.dictConfig(LOGGER_CONFIG)
logger = logging.getLogger(__name__)


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == "__main__":
    if not IS_FROZEN and global_settings.loglevel == "DEBUG":
        sys.excepthook = except_hook

    app = QApplication([])
    app.setWindowIcon(QIcon(os.path.join(ASSETS_PATH, "logo", "logo.ico")))

    main_window = gui.main_window.MainWindow()

    sys.exit(app.exec_())
