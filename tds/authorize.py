'Utilities for determining authorization level of actors'
import logging

import tds.utils

from tds.exceptions import AccessError

access_levels = ['disabled', 'admin', 'prod', 'stage', 'dev']
access_mapping = {'disabled': 'root',
                  'admin': 'siteops',
                  'prod': 'prodsupportlite',
                  'stage': 'stagesupport',
                  'dev': 'engteam', }

log = logging.getLogger('tds')


@tds.utils.debug
def get_access_level(actor):
    """Find highest access level for user"""

    log.debug('Finding user\'s access level')

    log.log(5, 'User\'s groups are: %s', ', '.join(actor.groups))

    for level in access_levels:
        if access_mapping[level] in actor.groups:
            log.log(5, 'Returning level: %s', level)
            return level

    log.log(5, 'No matching level found for user')
    return None


@tds.utils.debug
def verify_access(user_level, access_level):
    """Ensure user has appropriate access"""

    log.debug('Ensuring user has necessary access')

    if access_levels.index(user_level) > access_levels.index(access_level):
        raise AccessError('Your account does not have the appropriate '
                          'permissions\nto run the requested command.')
