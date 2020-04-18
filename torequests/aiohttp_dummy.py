# -*- coding: utf-8 -*-

from asyncio import get_event_loop
from concurrent.futures._base import Error
from inspect import isawaitable
from typing import Callable, Optional, Union

from aiohttp import ClientError, ClientSession

from ._py3_patch import NewResponse, NotSet, _exhaust_simple_coro, logger
from .exceptions import FailureException


class Requests:
    """Lite wrapper for aiohttp for better performance.

    Include:

        - retry
        - callback
        - referer_info

    Exclude:

        - frequency_controller
        - sync usage (r.x)
    """

    def __init__(self,
                 session: Optional[ClientSession] = None,
                 catch_exception: bool = True,
                 retry_exceptions: tuple = (ClientError, Error),
                 **kwargs):
        # ensure running loop to use unique loop.
        if not get_event_loop().is_running():
            raise RuntimeError('Please init Requests in running loop.')
        self.catch_exception = catch_exception
        self.retry_exceptions = retry_exceptions
        if session:
            self.session = session
        else:
            self.session = ClientSession(**kwargs)
        self.session._response_class = NewResponse

    async def request(self,
                      method: str,
                      url: str,
                      retry: int = 0,
                      callback: Optional[Callable] = None,
                      **kwargs) -> Union[NewResponse, FailureException]:
        result = await self._request(method=method,
                                     url=url,
                                     retry=retry,
                                     **kwargs)
        if callback:
            result = callback(result)
            if isawaitable(result):
                return await result
        return result

    async def _request(self, method: str, url: str, retry: int = 0, **kwargs):
        if "verify" in kwargs:
            kwargs["ssl"] = kwargs.pop('verify')
        if "proxies" in kwargs:
            # only support http proxy
            kwargs["proxy"] = "http://%s" % kwargs.pop('proxies').popitem()[1]
        encoding = kwargs.pop("encoding", None)
        referer_info = kwargs.pop("referer_info", NotSet)
        for retries in range(retry + 1):
            try:
                async with self.session.request(method, url, **kwargs) as resp:
                    if encoding:
                        setattr(resp, 'encoding', encoding)
                    if referer_info is not NotSet:
                        setattr(resp, 'referer_info', referer_info)
                    await resp.read()
                    resp.release()
                    return resp
            except self.retry_exceptions as err:
                error = err
                continue
        else:
            logger.debug("Retry %s & failed: %s." % (retry, error))
            failure = FailureException(error)
            if self.catch_exception:
                return failure
            else:
                raise failure

    async def get(self,
                  url: str,
                  params: Optional[dict] = None,
                  retry: int = 0,
                  callback: Optional[Callable] = None,
                  **kwargs):
        return await self.request("get",
                                  url=url,
                                  params=params,
                                  retry=retry,
                                  callback=callback,
                                  **kwargs)

    async def post(self,
                   url: str,
                   data=None,
                   retry: int = 0,
                   callback: Optional[Callable] = None,
                   **kwargs):
        return await self.request("post",
                                  url=url,
                                  data=data,
                                  retry=retry,
                                  callback=callback,
                                  **kwargs)

    async def delete(self,
                     url: str,
                     retry: int = 0,
                     callback: Optional[Callable] = None,
                     **kwargs):
        return await self.request("delete",
                                  url=url,
                                  retry=retry,
                                  callback=callback,
                                  **kwargs)

    async def put(self,
                  url: str,
                  data=None,
                  retry: int = 0,
                  callback: Optional[Callable] = None,
                  **kwargs):
        return await self.request("put",
                                  url=url,
                                  data=data,
                                  retry=retry,
                                  callback=callback,
                                  **kwargs)

    async def head(self,
                   url: str,
                   retry: int = 0,
                   callback: Optional[Callable] = None,
                   **kwargs):
        return await self.request("head",
                                  url=url,
                                  retry=retry,
                                  callback=callback,
                                  **kwargs)

    async def options(self,
                      url: str,
                      retry: int = 0,
                      callback: Optional[Callable] = None,
                      **kwargs):
        return await self.request("options",
                                  url=url,
                                  retry=retry,
                                  callback=callback,
                                  **kwargs)

    async def patch(self,
                    url: str,
                    retry: int = 0,
                    callback: Optional[Callable] = None,
                    **kwargs):
        return await self.request("patch",
                                  url=url,
                                  retry=retry,
                                  callback=callback,
                                  **kwargs)

    @property
    def closed(self):
        return self.session.closed

    async def close(self):
        if self.closed:
            return True
        try:
            return await self.session.close()
        except Exception as e:
            logger.error("can not close session for: %s" % e)

    def __del__(self):
        _exhaust_simple_coro(self.close())

    def __enter__(self):
        return self

    def __exit__(self, *args):
        _exhaust_simple_coro(self.close())

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
