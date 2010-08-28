# neubot/net/listeners.py
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
# Non-blocking listen() and accept() for stream sockets
#

from neubot.net.streams import create_stream
from neubot.net.pollers import Pollable, poller
from socket import SOCK_STREAM, AI_PASSIVE
from socket import error as SocketError
from ssl import wrap_socket, SSLError
from neubot.utils import fixkwargs
from socket import getaddrinfo
from socket import SO_REUSEADDR
from socket import SOL_SOCKET
from socket import socket
from socket import AF_INET
from neubot import log

LISTENARGS = {
    "cantbind"   : lambda: None,
    "certfile"   : None,
    "family"     : AF_INET,
    "listening"  : lambda: None,
#   "maxclients" : 7,
#   "maxconns"   : 4,
    "poller"     : poller,
    "secure"     : False,
}

class Listener(Pollable):
    def __init__(self, address, port, accepted, **kwargs):
        self.address = address
        self.port = port
        self.accepted = accepted
        self.kwargs = fixkwargs(kwargs, LISTENARGS)
        self.listening = self.kwargs["listening"]
        self.cantbind = self.kwargs["cantbind"]
        self.poller = self.kwargs["poller"]
        self.family = self.kwargs["family"]
        self.secure = self.kwargs["secure"]
        self.certfile = self.kwargs["certfile"]
        self.sock = None
        self._listen()

    def __del__(self):
        pass

    def _listen(self):
        try:
            addrinfo = getaddrinfo(self.address, self.port, self.family,
                                   SOCK_STREAM, 0, AI_PASSIVE)
            for family, socktype, protocol, canonname, sockaddr in addrinfo:
                try:
                    sock = socket(family, socktype, protocol)
                    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
                    sock.setblocking(False)
                    sock.bind(sockaddr)
                    # Probably the backlog here is too big
                    sock.listen(128)
                    self.sock = sock
                    self.poller.set_readable(self)
                    self.listening()
                    break
                except SocketError:
                    log.exception()
        except SocketError:
            log.exception()
        if not self.sock:
            self.cantbind()

    def fileno(self):
        return self.sock.fileno()

    def readable(self):
        try:
            sock, sockaddr = self.sock.accept()
            sock.setblocking(False)
            if self.secure:
                x = wrap_socket(sock, do_handshake_on_connect=False,
                 certfile=self.certfile, server_side=True)
            else:
                x = sock
            stream = create_stream(x, self.poller, sock.fileno(),
                          sock.getsockname(), sock.getpeername())
            self.accepted(stream)
        except (SocketError, SSLError):
            log.exception()

def listen(address, port, accepted, **kwargs):
    Listener(address, port, accepted, **kwargs)
