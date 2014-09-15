#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software. See AUTHORS and COPYING for more
# information on the copying conditions.
#

# pylint: disable = missing-docstring

import errno
import logging
import os
import sched
import select
import socket
import time

from .futures import _Future
from .transports import _TransportTCP, _TransportSSL, _ssl_handshake, \
                        _TCPConnector, _Server

# Winsock returns EWOULDBLOCK
_CONNECT_IN_PROGRESS = (0, errno.EINPROGRESS, errno.EWOULDBLOCK, errno.EAGAIN)

if os.name == 'nt':
    _TICKS_FUNC = time.clock
elif os.name == 'posix':
    _TICKS_FUNC = time.time
else:
    raise RuntimeError("Operating system not supported")

def ticks():
    ''' Returns a real representing the most precise clock available
        on the current platform.  Note that, depending on the platform,
        the returned value MIGHT NOT be a timestamp.  So, you MUST
        use this clock to calculate the time elapsed between two events
        ONLY, and you must not use it with timestamp semantics. '''
    return _TICKS_FUNC()

class _LeaveEventLoop(Exception):
    pass

class _Handle(object):

    def __init__(self, evloop, function, args):
        self._args = args
        self._evloop = evloop
        self._evt = None
        self._function = function

    def cancel(self):
        if self._evt:  # is pending?
            self._evloop.cancel_evt_(self._evt)
            self._evt = None

    def get_event_(self):
        return self._evt

    def set_event_(self, evt):
        self._evt = evt

    def callback_(self):
        self._evt = None  # mark as non pending
        self._function(*self._args)

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
        self._keep_running = True
        self._i_am_running = False
        self._i_am_dead = False
        self._readset = {}
        self._scheduler = sched.scheduler(ticks, self._run_select)
        self._writeset = {}

    #
    # 18.5.1.1. Run an event loop
    #

    def run_forever(self):
        if self._i_am_dead:
            raise RuntimeError("eventloop: already closed")
        keepalive_evt = _KeepaliveEvent()
        keepalive_evt.register(self)
        self._i_am_running = True
        try:
            self._scheduler.run()
        except _LeaveEventLoop:
            pass
        self._keep_running = True  # Make restart possible
        self._i_am_running = False

    def _run_select(self, timeout):

        if not self._keep_running:
            raise _LeaveEventLoop()

        if not self._readset and not self._writeset:
            time.sleep(timeout)
            return

        try:
            fdread, fdwrite, _ = select.select(list(self._readset),
              list(self._writeset), [], timeout)
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
            dispatch_io("read", self._readset, filenum)
        for filenum in fdwrite:
            dispatch_io("write", self._writeset, filenum)

    def run_until_complete(self, future):
        future.add_done_callback(self.stop)
        self.run_forever()

    def is_running(self):
        return self._i_am_running

    def stop(self):
        self._keep_running = False

    def close(self):
        self._keep_running = False
        self._i_am_dead = True

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
        handle = _Handle(self, function, args)
        handle.set_event_(self._scheduler.enter(delay, 0,
                          handle.callback_, ()))
        return handle

    def cancel_evt_(self, evt):
        self._scheduler.cancel(evt)

    def call_at(self, when, function, *args):
        raise NotImplementedError

    @staticmethod
    def time():
        return ticks()

    #
    # 18.5.1.4. Coroutines
    #

    def create_task(self, coro):
        raise NotImplementedError

    #
    # 18.5.1.5. Creating connections
    #

    def _create_transport(self, factory, ssl_context, sock,
                          hostname, result=None, server_side=False):
        if not result:
            result = _Future(loop=self)

        def make_both(sock, factory, transport):
            sock.setblocking(False)  # To be sure...
            protocol = factory()
            transport = transport(sock, protocol, self)
            self.call_soon(protocol.connection_made, transport)
            return transport, protocol

        def on_ssl_handshake(future):
            if future.exception():
                result.set_exception(future.exception())
                return
            ssl_sock = future.result()
            result.set_result(make_both(ssl_sock, factory, _TransportSSL))

        if ssl_context:
            fut = _ssl_handshake(self, sock, ssl_context, server_side, hostname)
            fut.add_done_callback(on_ssl_handshake)
        else:
            result.set_result(make_both(sock, factory, _TransportTCP))
        return result

    def create_connection(self, factory, hostname=None, port=None, **kwargs):
        # This implementation is very limited

        ssl_context = kwargs.get("ssl")

        if hostname and port:
            future = _Future(loop=self)
            connector = _TCPConnector(hostname, port, self)

            def on_connect(fut):
                if fut.cancelled():
                    future.cancel()
                    return
                if fut.exception():
                    future.set_exception(error)
                    return
                sock = fut.result()
                self._create_transport(factory, ssl_context, sock, hostname,
                                       result=future)

            connector.add_done_callback(on_connect)
            return future

        sock = kwargs.get("sock")
        if not sock:
            raise RuntimeError("The sock argument must be provided")

        # XXX we ignore server_hostname, we only check whether it's there
        if ssl_context and not kwargs.get("server_hostname"):
            raise RuntimeError("server_hostname is missing")

        return self._create_transport(factory, ssl_context, sock, hostname)

    def create_datagram_endpoint(self, factory, local_addr=None,
                                 remote_addr=None, **kwargs):
        raise NotImplementedError

    def create_unix_connection(self, factory, path=None, **kwargs):
        raise NotImplementedError

    #
    # 18.5.1.6. Creating listening connections
    #

    def create_server(self, factory, host=None, port=None, **kwargs):
        # This implementation is very limited

        sock = kwargs.get("sock")
        if sock:
            raise RuntimeError("sock must be not set")
        ssl_context = kwargs.get("ssl")

        def have_new_socket(new_sock):
            # This calls protocols' connection_made() on success
            self._create_transport(factory, ssl_context, new_sock, host,
                                   server_side=True)

        return _Server(host, port, self, have_new_socket).get_future_()

    def create_unix_server(self, factory, path=None, **kwargs):
        raise NotImplementedError

    #
    # 18.5.1.7. Watch file descriptors
    #

    def add_reader(self, filenum, callback, *args):
        self._readset[filenum] = (self.time(), callback, args)

    def remove_reader(self, filenum):
        if filenum in self._readset:
            del self._readset[filenum]

    def add_writer(self, filenum, callback, *args):
        self._writeset[filenum] = (self.time(), callback, args)

    def remove_writer(self, filenum):
        if filenum in self._writeset:
            del self._writeset[filenum]

    #
    # 18.5.1.8. Low-level socket operations
    #

    def sock_recv(self, sock, nbytes):
        raise NotImplementedError

    def sock_sendall(self, sock, data):
        raise NotImplementedError

    def sock_connect(self, sock, address):
        future = _Future(loop=self)

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
        future = _Future(loop=self)

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

        future = _Future(loop=self)
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

_EVENT_LOOP = _EventLoop()

def _get_event_loop():
    return _EVENT_LOOP
