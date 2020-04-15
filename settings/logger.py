import logging
from settings import settings


LOGGER = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'info_fmt': {
            'format': '%(levelname)s: %(message)s',
        },
        'debug_fmt': {
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
