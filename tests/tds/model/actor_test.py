'''Tests for the actor model'''

import unittest2

from mock import Mock, patch

import tds.model


class TestActorModel(unittest2.TestCase):
    'Tests for actor model'

    def setUp(self):
        self.actor_properties = {
            'name': 'fake_user',
            'groups': ['fake_group1', 'fake_group2'],
        }

        self.actor = tds.model.Actor(
            self.actor_properties['name'],
            self.actor_properties['groups']
        )

    def tearDown(self):
        pass

    def test_name(self):
        'Ensure "name" property is functional'

        assert self.actor.name == self.actor_properties['name']

    @staticmethod
    def get_group_names(gid):
        'Method to return fake group name for fake gid'
        if gid == 501:
            return Mock(gr_name='fake_group1')
        elif gid == 502:
            return Mock(gr_name='fake_group2')
        else:
            return None

    def test_groups(self):
        'Ensure "groups" property is functional'

        assert self.actor.groups == self.actor_properties['groups']
