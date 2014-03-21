'''Tests for authorize module'''

import unittest2

from mock import patch, PropertyMock
from unittest_data_provider import data_provider

import tds.authorize

GROUPS = {
    500: 'invalid_group',
    501: 'engteam',
    502: 'stagesupport',
    503: 'prodsupportlite',
    504: 'siteops',
    505: 'root',
}


def map_level(gr_name):
    'Find access level for a given group'
    for auth_level, group in tds.authorize.access_mapping.iteritems():
        if gr_name == group:
            return auth_level
    else:
        return None

GROUP_PROVIDER = lambda: [
    (gid, map_level(gr_name)) for gid, gr_name in GROUPS.items()
]


class TestAuthorization(unittest2.TestCase):
    'Tests for authorization module'

    def setUp(self):
        pass

    def tearDown(self):
        patch.stopall()

    @data_provider(GROUP_PROVIDER)
    def test_get_access_level(self, gid, auth_level):
        'Ensure proper access level for a given user is retrieved'
        with patch('tds.authorize.Actor.groups',
                   new_callable=PropertyMock) as mock_groups:
            mock_groups.return_value = [GROUPS[gid]]

            assert tds.authorize.get_access_level() == auth_level
