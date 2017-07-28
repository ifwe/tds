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

"""Mock Signalfx server for feature tests."""

import os
import json
import requests

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from multiprocessing import Process, Manager


class SignalfxHandler(BaseHTTPRequestHandler):
    """
    Handler for requests to the mock Signalfx server.
    """

    def parse_post(self):
        """
        Parse the post path into a dictionary and return it.
        """
        content_len = int(self.headers.getheader('content-length', 0))
        content = self.rfile.read(content_len)
        return json.loads(content)

    def determine_response(self, form=None):
        """
        Determine what response to send for a given POST request, with
        the fields and values stored in form.
        """
        # TODO: url unquoting
        if form and '200' in form['properties']['release_version'] and 'myapp' in form['properties']['artifact_name']:
            return 403
        if form and '500' in form['properties']['release_version'] and 'myapp' in form['properties']['artifact_name']:
            return 'No response'
        return 200

    def do_POST(self):
        form = self.parse_post()
        response = self.determine_response(form)
        self.server.add_notification((form, response))
        if response != 'No response':
            self.send_response(response)
        return


class SignalfxServer(HTTPServer, object):
    """
    Wrapper around HTTPServer with HipChatHandler.
    """

    def __init__(self, addr, *args, **kwargs):
        """Initialize the object."""
        HTTPServer.__init__(self, addr, SignalfxHandler, *args, **kwargs)

        self.address = 'http://%s:%s' % (self.server_name, self.server_port)

        self._manager = Manager()
        self.notifications = self._manager.list()

    def post(self, payload, path=None):
        """Perform and return response for a POST request to self."""
        address = self.address
        if path is not None:
            address = "%s%s" % (self.address, path)
        return requests.post(self.address, params=payload)

    def serve_forever(self, notifications):
        """Add notifications to self and serve forever."""
        self.notifications = notifications
        HTTPServer.serve_forever(self)

    def start(self):
        """Start serving."""
        self.server_process = Process(
            target=self.serve_forever,
            args=(self.notifications,)
        )
        self.server_process.start()

    def add_notification(self, notification):
        """Add a notification to the list."""
        self.notifications.append(notification)

    def halt(self):
        """Halt the server."""
        self.socket.close()
        self.server_process.terminate()
        self.server_process.join()

    def get_notifications(self):
        """Return all requests and responses."""
        return self.notifications
