# -*- coding: utf-8 -*-

from .sync_tools import Frequency

try:
    from .async_tools import Frequency as AsyncFrequency
except SyntaxError:
    # not support python2
    AsyncFrequency = None
