"""Common utility methods for the TDS application"""

import logging
import sys
import yaml

from tds.exceptions import ConfigurationError


tds_log = logging.getLogger('tds')

# Some common basic data
conf_dir = '/etc/tagops'
conf_params = {
    'dbaccess' : {
        'db' : [ 'user', 'password', ],
    },
    'deploy' : {
        'env' : [ 'environment', ],
        'logging' : [ 'syslog_facility', 'syslog_priority', ],
        'notifications' : [ 'enabled_methods', 'email_receiver',
                            'hipchat_rooms', 'hipchat_token',
                            'validation_time', ],
        'repo' : [ 'build_base', 'incoming', 'processing', ],
    },
}


def debug(f):
    do_depth = 1

    def wrapper(*a, **k):
        name = f.func_name
        filename = f.func_code.co_filename
        line_number = f.func_code.co_firstlineno
        typ = 'function'

        spacer = do_depth * getattr(debug, 'depth', 0) * ' '

        tds_log.log(5, '%(spacer)sEntering %(typ)s %(name)s '
                       '(%(filename)s:%(line_number)s). args=%(a)r, '
                       'kwargs=%(k)r' % locals())

        try:
            setattr(debug, 'depth', getattr(debug, 'depth', 0) + 1)
            return_val = f(*a, **k)
        except BaseException, e:
            tds_log.log(5, '%(spacer)sLeaving %(typ)s %(name)s '
                           '(%(filename)s:%(line_number)s). '
                           'exception=%(e)r', locals())
            raise
        else:
            tds_log.log(5, '%(spacer)sLeaving %(typ)s %(name)s '
                           '(%(filename)s:%(line_number)s). '
                           'returning=%(return_val)r' % locals())
        finally:
            setattr(debug, 'depth', getattr(debug, 'depth', 1) - 1)

        return return_val

    return wrapper


@debug
def load_conf_file(conf_file):
    """Load in the requested YAML configuration file"""

    tds_log.debug('Loading configuration file %r', conf_file)

    try:
        with open(conf_file) as fh:
            try:
                return yaml.load(fh.read())
            except yaml.parser.ParserError, e:
                raise ConfigurationError('YAML parse error: %s' % e)
    except IOError, e:
        raise ConfigurationError('Unable to access the configuration file '
                                 '%s: %s' % (conf_file, e))


@debug
def verify_conf_file_section(cf_name, section, sub_cf_name=None):
    """Ensure the given section in the given configuration file
       is valid and complete and return values
    """

    tds_log.debug('Verifying section %r for configuration %r',
                  section, cf_name)

    if sub_cf_name is None:
        conf_file = '%s/%s.yml' % (conf_dir, cf_name)
    else:
        conf_file = '%s/%s.%s.yml' % (conf_dir, cf_name, sub_cf_name)

    tds_log.debug(5, 'Configuration file is: %s', conf_file)

    data = load_conf_file(conf_file)
    tds_log.debug(5, 'Data is: %r', data)

    params = conf_params[cf_name][section]
    tds_log.debug(5, 'Params are: %s', ', '.join(params))

    for param in params:
        try:
            tds_log.debug(5, 'Checking for parameter %r in section %r',
                          param, section)
            data[section][param]
        except KeyError:
            raise ConfigurationError('Missing entry "%s" in "%s" section '
                                     'of configuration file "%s"'
                                     % (param, section, conf_file))

    # Do not return a list for a single parameter
    if len(params) == 1:
        return data[section][params[0]]
    else:
        return [ data[section][x] for x in params ]
