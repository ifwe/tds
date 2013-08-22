import grp
import logging
import os

import tds.utils

from tds.exceptions import AccessError

access_levels  = [ 'disabled', 'admin', 'prod', 'stage', 'dev' ]
access_mapping = { 'disabled' : 'root',
                   'admin' : 'siteops',
                   'prod' : 'prodsupportlite',
                   'stage' : 'stagesupport',
                   'dev' : 'engteam', }

tds_log = logging.getLogger('tds')


@tds.utils.debug
def get_access_level():
    """Find highest access level for user"""

    tds_log.debug('Finding user\'s access level')

    user_groups = [ grp.getgrgid(group).gr_name for group in os.getgroups() ]
    tds_log.debug(5, 'User\'s groups are: %s', ', '.join(user_groups))

    for level in access_levels:
        if access_mapping[level] in user_groups:
            tds_log.debug(5, 'Returning level: %s', level)
            return level
    else:
        tds_log.debug(5, 'No matching level found for user')
        return None


@tds.utils.debug
def verify_access(user_level, access_level):
    """Ensure user has appropriate access"""

    tds_log.debug('Ensuring user has necessary access')

    if access_levels.index(user_level) > access_levels.index(access_level):
        raise AccessError('Your account does not have the appropriate '
                          'permissions\nto run the requested command.')
