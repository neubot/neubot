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

from neubot.neubot_asyncio import async
from neubot.neubot_asyncio import get_event_loop

class TCPListenerError(Exception):

    def __init__(self, errors):
        Exception.__init__(self)
        self.errors = errors

    def __repr__(self):
        return "TCPListenerError<%s>" % self.errors

class TCPListener(object):

    def __init__(self, endpoint, prefer_ipv6, callback, *args):
        logging.debug("listen: %s [%s]", endpoint, prefer_ipv6)
        self.endpoint = endpoint
        self.prefer_ipv6 = prefer_ipv6
        self.callback = callback
        self.args = args
        self.loop = get_event_loop()
        self.ainfo_todo = deque()
        self.count_successful = []
        self.count_errors = []

    def listen(self):
        logging.debug("listen: resolve '%s'", self.endpoint[0])
        resolve_fut = self.loop.getaddrinfo(self.endpoint[0], self.endpoint[1],
          type=socket.SOCK_STREAM, flags=socket.AI_PASSIVE)
        resolve_fut.add_done_callback(self.has_ainfo)
        return self

    def has_ainfo(self, fut):

        if fut.exception():
            error = fut.exception()
            logging.warning("listen: resolver error: %s", error)
            self.callback(error, None, *self.args)
            return

        ainfo_all = fut.result()

        for index, ainfo in enumerate(ainfo_all):
            logging.debug("listen: ainfo_all[%d] = %s", index, ainfo)

        ainfo_v4 = [elem for elem in ainfo_all if elem[0] == socket.AF_INET]
        ainfo_v6 = [elem for elem in ainfo_all if elem[0] == socket.AF_INET6]

        if self.prefer_ipv6:
            self.ainfo_todo.extend(ainfo_v6)
            self.ainfo_todo.extend(ainfo_v4)
        else:
            self.ainfo_todo.extend(ainfo_v4)
            self.ainfo_todo.extend(ainfo_v6)

        for index, ainfo in enumerate(self.ainfo_todo):
            logging.debug("listen: ainfo_todo[%d] = %s", index, ainfo)

        self.loop.call_soon(self.listen_next)

    def listen_next(self):

        if not self.ainfo_todo:
            if not self.count_successful:
                self.callback(TCPListenerError(self.count_errors),
                              None, *self.args)
                return
            logging.debug("listen: no more available addrs")
            return

        ainfo = self.ainfo_todo.popleft()
        logging.debug("listen: try listen: %s", ainfo)

        try:
            sock = socket.socket(ainfo[0], socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setblocking(False)
            sock.bind(ainfo[4])
            # Probably the backlog here is too big
            sock.listen(128)

        except socket.error as error:
            logging.debug("listen: error occurred for %s: %s", ainfo[4], error)
            self.count_errors.append((ainfo, error))
        else:
            self.count_successful.append(sock)
            self.loop.call_soon(self.do_accept, sock)
        finally:
            self.loop.call_soon(self.listen_next)

    def do_accept(self, sock):
        future = self.loop.sock_accept(sock)
        def has_connected_socket(future):
            new_future = self.loop.sock_accept(sock)
            new_future.add_done_callback(has_connected_socket)
            self.callback(None, future.result()[0], *self.args)
        future.add_done_callback(has_connected_socket)

def listen_tcp_socket(endpoint, prefer_ipv6, callback, *args):
    TCPListener(endpoint, prefer_ipv6, callback, args).listen()

def listen_tcp_transport(factory, endpoint, prefer_ipv6, callback, *args):

    def connection_made(error, sock, *ignored_args):
        if error:
            callback(error, None, *args)
            return

        loop = get_event_loop()
        generator_fut = async(loop.create_connection(factory, sock=sock))

        def really_done(future):
            if future.exception():
                callback(future.exception(), None, *args)
                return
            callback(None, future.result(), *args)

        generator_fut.add_done_callback(really_done)

    listen_tcp_socket(endpoint, prefer_ipv6, connection_made)
