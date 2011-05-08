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

import StringIO
import os.path

from neubot.config import CONFIG
from neubot.arcfour import RandomBody
from neubot.http.message import Message
from neubot.http.server import ServerHTTP
from neubot.http import utils as http_utils
from neubot.log import LOG
from neubot.net.poller import POLLER

from neubot import utils
from neubot import boot
from neubot import system

class DeprecatedServerTest(object):

    def do_download(self, stream, request, self_config_path):
        response = Message()

        try:
            body = open(self_config_path, "rb")
        except (IOError, OSError):
            LOG.exception()
            response.compose(code="500", reason="Internal Server Error")
            stream.send_response(request, response)
            return

        if request["range"]:
            total = utils.file_length(body)

            try:
                first, last = http_utils.parse_range(request)
            except ValueError:
                LOG.exception()
                response.compose(code="400", reason="Bad Request")
                stream.send_response(request, response)
                return

            # XXX read() assumes there is enough core
            body.seek(first)
            partial = body.read(last - first + 1)
            response["content-range"] = "bytes %d-%d/%d" % (first, last, total)
            body = StringIO.StringIO(partial)
            code, reason = "206", "Partial Content"

        else:
            code, reason = "200", "Ok"

        response.compose(code=code, reason=reason, body=body,
                mimetype="application/octet-stream")
        stream.send_response(request, response)

FAKE_NEGOTIATION = '''\
<SpeedtestNegotiate_Response>
 <unchoked>True</unchoked>
</SpeedtestNegotiate_Response>
'''

class ServerTest(ServerHTTP):

    def __init__(self, poller):
        ServerHTTP.__init__(self, poller)
        self.old_server = DeprecatedServerTest()

    def configure(self, conf, measurer=None):
        conf["http.server.rootdir"] = ""
        ServerHTTP.configure(self, conf, measurer)

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
            fpath = self.conf.get("speedtest.server.path",
              "/var/neubot/large_file.bin")
            if os.path.isfile(fpath):
                self.old_server.do_download(stream, request, fpath)
            else:
                first, last = http_utils.parse_range(request)
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
                body = StringIO.StringIO(FAKE_NEGOTIATION)
            response.compose(code="200", reason="Ok", body=body)
            stream.send_response(request, response)

        else:
            response = Message()
            stringio = StringIO.StringIO("500 Internal Server Error")
            response.compose(code="500", reason="Internal Server Error",
                             body=stringio, mimetype="text/plain")
            stream.send_response(request, response)

CONFIG.register_defaults({
    "speedtest.server.address": "0.0.0.0",
    "speedtest.server.daemonize": True,
    "speedtest.server.path": "/var/neubot/large_file.bin",
    "speedtest.server.port": "80",
})
CONFIG.register_descriptions({
    "speedtest.server.path": "Read response pieces from this large file",
})

def main(args):
    boot.common("speedtest.server", "Speedtest Test Server", args)

    conf = CONFIG.copy()

    server = ServerTest(POLLER)
    server.configure(conf)
    server.listen((conf["speedtest.server.address"],
                  conf["speedtest.server.port"]))

    if conf["speedtest.server.daemonize"]:
        system.change_dir()
        system.go_background()
        LOG.redirect()

    system.drop_privileges()
    POLLER.loop()
