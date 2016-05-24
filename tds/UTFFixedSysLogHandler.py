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

"""
A bug-fix sub-class of SysLogHandler that fixes the UTF-8 BOM syslog
bug that caused UTF syslog entries to not go to the correct
facility.  This is fixed by over-riding the 'emit' definition
with one that puts the BOM in the right place (after prio, instead
of before it).
"""

import sys
import socket
from logging.handlers import SysLogHandler
try:
    import codecs
except ImportError:
    codecs = None


class UTFFixedSysLogHandler(SysLogHandler):
    """
    A bug-fix sub-class of SysLogHandler that fixes the UTF-8 BOM syslog
    bug that caused UTF syslog entries to not go to the correct
    facility.  This is fixed by over-riding the 'emit' definition
    with one that puts the BOM in the right place (after prio, instead
    of before it).

    Based on Python 2.7 version of logging.handlers.SysLogHandler.

    Bug Reference: http://bugs.python.org/issue7077
    """

    def _connect_unixsocket(self, address):
        result = super(UTFFixedSysLogHandler, self)._connect_unixsocket(address)

        if not self.socket or not sys.platform.startswith('darwin'):
            return result

        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2**16-1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2**16-1)

        return result

    def emit(self, record):
        """
        Emit a record.

        The record is formatted, and then sent to the syslog server.  If
        exception information is present, it is NOT sent to the server.
        """
        msg = self.format(record) + '\000'

        # We need to convert record level to lowercase, maybe this will
        # change in the future.
        prio = '<%d>' % self.encodePriority(
            self.facility,
            self.mapPriority(record.levelname)
        )
        prio = prio.encode('utf-8')
        # Message is a string. Convert to bytes as required by RFC 5424.
        msg = msg.encode('utf-8')
        # Really don't need to see the UTF-8 marker in the logs
        #if codecs:
        #    msg = codecs.BOM_UTF8 + msg
        msg = prio + msg
        try:
            if self.unixsocket:
                try:
                    self.socket.send(msg)
                except socket.error:
                    self._connect_unixsocket(self.address)
                    self.socket.send(msg)
            elif self.socktype == socket.SOCK_DGRAM:
                self.socket.sendto(msg, self.address)
            else:
                self.socket.sendall(msg)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
