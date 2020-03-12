#! coding:utf-8
import logging
import os
import sys

from .versions import PY3

if PY3:
    unicode = str


def init_logger(
        name="",
        handler_path_levels=None,
        level=logging.INFO,
        formatter=None,
        formatter_str=None,
        datefmt="%Y-%m-%d %H:%M:%S",
):
    """Add a default handler for logger.

    Args:

    name = '' or logger obj.

    handler_path_levels = [['loggerfile.log',13],['','DEBUG'],['','info'],['','notSet']] # [[path,level]]

    level = the least level for the logger.

    formatter = logging.Formatter(
            '%(levelname)-7s %(asctime)s %(name)s (%(filename)s: %(lineno)s): %(message)s',
             "%Y-%m-%d %H:%M:%S")

    formatter_str = '%(levelname)-7s %(asctime)s  %(name)s (%(funcName)s: %(lineno)s): %(message)s'

    custom formatter:
        %(asctime)s  %(created)f  %(filename)s  %(funcName)s  %(levelname)s  %(levelno)s  %(lineno)s   %(message)s   %(module)s    %(name)s   %(pathname)s   %(process)s   %(relativeCreated)s   %(thread)s  %(threadName)s  
    """
    levels = {
        "NOTSET": logging.NOTSET,
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    if not formatter:
        if formatter_str:
            formatter_str = formatter_str
        else:
            formatter_str = "%(asctime)s %(levelname)-5s [%(name)s] %(filename)s(%(lineno)s): %(message)s"
        formatter = logging.Formatter(formatter_str, datefmt=datefmt)
    logger = name if isinstance(name, logging.Logger) else logging.getLogger(
        str(name))
    logger.setLevel(level)
    handler_path_levels = handler_path_levels or [["", "INFO"]]
    # ---------------------------------------
    for each_handler in handler_path_levels:
        path, handler_level = each_handler
        handler = logging.FileHandler(path) if path else logging.StreamHandler()
        handler.setLevel(
            levels.get(handler_level.upper(), 1
                      ) if isinstance(handler_level, str) else handler_level)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


logger = logging.getLogger('torequests')
dummy_logger = logger
main_logger = logger
utils_logger = logger
print_logger = init_logger(
    "torequests.print",
    formatter_str="[%(asctime)s] %(fn)s(%(ln)s): %(message)s")


def print_info(*messages, **kwargs):
    """Simple print use logger, print with time / file / line_no.
        :param sep: sep of messages, " " by default.

    Basic Usage::

        print_info(1, 2, 3)
        print_info(1, 2, 3)
        print_info(1, 2, 3)

        # [2018-10-24 19:12:16] temp_code.py(7): 1 2 3
        # [2018-10-24 19:12:16] temp_code.py(8): 1 2 3
        # [2018-10-24 19:12:16] temp_code.py(9): 1 2 3
    """
    sep = kwargs.pop("sep", " ")
    frame = sys._getframe(1)
    ln = frame.f_lineno
    _file = frame.f_globals.get("__file__", "")
    fn = os.path.split(_file)[-1]
    return print_logger.info(
        sep.join(map(unicode, messages)), extra={
            "ln": ln,
            "fn": fn
        })
