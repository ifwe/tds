#!/usr/bin/env python2.7
#
# Copyright 2016 Ifwe Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

        if 'serverfail@example.com' in rcpttos:
            raise smtplib.SMTPException('Server crashed, try again')

        try:
            with open('message.json') as fh:
                email_list = json.loads(fh.read())
        except IOError:  # File does not yet exist, new list
            email_list = []

        email_list.append(dict(
            origin=peer,
            sender=mailfrom,
            receiver=rcpttos,
            contents=data
        ))

        with open('message.json', 'wb') as fh:
            fh.write(json.dumps(email_list))


if __name__ == '__main__':
    server = CustomSMTPServer(('127.0.0.1', int(sys.argv[1])), None)

    asyncore.loop()
