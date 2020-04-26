import logging

from colorama import Fore, Style

from settings import settings

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
            "level": settings.loglevel,
            "formatter": "debug_fmt" if settings.loglevel == "DEBUG" else "info_fmt",
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
        "ERROR": Fore.RED,
        "WARNING": Fore.LIGHTYELLOW_EX,
        "INFO": Fore.LIGHTBLUE_EX,
        "DEBUG": Fore.MAGENTA,
    }

    def format(self, record):
        levelname = record.levelname
        record.levelname = self.COLOURS[levelname] + levelname + Style.RESET_ALL
        return logging.Formatter.format(self, record)
