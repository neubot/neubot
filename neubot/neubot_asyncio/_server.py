#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software. See AUTHORS and COPYING for more
# information on the copying conditions.
#

# pylint: disable = missing-docstring

from collections import deque

import logging
import socket

from .futures import _Future

class _Server(object):

    def __init__(self, address, port, evloop, callback):
        self._address = address
        self._port = port
        self._loop = evloop
        self._callback = callback
        self._ainfo_todo = deque()
        self._server_fut = _Future(loop=evloop)
        self.sockets = []

    def listen_(self):
        logging.debug("listen at %s:%s", self._address, self._port)
        resolve_fut = self._loop.getaddrinfo(
                                             self._address,
                                             self._port,
                                             type=socket.SOCK_STREAM,
                                             flags=socket.AI_PASSIVE
                                            )
        resolve_fut.add_done_callback(self._has_ainfo)
        return self._server_fut

    def _has_ainfo(self, fut):

        if fut.exception():
            error = fut.exception()
            logging.warning("listen: resolver error: %s", error)
            self._server_fut.set_result(self)
            return

        ainfo_all = fut.result()

        for index, ainfo in enumerate(ainfo_all):
            logging.debug("listen: ainfo_all[%d] = %s", index, ainfo)

        ainfo_v4 = [elem for elem in ainfo_all if elem[0] == socket.AF_INET]
        ainfo_v6 = [elem for elem in ainfo_all if elem[0] == socket.AF_INET6]

        # XXX
        self._ainfo_todo.extend(ainfo_v6)
        self._ainfo_todo.extend(ainfo_v4)

        for index, ainfo in enumerate(self._ainfo_todo):
            logging.debug("listen: ainfo_todo[%d] = %s", index, ainfo)

        self._loop.call_soon(self._listen_next)

    def _listen_next(self):

        if not self._ainfo_todo:
            logging.debug("listen: no more available addrs")
            self._server_fut.set_result(self)
            return

        ainfo = self._ainfo_todo.popleft()
        logging.debug("listen: try listen: %s", ainfo)

        try:
            sock = socket.socket(ainfo[0], socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setblocking(False)
            # Nice trick from asyncio: disable dual stack on Linux
            if (ainfo[0] == socket.AF_INET6 and hasattr(socket, "IPV6_V6ONLY")
                and hasattr(socket, "IPPROTO_IPV6")):
                sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, True)
            sock.bind(ainfo[4])
            # Probably the backlog here is too big
            sock.listen(128)

        except socket.error as error:
            # Mimic the behavior of asyncio and bind all or nothing
            logging.debug("listen: error occurred for %s: %s", ainfo[4], error)
            for sock in self.sockets:
                sock.close()
            self.sockets = []
            self._server_fut.set_result(self)
        else:
            logging.debug("listen: OK for %s", ainfo[4])
            self.sockets.append(sock)
            self._loop.call_soon(self._do_accept, sock)
            self._loop.call_soon(self._listen_next)

    def _do_accept(self, sock):
        future = self._loop.sock_accept(sock)
        def has_connected_socket(future):
            new_future = self._loop.sock_accept(sock)
            new_future.add_done_callback(has_connected_socket)
            if future.exception():  # Should not happen
                return
            new_sock, _ = future.result()
            self._callback(new_sock)
        future.add_done_callback(has_connected_socket)

    def close(self):
        raise NotImplementedError

    def wait_closed(self):
        raise NotImplementedError
