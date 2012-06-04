import grp
import os

from tds.exceptions import AccessError

access_levels  = [ 'disabled', 'admin', 'prod', 'stage', 'dev' ]
access_mapping = { 'disabled' : 'root',
                   'admin' : 'siteops',
                   'prod' : 'prodsupportlite',
                   'stage' : 'stagesupport',
                   'dev' : 'engteam', }


def verify_access(access_level):
    """Ensure user has appropriate access"""

    user_groups = [ grp.getgrgid(group).gr_name for group in os.getgroups() ]

    for level in access_levels:
        if access_mapping[level] in user_groups:
            return True

        if level == access_level:
            raise AccessError('Not permitted to access this command')
