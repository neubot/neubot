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
import sys
import types
import logging
import ssl

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.config import CONFIG
from neubot.log import oops
from neubot.net.poller import POLLER
from neubot.net.poller import Pollable

from neubot.connector import ChildConnector
from neubot.pollable import CONNRESET
from neubot.pollable import SSLWrapper
from neubot.pollable import SUCCESS
from neubot.pollable import SocketWrapper
from neubot.pollable import WANT_READ
from neubot.pollable import WANT_WRITE

from neubot import utils_net
from neubot import six

from neubot.main import common

# Maximum amount of bytes we read from a socket
MAXBUF = 1 << 18

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
        self.recv_count = 0
        self.recv_ssl_needs_kickoff = False
        self.send_blocked = False
        self.send_queue = collections.deque()
        self.send_octets = b""

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
        if self.send_octets or self.close_complete:
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

        self.send_octets = b""
        self.sock.close()

    # Recv path

    def start_recv(self):
        if self.close_complete or self.close_pending:
            return

        result = self.simple_recv(MAXBUF)
        if result <= 0:
            return

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

    def simple_recv(self, recv_count):

        if self.recv_count > 0:
            logging.warning("stream: already receiving")
            return -1
        if recv_count <= 0:
            logging.warning("stream: invalid recv_count")
            return -1

        self.recv_count = recv_count

        if self.recv_blocked:
            logging.debug('stream: recv() is blocked')
            return 0

        self.poller.set_readable(self)
        return 1

    def handle_read(self):

        if self.recv_blocked:
            self.poller.set_writable(self)
            if self.recv_count <= 0:
                self.poller.unset_readable(self)
            self.recv_blocked = False
            self.handle_write()
            return

        status, octets = self.sock.sorecv(self.recv_count)

        if status == SUCCESS and octets:
            self.recv_count = 0
            self.poller.unset_readable(self)
            self.on_data(octets)
            return

        if status == WANT_READ:
            return

        if status == WANT_WRITE:
            self.poller.unset_readable(self)
            self.poller.set_writable(self)
            self.send_blocked = True
            return

        if status == SUCCESS and not octets:
            self.on_eof()
            self.poller.close(self)
            return

        if status == CONNRESET and not octets:
            self.on_rst()
            self.poller.close(self)
            return

        raise RuntimeError('stream: invalid status')

    def on_data(self, octets):
        self.bytes_recv_tot += len(octets)
        self.recv_complete(octets)

    def on_eof(self):
        self.eof = True

    def on_rst(self):
        self.rst = True

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
        if self.send_pending():
            return

        chunk = self.read_send_queue()
        if not chunk:
            return

        self.simple_send(chunk)

    def send_pending(self):
        return self.send_octets

    def simple_send(self, send_octets):

        if self.send_octets:
            logging.warning("stream: already sending")
            return -1

        self.send_octets = send_octets

        if self.send_blocked:
            logging.debug('stream: send() is blocked')
            return 0

        self.poller.set_writable(self)
        return len(send_octets)

    def handle_write(self):

        if self.send_blocked:
            self.poller.set_readable(self)
            if not self.send_octets:
                self.poller.unset_writable(self)
            self.send_blocked = False
            self.handle_read()
            return

        status, count = self.sock.sosend(self.send_octets)

        if status == SUCCESS and count > 0:

            if count == len(self.send_octets):
                self.poller.unset_writable(self)
                self.send_octets = b""
                self.on_flush(count, True)
                return

            if count < len(self.send_octets):
                self.send_octets = six.buff(self.send_octets, count)
                self.on_flush(count, False)
                return

            raise RuntimeError("Sent more than expected")

        if status == WANT_WRITE:
            return

        if status == WANT_READ:
            self.poller.unset_writable(self)
            self.poller.set_readable(self)
            self.recv_blocked = True
            return

        if status == CONNRESET and count == 0:
            self.on_rst()
            self.poller.close(self)
            return

        if status == SUCCESS and count < 0:
            raise RuntimeError("Unexpected count value")

        raise RuntimeError("Unexpected status value")

    def on_flush(self, count, complete):
        self.bytes_sent_tot += count
        if not complete:
            return

        self.send_octets = self.read_send_queue()
        if self.send_octets:
            self.poller.set_writable(self)
            return

        self.send_complete()

        if self.close_pending:
            self.poller.close(self)
            return

    def send_complete(self):
        pass

class Connector(object):

    def __init__(self, poller, parent):
        self.poller = poller
        self.parent = parent
        self.endpoint = None

    def __repr__(self):
        return "connector to %s" % str(self.endpoint)

    def _connection_failed(self):
        self.parent._connection_failed(self, None)

    def connect(self, endpoint, conf):

        self.endpoint = endpoint

        prefer_ipv6 = CONFIG["prefer_ipv6"]
        if conf and "prefer_ipv6" in conf:
            prefer_ipv6 = conf["prefer_ipv6"]

        # Note that connect() also accepts a boolean family
        child = ChildConnector.connect(self.poller, prefer_ipv6,
          self.endpoint[0], self.endpoint[1])
        if not child:
            self._connection_failed()
            return

        child.parent = self

    def child_completed_(self, child, error):

        if error:
            self._connection_failed()
            return

        self.parent._connection_made(child.get_socket(),
          self.endpoint, child.get_rtt())

class Listener(Pollable):
    def __init__(self, poller, parent, sock, endpoint):
        Pollable.__init__(self)
        self.poller = poller
        self.parent = parent
        self.lsock = sock
        self.endpoint = endpoint

        # Want to listen "forever"
        self.clear_timeout()

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
                    sock, endpoint, rtt = self.good.popleft()
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
