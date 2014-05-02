# neubot/pollable.py

#
# Copyright (c) 2010, 2012, 2014
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>.
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

#
# Adapted from neubot/net/poller.py
# pylint: disable = missing-docstring
# Python3-ready: yes
#

import errno
import logging
import socket
import ssl
import sys

from neubot import utils

# Soft errors on sockets, i.e. we can retry later
SOFT_ERRORS = (errno.EAGAIN, errno.EWOULDBLOCK, errno.EINTR)

# States returned by the socket model
(SUCCESS, WANT_READ, WANT_WRITE, CONNRESET) = range(4)

# Reclaim stream after 300 seconds
WATCHDOG = 300

class Pollable(object):

    ''' Base class for pollable objects '''

    def __init__(self):
        self.created = utils.ticks()
        self.watchdog = WATCHDOG

    def fileno(self):
        ''' Return file descriptor number '''
        return -1

    def handle_read(self):
        ''' Handle the READ event '''

    def handle_write(self):
        ''' Handle the WRITE event '''

    def handle_close(self):
        ''' Handle the CLOSE event '''

    def handle_periodic(self, timenow):
        ''' Handle the PERIODIC event '''
        return self.watchdog >= 0 and timenow - self.created > self.watchdog

    def set_timeout(self, timeo):
        ''' Set timeout of this pollable '''
        self.created = utils.ticks()
        self.watchdog = timeo

class SSLWrapper(object):
    def __init__(self, sock):
        self.sock = sock

    def close(self):
        try:
            self.sock.close()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            logging.warning('sslstream: sock.close() failed', exc_info=1)

    def sorecv(self, maxlen):
        try:
            return SUCCESS, self.sock.read(maxlen)
        except ssl.SSLError:
            exception = sys.exc_info()[1]
            if exception.args[0] == ssl.SSL_ERROR_WANT_READ:
                return WANT_READ, b""
            elif exception.args[0] == ssl.SSL_ERROR_WANT_WRITE:
                return WANT_WRITE, b""
            else:
                raise

    def sosend(self, octets):
        try:
            return SUCCESS, self.sock.write(octets)
        except ssl.SSLError:
            exception = sys.exc_info()[1]
            if exception.args[0] == ssl.SSL_ERROR_WANT_READ:
                return WANT_READ, 0
            elif exception.args[0] == ssl.SSL_ERROR_WANT_WRITE:
                return WANT_WRITE, 0
            else:
                raise

class SocketWrapper(object):
    def __init__(self, sock):
        self.sock = sock

    def close(self):
        try:
            self.sock.close()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            logging.warning('stream: sock.close() failed', exc_info=1)

    def sorecv(self, maxlen):
        try:
            return SUCCESS, self.sock.recv(maxlen)
        except socket.error:
            exception = sys.exc_info()[1]
            if exception.args[0] in SOFT_ERRORS:
                return WANT_READ, b""
            elif exception.args[0] == errno.ECONNRESET:
                return CONNRESET, b""
            else:
                raise

    def sosend(self, octets):
        try:
            return SUCCESS, self.sock.send(octets)
        except socket.error:
            exception = sys.exc_info()[1]
            if exception.args[0] in SOFT_ERRORS:
                return WANT_WRITE, 0
            elif exception.args[0] == errno.ECONNRESET:
                return CONNRESET, 0
            else:
                raise
