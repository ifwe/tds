"""Common utility methods for the TDS application"""

import yaml

from tds.exceptions import ConfigurationError


# Some common basic data
conf_dir = '/etc/tagops'
conf_params = {
    'dbaccess' : {
        'db' : [ 'user', 'password', ],
    },
    'deploy' : {
        'env' : [ 'environment', ],
        'notifications' : [ 'enabled_methods', 'email_receiver',
                            'hipchat_rooms', 'hipchat_token',
                            'validation_time', ],
        'repo' : [ 'build_base', 'incoming', 'processing', ],
    },
}


def load_conf_file(conf_file):
    """Load in the requested YAML configuration file"""

    try:
        with open(conf_file) as fh:
            try:
                return yaml.load(fh.read())
            except yaml.parser.ParserError, e:
                raise ConfigurationError('YAML parse error: %s' % e)
    except IOError, e:
        raise ConfigurationError('Unable to access the configuration file '
                                 '%s: e' % (conf_file, e))


def verify_conf_file_section(cf_name, section, sub_cf_name=None):
    """Ensure the given section in the given configuration file
       is valid and complete and return values
    """

    if sub_cf_name is None:
        conf_file = '%s/%s.yml' % (conf_dir, cf_name)
    else:
        conf_file = '%s/%s.%s.yml' % (conf_dir, cf_name, sub_cf_name)

    data = load_conf_file(conf_file)
    params = conf_params[cf_name][section]

    for param in params:
        try:
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
