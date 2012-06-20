import grp
import os

from tds.exceptions import AccessError

access_levels  = [ 'disabled', 'admin', 'prod', 'stage', 'dev' ]
access_mapping = { 'disabled' : 'root',
                   'admin' : 'siteops',
                   'prod' : 'prodsupportlite',
                   'stage' : 'stagesupport',
                   'dev' : 'engteam', }


def get_access_level():
    """Find highest access level for user"""

    user_groups = [ grp.getgrgid(group).gr_name for group in os.getgroups() ]

    for level in access_levels:
        if access_mapping[level] in user_groups:
            return level
    else:
        return None


def verify_access(user_level, access_level):
    """Ensure user has appropriate access"""

    if access_levels.index(user_level) > access_levels.index(access_level):
        raise AccessError('Not permitted to access this command')
