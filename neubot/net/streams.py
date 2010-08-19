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

SUCCESS, ERROR, WANT_READ, WANT_WRITE = range(0,4)
TIMEOUT = 300

#
# To improve this class we can:
#   1. Update .ticks after a partial send() for more precise timeout
#      calculation.
#

class Stream(Pollable):
    def __init__(self, poller, fileno, myname, peername):
        self.poller = poller
        self._fileno = fileno
        self.myname = myname
        self.peername = peername
        self.readable = None
        self.writable = None
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
        self.isclosing = False

    def __del__(self):
        pass

    def fileno(self):
        return self._fileno

    #
    # When you keep a reference to the stream in your class,
    # remember to point stream.notify_closing to a function
    # that removes such reference.
    #

    def close(self):
        self._do_close()

    def _do_close(self):
        if not self.isclosing:
            self.isclosing = True
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
            self.send_pending = False
            self.recv_maxlen = 0
            self.recv_success = None
            self.recv_ticks = 0
            self.recv_pending = False
            self.readable = None
            self.writable = None
            self.soclose()
            self.poller.close(self)

    def readtimeout(self, now):
        return self.recv_pending and now - self.recv_ticks > self.timeout

    def writetimeout(self, now):
        return self.send_pending and now - self.send_ticks > self.timeout

    #
    # Make sure that we set/unset readable/writable only if
    # needed, because the operation is a bit expensive (you
    # add/remove entries to/from an hash table).
    #

    def set_readable(self, func):
        if not self.readable:
            self.poller.set_readable(self)
        if self.readable != func:
            self.readable = func

    def set_writable(self, func):
        if not self.writable:
            self.poller.set_writable(self)
        if self.writable != func:
            self.writable = func

    def unset_readable(self):
        if self.readable:
            self.poller.unset_readable(self)
            self.readable = None

    def unset_writable(self):
        if self.writable:
            self.poller.unset_writable(self)
            self.writable = None

    #
    # When we are closing this stream recv() MUST NOT run because
    # it might self.poller.set_readable(self) and so the stream
    # would not be closed and garbage collected.
    # When we invoke recv() the code tries immediatly to receive
    # from the underlying socket and will only set_readable if
    # the operation returns WANT_READ.  This is called "optimistic"
    # I/O because we initially assume that the operation will be
    # successful.
    # When a receive is successful we invoke the recv_success
    # callback but we don't want this callback to be able to
    # issue another optimistic recv() because this might lead
    # to recursion and prevents other streams to get their chance
    # of receiving.  And so we employ .isreceiving to avoid
    # nesting optimistic recv()s.
    # The variable .recv_pending is True when the user wants to
    # receive from the socket.  We set this variable to False
    # after a successful recv, before invoking the recv_success
    # callback.  But we don't unset_readable before invoking
    # the callback, because the callback might want to receive
    # again (and it would be a waste to unset and suddenly set
    # readable again).  Instead, we check .recv_pending value
    # AFTER the callback: if it's False we unset readable, and
    # if it's True it means that the user invoked recv() from
    # the callback, and then we set_readable (we don't know at
    # this point whether we are already readable because of the
    # optimistic I/O).
    # With SSL sockets, recv() might also return WANT_WRITE and
    # this is treated as a special case.  While normally it is
    # possible for recv() and send() to go in parallel, in this
    # case we (i) set .writable to point to ._do_recv and (ii)
    # use .sendblocked to block send (if we don't send might be
    # invoked and might modify writable).  Then, when the under-
    # lying socket becomes writable and eventually ._do_recv()
    # is invoked, we check whether send was blocked, and, if so,
    # we unblock it, and we properly set/unset writable depending
    # on the value of .send_pending.
    #

    def recv(self, maxlen, recv_success, recv_error=None):
        if not self.isclosing:
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
                    self.set_writable(self._do_send)
                else:
                    self.unset_writable()
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
                    if not self.recvblocked and not self.isclosing:
                        if not self.recv_pending:
                            self.unset_readable()
                        else:
                            self.set_readable(self._do_recv)
                else:
                    self.eof = True
                    self._do_close()
            elif status == WANT_READ:
                self.set_readable(self._do_recv)
            elif status == WANT_WRITE:
                self.set_writable(self._do_recv)
                self.sendblocked = True
            elif status == ERROR:
                self._do_close()
            else:
                panic = "Unexpected status value"
            self.isreceiving = False
            if panic:
                raise Exception(panic)

    #
    # To get more insights on this implementation, refer to
    # the comment before recv().  What is said there is also
    # applicable here.
    #

    def send(self, octets, send_success, send_error=None):
        if not self.isclosing:
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
                    self.set_readable(self._do_recv)
                else:
                    self.unset_readable()
                self.recvblocked = False
            subset = buffer(self.send_octets, self.send_pos)
            status, count = self.sosend(subset)
            if status == SUCCESS:
                if count > 0:
                    self.send_pos += count
                    if self.send_pos < len(self.send_octets):
                        self.set_writable(self._do_send)
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
                        if not self.sendblocked and not self.isclosing:
                            if not self.send_pending:
                                self.unset_writable()
                            else:
                                self.set_writable(self._do_send)
                    else:
                        panic = "Internal error"
                else:
                    panic = "Unexpected count value"
            elif status == WANT_WRITE:
                self.set_writable(self._do_send)
            elif status == WANT_READ:
                self.set_readable(self._do_send)
                self.recvblocked = True
            elif status == ERROR:
                self._do_close()
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
