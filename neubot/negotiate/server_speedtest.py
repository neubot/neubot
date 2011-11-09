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

from neubot.negotiate.server import NegotiateServerModule
from neubot.database import table_speedtest
from neubot.database import DATABASE
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
            stream.atclose(self._update_clients)
            self.clients.add(ident)
            return {'authorization': ident}
        else:
            raise RuntimeError('Multiple unchoke')

    def collect(self, stream, request_body):
        ''' Invoked when we must save the result of a session '''
        ident = str(hash(stream))
        if ident not in self.clients:
            raise RuntimeError('Not authorized to collect')
        else:
            self.clients.remove(ident)
            if privacy.collect_allowed(request_body):
                table_speedtest.insert(DATABASE.connection(), request_body)
            return {}

    def _update_clients(self, stream, ignored):
        ''' Invoked when a session has been closed '''
        ident = str(hash(stream))
        if ident in self.clients:
            self.clients.remove(ident)

NEGOTIATE_SERVER_SPEEDTEST = NegotiateServerSpeedtest()
