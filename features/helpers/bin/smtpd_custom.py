#!/usr/bin/env python2.7
"""Customized SMTP server for testing"""

import asyncore
import json
import smtpd
import smtplib
import sys


class CustomSMTPServer(smtpd.SMTPServer):
    """Test mail server for feature tests"""

    def process_message(self, peer, mailfrom, rcpttos, data):
        """Handle incoming message"""

        if 'serverfail@example.com' in mailfrom:
            raise smtplib.SMTPException('Server crashed, try again')

        results = dict(
            origin=peer,
            sender=mailfrom,
            receiver=rcpttos,
            contents=data
        )

        with open('message.json', 'wb') as fh:
            fh.write(json.dumps(results))

        return


if __name__ == '__main__':
    server = CustomSMTPServer(('127.0.0.1', int(sys.argv[1])), None)

    asyncore.loop()
