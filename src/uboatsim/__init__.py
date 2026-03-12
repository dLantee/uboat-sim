"""

"""
import logging
import logging.config

# logging setup
LOG_FORMAT = "(%(asctime)s) %(levelname)s [%(name)s.%(funcName)s]: %(message)s"
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "defaultFormatter": {"format": LOG_FORMAT, "datefmt": "%H:%M:%S"}
    },
    "handlers": {
        "defaultHandler": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "defaultFormatter",
        }
    },
    "loggers": {
        __name__: {
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["defaultHandler"],
        },
    },
}
logging.config.dictConfig(LOG_CONFIG)

LOG = logging.getLogger(__name__)