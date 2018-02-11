#! coding:utf-8
import time

from .logs import dummy_logger, main_logger, utils_logger


class Config:
    __slots__ = ()
    # TIMEZONE = 8
    TIMEZONE = int(-time.timezone / 3600)
    dummy_logger = dummy_logger
    main_logger = main_logger
    utils_logger = utils_logger
