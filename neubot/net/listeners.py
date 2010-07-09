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

import socket
import ssl

import neubot

from neubot.net.streams import create_stream
from neubot.net.pollers import Pollable, poller

class Listener(Pollable):
    def __init__(self, address, port, accepted, listening, cantbind,
                 poller, family, secure, certfile):
        self.address = address
        self.port = port
        self.accepted = accepted
        self.listening = listening
        self.cantbind = cantbind
        self.poller = poller
        self.family = family
        self.secure = secure
        self.certfile = certfile
        self.sock = None
        self._listen()

    def __del__(self):
        pass

    def _listen(self):
        try:
            addrinfo = socket.getaddrinfo(self.address, self.port, self.family,
                                      socket.SOCK_STREAM, 0, socket.AI_PASSIVE)
            for family, socktype, protocol, canonname, sockaddr in addrinfo:
                try:
                    sock = socket.socket(family, socktype, protocol)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    sock.setblocking(False)
                    sock.bind(sockaddr)
                    # Probably the backlog here is too big
                    sock.listen(128)
                    self.sock = sock
                    self.poller.set_readable(self)
                    if self.listening:
                        self.listening()
                    break
                except socket.error:
                    neubot.utils.prettyprint_exception()
        except socket.error:
            neubot.utils.prettyprint_exception()
        if not self.sock:
            if self.cantbind:
                self.cantbind()

    def fileno(self):
        return self.sock.fileno()

    def closing(self):
        self.sock.close()

    def readable(self):
        try:
            sock, sockaddr = self.sock.accept()
            sock.setblocking(False)
            if self.secure:
                x = ssl.wrap_socket(sock, do_handshake_on_connect=False,
                               certfile=self.certfile, server_side=True)
            else:
                x = sock
            stream = create_stream(x, self.poller, sock.fileno(),
                          sock.getsockname(), sock.getpeername())
            if self.accepted:
                self.accepted(stream)
        except (socket.error, ssl.SSLError):
            neubot.utils.prettyprint_exception()

#
# TODO
#   (1) Maxclient, maxconns are not yet implemented
#

def listen(address, port, accepted, listening=None, cantbind=None,
           poller=poller, family=socket.AF_INET, secure=False,
           certfile=None, maxclients=7, maxconns=4):
    Listener(address, port, accepted, listening, cantbind, poller,
             family, secure, certfile)
