#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software. See AUTHORS and COPYING for more
# information on the copying conditions.
#

# pylint: disable = missing-docstring

from collections import deque

import errno
import socket

from ._utils import _getsockname
from ._utils import _getpeername

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

_SOFT_IO_ERRORS = (errno.EAGAIN, errno.EWOULDBLOCK, errno.EINTR)
_HI_WATERMARK = 1 << 17

#
# In the following, we do not override methods on purpose
# pylint: disable = abstract-method
#

class _TransportTCP(_Transport):

    def __init__(self, sock, proto, evloop):
        _Transport.__init__(self)
        self.evloop = evloop
        self.is_reading = False
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

    def get_extra_info(self, name, default=None):
        return {
            "peername": _getpeername(self.sock),
            "socket": self.sock,
            "sockname": _getsockname(self.sock),
        }.get(name, default)

    def pause_reading(self):
        self.evloop.remove_reader(self.sock.fileno())
        self.is_reading = False

    def resume_reading(self):
        self.evloop.add_reader(self.sock.fileno(), do_read)
        if self.is_reading:
            return
        self.is_reading = True

        def do_read():

            try:
                data = self.sock.recv()
            except socket.error as error:
                if error.errno in _SOFT_IO_ERRORS:
                    return
                self.evloop.call_soon(self._do_close, error)
                return

            if not data:
                if not self.proto.eof_received():
                    self.evloop.call_soon(self._do_close)
                return

            self.proto.data_received(data)

    def write(self, data):
        if not data:
            return

        self.snd_buff.append(data)
        self.snd_count += len(data)
        if self.snd_count > _HI_WATERMARK:
            self.proto.pause_writing()

        if len(self.snd_buff) > 1:  # Not first time we insert in queue
            return

        self.evloop.add_writer(self.sock.fileno(), do_write)

        def do_write():

            try:
                count = self.sock.send(self.snd_buff[0])
            except socket.error as error:
                if error.errno in _SOFT_IO_ERRORS:
                    return
                # Hard I/O error
                self.snd_buff.clear()
                self.evloop.call_soon(self._do_close, error)
                return

            self.snd_count -= len(self.snd_buff[0])
            self.snd_buff[0] = memoryview(self.snd_buff[0])[count:]

            if count != len(self.snd_buff[0]):  # Not fully consumed piece
                if count > len(self.snd_buff[0]):
                    self.snd_buff.clear()  # Make full close possible
                    self.evloop.call_soon(self._do_close,
                      RuntimeError("Programmer error"))
                    return
                return

            self.snd_buff.popleft()
            if self.snd_buff:  # More pieces to send
                return

            self.evloop.remove_writer(self.sock.fileno())

            if not self.proto:  # Detached
                self.evloop.call_soon(self._do_close)
                return

            self.proto.resume_writing()
