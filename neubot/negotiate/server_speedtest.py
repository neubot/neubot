# neubot/negotiate/server_speedtest.py

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

''' Speedtest negotiator '''

import logging

from neubot.negotiate.server import NegotiateServerModule
from neubot.backend import BACKEND

from neubot import privacy

class NegotiateServerSpeedtest(NegotiateServerModule):

    ''' Negotiator for Speedtest '''

    def __init__(self):
        ''' Initialize Speedtest negotiator '''
        NegotiateServerModule.__init__(self)
        self.clients = set()

    def unchoke(self, stream, request_body):
        ''' Invoked when we must unchoke a session '''
        ident = str(hash(stream))
        if ident not in self.clients:
            # Create record for this session
            self.clients.add(ident)
            stream.atclose(self._update_clients)
            return {'authorization': ident}
        else:
            raise RuntimeError('Multiple unchoke')

    def collect_legacy(self, stream, request_body, request):
        ''' Invoked when we must save the result of a session '''
        ident = str(hash(stream))
        if ident not in self.clients:
            #
            # Before Neubot 0.4.2 we were using multiple connections
            # for speedtest, which were used both for testing and for
            # negotiating/collecting.  Sometimes the connection used
            # to collect is not the one used to negotiate: the code
            # uses the one that terminates the upload first.
            # When this happens we inspect the Authorization header
            # before deciding the collect request is an abuse.
            #
            authorization = request['Authorization']
            if authorization not in self.clients:
                raise RuntimeError('Not authorized to collect')
            else:
                logging.warning('speedtest: working around multiple conns '
                                'issue')
                ident = authorization

        # Note: no more than one collect per session
        self.clients.remove(ident)

        #
        # Backward compatibility: the variable name changed from
        # can_share to can_publish after Neubot 0.4.5
        #
        if 'privacy_can_share' in request_body:
            request_body['privacy_can_publish'] = request_body[
              'privacy_can_share']
            del request_body['privacy_can_share']

        if privacy.collect_allowed(request_body):
            BACKEND.speedtest_store(request_body)
        else:
            logging.warning('* bad privacy settings: %s', str(stream))

        return {}

    # Note: if collect is successful ident is not in self.clients
    def _update_clients(self, stream, ignored):
        ''' Invoked when a session has been closed '''
        ident = str(hash(stream))
        if ident in self.clients:
            self.clients.remove(ident)

NEGOTIATE_SERVER_SPEEDTEST = NegotiateServerSpeedtest()
