#! coding:utf-8
import time

from .logs import dummy_logger, main_logger, utils_logger


class Config:
    """Some global default configs. """
    __slots__ = ()
    #: local timezone for calculating,
    # EAST8 = +8, WEST8 = -8
    TIMEZONE = int(-time.timezone / 3600)
    dummy_logger = dummy_logger
    main_logger = main_logger
    utils_logger = utils_logger
    wait_futures_before_exiting = True
