# neubot/pollable.py

#
# Copyright (c) 2010, 2012, 2014
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>.
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
# Adapted from neubot/net/poller.py
# pylint: disable = missing-docstring
# Python3-ready: yes
#

import errno
import logging
import socket
import ssl
import sys

from neubot import six
from neubot import utils
from neubot import utils_net

# Soft errors on sockets, i.e. we can retry later
SOFT_ERRORS = (errno.EAGAIN, errno.EWOULDBLOCK, errno.EINTR)

# States returned by the socket model
(SUCCESS, WANT_READ, WANT_WRITE, CONNRESET) = range(4)

# Reclaim stream after 300 seconds
WATCHDOG = 300

class Pollable(object):

    def __init__(self):
        self.created = utils.ticks()
        self.watchdog = WATCHDOG
        self.poller_api = 0

    def fileno(self):
        return -1

    def handle_read(self):
        pass

    def handle_write(self):
        pass

    def handle_close(self):  # Only poller_api == 0
        pass

    def handle_error(self):  # For poller_api >= 1
        pass

    def handle_periodic(self, timenow):
        return self.watchdog >= 0 and timenow - self.created > self.watchdog

    def set_timeout(self, timeo):
        self.created = utils.ticks()
        self.watchdog = timeo

    def clear_timeout(self):
        self.created = utils.ticks()
        self.watchdog = -1

class SSLWrapper(object):
    def __init__(self, sock):
        self.sock = sock

    def close(self):
        try:
            self.sock.close()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            logging.warning('sslstream: sock.close() failed', exc_info=1)

    def sorecv(self, maxlen):
        try:
            return SUCCESS, self.sock.read(maxlen)
        except ssl.SSLError:
            exception = sys.exc_info()[1]
            if exception.args[0] == ssl.SSL_ERROR_WANT_READ:
                return WANT_READ, b""
            elif exception.args[0] == ssl.SSL_ERROR_WANT_WRITE:
                return WANT_WRITE, b""
            else:
                raise

    def sosend(self, octets):
        try:
            return SUCCESS, self.sock.write(octets)
        except ssl.SSLError:
            exception = sys.exc_info()[1]
            if exception.args[0] == ssl.SSL_ERROR_WANT_READ:
                return WANT_READ, 0
            elif exception.args[0] == ssl.SSL_ERROR_WANT_WRITE:
                return WANT_WRITE, 0
            else:
                raise

class SocketWrapper(object):
    def __init__(self, sock):
        self.sock = sock

    def close(self):
        try:
            self.sock.close()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            logging.warning('stream: sock.close() failed', exc_info=1)

    def sorecv(self, maxlen):
        try:
            return SUCCESS, self.sock.recv(maxlen)
        except socket.error:
            exception = sys.exc_info()[1]
            if exception.args[0] in SOFT_ERRORS:
                return WANT_READ, b""
            elif exception.args[0] == errno.ECONNRESET:
                return CONNRESET, b""
            else:
                raise

    def sosend(self, octets):
        try:
            return SUCCESS, self.sock.send(octets)
        except socket.error:
            exception = sys.exc_info()[1]
            if exception.args[0] in SOFT_ERRORS:
                return WANT_WRITE, 0
            elif exception.args[0] == errno.ECONNRESET:
                return CONNRESET, 0
            else:
                raise

class StreamConnector(Pollable):

    def __init__(self):
        Pollable.__init__(self)
        self.address = "0.0.0.0"
        self.addrinfos = None
        self.family = "PF_UNSPEC"
        self.poller = None
        self.port = "0"
        self.sock = None
        self.rtt = 0.0

    def __repr__(self):
        return "StreamConnector(%s, %s, %s)" % (self.family,
          self.address, self.port)

    @classmethod
    def connect(cls, poller, family, address, port):
        logging.debug("StreamConnector: %s '%s' %s", family, address, port)

        self = cls()
        self.poller = poller
        self.family = family
        self.address = address
        self.port = port

        logging.debug("StreamConnector: resolve_list")
        self.addrinfos = utils_net.resolve_list(family, "SOCK_STREAM",
                                              address, port, "")
        if not self.addrinfos:
            logging.warning("StreamConnector: resolve FAIL")
            return None

        logging.debug("StreamConnector: resolve_list OK")
        logging.debug("StreamConnector: defer connect_next_")
        self.poller.sched(0.0, self.connect_next_, None)
        return self

    def connect_next_(self, argument):
        logging.debug("StreamConnector: connect_next_")

        if not self.addrinfos:
            logging.debug("StreamConnector: no more addrinfos: FAIL")
            self.handle_connect(-1)
            return

        logging.debug("StreamConnector: connect_ainfo")
        ainfo = self.addrinfos.popleft()
        sock = utils_net.connect_ainfo(ainfo)
        if not sock:
            logging.warning("StreamConnector: connect_ainfo FAIL")
            logging.debug("StreamConnector: defer connect_next_")
            self.poller.sched(0.0, self.connect_next_, None)
            return

        logging.debug("StreamConnector: connect_ainfo INPROGRESS")
        logging.debug("StreamConnector: wait for WRITABLE")
        self.set_timeout(10)
        self.sock = sock
        self.rtt = utils.ticks()
        self.poller.set_writable(self)

    def fileno(self):
        logging.debug("StreamConnector: fileno requested")
        return self.sock.fileno()

    def handle_write(self):
        logging.debug("StreamConnector: is WRITABLE")
        logging.debug("StreamConnector: stop waiting for WRITABLE")
        self.poller.unset_writable(self)

        logging.debug("StreamConnector: check_connected")
        if utils_net.check_connected(self.sock) != 0:
            logging.debug("StreamConnector: check_connected FAIL")
            logging.debug("StreamConnector: defer connect_next_")
            self.poller.sched(0.0, self.connect_next_, None)
            return

        logging.debug("StreamConnector: check_connected OK")
        self.rtt = utils.ticks() - self.rtt
        logging.debug("StreamConnector: RTT %f", self.rtt)
        self.handle_connect(0)

    def handle_error(self):

        logging.debug("StreamConnector: error while waiting for WRITABLE")
        logging.debug("StreamConnector: stop waiting for WRITABLE")
        self.poller.unset_writable(self)

        logging.debug("StreamConnector: defer connect_next_")
        self.poller.sched(0.0, self.connect_next_, None)

    def handle_connect(self, error):
        pass

    def get_socket(self):
        logging.debug("StreamConnector: socket requested")
        return self.sock

    def get_rtt(self):
        logging.debug("StreamConnector: rtt requested")
        return self.rtt

class AsyncStream(Pollable):

    def __init__(self, poller, sock):
        Pollable.__init__(self)
        self.recv_count = 0
        self.recv_blocked = False
        self.poller = poller
        self.sock = sock
        self.send_blocked = False
        self.send_octets = b""

    def close(self):
        self.poller.close(self)

    def handle_close(self):
        pass

    def read(self, recv_count):

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
        return recv_count

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
        pass

    def on_eof(self):
        pass

    def on_rst(self):
        pass

    def send_pending(self):
        return self.send_octets

    def write(self, send_octets):

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

            raise RuntimeError('stream: invalid count')

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
            raise RuntimeError('stream: negative count')

        raise RuntimeError('stream: invalid status')

    def on_flush(self, count, complete):
        pass

    def __repr__(self):
        return "AsyncStream(fileno=%d)" % self.fileno()

    def fileno(self):
        return self.sock.fileno()

    def __del__(self):
        logging.debug('stream: __del__(): %s', self)
