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

from neubot.neubot_asyncio import Future
from neubot.neubot_asyncio import async
from neubot.neubot_asyncio import get_event_loop

class TCPConnector(object):

    def __init__(self, endpoint, prefer_ipv6):
        self.endpoint = endpoint
        self.prefer_ipv6 = prefer_ipv6
        self.future = None
        self.ainfo_todo = deque()

    def connect(self):
        logging.debug("connect: %s [%s]", self.endpoint, self.prefer_ipv6)
        loop = get_event_loop()
        logging.debug("connect: resolve '%s'", self.endpoint[0])
        resolve_fut = loop.getaddrinfo(self.endpoint[0], self.endpoint[1],
                                       type=socket.SOCK_STREAM)
        self.future = Future(loop=loop)
        resolve_fut.add_done_callback(self.has_ainfo)
        return self.future

    def has_ainfo(self, fut):
        if fut.exception():
            error = fut.exception()
            logging.warning("connect: resolver error: %s", error)
            self.future.set_exception(error)
            return

        ainfo_all = fut.result()

        for index, ainfo in enumerate(ainfo_all):
            logging.debug("connect: ainfo_all[%d] = %s", index, ainfo)

        ainfo_v4 = [elem for elem in ainfo_all if elem[0] == socket.AF_INET]
        ainfo_v6 = [elem for elem in ainfo_all if elem[0] == socket.AF_INET6]

        if self.prefer_ipv6:
            self.ainfo_todo.extend(ainfo_v6)
            self.ainfo_todo.extend(ainfo_v4)
        else:
            self.ainfo_todo.extend(ainfo_v4)
            self.ainfo_todo.extend(ainfo_v6)

        for index, ainfo in enumerate(self.ainfo_todo):
            logging.debug("connect: ainfo_todo[%d] = %s", index, ainfo)

        self.connect_next()

    def connect_next(self):
        if not self.ainfo_todo:
            logging.warning("connect: no more available addrs")
            self.future.set_exception(RuntimeError("Connect failed"))
            return

        loop = get_event_loop()
        ainfo = self.ainfo_todo.popleft()
        logging.debug("connect: try connect: %s", ainfo)

        sock = socket.socket(ainfo[0], socket.SOCK_STREAM)
        sock.setblocking(False)
        connect_fut = loop.sock_connect(sock, ainfo[4])

        def maybe_connected(fut):
            if fut.exception():
                error = fut.exception()
                logging.warning("connect: connect error: %s", error)
                logging.warning("connect: will try next available address")
                loop.call_soon(self.connect_next)
                return

            logging.debug("connect: connect ok")
            self.future.set_result(sock)

        connect_fut.add_done_callback(maybe_connected)

def connect_tcp_socket(endpoint, prefer_ipv6):
    return TCPConnector(endpoint, prefer_ipv6).connect()
