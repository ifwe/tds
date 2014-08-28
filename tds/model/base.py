"""Base module for TDS objects."""
import tagopsdb


class BaseMeta(type):
    """Metaclass for Base to enable delegation of class attributes."""
    def __getattr__(cls, key):
        try:
            return type.__getattribute__(cls, key)
        except AttributeError as e:
            try:
                return getattr(cls.delegate, key)
            except AttributeError:
                raise e

class _Base(object):
    """Base class for Base to absorb all kwds."""

    __metaclass__ = BaseMeta
    delegate = None

    def __init__(self, **_kwds):
        super(_Base, self).__init__()

class Base(_Base):
    """Base class for TDS objects."""

    def __init__(self, **kwds):
        for key, val in kwds.iteritems():
            setattr(self, key, val)

        super(Base, self).__init__(**kwds)

    def __eq__(self, other):
        return self.__dict__.__eq__(other.__dict__)

    def __repr__(self):
        return '<%(class_name)s %(fields_str)s>' % dict(
            class_name=type(self).__name__,
            fields_str=' '.join('%s=%r' % i for i in vars(self).items()),
        )

    def __getattr__(self, key):
        try:
            return super(Base, self).__getattribute__(key)
        except AttributeError as e:
            try:
                return getattr(self.delegate, key)
            except AttributeError:
                raise e

    def delete(self, commit=True, *args, **kwargs):
        """Delete action with default auto-commit."""
        self.delegate.delete(*args, **kwargs)
        if commit:
            tagopsdb.Session.commit()

    @classmethod
    def create(cls, commit=True, **kwargs):
        """Create action with default auto-commit."""
        delegate = cls.delegate(**kwargs)
        tagopsdb.Session.add(delegate)
        self = cls(delegate=delegate)
        if commit:
            tagopsdb.Session.commit()
        return self

    @classmethod
    def get(cls, **kwargs):
        """
        Return one instance of cls with its delegate populated by the same
        get call made to cls's delegate type.

        Returns None if no matching instance is found.
        """
        delegate = cls.delegate.get(**kwargs)
        if delegate is None:
            return None

        return cls(delegate=delegate)

    @classmethod
    def all(cls, **kwargs):
        """
        Return a list of cls instances with each instance's delegate populated
        by an instance of cls's delegate type
        """

        delegates = cls.delegate.all(**kwargs)
        return [cls(delegate=d) for d in delegates]

    @classmethod
    def find(cls, **kwargs):
        """
        Return a list of cls instances with each instance's delegate populated
        by an instance of cls's delegate type matching the provided kwargs
        """

        delegates = cls.delegate.find(**kwargs)
        return [cls(delegate=d) for d in delegates]
