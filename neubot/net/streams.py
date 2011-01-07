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
    import ssl
except ImportError:
    ssl = None

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.net.pollers import sched
from neubot.net.pollers import Pollable
from neubot.net.pollers import poller
from neubot.net.pollers import loop
from neubot.utils import unit_formatter
from neubot.utils import ticks
from neubot.utils import fixkwargs
from neubot import log

SUCCESS, ERROR, WANT_READ, WANT_WRITE = range(0,4)
TIMEOUT = 300

ISCLOSED = 1<<0
SEND_PENDING = 1<<1
SENDBLOCKED = 1<<2
RECV_PENDING = 1<<3
RECVBLOCKED = 1<<4
ISSENDING = 1<<5
ISRECEIVING = 1<<6
EOF = 1<<7

MAXBUF = 1<<18

class Stream(Pollable):
    def __init__(self, poller, fileno, myname, peername, logname):
        self.poller = poller
        self._fileno = fileno
        self.myname = myname
        self.peername = peername
        self.logname = logname
        self.handleReadable = None
        self.handleWritable = None
        self.send_octets = None
        self.send_success = None
        self.send_ticks = 0
        self.send_pos = 0
        self.send_error = None
        self.recv_maxlen = 0
        self.recv_success = None
        self.recv_ticks = 0
        self.recv_error = None
        self.eof = False
        self.timeout = TIMEOUT
        self.notify_closing = None
        self.context = None
        self.stats = []
        self.stats.append(self.poller.stats)
        self.flags = 0

    def __del__(self):
        pass

    def fileno(self):
        return self._fileno

    #
    # When you keep a reference to the stream in your class,
    # remember to point stream.notify_closing to a function
    # that removes such reference.
    #

    def closing(self):
        self._do_close()

    def close(self):
        self._do_close()

    def _do_close(self):
        if not (self.flags & ISCLOSED):
            log.debug("* Closing connection %s" % self.logname)
            self.flags |= ISCLOSED
            if self.recv_error:
                self.recv_error(self)
                self.recv_error = None
            if self.send_error:
                self.send_error(self)
                self.send_error = None
            if self.notify_closing:
                self.notify_closing()
                self.notify_closing = None
            self.send_octets = None
            self.send_success = None
            self.send_ticks = 0
            self.send_pos = 0
            self.recv_maxlen = 0
            self.recv_success = None
            self.recv_ticks = 0
            self.handleReadable = None
            self.handleWritable = None
            self.soclose()
            self.poller.close(self)

    def readtimeout(self, now):
        return (self.flags & RECV_PENDING and
         (now - self.recv_ticks) > self.timeout)

    def writetimeout(self, now):
        return (self.flags & SEND_PENDING and
         (now - self.send_ticks) > self.timeout)

    #
    # Make sure that we set/unset readable/writable only if
    # needed, because the operation is a bit expensive (you
    # add/remove entries to/from an hash table).
    #

    def readable(self):
        self.handleReadable()

    def writable(self):
        self.handleWritable()

    def set_readable(self, func):
        if not self.handleReadable:
            self.poller.set_readable(self)
        if self.handleReadable != func:
            self.handleReadable = func

    def set_writable(self, func):
        if not self.handleWritable:
            self.poller.set_writable(self)
        if self.handleWritable != func:
            self.handleWritable = func

    def unset_readable(self):
        if self.handleReadable:
            self.poller.unset_readable(self)
            self.handleReadable = None

    def unset_writable(self):
        if self.handleWritable:
            self.poller.unset_writable(self)
            self.handleWritable = None

    def recv(self, maxlen, recv_success, recv_error=None):
        if not (self.flags & ISCLOSED):
            self.recv_maxlen = maxlen
            self.recv_success = recv_success
            self.recv_ticks = ticks()
            self.flags |= RECV_PENDING
            self.recv_error = recv_error
            #
            # ISRECEIVING means we're already inside _do_recv().
            # We don't want to invoke _do_recv() again, in this
            # case, because there' the risk of infinite recursion.
            #
            if not (self.flags & ISRECEIVING):
                self._do_recv()

    def _do_recv(self):
        #
        # RECVBLOCKED means that the underlying socket is SSL,
        # _and_ that SSL_write() returned WANT_READ, so we need
        # to wait for the underlying socket to become readable
        # to invoke SSL_write() again--and of course we can't
        # recv() until this happens.
        #
        if not (self.flags & RECVBLOCKED):
            self.flags |= ISRECEIVING
            panic = ""
            if self.flags & SENDBLOCKED:
                #
                # SENDBLOCKED is the symmetrical of RECVBLOCKED.
                # If we're here it means that SSL_read() returned
                # WANT_WRITE and we temporarily needed to block
                # send().
                #
                if self.flags & SEND_PENDING:
                    self.set_writable(self._do_send)
                else:
                    self.unset_writable()
                self.flags &= ~SENDBLOCKED
            status, octets = self.sorecv(self.recv_maxlen)
            if status == SUCCESS:
                if octets:
                    for stats in self.stats:
                        stats.recv.account(len(octets))
                    notify = self.recv_success
                    self.recv_maxlen = 0
                    self.recv_success = None
                    self.recv_ticks = 0
                    #
                    # Unset RECV_PENDING but wait before unsetting
                    # readable because notify() might invoke recv()
                    # again--and so we check RECV_PENDING again
                    # after notify().
                    #
                    self.flags &= ~RECV_PENDING
                    self.recv_error = None
                    if notify:
                        notify(self, octets)
                    #
                    # Be careful because notify() is an user-defined
                    # callback that might invoke send()--which might
                    # need to block recv()--or close().
                    #
                    if not (self.flags & (RECVBLOCKED|ISCLOSED)):
                        if self.flags & RECV_PENDING:
                            self.set_readable(self._do_recv)
                        else:
                            self.unset_readable()
                else:
                    log.debug("* Connection %s: EOF" % self.logname)
                    self.flags |= EOF
                    self.eof = True
                    self._do_close()
            elif status == WANT_READ:
                self.set_readable(self._do_recv)
            elif status == WANT_WRITE:
                self.set_writable(self._do_recv)
                self.flags |= SENDBLOCKED
            elif status == ERROR:
                log.error("* Connection %s: recv error" % self.logname)
                self._do_close()
            else:
                panic = "Unexpected status value"
            self.flags &= ~ISRECEIVING
            if panic:
                raise Exception(panic)

    #
    # send() is symmetrical to recv() and so to the comments
    # to recv()'s implementation are also applicable here.
    #

    def send(self, octets, send_success, send_error=None):
        if not (self.flags & ISCLOSED):
            #
            # Make sure we don't start sending an Unicode string
            # because _do_send() assumes 8 bits encoding and would
            # go very likely to 'Internal error' state if passed
            # an unicode encoding.
            #
            if type(octets) == types.UnicodeType:
                log.warning("* send: Working-around Unicode input")
                octets = octets.encode("utf-8")
            self.send_octets = octets
            self.send_pos = 0
            self.send_success = send_success
            self.send_ticks = ticks()
            self.flags |= SEND_PENDING
            self.send_error = send_error
            if not (self.flags & ISSENDING):
                self._do_send()

    def _do_send(self):
        if not (self.flags & SENDBLOCKED):
            self.flags |= ISSENDING
            panic = ""
            if self.flags & RECVBLOCKED:
                if self.flags & RECV_PENDING:
                    self.set_readable(self._do_recv)
                else:
                    self.unset_readable()
                self.flags &= ~RECVBLOCKED
            subset = buffer(self.send_octets, self.send_pos)
            status, count = self.sosend(subset)
            if status == SUCCESS:
                if count > 0:
                    for stats in self.stats:
                        stats.send.account(count)
                    self.send_pos += count
                    if self.send_pos < len(self.send_octets):
                        self.send_ticks = ticks()
                        self.set_writable(self._do_send)
                    elif self.send_pos == len(self.send_octets):
                        notify = self.send_success
                        octets = self.send_octets
                        self.send_octets = None
                        self.send_pos = 0
                        self.send_success = None
                        self.send_ticks = 0
                        self.flags &= ~SEND_PENDING
                        self.send_error = None
                        if notify:
                            notify(self, octets)
                        if not (self.flags & (SENDBLOCKED|ISCLOSED)):
                            if self.flags & SEND_PENDING:
                                self.set_writable(self._do_send)
                            else:
                                self.unset_writable()
                    else:
                        panic = "Internal error"
                else:
                    panic = "Unexpected count value"
            elif status == WANT_WRITE:
                self.set_writable(self._do_send)
            elif status == WANT_READ:
                self.set_readable(self._do_send)
                self.flags |= RECVBLOCKED
            elif status == ERROR:
                log.error("* Connection %s: send error" % self.logname)
                self._do_close()
            else:
                panic = "Unexpected status value"
            self.flags &= ~ISSENDING
            if panic:
                raise Exception(panic)

    #
    # These are the methods that an "underlying socket"
    # implementation should override.
    #

    def soclose(self):
        raise NotImplementedError

    def sorecv(self, maxlen):
        raise NotImplementedError

    def sosend(self, octets):
        raise NotImplementedError

if ssl:
    class StreamSSL(Stream):
        def __init__(self, ssl_sock, poller, fileno, myname, peername, logname):
            self.ssl_sock = ssl_sock
            Stream.__init__(self, poller, fileno, myname, peername, logname)
            self.need_handshake = True

        def __del__(self):
            Stream.__del__(self)

        def soclose(self):
            self.ssl_sock.close()

        def sorecv(self, maxlen):
            try:
                if self.need_handshake:
                    self.ssl_sock.do_handshake()
                    self.need_handshake = False
                octets = self.ssl_sock.read(maxlen)
                return SUCCESS, octets
            except ssl.SSLError, (code, reason):
                if code == ssl.SSL_ERROR_WANT_READ:
                    return WANT_READ, ""
                elif code == ssl.SSL_ERROR_WANT_WRITE:
                    return WANT_WRITE, ""
                else:
                    log.exception()
                    return ERROR, ""

        def sosend(self, octets):
            try:
                if self.need_handshake:
                    self.ssl_sock.do_handshake()
                    self.need_handshake = False
                count = self.ssl_sock.write(octets)
                return SUCCESS, count
            except ssl.SSLError, (code, reason):
                if code == ssl.SSL_ERROR_WANT_READ:
                    return WANT_READ, 0
                elif code == ssl.SSL_ERROR_WANT_WRITE:
                    return WANT_WRITE, 0
                else:
                    log.exception()
                    return ERROR, 0

class StreamSocket(Stream):
    def __init__(self, sock, poller, fileno, myname, peername, logname):
        self.sock = sock
        Stream.__init__(self, poller, fileno, myname, peername, logname)

    def __del__(self):
        Stream.__del__(self)

    def soclose(self):
        self.sock.close()

    def sorecv(self, maxlen):
        try:
            octets = self.sock.recv(maxlen)
            return SUCCESS, octets
        except socket.error, (code, reason):
            if code in [errno.EAGAIN, errno.EWOULDBLOCK]:
                return WANT_READ, ""
            else:
                log.exception()
                return ERROR, ""

    def sosend(self, octets):
        try:
            count = self.sock.send(octets)
            return SUCCESS, count
        except socket.error, (code, reason):
            if code in [errno.EAGAIN, errno.EWOULDBLOCK]:
                return WANT_WRITE, 0
            else:
                log.exception()
                return ERROR, 0

def create_stream(sock, poller, fileno, myname, peername, logname, secure,
                  certfile, server_side):
    if ssl:
        if secure:
            try:
                sock = ssl.wrap_socket(sock, do_handshake_on_connect=False,
                  certfile=certfile, server_side=server_side)
            except ssl.SSLError, exception:
                raise socket.error(exception)
            stream = StreamSSL(sock, poller, fileno, myname, peername, logname)
            return stream
    if type(sock) == socket.SocketType and secure:
        raise socket.error("SSL support not available")
    stream = StreamSocket(sock, poller, fileno, myname, peername, logname)
    return stream

# Connect

#
# XXX IIRC connect() returns 0 only if connecting to 127.0.0.1:port.
#
# We have the same code path for connect_ex() returning 0 and returning
# one of [EINPROGRESS, EWOULDBLOCK].  This is not very efficient because
# when it returns 0 we know we are already connected and so it would be
# more logical not to check for writability.  But there is also value
# in sharing the same code path, namely that testing is simpler because
# we don't have to test the [EINPROGRESS, EWOULDBLOCK] corner case.
#

# Winsock returns EWOULDBLOCK
INPROGRESS = [ 0, errno.EINPROGRESS, errno.EWOULDBLOCK, errno.EAGAIN ]

CONNECTARGS = {
    "cantconnect" : lambda: None,
    "connecting"  : lambda: None,
    "conntimeo"   : 10,
    "family"      : socket.AF_INET,
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

    def closing(self):
        log.debug("* closing Connector to %s:%s" % self.name)
        self.cantconnect()

def connect(address, port, connected, **kwargs):
    Connector(address, port, connected, **kwargs)

# Listen

LISTENARGS = {
    "cantbind"   : lambda: None,
    "certfile"   : None,
    "family"     : socket.AF_INET,
    "listening"  : lambda: None,
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
    Listener(address, port, accepted, **kwargs)

# TODO move to neubot/utils.py
def speed_formatter(speed, base10=True, bytes=False):
    unit = "Byte/s"
    if not bytes:
        speed = speed * 8
        unit = "bit/s"
    return unit_formatter(speed, base10, unit)

# Unit test

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

    def __del__(self):
        pass

class Echo:
    def __init__(self, stream):
        stream.recv(MAXBUF, self.got_data)

    def got_data(self, stream, octets):
        stream.send(octets, self.sent_data)

    def sent_data(self, stream, octets):
        stream.recv(MAXBUF, self.got_data)

    def __del__(self):
        pass

class Source:
    def __init__(self, stream):
        self.buffer = "A" * MAXBUF
        stream.send(self.buffer, self.sent_data)

    def sent_data(self, stream, octets):
        stream.send(self.buffer, self.sent_data)

    def __del__(self):
        pass

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.stdout.write("Usage: %s discard|echo|source\n" % sys.argv[0])
        sys.exit(1)
    elif sys.argv[1] == "discard":
        listen("127.0.0.1", "8009", accepted=Discard)
        loop()
        sys.exit(0)
    elif sys.argv[1] == "echo":
        listen("127.0.0.1", "8007", accepted=Echo)
        loop()
        sys.exit(0)
    elif sys.argv[1] == "source":
        connect("127.0.0.1", "8009", connected=Source)
        loop()
        sys.exit(0)
    else:
        sys.stderr.write("Usage: %s discard|echo|source\n" % sys.argv[0])
        sys.exit(1)
