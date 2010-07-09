# neubot/net/connectors.py
# Copyright (c) 2010 NEXA Center for Internet & Society

# This file is part of Neubot.
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
# Non-blocking connect for stream sockets
#

import errno
import os
import socket
import ssl

import neubot

from neubot.net.streams import create_stream
from neubot.net.pollers import Pollable, poller

#
# We have the same code path for connect_ex() returning 0 and returning
# one of [EINPROGRESS, EWOULDBLOCK].  This is not very efficient because
# when it returns 0 we know we are already connected and so it would be
# more logical not to check for writability.  But there is also value
# in sharing the same code path, namely that testing is simpler because
# we don't have to test the [EINPROGRESS, EWOULDBLOCK] corner case.
#

class Connector(Pollable):
    def __init__(self, address, port, connected, connecting, cantconnect,
                 poller, family, secure, conntimeo):
        self.address = address
        self.port = port
        self.connected = connected
        self.connecting = connecting
        self.cantconnect = cantconnect
        self.poller = poller
        self.family = family
        self.secure = secure
        self.conntimeo = conntimeo
        self.begin = 0
        self.sock = None
        self._connect()

    def __del__(self):
        pass

    def _connect(self):
        try:
            addrinfo = socket.getaddrinfo(self.address, self.port, self.family,
                                                      socket.SOCK_STREAM, 0, 0)
            for family, socktype, protocol, cannonname, sockaddr in addrinfo:
                try:
                    sock = socket.socket(family, socktype, protocol)
                    sock.setblocking(False)
                    error = sock.connect_ex(sockaddr)
                    # Winsock returns EWOULDBLOCK
                    if error not in [0, errno.EINPROGRESS, errno.EWOULDBLOCK]:
                        raise socket.error(error, os.strerror(error))
                    self.sock = sock
                    self.begin = self.poller.get_ticks()
                    self.poller.set_writable(self)
                    if self.connecting:
                        self.connecting()
                    break
                except socket.error:
                    neubot.utils.prettyprint_exception()
        except socket.error:
            neubot.utils.prettyprint_exception()
        if not self.sock:
            if self.cantconnect:
                self.cantconnect()

    def closing(self):
        if self.cantconnect:
            self.cantconnect()

    def fileno(self):
        return self.sock.fileno()

    def writable(self):
        self.poller.unset_writable(self)
        try:
            # See http://cr.yp.to/docs/connect.html
            try:
                self.sock.getpeername()
            except socket.error, (code, reason):
                if code == errno.ENOTCONN:
                    self.sock.recv(8000)
                else:
                    raise
            if self.secure:
                x = ssl.wrap_socket(self.sock,do_handshake_on_connect=False)
            else:
                x = self.sock
            stream = create_stream(x, self.poller, self.sock.fileno(),
                     self.sock.getsockname(), self.sock.getpeername())
            if self.connected:
                self.connected(stream)
        except (socket.error, ssl.SSLError):
            neubot.utils.prettyprint_exception()
            if self.cantconnect:
                self.cantconnect()

    def writetimeout(self, now):
        return now - self.begin > self.conntimeo

def connect(address, port, connected, connecting=None, cantconnect=None,
            poller=poller, family=socket.AF_INET, secure=False, conntimeo=10):
    Connector(address, port, connected, connecting, cantconnect,
              poller, family, secure, conntimeo)
