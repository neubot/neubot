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

import logging
import hashlib

from neubot.negotiate.server import NegotiateServerModule
from neubot.backend import BACKEND
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
            test_version = int(request_body.get('test_version', 1))
            if test_version < 1 or test_version > 2:
                raise ValueError('Invalid test_version')
            target_bytes = int(request_body.get('target_bytes', 0))
            if target_bytes < 0:
                raise ValueError('Invalid target_bytes')
            # Create record for this stream
            self.peers[sha1] = {'target_bytes': target_bytes,
                                'test_version': test_version}
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

            # Note: no more than one collect per session
            result = self.peers[sha1]
            del self.peers[sha1]

            #
            # Backward compatibility: the variable name changed from
            # can_share to can_publish after Neubot 0.4.5
            #
            if 'privacy_can_share' in request_body:
                request_body['privacy_can_publish'] = request_body[
                  'privacy_can_share']
                del request_body['privacy_can_share']

            #
            # Note that the following is not a bug: it's just that
            # the server saves results using the point of view of the
            # client, i.e. upload_speed _is_ client's upload speed.
            #
            request_body['timestamp'] = result['timestamp']
            request_body['upload_speed'] = result['upload_speed']

            if privacy.collect_allowed(request_body):
                BACKEND.bittorrent_store(request_body)
            else:
                logging.warning('* bad privacy settings: %s', str(stream))

            #
            # After we've saved the result into the dictionary we
            # can add extra information we would like to return to
            # the client.
            #
            request_body['target_bytes'] = result['target_bytes']
            return request_body

    # Note: if collect is successful self.peers[sha1] doesn't exist
    def _update_peers(self, stream, ignored):
        ''' Invoked when a session has been closed '''
        sha1 = self._stream_to_sha1(stream)
        if sha1 in self.peers:
            del self.peers[sha1]

NEGOTIATE_SERVER_BITTORRENT = NegotiateServerBitTorrent()
