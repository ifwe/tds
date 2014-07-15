from mock import patch, Mock
from unittest_data_provider import data_provider

import unittest2
import tds.notifications.base as base

from tests.factories.utils.config import DeployConfigFactory
from tests.factories.model.deployment import (
    DeploymentFactory,
    UnvalidatedDeploymentFactory,
    HostDeploymentFactory,
    AllApptypesDeploymentFactory,
)

APP_CONFIG = DeployConfigFactory()


class TestNotifications(unittest2.TestCase):

    def setUp(self):
        self.config = APP_CONFIG['notifications']

    def create_notification(self):
        return base.Notifications(APP_CONFIG)

    def test_constructor(self):
        n = self.create_notification()

        assert n.config == self.config
        assert n.enabled_methods == self.config['enabled_methods']
        assert n.validation_time == self.config['validation_time']

    @patch('tds.notifications.mail.EmailNotifier', autospec=True)
    @patch('tds.notifications.hipchat.HipchatNotifier', autospec=True)
    def test_send_notifications(self, hipchat, email):
        n = self.create_notification()

        notifiers = {
            'email': email,
            'hipchat': hipchat
        }

        deployment = DeploymentFactory()
        with patch.object(n, '_notifiers', notifiers):
            n.notify(deployment)

            for mock in notifiers.values():
                mock.return_value.notify.assert_called_with(deployment)


class TestNotifierClass(unittest2.TestCase):
    def test_send(self):
        n = base.Notifier({}, {})
        self.assertRaises(
            NotImplementedError,
            n.notify,
            deployment=object()
        )

    deployment_factory_provider = lambda *a: [
        (
            DeploymentFactory,
            'Promote of version badf00d of fake_package on app tier(s)'
            ' fake_apptype in fakedev',
            'fake_user performed a "tds deploy promote" for the following app'
            ' tier(s) in fakedev:\n'
            '    fake_apptype'
        ),
        (
            HostDeploymentFactory,
            'Promote of version badf00d of fake_package on hosts'
            ' whatever.example.com in fakedev',
            'fake_user performed a "tds deploy promote" for the following'
            ' hosts in fakedev:\n'
            '    whatever.example.com'
        ),
        (
            AllApptypesDeploymentFactory,
            'Promote of version badf00d of fake_package on app tier(s)'
            ' fake_apptype1, fake_apptype2 in fakedev',
            'fake_user performed a "tds deploy promote" for the following app'
            ' tier(s) in fakedev:\n'
            '    fake_apptype1, fake_apptype2'
        ),
    ]

    @data_provider(deployment_factory_provider)
    def test_message_for_deploy_promote(self, deployment_factory, subject, body):
        with patch('tds.model.Project') as Project:
            Project.get.return_value.targets = [
                Mock(app_type=x) for x in ('fake_apptype1', 'fake_apptype2')
            ]

            n = base.Notifier(
                APP_CONFIG,
                APP_CONFIG['notifications']
            )
            message = n.message_for_deployment(deployment_factory())

            assert isinstance(message['subject'], basestring)
            assert isinstance(message['body'], basestring)

            # are these assertions really necessary?
            assert message['subject'] == subject
            assert message['body'] == body

    def test_message_for_unvalidated(self):
        n = base.Notifier(
            APP_CONFIG,
            APP_CONFIG['notifications'],
        )

        message = n.message_for_deployment(
            UnvalidatedDeploymentFactory()
        )
        assert isinstance(message['subject'], basestring)
        assert isinstance(message['body'], basestring)
        # do we want to assert any more here?