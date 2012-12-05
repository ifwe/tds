#!/usr/bin/env python

import logging
import logging.handlers
import os
import pwd
import stat
import sys

from tds.UTFFixedSysLogHandler import UTFFixedSysLogHandler

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

# Extend DEBUG settings for level
for idx in xrange(1, 11):
    logging.addLevelName(idx, 'DEBUG')

# Common settings to use in following code
LOG_DAEMON = facilities['daemon']
LOG_LOCAL3 = facilities['local3']
LOG_LOCAL4 = facilities['local4']

LOG_DEBUG = priorities['debug']
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
            f = handler.formatter

            if f is not None:
                f.set_user(self.user)
                f.set_code(self.code)


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


    def pop(self, user=None, code=None):
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

    try:
        mode = os.stat(dev_log)[stat.ST_MODE]
    except OSError:
        mode = 0

    # Use /dev/log socket on platforms that have one
    if stat.S_ISSOCK(mode):
        handle = UTFFixedSysLogHandler(dev_log, facility)
    else:
        handle = UTFFixedSysLogHandler(facility=facility)

    format = Formatter('%(name)s[%(process)d]%(user)s%(code)s: '
                       '%(levelname)s: %(message)s',
                       user=getattr(logger, 'user', 'unknown-user'),
                       code=getattr(logger, 'code', 0))

    handle.setFormatter(format)
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
               syslog_format=False):
    """Set up stream (stdout and stderr) logging"""

    if stream is None:
        stream = sys.stderr

    handle = logging.StreamHandler(stream)

    if syslog_format:
        format = Formatter('%(asctime)s.%(msecs)03d: '
                           '%(name)s[%(process)d]%(user)s %(code)s: '
                           '%(levelname)s: %(message)s',
                           '%H:%M:%S',
                           user=getattr(logger, 'user', 'unknown-user'),
                           code=getattr(logger, 'code', 0))
    else:
        format = Formatter('%(message)s',
                           user=getattr(logger, 'user', 'unknown-user'),
                           code=getattr(logger, 'code', 0))

    handle.setFormatter(format)

    if level is None:
        if stream == sys.stderr:
            level = logging.ERROR
        else:
            level = logging.INFO

    handle.setLevel(level)

    if nostderr:
        filter = MaxLevelFilter(logging.WARNING)
        handle.addFilter(filter)

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


if __name__ == "__main__":
    logger = Logger('log_testing')
    logger.add_syslog('syslog_info', facility=LOG_LOCAL3)
    logger.add_syslog('syslog_err', facility=LOG_LOCAL3, priority=LOG_ERR)
    logger.add_stream('stdout', stream=sys.stdout, nostderr=True)
    logger.add_stream('stderr', stream=sys.stderr)

    logger.info('This is a test for the info level of logging.')
    logger.error('This is a test for the error level of logging.')

    # Uncomment below to test multiple log levels
    #logger.add_syslog('syslog_err', facility=LOG_LOCAL4, priority=LOG_DEBUG)

    #for idx in xrange(0, 10):
    #    logger.debug(idx, 'This is log level %d', logging.DEBUG - idx)
