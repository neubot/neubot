# neubot/http/clients.py

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
# HTTP client
#

if __name__ == "__main__":
    from sys import path
    path.insert(0, ".")

from StringIO import StringIO
from os.path import exists
from getopt import GetoptError
from getopt import getopt
from neubot import log
from os import unlink, SEEK_SET, SEEK_END
from neubot import version as VERSION
from neubot.http.handlers import ERROR
from neubot.http.handlers import FIRSTLINE
from neubot.http.handlers import Handler
from neubot.http.handlers import Receiver
from neubot.http.messages import Message
from neubot.http.messages import compose
from neubot.http.utils import nextstate
from neubot.http.utils import prettyprint
from neubot.net.streams import connect
from neubot.net.pollers import loop
from neubot.net.pollers import enable_stats
from neubot.times import ticks
from neubot.utils import safe_seek
from neubot.http.utils import make_filename
from sys import stdin, stdout, stderr
from neubot.utils import unit_formatter
from neubot.utils import SimpleStats
from sys import exit
from sys import argv

def SECURE(message):
    return message.scheme == "https"

#
# This class defines a simple client model that opens
# a single connection with the server.
#

class SimpleClient(Receiver):
    def __init__(self):
        self.begun_receiving = False
        self.handler = None
        self.request = None
        self.response = None

    def __del__(self):
        pass

    #
    # Notifications--These functions are empty and could be ovveriden
    # in subclasses; the DATA parameter is the string that, respectively,
    # has been received from or sent to the underlying stream socket.
    #

    def connection_failed(self):
        pass

    def begin_connect(self):
        pass

    def end_connect(self):
        pass

    def begin_receiving(self):
        pass

    def recv_progress(self, data):
        pass

    def got_response(self, request, response):
        pass

    def begin_sending(self):
        pass

    def send_progress(self, data):
        pass

    def sent_request(self):
        pass

    def connection_lost(self):
        pass

    #
    # This is the most important method of the client, that starts
    # the send/recv cycle.  Note that it makes sense to provide a
    # response message when you want to save the response body into
    # an already opened file.
    #

    def sendrecv(self, message, response=None):
        self.request = message
        self.response = response
        if not self.handler:
            self._do_connect()
        else:
            self._do_send()

    def _do_connect(self):
        self.begin_connect()
        connect(self.request.address, self.request.port, self._connect_success,
                cantconnect=self.connection_failed, secure=SECURE(self.request),
                family=self.request.family)

    def _connect_success(self, stream):
        self.end_connect()
        self.handler = Handler(stream, self)
        self.handler.start_receiving()
        #
        # self.handler.start_receiving() starts reading from
        # the underlying socket.  So, if the server has already
        # closed the connection self.handler will be None when
        # start_receiving() returns.
        #
        if self.handler:
            self._do_send()

    def _do_send(self):
        self.handler.bufferize(self.request.serialize_headers())
        self.handler.bufferize(self.request.serialize_body())
        prettyprint(log.debug, "> ", self.request)
        self.begin_sending()
        self.handler.flush(flush_progress=self.send_progress,
                           flush_success=self.sent_request)

    def closing(self):
        self.connection_lost()
        self.handler = None
        self.request = None
        self.response = None

    def progress(self, data):
        if not self.begun_receiving:
            self.begun_receiving = True
            self.begin_receiving()
        self.recv_progress(data)

    def got_request_line(self, method, uri, protocol):
        # We are a client and not a server!
        self.handler.close()

    def got_response_line(self, protocol, code, reason):
        if not self.response:
            self.response = Message()
        self.response.protocol = protocol
        self.response.code = code
        self.response.reason = reason
        if not self.request:
            # We are not waiting for a response!
            self.handler.close()

    def got_header(self, key, value):
        self.response[key] = value

    def end_of_headers(self):
        prettyprint(log.debug, "< ", self.response)
        state, length = self.nextstate(self.request, self.response)
        if state == FIRSTLINE:
            #
            # The handler does not recognize a transition
            # from reading headers to first-line as the end
            # of the response.  We do.
            #
            self._got_response()
        return state, length

    # Override this function to filter incoming headers
    def nextstate(self, request, response):
        return nextstate(request, response)

    def got_piece(self, piece):
        self.response.body.write(piece)

    def end_of_body(self):
        self._got_response()

    def _got_response(self):
        safe_seek(self.response.body, 0)
        request, response = self.request, self.response
        self.request, self.response = None, None
        self.begun_receiving = False
        self.got_response(request, response)
        if (request["connection"] == "close" or
            response["connection"] == "close"):
            self.handler.close()

#
# Add the SimpleClient timing information and convenience
# functions for GET, HEAD, and PUT.  Both additions are
# required to implement the transmission tests using the
# HTTP protocol.
#

class Client(SimpleClient):
    def __init__(self, parent):
        SimpleClient.__init__(self)
        self.sending = SimpleStats()
        self.connecting = SimpleStats()
        self.receiving = SimpleStats()
        self.parent = parent

    def __del__(self):
        SimpleClient.__del__(self)

    def connection_failed(self):
        self.parent.connection_failed(self)

    def begin_connect(self):
        self.connecting.begin()

    def end_connect(self):
        self.connecting.end()

    def begin_sending(self):
        self.sending.begin()

    def send_progress(self, data):
        self.sending.account(len(data))

    def sent_request(self):
        self.sending.end()

    def begin_receiving(self):
        self.receiving.begin()

    def recv_progress(self, data):
        self.receiving.account(len(data))

    def nextstate(self, request, response):
        if not self.parent.got_response_headers(self, request, response):
            return ERROR, 0
        return SimpleClient.nextstate(self, request, response)

    def got_response(self, request, response):
        self.receiving.end()
        self.parent.got_response(self, request, response)

    def connection_lost(self):
        self.parent.connection_lost(self)

class ClientController:
    def connection_lost(self, client):
        pass

    def connection_failed(self, client):
        pass

    def got_response_headers(self, client, request, response):
        return True

    def got_response(self, client, request, response):
        pass

#
# This class tries to employ two connections to download a
# resource, and this might speed-up the download when the
# round-trip delay is high and the available bandwidth is
# significant.
#

DM_LENGTH = 1<<0
DM_SINGLE = 1<<1
DM_TWO    = 1<<2

class DownloadManager(ClientController):
    def __init__(self, uri, filename=None):
        self.uri = uri
        if not filename:
            filename = make_filename(uri, "index.html")
        self.filename = filename
        self.filenames = {}
        self.flags = 0
        self._get_resource_length()

    #
    # Interface with client
    #

    def got_response(self, client, request, response):
        if self.flags & DM_LENGTH:
            self._got_resource_length(client, request, response)
        elif self.flags & DM_SINGLE:
            self._got_resource(client, request, response)
        elif self.flags & DM_TWO:
            self._got_resource_piece(client, request, response)
        else:
            raise Exception("Bad flags")

    #
    # We send an HEAD request to retrieve resource meta-
    # data.  We can split the work between two clients if
    # the response contains the resource length and the
    # origin server advertises byte-range support (it is
    # "not required to do so", per RFC 2616, but we don't
    # want to send a byte-range request when we are not
    # sure).
    # In case of two-clients download we need to open the
    # output file in append mode, and so, if the output
    # file already exists, we must unlink it.
    # We don't set keepalive=False in the first message
    # because we would like to re-use the connection for
    # the subsequent GET request.
    #

    def _get_resource_length(self):
        client = Client(self)
        request = Message()
        compose(request, method="HEAD", uri=self.uri)
        self.flags |= DM_LENGTH
        client.sendrecv(request)

    def _got_resource_length(self, client, request, response):
        self.flags &= ~DM_LENGTH
        if (response.code == "200" and response["content-length"]
         and response["accept-ranges"] == "bytes"):
            length = response["content-length"]
            try:
                length = int(length)
            except ValueError:
                length = -1
            if length >= 0:
                if exists(self.filename):
                    unlink(self.filename)
                self.flags |= DM_TWO
                self._get_resource_piece(0, [0, length/2-1], client)
                self._get_resource_piece(1, [length/2, length-1], None)
            else:
                log.error("Bad content-length")
        else:
            self._get_resource(client)

    #
    # GET a resource the traditional way, with a single
    # request, and saving the result directly in the out-
    # put file.
    # XXX Rather than using the .responsebody hack it would
    # be better to pass the client the response with the body
    # field already set.
    # Some OSes does not allow to remove an opened file and
    # so we close the body before trying unlink().
    #

    def _get_resource(self, client):
        try:
            afile = open(self.filename, "wb")
        except IOError:
            log.error("Can't open file: %s" % self.filename)
            log.exception()
        else:
            request = Message()
            compose(request, method="GET", uri=self.uri, keepalive=False)
            self.flags |= DM_SINGLE
            response = Message()
            response.body = afile
            client.sendrecv(request, response)

    def _got_resource(self, client, request, response):
        if response.code != "200":
            log.error("Response: %s %s" % (response.code, response.reason))
            response.body.close()
            unlink(self.filename)

    #
    # We accept the response if the range in the response
    # is the same range we requested for.  Once we got both
    # halves, we cat them to re-construct the resource.
    # Some OSes does not allow to remove an opened file and
    # so we close the body before trying unlink.
    # XXX Rather than using the .responsebody hack it would
    # be better to pass the client the response with the body
    # field already set.
    #

    def _get_resource_piece(self, index, rangev, client=None):
        filename = "%s.%d" % (self.filename, index)
        byterange = "%d-%d" % (rangev[0], rangev[1])
        self.filenames[byterange] = filename
        try:
            afile = open(filename, "wb")
        except IOError:
            log.error("Can't open file: %s" % filename)
            log.exception()
        else:
            request = Message()
            compose(request, method="GET", uri=self.uri, keepalive=False)
            request["range"] = "bytes=%s" % byterange
            if not client:
                client = Client(self)
            response = Message()
            response.body = afile
            client.sendrecv(request, response)

    def _got_resource_piece(self, client, request, response):
        response.body.close()
        # parse
        value = response["content-range"]
        vector = value.split()
        if len(vector) != 2 or vector[0] != "bytes":
            log.error("Bad content-range")
            return
        value = vector[1]
        vector = value.split("/")
        if len(vector) != 2:
            log.error("Bad content-range")
            return
        # check
        byterange = vector[0]
        if not self.filenames.has_key(byterange):
            log.error("Unexpected content-range")
            return
        # fopen
        try:
            afile = open(self.filename, "ab")
        except IOError:
            log.error("Can't open file: %s" % self.filename)
            log.exception()
            return
        response.body.close()
        filename = self.filenames[byterange]
        try:
            response.body = open(filename, "rb")
        except IOError:
            log.error("Can't open file: %s" % filename)
            log.exception()
            return
        # unpack
        try:
            vector = byterange.split("-")
            lower, upper = map(int, vector)
        except ValueError:
            log.exception()
            return
        # copy
        safe_seek(afile, lower, SEEK_SET)
        while True:
            octets = response.body.read(262144)
            if not octets:
                break
            afile.write(octets)
        # cleanup
        afile.close()
        response.body.close()
        unlink(filename)

#
# Rather than inventing random command line arguments for what
# we want to do, let's re-use as many switches accepted by curl(1)
# as possible.
#

USAGE =									\
"Usage: @PROGNAME@ -V\n"						\
"       @PROGNAME@ --help\n"						\
"       @PROGNAME@ -2 [-v] http://host[:port]/resource ...\n"		\
"       @PROGNAME@ -I [-sv] http://host[:port]/resource ...\n"		\
"       @PROGNAME@ -o outfile [-sv] http://host[:port]/resource ...\n"	\
"       @PROGNAME@ -T infile [-sv] http://host[:port]/resource ...\n"	\
"       @PROGNAME@ [-sv] http://host[:port]/resource ...\n"

HELP = USAGE +								\
"Options:\n"								\
"  -2         : Try to download using two connections.\n"		\
"  --help     : Print this help screen and exit.\n"			\
"  -I         : Use HEAD to retrieve HTTP headers only.\n"		\
"  -o outfile : GET uri and save response body in outfile.\n"		\
"  -s         : Do not print per-request statistics.\n"			\
"  -T infile  : PUT uri and read request body from infile.\n"		\
"  -V         : Print version number and exit.\n"			\
"  -v         : Run the program in verbose mode.\n"

class DefaultController(ClientController):
    def __init__(self):
        self.print_headers = None

    def got_response(self, client, request, response):
        if self.print_headers:
            self.print_headers(client, request, response)

class VerboseController(DefaultController):
    def __init__(self):
        self.print_headers = None

    #
    # If the user specified -I we must print headers we have
    # read on the standard output, and then the statistics
    # must go on the standard error.
    # If the output file is the standard output we must print
    # stats on the standard error as well (or the output will
    # become an horrible mess).
    # Otherwise it's fine to use standard output.
    #

    def got_response(self, client, request, response):
        if request.method == "HEAD" or response.body == stdout:
            self._print_stats(client, stderr)
        else:
            self._print_stats(client, stdout)
        DefaultController.got_response(self, client, request, response)

    def _print_stats(self, client, f):
        f.write("connect-time: %f s\n" % client.connecting.diff())
        f.write("send-count: %sB\n" % unit_formatter(client.sending.length))
        f.write("send-time: %f s\n" % client.sending.diff())
        f.write("send-speed: %sB/s\n" % unit_formatter(client.sending.speed()))
        f.write("recv-count: %sB\n" % unit_formatter(client.receiving.length))
        f.write("recv-time: %f s\n" % client.receiving.diff())
        f.write("recv-speed: %sB/s\n" % unit_formatter(client.receiving.speed()))
        f.write("rr-time: %f s\n"%(client.receiving.stop-client.sending.start))

def print_headers(client, request, response):
    prettyprint(stdout.write, "", response, eol="\r\n")

#
# There is a function named main() because we want to be able to
# run this module from neubot(1).
#

GET, HEAD, PUT, TWOCONN = range(0,4)

def main(args):
    # defaults
    new_controller = VerboseController
    infile = stdin
    outfile = None
    method = GET
    # parse command line
    try:
        options, arguments = getopt(args[1:], "2Io:sT:Vv", ["help"])
    except GetoptError:
        stderr.write(USAGE.replace("@PROGNAME@", args[0]))
        exit(1)
    for name, value in options:
        if name == "-2":
            method = TWOCONN
        elif name == "--help":
            stdout.write(HELP.replace("@PROGNAME@", args[0]))
            exit(0)
        elif name == "-I":
            method = HEAD
        elif name == "-o":
            method = GET
            if value == "-":
                outfile = stdout
                continue
            try:
                outfile = open(value, "wb")
            except IOError:
                log.exception()
                exit(1)
        elif name == "-s":
            new_controller = DefaultController
        elif name == "-T":
            method = PUT
            if value == "-":
                infile = stdin
                continue
            try:
                infile = open(value, "rb")
            except IOError:
                log.exception()
                exit(1)
        elif name == "-V":
            stdout.write(VERSION+"\n")
            exit(0)
        elif name == "-v":
            log.verbose()
            enable_stats()
    # sanity
    if len(arguments) == 0:
        stderr.write(USAGE.replace("@PROGNAME@", args[0]))
        exit(1)
    # run
    if method == TWOCONN:
        #
        # XXX The download manager will fail if invoked more than
        # once for the SAME download.  I don't want to fix this
        # problem because it is not relevant for my tests, and so,
        # just don't do that :).
        #
        for uri in arguments:
            DownloadManager(uri)
        loop()
    else:
        controller = new_controller()
        if method == GET:
            #
            # If the output file is not specified we are able to download
            # all the URIs concurrently.
            # If the output file is the standard output or the user specified
            # an output file, we download each URI sequentially because we do
            # not want pieces of different files to mix.
            #
            for uri in arguments:
                if outfile == None:
                    try:
                        filename = make_filename(uri, "index.html")
                        ofile = open(filename, "wb")
                    except IOError:
                        log.exception()
                        continue
                else:
                    ofile = outfile
                client = Client(controller)
                request = Message()
                compose(request, method="GET", uri=uri, keepalive=False)
                response = Message()
                response.body = ofile
                client.sendrecv(request, response)
                if outfile != None:
                    loop()
                    if outfile != stdout:
                        #
                        # The SimpleClient code rewind()s the file because
                        # it assumes that the user is interested in reading
                        # the body.  This is not what we want here, because
                        # we are appending to a single output file, and so
                        # undo the rewind().
                        #
                        safe_seek(outfile, 0, SEEK_END)
                    else:
                        outfile.flush()
            if outfile == None:
                loop()
        elif method == HEAD:
            for uri in arguments:
                client = Client(controller)
                controller.print_headers = print_headers
                request = Message()
                compose(request, method="HEAD", uri=uri, keepalive=False)
                client.sendrecv(request)
            loop()
        elif method == PUT:
            #
            # To keep things simple, we PUT each URI sequentially,
            # and so we just need to rewind the input stream after
            # each PUT.
            # When the input stream is the standard input, we have
            # to read stdin until EOF and wrap the content into
            # a StringIO, because we need to know stardard input
            # length in advance (and we issue a warning because we
            # might run out-of-memory because of that).
            #
            if infile == stdin:
                log.warning("Trying to bufferize standard input")
                log.warning("We might run out of memory because of that")
                infile = StringIO(stdin.read())
            for uri in arguments:
                client = Client(controller)
                request = Message()
                compose(request, method="PUT", uri=uri, keepalive=False)
                client.sendrecv(request)
                loop()
                safe_seek(infile, 0, SEEK_SET)

if __name__ == "__main__":
    main(argv)
