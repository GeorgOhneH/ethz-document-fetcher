import logging.config
import sys
from multiprocessing import freeze_support
import encodings.idna  # This import is important, else aiohttp won't be able to work probably

freeze_support()

import colorama
from PyQt5.QtWidgets import QApplication

import gui.main_window
from settings.logger import LOGGER_CONFIG

colorama.init()

logging.config.dictConfig(LOGGER_CONFIG)
logger = logging.getLogger(__name__)


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == "__main__":
    sys.excepthook = except_hook
    app = QApplication([])

    main_window = gui.main_window.MainWindow()

    sys.exit(app.exec_())
