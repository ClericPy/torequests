#! coding:utf-8
import time


class Config:
    """Some global default configs. """
    __slots__ = ()
    #: local timezone for calculating,
    # EAST8 = +8, WEST8 = -8
    TIMEZONE = int(-time.timezone / 3600)
    wait_futures_before_exiting = True
