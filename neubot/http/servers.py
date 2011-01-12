# neubot/http/servers.py

#
# Copyright (c) 2010 Simone Basso <bassosimone@gmail.com>,
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

#
# HTTP server
#

if __name__ == "__main__":
    from sys import path
    path.insert(0, ".")

from neubot.http.handlers import ERROR
from neubot.http.handlers import BOUNDED
from neubot.http.handlers import CHUNK_LENGTH
from neubot.http.handlers import FIRSTLINE
from neubot.http.handlers import Handler
from neubot.http.handlers import Receiver
from neubot.http.messages import Message
from neubot.http.messages import compose
from neubot.http.utils import nextstate
from neubot.http.utils import prettyprint
from sys import stdin, stdout, stderr
from neubot.net.listeners import listen
from neubot.utils import fixkwargs
from neubot import version as VERSION
from neubot.utils import safe_seek
from neubot.net.pollers import loop
from types import StringType
from getopt import GetoptError
from getopt import getopt
from os import SEEK_END
from os import sep as SEP
from time import gmtime
from neubot import log
from sys import argv
from sys import exit
from os import getcwd

from socket import AF_INET

#
# Simple model for client connection that serves
# up to seven keepalive requests
#

# 3-letter abbreviation of month names, note that
# python tm.tm_mon is in range [1,12]
# we use our abbreviation because we don't want the
# month name to depend on the locale
MONTH = [
    "", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug",
    "Sep", "Oct", "Nov", "Dec",
]

class SimpleConnection(Receiver):
    def __init__(self):
        self.begun_receiving = False
        self.handler = None
        self.message = None
        self.keepalive = True
        self.nleft = 128

    def __del__(self):
        pass

    def attach(self, handler):
        self.handler = handler
        self.handler.start_receiving()

    #
    # Override these functions if you are interested in being notified of
    # send/recv errors and of send/recv progress. The DATA parameter is the
    # string that, respectively, has been received from or sent to the
    # underlying stream socket.
    #

    def connection_lost(self):
        pass

    def begin_receiving(self):
        pass

    def recv_progress(self, data):
        pass

    def got_request(self, message):
        pass

    def begin_sending(self):
        pass

    def send_progress(self, data):
        pass

    def sent_response(self):
        pass

    #
    # Reply receives request and response and so we can update acc-
    # ess log.  We use Common Log Format (CLF) for access log.
    # In case of comet response the client might already have closed
    # the connection and we can detect that because in this case the
    # handler is None.
    #

    def reply(self, request, response):
        if self.handler == None:
            return
        if not self.keepalive:
            response["connection"] = "close"
        self.handler.bufferize(response.serialize_headers())
        self.handler.bufferize(response.serialize_body())
        prettyprint(log.debug, "> ", response)
        self._access_log(request, response)
        self.begin_sending()
        self.handler.flush(flush_progress=self.send_progress,
                           flush_success=self._send_success)

    #
    # We cannot enter in passiveclose mode before we have finished
    # sending the response.
    #

    def _send_success(self):
        self.sent_response()
        if not self.keepalive:
            self.handler.passiveclose()

    def _access_log(self, request, response):
        address = self.handler.stream.peername[0]
        x = gmtime()
        xt = "%02d/%s/%04d:%02d:%02d:%02d -0000" % (x.tm_mday,MONTH[x.tm_mon],
         x.tm_year, x.tm_hour, x.tm_min, x.tm_sec)
        requestline = "%s %s %s" % (request.method,request.uri,request.protocol)
        statuscode = response.code
        nbytes = "-"
        if response["content-length"]:
            nbytes = response["content-length"]
            if nbytes == "0":
                nbytes = "-"
        log.log_access("%s - - [%s] \"%s\" %s %s" % (address, xt, requestline,
         statuscode, nbytes))

    def closing(self):
        self.connection_lost()
        self.handler = None
        self.message = None

    def progress(self, data):
        if not self.begun_receiving:
            self.begun_receiving = True
            self.begin_receiving()
        self.recv_progress(data)

    def got_request_line(self, method, uri, protocol):
        self.message = Message(method=method, uri=uri, protocol=protocol)

    def got_response_line(self, protocol, code, reason):
        # We are a server and not a client!
        self.handler.close()

    def got_header(self, key, value):
        self.message[key] = value

    def end_of_headers(self):
        prettyprint(log.debug, "< ", self.message)
        state, length = self.nextstate(self.message)
        if state == FIRSTLINE:
            #
            # The handler does not recognize a transition
            # from reading headers to first-line as the end
            # of the response.  We do.
            #
            self._got_request()
        return state, length

    # Override this function to filter incoming headers
    def nextstate(self, request):
        return nextstate(request)

    def got_piece(self, piece):
        self.message.body.write(piece)

    def end_of_body(self):
        self._got_request()

    #
    # We don't keepalive when the client use HTTP/1.0 or the client
    # explicitly requests to close the connection or we have served
    # too many requests over this connection.
    #

    def _got_request(self):
        safe_seek(self.message.body, 0)
        message = self.message
        self.message = None
        self.nleft = self.nleft - 1
        if (self.nleft == 0 or message["connection"] == "close"
            or message.protocol == "HTTP/1.0"):
            self.keepalive = False
        self.begun_receiving = False
        self.got_request(message)

from neubot.utils import unit_formatter
from neubot.net.pollers import SimpleStats

#
# Add SimpleConnection timing information and implement
# standard methods like GET, HEAD, POST, and PUT.  Both
# additions are required to implement the transmission
# tests using the HTTP protocol.
#

class Connection(SimpleConnection):
    def __init__(self, parent):
        SimpleConnection.__init__(self)
        self.receiving = SimpleStats()
        self.sending = SimpleStats()
        self.parent = parent

    def begin_sending(self):
        self.sending.begin()

    def send_progress(self, data):
        self.sending.account(len(data))

    def sent_response(self):
        self.sending.end()

    def begin_receiving(self):
        self.receiving.begin()

    def recv_progress(self, data):
        self.receiving.account(len(data))

    def nextstate(self, request):
        if not self.parent.got_request_headers(self, request):
            return ERROR, 0
        return SimpleConnection.nextstate(self, request)

    def got_request(self, message):
        self.receiving.end()
        self.parent.got_request(self, message)

    def connection_lost(self):
        self.parent.connection_lost(self)

#
# Handles many client connections
#

SERVERARGS = {
    "certfile" : None,
    "family"   : AF_INET,
    "port"     : None,
    "secure"   : False,
}

class Server:
    def __init__(self, address, **kwargs):
        self.address = address
        self.kwargs = fixkwargs(kwargs, SERVERARGS)
        self.certfile = kwargs["certfile"]
        self.family = kwargs["family"]
        self.port = kwargs["port"]
        self.secure = kwargs["secure"]
        self.new_connection = Connection

    def bind_failed(self):
        pass

    #
    # If there is not a port, search port information in address.  We use
    # rfind() rathern than find() because it is possible for an IPv6 address
    # to contain colons.  If the address is an empty string (either because
    # the user passed an empty string or because it contained port info
    # only, such as in ':443') we set it to None--I'm not sure whether this
    # is needed or not.
    #

    def listen(self):
        if not self.port:
            index = self.address.rfind(":")
            if index >= 0:
                self.port = self.address[index+1:]
                self.address = self.address[:index]
            elif self.secure:
                self.port = "443"
            else:
                self.port = "80"
        if self.address == "":
            self.address = None
        listen(self.address, self.port, accepted=self._got_connection,
         cantbind=self.bind_failed, family=self.family, secure=self.secure,
         certfile=self.certfile)

    def _got_connection(self, stream):
        connection = self.new_connection(self)
        connection.attach(Handler(stream, connection))

    def connection_lost(self, connection):
        pass

    def got_request_headers(self, connection, request):
        return True

    def got_request(self, connection, request):
        pass

# this should be a test-only class
class WebServer(Server):
    def __init__(self, address, **kwargs):
        Server.__init__(self, address, **kwargs)

    # don't want to write on fs
    def got_request_headers(self, connection, request):
        request.body.write = lambda data: None
        return True

    def got_request(self, connection, message):
        try:
            self.process_request(connection, message)
        except KeyboardInterrupt:
            raise
        except:
            log.exception()
            m = Message()
            compose(m, code="500", reason="Internal Server Error")
            connection.reply(message, m)

    def process_request(self, connection, message):
        # uri
        if type(message.uri) != StringType:
            # being defensive
            m = Message()
            compose(m, code="500", reason="Internal Server Error")
            connection.reply(message, m)
            return
        vector = message.uri.split("/")
        if ".." in vector:
            m = Message()
            compose(m, code="403", reason="Forbidden")
            connection.reply(message, m)
            return
        if message.uri[0] != "/":
            m = Message()
            compose(m, code="403", reason="Forbidden")
            connection.reply(message, m)
            return
        path = getcwd() + message.uri
        if SEP != "/":
            path = path.replace("/", SEP)
        # method
        if message.method in [ "GET", "HEAD" ]:
            try:
                afile = open(path, "rb")
            except IOError:
                m = Message()
                compose(m, code="404", reason="Not Found")
            else:
                m = Message()
                compose(m, code="200", reason="Ok",
                 body=afile, mimetype="text/plain")
                if message.method == "HEAD":
                    # empty body
                    safe_seek(afile, 0, SEEK_END)
        elif message.method in [ "POST", "PUT" ]:
            m = Message()
            compose(m, code="200", reason="Ok")
        else:
            m = Message()
            compose(m, code="405", reason="Method Not Allowed")
            m["allow"] = "GET, HEAD, POST, PUT"
        connection.reply(message, m)

#
# Noisy connection that prints statistics at the end
# of each request.
#

class NoisyConnection(Connection):
    def __init__(self, parent):
        Connection.__init__(self, parent)

    def sent_response(self):
        Connection.sent_response(self)
        stderr.write("send-count: %sB\n" % unit_formatter(self.sending.length))
        stderr.write("send-time: %f s\n" % self.sending.diff())
        stderr.write("send-speed: %sB/s\n" % unit_formatter(self.sending.speed()))
        stderr.write("recv-count: %sB\n" % unit_formatter(self.receiving.length))
        stderr.write("recv-time: %f s\n" % self.receiving.diff())
        stderr.write("recv-speed: %sB/s\n" % unit_formatter(self.receiving.speed()))
        stderr.write("rr-time: %f s\n"%(self.sending.stop-self.receiving.start))
        stderr.write("\n")

#
# Serve files in the current working directory accepting
# connections directed to the specified address and port
# using by default :8080.
#

USAGE = "Usage: %s [-sVv] [--help] [[address] port]\n"

HELP = USAGE +								\
"Options:\n"								\
"  --help     : Print this help screen and exit.\n"			\
"  -s         : Do not print per-request statistics.\n"			\
"  -V         : Print version number and exit.\n"			\
"  -v         : Run the program in verbose mode.\n"

def main(args):
    new_connection = NoisyConnection
    # cmdline
    try:
        options, arguments = getopt(args[1:], "sVv", ["help"])
    except GetoptError:
        stderr.write(USAGE % args[0])
        exit(1)
    # options
    for name, value in options:
        if name == "--help":
            stdout.write(HELP % args[0])
            exit(0)
        elif name == "-s":
            new_connection = Connection
        elif name == "-V":
            stdout.write(VERSION+"\n")
            exit(0)
        elif name == "-v":
            log.verbose()
    # arguments
    if len(arguments) >= 3:
        stderr.write(USAGE % args[0])
        exit(1)
    elif len(arguments) == 2:
        address = arguments[0]
        port = arguments[1]
    elif len(arguments) == 1:
        address = None
        port = arguments[0]
    else:
        address = None
        port = "8080"
    # run
    server = WebServer(address, port=port)
    server.new_connection = new_connection
    server.listen()
    loop()

if __name__ == "__main__":
    main(argv)
