from asyncio import Lock, sleep
from time import time


class Frequency(object):
    """Frequency controller, means concurrent running n tasks every interval seconds."""
    __slots__ = ("gen", "__aenter__", "repr", "_lock", "n", "interval")
    TIMER = time

    def __init__(self, n=None, interval=0):
        self.n = n
        self.interval = interval
        if n:
            self.gen = self.generator(n, interval)
            self._lock = None
            self.__aenter__ = self._acquire
            self.repr = f"Frequency({n}, {interval})"
        else:
            self.gen = None
            self.__aenter__ = self.__aexit__
            self.repr = "Frequency(unlimited)"

    def to_list(self):
        return [self.n, self.interval]

    def to_dict(self):
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
