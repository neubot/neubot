# neubot/http/client.py

#
# Copyright (c) 2010-2011 Simone Basso <bassosimone@gmail.com>,
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

''' HTTP client '''

# Will be replaced by neubot/http_clnt.py

import collections
import os.path
import sys
import logging

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.config import CONFIG
from neubot.http.stream import StreamHTTP
from neubot.net.stream import StreamHandler
from neubot.http.stream import ERROR
from neubot.http.stream import nextstate
from neubot.http.message import Message
from neubot.net.poller import POLLER
from neubot import utils
from neubot import utils_net
from neubot.main import common

class ClientStream(StreamHTTP):

    ''' Specializes StreamHTTP and implements the client
        side of an HTTP channel '''

    def __init__(self, poller):
        ''' Initialize client stream '''
        StreamHTTP.__init__(self, poller)
        self.requests = collections.deque()

    def send_request(self, request, response=None):
        ''' Sends a request '''
        self.requests.append(request)
        if not response:
            response = Message()
        request.response = response
        self.send_message(request)

    def got_response_line(self, protocol, code, reason):
        ''' Invoked when we receive the response line '''
        if self.requests:
            response = self.requests[0].response
            response.protocol = protocol
            response.code = code
            response.reason = reason
        else:
            self.close()

    def got_header(self, key, value):
        ''' Invoked when we receive an header '''
        if self.requests:
            response = self.requests[0].response
            response[key] = value
        else:
            self.close()

    def got_end_of_headers(self):
        ''' Invoked at the end of headers '''
        if self.requests:
            request = self.requests[0]
            if not self.parent.got_response_headers(self, request,
                                                request.response):
                return ERROR, 0
            return nextstate(request, request.response)
        else:
            return ERROR, 0

    def got_piece(self, piece):
        ''' Invoked when we receive a body piece '''
        if self.requests:
            response = self.requests[0].response
            response.body.write(piece)
        else:
            self.close()

    def got_end_of_body(self):
        ''' Invoked at the end of the body '''
        if self.requests:
            request = self.requests.popleft()
            utils.safe_seek(request.response.body, 0)
            request.response.prettyprintbody("<")
            self.parent.got_response(self, request, request.response)
            if (request["connection"] == "close" or
              request.response["connection"] == "close"):
                self.close()
        else:
            self.close()

class ClientHTTP(StreamHandler):

    ''' Manages one or more HTTP streams '''

    def __init__(self, poller):
        ''' Initialize the HTTP client '''
        StreamHandler.__init__(self, poller)
        self.host_header = ""
        self.rtt = 0

    def connect_uri(self, uri, count=1):
        ''' Connects to the given URI '''
        try:
            message = Message()
            message.compose(method="GET", uri=uri)
            if message.scheme == "https":
                self.conf["net.stream.secure"] = True
            endpoint = (message.address, int(message.port))
            self.host_header = utils_net.format_epnt(endpoint)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception, why:
            self.connection_failed(None, why)
        else:
            self.connect(endpoint, count)

    def connection_ready(self, stream):
        ''' Invoked when the connection is ready '''

    def got_response_headers(self, stream, request, response):
        ''' Invoked when we receive response headers '''
        return True

    def got_response(self, stream, request, response):
        ''' Invoked when we receive the response '''

    def connection_made(self, sock, endpoint, rtt):
        ''' Invoked when the connection is created '''
        if rtt:
            logging.debug("ClientHTTP: latency: %s", utils.time_formatter(rtt))
            self.rtt = rtt
        # XXX If we didn't connect via connect_uri()...
        if not self.host_header:
            self.host_header = utils_net.format_epnt(endpoint)
        stream = ClientStream(self.poller)
        stream.attach(self, sock, self.conf)
        self.connection_ready(stream)

class TestClient(ClientHTTP):

    ''' Test client for this module '''

    def connection_ready(self, stream):
        ''' Invoked when the connection is ready '''
        method = self.conf["http.client.method"]
        stdout = self.conf["http.client.stdout"]
        uri = self.conf["http.client.uri"]

        request = Message()
        if method == "PUT":
            fpath = uri.split("/")[-1]
            if not os.path.exists(fpath):
                logging.error("* Local file does not exist: %s", fpath)
                sys.exit(1)
            request.compose(method=method, uri=uri, keepalive=False,
              mimetype="text/plain", body=open(fpath, "rb"))
        else:
            request.compose(method=method, uri=uri, keepalive=False)

        response = Message()
        if method == "GET" and not stdout:
            fpath = uri.split("/")[-1]
            if os.path.exists(fpath):
                logging.error("* Local file already exists: %s", fpath)
                sys.exit(1)
            response.body = open(fpath, "wb")
        else:
            response.body = sys.stdout

        stream.send_request(request, response)

CONFIG.register_defaults({
    "http.client.class": "",
    "http.client.method": "GET",
    "http.client.stdout": False,
    "http.client.uri": "",
})

def main(args):

    ''' main() of this module '''

    CONFIG.register_descriptions({
        "http.client.class": "Specify alternate ClientHTTP-like class",
        "http.client.method": "Specify alternate HTTP method",
        "http.client.stdout": "Enable writing response to stdout",
        "http.client.uri": "Specify URI to download from/upload to",
    })

    common.main("http.client", "Simple Neubot HTTP client", args)
    conf = CONFIG.copy()

    if not conf["http.client.uri"]:
        sys.stdout.write("Please, specify URI via -D http.client.uri=URI\n")
        sys.exit(0)

    client = TestClient(POLLER)
    client.configure(conf)
    client.connect_uri(conf["http.client.uri"])

    POLLER.loop()
    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)
