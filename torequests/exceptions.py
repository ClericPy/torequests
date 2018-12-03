#! coding:utf-8


class CommonException(Exception):
    """This Exception mainly used for `bool(self) is False`, and not `callable`."""

    def __init__(self, name):
        self.name = name

    def __bool__(self):
        return False

    def __nonzero__(self):
        return False

    def __call__(self, *args, **kwargs):
        raise TypeError("%s object is not callable" % repr(self))

    def __str__(self):
        return "%s: %s" % (self.__class__.__name__, self.name)

    def __repr__(self):
        return "%s('%s',)" % (self.__class__.__name__, self.name)


class FailureException(CommonException):
    """Use `self.error` to review the origin exception."""

    def __new__(cls, error, name=None):
        if isinstance(error, cls):
            return error
        else:
            return super(FailureException, cls).__new__(cls, error, name=name)

    def __init__(self, error, name=None):
        if isinstance(error, self.__class__):
            error = error.error
        self.__dict__ = error.__dict__
        self.error = error
        self.name = name or self.error.__class__.__name__
        self.ok = False

    def __str__(self):
        return "%s: %s%s" % (
            self.__class__.__name__,
            self.name,
            getattr(self.error, "args", ""),
        )

    def __repr__(self):
        return "<FailureException [%s]>" % (self.name)

    @property
    def text(self):
        return str(self)


class ImportErrorModule(CommonException, ImportError):
    pass
