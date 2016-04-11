"""
Generate a REST API cookie with the given information and print it to stdout
as a JSON object with information on the generated cookie.
"""

import sys

from os.path import join as opj

import json
import yaml

import tds.utils.config
from tds.views.rest import utils


def generate_cookie(username, address, environment_ids=None, methods=None,
                    eternal=False):
    """
    Generate and return a cookie with the given information.
    username should be the username of the cookie user.
    environment_ids should be an iterable of environment ID restrictions.
    methods should be an iterable of method restrictions.
    wildcard should be whether the cookie will be IP-wildcard.
    eternal should be whether the cookie will have no expiration.
    """
    prepend = ''
    if environment_ids is not None:
        prepend += 'environment_ids={ids}&'.format(
            ids='+'.join(environment_ids),
        )
    if methods is not None:
        prepend += 'methods={methods}&'.format(
            methods='+'.join(methods),
        )
    settings_path = opj(
        tds.utils.config.TDSConfig.default_conf_dir,
        'deploy.yml',
    )
    with open(settings_path) as settings_file:
        settings = yaml.load(settings.file.read())
    cookie_val = utils._create_cookie(
        username,
        address,
        settings,
        False,                          # Risky to generate admin cookies
        prepend,
        eternal,
    )
    env_dict = {'1': 'development', '2': 'staging', '3': 'production'}
    expires = 'never' if eternal else (
        datetime.now() + timedelta(seconds=settings['cookie_life'])
    ).strftime("%Y-%m-%d %H:%M:%S")
    return dict(
        cookie=cookie_val,
        allowedMethods=methods,
        expires=expires,
        allowedEnvironments=[env_dict[env_id] for env_id in environment_ids],
    )


class ArgException(Exception):
    """
    Custom exception for improper CLI arguments.
    """

    def __init__(self, output, *args, **kwargs):
        usage_text = (
            "Usage:\n"
            "\tpython save_cookie.py <username> <address> "
            "[--environment_ids=<environment_ids>] [--methods=<methods>] "
            "[--eternal]\n\n"
            "Arguments:\n"
            "\tusername should be the username for the cookie user.\n"
            "\taddress should be the IP address the cookie is tied to or 'any'"
            "if the generated cookie is to be an IP-wildcard cookie.\n"
            "\tenvironment_ids should be a comma-separated list of "
            "environment ID restrictions.\n"
            "\tmethods should be a comma-separated list of method "
            "restrictions in caps (i.e., 'GET', not 'get').\n"
            "\tUse wildcard to get an IP-wildcard cookie (if authorized).\n"
            "\tUse eternal to get a non-expiring cookie (if authorized)."
        )
        self.output = output + '\n\n' + usage_text
        super(ArgException, self).__init__(self.output, *args, **kwargs)


def parse_command_line(argv):
    """
    Return a dict with the parsed command line arguments or raise an exception
    if unable to parse.
    The returned dict will be compatible with save_cookie as a keyword argument
    dict.
    """
    arg_dict = dict()
    to_remove = list()
    for arg in argv:
        if arg.startswith('--environment_ids='):
            if 'environment_ids' in arg_dict:
                raise ArgException(
                    'ERROR: Encountered --environment_ids twice.'
                )
            to_remove.append(arg)
            env_ids = arg.split('=', 1)[1].split(',')
            for env_id in env_ids:
                try:
                    int(env_id)
                except ValueError:
                    raise ArgException(
                        "ERROR: Could not parse environment ID as int:"
                        " {env_id}.".format(env_id=env_id)
                    )
            arg_dict['environment_ids'] = env_ids
        elif arg.startswith('--methods='):
            if 'methods' in arg_dict:
                raise ArgException('ERROR: Encountered --methods twice.')
            methods = arg.split('=', 1)[1].split(',')
            to_remove.append(arg)
            valid_methods = ('DELETE', 'GET', 'POST', 'PUT')
            for method in methods:
                if method not in valid_methods:
                    raise ArgException(
                        "ERROR: Encountered unknown method {method}. "
                        "Valid_methods: {valid_methods}.".format(
                            method=method,
                            valid_methods=valid_methods,
                        )
                    )
            arg_dict['methods'] = methods
        elif arg == '--eternal':
            if 'eternal' in arg_dict:
                raise ArgException('ERROR: Encountered --eternal twice.')
            arg_dict['eternal'] = bool(arg)
            to_remove.append(arg)
    for arg in to_remove:
        argv.remove(arg)
    if len(argv) != 3:
        raise ArgException('ERROR: got too {desc} arguments.'.format(
            desc='few' if len(argv) < 3 else 'many',
        ))
    arg_dict['username'] = argv[1]
    arg_dict['address'] = argv[2]
    return arg_dict


if __name__ == '__main__':
    try:
        args = parse_command_line(sys.argv)
    except ArgException, exc:
        raise exc
    else:
        print json.dumps(generate_cookie(**args))
