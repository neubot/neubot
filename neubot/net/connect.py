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

def connect_tcp_socket(endpoint, prefer_ipv6):

    logging.debug("connect: %s [%s]", endpoint, prefer_ipv6)

    loop = get_event_loop()

    logging.debug("connect: resolve '%s'", endpoint[0])
    resolve_fut = loop.getaddrinfo(endpoint[0], endpoint[1],
                                   type=socket.SOCK_STREAM)
    outer_fut = Future(loop=loop)

    def has_ainfo(fut):
        if fut.exception():
            error = fut.exception()
            logging.warning("connect: resolver error: %s", error)
            outer_fut.set_exception(error)
            return

        ainfo_all = fut.result()

        for index, ainfo in enumerate(ainfo_all):
            logging.debug("connect: ainfo_all[%d] = %s", index, ainfo)

        ainfo_v4 = [elem for elem in ainfo_all if elem[0] == socket.AF_INET]
        ainfo_v6 = [elem for elem in ainfo_all if elem[0] == socket.AF_INET6]
        ainfo_todo = deque()

        if prefer_ipv6:
            ainfo_todo.extend(ainfo_v6)
            ainfo_todo.extend(ainfo_v4)
        else:
            ainfo_todo.extend(ainfo_v4)
            ainfo_todo.extend(ainfo_v6)

        for index, ainfo in enumerate(ainfo_todo):
            logging.debug("connect: ainfo_todo[%d] = %s", index, ainfo)

        def connect_next():
            if not ainfo_todo:
                logging.warning("connect: no more available addrs")
                outer_fut.set_exception(RuntimeError("Connect failed"))
                return

            ainfo = ainfo_todo.popleft()
            logging.debug("connect: try connect: %s", ainfo)

            sock = socket.socket(ainfo[0], socket.SOCK_STREAM)
            sock.setblocking(False)
            connect_fut = loop.sock_connect(sock, ainfo[4])

            def maybe_connected(fut):
                if fut.exception():
                    error = fut.exception()
                    logging.warning("connect: connect error: %s", error)
                    loop.call_soon(connect_next)
                    return

                logging.debug("connect: connect ok")
                outer_fut.set_result(sock)

            connect_fut.add_done_callback(maybe_connected)

        connect_next()

    resolve_fut.add_done_callback(has_ainfo)
    return outer_fut

def connect_tcp_transport(factory, endpoint, prefer_ipv6):

    loop = get_event_loop()
    outer_fut = Future(loop=loop)
    connect_fut = connect_tcp_socket(endpoint, prefer_ipv6)

    def connection_made(future):
        if future.exception():
            error = future.exception()
            outer_fut.set_exception(error)
            return

        sock = future.result()

        generator_fut = async(loop.create_connection(factory, sock=sock))

        def really_done(future):
            if future.exception():
                outer_fut.set_exception(future.exception())
                return
            outer_fut.set_result(future.result())

        generator_fut.add_done_callback(really_done)

    connect_fut.add_done_callback(connection_made)
    return outer_fut
