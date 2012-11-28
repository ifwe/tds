#!/usr/bin/env python

import logging
import logging.handlers
import os
import pwd
import stat
import sys


sysloghandler = logging.handlers.SysLogHandler

# Basic dictionary settings
facilities = {}
for facility in sysloghandler.facility_names.keys():
    if getattr(sysloghandler, 'LOG_%s' % facility.upper(), None) != None:
        facilities[facility] = sysloghandler.facility_names[facility]

priorities = {}
for priority in sysloghandler.priority_names.keys():
    if getattr(sysloghandler, 'LOG_%s' % priority.upper(), None) != None:
        priorities[priority] = sysloghandler.priority_names[priority]

reversePriority = {}
for i in priorities:
    reversePriority[priorities[i]] = i


# Common settings to use in following code
LOG_DAEMON = facilities['daemon']
LOG_LOCAL3 = facilities['local3']

LOG_INFO = priorities['info']
LOG_ERR  = priorities['err']


def _extract_from_dict(dict, key, default=None):
    """Extract a given key from a dictionary.  If the key doesn't exist
       and a default parameter has been set, return that.
    """

    try:
        value = dict[key]
        del dict[key]
    except KeyError:
        value = default

    return value


class Formatter(logging.Formatter):
    """Formatting class used by the logging class to format entries
       similar to the way syslog generates entries
    """

    def __init__(self, *args, **kwargs):
        """Basic initialization"""

        user = _extract_from_dict(kwargs, 'user')
        code = _extract_from_dict(kwargs, 'code')

        logging.Formatter.__init__(self, *args, **kwargs)

        self.set_user(user)
        self.set_code(code)


    def set_user(self, user):
        """Set current user for logging info"""

        if user is None:
            user = pwd.getpwuid(os.getuid())[0]

        self.user = user


    def set_code(self, code):
        """Set code information for logging info"""

        if code is None:
            code = 0

        self.code = code


    def format(self, record):
        """Set format for logging info"""

        if self.user != '':
            record.user = ': %s' % self.user
        else:
            record.user = ''

        if self.code != 0:
            if self.user != '':
                record.code = ':%d' % self.code
            else:
                record.code = ': %d' % self.code
        else:
            record.code = ''

        return logging.Formatter.format(self, record)


class Logger(logging.Logger):
    """Logging class which is implemented as a singleton in order
       to allow the data/methods to be used in multiple modules without
       having to pass down arbitrary attributes to all the modules.
    """

    singleton_object = None


    def __init__(self, name, user=None, code=None):
        """Create singleton Logger object"""

        if self.__class__.singleton_object is not None:
            raise AttributeError('Attempting to create duplicate '
                                 'singleton object')

        logging.Logger.__init__(self, name)

        self.syslog_handlers  = {}
        self.syslog_formatter = None
        self.stream_handlers  = {}
        self.stream_formatter = None

        self.saved_state = []
        self.set_user(user)
        self.set_code(code)

        self.__class__.singleton_object = self


    @classmethod
    def get_object(cls):
        """Class method to return the singleton object"""

        if cls.singleton_object is None:
            raise AttributeError('Singleton object does not yet exist')

        return cls.singleton_object


    def add_syslog(self, fh_name, facility=LOG_DAEMON, priority=LOG_INFO):
        """Set up syslog logging"""

        dev_log = '/dev/log'

        try:
            mode = os.stat(dev_log)[stat.ST_MODE]
        except OSError:
            mode = 0

        # Use /dev/log socket on platforms that have one
        if stat.S_ISSOCK(mode):
            handle = logging.handlers.SysLogHandler(dev_log, facility)
        else:
            handle = logging.handlers.SysLogHandler(facility=facility)

        format = Formatter('%(name)s[%(process)d]%(user)s%(code)s: '
                           '%(levelname)s: %(message)s',
                           user=self.user, code=self.code)

        handle.setFormatter(format)
        handle.encodePriority(facility, priority)

        self.addHandler(handle)
        self.syslog_handlers[fh_name] = handle

        if self.syslog_formatter is None:
            self.syslog_formatter = format


    def delete_syslog(self, fh_name):
        """Remove entry from syslog logging"""

        if fh_name in self.syslog_handlers:
            self.removeHandler(self.syslog_handlers[fh_name])
            del self.syslog_handlers[fh_name]


    def add_stream(self, fh_name, stream=None):
        """Set up stream (stdout and stderr) logging"""

        if stream is None:
            stream = sys.stderr

        handle = logging.StreamHandler(stream)

        format = Formatter('%(asctime)s.%(msecs)03d: '
                           '%(name)s[%(process)d]%(user)s%(code)s: '
                           '%(levelname)s: %(message)s',
                           '%H:%M:%S', user=self.user, code=self.code)

        handle.setFormatter(format)

        if stream == sys.stderr:
            level = logging.ERROR
        else:
            level = logging.INFO

        handle.setLevel(level)

        self.addHandler(handle)
        self.stream_handlers[fh_name] = handle

        if self.stream_formatter is None:
            self.stream_formatter = format


    def delete_stream(self, fh_name):
        """Remove entry from stream (stdout and stderr) logging"""

        if fh_name in self.stream_handlers:
            self.removeHandler(self.stream_handlers[fh_name])
            del self.stream_handlers[fh_name]


    def _update_formatters(self):
        """Update the user and code entries for the formatters"""

        for f in [self.stream_formatter, self.syslog_formatter]:
            if f is not None:
                f.set_user(self.user)
                f.set_code(self.code)


    def set_user(self, user=None):
        """Set user in formatter"""

        self.user = user
        self._update_formatters()


    def set_code(self, code=None):
        """Set code in formatter"""

        self.code = code
        self._update_formatters()


    def push(self, user=None, code=None):
        """Set new values for user and code entries, saving the previous
           values
        """

        self.saved_state.append((self.user, self.code))

        if user is not None:
            self.user = user

        if code is not None:
            self.code = code

        self._update_formatters()


    def pop(self, user=None, code=None):
        """Retrieve the previous values for user and code and set them"""

        self.user, self.code = self.saved_state.pop()
        self._update_formatters()


    def _invoke(self, f, args, kwargs):
        """Call the method passed with the current values for user and code,
           returning them to their previous state once the call is completed
        """

        user = _extract_from_dict(kwargs, 'user', self.user)
        code = _extract_from_dict(kwargs, 'code', self.code)

        self.push(user, code)

        try:
            f(self, *args, **kwargs)
        finally:
            self.pop()


    # Overrides for the various logging methods

    def debug(self, *args, **kwargs):
        self._invoke(logging.Logger.debug, args, kwargs)


    def info(self, *args, **kwargs):
        self._invoke(logging.Logger.info, args, kwargs)


    def notice(self, *args, **kwargs):
        self._invoke(logging.Logger.notice, args, kwargs)


    def warning(self, *args, **kwargs):
        self._invoke(logging.Logger.warning, args, kwargs)


    def error(self, *args, **kwargs):
        self._invoke(logging.Logger.error, args, kwargs)


    def exception(self, *args, **kwargs):
        self._invoke(logging.Logger.exception, args, kwargs)


    def critical(self, *args, **kwargs):
        self._invoke(logging.Logger.critical, args, kwargs)


def create_object(name, user=None, code=None):
    """Create the singleton Support object and return a reference to it.
       Raises an exception if the singleton Support object already exists.
    """

    return Logger(name, user=user, code=code)


def get_object():
    """Get the singleton Support object.  Raises an exception if the
       singleton Support object does not yet exist.
    """

    return Logger.get_object()


if __name__ == "__main__":
    logger = Logger('log_testing')
    logger.add_syslog('syslog_info', facility=LOG_LOCAL3)
    logger.add_syslog('syslog_err', facility=LOG_LOCAL3, priority=LOG_ERR)
    logger.add_stream('stdout', stream=sys.stdout)
    logger.add_stream('stderr', stream=sys.stderr)

    logger.info('This is a test for the info level of logging.')
    logger.error('This is a test for the error level of logging.')
