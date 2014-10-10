"""Mock servers for feature tests."""

import os
import requests

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from multiprocessing import Process, Manager


class HipChatHandler(BaseHTTPRequestHandler):
    """
    Handler for requests to the mock HipChat server.
    """

    def parse_post(self):
        """
        Parse the post path into a dictionary and return it.
        """
        return dict(x.split('=') for x in self.path[2:].split('&'))

    def determine_response(self, form=None):
        """
        Determine what response to send for a given POST request, with
        the fields and values stored in form.
        """
        return 200

    def do_POST(self):
        form = self.parse_post()
        response = self.determine_response(form)
        self.server.add_notification((form, response))
        self.send_response(response)
        return


class HipChatServer(HTTPServer, object):
    """
    Wrapper around HTTPServer with HipChatHandler.
    """

    def __init__(self, addr, *args, **kwargs):
        """Initialize the object."""
        HTTPServer.__init__(self, addr, HipChatHandler, *args, **kwargs)

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
        """Add a notification to the storage file."""
        self.notifications.append(notification)

    def halt(self):
        """Halt the server."""
        self.socket.close()
        self.server_process.terminate()
        self.server_process.join()

    def get_notifications(self):
        """Return all requests and responses."""
        return self.notifications
