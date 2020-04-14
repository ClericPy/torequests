from asyncio import Lock, sleep
from time import time


class AsyncFrequency(object):
    """AsyncFrequency controller, means concurrent running n tasks every interval seconds.

        Basic Usage::

            from torequests.frequency_controller.async_tools import AsyncFrequency
            from asyncio import ensure_future, get_event_loop
            from time import time


            async def test_async():
                frequency = AsyncFrequency(2, 1)

                async def task():
                    async with frequency:
                        return time()

                now = time()
                tasks = [ensure_future(task()) for _ in range(5)]
                result = [await task for task in tasks]
                assert result[0] - now < 1
                assert result[1] - now < 1
                assert result[2] - now > 1
                assert result[3] - now > 1
                assert result[4] - now > 2
                assert frequency.to_dict() == {'n': 2, 'interval': 1}
                assert frequency.to_list() == [2, 1]

            get_event_loop().run_until_complete(test_async())
    """
    __slots__ = ("gen", "__aenter__", "repr", "_lock", "n", "interval")
    TIMER = time

    def __init__(self, n=None, interval=0):
        self.n = n
        self.interval = interval
        if n:
            self.gen = self.generator(n, interval)
            self._lock = None
            self.__aenter__ = self._acquire
            self.repr = f"AsyncFrequency({n}, {interval})"
        else:
            self.gen = None
            self.__aenter__ = self.__aexit__
            self.repr = "AsyncFrequency(unlimited)"

    def to_list(self):
        """Return the [self.n, self.interval]"""
        return [self.n, self.interval]

    def to_dict(self):
        """Return the dict {'n': self.n, 'interval': self.interval}"""
        return {'n': self.n, 'interval': self.interval}

    @property
    def lock(self):
        # lazy init loop
        if self._lock is None:
            self._lock = Lock()
        return self._lock

    async def generator(self, n, interval):
        q = [0] * n
        while 1:
            for index, i in enumerate(q):
                # or timeit.default_timer()
                now = self.TIMER()
                diff = now - i
                if diff < interval:
                    await sleep(interval - diff)
                now = self.TIMER()
                q[index] = now
                # python3.8+ need lock for generator contest, 3.6 3.7 not need
                yield now

    @classmethod
    def ensure_frequency(cls, frequency):
        """Ensure the given args is AsyncFrequency.

        :param frequency: args to create a AsyncFrequency instance.
        :type frequency: AsyncFrequency / dict / list / tuple
        :return: AsyncFrequency instance
        :rtype: AsyncFrequency
        """
        if isinstance(frequency, cls):
            return frequency
        elif isinstance(frequency, dict):
            return cls(**frequency)
        else:
            return cls(*frequency)

    async def _acquire(self):
        async with self.lock:
            return await self.gen.asend(None)

    async def __aexit__(self, *args):
        pass

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return self.repr

    def __bool__(self):
        return bool(self.gen)
