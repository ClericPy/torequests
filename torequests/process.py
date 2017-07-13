#! coding:utf-8
from multiprocessing.pool import Pool


class ProcessPool(Pool):

    def __init__(self, n=None, **kwargs):
        super(ProcessPool, self).__init__(n, **kwargs)


if __name__ == '__main__':
    pp = ProcessPool(3)
    print(pp)
    pp.map(print, range(3))
