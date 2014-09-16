# neubot/negotiate/module.py

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

''' Negotiate server module '''

class NegotiateServerModule(object):

    ''' Each test should implement this interface '''

    # The minimal collect echoes the request body
    def collect(self, stream, request_body):
        ''' Invoked at the end of the test, to collect data '''
        return request_body

    # Only speedtest reimplements this method
    def collect_legacy(self, stream, request_body, request):
        ''' Legacy interface to collect that also receives the
            request object: speedtest needs to inspect the Authorization
            header when the connecting client is pretty old '''
        return self.collect(stream, request_body)

    # The minimal unchoke returns the stream unique identifier only
    def unchoke(self, stream, request_body):
        ''' Invoked when a stream is authorized to take the test '''
        return { 'authorization': str(hash(stream)) }
