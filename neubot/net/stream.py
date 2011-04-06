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
        self.bytes_recv_tot = 0
        self.bytes_sent_tot = 0
        self.bytes_recv = 0
        self.bytes_sent = 0

    def fileno(self):
        return self.filenum

    def attach(self, parent, sock, conf):

        self.parent = parent

        self.filenum = sock.fileno()
        self.myname = sock.getsockname()
        self.peername = sock.getpeername()
        self.logname = str((self.myname, self.peername))

        LOG.debug("* Connection made %s" % str(self.logname))

        if conf.get("secure", False):
            if not ssl:
                raise RuntimeError("SSL support not available")

            server_side = conf.get("server_side", False)
            certfile = conf.get("certfile", None)

            so = ssl.wrap_socket(sock, do_handshake_on_connect=False,
              certfile=certfile, server_side=server_side)
            self.sock = SSLWrapper(so)

            if not server_side:
                self.kickoffssl = 1

        else:
            self.sock = SocketWrapper(sock)

        if conf.get("obfuscate", False):
            key = conf.get("key", None)
            self.encrypt = arcfour_new(key).encrypt
            self.decrypt = arcfour_new(key).decrypt

        self.connection_made()

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

        if exception:
            LOG.error("* Connection %s: %s" % (self.logname, exception))
        elif self.eof:
            LOG.debug("* Connection %s: EOF" % (self.logname))
        else:
            LOG.debug("* Closed connection %s" % (self.logname))

        self.connection_lost(exception)
        if self.parent:
            self.parent.connection_lost(self)

        if self.measurer:
            self.measurer.unregister_stream(self)

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

            self.bytes_recv_tot += len(octets)
            self.bytes_recv += len(octets)

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

            self.bytes_sent_tot += count
            self.bytes_sent += count

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

    def __init__(self, poller, parent):
        self.poller = poller
        self.parent = parent
        self.sock = None
        self.timeout = 15
        self.timestamp = 0
        self.endpoint = None
        self.family = 0
        self.measurer = None

    def connect(self, endpoint, conf):
        self.endpoint = endpoint
        self.family = conf.get("family", socket.AF_INET)
        self.measurer = conf.get("measurer", None)
        sobuf = conf.get("sobuf", 0)

        try:
            addrinfo = socket.getaddrinfo(endpoint[0], endpoint[1],
                                          self.family, socket.SOCK_STREAM)
        except socket.error, exception:
            LOG.error("* Connection to %s failed: %s" % (endpoint, exception))
            self.parent.connection_failed(self, exception)
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
                    LOG.debug("* Connecting to %s ..." % str(endpoint))
                    self.parent.started_connecting(self)
                return

            except socket.error, exception:
                last_exception = exception

        LOG.error("* Connection to %s failed: %s" % (endpoint, last_exception))
        self.parent.connection_failed(self, last_exception)

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
            self.parent.connection_failed(self, exception)
            return

        if self.measurer:
            rtt = ticks() - self.timestamp
            self.measurer.rtts.append(rtt)

        self.parent.connection_made(self.sock)

    def writetimeout(self, now):
        return now - self.timestamp >= self.timeout

    def closing(self, exception=None):
        LOG.error("* Connection to %s failed: %s" % (self.endpoint, exception))
        self.parent.connection_failed(self, exception)


class Listener(Pollable):

    def __init__(self, poller, parent):
        self.poller = poller
        self.parent = parent
        self.lsock = None
        self.endpoint = None
        self.family = 0

    def listen(self, endpoint, conf):
        self.endpoint = endpoint
        self.family = conf.get("family", socket.AF_INET)
        sobuf = conf.get("sobuf", 0)

        try:
            addrinfo = socket.getaddrinfo(endpoint[0], endpoint[1],
              self.family, socket.SOCK_STREAM, 0, socket.AI_PASSIVE)
        except socket.error, exception:
            LOG.error("* Bind %s failed: %s" % (self.endpoint, exception))
            self.parent.bind_failed(self, exception)
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

                LOG.debug("* Listening at %s" % str(self.endpoint))

                self.lsock = lsock
                self.poller.set_readable(self)
                self.parent.started_listening(self)
                return

            except socket.error, exception:
                last_exception = exception

        LOG.error("* Bind %s failed: %s" % (self.endpoint, last_exception))
        self.parent.bind_failed(self, last_exception)

    def fileno(self):
        return self.lsock.fileno()

    def readable(self):
        try:
            sock, sockaddr = self.lsock.accept()
            sock.setblocking(False)
        except socket.error, exception:
            self.parent.accept_failed(self, exception)
            return

        self.parent.connection_made(sock)

    def closing(self, exception=None):
        LOG.error("* Bind %s failed: %s" % (self.endpoint, exception))
        self.parent.bind_failed(self, exception)     # XXX


class Measurer(object):
    def __init__(self):
        self.last = ticks()
        self.streams = []
        self.rtts = []

    def register_stream(self, stream):
        self.streams.append(stream)
        stream.measurer = self

    def unregister_stream(self, stream):
        self.streams.remove(stream)
        stream.measurer = None

    def measure_rtt(self):
        rttavg = 0
        rttdetails = []
        if len(self.rtts) > 0:
            for rtt in self.rtts:
                rttavg += rtt
            rttavg = rttavg / len(self.rtts)
            rttdetails = self.rtts
            self.rtts = []
        return rttavg, rttdetails

    def compute_delta_and_sums(self, clear=True):
        now = ticks()
        delta = now - self.last
        self.last = now

        if delta <= 0:
            return 0.0, 0, 0

        recvsum = 0
        sendsum = 0
        for stream in self.streams:
            recvsum += stream.bytes_recv
            sendsum += stream.bytes_sent
            if clear:
                stream.bytes_recv = stream.bytes_sent = 0

        return delta, recvsum, sendsum

    def measure_speed(self):
        delta, recvsum, sendsum = self.compute_delta_and_sums(clear=False)
        if delta <= 0:
            return 0, 0, []

        recvavg = recvsum / delta
        sendavg = sendsum / delta

        percentages = []
        for stream in self.streams:
            recvp, sendp = 0, 0
            if recvsum:
                recvp = 100 * stream.bytes_recv / recvsum
            if sendsum:
                sendp = 100 * stream.bytes_sent / sendsum
            percentages.append((recvp, sendp))
            stream.bytes_recv = stream.bytes_sent = 0

        return recvavg, sendavg, percentages


class HeadlessMeasurer(Measurer):
    def __init__(self, poller, interval=1):
        Measurer.__init__(self)
        self.poller = poller
        self.interval = interval
        self.recv_hist = {}
        self.send_hist = {}
        self.marker = None
        self.task = None

    def start(self, marker):
        self.collect()
        self.marker = marker

    def stop(self):
        if self.task:
            self.task.unsched()

    def collect(self):
        if self.task:
            self.task.unsched()
        self.task = self.poller.sched(self.interval, self.collect)
        delta, recvsum, sendsum = self.compute_delta_and_sums()
        if self.marker:
            self.recv_hist.setdefault(self.marker, []).append((delta, recvsum))
            self.send_hist.setdefault(self.marker, []).append((delta, sendsum))


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

        rttavg, rttdetails = self.measure_rtt()
        if len(rttdetails) > 0:
            rttavg = "%d us" % int(1000000 * rttavg)
            self.output.write("\t\t%s\t\t---\t\t---\n" % rttavg)
            if len(rttdetails) > 1:
                for detail in rttdetails:
                    detail = "%d us" % int(1000000 * detail)
                    self.output.write("\t\t  %s\t\t---\t\t---\n" % detail)

        recvavg, sendavg, percentages = self.measure_speed()
        if len(percentages) > 0:
            recv, send = speed_formatter(recvavg), speed_formatter(sendavg)
            self.output.write("\t\t---\t\t%s\t\t%s\n" % (recv, send))
            if len(percentages) > 1:
                for val in percentages:
                    val = map(lambda x: "%.2f%%" % x, val)
                    self.output.write("\t\t---\t\t  %s\t\t  %s\n" %
                                      (val[0], val[1]))


MEASURER = VerboseMeasurer(POLLER)


class StreamHandler(object):

    def __init__(self, poller):
        self.poller = poller
        self.conf = {}

    def configure(self, conf):
        self.conf = conf

    def listen(self, endpoint):
        listener = Listener(self.poller, self)
        listener.listen(endpoint, self.conf)

    def bind_failed(self, listener, exception):
        pass

    def started_listening(self, listener):
        pass

    def accept_failed(self, listener, exception):
        pass

    def connect(self, endpoint, count=1):
        while count > 0:
            connector = Connector(self.poller, self)
            connector.connect(endpoint, self.conf)
            count = count - 1

    def connection_failed(self, connector, exception):
        pass

    def started_connecting(self, connector):
        pass

    def connection_made(self, sock):
        pass

    def connection_lost(self, stream):
        pass


KIND_NONE = 0
KIND_DISCARD = 1
KIND_CHARGEN = 2


class GenericHandler(StreamHandler):

    def connection_made(self, sock):
        stream = GenericProtocolStream(self.poller)
        stream.kind = self.conf.get("kind", KIND_NONE)
        stream.attach(self, sock, self.conf)


class GenericProtocolStream(Stream):

    """Specializes stream in order to handle some byte-oriented
       protocols like discard and chargen."""

    def __init__(self, poller):
        Stream.__init__(self, poller)
        self.buffer = "A" * MAXBUF
        self.kind = KIND_NONE

    def connection_made(self):
        MEASURER.register_stream(self)
        if self.kind == KIND_DISCARD:
            self.start_recv()
        elif self.kind == KIND_CHARGEN:
            self.start_send(self.buffer)
        else:
            self.shutdown()

    def recv_complete(self, octets):
        self.start_recv()

    def send_complete(self):
        self.start_send(self.buffer)


USAGE = """Neubot net -- TCP bulk transfer test

Usage: neubot net [-Vv] [-D macro[=value]] [-f file] [--help]

Options:
    -D macro[=value]   : Set the value of the macro `macro`
    -f file            : Read options from file `file`
    --help             : Print this help screen and exit
    -V                 : Print version number and exit
    -v                 : Run the program in verbose mode

Macros (defaults in square brackets):
    address=addr       : Select the address to use                 []
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

If you don't specify an address Neubot will pick 0.0.0.0 in listen mode
and neubot.blupixel.net in connect mode.

"""

VERSION = "Neubot 0.3.6\n"

def main(args):

    conf = OptionParser()
    conf.set_option("stream", "address", "")
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

    if not address:
        if not listen:
            address = "neubot.blupixel.net"
        else:
            address = "0.0.0.0"

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

    dictionary["measurer"] = MEASURER
    dictionary["kind"] = kind
    dictionary["sobuf"] = sobuf

    handler = GenericHandler(POLLER)
    handler.configure(dictionary)

    if listen:
        if daemonize:
            become_daemon()
        dictionary["server_side"] = True
        handler.listen(endpoint)
        POLLER.loop()
        sys.exit(0)

    if duration >= 0:
        duration = duration + 0.1       # XXX
        POLLER.sched(duration, POLLER.break_loop)

    while clients > 0:
        clients = clients - 1
        handler.connect(endpoint)
    POLLER.loop()
    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)
