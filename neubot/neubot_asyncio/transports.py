#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software. See AUTHORS and COPYING for more
# information on the copying conditions.
#

# pylint: disable = missing-docstring

from collections import deque

import errno
import logging
import socket
import ssl

from ._utils import _getsockname
from ._utils import _getpeername
from .futures import _Future

class _Transport(object):

    def get_extra_info(self, name, default=None):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def pause_reading(self):
        raise NotImplementedError

    def resume_reading(self):
        raise NotImplementedError

    def set_write_buffer_limits(self, high=None, low=None):
        raise NotImplementedError

    def get_write_buffer_size(self):
        raise NotImplementedError

    def write(self, data):
        raise NotImplementedError

    def writelines(self, list_of_data):
        raise NotImplementedError

    def write_eof(self):
        raise NotImplementedError

    def can_write_eof(self):
        raise NotImplementedError

    def abort(self):
        raise NotImplementedError

_HI_WATERMARK = 1 << 17
_MAXRECV = 1 << 17
_SOFT_IO_ERRORS = (errno.EAGAIN, errno.EWOULDBLOCK, errno.EINTR)

#
# In the following, we do not override methods on purpose
# pylint: disable = abstract-method
#

class _TransportMixin(_Transport):

    def __init__(self, sock, proto, evloop):
        _Transport.__init__(self)
        self.evloop = evloop
        self.is_reading = False
        self.is_writing = False
        self.proto = proto
        self.snd_buff = deque()
        self.snd_count = 0
        self.sock = sock

    def close(self):
        self._do_close()

    def _do_close(self, error=None):
        if self.proto:
            self.proto.connection_lost(error)
            self.proto = None
        if self.snd_buff:  # Only detach if we have more to send
            return
        self.snd_buff = None
        # Make sure the `evloop` forgets about this instance
        self.evloop.remove_reader(self.sock.fileno())
        self.evloop.remove_writer(self.sock.fileno())
        self.evloop = None
        self.sock = None

    def pause_reading(self):
        if not self.is_reading:
            return
        self.evloop.remove_reader(self.sock.fileno())
        self.is_reading = False

    def resume_reading(self):
        if self.is_reading:
            return
        self.evloop.add_reader(self.sock.fileno(), self._do_read)
        self.is_reading = True

    def _do_read(self):
        pass

    def _handle_read_error(self, error):
        logging.debug("transport: read error: %s", error)
        self.evloop.call_soon(self._do_close, error)

    def _handle_read(self, data):
        if not data:
            if not self.proto.eof_received():
                self.evloop.call_soon(self._do_close)
        else:
            self.proto.data_received(data)

    def _pause_writing(self):
        if not self.is_writing:
            return
        self.evloop.remove_writer(self.sock.fileno())
        self.is_writing = False

    def _resume_writing(self):
        if self.is_writing:
            return
        self.evloop.add_writer(self.sock.fileno(), self._do_write)
        self.is_writing = True

    def write(self, data):
        if not data:
            return

        self.snd_buff.append(data)
        self.snd_count += len(data)
        if self.snd_count > _HI_WATERMARK:
            self.proto.pause_writing()

        self._resume_writing()

    def _do_write(self):
        pass

    def _handle_write_error(self, error):
        logging.debug("transport: write error: %s", error)
        self.snd_buff.clear()  # Make full close possible
        self.evloop.call_soon(self._do_close, error)

    def _handle_write(self, count):

        if count != len(self.snd_buff[0]):  # Not fully consumed piece
            if count > len(self.snd_buff[0]):
                self._handle_write_error(RuntimeError("Programmer error"))
                return
            self.snd_count -= count
            self.snd_buff[0] = memoryview(self.snd_buff[0])[count:]
            return

        self.snd_count -= len(self.snd_buff[0])
        self.snd_buff.popleft()
        if self.snd_buff:  # More pieces to send
            return

        self._pause_writing()

        if not self.proto:  # Detached
            self.evloop.call_soon(self._do_close)
            return

        self.proto.resume_writing()

class _TransportTCP(_TransportMixin):

    def __init__(self, sock, proto, evloop):
        _TransportMixin.__init__(self, sock, proto, evloop)

    def get_extra_info(self, name, default=None):
        return {
            "peername": _getpeername(self.sock),
            "socket": self.sock,
            "sockname": _getsockname(self.sock),
        }.get(name, default)

    def _do_read(self):
        try:
            data = self.sock.recv(_MAXRECV)
        except socket.error as error:
            if error.errno in _SOFT_IO_ERRORS:
                return
            self._handle_read_error(error)
        else:
            self._handle_read(data)

    def _do_write(self):
        try:
            count = self.sock.send(self.snd_buff[0])
        except socket.error as error:
            if error.errno in _SOFT_IO_ERRORS:
                return
            self._handle_write_error(error)
        else:
            self._handle_write(count)

class _TransportSSL(_TransportMixin):

    def __init__(self, sock, proto, evloop):
        _TransportMixin.__init__(self, sock, proto, evloop)
        self.divert_read = False
        self.divert_write = False
        self.was_reading = False
        self.was_writing = False

    def get_extra_info(self, name, default=None):  # XXX
        return {
            "compression": None,
            "cipher": None,
            "peercert": None,
            "sslcontext": None,
        }.get(name, default)

    def _do_read(self):
        if self.divert_read:
            self.divert_read = False
            if not self.was_reading:
                self.pause_reading()
            self._do_write()
            return
        try:
            data = self.sock.read()
        except socket.error as error:
            if error.args[0] == ssl.SSL_ERROR_WANT_READ:
                return
            if error.args[0] == ssl.SSL_ERROR_WANT_WRITE:
                self.divert_write = True
                self.was_writing = self.is_writing
                self._resume_writing()
                return
            self._handle_read_error(error)
        else:
            self._handle_read(data)

    def _do_write(self):
        if self.divert_write:
            self.divert_write = False
            if not self.was_writing:
                self._pause_writing()
            self._do_read()
            return
        try:
            count = self.sock.write(self.snd_buff[0])
        except socket.error as error:
            if error.args[0] == ssl.SSL_ERROR_WANT_READ:
                self.divert_read = True
                self.was_reading = self.is_reading
                self.resume_reading()
                return
            if error.args[0] == ssl.SSL_ERROR_WANT_WRITE:
                return
            self._handle_write_error(error)
        else:
            self._handle_write(count)

def _ssl_handshake(evloop, sock, ssl_context, server_side, server_hostname):
    # XXX This function raises, make sure the evloop knows that
    ssl_sock = ssl_context.wrap_socket(sock, server_side=server_side,
      do_handshake_on_connect=False, server_hostname=server_hostname)
    future = _Future(loop=evloop)

    def try_handshake():

        def retry_read():
            evloop.remove_reader(ssl_sock.fileno())
            try_handshake()
        def retry_write():
            evloop.remove_writer(ssl_sock.fileno())
            try_handshake()

        try:
            logging.debug("ssl handshaking fileno %d", ssl_sock.fileno())
            ssl_sock.do_handshake()
        except ssl.SSLError as error:
            if error.args[0] == ssl.SSL_ERROR_WANT_READ:
                logging.debug("ssl handshake wants read")
                evloop.add_reader(ssl_sock.fileno(), retry_read)
            elif error.args[0] == ssl.SSL_ERROR_WANT_WRITE:
                logging.debug("ssl handshake wants write")
                evloop.add_writer(ssl_sock.fileno(), retry_write)
            else:
                logging.debug("ssl handshake error: %s", error)
                future.set_exception(error)
        else:
            logging.debug("ssl handshake complete")
            future.set_result(ssl_sock)

    logging.debug("ssl handhsake in progress for %d", ssl_sock.fileno())
    evloop.call_soon(try_handshake)
    return future
