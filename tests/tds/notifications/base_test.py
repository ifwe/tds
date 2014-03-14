from mock import patch
import unittest2

import tds.notifications.base as base

from tests.factories.utils.config import DeployConfigFactory
from tests.factories.model.deployment import (
    DeploymentFactory,
    UnvalidatedDeploymentFactory,
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

    def test_message_for_deploy_promote(self):
        n = base.Notifier(
            APP_CONFIG,
            APP_CONFIG['notifications']
        )
        message = n.message_for_deployment(DeploymentFactory())

        assert isinstance(message['subject'], basestring)
        assert isinstance(message['body'], basestring)

        # are these assertions really necessary?
        assert message['subject'] == (
            'Promote of version badf00d of fake_package on app tier(s)'
            ' fake_apptype in fakedev'
        )
        assert message['body'] == (
            'fake_user performed a "tds deploy promote" for the following app '
            'tier(s) in fakedev:\n'
            '    fake_apptype'
        )

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
