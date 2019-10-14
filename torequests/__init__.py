#! coding: utf-8
import codecs
import os

from .main import *

__all__ = [
    "Pool",
    "ProcessPool",
    "NewFuture",
    "Async",
    "threads",
    "get_results_generator",
    "run_after_async",
    "tPool",
]
here = os.path.abspath(os.path.dirname(__file__))
with codecs.open(os.path.join(here, '__version__'), encoding="u8") as f:
    __version__ = f.read().strip()
