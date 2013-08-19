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

""" Network core """

include(`m4/include/aaa_base.m4')
include(`m4/include/network.m4')

NEUBOT_PY3_READY()

import errno
import logging
import os
import socket
import sys

from neubot import six
from neubot import utils_net

class DatagramSocket(object):
    """ Datagram socket object """

    SOCK_IMPLEMENT_INIT()

    SOCK_IMPLEMENT_BIND_AND_CONNECT()

    SOCK_IMPLEMENT_RECV_AND_SEND(sock_handle_read, sock_handle_write)

    SOCK_IMPLEMENT_COMMON_CODE()

class StreamSocket(object):
    """ Stream socket object """

    #
    # The stream socket is more complex than the datagram socket because the
    # stream socket also keeps track of the connecting/accepting state.
    #

    SOCK_IMPLEMENT_INIT()
        self.tcp_accept_pending = 0
        self.tcp_connect_pending = 0

    SOCK_IMPLEMENT_BIND_AND_CONNECT()

    SOCK_IMPLEMENT_RECV_AND_SEND(_tcp_recv, _tcp_send)

    SOCK_IMPLEMENT_COMMON_CODE()

    TCP_IMPLEMENT_WAIT_CONNECTED()

    TCP_IMPLEMENT_LISTEN_AND_ACCEPT()

    TCP_IMPLEMENT_READWRITE_HANDLERS(_tcp_recv, _tcp_send)

class BuffStreamSocket(StreamSocket):
    """ Bufferised stream socket """

    BUFF_IMPLEMENT_INIT(StreamSocket)

    BUFF_IMPLEMENT_IBUFF()

    BUFF_IMPLEMENT_OBUFF()
