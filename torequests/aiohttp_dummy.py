# -*- coding: utf-8 -*-

from asyncio import TimeoutError, get_event_loop, sleep
from concurrent.futures._base import Error
from inspect import isawaitable
from typing import Callable, Optional, Union

from aiohttp import ClientError, ClientSession

from ._py3_patch import (NewResponse, NotSet, _ensure_can_be_await,
                         _exhaust_simple_coro, logger)
from .exceptions import FailureException, ValidationError


class Requests:
    """Lite wrapper for aiohttp for better performance.

    Removes the frequency_controller & sync usage (task.x) & compatible args of requests for good performance, but remains retry / callback / referer_info.

    referer_info: sometimes used for callback.
    """

    def __init__(self,
                 session: Optional[ClientSession] = None,
                 catch_exception: bool = True,
                 retry_exceptions: tuple = (ClientError, Error, TimeoutError,
                                            ValidationError),
                 **kwargs):
        # ensure running loop to use unique loop.
        if not get_event_loop().is_running():
            raise RuntimeError('Please init Requests in a running loop.')
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
                      response_validator: Optional[Callable] = None,
                      referer_info=NotSet,
                      encoding=None,
                      **kwargs) -> Union[NewResponse, FailureException]:
        result = await self._request(method=method,
                                     url=url,
                                     retry=retry,
                                     response_validator=response_validator,
                                     referer_info=referer_info,
                                     encoding=encoding,
                                     **kwargs)
        if callback:
            result = callback(result)
            if isawaitable(result):
                return await result
        return result

    async def _request(self,
                       method: str,
                       url: str,
                       retry: int = 0,
                       response_validator: Optional[Callable] = None,
                       referer_info=NotSet,
                       encoding=None,
                       retry_interval = 0,
                       **kwargs):
        error = Exception()
        for retries in range(retry + 1):
            try:
                async with self.session.request(method, url, **kwargs) as resp:
                    if encoding:
                        setattr(resp, 'encoding', encoding)
                    setattr(resp, 'referer_info', referer_info)
                    if response_validator and not await _ensure_can_be_await(
                            response_validator(resp)):
                        raise ValidationError(response_validator.__name__)
                    await resp.read()
                    resp.release()
                    return resp
            except self.retry_exceptions as err:
                error = err
                if retry_interval:
                    await sleep(retry_interval)
                continue
        else:
            logger.debug("Retry %s times failed again: %s." % (retry, error))
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
                  referer_info=NotSet,
                  response_validator: Optional[Callable] = None,
                  **kwargs):
        return await self.request("get",
                                  url=url,
                                  params=params,
                                  retry=retry,
                                  callback=callback,
                                  referer_info=referer_info,
                                  response_validator=response_validator,
                                  **kwargs)

    async def post(self,
                   url: str,
                   data=None,
                   retry: int = 0,
                   callback: Optional[Callable] = None,
                   referer_info=NotSet,
                   response_validator: Optional[Callable] = None,
                   **kwargs):
        return await self.request("post",
                                  url=url,
                                  data=data,
                                  retry=retry,
                                  callback=callback,
                                  referer_info=referer_info,
                                  response_validator=response_validator,
                                  **kwargs)

    async def delete(self,
                     url: str,
                     retry: int = 0,
                     callback: Optional[Callable] = None,
                     referer_info=NotSet,
                     response_validator: Optional[Callable] = None,
                     **kwargs):
        return await self.request("delete",
                                  url=url,
                                  retry=retry,
                                  callback=callback,
                                  referer_info=referer_info,
                                  response_validator=response_validator,
                                  **kwargs)

    async def put(self,
                  url: str,
                  data=None,
                  retry: int = 0,
                  callback: Optional[Callable] = None,
                  referer_info=NotSet,
                  response_validator: Optional[Callable] = None,
                  **kwargs):
        return await self.request("put",
                                  url=url,
                                  data=data,
                                  retry=retry,
                                  callback=callback,
                                  referer_info=referer_info,
                                  response_validator=response_validator,
                                  **kwargs)

    async def head(self,
                   url: str,
                   retry: int = 0,
                   callback: Optional[Callable] = None,
                   referer_info=NotSet,
                   response_validator: Optional[Callable] = None,
                   allow_redirects: bool = False,
                   **kwargs):
        kwargs['allow_redirects'] = allow_redirects
        return await self.request("head",
                                  url=url,
                                  retry=retry,
                                  callback=callback,
                                  referer_info=referer_info,
                                  response_validator=response_validator,
                                  **kwargs)

    async def options(self,
                      url: str,
                      retry: int = 0,
                      callback: Optional[Callable] = None,
                      referer_info=NotSet,
                      response_validator: Optional[Callable] = None,
                      **kwargs):
        return await self.request("options",
                                  url=url,
                                  retry=retry,
                                  callback=callback,
                                  referer_info=referer_info,
                                  response_validator=response_validator,
                                  **kwargs)

    async def patch(self,
                    url: str,
                    retry: int = 0,
                    callback: Optional[Callable] = None,
                    referer_info=NotSet,
                    response_validator: Optional[Callable] = None,
                    **kwargs):
        return await self.request("patch",
                                  url=url,
                                  retry=retry,
                                  callback=callback,
                                  referer_info=referer_info,
                                  response_validator=response_validator,
                                  **kwargs)

    @property
    def closed(self):
        if hasattr(self, 'session'):
            return self.session.closed
        else:
            return True

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
