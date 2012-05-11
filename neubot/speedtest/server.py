# neubot/speedtest/server.py

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

''' Speedtest server '''

from neubot.utils_random import RandomBody
from neubot.http.message import Message
from neubot.http.server import ServerHTTP

from neubot.bytegen_speedtest import BytegenSpeedtest

TARGET = 5

class SpeedtestServer(ServerHTTP):

    ''' Server-side of the speedtest test '''

    # Adapted from neubot/negotiate/server.py
    def got_request_headers(self, stream, request):
        ''' Filter incoming HTTP requests '''
        isgood = (request.uri == '/speedtest/latency' or
                  request.uri == '/speedtest/download' or
                  request.uri == '/speedtest/upload')
        #
        # NOTE Ignore the request body.  First of all, we are
        # not interested in reading it, we just want to receive
        # it.  Moreover, reading it leads to framentation, as
        # we need to actually allocate and then free all those
        # bytes.  (This is true especially when testing with
        # fast Neubot clients.)  This fix brings the amount of
        # memory consumed by the server under control again.
        #
        request.body.write = lambda data: None
        return isgood

    @staticmethod
    def _parse_range(message):
        ''' Parse incoming range header '''
        first, last = message['range'].replace('bytes=', '').strip().split('-')
        first, last = int(first), int(last)
        if first < 0 or last < 0 or last < first:
            raise ValueError('Invalid range header')
        return first, last

    def process_request(self, stream, request):
        ''' Process incoming HTTP request '''

        # Just ignore the incoming body
        if request.uri in ('/speedtest/latency', '/speedtest/upload'):
            response = Message()
            response.compose(code='200', reason='Ok')
            stream.send_response(request, response)

        elif request.uri == '/speedtest/download':

            #
            # If range is not present send chunked
            # data for TARGET seconds.
            # This is version 2 of the speedtest.
            #
            if not request['range']:
                body = BytegenSpeedtest(TARGET)
                response = Message()
                response.compose(code='200', reason='Ok',
                  mimetype='application/octet-stream',
                  chunked=body)
                stream.send_response(request, response)
                return

            # Honour range
            first, last = self._parse_range(request)
            response = Message()
            response.compose(code='200', reason='Ok',
              body=RandomBody(last - first + 1),
              mimetype='application/octet-stream')
            stream.send_response(request, response)

        # For robustness
        else:
            raise RuntimeError('Unexpected URI')

# No poller, so it cannot be used directly
SPEEDTEST_SERVER = SpeedtestServer(None)
