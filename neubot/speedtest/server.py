# neubot/speedtest/server.py

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

import os.path

from neubot.config import CONFIG
from neubot.blocks import RandomBody
from neubot.http.message import Message
from neubot.http.server import ServerHTTP
from neubot.log import LOG
from neubot.net.poller import POLLER

from neubot import utils
from neubot.main import common
from neubot import system

FAKE_NEGOTIATION = '''\
<SpeedtestNegotiate_Response>
 <unchoked>True</unchoked>
</SpeedtestNegotiate_Response>
'''

#
# Parse 'range:' header
# Here we don't care of Exceptions as long as these exceptions
# are ValueErrors, because the caller expects this function to
# succed OR to raise ValueError.
#

def parse_range(message):
    vector = message["range"].replace("bytes=", "").strip().split("-")
    first, last = map(int, vector)
    if first < 0 or last < 0 or last < first:
        raise ValueError("Cannot parse range header")
    return first, last

class ServerTest(ServerHTTP):

    def configure(self, conf):
        conf["http.server.rootdir"] = ""
        ServerHTTP.configure(self, conf)

    def got_request_headers(self, stream, request):
        if request.uri == "/speedtest/upload":
            request.body.write = lambda octets: None
        return True

    def process_request(self, stream, request):

        if request.uri in ("/speedtest/latency", "/speedtest/upload"):
            response = Message()
            response.compose(code="200", reason="Ok")
            stream.send_response(request, response)

        elif request.uri == "/speedtest/download":
            first, last = parse_range(request)
            response = Message()
            response.compose(code="200", reason="Ok",
              body=RandomBody(last - first + 1),
              mimetype="application/octet-stream")
            stream.send_response(request, response)

        # Fake for testing purpose only
        elif request.uri in ("/speedtest/negotiate", "/speedtest/collect"):
            response = Message()
            body = None
            if request.uri == "/speedtest/negotiate":
                body = FAKE_NEGOTIATION
            response.compose(code="200", reason="Ok", body=body)
            stream.send_response(request, response)

        else:
            response = Message()
            body = "500 Internal Server Error"
            response.compose(code="500", reason="Internal Server Error",
                             body=body, mimetype="text/plain")
            stream.send_response(request, response)

CONFIG.register_defaults({
    "speedtest.server.address": "0.0.0.0",
    "speedtest.server.daemonize": True,
    "speedtest.server.port": "80",
})

def main(args):

    common.main("speedtest.server", "Speedtest Test Server", args)

    conf = CONFIG.copy()

    server = ServerTest(POLLER)
    server.configure(conf)
    server.listen((conf["speedtest.server.address"],
                  conf["speedtest.server.port"]))

    if conf["speedtest.server.daemonize"]:
        system.change_dir()
        system.go_background()
        LOG.redirect()

    system.drop_privileges(LOG.error)
    POLLER.loop()
