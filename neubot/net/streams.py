# neubot/net/streams.py
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
# Asynchronous I/O for non-blocking sockets (and SSL)
#

import errno
import socket
import ssl

import neubot

from neubot.net.pollers import Pollable

SUCCESS, ERROR, WANT_READ, WANT_WRITE = range(0, 4)
TIMEOUT = 300

#
# To improve this class we can:
#   1. Update .ticks after a partial send() for more precise timeout
#      calculation.
#   2. Address the case when the caller is doing something like:
#        ...
#        def send_data(self, stream, octets):
#            data = self.get_data()
#            stream.send(data, self.send_data)
#        ...
#      The problem is that our code unset_writable() before invoking
#      the user defined callback (in this case send_data()), but the
#      callback invokes send() which in turn invokes set_writable().
#      We should optimize for this case, and then measure whether it
#      is worth doing that.  By the way, it seems feasible to write
#      the optimization, because we already detect when the callback
#      for send() invokes send() again (self.issending == True.)
#      Of course, we have the same problem with recv().
#

class Stream(Pollable):
    def __init__(self, poller, fileno, myname, peername):
        self.poller = poller
        self._fileno = fileno
        self.myname = myname
        self.peername = peername
        self.send_octets = None
        self.send_success = None
        self.send_ticks = 0
        self.send_pos = 0
        self.send_pending = False
        self.send_error = None
        self.recv_maxlen = 0
        self.recv_success = None
        self.recv_ticks = 0
        self.recv_pending = False
        self.recv_error = None
        self.eof = False
        self.isreceiving = False
        self.issending = False
        self.recvblocked = False
        self.sendblocked = False
        self.timeout = TIMEOUT
        self.notify_closing = None
        self.context = None

    def __del__(self):
        pass

    #
    # When .closing() is invoked the poller has already removed any
    # reference to this object.
    # For passive close (e.g. connection closed by remote host)
    # we expect recv_error() and send_error() to remove any extra
    # reference to this object.
    # Notify_closing() propagates the "closing" event and is an
    # alternative to send_error and recv_error.
    #

    def closing(self):
        self.soclose()
        if self.recv_error:
            self.recv_error(self)
        if self.send_error:
            self.send_error(self)
        self.readable = None
        self.writable = None
        if self.notify_closing:
            self.notify_closing()

    def fileno(self):
        return self._fileno

    def readable(self):
        raise Exception("Should have been overriden")

    def writable(self):
        raise Exception("Should have been overriden")

    #
    # When the user issues an active close we need to reset
    # the state of async send() and recv() to avoid calling
    # back .send_error() or .recv_error() in .closing()
    # The caller should remove any extra reference to the
    # object just after close() returns.
    #

    def close(self):
        self.send_octets = None
        self.send_success = None
        self.send_ticks = 0
        self.send_pos = 0
        self.send_pending = False
        self.send_error = None
        self.recv_maxlen = 0
        self.recv_success = None
        self.recv_ticks = 0
        self.recv_pending = False
        self.recv_error = None
        self.poller.close(self)

    def readtimeout(self, now):
        return self.recv_pending and now - self.recv_ticks > self.timeout

    def writetimeout(self, now):
        return self.send_pending and now - self.send_ticks > self.timeout

    #
    # With SSL sockets it is possible for .sorecv() to return
    # WANT_WRITE and for .sosend() to return WANT_READ.
    # The code for send() and recv() deals with this problem
    # temporarily blocking recv() when send() wants to read,
    # and, similarly, blocking send() when recv() wants to
    # write.
    # When there is an error we close the stream immediately
    # rather than registering a delayed close and, this way,
    # we avoid the complexity of getting I/O events on a stream
    # that is already closed.
    # We set self.eof when we get EOF when reading because there
    # are protocols that use EOF as ``end of record'', and, of
    # course, they need a way to tell whether the connection was
    # closed because of an error (and so the message should be
    # discarded) or because of EOF (and so the message is good.)
    #

    # Remember to modify neubot.http and remove compat
    def recv(self, maxlen, recv_success, recv_error=None, compat=False):
        self.recv_maxlen = maxlen
        self.recv_success = recv_success
        self.recv_ticks = self.poller.get_ticks()
        self.recv_pending = True
        self.recv_error = recv_error
        if not self.isreceiving:
            self._do_recv()

    def _do_recv(self):
        if not self.recvblocked:
            self.isreceiving = True
            panic = ""
            if self.sendblocked:
                if self.send_pending:
                    self.poller.set_writable(self)
                    self.writable = self._do_send
                else:
                    self.poller.unset_writable(self)
                    self.writable = None
                # Unblock send() because we restored writable()
                self.sendblocked = False
            status, octets = self.sorecv(self.recv_maxlen)
            if status == SUCCESS:
                if octets:
                    notify = self.recv_success
                    self.recv_maxlen = 0
                    self.recv_success = None
                    self.recv_ticks = 0
                    self.recv_pending = False
                    self.recv_error = None
                    if notify:
                        notify(self, octets)
                    # Notify() might invoke send() that might block recv()
                    if not self.recvblocked:
                        if not self.recv_pending:
                            self.poller.unset_readable(self)
                            self.readable = None
                        else:
                            self.poller.set_readable(self)
                            self.readable = self._do_recv
                else:
                    self.eof = True
                    self.poller.close(self)
            elif status == WANT_READ:
                self.poller.set_readable(self)
                self.readable = self._do_recv
            elif status == WANT_WRITE:
                self.poller.set_writable(self)
                self.writable = self._do_recv
                # Block send() because we changed writable()
                self.sendblocked = True
            elif status == ERROR:
                self.poller.close(self)
            else:
                panic = "Unexpected status value"
            self.isreceiving = False
            if panic:
                raise Exception(panic)

    # Remember to modify neubot.http and remove compat
    def send(self, octets, send_success, send_error=None, compat=False):
        self.send_octets = octets
        self.send_pos = 0
        self.send_success = send_success
        self.send_ticks = self.poller.get_ticks()
        self.send_pending = True
        self.send_error = send_error
        if not self.issending:
            self._do_send()

    def _do_send(self):
        if not self.sendblocked:
            self.issending = True
            panic = ""
            if self.recvblocked:
                if self.recv_pending:
                    self.poller.set_readable(self)
                    self.readable = self._do_recv
                else:
                    self.poller.unset_readable(self)
                    self.readable = None
                # Unblock recv() because we restored readable()
                self.recvblocked = False
            subset = buffer(self.send_octets, self.send_pos)
            status, count = self.sosend(subset)
            if status == SUCCESS:
                if count > 0:
                    self.send_pos += count
                    if self.send_pos < len(self.send_octets):
                        self.poller.set_writable(self)
                        self.writable = self._do_send
                    elif self.send_pos == len(self.send_octets):
                        notify = self.send_success
                        octets = self.send_octets
                        self.send_octets = None
                        self.send_pos = 0
                        self.send_success = None
                        self.send_ticks = 0
                        self.send_pending = False
                        self.send_error = None
                        if notify:
                            notify(self, octets)
                        # Notify() might invoke recv() that might block send()
                        if not self.sendblocked:
                            if not self.send_pending:
                                self.poller.unset_writable(self)
                                self.writable = None
                            else:
                                self.poller.set_writable(self)
                                self.writable = self._do_send
                    else:
                        panic = "Internal error"
                else:
                    panic = "Unexpected count value"
            elif status == WANT_WRITE:
                self.poller.set_writable(self)
                self.writable = self._do_send
            elif status == WANT_READ:
                self.poller.set_readable(self)
                self.readable = self._do_send
                # Block recv() because we changed readable()
                self.recvblocked = True
            elif status == ERROR:
                self.poller.close(self)
            else:
                panic = "Unexpected status value"
            self.issending = False
            if panic:
                raise Exception(panic)

    def soclose(self):
        raise Exception("You must override this method")

    def sorecv(self, maxlen):
        raise Exception("You must override this method")

    def sosend(self, octets):
        raise Exception("You must override this method")

class StreamSSL(Stream):
    def __init__(self, ssl_sock, poller, fileno, myname, peername):
        self.ssl_sock = ssl_sock
        Stream.__init__(self, poller, fileno, myname, peername)
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
                neubot.utils.prettyprint_exception()
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
                neubot.utils.prettyprint_exception()
                return ERROR, 0

class StreamSocket(Stream):
    def __init__(self, sock, poller, fileno, myname, peername):
        self.sock = sock
        Stream.__init__(self, poller, fileno, myname, peername)

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
                neubot.utils.prettyprint_exception()
                return ERROR, ""

    def sosend(self, octets):
        try:
            count = self.sock.send(octets)
            return SUCCESS, count
        except socket.error, (code, reason):
            if code in [errno.EAGAIN, errno.EWOULDBLOCK]:
                return WANT_WRITE, 0
            else:
                neubot.utils.prettyprint_exception()
                return ERROR, 0

def create_stream(sock, poller, fileno, myname, peername):
    if type(sock) == ssl.SSLSocket:
        stream = StreamSSL(sock, poller, fileno, myname, peername)
    elif type(sock) == socket.SocketType:
        stream = StreamSocket(sock, poller, fileno, myname, peername)
    else:
        raise Exception("Unknown socket type")
    return stream
