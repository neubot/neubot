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

''' HTTP server '''

import StringIO
import mimetypes
import os.path
import sys
import time
import logging

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.config import CONFIG
from neubot.http.stream import ERROR
from neubot.http.message import Message
from neubot.http.ssi import ssi_replace
from neubot.http.stream import nextstate
from neubot.http.stream import StreamHTTP
from neubot.log import LOG
from neubot.net.stream import StreamHandler
from neubot.net.poller import POLLER

from neubot.main import common

from neubot import utils
from neubot import utils_path
from neubot import utils_net

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

    ''' Specializes StreamHTTP to implement the server-side
        of an HTTP channel '''

    def __init__(self, poller):
        ''' Initialize '''
        StreamHTTP.__init__(self, poller)
        self.response_rewriter = None
        self.request = None

    def got_request_line(self, method, uri, protocol):
        ''' Invoked when we get a request line '''
        self.request = Message(method=method, uri=uri, protocol=protocol)

    def got_header(self, key, value):
        ''' Invoked when we get an header '''
        if self.request:
            self.request[key] = value
        else:
            self.close()

    def got_end_of_headers(self):
        ''' Invoked at the end of headers '''
        if self.request:
            if not self.parent.got_request_headers(self, self.request):
                return ERROR, 0
            return nextstate(self.request)
        else:
            return ERROR, 0

    def got_piece(self, piece):
        ''' Invoked when we read a piece of the body '''
        if self.request:
            self.request.body.write(piece)
        else:
            self.close()

    def got_end_of_body(self):
        ''' Invoked at the end of the body '''
        if self.request:
            utils.safe_seek(self.request.body, 0)
            self.request.prettyprintbody("<")
            self.parent.got_request(self, self.request)
            self.request = None
        else:
            self.close()

    def send_response(self, request, response):
        ''' Send a response to the client '''

        if self.response_rewriter:
            self.response_rewriter(request, response)

        if request['connection'] == 'close' or request.protocol == 'HTTP/1.0':
            del response['connection']
            response['connection'] = 'close'

        self.send_message(response)

        if response['connection'] == 'close':
            self.close()

        address = self.peername[0]
        now = time.gmtime()
        timestring = "%02d/%s/%04d:%02d:%02d:%02d -0000" % (now.tm_mday,
          MONTH[now.tm_mon], now.tm_year, now.tm_hour, now.tm_min, now.tm_sec)
        requestline = request.requestline
        statuscode = response.code

        nbytes = "-"
        if response["content-length"]:
            nbytes = response["content-length"]
            if nbytes == "0":
                nbytes = "-"

        LOG.log("ACCESS",
                "%s - - [%s] \"%s\" %s %s",
                (address, timestring, requestline, statuscode, nbytes),
                None)

class ServerHTTP(StreamHandler):

    ''' Manages many HTTP connections '''

    def __init__(self, poller):
        ''' Initialize the HTTP server '''
        StreamHandler.__init__(self, poller)
        self._ssl_ports = set()
        self.childs = {}

    def bind_failed(self, epnt):
        ''' Invoked when we cannot bind a socket '''
        if self.conf.get("http.server.bind_or_die", False):
            sys.exit(1)

    def register_child(self, child, prefix):
        ''' Register a child server object '''
        self.childs[prefix] = child
        child.child = self

    def register_ssl_port(self, port):
        ''' Register a port where we should speak SSL '''
        self._ssl_ports.add(port)

    def got_request_headers(self, stream, request):
        ''' Invoked when we got request headers '''
        if self.childs:
            for prefix, child in self.childs.items():
                if request.uri.startswith(prefix):
                    try:
                        return child.got_request_headers(stream, request)
                    except (KeyboardInterrupt, SystemExit):
                        raise
                    except:
                        self._on_internal_error(stream, request)
                        return False
        return True

    def process_request(self, stream, request):
        ''' Process a request and generate the response '''
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
            response.compose_redirect(stream, "/api/index")
            stream.send_response(request, response)
            return

        if '?' in request.uri:
            request_uri = request.uri.split('?')[0]
        else:
            request_uri = request.uri

        fullpath = utils_path.append(rootdir, request_uri, True)
        if not fullpath:
            response.compose(code="403", reason="Forbidden",
                             body="403 Forbidden")
            stream.send_response(request, response)
            return

        try:
            filep = open(fullpath, "rb")
        except (IOError, OSError):
            logging.error("HTTP: Not Found: %s (WWWDIR: %s)",
                          fullpath, rootdir)
            response.compose(code="404", reason="Not Found",
                             body="404 Not Found")
            stream.send_response(request, response)
            return

        if self.conf.get("http.server.mime", True):
            mimetype, encoding = mimetypes.guess_type(fullpath)

            # Do not attempt SSI if the resource is, say, gzipped
            if not encoding:
                if mimetype == "text/html":
                    ssi = self.conf.get("http.server.ssi", False)
                    if ssi:
                        body = ssi_replace(rootdir, filep)
                        filep = StringIO.StringIO(body)

                #XXX Do we need to enforce the charset?
                if mimetype in ("text/html", "application/x-javascript"):
                    mimetype += "; charset=UTF-8"
            else:
                response["content-encoding"] = encoding

        else:
            mimetype = "text/plain"

        response.compose(code="200", reason="Ok", body=filep,
                         mimetype=mimetype)
        if request.method == "HEAD":
            utils.safe_seek(filep, 0, os.SEEK_END)
        stream.send_response(request, response)

    def got_request(self, stream, request):
        ''' Invoked when we got a request '''
        try:
            self.process_request(stream, request)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self._on_internal_error(stream, request)

    def _on_internal_error(self, stream, request):
        ''' Generate 500 Internal Server Error page '''
        logging.error('Internal error while serving response', exc_info=1)
        response = Message()
        response.compose(code="500", reason="Internal Server Error",
                         body="500 Internal Server Error", keepalive=0)
        stream.send_response(request, response)
        stream.close()

    def connection_made(self, sock, endpoint, rtt):
        ''' Invoked when the connection is made '''
        stream = ServerStream(self.poller)
        nconf = self.conf.copy()

        #
        # Setup SSL if needed.
        # XXX The private key and public certificate file is
        # hardcoded and must be readable by the user that owns
        # this process for SSL to work.  We can live with the
        # former issue but the latter belongs clearly to the
        # not-so-good dept.  (Even if loading a copy of the
        # private key at startup and then keeping it in memory
        # is dangerous as well.  Yes an attacker cannot read
        # the file but she can read the process memory and
        # find the private key without too much effort.)
        # Maybe radical privilege separation is the answer
        # here, but I'm not sure: I need to study more.
        #
        port = utils_net.getsockname(sock)[1]
        if port in self._ssl_ports:
            nconf["net.stream.certfile"] = "/etc/neubot/cert.pem"
            nconf["net.stream.secure"] = True
            nconf["net.stream.server_side"] = True

        stream.attach(self, sock, nconf)
        self.connection_ready(stream)

    def connection_ready(self, stream):
        ''' Invoked when the connection is ready '''

    def accept_failed(self, listener, exception):
        ''' Print a warning if accept() fails (often due to SSL) '''
        logging.warning("ServerHTTP: accept() failed: %s", str(exception))

HTTP_SERVER = ServerHTTP(POLLER)

CONFIG.register_defaults({
    "http.server.address": "",
    "http.server.class": "",
    "http.server.mime": True,
    "http.server.ports": "8080,",
    "http.server.rootdir": "",
    "http.server.ssi": False,
})

def main(args):

    ''' main() function of this module '''

    CONFIG.register_descriptions({
        "http.server.address": "Address to listen to",
        "http.server.class": "Use alternate ServerHTTP-like class",
        "http.server.mime": "Enable code that guess mime types",
        "http.server.ports": "List of ports to listen to",
        "http.server.rootdir": "Root directory for static pages",
        "http.server.ssi": "Enable server-side includes",
    })

    common.main("http.server", "Neubot simple HTTP server", args)
    conf = CONFIG.copy()

    HTTP_SERVER.configure(conf)

    if conf["http.server.rootdir"] == ".":
        conf["http.server.rootdir"] = os.path.abspath(".")

    for port in conf["http.server.ports"].split(","):
        if port:
            HTTP_SERVER.listen((conf["http.server.address"], int(port)))

    POLLER.loop()

if __name__ == "__main__":
    main(sys.argv)
