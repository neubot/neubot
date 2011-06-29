# neubot/http/server.py

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
import mimetypes
import sys
import os.path
import time

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.config import CONFIG
from neubot.http.stream import ERROR
from neubot.http.message import Message
from neubot.http.ssi import ssi_replace
from neubot.http.utils import nextstate
from neubot.http.utils import prettyprintbody
from neubot.http.stream import StreamHTTP
from neubot.net.stream import StreamHandler
from neubot.log import LOG
from neubot.net.poller import POLLER
from neubot import utils
from neubot import boot

#
# 3-letter abbreviation of month names.
# We use our abbreviation because we don't want the
# month name to depend on the locale.
# Note that Python tm.tm_mon is in range [1,12].
#
MONTH = [
    "", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug",
    "Sep", "Oct", "Nov", "Dec",
]

class ServerStream(StreamHTTP):

    def __init__(self, poller):
        StreamHTTP.__init__(self, poller)
        self.request = None

    def got_request_line(self, method, uri, protocol):
        self.request = Message(method=method, uri=uri, protocol=protocol)

    def got_header(self, key, value):
        if self.request:
            self.request[key] = value
        else:
            self.close()

    def got_end_of_headers(self):
        if self.request:
            if not self.parent.got_request_headers(self, self.request):
                return ERROR, 0
            return nextstate(self.request)
        else:
            return ERROR, 0

    def got_piece(self, piece):
        if self.request:
            self.request.body.write(piece)
        else:
            self.close()

    def got_end_of_body(self):
        if self.request:
            utils.safe_seek(self.request.body, 0)
            prettyprintbody(self.request, "<")
            self.parent.got_request(self, self.request)
            self.request = None
        else:
            self.close()

    def send_response(self, request, response):
        self.send_message(response)

        address = self.peername[0]
        now = time.gmtime()
        timestring = "%02d/%s/%04d:%02d:%02d:%02d -0000" % (now.tm_mday,
          MONTH[now.tm_mon], now.tm_year, now.tm_hour, now.tm_min, now.tm_sec)
        requestline = " ".join([request.method, request.uri, request.protocol])
        statuscode = response.code

        nbytes = "-"
        if response["content-length"]:
            nbytes = response["content-length"]
            if nbytes == "0":
                nbytes = "-"

        LOG.log_access("%s - - [%s] \"%s\" %s %s" % (address, timestring,
                                                     requestline, statuscode,
                                                     nbytes))

REDIRECT = """
<HTML>
 <HEAD>
  <TITLE>Moved permanently</TITLE>
 </HEAD>
 <BODY>
  Moved permanently to <A HREF="/index.html">index.html</A>.
 </BODY>
</HTML>
"""

class ServerHTTP(StreamHandler):

    def __init__(self, poller):
        StreamHandler.__init__(self, poller)
        self.childs = {}

    def bind_failed(self, listener, exception):
        if self.conf.get("http.server.bind_or_die", False):
            sys.exit(1)

    def register_child(self, child, prefix):
        self.childs[prefix] = child
        child.child = self

    def got_request_headers(self, stream, request):
        if self.childs:
            for prefix, child in self.childs.items():
                if request.uri.startswith(prefix):
                    return child.got_request_headers(stream, request)
        return True

    def process_request(self, stream, request):
        response = Message()

        if not request.uri.startswith("/"):
            response.compose(code="403", reason="Forbidden",
                             body="403 Forbidden")
            stream.send_response(request, response)
            return

        for prefix, child in self.childs.items():
            if request.uri.startswith(prefix):
                child.process_request(stream, request)
                return

        rootdir = self.conf.get("http.server.rootdir", "")
        if not rootdir:
            response.compose(code="403", reason="Forbidden",
                             body="403 Forbidden")
            stream.send_response(request, response)
            return

        if request.uri == "/":
            response.compose(code="301", reason="Moved Permanently",
              body=REDIRECT, mimetype="text/html; charset=UTF-8")
            #XXX With IPv6 we need to enclose address in square braces
            response["location"] = "http://%s:%s/index.html" % stream.myname
            stream.send_response(request, response)
            return

        # Paranoid mode: ON
        rootdir = utils.asciiify(rootdir)
        uripath = utils.asciiify(request.uri)
        fullpath = os.path.normpath(rootdir + uripath)
        fullpath = utils.asciiify(fullpath)

        if not fullpath.startswith(rootdir):
            response.compose(code="403", reason="Forbidden",
                             body="403 Forbidden")
            stream.send_response(request, response)
            return

        try:
            fp = open(fullpath, "rb")
        except (IOError, OSError):
            response.compose(code="404", reason="Not Found",
                             body="404 Not Found")
            stream.send_response(request, response)
            return

        if self.conf.get("http.server.mime", True):
            mimetype, encoding = mimetypes.guess_type(fullpath)

            if mimetype == "text/html":
                ssi = self.conf.get("http.server.ssi", False)
                if ssi:
                    body = ssi_replace(rootdir, fp)
                    fp = StringIO.StringIO(body)

            if encoding:
                mimetype = "; charset=".join((mimetype, encoding))
        else:
            mimetype = "text/plain"

        response.compose(code="200", reason="Ok", body=fp,
                         mimetype=mimetype)
        if request.method == "HEAD":
            utils.safe_seek(fp, 0, os.SEEK_END)
        stream.send_response(request, response)

    def got_request(self, stream, request):
        try:
            self.process_request(stream, request)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            LOG.exception()
            response = Message()
            response.compose(code="500", reason="Internal Server Error",
                             body="500 Internal Server Error", keepalive=0)
            stream.send_response(request, response)
            stream.close()

    def connection_made(self, sock, rtt=0):
        stream = ServerStream(self.poller)
        stream.attach(self, sock, self.conf)
        self.connection_ready(stream)

    def connection_ready(self, stream):
        pass

HTTP_SERVER = ServerHTTP(POLLER)

CONFIG.register_defaults({
    "http.server.address": "0.0.0.0",
    "http.server.class": "",
    "http.server.mime": True,
    "http.server.ports": "8080,",
    "http.server.rootdir": "",
    "http.server.ssi": False,
})

def main(args):
    CONFIG.register_descriptions({
        "http.server.address": "Address to listen to",
        "http.server.class": "Use alternate ServerHTTP-like class",
        "http.server.mime": "Enable code that guess mime types",
        "http.server.ports": "List of ports to listen to",
        "http.server.rootdir": "Root directory for static pages",
        "http.server.ssi": "Enable server-side includes",
    })

    boot.common("http.server", "Neubot simple HTTP server", args)
    conf = CONFIG.copy()

    if conf["http.server.class"]:
        make_child = utils.import_class(conf["http.server.class"])
        server = make_child(POLLER)
    else:
        server = HTTP_SERVER

    server.configure(conf)

    if conf["http.server.rootdir"] == ".":
        conf["http.server.rootdir"] = os.path.abspath(".")

    for port in conf["http.server.ports"].split(","):
        if port:
            server.listen((conf["http.server.address"], int(port)))

    POLLER.loop()

if __name__ == "__main__":
    main(sys.argv)
