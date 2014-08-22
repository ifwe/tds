import logging
import os.path
import sys
import yaml
import yaml.parser

import tds.logging_wrapper as log_wrap

from tds.exceptions import ConfigurationError


conf_log_params = ['syslog_facility', 'syslog_priority', ]


def verify_logging_conf_file_info(config_dir):
    """Customized version of verify_conf_file_section() in tds.utils
       to avoid circular dependencies with logging configuration
    """

    try:
        with open(os.path.join(config_dir, 'deploy.yml')) as fh:
            try:
                data = yaml.load(fh.read())
            except yaml.parser.ParserError, e:
                raise ConfigurationError('YAML parse error: %s' % e)
    except IOError, e:
        raise ConfigurationError('Unable to access the configuration file '
                                 '"deploy.yml": %s' % e)

    for param in conf_log_params:
        try:
            data['logging'][param]
        except KeyError:
            raise ConfigurationError('Missing entry "%s" in "logging" '
                                     'section of configuration file '
                                     '"deploy.yml"' % param)

    return [data['logging'][x] for x in conf_log_params]


def configure_logging(config_dir, verbosity, use_color, daemon=False):
    """Configure logging for the application; this will set up
       the initial syslog and console loggers and handlers for
       the application
    """

    sqla_level = logging.WARNING
    log_prefix = True

    if verbosity is None:
        # No prefix or color for normal runs
        level = None
        log_prefix = False
        use_color = False
    elif verbosity == 1:
        level = 10
    elif verbosity == 2:
        level = 5
    else:
        level = 1
        sqla_level = 1   # Ensure SQLAlchemy gives full log info

    syslog_facility, syslog_priority = verify_logging_conf_file_info(config_dir)

    logging.setLoggerClass(log_wrap.Logger)

    logger = logging.getLogger()
    logger.setLevel(1)
    log_wrap.add_syslog(logger, 'syslog',
                        facility=log_wrap.facilities.get(syslog_facility, log_wrap.LOG_LOCAL4),
                        priority=log_wrap.priorities.get(syslog_priority, log_wrap.LOG_DEBUG))

    if not daemon:
        log_wrap.add_stream(logger, 'stderr', stream=sys.stderr,
                            prefix=log_prefix, use_color=use_color)

    tds_logger = logging.getLogger('tds')

    if not daemon:
        log_wrap.add_stream(tds_logger, 'stdout', stream=sys.stdout,
                            level=level, nostderr=True, prefix=log_prefix,
                            use_color=use_color)

    sqla_logger = logging.getLogger('sqlalchemy.engine')
    sqla_logger.setLevel(1)

    if not daemon:
        log_wrap.add_stream(sqla_logger, 'stdout', stream=sys.stdout,
                            level=sqla_level, nostderr=True,
                            prefix=log_prefix, use_color=use_color)

    return tds_logger
