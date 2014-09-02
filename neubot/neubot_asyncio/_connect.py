#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software. See AUTHORS and COPYING for more
# information on the copying conditions.
#

""" Implementation of connect() for event_loop.create_connection(). """

# pylint: disable = missing-docstring

from collections import deque

import logging
import socket

class _TCPConnector(object):

    """ Connects to the given address and port.

        Address is always resolved to a sequence of addrinfo using the
        getaddrinfo library call, as implemented by the event loop.

        Then, the connector tries to connect() to the first addrinfo
        returned. If successful, it emits the "connect" event that also
        receives the connected socket as an argument. Otherwise, it
        tries with the second addrinfo in the list, and so on, until
        all the addrinfos have been exhausted. In such case, the "error"
        event is emitted with an exception as an argument. """

    def __init__(self, address, port, evloop):
        self._evloop = evloop
        self._handlers = {}
        self._is_cancelled = False
        self._ainfo_todo = None

        logging.debug("connect: %s:%s", address, port)
        resolve_fut = self._evloop.getaddrinfo(address, port,
                        type=socket.SOCK_STREAM)
        resolve_fut.add_done_callback(self._has_ainfo)

    def on(self, event, handler):
        self._handlers[event] = handler

    def cancel(self):
        self._is_cancelled = True

    def _emit(self, event, *args):
        handler = self._handlers.get(event)
        if handler:
            handler(*args)

    def _has_ainfo(self, fut):
        if self._is_cancelled:
            self._emit("error", RuntimeError("Is cancelled"))
            return

        if fut.exception():
            error = fut.exception()
            logging.warning("connect: resolver error: %s", error)
            self._emit("error", error)
            return

        self._ainfo_todo = deque(fut.result())

        for index, ainfo in enumerate(self._ainfo_todo):
            logging.debug("connect: ainfo[%d] = %s", index, ainfo)

        self._connect_next()

    def _connect_next(self):
        if self._is_cancelled:
            self._emit("error", RuntimeError("Is cancelled"))
            return

        if not self._ainfo_todo:
            logging.warning("connect: no more available addrs")
            self._emit("error", RuntimeError("All connect()s failed"))
            return

        ainfo = self._ainfo_todo.popleft()
        logging.debug("connect: try connect: %s", ainfo)

        sock = socket.socket(ainfo[0], socket.SOCK_STREAM)
        sock.setblocking(False)
        connect_fut = self._evloop.sock_connect(sock, ainfo[4])

        def maybe_connected(fut):
            if fut.exception():
                error = fut.exception()
                logging.warning("connect: connect error: %s", error)
                logging.warning("connect: will try next available address")
                self._evloop.call_soon(self._connect_next)
                return

            logging.debug("connect: connect ok")
            self._emit("connect", sock)

        connect_fut.add_done_callback(maybe_connected)
