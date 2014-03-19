'''Tests for the actor model'''

import unittest2

from mock import patch, PropertyMock

import tds.model


class TestActorModel(unittest2.TestCase):
    'Tests for actor model'

    def setUp(self):
        self.actor = tds.model.Actor()

        self.actor_properties = {
            'name': 'fake_user',
            'groups': ['fake_group1', 'fake_group2'],
        }

    def tearDown(self):
        patch.stopall()

    def test_name(self):
        'Ensure "name" property is functional'
        actor_name = patch(
            'tds.model.Actor.name',
            new_callable=PropertyMock
        ).start()
        actor_name.return_value = self.actor_properties['name']

        assert self.actor.name == self.actor_properties['name']

    def test_groups(self):
        'Ensure "groups" property is functional'
        actor_group = patch(
            'tds.model.Actor.groups',
            new_callable=PropertyMock
        ).start()
        actor_group.return_value = self.actor_properties['groups']

        assert self.actor.groups == self.actor_properties['groups']
