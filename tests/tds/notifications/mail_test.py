from mock import patch
import unittest2

import re
import email
import tds.notifications.mail as mail

from tests.factories.utils.config import DeployConfigFactory
from tests.factories.model.deployment import DeploymentFactory

APP_CONFIG = DeployConfigFactory()


class TestEmailNotifier(unittest2.TestCase):
    @patch('smtplib.SMTP')
    def test_notify(self, SMTP):
        e = mail.EmailNotifier(
            APP_CONFIG,
            APP_CONFIG['notifications']['email']
        )

        receiver = APP_CONFIG['notifications']['email']['receiver']
        deployment = DeploymentFactory()

        with patch.object(e, 'message_for_deployment') as mock_message:
            mock_message.return_value = dict(
                subject='fake subj',
                body='fake body'
            )

            e.notify(deployment)

        SMTP.assert_called_with('localhost')
        (sender, recvrs, content), _kw = SMTP.return_value.sendmail.call_args
        assert sender == deployment.actor['username']
        self.assertItemsEqual(
            recvrs,
            [deployment.actor['username']+'@tagged.com',
             receiver]
        )

        unfold_header = lambda s: re.sub(r'\n(?:[ \t]+)', r' ', s)

        msg = email.message_from_string(content)
        username = deployment.actor['username']
        sender_email = username+'@tagged.com'
        ctype = 'text/plain; charset="us-ascii"'
        assert unfold_header(msg.get('content-type')) == ctype
        assert unfold_header(msg.get('subject')) == '[TDS] fake subj'
        assert unfold_header(msg.get('from')) == sender_email
        self.assertItemsEqual(
            msg.get('to').split(', '),
            [sender_email, receiver]
        )
        assert msg.get_payload() == 'fake body'

        assert SMTP.return_value.quit.called
