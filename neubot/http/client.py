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
import socket
import getopt
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.http.stream import StreamHTTP
from neubot.net.stream import StreamHandler
from neubot.options import OptionParser
from neubot.utils import file_length
from neubot.http.stream import ERROR
from neubot.http.utils import nextstate
from neubot.http.messages import Message
from neubot.net.poller import POLLER
from neubot.net.stream import MEASURER
from neubot.utils import safe_seek
from neubot.log import LOG


class ClientStream(StreamHTTP):

    """Specializes StreamHTTP and implements the client
       side of an HTTP channel."""

    def __init__(self, poller):
        StreamHTTP.__init__(self, poller)
        self.requests = collections.deque()

    def connection_ready(self):
        self.parent.connection_ready(self)

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
            safe_seek(request.response.body, 0)
            self.parent.got_response(self, request, request.response)
            if (request["connection"] == "close" or
              request.response["connection"] == "close"):
                self.close()
        else:
            self.close()


class ClientHTTP(StreamHandler):

    def connection_ready(self, stream):
        pass

    def got_response_headers(self, stream, request, response):
        return True

    def got_response(self, stream, request, response):
        pass

    def connection_made(self, sock):
        stream = ClientStream(self.poller)
        stream.attach(self, sock, self.conf)


# Unit test

USAGE = """Neubot http -- Test unit for the http client module

Usage: neubot http [-Vv] [-D macro[=value]] [-f file] [--help] uri ...

Options:
    -D macro[=value]   : Set the value of the macro `macro`.
    -f file            : Read options from file `file`.
    --help             : Print this help screen and exit.
    -V                 : Print version number and exit.
    -v                 : Run the program in verbose mode.

Macros (defaults in square brackets):
    method=method      : Select the method to use [GET]
    stdout             : Write output to stdout [no]

"""

VERSION = "Neubot 0.3.6\n"


class TestClient(ClientHTTP):

    def __init__(self, poller):
        ClientHTTP.__init__(self, poller)
        self.response = None
        self.request = None

    def set_request_response(self, request, response):
        self.response = response
        self.request = request

    def connection_ready(self, stream):
        stream.send_request(self.request, self.response)


def main(args):

    conf = OptionParser()
    conf.set_option("http", "method", "GET")
    conf.set_option("http", "stdout", "no")

    try:
        options, arguments = getopt.getopt(args[1:], "D:f:Vv", ["help"])
    except getopt.GetoptError:
        sys.stderr.write(USAGE)
        sys.exit(1)

    if len(arguments) == 0:
        sys.stderr.write(USAGE)
        sys.exit(1)

    for name, value in options:
        if name == "-D":
             conf.register_opt(value, "http")
             continue
        if name == "-f":
             conf.register_file(value)
             continue
        if name == "--help":
             sys.stdout.write(USAGE)
             sys.exit(0)
        if name == "-V":
             sys.stdout.write(VERSION)
             sys.exit(0)
        if name == "-v":
             LOG.verbose()
             continue

    conf.merge_files()
    conf.merge_environ()
    conf.merge_opts()

    method = conf.get_option("http", "method")
    stdout = conf.get_option_bool("http", "stdout")

    if not stdout:
        POLLER.sched(0.5, MEASURER.start)

    for uri in arguments:
        request = Message()
        request.compose(method=method, uri=uri, keepalive=False)
        response = Message()
        response.body = sys.stdout
        dictionary = {}
        if request.scheme == "https":
            dictionary["secure"] = True
        endpoint = (request.address, int(request.port))

        client = TestClient(POLLER)
        client.configure(dictionary)
        client.set_request_response(request, response)

        if method == "PUT":
            fpath = request.pathquery.split("/")[-1]
            if not os.path.exists(fpath):
                LOG.error("* Local file does not exist: %s" % fpath)
                sys.exit(1)
            request.body = open(fpath, "rb")
            del request["content-length"]
            request["content-length"] = str(file_length(request.body))
            request["content-type"] = "text/plain"

        if method == "GET" and not stdout:
            output = request.pathquery.split("/")[-1]
            if os.path.exists(output):
                LOG.error("* Local file already exists: %s" % output)
                sys.exit(1)
            response.body = open(output, "wb")

        MEASURER.connect(client, endpoint)

    POLLER.loop()
    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)
