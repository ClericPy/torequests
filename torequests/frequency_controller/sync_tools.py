from threading import Lock
from time import sleep, time


class Frequency(object):
    """Frequency controller, means concurrent running n tasks every interval seconds."""
    __slots__ = ("gen", "repr", "lock", "__enter__", "n", "interval")
    TIMER = time

    def __init__(self, n=None, interval=0):
        self.n = n
        self.interval = interval
        self.repr = "Frequency({n}, {interval})".format(n=n, interval=interval)
        if n:
            self.lock = Lock()
            # generator is a little faster than Queue, and using little memory
            self.gen = self.generator(n, interval)
            self.__enter__ = self._acquire
        else:
            self.gen = None
            self.__enter__ = self.__exit__

    def to_list(self):
        return [self.n, self.interval]

    def to_dict(self):
        return {'n': self.n, 'interval': self.interval}

    def generator(self, n=2, interval=1):
        q = [0] * n
        while 1:
            for index, i in enumerate(q):
                # or timeit.default_timer()
                now = self.TIMER()
                diff = now - i
                if diff < interval:
                    sleep(interval - diff)
                now = self.TIMER()
                q[index] = now
                yield now

    @classmethod
    def ensure_frequency(cls, frequency):
        if isinstance(frequency, cls):
            return frequency
        elif isinstance(frequency, dict):
            return cls(**frequency)
        else:
            return cls(*frequency)

    def _acquire(self):
        with self.lock:
            return next(self.gen)

    def __exit__(self, *args):
        pass

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return self.repr

    def __bool__(self):
        return bool(self.gen)
