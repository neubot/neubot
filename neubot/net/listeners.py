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

if __name__ == "__main__":
    from sys import path
    path.insert(0, ".")

HAVE_SSL = True
try:
    from ssl import wrap_socket, SSLError
except ImportError:
    HAVE_SSL = False
    class SSLError(Exception):
        pass

from neubot.net.streams import create_stream
from neubot.net.pollers import Pollable, poller
from socket import SOCK_STREAM, AI_PASSIVE
from socket import error as SocketError
from neubot.utils import fixkwargs
from socket import getaddrinfo
from socket import SO_REUSEADDR
from socket import SOL_SOCKET
from socket import socket
from socket import AF_INET
from sys import exit
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
        self.name = (self.address, self.port)
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
        log.debug("* About to bind %s:%s" % self.name)
        try:
            addrinfo = getaddrinfo(self.address, self.port, self.family,
                                   SOCK_STREAM, 0, AI_PASSIVE)
            for family, socktype, protocol, canonname, sockaddr in addrinfo:
                try:
                    log.debug("* Trying with %s..." % str(sockaddr))
                    sock = socket(family, socktype, protocol)
                    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
                    sock.setblocking(False)
                    sock.bind(sockaddr)
                    # Probably the backlog here is too big
                    sock.listen(128)
                    self.sock = sock
                    self.poller.set_readable(self)
                    log.debug("* Bound with %s" % str(sockaddr))
                    log.debug("* Listening at %s:%s..." % self.name)
                    self.listening()
                    break
                except SocketError:
                    log.error("* bind() with %s failed" % str(sockaddr))
                    log.exception()
        except SocketError:
            log.error("* getaddrinfo() %s:%s failed" % self.name)
            log.exception()
        if not self.sock:
            log.error("* Can't bind %s:%s" % self.name)
            self.cantbind()

    def fileno(self):
        return self.sock.fileno()

    def readable(self):
        try:
            sock, sockaddr = self.sock.accept()
            sock.setblocking(False)
            if self.secure:
                if HAVE_SSL:
                    x = wrap_socket(sock, do_handshake_on_connect=False,
                     certfile=self.certfile, server_side=True)
                else:
                    raise RuntimeError("SSL support not available")
            else:
                x = sock
            logname = "with %s" % str(sock.getpeername())
            stream = create_stream(x, self.poller, sock.fileno(),
             sock.getsockname(), sock.getpeername(), logname)
            log.debug("* Got connection from %s" % str(sock.getpeername()))
            self.accepted(stream)
        except (SocketError, SSLError):
            log.exception()

def listen(address, port, accepted, **kwargs):
    Listener(address, port, accepted, **kwargs)

#
# Test unit
#

from socket import AF_INET6
from neubot.net.pollers import loop
from neubot import version
from getopt import GetoptError
from getopt import getopt
from sys import stdout
from sys import stderr
from sys import argv

USAGE = "Usage: %s [-6Vv] [-S certfile] [--help] address port\n"

HELP = USAGE +								\
"Options:\n"								\
"  -6          : Use IPv6 rather than IPv4.\n"				\
"  --help      : Print this help screen and exit.\n"			\
"  -S certfile : Use OpenSSL and the specified certfile.\n"		\
"  -V          : Print version number and exit.\n"			\
"  -v          : Run the program in verbose mode.\n"

def accepted(stream):
    stream.close()

def main(args):
    family = AF_INET
    secure = False
    certfile = None
    try:
        options, arguments = getopt(args[1:], "6S:Vv", ["help"])
    except GetoptError:
        stderr.write(USAGE % args[0])
        exit(1)
    for name, value in options:
        if name == "-6":
            family = AF_INET6
        elif name == "--help":
            stdout.write(HELP % args[0])
            exit(0)
        elif name == "-S":
            secure = True
            certfile = value
        elif name == "-V":
            stdout.write(version + "\n")
            exit(0)
        elif name == "-v":
            log.verbose()
    if len(arguments) != 2:
        stderr.write(USAGE % args[0])
        exit(1)
    listen(arguments[0], arguments[1], accepted, family=family,
     secure=secure, certfile=certfile)
    loop()

if __name__ == "__main__":
    main(argv)
