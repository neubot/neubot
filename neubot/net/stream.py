# neubot/net/stream.py

#
# Copyright (c) 2010-2011 Simone Basso <bassosimone@gmail.com>,
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

import collections
import errno
import os
import socket
import sys
import types
import getopt

try:
    import ssl
except ImportError:
    ssl = None

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.net.poller import Pollable
from neubot.options import OptionParser
from neubot.net.poller import POLLER
from neubot.utils import become_daemon
from neubot.utils import speed_formatter
from neubot.arcfour import arcfour_new
from neubot.times import ticks
from neubot.log import LOG

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

        def soclose(self):
            try:
                self.sock.close()
            except ssl.SSLError:
                pass

        def sorecv(self, maxlen):
            try:
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

    """To implement the protocol syntax, subclass this class and
       implement the finite state machine described in the file
       `doc/protocol.png`.  The low level finite state machines for
       the send and recv path are documented, respectively, in
       `doc/sendpath.png` and `doc/recvpath.png`."""

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
        self.send_queue = collections.deque()
        self.send_ticks = 0
        self.recv_maxlen = 0
        self.recv_ticks = 0

        self.eof = False
        self.isclosed = 0
        self.send_pending = 0
        self.sendblocked = 0
        self.recv_pending = 0
        self.recvblocked = 0
        self.kickoffssl = 0

        self.measurer = None

    def fileno(self):
        return self.filenum

    def make_connection(self, sock):
        if self.sock:
            raise RuntimeError("make_connection() invoked more than once")
        self.filenum = sock.fileno()
        self.myname = sock.getsockname()
        self.peername = sock.getpeername()
        self.logname = str((self.myname, self.peername))
        self.sock = SocketWrapper(sock)

    def configure(self, dictionary):
        if not self.sock:
            raise RuntimeError("configure() invoked before make_connection()")

        if "secure" in dictionary and dictionary["secure"]:
            if not ssl:
                raise RuntimeError("SSL support not available")
            if hasattr(self.sock, "need_handshake"):
                raise RuntimeError("Can't wrap SSL socket twice")

            server_side = False
            if "server_side" in dictionary and dictionary["server_side"]:
                server_side = dictionary["server_side"]
            certfile = None
            if "certfile" in dictionary and dictionary["certfile"]:
                certfile = dictionary["certfile"]

            so = ssl.wrap_socket(self.sock.sock, do_handshake_on_connect=False,
              certfile=certfile, server_side=server_side)
            self.sock = SSLWrapper(so)

            if not server_side:
                self.kickoffssl = 1

        if "obfuscate" in dictionary and dictionary["obfuscate"]:
            key = None
            if "key" in dictionary and dictionary["key"]:
                key = dictionary["key"]

            self.encrypt = arcfour_new(key).encrypt
            self.decrypt = arcfour_new(key).decrypt

        if "measurer" in dictionary and dictionary["measurer"]:
            self.measurer = dictionary["measurer"]

    def connection_made(self):
        pass

    # Close path

    def connection_lost(self, exception):
        pass

    def closed(self, exception=None):
        self._do_close(exception)

    def shutdown(self):
        self._do_close()

    def _do_close(self, exception=None):
        if self.isclosed:
            return

        self.isclosed = 1

        self.connection_lost(exception)
        if self.parent:
            self.parent.connection_lost(self)

        if self.measurer:
            self.measurer.dead = True

        self.send_octets = None
        self.send_ticks = 0
        self.recv_maxlen = 0
        self.recv_ticks = 0
        self.sock.soclose()

        self.poller.close(self)

    # Timeouts

    def readtimeout(self, now):
        return (self.recv_pending and (now - self.recv_ticks) > self.timeout)

    def writetimeout(self, now):
        return (self.send_pending and (now - self.send_ticks) > self.timeout)

    # Recv path

    def start_recv(self, maxlen=MAXBUF):
        if self.isclosed:
            return
        if self.recv_pending:
            return

        self.recv_maxlen = maxlen
        self.recv_ticks = ticks()
        self.recv_pending = 1

        if self.recvblocked:
            return

        self.poller.set_readable(self)

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

        if self.kickoffssl:
            self.kickoffssl = 0
            self.readable()

    def readable(self):
        if self.recvblocked:
            self.poller.set_writable(self)
            if not self.recv_pending:
                self.poller.unset_readable(self)
            self.recvblocked = 0
            self.writable()
            return

        status, octets = self.sock.sorecv(self.recv_maxlen)

        if status == SUCCESS and octets:

            if self.measurer:
                self.measurer.recv += len(octets)

            self.recv_maxlen = 0
            self.recv_ticks = 0
            self.recv_pending = 0
            self.poller.unset_readable(self)

            if self.decrypt:
                octets = self.decrypt(octets)

            self.recv_complete(octets)
            return

        if status == WANT_READ:
            return

        if status == WANT_WRITE:
            self.poller.unset_readable(self)
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

    def recv_complete(self, octets):
        pass

    # Send path

    def start_send(self, octets):
        if self.isclosed:
            return

        if type(octets) == types.UnicodeType:
            LOG.warning("* send: Working-around Unicode input")
            octets = octets.encode("utf-8")
        if self.encrypt:
            octets = self.encrypt(octets)

        if self.send_pending:
            self.send_queue.append(octets)
            return

        self.send_octets = octets
        self.send_ticks = ticks()
        self.send_pending = 1

        if self.sendblocked:
            return

        self.poller.set_writable(self)

    def writable(self):
        if self.sendblocked:
            self.poller.set_readable(self)
            if not self.send_pending:
                self.poller.unset_writable(self)
            self.sendblocked = 0
            self.readable()
            return

        status, count = self.sock.sosend(self.send_octets)

        if status == SUCCESS and count > 0:

            if self.measurer:
                self.measurer.send += count

            if count == len(self.send_octets):

                if len(self.send_queue) > 0:
                    self.send_octets = self.send_queue.popleft()
                    self.send_ticks = ticks()
                    return

                self.send_octets = None
                self.send_ticks = 0
                self.send_pending = 0
                self.poller.unset_writable(self)

                self.send_complete()
                return

            if count < len(self.send_octets):
                self.send_octets = buffer(self.send_octets, count)
                self.send_ticks = ticks()
                self.poller.set_writable(self)
                return

            raise RuntimeError("Sent more than expected")

        if status == WANT_WRITE:
            return

        if status == WANT_READ:
            self.poller.unset_writable(self)
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

    def send_complete(self):
        pass


class Connector(Pollable):

    def __init__(self, poller):
        self.poller = poller
        self.stream = None
        self.sock = None
        self.timeout = 15
        self.timestamp = 0
        self.endpoint = None
        self.family = 0
        self.measurer = None

    def connect(self, endpoint, family=socket.AF_INET, measurer=None, sobuf=0):
        self.endpoint = endpoint
        self.family = family
        self.measurer = measurer

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

        stream = self.stream(self.poller)
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


class Listener(Pollable):

    def __init__(self, poller):
        self.stream = None
        self.poller = poller
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

        stream = self.stream(self.poller)
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


class StreamMeasurer(object):
    def __init__(self):
        self.dead = False
        self.recv = 0
        self.send = 0


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
    def __init__(self, poller, output=sys.stdout, interval=1):
        Measurer.__init__(self)

        self.poller = poller
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


class StreamVerboser(object):
    def connection_lost(self, logname, eof, exception):
        if exception:
            LOG.error("* Connection %s: %s" % (logname, exception))
        elif eof:
            LOG.debug("* Connection %s: EOF" % (logname))
        else:
            LOG.debug("* Closed connection %s" % (logname))

    def bind_failed(self, endpoint, exception, fatal=False):
        LOG.error("* Bind %s failed: %s" % (endpoint, exception))
        if fatal:
            sys.exit(1)

    def started_listening(self, endpoint):
        LOG.debug("* Listening at %s" % str(endpoint))

    def connection_made(self, logname):
        LOG.debug("* Connection made %s" % str(logname))

    def connection_failed(self, endpoint, exception, fatal=False):
        LOG.error("* Connection to %s failed: %s" % (endpoint, exception))
        if fatal:
            sys.exit(1)

    def started_connecting(self, endpoint):
        LOG.debug("* Connecting to %s ..." % str(endpoint))


MEASURER = VerboseMeasurer(POLLER)
VERBOSER = StreamVerboser()

KIND_NONE = 0
KIND_DISCARD = 1
KIND_CHARGEN = 2


class GenericProtocolStream(Stream):

    """Specializes stream in order to handle some byte-oriented
       protocols like discard and chargen."""

    def __init__(self, poller):
        Stream.__init__(self, poller)
        self.buffer = "A" * MAXBUF
        self.kind = KIND_NONE

    def connection_made(self):
        VERBOSER.connection_made(self.logname)
        MEASURER.register_stream(self)
        if self.kind == KIND_DISCARD:
            self.start_recv()
            return
        if self.kind == KIND_CHARGEN:
            self.start_send(self.buffer)
            return
        self.shutdown()

    def recv_complete(self, octets):
        self.start_recv()

    def send_complete(self):
        self.start_send(self.buffer)

    def connection_lost(self, exception):
        VERBOSER.connection_lost(self.logname, self.eof, exception)


class GenericListener(Listener):
    def __init__(self, poller, dictionary, kind):
        Listener.__init__(self, poller)
        self.stream = GenericProtocolStream
        self.dictionary = dictionary
        self.kind = kind

    def bind_failed(self, exception):
        VERBOSER.bind_failed(self.endpoint, exception, fatal=True)

    def started_listening(self):
        VERBOSER.started_listening(self.endpoint)

    def connection_made(self, stream):
        stream.configure(self.dictionary)
        stream.kind = self.kind


class GenericConnector(Connector):
    def __init__(self, poller, dictionary, kind):
        Connector.__init__(self, poller)
        self.stream = GenericProtocolStream
        self.dictionary = dictionary
        self.kind = kind

    def connection_failed(self, exception):
        VERBOSER.connection_failed(self.endpoint, exception, fatal=True)

    def started_connecting(self):
        VERBOSER.started_connecting(self.endpoint)

    def connection_made(self, stream):
        stream.configure(self.dictionary)
        stream.kind = self.kind


USAGE = """Neubot net -- TCP bulk transfer test

Usage: neubot net [-Vv] [-D macro[=value]] [-f file] [--help]

Options:
    -D macro[=value]   : Set the value of the macro `macro`
    -f file            : Read options from file `file`
    --help             : Print this help screen and exit
    -V                 : Print version number and exit
    -v                 : Run the program in verbose mode

Macros (defaults in square brackets):
    address=addr       : Select the address to use                 [127.0.0.1]
    certfile           : Path to private key and certificate file
                         to be used together with `-D secure`      []
    clients=N          : Spawn N client connections at a time      [1]
    daemonize          : Drop privileges and run in background     [False]
    duration=N         : Stop the client(s) after N seconds        [10]
    key=KEY            : Use KEY to initialize ARC4 stream         []
    listen             : Listen for incoming connections           [False]
    obfuscate          : Obfuscate traffic using ARC4              [False]
    port=port          : Select the port to use                    [12345]
    proto=proto        : Override protocol (see below)             []
    secure             : Secure the communication using SSL        [False]
    sobuf=size         : Set socket buffer size to `size`          []

Protocols:
    There are two available protocols: `discard` and `chargen`.
    When running in server mode the default is `chargen` and when
    running in client mode the default is `discard`.
"""

VERSION = "Neubot 0.3.5\n"

def main(args):

    conf = OptionParser()
    conf.set_option("stream", "address", "127.0.0.1")
    conf.set_option("stream", "certfile", "")
    conf.set_option("stream", "clients", "1")
    conf.set_option("stream", "daemonize", "False")
    conf.set_option("stream", "duration", "10")
    conf.set_option("stream", "key", "")
    conf.set_option("stream", "listen", "False")
    conf.set_option("stream", "obfuscate", "False")
    conf.set_option("stream", "port", "12345")
    conf.set_option("stream", "proto", "")
    conf.set_option("stream", "secure", "False")
    conf.set_option("stream", "sobuf", "0")

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
             conf.register_opt(value, "stream")
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
             LOG.verbose()
             continue

    conf.merge_files()
    conf.merge_environ()
    conf.merge_opts()

    address = conf.get_option("stream", "address")
    clients = conf.get_option_uint("stream", "clients")
    daemonize = conf.get_option_bool("stream", "daemonize")
    duration = conf.get_option_uint("stream", "duration")
    listen = conf.get_option_bool("stream", "listen")
    port = conf.get_option_uint("stream", "port")
    proto = conf.get_option("stream", "proto")
    sobuf = conf.get_option_uint("stream", "sobuf")

    if not (listen and daemonize):
        MEASURER.start()

    dictionary = {
        "certfile": conf.get_option("stream", "certfile"),
        "key": conf.get_option("stream", "key"),
        "obfuscate": conf.get_option_bool("stream", "obfuscate"),
        "secure": conf.get_option_bool("stream", "secure"),
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
        if daemonize:
            become_daemon()
        dictionary["server_side"] = True
        listener = GenericListener(POLLER, dictionary, kind)
        listener.listen(endpoint, sobuf=sobuf)
        POLLER.loop()
        sys.exit(0)

    if duration >= 0:
        duration = duration + 0.1       # XXX
        POLLER.sched(duration, POLLER.break_loop)

    while clients > 0:
        clients = clients - 1
        connector = GenericConnector(POLLER, dictionary, kind)
        MEASURER.connect(connector, endpoint, sobuf=sobuf)
    POLLER.loop()
    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)
