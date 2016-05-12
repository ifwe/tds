from mock import patch
import unittest

import re
import email
import tds.notifications.mail as mail

from tests.factories.utils.config import DeployConfigFactory
from tests.factories.model.deployment import DeploymentFactory

APP_CONFIG = DeployConfigFactory()


class TestEmailNotifier(unittest.TestCase):
    @patch('smtplib.SMTP')
    def test_notify(self, SMTP):
        e = mail.EmailNotifier(
            APP_CONFIG,
            APP_CONFIG['notifications']['email']
        )

        receiver = APP_CONFIG['notifications']['email']['receiver']
        domain = APP_CONFIG['notifications']['email']['sender_domain']
        deployment = DeploymentFactory()

        with patch.object(e, 'message_for_deployment') as mock_message:
            mock_message.return_value = dict(
                subject='fake subj',
                body='fake body'
            )

            e.notify(deployment)

        SMTP.assert_called_with('localhost', 1025)
        (sender, recvrs, content), _kw = SMTP.return_value.sendmail.call_args
        self.assertEqual(sender, deployment.actor.name)
        self.assertItemsEqual(
            recvrs,
            [deployment.actor.name+domain,
             receiver]
        )

        unfold_header = lambda s: re.sub(r'\n(?:[ \t]+)', r' ', s)

        msg = email.message_from_string(content)
        username = deployment.actor.name
        sender_email = username+domain
        ctype = 'text/plain; charset="us-ascii"'
        self.assertEqual(unfold_header(msg.get('content-type')), ctype)
        self.assertEqual(unfold_header(msg.get('subject')), '[TDS] fake subj')
        self.assertEqual(unfold_header(msg.get('from')), sender_email)
        self.assertItemsEqual(
            msg.get('to').split(', '),
            [sender_email, receiver]
        )
        self.assertEqual(msg.get_payload(), 'fake body')

        self.assertTrue(SMTP.return_value.quit.called)
