# Copyright 2016 Ifwe Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

    def __cmp__(self, other):
        if getattr(other, '__dict__', None) is None:
            return 1

        return self.__dict__.__cmp__(other.__dict__)

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

    def __setattr__(self, key, val):
        if hasattr(self.delegate, key):
            setattr(self.delegate, key, val)
        else:
            _Base.__setattr__(self, key, val)

    def delete(self, commit=True, session=None, *args, **kwargs):
        """Delete action with default auto-commit."""
        self.delegate.delete(*args, **kwargs)
        if commit:
            if session is None:
                tagopsdb.Session.commit()
            else:
                session.commit()

    @classmethod
    def create(cls, commit=True, session=None, **kwargs):
        """Create action with default auto-commit."""
        if session is None:
            session = tagopsdb.Session
        delegate = cls.delegate(**kwargs)
        session.add(delegate)
        self = cls(delegate=delegate)
        if commit:
            session.commit()
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
