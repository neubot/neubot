# http/client.py

#
# Copyright (c) 2010-2011, 2014
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

''' HTTP client '''

import collections

from neubot import utils
from neubot import utils_net

from ..net import Handler
from .message import HTTPMessage
from .stream import StreamHTTP, ERROR, nextstate

class ClientStream(StreamHTTP):

    ''' Specializes StreamHTTP and implements the client
        side of an HTTP channel '''

    def __init__(self, poller):
        StreamHTTP.__init__(self, poller)
        self._requests = collections.deque()

    def send_request(self, request, response=None):
        ''' Sends a request '''
        self._requests.append(request)
        if not response:
            response = HTTPMessage()
        request.response = response
        self.send_message(request)

    def got_response_line(self, protocol, code, reason):
        if self._requests:
            response = self._requests[0].response
            response.protocol = protocol
            response.code = code
            response.reason = reason
        else:
            self.close()

    def got_request_line(self, method, url, protocol):
        raise RuntimeError("Unexpected event")

    def got_header(self, key, value):
        if self._requests:
            response = self._requests[0].response
            response[key] = value
        else:
            self.close()

    def got_end_of_headers(self):
        if self._requests:
            request = self._requests[0]
            if not self.parent.got_response_headers(self, request,
                     request.response):
                return ERROR, 0
            return nextstate(request, request.response)
        else:
            return ERROR, 0

    def got_piece(self, piece):
        if self._requests:
            response = self._requests[0].response
            response.body.write(piece)
        else:
            self.close()

    def got_end_of_body(self):
        if self._requests:
            request = self._requests.popleft()
            utils.safe_seek(request.response.body, 0)
            request.response.prettyprintbody("<")
            self.parent.got_response(self, request, request.response)
            if (request["connection"] == "close" or
              request.response["connection"] == "close"):
                self.close()
        else:
            self.close()

class HTTPClient(Handler):
    ''' HTTP client '''

    def __init__(self, poller):
        Handler.__init__(self, poller)
        self.host_header = ""
        self.rtt = 0

    def connect(self, endpoint, count=1):
        self.host_header = utils_net.format_epnt(endpoint)
        Handler.connect(self, endpoint, count)

    def connection_made(self, sock, endpoint, rtt):
        if rtt:
            self.rtt = rtt
        stream = ClientStream(self.poller)
        stream.attach(self, sock, self.conf)
        self.connection_ready(stream)

    def connection_ready(self, stream):
        ''' Override this method in derived classes '''

    def got_response_headers(self, stream, request, response):
        ''' Invoked when we receive response headers '''
        return True

    def got_response(self, stream, request, response):
        ''' Override this method in derived classes '''
