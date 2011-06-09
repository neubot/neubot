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

import collections
import os.path
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.config import CONFIG
from neubot.http.stream import StreamHTTP
from neubot.net.stream import StreamHandler
from neubot.http.stream import ERROR
from neubot.http.utils import nextstate
from neubot.http.utils import prettyprintbody
from neubot.http.message import Message
from neubot.net.poller import POLLER
from neubot.net.measurer import MEASURER
from neubot.log import LOG
from neubot import utils
from neubot import boot

class ClientStream(StreamHTTP):

    """Specializes StreamHTTP and implements the client
       side of an HTTP channel."""

    def __init__(self, poller):
        StreamHTTP.__init__(self, poller)
        self.requests = collections.deque()

    def send_request(self, request, response=None):
        self.requests.append(request)
        if not response:
            response = Message()
        request.response = response
        self.send_message(request)

    def got_response_line(self, protocol, code, reason):
        if self.requests:
            response = self.requests[0].response
            response.protocol = protocol
            response.code = code
            response.reason = reason
        else:
            self.close()

    def got_header(self, key, value):
        if self.requests:
            response = self.requests[0].response
            response[key] = value
        else:
            self.close()

    def got_end_of_headers(self):
        if self.requests:
            request = self.requests[0]
            if not self.parent.got_response_headers(self, request,
                                                request.response):
                return ERROR, 0
            return nextstate(request, request.response)
        else:
            return ERROR, 0

    def got_piece(self, piece):
        if self.requests:
            response = self.requests[0].response
            response.body.write(piece)
        else:
            self.close()

    def got_end_of_body(self):
        if self.requests:
            request = self.requests.popleft()
            utils.safe_seek(request.response.body, 0)
            prettyprintbody(request.response, "<")
            self.parent.got_response(self, request, request.response)
            if (request["connection"] == "close" or
              request.response["connection"] == "close"):
                self.close()
        else:
            self.close()

class ClientHTTP(StreamHandler):

    def connect_uri(self, uri, count=1):
        try:
            m = Message()
            m.compose(method="GET", uri=uri)
            if m.scheme == "https":
                self.conf["net.stream.secure"] = True
            endpoint = (m.address, int(m.port))
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception, e:
            self.connection_failed(None, e)
        else:
            self.connect(endpoint, count)

    def connection_ready(self, stream):
        pass

    def got_response_headers(self, stream, request, response):
        return True

    def got_response(self, stream, request, response):
        pass

    def connection_made(self, sock, rtt=0):
        stream = ClientStream(self.poller)
        stream.attach(self, sock, self.conf, self.measurer)
        self.connection_ready(stream)

class TestClient(ClientHTTP):

    def connection_ready(self, stream):
        method = self.conf["http.client.method"]
        stdout = self.conf["http.client.stdout"]
        uri = self.conf["http.client.uri"]

        request = Message()
        if method == "PUT":
            fpath = uri.split("/")[-1]
            if not os.path.exists(fpath):
                LOG.error("* Local file does not exist: %s" % fpath)
                sys.exit(1)
            request.compose(method=method, uri=uri, keepalive=False,
              mimetype="text/plain", body=open(fpath, "rb"))
        else:
            request.compose(method=method, uri=uri, keepalive=False)

        response = Message()
        if method == "GET" and not stdout:
            fpath = uri.split("/")[-1]
            if os.path.exists(fpath):
                LOG.error("* Local file already exists: %s" % fpath)
                sys.exit(1)
            response.body = open(fpath, "wb")
        else:
            response.body = sys.stdout

        stream.send_request(request, response)

def main(args):

    CONFIG.register_defaults({
        "http.client.class": "",
        "http.client.method": "GET",
        "http.client.stats": True,
        "http.client.stdout": False,
        "http.client.uri": "",
    })
    CONFIG.register_descriptions({
        "http.client.class": "Specify alternate ClientHTTP-like class",
        "http.client.method": "Specify alternate HTTP method",
        "http.client.stats": "Enable printing download stats on stdout",
        "http.client.stdout": "Enable writing response to stdout",
        "http.client.uri": "Specify URI to download from/upload to",
    })

    boot.common("http.client", "Simple Neubot HTTP client", args)
    conf = CONFIG.copy()

    if conf["http.client.stats"]:
        POLLER.sched(0.5, MEASURER.start)

    make_client = TestClient
    if conf["http.client.class"]:
        make_client = utils.import_class(conf["http.client.class"])

    if not conf["http.client.uri"]:
        sys.stdout.write("Please, specify URI via -D http.client.uri=URI\n")
        sys.exit(0)

    client = make_client(POLLER)
    client.configure(conf, MEASURER)
    client.connect_uri(conf["http.client.uri"])

    POLLER.loop()
    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)
