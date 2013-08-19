# @DEST@

#
# Copyright (c) 2010, 2011-2013
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>
#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Neubot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Neubot.  If not, see <http://www.gnu.org/licenses/>.
#

""" Network SSL """

include(`m4/include/aaa_base.m4')
include(`m4/include/network.m4')

NEUBOT_PY3_READY()

import errno
import logging
import os
import ssl
import socket
import sys

from neubot import six
from neubot import utils_net

class SSLSocket(object):
    """ SSL socket object """

    #
    # The SSL socket is more complex than the stream socket. There is extra
    # complexity, in fact, because the SSL socket also needs to deal with (i)
    # handshaking and (ii) renegotiations. In both cases, a read operation
    # may also want to read from the socket, and a write operation may also
    # want to write into the socket.
    #

    SOCK_IMPLEMENT_INIT()
        self.tcp_accept_pending = 0
        self.tcp_connect_pending = 0

        self.ssl_handshake_pending = 0
        self.ssl_hijack_recv = 0
        self.ssl_hijack_send = 0
        self.ssl_recv_pending = 0
        self.ssl_send_pending = 0

    SOCK_IMPLEMENT_BIND_AND_CONNECT()

    SSL_IMPLEMENT_SENDRECV(recv, read, read, send, write,
      SSL_ERROR_WANT_READ, SSL_ERROR_WANT_WRITE, 0, None)

    SSL_IMPLEMENT_SENDRECV(send, write, write, recv, read,
      SSL_ERROR_WANT_WRITE, SSL_ERROR_WANT_READ, None, 0)

    SOCK_IMPLEMENT_COMMON_CODE()

    TCP_IMPLEMENT_WAIT_CONNECTED()

    TCP_IMPLEMENT_LISTEN_AND_ACCEPT()

    TCP_IMPLEMENT_READWRITE_HANDLERS(_ssl_recv, _ssl_send)

    def ssl_handshake(self, server_side, certfile):
        """ Perform the SSL handshake """
        #
        # Replace sock_socket, because sock_socket becomes pretty useless
        # after we call ssl.SSLSocket().
        #
        try:
            self.sock_socket = ssl.SSLSocket(self.sock_socket,
              do_handshake_on_connect=False, certfile=certfile,
              server_side=server_side)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            NEUBOT_ERRNO(error)
            NEUBOT_PERROR(warning, network: ssl.SSLSocket failed, error)
            self.ssl_handshake_complete(error)

        self._ssl_do_handshake()

    def _ssl_do_handshake(self):
        """ Internal SSL handshake function """
        try:
            self.sock_socket.do_handshake()
        except ssl.SSLError:
            NEUBOT_ERRNO(error)
            if error.args[0] == ssl.SSL_ERROR_WANT_READ:
                self.sock_poller.set_read(self)
                self.ssl_handshake_pending = 1
            elif error.args[0] == ssl.SSL_ERROR_WANT_WRITE:
                self.sock_poller.set_write(self)
                self.ssl_handshake_pending = 1
            else:
                NEUBOT_PERROR(warning, network: SSL_handshake failed, error)
                self.ssl_handshake_complete(error)
        else:
            self.ssl_handshake_complete(None)

    def ssl_handshake_complete(self, error):
        """ Invoked when the handshake is complete """

class BuffSSLSocket(SSLSocket):
    """ Bufferised SSL socket """

    BUFF_IMPLEMENT_INIT(SSLSocket)

    BUFF_IMPLEMENT_IBUFF()

    BUFF_IMPLEMENT_OBUFF()
