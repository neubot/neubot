# mod_library_net/net/stream_ssl.py

#
# Copyright (c) 2010-2012, 2014
#   Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#   and Simone Basso <bassosimone@gmail.com>.
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

""" SSL stream wrapper """

import logging
import ssl

from .stream_model import SUCCESS
from .stream_model import WANT_READ
from .stream_model import WANT_WRITE
from .stream_model import ERROR
#from .stream_model import CONNRESET
from .stream_model import StreamModel

class StreamSSL(StreamModel):
    """ Wrapper for SSL sockets """

    def __init__(self, sock):
        StreamModel.__init__(self, sock)

    def soclose(self):
        try:
            self.sock.close()
        except ssl.SSLError:
            logging.error('Exception', exc_info=1)

    def sorecv(self, maxlen):
        try:
            octets = self.sock.read(maxlen)
            return SUCCESS, octets
        except ssl.SSLError, exception:
            if exception[0] == ssl.SSL_ERROR_WANT_READ:
                return WANT_READ, ""
            elif exception[0] == ssl.SSL_ERROR_WANT_WRITE:
                return WANT_WRITE, ""
            else:
                return ERROR, exception

    def sosend(self, octets):
        try:
            count = self.sock.write(octets)
            return SUCCESS, count
        except ssl.SSLError, exception:
            if exception[0] == ssl.SSL_ERROR_WANT_READ:
                return WANT_READ, 0
            elif exception[0] == ssl.SSL_ERROR_WANT_WRITE:
                return WANT_WRITE, 0
            else:
                return ERROR, exception
