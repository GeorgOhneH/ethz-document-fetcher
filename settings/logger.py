import copy
import datetime
import logging
import os
import sys

from PyQt5.QtCore import *
from colorama import Fore, Style

import core.utils


def setup_logger(loglevel):
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    loglevel = loglevel if loglevel in ["ERROR", "WARNING", "INFO", "DEBUG"] else "INFO"

    basic_format_string = "%(levelname)s: %(message)s"
    debug_format_string = "%(levelname)s: %(asctime)s - %(name)s - %(message)s"
    console_basic_fmt = AnsiColouredFormatter(basic_format_string)
    console_debug_fmt = AnsiColouredFormatter(debug_format_string)

    console = ExcInfoStreamHandler(stream=sys.stdout)
    console.setLevel(loglevel)
    console.setFormatter(console_debug_fmt if loglevel == "DEBUG" else console_basic_fmt)

    log_path = os.path.join(core.utils.get_logs_path(), datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S") + ".log")
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel("DEBUG")
    file_handler.setFormatter(logging.Formatter(debug_format_string))

    root.addHandler(console)
    root.addHandler(file_handler)


class ExcInfoStreamHandler(logging.StreamHandler):
    def emit(self, record: logging.LogRecord) -> None:
        copy_record = copy.copy(record)
        super().emit(copy_record)


class AnsiColouredFormatter(logging.Formatter):
    COLOURS = {
        "CRITICAL": Fore.RED,
        "ERROR": Fore.RED,
        "WARNING": Fore.LIGHTYELLOW_EX,
        "INFO": Fore.LIGHTBLUE_EX,
        "DEBUG": Fore.MAGENTA,
    }

    def format(self, record):
        levelname = record.levelname
        copy_record = copy.copy(record)
        copy_record.levelname = self.COLOURS[levelname] + levelname + Style.RESET_ALL
        return super().format(copy_record)


class QtHandler(QObject, logging.Handler):
    new_record = pyqtSignal(object)

    def __init__(self, parent):
        super().__init__(parent)
        super(logging.Handler).__init__()
        formatter = HtmlColourFormatter("%(levelname)s: %(asctime)s - %(name)s - %(message)s")
        self.setFormatter(formatter)

    def emit(self, record):
        msg = self.format(record)

        for line in msg.split("\n"):
            white_space_count = 0
            while line and line[0] == " ":
                line = line[1:]
                white_space_count += 1

            if white_space_count != 0:
                line = ("&nbsp;" * white_space_count) + line
            try:
                self.new_record.emit(line)
            except RuntimeError:
                # if the app closes and we still send lines, we get a runtime error
                pass


class HtmlColourFormatter(logging.Formatter):
    COLOURS = {
        "CRITICAL": "red",
        "ERROR": "red",
        "WARNING": "Orange",
        "INFO": "#1a75ff",
        "DEBUG": "magenta",
    }

    def format(self, record):
        levelname = record.levelname
        copy_record = copy.copy(record)
        copy_record.levelname = f"""<span style="color:{self.COLOURS[levelname]};">{copy_record.levelname}</span>"""
        return super().format(copy_record)
