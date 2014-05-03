# neubot/stream.py

#
# Copyright (c) 2010-2012 Simone Basso <bassosimone@gmail.com>,
#  NEXA Center for Internet & Society at Politecnico di Torino
#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Neubot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Neubot.  If not, see <http://www.gnu.org/licenses/>.
#

#
# pylint: disable = missing-docstring
# Python3-ready: yes
#

import logging

from neubot.defer import Deferred
from neubot.pollable import AsyncStream
from neubot.pollable import SocketWrapper
from neubot.poller import POLLER

from neubot import utils_net

class Stream(AsyncStream):

    def __init__(self, sock, connection_made, connection_lost, sslconfig,
                 sslcert, opaque):
        AsyncStream.__init__(self, POLLER, None)

        self.myname = utils_net.getsockname(sock)
        self.peername = utils_net.getpeername(sock)
        self.logname = '%s %s' % (utils_net.format_epnt(self.myname),
                                  utils_net.format_epnt(self.peername))

        logging.debug('stream: __init__(): %s', self.logname)

        # Variables pointing to other objects
        self.atclose = Deferred()
        self.atconnect = Deferred()
        self.opaque = opaque
        self.recv_complete = None
        self.send_complete = None

        # Variables we don't need to clear
        self.bytes_in = 0
        self.bytes_out = 0
        self.conn_rst = False
        self.eof = False
        self.isclosed = False

        self.atclose.add_callback(connection_lost)
        self.atconnect.add_callback(connection_made)
        self.atconnect.add_errback(self._connection_made_error)

        if not sslconfig:
            self.sock = SocketWrapper(sock)  # XXX
            self.atconnect.callback(self)
            return

        #
        # Lazy import: this fails on Python 2.5, because SSL is not part of
        # v2.5 standard library.  We do not intercept the error here, because
        # accept() code already needs to setup a try..except to route any
        # error away from the listening socket.
        #
        from neubot import sslstream

        #
        # If there is SSL support, initialise() deals transparently with SSL
        # negotiation, and invokes connection_made() when done.  Errors are
        # routed to the POLLER, which generates CLOSE events accordingly.
        #
        sslstream.initialise(self, sock, sslcert)

    def _connection_made_error(self, exception):
        logging.warning('stream: connection_made() failed: %s', str(exception))
        self.poller.close(self)

    def register_cleanup(self, func):
        self.atclose.add_callback(func)

    def handle_close(self):

        if self.isclosed:
            return

        logging.debug('stream: closing %s', self.logname)
        self.isclosed = True

        self.atclose.callback_each_np(self)
        self.sock.close()

        self.atclose = None
        self.atconnect = None
        self.opaque = None
        self.recv_complete = None
        self.send_complete = None

    def recv(self, recv_count, recv_complete):

        if self.isclosed:
            raise RuntimeError('stream: recv() on a closed stream')

        if self.read(recv_count) < 0:
            raise RuntimeError("stream: read failed")

        self.recv_complete = recv_complete

    def on_data(self, octets):
        self.bytes_in += len(octets)
        self.recv_complete(self, octets)

    def on_eof(self):
        self.eof = True

    def on_rst(self):
        self.conn_rst = True

    def send(self, send_octets, send_complete):

        if self.isclosed:
            raise RuntimeError('stream: send() on a closed stream')

        if self.write(send_octets) < 0:
            raise RuntimeError("stream: write failed")

        self.send_complete = send_complete

    def on_flush(self, count, complete):
        self.bytes_out += count
        if not complete:
            return
        self.send_complete(self)
