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

import collections
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
    def __init__(self, poller_):
        self.poller = poller_
        self.parent = None

        self.sock = None
        self.filenum = -1
        self.myname = None
        self.peername = None
        self.logname = None

        self.timeout = TIMEOUT
        self.encrypt = None
        self.decrypt = None

        self.send_pos = 0
        self.send_octets = None
        self.send_queue = collections.deque()
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

        self.measurer = None

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

        if "measurer" in dictionary and dictionary["measurer"]:
            self.measurer = dictionary["measurer"]

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

    def closed(self, exception=None):
        self._do_close(exception)

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
            if self.measurer:
                self.measurer.dead = True
            self.send_pos = 0
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

            if self.measurer:
                self.measurer.recv += len(octets)
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

        if self.send_pending:
            self.send_queue.append(octets)
            return

        self.send_pos = 0
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

        subset = buffer(self.send_octets, self.send_pos)
        status, count = self.sock.sosend(subset)

        if status == SUCCESS and count > 0:

            if self.measurer:
                self.measurer.send += count
            for stats in self.stats:
                stats.send.account(count)

            self.send_pos += count

            if self.send_pos == len(self.send_octets):

                #
                # XXX Note that the following snippet is potentially
                # wrong as long as each send() is free to set the call-
                # back to notify `send complete` to.  I don't want to
                # fix it because I plan to modify the stream API so
                # that this is not an issue anymore.
                #

                if len(self.send_queue) > 0:
                    self.send_octets = self.send_queue.popleft()
                    self.send_ticks = ticks()
                    return

                notify = self.send_success
                octets = self.send_octets
                self.send_pos = 0
                self.send_octets = None
                self.send_success = None
                self.send_ticks = 0
                self.send_pending = 0
                self.poller.unset_writable(self)
                if notify:
                    notify(self, octets)
                return

            if self.send_pos < len(self.send_octets):
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

def create_stream(sock, poller_, fileno, myname, peername, logname, secure,
                  certfile, server_side):
    conf = {
        "certfile": certfile,
        "server_side": server_side,
        "secure": secure,
    }
    stream = Stream(poller_)
    stream.make_connection(sock)
    stream.configure(conf)
    return stream

                           #
### END DEPRECATED CODE ####

# Connect

class Connector(Pollable):

    def __init__(self, poller_):
        self.poller = poller_
        self.protocol = None
        self.sock = None
        self.timeout = 15
        self.timestamp = 0
        self.endpoint = None
        self.family = 0
        self.measurer = None

    def connect(self, endpoint, family=socket.AF_INET, measurer_=None, sobuf=0):
        self.endpoint = endpoint
        self.family = family
        self.measurer = measurer_

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
                if sobuf:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, sobuf)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, sobuf)
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

        if self.measurer:
            rtt = ticks() - self.timestamp
            self.measurer.rtts.append(rtt)

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
        except socket.error:
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

            except socket.error:
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

    def closed(self, exception=None):
        log.debug("* closing Connector to %s:%s" % self.name)
        self.cantconnect()

def connect(address, port, connected, **kwargs):
    OldConnector(address, port, connected, **kwargs)

                           #
### END DEPRECATED CODE ####

# Listen

class Listener(Pollable):

    def __init__(self, poller_):
        self.protocol = None
        self.poller = poller_
        self.lsock = None
        self.endpoint = None
        self.family = 0

    def listen(self, endpoint, family=socket.AF_INET, sobuf=0):
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
                if sobuf:
                    lsock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, sobuf)
                    lsock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, sobuf)
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
        except socket.error:
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

            except socket.error:
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

# Measurer

class StreamMeasurer(object):
    dead = False
    recv = 0
    send = 0

class Measurer(object):
    def __init__(self):
        self.last = ticks()
        self.streams = []
        self.rtts = []

    def connect(self, connector, endpoint, family=socket.AF_INET, sobuf=0):
        connector.connect(endpoint, family, self, sobuf)

    def register_stream(self, stream):
        m = StreamMeasurer()
        stream.configure({"measurer": m})
        self.streams.append(m)

    def measure(self):
        now = ticks()
        delta = now - self.last
        self.last = now

        if delta <= 0:
            return None

        rttavg = 0
        rttdetails = []
        if len(self.rtts) > 0:
            for rtt in self.rtts:
                rttavg += rtt
            rttavg = rttavg / len(self.rtts)
            rttdetails = self.rtts
            self.rtts = []

        alive = []
        recvsum = 0
        sendsum = 0
        for m in self.streams:
            recvsum += m.recv
            sendsum += m.send
            if not m.dead:
                alive.append(m)
        recvavg = recvsum / delta
        sendavg = sendsum / delta
        percentages = []
        for m in self.streams:
            recvp, sendp = 0, 0
            if recvsum:
                recvp = 100 * m.recv / recvsum
            if sendsum:
                sendp = 100 * m.send / sendsum
            percentages.append((recvp, sendp))
            if not m.dead:
                m.recv = m.send = 0
        self.streams = alive

        return rttavg, rttdetails, recvavg, sendavg, percentages

class VerboseMeasurer(Measurer):
    def __init__(self, poller_, output=sys.stdout, interval=1):
        Measurer.__init__(self)

        self.poller = poller_
        self.output = output
        self.interval = interval

    def start(self):
        self.poller.sched(self.interval, self.report)
        self.output.write("\t\trtt\t\trecv\t\t\tsend\n")

    def report(self):
        self.poller.sched(self.interval, self.report)

        rttavg, rttdetails, recvavg, sendavg, percentages = self.measure()

        if len(rttdetails) > 0:
            rttavg = "%d us" % int(1000000 * rttavg)
            self.output.write("\t\t%s\t\t---\t\t---\n" % rttavg)
            if len(rttdetails) > 1:
                for detail in rttdetails:
                    detail = "%d us" % int(1000000 * detail)
                    self.output.write("\t\t  %s\t\t---\t\t---\n" % detail)

        if len(percentages) > 0:
            recv, send = speed_formatter(recvavg), speed_formatter(sendavg)
            self.output.write("\t\t---\t\t%s\t\t%s\n" % (recv, send))
            if len(percentages) > 1:
                for val in percentages:
                    val = map(lambda x: "%.2f%%" % x, val)
                    self.output.write("\t\t---\t\t  %s\t\t  %s\n" %
                                      (val[0], val[1]))

# Verboser

class StreamVerboser(object):
    def connection_lost(self, logname, eof, exception):
        if exception:
            log.error("* Connection %s: %s" % (logname, exception))
        elif eof:
            log.debug("* Connection %s: EOF" % (logname))
        else:
            log.error("* Connection %s: lost (no reason given)" % (logname))

    def bind_failed(self, endpoint, exception, fatal=False):
        log.error("* Bind %s failed: %s" % (endpoint, exception))
        if fatal:
            sys.exit(1)

    def started_listening(self, endpoint):
        log.debug("* Listening at %s" % str(endpoint))

    def connection_made(self, logname):
        log.debug("* Connection made %s" % str(logname))

    def connection_failed(self, endpoint, exception, fatal=False):
        log.error("* Connection to %s failed: %s" % (endpoint, exception))
        if fatal:
            sys.exit(1)

    def started_connecting(self, endpoint):
        log.debug("* Connecting to %s ..." % str(endpoint))

# Unit test

from neubot.options import OptionParser
import getopt

measurer = VerboseMeasurer(poller)
verboser = StreamVerboser()

KIND_NONE = 0
KIND_DISCARD = 1
KIND_CHARGEN = 2

class GenericProtocol(Stream):
    def __init__(self, poller_):
        Stream.__init__(self, poller_)
        self.buffer = "A" * MAXBUF
        self.kind = KIND_NONE

    def connection_made(self):
        verboser.connection_made(self.logname)
        measurer.register_stream(self)
        if self.kind == KIND_DISCARD:
            self.start_recv(MAXBUF)
            return
        if self.kind == KIND_CHARGEN:
            self.start_send(self.buffer)
            return
        self.close()

    def recv_complete(self, octets):
        self.start_recv(MAXBUF)

    def send_complete(self, octets):
        self.start_send(self.buffer)

    def connection_lost(self, exception):
        verboser.connection_lost(self.logname, self.eof, exception)

class GenericListener(Listener):
    def __init__(self, poller_, dictionary, kind):
        Listener.__init__(self, poller_)
        self.protocol = GenericProtocol
        self.dictionary = dictionary
        self.kind = kind

    def bind_failed(self, exception):
        verboser.bind_failed(self.endpoint, exception, fatal=True)

    def started_listening(self):
        verboser.started_listening(self.endpoint)

    def connection_made(self, stream):
        stream.configure(self.dictionary)
        stream.kind = self.kind

class GenericConnector(Connector):
    def __init__(self, poller_, dictionary, kind):
        Connector.__init__(self, poller_)
        self.protocol = GenericProtocol
        self.dictionary = dictionary
        self.kind = kind

    def connection_failed(self, exception):
        verboser.connection_failed(self.endpoint, exception, fatal=True)

    def started_connecting(self):
        verboser.started_connecting(self.endpoint)

    def connection_made(self, stream):
        stream.configure(self.dictionary)
        stream.kind = self.kind

USAGE = """Neubot net -- Test unit for the asynchronous network layer

Usage: neubot net [-Vv] [-D macro[=value]] [-f file] [--help]

Options:
    -D macro[=value]   : Set the value of the macro `macro`.
    -f file            : Read options from file `file`.
    --help             : Print this help screen and exit.
    -V                 : Print version number and exit.
    -v                 : Run the program in verbose mode.

Macros (defaults in square brackets):
    address=addr       : Select the address to use [127.0.0.1]
    certfile           : Path to private key and certificate file
                         to be used together with `-D secure` []
    count=N            : Spawn N client connections at a time [1]
    key=KEY            : Use KEY to initialize ARC4 stream []
    listen             : Listen for incoming connections [False]
    obfuscate          : Obfuscate traffic using ARC4 [False]
    port=port          : Select the port to use [12345]
    proto=proto        : Override protocol [] (see below).
    secure             : Secure the communication using SSL [False]
    sobuf=size         : Set socket buffer size to `size` []

Protocols:
    There are two available protocols: `discard` and `chargen`.
    When running in server mode the default is `chargen` and when
    running in client mode the default is `discard`.
"""

VERSION = "Neubot 0.3.2\n"

def main(args):

    conf = OptionParser()
    conf.set_option("net", "address", "127.0.0.1")
    conf.set_option("net", "certfile", "")
    conf.set_option("net", "count", "1")
    conf.set_option("net", "key", "")
    conf.set_option("net", "listen", "False")
    conf.set_option("net", "obfuscate", "False")
    conf.set_option("net", "port", "12345")
    conf.set_option("net", "proto", "")
    conf.set_option("net", "secure", "False")
    conf.set_option("net", "sobuf", "0")

    try:
        options, arguments = getopt.getopt(args[1:], "D:f:Vv", ["help"])
    except getopt.GetoptError:
        sys.stderr.write(USAGE)
        sys.exit(1)

    if len(arguments) > 0:
        sys.stdout.write(USAGE)
        sys.exit(1)

    for name, value in options:
        if name == "-D":
             conf.register_opt(value, "net")
             continue
        if name == "-f":
             conf.register_file(value)
             continue
        if name == "--help":
             sys.stdout.write(USAGE)
             sys.exit(0)
        if name == "-V":
             sys.stdout.write(VERSION)
             sys.exit(0)
        if name == "-v":
             log.verbose()
             continue

    conf.merge_files()
    conf.merge_environ()
    conf.merge_opts()

    measurer.start()

    address = conf.get_option("net", "address")
    count = conf.get_option_uint("net", "count")
    listen = conf.get_option_bool("net", "listen")
    port = conf.get_option_uint("net", "port")
    proto = conf.get_option("net", "proto")
    sobuf = conf.get_option_uint("net", "sobuf")

    dictionary = {
        "certfile": conf.get_option("net", "certfile"),
        "key": conf.get_option("net", "key"),
        "obfuscate": conf.get_option_bool("net", "obfuscate"),
        "secure": conf.get_option_bool("net", "secure"),
    }

    endpoint = (address, port)

    if proto == "chargen":
        kind = KIND_CHARGEN
    elif proto == "discard":
        kind = KIND_DISCARD
    elif proto == "":
        if listen:
            kind = KIND_CHARGEN
        else:
            kind = KIND_DISCARD
    else:
        sys.stderr.write(USAGE)
        sys.exit(1)

    if listen:
        dictionary["server_side"] = True
        listener = GenericListener(poller, dictionary, kind)
        listener.listen(endpoint, sobuf=sobuf)
        loop()
        sys.exit(0)

    while count > 0:
        count = count - 1
        connector = GenericConnector(poller, dictionary, kind)
        measurer.connect(connector, endpoint, sobuf=sobuf)
    loop()
    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)
