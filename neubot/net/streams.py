# neubot/net/streams.py

#
# Copyright (c) 2010 Simone Basso <bassosimone@gmail.com>,
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
# Asynchronous I/O for non-blocking sockets (and SSL)
#

import errno
import os
import socket
import sys
import types

try:
    from Crypto.Cipher import ARC4
except ImportError:
    ARC4 = None
try:
    import ssl
except ImportError:
    ssl = None

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.net.pollers import sched
from neubot.net.pollers import Pollable
from neubot.net.pollers import poller
from neubot.net.pollers import loop
from neubot.utils import speed_formatter
from neubot.utils import ticks
from neubot.utils import fixkwargs
from neubot import log

SUCCESS = 0
ERROR = 1
WANT_READ = 2
WANT_WRITE = 3

TIMEOUT = 300

MAXBUF = 1<<18

SOFT_ERRORS = [ errno.EAGAIN, errno.EWOULDBLOCK, errno.EINTR ]

# Winsock returns EWOULDBLOCK
INPROGRESS = [ 0, errno.EINPROGRESS, errno.EWOULDBLOCK, errno.EAGAIN ]

if ssl:
    class SSLWrapper(object):
        def __init__(self, sock):
            self.sock = sock
            self.need_handshake = True

        def soclose(self):
            try:
                self.sock.close()
            except ssl.SSLError:
                pass

        def sorecv(self, maxlen):
            try:
                if self.need_handshake:
                    self.sock.do_handshake()
                    self.need_handshake = False
                octets = self.sock.read(maxlen)
                return SUCCESS, octets
            except ssl.SSLError, exception:
                if exception[0] == ssl.SSL_ERROR_WANT_READ:
                    return WANT_READ, ""
                elif exception[0] == ssl.SSL_ERROR_WANT_WRITE:
                    return WANT_WRITE, ""
                else:
                    return ERROR, exception

        def sosend(self, octets):
            try:
                if self.need_handshake:
                    self.sock.do_handshake()
                    self.need_handshake = False
                count = self.sock.write(octets)
                return SUCCESS, count
            except ssl.SSLError, exception:
                if exception[0] == ssl.SSL_ERROR_WANT_READ:
                    return WANT_READ, 0
                elif exception[0] == ssl.SSL_ERROR_WANT_WRITE:
                    return WANT_WRITE, 0
                else:
                    return ERROR, exception

class SocketWrapper(object):
    def __init__(self, sock):
        self.sock = sock

    def soclose(self):
        try:
            self.sock.close()
        except socket.error:
            pass

    def sorecv(self, maxlen):
        try:
            octets = self.sock.recv(maxlen)
            return SUCCESS, octets
        except socket.error, exception:
            if exception[0] in SOFT_ERRORS:
                return WANT_READ, ""
            else:
                return ERROR, exception

    def sosend(self, octets):
        try:
            count = self.sock.send(octets)
            return SUCCESS, count
        except socket.error, exception:
            if exception[0] in SOFT_ERRORS:
                return WANT_WRITE, 0
            else:
                return ERROR, exception

class Stream(Pollable):
    def __init__(self, poller):
        self.poller = poller
        self.parent = None

        self.sock = None
        self.filenum = -1
        self.myname = None
        self.peername = None
        self.logname = None

        self.timeout = TIMEOUT
        self.encrypt = None
        self.decrypt = None

        self.send_octets = None
        self.send_success = None
        self.send_ticks = 0
        self.recv_maxlen = 0
        self.recv_success = None
        self.recv_ticks = 0

        self.eof = False
        self.isclosed = 0
        self.send_pending = 0
        self.sendblocked = 0
        self.recv_pending = 0
        self.recvblocked = 0

        self.stats = []
        self.stats.append(self.poller.stats)
        self.notify_closing = None

    #
    # XXX
    # Reading the code, please keep in mind that there are two
    # possible levels of abstraction.  At the higher level your
    # protocol class derives from this class, and you override
    # connection_lost(), recv_complete(), send_complete() and
    # you invoke start_recv() and start_send() and so forth.
    # At the lower level you invoke directly recv() and send()
    # and you register a cleanup function in notify_closing.
    # Further comments will highlight what parts of the code
    # are at the higher level and what are at the lower level.
    # We will merge the low level into the high one in the
    # future.    (2011-01-09, Simone)
    #

    def fileno(self):
        return self.filenum

    def make_connection(self, sock):
        self.filenum = sock.fileno()
        self.myname = sock.getsockname()
        self.peername = sock.getpeername()
        self.logname = str((self.myname, self.peername))
        self.sock = SocketWrapper(sock)

    def configure(self, dictionary):
        if "secure" in dictionary and dictionary["secure"]:

            if not ssl:
                raise RuntimeError("SSL support not available")

            server_side = False
            if "server_side" in dictionary and dictionary["server_side"]:
                server_side = dictionary["server_side"]
            certfile = None
            if "certfile" in dictionary and dictionary["certfile"]:
                certfile = dictionary["certfile"]

            so = ssl.wrap_socket(self.sock.sock, do_handshake_on_connect=False,
              certfile=certfile, server_side=server_side)
            self.sock = SSLWrapper(so)

        if "obfuscate" in dictionary and dictionary["obfuscate"]:

            if not ARC4:
                raise RuntimeError("ARC4 support not available")

            key = "neubot"
            if "key" in dictionary and dictionary["key"]:
                key = dictionary["key"]

            algo = ARC4.new(key)
            self.encrypt = algo.encrypt
            self.decrypt = algo.decrypt

    def connection_made(self):
        pass

    def connection_lost(self, exception):
        pass

    #
    # Low level of abstraction only:
    # When you keep a reference to the stream in your class,
    # remember to point stream.notify_closing to a function
    # that removes such reference.
    #

    def closed(self):
        self._do_close()

    def close(self):
        self._do_close()

    def _do_close(self, exception=None):
        if not self.isclosed:
            self.isclosed = 1
            if self.notify_closing:
                self.notify_closing()
                self.notify_closing = None
            self.connection_lost(exception)
            if self.parent:
                self.parent.connection_lost(self)
            self.send_octets = None
            self.send_success = None
            self.send_ticks = 0
            self.recv_maxlen = 0
            self.recv_success = None
            self.recv_ticks = 0
            self.sock.soclose()
            self.poller.close(self)

    def readtimeout(self, now):
        return (self.recv_pending and (now - self.recv_ticks) > self.timeout)

    def writetimeout(self, now):
        return (self.send_pending and (now - self.send_ticks) > self.timeout)

    # Recv path

    def start_recv(self, maxlen):
        self.recv(maxlen, self.recv_complete1)

    def recv(self, maxlen, recv_success):
        if self.isclosed:
            return

        self.recv_maxlen = maxlen
        self.recv_success = recv_success
        self.recv_ticks = ticks()
        self.recv_pending = 1

        if self.recvblocked:
            return

        self.poller.set_readable(self)

    def readable(self):
        if self.recvblocked:
            self.writable()
            return

        if self.sendblocked:
            if self.send_pending:
                self.poller.set_writable(self)
            else:
                self.poller.unset_writable(self)
            self.sendblocked = 0

        status, octets = self.sock.sorecv(self.recv_maxlen)

        if status == SUCCESS and octets:

            for stats in self.stats:
                stats.recv.account(len(octets))

            notify = self.recv_success
            self.recv_maxlen = 0
            self.recv_success = None
            self.recv_ticks = 0
            self.recv_pending = 0
            self.poller.unset_readable(self)

            if self.decrypt:
                octets = self.decrypt(octets)
            if notify:
                notify(self, octets)

            return

        if status == WANT_READ:
            self.poller.set_readable(self)
            return

        if status == WANT_WRITE:
            self.poller.set_writable(self)
            self.sendblocked = 1
            return

        if status == SUCCESS and not octets:
            self.eof = True
            self._do_close()
            return

        if status == ERROR:
            # Here octets is the exception that occurred
            self._do_close(octets)
            return

        raise RuntimeError("Unexpected status value")

    def recv_complete1(self, stream, octets):
        self.recv_complete(octets)

    def recv_complete(self, octets):
        pass

    # Send path

    def start_send(self, octets):
        self.send(octets, self.send_complete1)

    def send(self, octets, send_success):
        if self.isclosed:
            return

        if type(octets) == types.UnicodeType:
            log.warning("* send: Working-around Unicode input")
            octets = octets.encode("utf-8")
        if self.encrypt:
            octets = self.encrypt(octets)

        self.send_octets = octets
        self.send_success = send_success
        self.send_ticks = ticks()
        self.send_pending = 1

        if self.sendblocked:
            return

        self.poller.set_writable(self)

    def writable(self):
        if self.sendblocked:
            self.readable()
            return

        if self.recvblocked:
            if self.recv_pending:
                self.poller.set_readable(self)
            else:
                self.poller.unset_readable(self)
            self.recvblocked = 0

        status, count = self.sock.sosend(self.send_octets)

        if status == SUCCESS and count > 0:
            for stats in self.stats:
                stats.send.account(count)

            if count == len(self.send_octets):
                notify = self.send_success
                octets = self.send_octets
                self.send_octets = None
                self.send_success = None
                self.send_ticks = 0
                self.send_pending = 0
                self.poller.unset_writable(self)
                if notify:
                    notify(self, octets)
                return

            if count < len(self.send_octets):
                self.send_octets = buffer(self.send_octets, count)
                self.send_ticks = ticks()
                self.poller.set_writable(self)
                return

            raise RuntimeError("Sent more than expected")

        if status == WANT_WRITE:
            self.poller.set_writable(self)
            return

        if status == WANT_READ:
            self.poller.set_readable(self)
            self.recvblocked = 1
            return

        if status == ERROR:
            # Here count is the exception that occurred
            self._do_close(count)
            return

        if status == SUCCESS and count <= 0:
            raise RuntimeError("Unexpected count value")

        raise RuntimeError("Unexpected status value")

    def send_complete1(self, stream, octets):
        self.send_complete(len(octets))

    def send_complete(self, count):
        pass

### BEGIN DEPRECATED CODE ####
#

def create_stream(sock, poller, fileno, myname, peername, logname, secure,
                  certfile, server_side):
    conf = {
        "certfile": certfile,
        "server_side": server_side,
        "secure": secure,
    }
    stream = Stream(poller)
    stream.make_connection(sock)
    stream.configure(conf)
    return stream

                           #
### END DEPRECATED CODE ####

# Connect

class Connector(Pollable):

    def __init__(self, poller):
        self.poller = poller
        self.protocol = None
        self.sock = None
        self.timeout = 15
        self.timestamp = 0
        self.endpoint = None
        self.family = 0

    def connect(self, endpoint, family=socket.AF_INET):
        self.endpoint = endpoint
        self.family = family

        try:
            addrinfo = socket.getaddrinfo(endpoint[0], endpoint[1],
                                          family, socket.SOCK_STREAM)
        except socket.error, exception:
            self.connection_failed(exception)
            return

        last_exception = None
        for family, socktype, protocol, cannonname, sockaddr in addrinfo:
            try:

                sock = socket.socket(family, socktype, protocol)
                sock.setblocking(False)
                result = sock.connect_ex(sockaddr)
                if result not in INPROGRESS:
                    raise socket.error(result, os.strerror(result))

                self.sock = sock
                self.timestamp = ticks()
                self.poller.set_writable(self)
                if result != 0:
                    self.started_connecting()
                return

            except socket.error, exception:
                last_exception = exception

        self.connection_failed(last_exception)

    def connection_failed(self, exception):
        pass

    def started_connecting(self):
        pass

    def fileno(self):
        return self.sock.fileno()

    def writable(self):
        self.poller.unset_writable(self)

        # See http://cr.yp.to/docs/connect.html
        try:
            self.sock.getpeername()
        except socket.error, exception:
            if exception[0] == errno.ENOTCONN:
                try:
                    self.sock.recv(MAXBUF)
                except socket.error, exception2:
                    exception = exception2
            self.connection_failed(exception)
            return

        stream = self.protocol(self.poller)
        stream.parent = self
        stream.make_connection(self.sock)
        self.connection_made(stream)
        stream.connection_made()

    def connection_made(self, stream):
        pass

    def connection_lost(self, stream):
        pass

    def writetimeout(self, now):
        return now - self.timestamp >= self.timeout

    def closing(self, exception=None):
        self.connection_failed(exception)

### BEGIN DEPRECATED CODE ####
#

CONNECTARGS = {
    "cantconnect" : lambda: None,
    "connecting"  : lambda: None,
    "conntimeo"   : 10,
    "family"      : socket.AF_INET,
    "poller"      : poller,
    "secure"      : False,
}

class OldConnector(Pollable):
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

    def _connect(self):
        log.debug("* About to connect to %s:%s" % self.name)

        try:
            addrinfo = socket.getaddrinfo(self.address, self.port,
                                   self.family, socket.SOCK_STREAM)
        except socket.error, exception:
            log.error("* getaddrinfo() %s:%s failed" % self.name)
            log.exception()
            self.cantconnect()
            return

        for family, socktype, protocol, cannonname, sockaddr in addrinfo:
            try:
                log.debug("* Trying with %s..." % str(sockaddr))

                sock = socket.socket(family, socktype, protocol)
                sock.setblocking(False)
                result = sock.connect_ex(sockaddr)
                if result not in INPROGRESS:
                    raise socket.error(result, os.strerror(result))

                self.sock = sock
                self.begin = ticks()
                self.poller.set_writable(self)
                log.debug("* Connection to %s in progress" % str(sockaddr))
                self.connecting()
                return

            except socket.error, exception:
                log.error("* connect() to %s failed" % str(sockaddr))
                log.exception()

        log.error("* Can't connect to %s:%s" % self.name)
        self.cantconnect()

    def fileno(self):
        return self.sock.fileno()

    def writable(self):
        self.poller.unset_writable(self)

        # See http://cr.yp.to/docs/connect.html
        try:
            self.sock.getpeername()
        except socket.error, exception:
            log.error("* Can't connect to %s:%s" % self.name)
            if exception[0] == errno.ENOTCONN:
                try:
                    self.sock.recv(MAXBUF)
                except socket.error, exception:
                    log.exception()
            else:
                log.exception()
            self.cantconnect()
            return

        logname = "with %s:%s" % self.name
        stream = create_stream(self.sock, self.poller, self.sock.fileno(),
          self.sock.getsockname(), self.sock.getpeername(), logname,
          self.secure, None, False)
        log.debug("* Connected to %s:%s!" % self.name)
        self.connected(stream)

    def writetimeout(self, now):
        timedout = (now - self.begin >= self.conntimeo)
        if timedout:
            log.error("* connect() to %s:%s timed-out" % self.name)
        return timedout

    def closed(self):
        log.debug("* closing Connector to %s:%s" % self.name)
        self.cantconnect()

def connect(address, port, connected, **kwargs):
    OldConnector(address, port, connected, **kwargs)

                           #
### END DEPRECATED CODE ####

# Listen

class Listener(Pollable):

    def __init__(self, poller):
        self.protocol = None
        self.poller = poller
        self.lsock = None
        self.endpoint = None
        self.family = 0

    def listen(self, endpoint, family=socket.AF_INET):
        self.endpoint = endpoint
        self.family = family

        try:
            addrinfo = socket.getaddrinfo(endpoint[0], endpoint[1], family,
                         socket.SOCK_STREAM, 0, socket.AI_PASSIVE)
        except socket.error, exception:
            self.bind_failed(exception)
            return

        last_exception = None
        for family, socktype, protocol, canonname, sockaddr in addrinfo:
            try:

                lsock = socket.socket(family, socktype, protocol)
                lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                lsock.setblocking(False)
                lsock.bind(sockaddr)
                # Probably the backlog here is too big
                lsock.listen(128)

                self.lsock = lsock
                self.poller.set_readable(self)
                self.started_listening()
                return

            except socket.error, exception:
                last_exception = exception

        self.bind_failed(last_exception)

    def bind_failed(self, exception):
        pass

    def started_listening(self):
        pass

    def fileno(self):
        return self.lsock.fileno()

    def readable(self):
        try:
            sock, sockaddr = self.lsock.accept()
            sock.setblocking(False)
        except socket.error, exception:
            self.accept_failed(exception)
            return

        stream = self.protocol(self.poller)
        stream.parent = self
        stream.make_connection(sock)
        self.connection_made(stream)
        stream.connection_made()

    def accept_failed(self, exception):
        pass

    def connection_made(self, stream):
        pass

    def connection_lost(self, stream):
        pass

    def closing(self, exception=None):
        self.bind_failed(exception)     # XXX

### BEGIN DEPRECATED CODE ####
#

LISTENARGS = {
    "cantbind"   : lambda: None,
    "certfile"   : None,
    "family"     : socket.AF_INET,
    "listening"  : lambda: None,
    "poller"     : poller,
    "secure"     : False,
}

class OldListener(Pollable):
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

    def _listen(self):
        log.debug("* About to bind %s:%s" % self.name)

        try:
            addrinfo = socket.getaddrinfo(self.address, self.port, self.family,
                                   socket.SOCK_STREAM, 0, socket.AI_PASSIVE)
        except socket.error, exception:
            log.error("* getaddrinfo() %s:%s failed" % self.name)
            log.exception()
            self.cantbind()
            return

        for family, socktype, protocol, canonname, sockaddr in addrinfo:
            try:
                log.debug("* Trying with %s..." % str(sockaddr))

                sock = socket.socket(family, socktype, protocol)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.setblocking(False)
                sock.bind(sockaddr)
                # Probably the backlog here is too big
                sock.listen(128)

                self.sock = sock
                self.poller.set_readable(self)
                log.debug("* Bound with %s" % str(sockaddr))
                log.debug("* Listening at %s:%s..." % self.name)
                self.listening()
                return

            except socket.error, exception:
                log.error("* bind() with %s failed" % str(sockaddr))
                log.exception()

        log.error("* Can't bind %s:%s" % self.name)
        self.cantbind()

    def fileno(self):
        return self.sock.fileno()

    def readable(self):

        try:
            sock, sockaddr = self.sock.accept()
            sock.setblocking(False)
        except socket.error:
            log.exception()
            return

        logname = "with %s" % str(sock.getpeername())
        stream = create_stream(sock, self.poller, sock.fileno(),
          sock.getsockname(), sock.getpeername(), logname,
          self.secure, self.certfile, True)
        log.debug("* Got connection from %s" % str(sock.getpeername()))
        self.accepted(stream)

def listen(address, port, accepted, **kwargs):
    OldListener(address, port, accepted, **kwargs)

                           #
### END DEPRECATED CODE ####

# Unit test

import getopt

class Discard:
    def __init__(self, stream):
        self.timestamp = ticks()
        sched(1, self.update_stats)
        self.received = 0
        stream.recv(MAXBUF, self.got_data)

    def got_data(self, stream, octets):
        self.received += len(octets)
        stream.recv(MAXBUF, self.got_data)

    def update_stats(self):
        sched(1, self.update_stats)
        now = ticks()
        speed = self.received / (now - self.timestamp)
        print "Current speed: ", speed_formatter(speed)
        self.timestamp = now
        self.received = 0

class Echo:
    def __init__(self, stream):
        stream.recv(MAXBUF, self.got_data)

    def got_data(self, stream, octets):
        stream.send(octets, self.sent_data)

    def sent_data(self, stream, octets):
        stream.recv(MAXBUF, self.got_data)

class Source:
    def __init__(self, stream):
        self.buffer = "A" * MAXBUF
        stream.send(self.buffer, self.sent_data)

    def sent_data(self, stream, octets):
        stream.send(self.buffer, self.sent_data)

from neubot import version

USAGE = "Usage: %s [-6SlVv] [-C cert] [-n timeout] [-P proto] [--help] address port\n"

HELP = USAGE +								\
"Options:\n"								\
"  -6         : Use IPv6 rather than IPv4.\n"				\
"  -C cert    : Secure listen().  Use OpenSSL cert.\n"                  \
"  --help     : Print this help screen and exit.\n"			\
"  -l         : Listen for incoming connections.\n"			\
"  -n timeout : Time-out after timeout seconds.\n"			\
"  -P proto   : Run the specified protocol.\n"				\
"               Avail. protos: echo, discard.\n"			\
"  -S         : Secure connect().  Use OpenSSL.\n"			\
"  -V         : Print version number and exit.\n"			\
"  -v         : Run the program in verbose mode.\n"

def connected(stream):
    stream.close()

def main(args):
    family = socket.AF_INET
    srvmode = False
    timeout = 10
    secure = False
    certfile = None
    proto = None
    try:
        options, arguments = getopt.getopt(args[1:], "6C:ln:P:SVv", ["help"])
    except getopt.GetoptError:
        sys.stderr.write(USAGE % args[0])
        sys.exit(1)
    for name, value in options:
        if name == "-6":
            family = socket.AF_INET6
        elif name == "-C":
            certfile = value
        elif name == "--help":
            sys.stdout.write(HELP % args[0])
            sys.exit(0)
        elif name == "-l":
            srvmode = True
        elif name == "-n":
            try:
                timeout = int(value)
            except ValueError:
                timeout = -1
            if timeout < 0:
                log.error("Bad timeout")
                sys.exit(1)
        elif name == "-P":
            proto = value
        elif name == "-S":
            secure = True
        elif name == "-V":
            sys.stdout.write(version + "\n")
            sys.exit(0)
        elif name == "-v":
            log.verbose()
    if len(arguments) != 2:
        sys.stderr.write(USAGE % args[0])
        sys.exit(1)
    if proto == "discard":
        if srvmode:
            listen("127.0.0.1", "8009", accepted=Discard)
        else:
            connect("127.0.0.1", "8009", connected=Source)
        loop()
        sys.exit(0)
    elif proto == "echo":
        listen("127.0.0.1", "8007", accepted=Echo)
        loop()
        sys.exit(0)
    elif proto:
        sys.stderr.write(USAGE)
        sys.exit(1)
    if srvmode:
        listen(arguments[0], arguments[1], connected, family=family,
               secure=secure, certfile=certfile)
    else:
        connect(arguments[0], arguments[1], connected, conntimeo=timeout,
                family=family, secure=secure)
    loop()

if __name__ == "__main__":
    main(sys.argv)
