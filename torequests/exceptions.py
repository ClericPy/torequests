#! coding:utf-8


class CommonException(Exception):
    def __init__(self, name):
        self.name = name

    def __bool__(self):
        return False

    def __nonzero__(self):
        return False

    def __call__(self, *args, **kwargs):
        raise TypeError('%s object is not callable' % repr(self))

    def __str__(self):
        return "%s: %s" % (self.__class__.__name__, self.name)

    def __repr__(self):
        return "%s('%s',)" % (self.__class__.__name__, self.name)


class FailureException(CommonException):
    """This class mainly used for __bool__,
        self.error for reviewing the source exception."""

    def __init__(self, error, name=None):
        self.__dict__ = error.__dict__
        self.error = error
        self.name = self.error.__class__.__name__
        self.ok = False


class ImportErrorModule(CommonException, ImportError):
    """
    This obj will raise error while __call__.
    bool(self) will always be False.
    """
