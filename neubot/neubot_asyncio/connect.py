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

try:
    from asyncio import Future
    from asyncio import get_event_loop
    _HAVE_NATIVE_ASYNCIO = True

except ImportError:
    from .futures import Future
    from ._globals import _get_event_loop as get_event_loop
    from .transports import _TransportTCP
    _HAVE_NATIVE_ASYNCIO = False

def connect_tcp_socket(hostname, port, family):

    if family.startswith("PF_"):
        family = family.replace("PF_", "AF_")

    logging.debug("connect: %s:%s [%s]", hostname, port, family)

    loop = get_event_loop()

    logging.debug("connect: resolve '%s'", hostname)
    resolve_fut = loop.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    outer_fut = Future()

    def has_ainfo(fut):
        if fut.exception():
            error = fut.exception()
            logging.warning("connect: resolver error: %s", error)
            outer_fut.set_exception(error)
            return

        ainfo_all = fut.result()

        for index, ainfo in enumerate(ainfo_all):
            logging.debug("connect: ainfo_all[%d] = %s", (index, ainfo))

        ainfo_v4 = [elem for elem in ainfo_all if elem[0] == socket.AF_INET]
        ainfo_v6 = [elem for elem in ainfo_all if elem[0] == socket.AF_INET6]
        ainfo_todo = deque()

        if family == "AF_INET":
            ainfo_todo.extend(ainfo_v4)
        elif family == "AF_INET6":
            ainfo_todo.extend(ainfo_v6)
        elif family == "AF_UNSPEC":
            ainfo_todo.extend(ainfo_v4)
            ainfo_todo.extend(ainfo_v6)
        elif family == "AF_UNSPEC6":
            ainfo_todo.extend(ainfo_v6)
            ainfo_todo.extend(ainfo_v4)
        else:
            outer_fut.set_exception(RuntimeError("Invalid family"))
            return

        for index, ainfo in enumerate(ainfo_todo):
            logging.debug("connect: ainfo_todo[%d] = %s", (index, ainfo))

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

if _HAVE_NATIVE_ASYNCIO:

    def connect_tcp_transport(factory, hostname, port, family):

        loop = get_event_loop()
        outer_fut = Future()
        connect_fut = connect_tcp_socket(hostname, port, family)

        def connection_made(future):
            if future.exception():
                error = future.exception()
                outer_fut.set_exception(error)
                return

            sock = future.result()

            generator = loop.create_connection(factory, sock=sock)
            generator_fut = async(generator)

            def really_done(future):
                if future.exception():
                    outer_fut.set_exception(future.exception())
                    return
                outer_fut.set_result(future.result())

            generator_fut.add_done_callback(really_done)

        connect_fut.add_done_callback(connection_made)
        return outer_fut

else:
    def connect_tcp_transport(factory, hostname, port, family):

        loop = get_event_loop()
        outer_fut = Future()
        connect_fut = connect_tcp_socket(hostname, port, family)

        def connection_made(future):
            if future.exception():
                error = future.exception()
                outer_fut.set_exception(error)
                return

            sock = future.result()

            protocol = factory()
            transport = _TransportTCP(sock, protocol)
            loop.call_soon(protocol.connection_made, transport)
            outer_fut.set_result((transport, protocol))
            return

        connect_fut.add_done_callback(connection_made)
        return outer_fut
