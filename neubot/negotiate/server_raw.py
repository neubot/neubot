# neubot/negotiate/server_raw.py

#
# Copyright (c) 2011-2012
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

'''
 Server-side raw-test negotiate and collect.
'''

# Adapted from neubot/negotiate/server_bittorrent.py
# To be renamed neubot/raw_negotiate_srvr.py

import logging
import hashlib

from neubot.negotiate.server import NegotiateServerModule
from neubot.backend import BACKEND

class NegotiateServerRaw(NegotiateServerModule):

    ''' Negotiator for RAW test '''

    def __init__(self):
        NegotiateServerModule.__init__(self)
        self.peers = {}

    @staticmethod
    def _stream_to_sha512(stream):
        ''' Stream to SHA512 identifier '''
        sha512 = hashlib.new('sha512')
        sha512.update(str(hash(stream)))
        return sha512.digest()

    def unchoke(self, stream, request_body):
        ''' Invoked when we must unchoke a session '''
        sha512 = self._stream_to_sha512(stream)
        if sha512 not in self.peers:
            # Create record for this stream
            self.peers[sha512] = {}
            logging.debug('negotiate_server_raw: add sha512: %s',
              sha512.encode('hex'))
            stream.atclose(self._update_peers)
            return {'authorization': sha512.encode('hex'), 'port': 12345}
        else:
            raise RuntimeError('negotiate_server_raw: multiple unchoke')

    def collect(self, stream, request_body):
        ''' Invoked when we must save the result of a session '''
        sha512 = self._stream_to_sha512(stream)
        if sha512 not in self.peers:
            raise RuntimeError('negotiate_server_raw: not authorized')
        else:
            result = self.peers[sha512]
            # Note: no more than one collect per session
            del self.peers[sha512]
            logging.debug('negotiate_server_raw: del sha512 OK: %s',
              sha512.encode('hex'))
            complete_result = {'client': request_body, 'server': result}
            BACKEND.store_raw(complete_result)
            return result

    def _update_peers(self, stream, ignored):
        ''' Invoked when a session has been closed '''
        # Note: if collect is successful self.peers[sha512] doesn't exist
        sha512 = self._stream_to_sha512(stream)
        if sha512 in self.peers:
            logging.warning('negotiate_server_raw: del sha512 unexpected: %s',
              sha512.encode('hex'))
            del self.peers[sha512]

NEGOTIATE_SERVER_RAW = NegotiateServerRaw()
