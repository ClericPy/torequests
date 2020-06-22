#! coding:utf-8
import logging
import logging.handlers
import os
import sys

from .versions import PY3

if PY3:
    unicode = str

formatter_str_styles = [
    "%(asctime)s %(levelname)-5s [%(name)s] %(filename)s(%(lineno)s): %(message)s",
    "%(asctime)s | %(levelname)-5s | %(filename)s(%(lineno)s):%(funcName)s | %(name)s: %(message)s",
    "%(asctime)s | %(levelname)-5s | %(filename)s(%(lineno)s) | %(name)s: %(message)s",
    "%(asctime)s | %(levelname)-5s | %(name)s | %(filename)s(%(lineno)s): %(message)s",
    "%(asctime)s | %(levelname)-5s | %(name)s | %(funcName)s(%(lineno)s): %(message)s",
]


def init_logger(name=None,
                handler_path_levels=None,
                level=logging.INFO,
                formatter=None,
                formatter_str=0,
                datefmt="%Y-%m-%d %H:%M:%S",
                encoding="utf-8",
                file_handler_class=None,
                shorten_level_names=False,
                **file_handler_kwargs):
    """Add a default handler for logger.

    Args::

        name = string or logger obj.

        handler_path_levels = [['loggerfile.log',13],['','DEBUG'],['','info'],['','notSet']] # [[path,level]]

        level = the least level for the logger.

        formatter = logging.Formatter(
                '%(levelname)-7s %(asctime)s %(name)s (%(filename)s: %(lineno)s): %(message)s',
                "%Y-%m-%d %H:%M:%S")

        formatter_str string like '%(levelname)-7s %(asctime)s  %(name)s (%(funcName)s: %(lineno)s): %(message)s', or int index to get from formatter_str_styles

        custom formatter:
            %(asctime)s  %(created)f  %(filename)s  %(funcName)s  %(levelname)s  %(levelno)s  %(lineno)s   %(message)s   %(module)s    %(name)s   %(pathname)s   %(process)s   %(relativeCreated)s   %(thread)s  %(threadName)s

        encoding: encoding for FileHandlers
        file_handler_class: FileHandlers / RotatingFileHandler / TimedRotatingFileHandler, default to FileHandlers.
        file_handler_kwargs: init kwargs for file_handler_class, such as when / interval / backupCount / maxBytes.

    Demo::

        # RotatingFileHandler
        logger = init_logger(
            '',
            [['info.log', 'info']],
            file_handler_class='size',
            maxBytes=10 * 1024 * 1024,
            backupCount=2,
        )
        logger.info('test')
        logger.info('test')
        # RotatingFileHandler
        logger = init_logger(
            '',
            [['info.log', 'info']],
            file_handler_class='time',
            when='D',
            interval=1,
            backupCount=7,
        )
        logger.info('test')
        logger.info('test')

    """
    if shorten_level_names:
        logging.addLevelName(logging.WARNING, 'WARN')
        logging.addLevelName(logging.CRITICAL, 'FATAL')
    if file_handler_class is None:
        file_handler_class = logging.FileHandler
    elif isinstance(file_handler_class, unicode):
        alias_names = {
            'size': 'RotatingFileHandler',
            'time': 'TimedRotatingFileHandler',
        }
        file_handler_class = alias_names.get(file_handler_class,
                                             file_handler_class)
        file_handler_class = getattr(
            logging, file_handler_class,
            getattr(logging.handlers, file_handler_class))
    if not file_handler_class:
        raise NameError('invalid file_handler_class %s' % file_handler_class)
    if 'encoding' in file_handler_kwargs:
        encoding = file_handler_kwargs.pop('encoding')
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
            if isinstance(formatter_str, unicode):
                formatter_str = formatter_str
            elif isinstance(formatter_str, int):
                formatter_str = formatter_str_styles[formatter_str]
            else:
                formatter_str = formatter_str_styles[0]
        else:
            formatter_str = formatter_str_styles[0]
        formatter = logging.Formatter(formatter_str, datefmt=datefmt)
    if isinstance(name, logging.Logger):
        logger = logging.getLogger(name.name)
    else:
        logger = logging.getLogger(unicode(name))
    logger.setLevel(level)
    handler_path_levels = handler_path_levels or [["", level]]
    # ---------------------------------------
    for each_handler in handler_path_levels:
        if isinstance(each_handler, logging.Handler):
            logger.addHandler(each_handler)
        else:
            path, handler_level = each_handler
            if path:
                handler = file_handler_class(path,
                                             encoding=encoding,
                                             **file_handler_kwargs)
            else:
                handler = logging.StreamHandler()
            _level = levels.get(handler_level.upper(), 1) if isinstance(
                handler_level, str) else handler_level
            handler.setLevel(_level)
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
    return print_logger.info(sep.join(map(unicode, messages)),
                             extra={
                                 "ln": ln,
                                 "fn": fn
                             })
