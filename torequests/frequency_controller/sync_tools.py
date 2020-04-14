from threading import Lock
from time import sleep, time


class Frequency(object):
    """Frequency controller, means concurrent running n tasks every interval seconds.

        Basic Usage::

            from torequests.frequency_controller.sync_tools import Frequency
            from concurrent.futures import ThreadPoolExecutor
            from time import time

            # limit to 2 concurrent tasks each 1 second
            frequency = Frequency(2, 1)

            def test():
                with frequency:
                    return time()

            now = time()
            pool = ThreadPoolExecutor()
            tasks = []
            for _ in range(5):
                tasks.append(pool.submit(test))
            result = [task.result() for task in tasks]
            assert result[0] - now < 1
            assert result[1] - now < 1
            assert result[2] - now > 1
            assert result[3] - now > 1
            assert result[4] - now > 2
            assert frequency.to_dict() == {'n': 2, 'interval': 1}
            assert frequency.to_list() == [2, 1]
    """
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
        """Return the [self.n, self.interval]"""
        return [self.n, self.interval]

    def to_dict(self):
        """Return the dict {'n': self.n, 'interval': self.interval}"""
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
        """Ensure the given args is Frequency.

        :param frequency: args to create a Frequency instance.
        :type frequency: Frequency / dict / list / tuple
        :return: Frequency instance
        :rtype: Frequency
        """
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
