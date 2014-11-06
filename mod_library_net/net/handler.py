# neubot/net/stream.py

#
# There are tons of pylint warnings in this file, disable
# the less relevant ones for now.
#
# pylint: disable=C0111
#

#
# Copyright (c) 2010-2012 Simone Basso <bassosimone@gmail.com>,
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

# Will be replaced by neubot/stream.py 

import collections
import errno
import socket
import sys
import types
import logging

try:
    import ssl
except ImportError:
    ssl = None

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.config import CONFIG
from neubot.log import oops
from neubot.net.poller import POLLER
from neubot.net.poller import Pollable

from neubot import utils
from neubot import utils_net

from neubot.main import common

# States returned by the socket model
STATES = [SUCCESS, ERROR, WANT_READ, WANT_WRITE, CONNRESET] = range(5)

# Maximum amount of bytes we read from a socket
MAXBUF = 1 << 18

# Soft errors on sockets, i.e. we can retry later
SOFT_ERRORS = [ errno.EAGAIN, errno.EWOULDBLOCK, errno.EINTR ]

if ssl:
    class SSLWrapper(object):
        def __init__(self, sock):
            self.sock = sock

        def soclose(self):
            try:
                self.sock.close()
            except ssl.SSLError:
                logging.error('Exception', exc_info=1)

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
            logging.error('Exception', exc_info=1)

    def sorecv(self, maxlen):
        try:
            octets = self.sock.recv(maxlen)
            return SUCCESS, octets
        except socket.error, exception:
            if exception[0] in SOFT_ERRORS:
                return WANT_READ, ""
            elif exception[0] == errno.ECONNRESET:
                return CONNRESET, ""
            else:
                return ERROR, exception

    def sosend(self, octets):
        try:
            count = self.sock.send(octets)
            return SUCCESS, count
        except socket.error, exception:
            if exception[0] in SOFT_ERRORS:
                return WANT_WRITE, 0
            elif exception[0] == errno.ECONNRESET:
                return CONNRESET, 0
            else:
                return ERROR, exception

class Stream(Pollable):
    def __init__(self, poller):
        Pollable.__init__(self)
        self.poller = poller
        self.parent = None
        self.conf = None

        self.sock = None
        self.filenum = -1
        self.myname = None
        self.peername = None
        self.logname = None
        self.eof = False
        self.rst = False

        self.close_complete = False
        self.close_pending = False
        self.recv_blocked = False
        self.recv_pending = False
        self.recv_ssl_needs_kickoff = False
        self.send_blocked = False
        self.send_octets = None
        self.send_queue = collections.deque()
        self.send_pending = False

        self.bytes_recv_tot = 0
        self.bytes_sent_tot = 0

        self.opaque = None
        self.atclosev = set()

    def __repr__(self):
        return "stream %s" % self.logname

    def fileno(self):
        return self.filenum

    def attach(self, parent, sock, conf):

        self.parent = parent
        self.conf = conf

        self.filenum = sock.fileno()
        self.myname = utils_net.getsockname(sock)
        self.peername = utils_net.getpeername(sock)
        self.logname = str((self.myname, self.peername))

        logging.debug("* Connection made %s", str(self.logname))

        if conf["net.stream.secure"]:
            if not ssl:
                raise RuntimeError("SSL support not available")

            server_side = conf["net.stream.server_side"]
            certfile = conf["net.stream.certfile"]

            # wrap_socket distinguishes between None and ''
            if not certfile:
                certfile = None

            ssl_sock = ssl.wrap_socket(sock, do_handshake_on_connect=False,
              certfile=certfile, server_side=server_side)
            self.sock = SSLWrapper(ssl_sock)

            self.recv_ssl_needs_kickoff = not server_side

        else:
            self.sock = SocketWrapper(sock)

        self.connection_made()

    def connection_made(self):
        pass

    def atclose(self, func):
        if func in self.atclosev:
            oops("Duplicate atclose(): %s" % func)
        self.atclosev.add(func)

    def unregister_atclose(self, func):
        if func in self.atclosev:
            self.atclosev.remove(func)

    # Close path

    def connection_lost(self, exception):
        pass

    def close(self):
        self.close_pending = True
        if self.send_pending or self.close_complete:
            return
        self.poller.close(self)

    def handle_close(self):
        if self.close_complete:
            return

        self.close_complete = True

        self.connection_lost(None)
        self.parent.connection_lost(self)

        atclosev, self.atclosev = self.atclosev, set()
        for func in atclosev:
            try:
                func(self, None)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                logging.error("Error in atclosev", exc_info=1)

        self.send_octets = None
        self.sock.soclose()

    # Recv path

    def start_recv(self):
        if (self.close_complete or self.close_pending
          or self.recv_pending):
            return

        self.recv_pending = True

        if self.recv_blocked:
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
        if self.recv_ssl_needs_kickoff:
            self.recv_ssl_needs_kickoff = False
            self.handle_read()

    def handle_read(self):
        if self.recv_blocked:
            self.poller.set_writable(self)
            if not self.recv_pending:
                self.poller.unset_readable(self)
            self.recv_blocked = False
            self.handle_write()
            return

        status, octets = self.sock.sorecv(MAXBUF)

        if status == SUCCESS and octets:

            self.bytes_recv_tot += len(octets)
            self.recv_pending = False
            self.poller.unset_readable(self)

            self.recv_complete(octets)
            return

        if status == WANT_READ:
            return

        if status == WANT_WRITE:
            self.poller.unset_readable(self)
            self.poller.set_writable(self)
            self.send_blocked = True
            return

        if status == CONNRESET and not octets:
            self.rst = True
            self.poller.close(self)
            return

        if status == SUCCESS and not octets:
            self.eof = True
            self.poller.close(self)
            return

        if status == ERROR:
            # Here octets is the exception that occurred
            raise octets

        raise RuntimeError("Unexpected status value")

    def recv_complete(self, octets):
        pass

    # Send path

    def read_send_queue(self):
        octets = ""

        while self.send_queue:
            octets = self.send_queue[0]
            if isinstance(octets, basestring):
                # remove the piece in any case
                self.send_queue.popleft()
                if octets:
                    break
            else:
                octets = octets.read(MAXBUF)
                if octets:
                    break
                # remove the file-like when it is empty
                self.send_queue.popleft()

        if octets:
            if type(octets) == types.UnicodeType:
                oops("Received unicode input")
                octets = octets.encode("utf-8")

        return octets

    def start_send(self, octets):
        if self.close_complete or self.close_pending:
            return

        self.send_queue.append(octets)
        if self.send_pending:
            return

        self.send_octets = self.read_send_queue()
        if not self.send_octets:
            return

        self.send_pending = True

        if self.send_blocked:
            return

        self.poller.set_writable(self)

    def handle_write(self):
        if self.send_blocked:
            self.poller.set_readable(self)
            if not self.send_pending:
                self.poller.unset_writable(self)
            self.send_blocked = False
            self.handle_read()
            return

        status, count = self.sock.sosend(self.send_octets)

        if status == SUCCESS and count > 0:
            self.bytes_sent_tot += count

            if count == len(self.send_octets):

                self.send_octets = self.read_send_queue()
                if self.send_octets:
                    return

                self.send_pending = False
                self.poller.unset_writable(self)

                self.send_complete()
                if self.close_pending:
                    self.poller.close(self)
                return

            if count < len(self.send_octets):
                self.send_octets = buffer(self.send_octets, count)
                self.poller.set_writable(self)
                return

            raise RuntimeError("Sent more than expected")

        if status == WANT_WRITE:
            return

        if status == WANT_READ:
            self.poller.unset_writable(self)
            self.poller.set_readable(self)
            self.recv_blocked = True
            return

        if status == ERROR:
            # Here count is the exception that occurred
            raise count

        if status == CONNRESET and count == 0:
            self.rst = True
            self.poller.close(self)
            return

        if status == SUCCESS and count == 0:
            self.eof = True
            self.poller.close(self)
            return

        if status == SUCCESS and count < 0:
            raise RuntimeError("Unexpected count value")

        raise RuntimeError("Unexpected status value")

    def send_complete(self):
        pass

class Connector(Pollable):
    def __init__(self, poller, parent):
        Pollable.__init__(self)
        self.poller = poller
        self.parent = parent
        self.sock = None
        self.timestamp = 0
        self.endpoint = None
        self.epnts = collections.deque()
        self.watchdog = 10

    def __repr__(self):
        return "connector to %s" % str(self.endpoint)

    def _connection_failed(self):
        if self.sock:
            self.poller.unset_writable(self)
            self.sock = None
        if not self.epnts:
            self.parent._connection_failed(self, None)
            return
        self.connect(self.epnts.popleft(), None)

    def connect(self, endpoint, conf):

        # Connect first address in a list
        if ' ' in endpoint[0]:
            logging.debug('* Connecting to %s', str(endpoint))
            for address in endpoint[0].split():
                epnt = (address.strip(), endpoint[1])
                self.epnts.append(epnt)
            endpoint = self.epnts.popleft()

        self.endpoint = endpoint

        prefer_ipv6 = CONFIG["prefer_ipv6"]
        if conf and "prefer_ipv6" in conf:
            prefer_ipv6 = conf["prefer_ipv6"]
        sock = utils_net.connect(endpoint, prefer_ipv6)
        if not sock:
            self._connection_failed()
            return

        self.sock = sock
        self.timestamp = utils.ticks()
        self.poller.set_writable(self)

    def fileno(self):
        return self.sock.fileno()

    def handle_write(self):
        self.poller.unset_writable(self)

        if not utils_net.isconnected(self.endpoint, self.sock):
            self._connection_failed()
            return

        rtt = utils.ticks() - self.timestamp
        self.parent._connection_made(self.sock, self.endpoint, rtt)

    def handle_close(self):
        self._connection_failed()

class Listener(Pollable):
    def __init__(self, poller, parent, sock, endpoint):
        Pollable.__init__(self)
        self.poller = poller
        self.parent = parent
        self.lsock = sock
        self.endpoint = endpoint

        # Want to listen "forever"
        self.watchdog = -1

    def __repr__(self):
        return "listener at %s" % str(self.endpoint)

    def listen(self):
        self.poller.set_readable(self)
        self.parent.started_listening(self)

    def fileno(self):
        return self.lsock.fileno()

    #
    # Catch all types of exception because an error in
    # connection_made() MUST NOT cause the server to stop
    # listening for new connections.
    #
    def handle_read(self):
        try:
            sock = self.lsock.accept()[0]
            sock.setblocking(False)
            self.parent.connection_made(sock, self.endpoint, 0)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception, exception:
            self.parent.accept_failed(self, exception)
            return

    def handle_close(self):
        self.parent.bind_failed(self.endpoint)  # XXX

class StreamHandler(object):
    def __init__(self, poller):
        self.poller = poller
        self.conf = {}
        self.epnts = collections.deque()
        self.bad = collections.deque()
        self.good = collections.deque()
        self.rtts = []

    def configure(self, conf):
        self.conf = conf

    def listen(self, endpoint):
        sockets = utils_net.listen(endpoint, CONFIG['prefer_ipv6'])
        if not sockets:
            self.bind_failed(endpoint)
            return
        for sock in sockets:
            listener = Listener(self.poller, self, sock, endpoint)
            listener.listen()

    def bind_failed(self, epnt):
        pass

    def started_listening(self, listener):
        pass

    def accept_failed(self, listener, exception):
        pass

    def connect(self, endpoint, count=1):
        while count > 0:
            self.epnts.append(endpoint)
            count = count - 1
        self._next_connect()

    def _next_connect(self):
        if self.epnts:
            connector = Connector(self.poller, self)
            connector.connect(self.epnts.popleft(), self.conf)
        else:
            if self.bad:
                while self.bad:
                    connector, exception = self.bad.popleft()
                    self.connection_failed(connector, exception)
                while self.good:
                    sock = self.good.popleft()
                    sock.close()
            else:
                while self.good:
                    sock, endpoint, rtt = self.good.popleft()
                    self.connection_made(sock, endpoint, rtt)

    def _connection_failed(self, connector, exception):
        self.bad.append((connector, exception))
        self._next_connect()

    def connection_failed(self, connector, exception):
        pass

    def started_connecting(self, connector):
        pass

    def _connection_made(self, sock, endpoint, rtt):
        self.rtts.append(rtt)
        self.good.append((sock, endpoint, rtt))
        self._next_connect()

    def connection_made(self, sock, endpoint, rtt):
        pass

    def connection_lost(self, stream):
        pass

class GenericHandler(StreamHandler):
    def connection_made(self, sock, endpoint, rtt):
        stream = GenericProtocolStream(self.poller)
        stream.kind = self.conf["net.stream.proto"]
        stream.attach(self, sock, self.conf)

#
# Specializes stream in order to handle some byte-oriented
# protocols like discard, chargen, and echo.
#
class GenericProtocolStream(Stream):
    def __init__(self, poller):
        Stream.__init__(self, poller)
        self.buffer = None
        self.kind = ""

    def connection_made(self):
        self.buffer = "A" * self.conf["net.stream.chunk"]
        duration = self.conf["net.stream.duration"]
        if duration >= 0:
            POLLER.sched(duration, self._do_close)
        if self.kind == "discard":
            self.start_recv()
        elif self.kind == "chargen":
            self.start_send(self.buffer)
        elif self.kind == "echo":
            self.start_recv()
        else:
            self.close()

    def _do_close(self, *args, **kwargs):
        self.close()

    def recv_complete(self, octets):
        self.start_recv()
        if self.kind == "echo":
            self.start_send(octets)

    def send_complete(self):
        if self.kind == "echo":
            self.start_recv()
            return
        self.start_send(self.buffer)

CONFIG.register_defaults({
    # General variables
    "net.stream.certfile": "",
    "net.stream.secure": False,
    "net.stream.server_side": False,
    # For main()
    "net.stream.address": "127.0.0.1 ::1",
    "net.stream.chunk": 262144,
    "net.stream.clients": 1,
    "net.stream.duration": 10,
    "net.stream.listen": False,
    "net.stream.port": 12345,
    "net.stream.proto": "",
})

def main(args):

    CONFIG.register_descriptions({
        # General variables
        "net.stream.certfile": "Set SSL certfile path",
        "net.stream.secure": "Enable SSL",
        "net.stream.server_side": "Enable SSL server-side mode",
        # For main()
        "net.stream.address": "Set client or server address",
        "net.stream.chunk": "Chunk written by each write",
        "net.stream.clients": "Set number of client connections",
        "net.stream.duration": "Set duration of a test",
        "net.stream.listen": "Enable server mode",
        "net.stream.port": "Set client or server port",
        "net.stream.proto": "Set proto (chargen, discard, or echo)",
    })

    common.main("net.stream", "TCP bulk transfer test", args)

    conf = CONFIG.copy()

    endpoint = (conf["net.stream.address"], conf["net.stream.port"])

    if not conf["net.stream.proto"]:
        if conf["net.stream.listen"]:
            conf["net.stream.proto"] = "chargen"
        else:
            conf["net.stream.proto"] = "discard"
    elif conf["net.stream.proto"] not in ("chargen", "discard", "echo"):
        common.write_help(sys.stderr, "net.stream", "TCP bulk transfer test")
        sys.exit(1)

    handler = GenericHandler(POLLER)
    handler.configure(conf)

    if conf["net.stream.listen"]:
        conf["net.stream.server_side"] = True
        handler.listen(endpoint)
    else:
        handler.connect(endpoint, count=conf["net.stream.clients"])

    POLLER.loop()
    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)
