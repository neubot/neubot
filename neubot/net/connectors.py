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

from neubot.net.streams import create_stream
from neubot.net.pollers import Pollable, poller
from neubot.utils import fixkwargs
from socket import error as SocketError
from ssl import wrap_socket, SSLError
from socket import SOCK_STREAM
from errno import EINPROGRESS
from errno import EWOULDBLOCK
from socket import getaddrinfo
from errno import ENOTCONN
from socket import AF_INET
from socket import socket
from neubot import log
from os import strerror

#
# We have the same code path for connect_ex() returning 0 and returning
# one of [EINPROGRESS, EWOULDBLOCK].  This is not very efficient because
# when it returns 0 we know we are already connected and so it would be
# more logical not to check for writability.  But there is also value
# in sharing the same code path, namely that testing is simpler because
# we don't have to test the [EINPROGRESS, EWOULDBLOCK] corner case.
#

CONNECTARGS = {
    "cantconnect" : lambda: None,
    "connecting"  : lambda: None,
    "conntimeo"   : 10,
    "family"      : AF_INET,
    "poller"      : poller,
    "secure"      : False,
}

class Connector(Pollable):
    def __init__(self, address, port, connected, **kwargs):
        self.address = address
        self.port = port
        self.connected = connected
        self.kwargs = fixkwargs(kwargs, CONNECTARGS)
        self.connecting = self.kwargs["connecting"]
        self.cantconnect = self.kwargs["cantconnect"]
        self.poller = self.kwargs["poller"]
        self.family = self.kwargs["family"]
        self.secure = self.kwargs["secure"]
        self.conntimeo = self.kwargs["conntimeo"]
        self.begin = 0
        self.sock = None
        self._connect()

    def __del__(self):
        pass

    def _connect(self):
        try:
            addrinfo = getaddrinfo(self.address, self.port,
                                   self.family, SOCK_STREAM)
            for family, socktype, protocol, cannonname, sockaddr in addrinfo:
                try:
                    sock = socket(family, socktype, protocol)
                    sock.setblocking(False)
                    error = sock.connect_ex(sockaddr)
                    # Winsock returns EWOULDBLOCK
                    if error not in [0, EINPROGRESS, EWOULDBLOCK]:
                        raise SocketError(error, strerror(error))
                    self.sock = sock
                    self.begin = self.poller.get_ticks()
                    self.poller.set_writable(self)
                    self.connecting()
                    break
                except SocketError:
                    log.exception()
        except SocketError:
            log.exception()
        if not self.sock:
            self.cantconnect()

    def fileno(self):
        return self.sock.fileno()

    def writable(self):
        self.poller.unset_writable(self)
        try:
            # See http://cr.yp.to/docs/connect.html
            try:
                self.sock.getpeername()
            except SocketError, (code, reason):
                if code == ENOTCONN:
                    self.sock.recv(8000)
                else:
                    raise
            if self.secure:
                x = wrap_socket(self.sock, do_handshake_on_connect=False)
            else:
                x = self.sock
            stream = create_stream(x, self.poller, self.sock.fileno(),
                     self.sock.getsockname(), self.sock.getpeername())
            self.connected(stream)
        except (SocketError, SSLError):
            log.exception()
            self.cantconnect()

    def writetimeout(self, now):
        return now - self.begin >= self.conntimeo

def connect(address, port, connected, **kwargs):
    Connector(address, port, connected, **kwargs)
