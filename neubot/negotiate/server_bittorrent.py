# neubot/negotiate/server_bittorrent.py

#
# Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
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

''' BitTorrent negotiator '''

import hashlib

from neubot.negotiate.server import NegotiateServerModule
from neubot.database import table_bittorrent
from neubot.database import DATABASE
from neubot import privacy

class NegotiateServerBitTorrent(NegotiateServerModule):

    ''' Negotiator for BitTorrent '''

    def __init__(self):
        ''' Initialize BitTorrent negotiator '''
        NegotiateServerModule.__init__(self)
        self.peers = {}

    @staticmethod
    def _stream_to_ident(stream):
        ''' Stream to unique identifier '''
        return str(hash(stream))

    @staticmethod
    def _stream_to_sha1(stream):
        ''' Stream to SHA1 identifier '''
        sha1 = hashlib.new('sha1')
        sha1.update(str(hash(stream)))
        return sha1.digest()

    def unchoke(self, stream, request_body):
        ''' Invoked when we must unchoke a session '''
        sha1 = self._stream_to_sha1(stream)
        if sha1 not in self.peers:
            target_bytes = int(request_body['target_bytes'])
            if target_bytes < 0:
                raise ValueError('Invalid target_bytes')
            self.peers[sha1] = {'target_bytes': target_bytes}
            stream.atclose(self._update_peers)
            return {'authorization': self._stream_to_ident(stream)}
        else:
            raise RuntimeError('Multiple unchoke')

    def collect(self, stream, request_body):
        ''' Invoked when we must save the result of a session '''
        sha1 = self._stream_to_sha1(stream)
        if sha1 not in self.peers:
            raise RuntimeError('Not authorized to collect')
        else:

            # No more than one collect per session
            result = self.peers[sha1]
            del self.peers[sha1]

            #
            # Note that the following is not a bug: it's just that
            # the server saves results using the point of view of the
            # client, i.e. upload_speed _is_ client's upload speed.
            #
            request_body['timestamp'] = result['timestamp']
            request_body['upload_speed'] = result['upload_speed']

            if privacy.collect_allowed(request_body):
                table_bittorrent.insert(DATABASE.connection(), request_body)

            #
            # After we've saved the result into the dictionary we
            # can add extra information we would like to return to
            # the client.
            #
            request_body['target_bytes'] = result['target_bytes']
            return request_body

    # If collect is successful we should not have self.peers[sha1]
    def _update_peers(self, stream, ignored):
        ''' Invoked when a session has been closed '''
        sha1 = self._stream_to_sha1(stream)
        if sha1 in self.peers:
            del self.peers[sha1]

NEGOTIATE_SERVER_BITTORRENT = NegotiateServerBitTorrent()
