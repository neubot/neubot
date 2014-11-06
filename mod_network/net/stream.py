# net/stream.py

#
# Copyright (c) 2010-2012, 2014
#   Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#   and Simone Basso <bassosimone@gmail.com>.
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

""" A connected stream socket """

import collections
import logging
import ssl

from neubot.pollable import Pollable
from neubot import utils_net

from .stream_model import SUCCESS
from .stream_model import WANT_READ
from .stream_model import WANT_WRITE
from .stream_model import ERROR
from .stream_model import CONNRESET
from .stream_ssl import StreamSSL
from .stream_tcp import StreamTCP

# Maximum amount of bytes we read from a socket
MAXBUF = 1 << 18

class Stream(Pollable):
    """ A connected stream socket """

    def __init__(self, poller):

        # Note: API possibly broken by now-hidden internal variables

        Pollable.__init__(self)
        self._poller = poller
        self.parent = None
        self.conf = None

        self._sock = None
        self._filenum = -1
        self.myname = None
        self.peername = None
        self._logname = None
        self.eof = False
        self.rst = False

        self.close_complete = False
        self.close_pending = False
        self._recv_blocked = False
        self._recv_pending = False
        self._recv_ssl_needs_kickoff = False
        self._send_blocked = False
        self._send_octets = None
        self._send_queue = collections.deque()
        self._send_pending = False

        self.bytes_recv_tot = 0
        self.bytes_sent_tot = 0

        self.opaque = None
        self._atclosev = set()

    def __repr__(self):
        return "stream %s" % self._logname

    def fileno(self):
        return self._filenum

    def attach(self, parent, sock, conf=None):
        """ Attach the otherwise empty stream to parent socket and conf """

        if not conf:
            conf = {}

        self.parent = parent
        self.conf = conf

        self._filenum = sock.fileno()
        self.myname = utils_net.getsockname(sock)
        self.peername = utils_net.getpeername(sock)
        self._logname = "Stream(%s, %s)" % (self.myname, self.peername)

        logging.debug("%s: connection made", self)

        # Map old names for compatibility
        self.conf["ssl/enable"] = self.conf.get("net.stream.secure")
        self.conf["ssl/server_side"] = self.conf.get("net.stream.server_side")
        self.conf["ssl/certfile"] = self.conf.get("net.stream.certfile")

        if self.conf.get("ssl/enable"):

            server_side = self.conf.get("ssl/server_side")
            certfile = self.conf.get("ssl/certfile")

            # wrap_socket distinguishes between None and ''
            if not certfile:
                certfile = None

            ssl_sock = ssl.wrap_socket(sock, do_handshake_on_connect=False,
              certfile=certfile, server_side=server_side)
            self._sock = StreamSSL(ssl_sock)

            self._recv_ssl_needs_kickoff = not server_side

        else:
            self._sock = StreamTCP(sock)

        self.connection_made()

    def connection_made(self):
        """ Override this method in derived classes """

    def atclose(self, func):
        """ Register a function to be called when the stream is closed """
        if func in self._atclosev:
            logging.warning("%s: duplicate atclose(): %s", self, func)
        self._atclosev.add(func)

    def unregister_atclose(self, func):
        """ Unregister a function to be called at close() """
        if func in self._atclosev:
            self._atclosev.remove(func)

    # Close path

    def connection_lost(self, exception):
        """ Override this method in derived classes """

    def close(self):
        """ Close the stream """

        self.close_pending = True
        if self._send_pending or self.close_complete:
            return
        self._poller.close(self)

    def handle_close(self):  # Part of the Pollable object model

        if self.close_complete:
            return

        self.close_complete = True

        self.connection_lost(None)
        self.parent.connection_lost(self)

        atclosev, self._atclosev = self._atclosev, set()
        for func in atclosev:
            try:
                func(self, None)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                logging.error("%s: error in atclosev", self, exc_info=1)

        self._send_octets = None
        self._sock.soclose()
        self.opaque = None

    # Recv path

    def start_recv(self):
        """ Start an async receive operation """

        if (self.close_complete or self.close_pending
          or self._recv_pending):
            return

        self._recv_pending = True

        if self._recv_blocked:
            return

        self._poller.set_readable(self)

        #
        # The client-side of an SSL connection must send the HELLO
        # message to start the negotiation.  This is done automagically
        # by SSL_read and SSL_write.  When the client first operation
        # is a send(), no problem: the socket is always writable at
        # the beginning and writable() invokes sosend() that invokes
        # SSL_write() that negotiates.  The problem is when the client
        # first operation is recv(): in this case the socket would never
        # become readable because the server side is waiting for an HELLO.
        # The following piece of code makes sure that the first recv()
        # of the client invokes readable() that invokes sorecv() that
        # invokes SSL_read() that starts the negotiation.
        #
        if self._recv_ssl_needs_kickoff:
            self._recv_ssl_needs_kickoff = False
            self.handle_read()

    def handle_read(self):  # Part of the Pollable object model

        if self._recv_blocked:
            self._poller.set_writable(self)
            if not self._recv_pending:
                self._poller.unset_readable(self)
            self._recv_blocked = False
            self.handle_write()
            return

        status, octets = self._sock.sorecv(MAXBUF)

        if status == SUCCESS and octets:

            self.bytes_recv_tot += len(octets)
            self._recv_pending = False
            self._poller.unset_readable(self)

            self.recv_complete(octets)
            return

        if status == WANT_READ:
            return

        if status == WANT_WRITE:
            self._poller.unset_readable(self)
            self._poller.set_writable(self)
            self._send_blocked = True
            return

        if status == CONNRESET and not octets:
            self.rst = True
            self._poller.close(self)
            return

        if status == SUCCESS and not octets:
            self.eof = True
            self._poller.close(self)
            return

        if status == ERROR:
            # Here octets is the exception that occurred
            raise octets

        raise RuntimeError("Unexpected status value")

    def recv_complete(self, octets):
        """ Override this method in derived classes """

    # Send path

    def _read_send_queue(self):
        """ Reads the next block that must be sent """

        while self._send_queue:
            octets = self._send_queue[0]
            if hasattr(octets, "read"):
                octets = octets.read(MAXBUF)
                if octets:
                    return octets
                # remove the file-like when it is empty
                self._send_queue.popleft()
            else:
                # remove the piece in any case
                self._send_queue.popleft()
                if octets:
                    return octets

        return ""

    def start_send(self, octets):
        """ Start an async send operation """

        if self.close_complete or self.close_pending:
            return

        self._send_queue.append(octets)
        if self._send_pending:
            return

        self._send_octets = self._read_send_queue()
        if not self._send_octets:
            return

        self._send_pending = True

        if self._send_blocked:
            return

        self._poller.set_writable(self)

    def handle_write(self):  # Part of the Pollable object model

        if self._send_blocked:
            self._poller.set_readable(self)
            if not self._send_pending:
                self._poller.unset_writable(self)
            self._send_blocked = False
            self.handle_read()
            return

        status, count = self._sock.sosend(self._send_octets)

        if status == SUCCESS and count > 0:
            self.bytes_sent_tot += count

            if count == len(self._send_octets):

                self._send_octets = self._read_send_queue()
                if self._send_octets:
                    return

                self._send_pending = False
                self._poller.unset_writable(self)

                self.send_complete()
                if self.close_pending:
                    self._poller.close(self)
                return

            if count < len(self._send_octets):
                self._send_octets = buffer(self._send_octets, count)
                self._poller.set_writable(self)
                return

            raise RuntimeError("Sent more than expected")

        if status == WANT_WRITE:
            return

        if status == WANT_READ:
            self._poller.unset_writable(self)
            self._poller.set_readable(self)
            self._recv_blocked = True
            return

        if status == ERROR:
            # Here count is the exception that occurred
            raise count

        if status == CONNRESET and count == 0:
            self.rst = True
            self._poller.close(self)
            return

        if status == SUCCESS and count == 0:
            self.eof = True
            self._poller.close(self)
            return

        if status == SUCCESS and count < 0:
            raise RuntimeError("Unexpected count value")

        raise RuntimeError("Unexpected status value")

    def send_complete(self):
        """ Override this method in derived classes """
