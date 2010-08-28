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

from sys import path as PATH
if __name__ == "__main__":
    PATH.insert(0, ".")

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
from socket import AF_INET6
from socket import AF_INET
from socket import socket
from neubot import log
from os import strerror
from sys import argv

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
        self.name = (self.address, self.port)
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
        log.debug("* About to connect to %s:%s" % self.name)
        try:
            addrinfo = getaddrinfo(self.address, self.port,
                                   self.family, SOCK_STREAM)
            for family, socktype, protocol, cannonname, sockaddr in addrinfo:
                try:
                    log.debug("* Trying with %s..." % str(sockaddr))
                    sock = socket(family, socktype, protocol)
                    sock.setblocking(False)
                    error = sock.connect_ex(sockaddr)
                    # Winsock returns EWOULDBLOCK
                    if error not in [0, EINPROGRESS, EWOULDBLOCK]:
                        raise SocketError(error, strerror(error))
                    self.sock = sock
                    self.begin = self.poller.get_ticks()
                    self.poller.set_writable(self)
                    log.debug("* Connection to %s in progress" % str(sockaddr))
                    self.connecting()
                    break
                except SocketError:
                    log.error("* connect() to %s failed" % str(sockaddr))
                    log.exception()
        except SocketError:
            log.error("* getaddrinfo() %s:%s failed" % self.name)
            log.exception()
        if not self.sock:
            log.error("* Can't connect to %s:%s" % self.name)
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
            logname = "with %s:%s" % self.name
            stream = create_stream(x, self.poller, self.sock.fileno(),
             self.sock.getsockname(), self.sock.getpeername(), logname)
            log.debug("* Connected to %s:%s!" % self.name)
            self.connected(stream)
        except (SocketError, SSLError):
            log.error("* Can't connect to %s:%s" % self.name)
            log.exception()
            self.cantconnect()

    def writetimeout(self, now):
        timedout = (now - self.begin >= self.conntimeo)
        if timedout:
            log.error("* connect() to %s:%s timed-out" % self.name)
        return timedout

def connect(address, port, connected, **kwargs):
    Connector(address, port, connected, **kwargs)

#
# Test unit
#

from neubot.net.pollers import loop
from neubot import version
from getopt import GetoptError
from getopt import getopt
from sys import stdout
from sys import stderr

USAGE = "Usage: %s [-6SVv] [-n timeout] [--help] address port\n"

HELP = USAGE +								\
"Options:\n"								\
"  -6         : Use IPv6 rather than IPv4.\n"				\
"  --help     : Print this help screen and exit.\n"			\
"  -n timeout : Time-out after timeout seconds.\n"			\
"  -S         : Secure connect().  Use OpenSSL.\n"			\
"  -V         : Print version number and exit.\n"			\
"  -v         : Run the program in verbose mode.\n"

def connected(stream):
    stream.close()

def main(args):
    family = AF_INET
    timeout = 10
    secure = False
    try:
        options, arguments = getopt(args[1:], "6n:SVv", ["help"])
    except GetoptError:
        stderr.write(USAGE % args[0])
        exit(1)
    for name, value in options:
        if name == "-6":
            family = AF_INET6
        elif name == "--help":
            stdout.write(HELP % args[0])
            exit(0)
        elif name == "-n":
            try:
                timeout = int(value)
            except ValueError:
                timeout = -1
            if timeout < 0:
                log.error("Bad timeout")
                exit(1)
        elif name == "-S":
            secure = True
        elif name == "-V":
            stdout.write(version + "\n")
            exit(0)
        elif name == "-v":
            log.verbose()
    if len(arguments) != 2:
        stderr.write(USAGE % args[0])
        exit(1)
    connect(arguments[0], arguments[1], connected, conntimeo=timeout,
            family=family, secure=secure)
    loop()

if __name__ == "__main__":
    main(argv)
