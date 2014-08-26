#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software. See AUTHORS and COPYING for more
# information on the copying conditions.
#

# pylint: disable = missing-docstring

import errno
import logging
import sched
import select
import socket
import time

from ._futures import _FutureImpl
from ._utils import _ticks

# Winsock returns EWOULDBLOCK
_CONNECT_IN_PROGRESS = (0, errno.EINPROGRESS, errno.EWOULDBLOCK, errno.EAGAIN)

class _LeaveEventLoop(Exception):
    pass

class _Handle(object):

    def __init__(self, evloop, evt):
        self.evloop = evloop
        self.evt = evt

    def cancel(self):
        self.evloop.cancel_evt_(self.evt)

    def get_evt_(self):
        return self.evt

class _KeepaliveEvent(object):

    def __init__(self):
        self.evloop = None
        self.evt = None

    def __del__(self):
        self.evt.cancel()
        self.evloop = None
        self.evt = None

    def register(self, evloop):
        self.evloop = evloop
        self.evt = self.evloop.call_later(10.0, self.keepalive_fn)
        return self

    def keepalive_fn(self):
        self.evt = self.evloop.call_later(10.0, self.keepalive_fn)

class _EventLoop(object):

    def __init__(self):
        self.keep_running = True
        self.i_am_running = False
        self.i_am_dead = False
        self.readset = {}
        self.scheduler = sched.scheduler(_ticks, self._run_select)
        self.writeset = {}

    #
    # 18.5.1.1. Run an event loop
    #

    def run_forever(self):
        if self.i_am_dead:
            raise RuntimeError("eventloop: already closed")
        keepalive_evt = _KeepaliveEvent()
        keepalive_evt.register(self)
        self.i_am_running = True
        try:
            self.scheduler.run()
        except _LeaveEventLoop:
            pass
        self.keep_running = True  # Make restart possible
        self.i_am_running = False

    def _run_select(self, timeout):

        if not self.keep_running:
            raise _LeaveEventLoop()

        if not self.readset and not self.writeset:
            time.sleep(timeout)
            return

        try:
            fdread, fdwrite, _ = select.select(list(self.readset),
              list(self.writeset), [], timeout)
        except select.error as error:
            if error[0] == errno.EINTR:
                return
            raise

        def dispatch_io(what, ioset, filenum):
            logging.debug("eventloop: dispatch '%s' event of filedesc %d",
                          what, filenum)
            try:
                _, callback, args = ioset[filenum]
                callback(*args)
            except KeyboardInterrupt:
                raise
            except SystemExit:
                raise
            except Exception as error:
                self.call_exception_handler({
                    "message": "I/O callback failed",
                    "exception": error
                })

        for filenum in fdread:
            dispatch_io("read", self.readset, filenum)
        for filenum in fdwrite:
            dispatch_io("write", self.writeset, filenum)

    def run_until_complete(self, future):
        future.add_done_callback(self.stop)
        self.run_forever()

    def is_running(self):
        return self.i_am_running

    def stop(self):
        self.keep_running = False

    def close(self):
        self.keep_running = False
        self.i_am_dead = True

    #
    # 18.5.1.2. Calls
    #

    def call_soon(self, function, *args):
        return self.call_later(0.0, function, *args)

    def call_soon_threadsafe(self, function, *args):
        raise NotImplementedError

    #
    # 18.5.1.3. Delayed calls
    #

    def call_later(self, delay, function, *args):
        return _Handle(self, self.scheduler.enter(delay, 0, function, args))

    def cancel_evt_(self, evt):
        self.scheduler.cancel(evt)

    def call_at(self, when, function, *args):
        raise NotImplementedError

    @staticmethod
    def time():
        return _ticks()

    #
    # 18.5.1.4. Coroutines
    #

    def create_task(self, coro):
        raise NotImplementedError

    #
    # 18.5.1.5. Creating connections
    #

    def create_connection(self, factory, hostname=None, port=None, **kwargs):
        raise NotImplementedError

    def create_datagram_endpoint(self, factory, local_addr=None,
                                 remote_addr=None, **kwargs):
        raise NotImplementedError

    def create_unix_connection(self, factory, path=None, **kwargs):
        raise NotImplementedError

    #
    # 18.5.1.6. Creating listening connections
    #

    def create_server(self, factory, host=None, port=None, **kwargs):
        raise NotImplementedError

    def create_unix_server(self, factory, path=None, **kwargs):
        raise NotImplementedError

    #
    # 18.5.1.7. Watch file descriptors
    #

    def add_reader(self, filenum, callback, *args):
        self.readset[filenum] = (self.time(), callback, args)

    def remove_reader(self, filenum):
        if filenum in self.readset:
            del self.readset[filenum]

    def add_writer(self, filenum, callback, *args):
        self.writeset[filenum] = (self.time(), callback, args)

    def remove_writer(self, filenum):
        if filenum in self.writeset:
            del self.writeset[filenum]

    #
    # 18.5.1.8. Low-level socket operations
    #

    def sock_recv(self, sock, nbytes):
        raise NotImplementedError

    def sock_sendall(self, sock, data):
        raise NotImplementedError

    def sock_connect(self, sock, address):
        future = _FutureImpl(self)

        try:
            sock.connect(address)
        except socket.error as error:
            if error.errno not in _CONNECT_IN_PROGRESS:
                future.set_exception(error)
                return future
            # FALLTHROUGH

        def maybe_connected():
            self.remove_writer(sock.fileno())
            # See http://cr.yp.to/docs/connect.html
            try:
                sock.getpeername()
            except socket.error:
                # Simplified version: just check error after recv()
                try:
                    sock.recv(1)
                except socket.error as error:
                    future.set_exception(error)
            else:
                future.set_result(None)

        self.add_writer(sock.fileno(), maybe_connected)
        return future

    def sock_accept(self, sock):
        future = _FutureImpl(self)

        def maybe_accept():
            try:
                conn, address = sock.accept()
            except socket.error:
                # Apparently, Python3.4 does not report any error
                logging.warning("eventloop: accept() failed", exc_info=1)
            else:
                conn.setblocking(False)
                future.set_result((conn, address))

        self.add_reader(sock.fileno(), maybe_accept)
        return future

    #
    # 18.5.1.9. Resolve host name
    #

    def getaddrinfo(self, hostname, port, **kwargs):

        future = _FutureImpl(self)
        try:
            ainfo = socket.getaddrinfo(hostname, port, kwargs.get("family", 0),
              kwargs.get("type", 0), kwargs.get("proto", 0),
              kwargs.get("flags", 0))
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as error:
            future.set_exception(error)
        else:
            future.set_result(ainfo)
        return future

    def getnameinfo(self, sockaddr, flags=0):
        raise NotImplementedError

    #
    # 18.5.1.10. Connect pipes
    #

    def connect_read_pipe(self, factory, pipe):
        raise NotImplementedError

    def connect_write_pipe(self, factory, pipe):
        raise NotImplementedError

    #
    # 18.5.1.11. UNIX signals
    #

    def add_signal_handler(self, signum, callback, *args):
        raise NotImplementedError

    def remove_signal_handler(self, signum):
        raise NotImplementedError

    #
    # 18.5.1.12. Executor
    #

    def run_in_executor(self, executor, callback, *args):
        raise NotImplementedError

    def set_default_executor(self, executor):
        raise NotImplementedError

    #
    # 18.5.1.13. Error Handling API
    #

    def set_exception_handler(self, handler):
        raise NotImplementedError

    def default_exception_handler(self, context):
        self._real_exception_handler(context)

    @staticmethod
    def _real_exception_handler(context):
        logging.debug("evloop: unhandled exception: %s", context)

    def call_exception_handler(self, context):
        self.default_exception_handler(context)

    #
    # 18.5.1.14. Debug mode
    #

    def get_debug(self):
        raise NotImplementedError

    def set_debug(self, enabled):
        raise NotImplementedError
