# neubot/sslstream.py

#
# Copyright (c) 2010-2012 Simone Basso <bassosimone@gmail.com>,
#  NEXA Center for Internet & Society at Politecnico di Torino
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

''' Pollable SSL stream '''

# Python3-ready: yes

import logging
import ssl
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.pollable import Pollable
from neubot.pollable import SUCCESS
from neubot.pollable import WANT_READ
from neubot.pollable import WANT_WRITE
from neubot.poller import POLLER

class SSLWrapper(object):
    ''' Wrapper for an SSL socket '''

    #
    # The point of this class is to route differently soft errors (i.e. when
    # you can retry later) and hard errors.  A similar class exists for normal
    # sockets, and the overall result is that the PollableStream always deals
    # with the same (simple) socket interface.
    #

    def __init__(self, sock):
        self.sock = sock

    def close(self):
        ''' Wrapper for SSL_close() '''
        try:
            self.sock.close()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            logging.warning('sslstream: sock.close() failed', exc_info=1)

    def sorecv(self, maxlen):
        ''' Wrapper for SSL_read() '''
        try:
            return SUCCESS, self.sock.read(maxlen)
        except ssl.SSLError:
            exception = sys.exc_info()[1]
            if exception.args[0] == ssl.SSL_ERROR_WANT_READ:
                return WANT_READ, ''
            elif exception.args[0] == ssl.SSL_ERROR_WANT_WRITE:
                return WANT_WRITE, ''
            else:
                raise

    def sosend(self, octets):
        ''' Wrapper for SSL_write() '''
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

class Handshaker(Pollable):
    ''' A pollable SSL handshaker '''

    #
    # This class wraps around the real stream and just performs the SSL
    # handshake.  Once handshake is complete, the connection_ready() method
    # of the wrapped stream is invoked, and this class is destroyed.
    #

    def __init__(self, stream):
        Pollable.__init__(self)
        self.opaque = stream

    def fileno(self):
        return self.opaque.fileno()

    def handle_read(self):
        POLLER.unset_readable(self)
        self.handshake()

    def handle_write(self):
        POLLER.unset_writable(self)
        self.handshake()

    def handshake(self):
        ''' Async SSL handshake '''
        try:
            self.opaque.sock.sock.do_handshake()
        except ssl.SSLError:
            exception = sys.exc_info()[1]
            if exception.args[0] == ssl.SSL_ERROR_WANT_READ:
                POLLER.set_readable(self)
            elif exception.args[0] == ssl.SSL_ERROR_WANT_WRITE:
                POLLER.set_writable(self)
            else:
                raise
        else:
            stream = self.opaque
            self.opaque = None
            stream.atconnect.callback(stream)

    def handle_close(self):
        stream = self.opaque
        self.opaque = None
        stream.handle_close()

def initialise(stream, sock, sslcert):
    ''' Initialise SSL socket '''

    logging.debug('stream_ssl: initialise()')

    #
    # Do not use '' to indicate no certfile, because wrap_socket() only
    # recognizes None for that purpose.  Instead, the empty string is
    # taken as the path for the certificate and the call raises an error.
    #
    if not sslcert:
        server_side = False
        sslcert = None
    else:
        server_side = True

    stream.sock = SSLWrapper(ssl.SSLSocket(sock, do_handshake_on_connect=False,
                                   certfile=sslcert, server_side=server_side))

    handshaker = Handshaker(stream)
    handshaker.handshake()
