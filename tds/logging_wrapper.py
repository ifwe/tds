#!/usr/bin/env python

"""
Wrapper around different logging facilities.
"""

import logging
import logging.handlers
import os
import pwd
import stat
import sys

try:
    from tds.UTFFixedSysLogHandler import UTFFixedSysLogHandler
except ImportError:
    from UTFFixedSysLogHandler import UTFFixedSysLogHandler


def _create_facilities(handler, facilities=dict()):
    """Initialize a facilities dictionary."""
    for facility in handler.facility_names.keys():
        if getattr(handler, 'LOG_%s' % facility.upper(), None) is not None:
            facilities[facility] = handler.facility_names[facility]
    return facilities


def _create_priorities(handler, priorities=dict()):
    """Initialize a priorities dictionary."""
    for priority in handler.priority_names.keys():
        if getattr(handler, 'LOG_%s' % priority.upper(), None) is not None:
            priorities[priority] = handler.priority_names[priority]
    return priorities


def _add_log_levels():
    """Add debug logging level names."""
    for idx in xrange(1, 11):
        logging.addLevelName(idx, 'DEBUG')


SYSLOGHANDLER = logging.handlers.SysLogHandler

# Basic dictionary settings
FACILITIES = _create_facilities(SYSLOGHANDLER)
PRIORITIES = _create_priorities(SYSLOGHANDLER)

# Extend DEBUG settings for level
_add_log_levels()

# Common settings to use in following code
LOG_DAEMON = FACILITIES['daemon']
LOG_LOCAL3 = FACILITIES['local3']
LOG_LOCAL4 = FACILITIES['local4']

LOG_DEBUG = PRIORITIES['debug']
LOG_INFO = PRIORITIES['info']
LOG_ERR = PRIORITIES['err']


def _extract_from_dict(dictionary, key, default=None):
    """Extract a given key from a dictionary.  If the key doesn't exist
       and a default parameter has been set, return that.
    """

    try:
        value = dictionary[key]
        del dictionary[key]
    except KeyError:
        value = default

    return value


class ColorCodes(object):
    """A simple class to help add color to the logging output (to be
       used for stream handlers, not syslog handlers!) by setting up
       attributes to use for setting ANSI escape sequences and mapping
       them to the various logging levels
    """

    END = '\033[0m'   # Turn off color
    RED = '\033[1;31m'
    GREEN = '\033[1;32m'
    YELLOW = '\033[1;33m'
    PURPLE = '\033[1;35m'
    CYAN = '\033[1;36m'

    c_map = {
        'DEBUG': CYAN,
        'INFO': GREEN,
        'WARNING': YELLOW,
        'ERROR': RED,
        'CRITICAL': PURPLE,
    }


class MaxLevelFilter(logging.Filter):
    """Setting a 'maximum' level to log at, allows to set a logging
       'range' for a given handler (e.g. stdout not showing stderr
       messages)
    """

    def __init__(self, level):
        """Set maximum level"""

        self._level = level

    def filter(self, record):
        """Message is filtered if it's above specified level"""

        return record.levelno <= self._level


class Formatter(logging.Formatter):
    """Formatting class used by the logging class to format entries
       similar to the way syslog generates entries
    """

    def __init__(self, *args, **kwargs):
        """Basic initialization"""

        use_color = _extract_from_dict(kwargs, 'use_color')
        user = _extract_from_dict(kwargs, 'user')
        code = _extract_from_dict(kwargs, 'code')

        logging.Formatter.__init__(self, *args, **kwargs)

        self.set_user(user)
        self.set_code(code)

        self.use_color = use_color

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

        # Set color
        color_codes = ColorCodes()
        levelname = record.levelname

        if self.use_color and levelname in color_codes.c_map.keys():
            level_color = color_codes.c_map[levelname]
            message = logging.Formatter.format(self, record)
            message = level_color + message + color_codes.END
        else:
            message = logging.Formatter.format(self, record)

        return message


class Logger(logging.Logger, object):
    """Customized Logger object for the logging module"""

    user = None
    code = None
    saved_state = []

    def __init__(self, name, user=None, code=None):
        """Basic configuration"""

        logging.Logger.__init__(self, name)

        if user is None:
            user = self.user

        if code is None:
            user = self.code

        self.set_user(user)
        self.set_code(code)

    def _update_formatters(self):
        """Update the user and code entries for the formatters"""

        for handler in (getattr(self, 'stream_handlers', {}).values() +
                        getattr(self, 'syslog_handlers', {}).values()):
            if handler.formatter is not None:
                handler.formatter.set_user(self.user)
                handler.formatter.set_code(self.code)

    def set_user(self, user=None):
        """Set user in formatter"""

        cls = type(self)
        cls.user = user
        self._update_formatters()

    def set_code(self, code=None):
        """Set code in formatter"""

        cls = type(self)
        cls.code = code
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

    def pop(self, *_args, **_kwargs):
        """Retrieve the previous values for user and code and set them"""

        self.user, self.code = self.saved_state.pop()
        self._update_formatters()

    def log(self, *args, **kwargs):
        """Call the method passed with the current values for user and code,
           returning them to their previous state once the call is completed
        """

        user = _extract_from_dict(kwargs, 'user', self.user)
        code = _extract_from_dict(kwargs, 'code', self.code)

        self.push(user, code)

        try:
            logging.Logger.log(self, *args, **kwargs)
        finally:
            self.pop()

    # Allow for multiple debug levels
    def debug(self, level, *args, **kwargs):
        try:
            int(level)
        except ValueError:
            # This allows 'level' to be optional
            args = (level,) + args
            level = 0

        self.log(logging.DEBUG - level, *args, **kwargs)


    #def filter(self, record):
    #    should_filter = logging.Logger.filter(self, record)
    #    if should_filter:
    #        print "Filtering from %s at level %d" % (record.name,
    #                                                 record.levelno)
    #    return should_filter


def add_syslog(logger, fh_name, facility=LOG_DAEMON, priority=LOG_INFO):
    """Set up syslog logging"""

    dev_log = '/dev/log'

    if sys.platform.startswith('darwin'):
        dev_log = '/var/run/syslog'

    try:
        mode = os.stat(dev_log).st_mode
    except OSError:
        mode = 0

    # Use /dev/log socket on platforms that have one
    if stat.S_ISSOCK(mode):
        handle = UTFFixedSysLogHandler(dev_log, facility)
    else:
        handle = UTFFixedSysLogHandler(facility=facility)

    handle.setFormatter(Formatter('%(name)s[%(process)d]%(user)s%(code)s: '
                                  '%(levelname)s: %(message)s',
                                  use_color=False,
                                  user=getattr(logger, 'user', None),
                                  code=getattr(logger, 'code', None)))
    handle.encodePriority(facility, priority)

    logger.addHandler(handle)

    if getattr(logger, 'syslog_handlers', None) is None:
        logger.syslog_handlers = {}

    logger.syslog_handlers[fh_name] = handle


def delete_syslog(logger, fh_name):
    """Remove entry from syslog logging"""

    if getattr(logger, 'syslog_handlers', None) is None:
        return

    if fh_name in logger.syslog_handlers:
        logger.removeHandler(logger.syslog_handlers[fh_name])
        logger.syslog_handlers.pop(fh_name, None)


def add_stream(logger, fh_name, stream=None, level=None, nostderr=False,
               syslog_format=False, prefix=False, use_color=False):
    """Set up stream (stdout and stderr) logging"""

    if stream is None:
        stream = sys.stderr

    handle = logging.StreamHandler(stream)

    if syslog_format:
        format_string = ('%(asctime)s.%(msecs)03d: '
                         '%(name)s[%(process)d]%(user)s %(code)s: '
                         '%(levelname)s: %(message)s',
                         '%H:%M:%S')
    else:
        format_string = '%(message)s'

        if prefix:
            format_string = '[%(levelname)s] ' + format_string

    handle.setFormatter(Formatter(format_string, use_color=use_color,
                                  user=getattr(logger, 'user', None),
                                  code=getattr(logger, 'code', None)))

    if level is None:
        if stream == sys.stderr:
            level = logging.ERROR
        else:
            level = logging.INFO

    handle.setLevel(level)

    if nostderr:
        handle.addFilter(MaxLevelFilter(logging.WARNING))

    logger.addHandler(handle)

    if getattr(logger, 'stream_handlers', None) is None:
        logger.stream_handlers = {}

    logger.stream_handlers[fh_name] = handle


def delete_stream(logger, fh_name):
    """Remove entry from stream (stdout and stderr) logging"""

    if getattr(logger, 'stream_handlers', None) is None:
        return

    if fh_name in logger.stream_handlers:
        logger.removeHandler(logger.stream_handlers[fh_name])
        logger.stream_handlers.pop(fh_name, None)


def main():
    """Initialize things."""
    prefix = False   # Set to True for streams to have log level prefix

    logger = Logger('log_testing')
    add_syslog(logger, 'syslog_info', facility=LOG_LOCAL3)
    add_syslog(logger, 'syslog_err', facility=LOG_LOCAL3, priority=LOG_ERR)
    add_stream(logger, 'stdout', stream=sys.stdout, nostderr=True,
               prefix=prefix)
    add_stream(logger, 'stderr', stream=sys.stderr, prefix=prefix)

    logger.info('This is a test for the info level of logging.')
    logger.error('This is a test for the error level of logging.')

    # Uncomment below to test multiple log levels
    #add_syslog(logger, 'syslog_err', facility=LOG_LOCAL3, priority=LOG_DEBUG)

    #for idx in xrange(0, 10):
    #    logger.debug(idx, 'This is log level %d', logging.DEBUG - idx)


if __name__ == "__main__":
    main()
