import logging
import re
from ansi2html import Ansi2HTMLConverter

from PyQt5.QtCore import *
from colorama import Fore, Style

from settings import global_settings

LOGGER_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'info_fmt': {
            '()': 'settings.logger.ColouredFormatter',
            'format': '%(levelname)s: %(message)s',
        },
        'debug_fmt': {
            '()': 'settings.logger.ColouredFormatter',
            'format': '%(levelname)s: %(asctime)s - %(name)s - %(message)s',
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": global_settings.loglevel if global_settings.loglevel in ["ERROR", "WARNING", "INFO",
                                                                              "DEBUG"] else "INFO",
            "formatter": "debug_fmt" if global_settings.loglevel == "DEBUG" else "info_fmt",
            "stream": "ext://sys.stdout",
        },
    },
    'loggers': {
        '': {
            'level': 'DEBUG',
            'handlers': ["console"],
        },
    }
}


class ColouredFormatter(logging.Formatter):
    COLOURS = {
        "CRITICAL": Fore.RED,
        "ERROR": Fore.RED,
        "WARNING": Fore.LIGHTYELLOW_EX,
        "INFO": Fore.LIGHTBLUE_EX,
        "DEBUG": Fore.MAGENTA,
    }

    def format(self, record):
        levelname = record.levelname
        record.levelname = self.COLOURS[levelname] + levelname + Style.RESET_ALL
        return logging.Formatter.format(self, record)


class QtHandler(QObject, logging.Handler):
    new_record = pyqtSignal(object)

    def __init__(self, parent):
        super().__init__(parent)
        super(logging.Handler).__init__()
        formatter = QtFormatter('%(levelname)s: %(asctime)s - %(name)s - %(message)s')
        self.setFormatter(formatter)

    def emit(self, record):
        msg = self.format(record)
        self.new_record.emit(msg)


class QtFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conv = Ansi2HTMLConverter(linkify=True, line_wrap=False)

    def format(self, record):
        s = super().format(record)
        html = self.conv.convert(s, full=True)
        html = html.replace(""".ansi2html-content { display: inline; white-space: pre; word-wrap: break-word; }
.body_foreground { color: #AAAAAA; }
.body_background { background-color: #000000; }
.body_foreground > .bold,.bold > .body_foreground, body.body_foreground > pre > .bold { color: #FFFFFF; font-weight: normal; }
.inv_foreground { color: #000000; }
.inv_background { background-color: #AAAAAA; }""", "")
        return html
