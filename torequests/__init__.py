#! coding: utf-8
import logging
from .main import (Async, NewFuture, Pool, ProcessPool, delete,
                   disable_warnings, get, get_results_generator, head, options,
                   patch, post, put, request, run_after_async, threads, tPool)

__all__ = [
    "Pool", "ProcessPool", "NewFuture", "Async", "threads",
    "get_results_generator", "run_after_async", "tPool", "get", "post",
    "options", "delete", "put", "head", "patch", "request", "disable_warnings"
]
__version__ = '5.1.5'
logging.getLogger("torequests").addHandler(logging.NullHandler())
