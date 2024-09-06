import os
import sys
import yaml
import logging, logging.handlers
from pathlib import Path

import coloredlogs

FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]  # project root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH

from .constants import Constants
os.makedirs(Constants.LOGS_FOLDER.value, exist_ok=True)

SUCCESS = logging.ERROR + 10
logging.addLevelName(SUCCESS, "SUCCESS")

def success(self, message, *args, **kws):
    # Yes, logger takes its '*args' as 'args'.
    self._log(SUCCESS, message, args, **kws) 

logging.Logger.success = success


file_loc = os.path.join(Constants.LOGS_FOLDER.value, Constants.LOGS_FILE.value)

# Create a ColoredFormatter instance and set color codes
colored_formatter = coloredlogs.ColoredFormatter(
    fmt="%(asctime)s -- %(levelname)s -- %(name)s -- %(funcName)s -- (%(lineno)d) -- %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    level_styles={
        'debug': {'color': 'white'},
        'info': {'color': 'green'},
        'warning': {'color': 'yellow'},
        'success': {'color': 'green', 'bold': True},
        'error': {'color': 'white', 'bold': True, 'background': 'red'}
    },
    field_styles={
        'asctime': {'color': 'white'},
        'levelname': {'color': 'black', 'bold': True},
        'message': {'color': 'white'},
    }
)

def get_logger(name):
    log_level = Constants.LOG_LEVEL.value
    LOGGER = logging.getLogger(name)
    eval("LOGGER.setLevel(logging.{0})".format(log_level))

    # Remove any existing handlers to avoid duplication
    for handler in LOGGER.handlers:
        LOGGER.removeHandler(handler)

    handler_file = logging.handlers.RotatingFileHandler(
        file_loc,
        mode="a",
        maxBytes=10 * 1024 * 1024,
        backupCount=50,
        encoding=None,
        delay=0,
    )

    log_formatter = logging.Formatter(
        "%(asctime)s -- %(levelname)s -- %(name)s -- %(funcName)s -- (%(lineno)d) -- %(message)s"
    )

    handler_file.setFormatter(log_formatter)
    eval("handler_file.setLevel(logging.{0})".format(log_level))

    LOGGER.addHandler(handler_file)

    colored_handler = logging.StreamHandler(sys.stdout)
    
    colored_handler.setFormatter(colored_formatter)
    eval("colored_handler.setLevel(logging.{0})".format(log_level))
    LOGGER.addHandler(colored_handler)
    LOGGER.propagate = False

    return LOGGER
