"""Mock servers for feature tests."""

import os
import requests

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from multiprocessing import Process


class HipChatHandler(BaseHTTPRequestHandler):
    """
    Handler for requests to the mock HipChat server.
    """

    def __init__(self, *args, **kwargs):
        """Initialize storage for requests."""
        BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

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


class HipChatServer(HTTPServer):
    """
    Wrapper around HTTPServer with HipChatHandler.
    """

    def __init__(self, addr, filename, *args, **kwargs):
        """Initialize the object."""
        HTTPServer.__init__(self, addr, HipChatHandler, *args, **kwargs)
        self.address = 'http://%s:%s' % (self.server_name, self.server_port)
        self.filename = filename

    def post(self, payload, path=None):
        """Perform and return response for a POST request to self."""
        address = self.address
        if path is not None:
            address = "%s%s" % (self.address, path)
        return requests.post(self.address, params=payload)

    def start(self):
        """Start serving."""
        self.server_process = Process(target=self.serve_forever)
        self.server_process.start()

    def add_notification(self, notification):
        """Add a notification to the storage file."""
        item_parent = os.path.dirname(self.filename)

        if not os.path.isdir(item_parent):
            os.makedirs(item_parent)

        old_lines = []
        if os.path.isfile(self.filename):
            with open(self.filename) as f:
                old_lines = eval(f.read())

        with open(self.filename, 'wb') as f:
            old_lines.append(notification)
            f.write(str(old_lines))

    def halt(self):
        """Halt the server."""
        self.socket.close()
        self.server_process.terminate()

    def get_notifications(self):
        """Return all requests and responses."""
        with open(self.filename, 'r') as f:
            return eval(f.read())
