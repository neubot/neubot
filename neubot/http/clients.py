# neubot/http/clients.py
# Copyright (c) 2010 NEXA Center for Internet & Society

# This file is part of Neubot.
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
# HTTP client
#

from sys import path as PATH
if __name__ == "__main__":
    PATH.insert(0, ".")

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
from neubot.http.utils import prettyprinter
from neubot.net.connectors import connect
from neubot.net.pollers import loop
from neubot.utils import ticks
from neubot.http import make_filename
from sys import stdin, stdout, stderr
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
    # Error handling--subclasses should override this two functions to
    # be notified of problems when connecting or when exchanging data
    # with the server.  Note that sendrecv_error() might be invoked in
    # case of network error as well as in case of protocol error.
    #

    def connect_error(self):
        pass

    def sendrecv_error(self):
        pass

    #
    # Notifications--These functions are empty and could be ovveriden in
    # subclasses if there is interest in, say, measuring the incoming
    # or outgoing data rate.  The DATA parameter is the string that,
    # respectively, has been received from or sent to the underlying
    # stream socket.
    #

    def begin_connect(self):
        pass

    def end_connect(self):
        pass

    def begin_receiving(self):
        pass

    def recv_progress(self, data):
        pass

    def begin_sending(self):
        pass

    def send_progress(self, data):
        pass

    def sent_request(self):
        pass

    #
    # Code for sending--If the client is not connected to the server we
    # use the information in the message to establish a connection.
    # We are attached to an handler when we flush(), and so we don't need
    # to pass flush() an error-handling callback because closing() will be
    # invoked in case of errors.
    # When connect() completes we attach the handler and start receiving,
    # and so, if the connection has been closed by the remote host, our
    # closing method is invoked, and self.handler is cleared.  This is the
    # reason why we check for self.handler before invoking _do_send().
    #

    def send(self, message):
        self.request = message
        if not self.handler:
            self._do_connect()
        else:
            self._do_send()

    def _do_connect(self):
        self.begin_connect()
        connect(self.request.address, self.request.port, self._connect_success,
                cantconnect=self.connect_error, secure=SECURE(self.request),
                family=self.request.family)

    def _connect_success(self, stream):
        self.end_connect()
        self.handler = Handler(stream)
        self.handler.attach(self)
        self.handler.start_receiving()
        if self.handler:
            self._do_send()

    def _do_send(self):
        self.handler.bufferize(self.request.serialize_headers())
        self.handler.bufferize(self.request.serialize_body())
        prettyprinter(log.debug, "> ", self.request)
        self.begin_sending()
        self.handler.flush(flush_progress=self.send_progress,
                           flush_success=self.sent_request)

    #
    # In closing we dispatch send/recv errors only if there is a pending
    # request, otherwise (i) either closing() is running because we have
    # invoked handler.close() in _got_response(), (ii) or we ASSUME that
    # the server closed the connection due to timeout.  BTW this is not
    # 100% correct because we invoke sendrecv_error() even when there has
    # been a protocol error.  We need to refine this a bit.
    # We assume that we will receive a response for each request we send,
    # and so we close the connection if we receive a response when there
    # is not a pending request.  This might cause problems if we receive
    # a 100-continue response, because the 100-continue will be treated as
    # the actual response, and the actual response will therefore be not
    # expected.  That said, this is not a pratical issue because we don't
    # send 'expect: 100-continue' and so we don't expect the server to send
    # back a 100-continue interim response.
    # We notify we got_response() if nextstate is FIRSTLINE because the
    # handler does not invoke end_of_body() when there is not an attached
    # body.
    # If you want to filter incoming responses depending on their headers,
    # you can override self.nextstate()--the overriden function should
    # return (ERROR, 0) when the incoming response seems not acceptable,
    # and, otherwise, the return value of nextstate().
    # If 'connection: close' we must self.handler.close() AFTER we have
    # cleared self.request, or closing() will generate a sendrecv_error.
    #

    def closing(self):
        self.handler = None
        if self.request:
            self.sendrecv_error()
        # conservative
        self.request = None
        self.response = None

    def progress(self, data):
        if not self.begun_receiving:
            self.begun_receiving = True
            self.begin_receiving()
        self.recv_progress(data)

    def got_request_line(self, method, uri, protocol):
        self.handler.close()

    def got_response_line(self, protocol, code, reason):
        self.response = Message(protocol=protocol, code=code, reason=reason)
        if not self.request:
            self.handler.close()

    def got_header(self, key, value):
        self.response[key] = value

    def end_of_headers(self):
        prettyprinter(log.debug, "< ", self.response)
        state, length = self.nextstate(self.request, self.response)
        if state == FIRSTLINE:
            self._got_response()
        return state, length

    def nextstate(self, request, response):
        return nextstate(request, response)

    def got_piece(self, piece):
        self.response.body.write(piece)

    def end_of_body(self):
        self._got_response()

    def _got_response(self):
        self.response.body.seek(0)
        request, response = self.request, self.response
        self.request, self.response = None, None
        if response["connection"] == "close":
            self.handler.close()
        self.begun_receiving = False
        self.got_response(request, response)

    def got_response(self, request, response):
        pass

#
# When we'll measure more than one protocol, the code
# below should be moved in some shared place.
#

KiB = 1024.0
MiB = KiB * 1024.0
GiB = MiB * 1024.0

def formatbytes(count):
    if count >= GiB:
        count /= GiB
        suffix = "G"
    elif count >= MiB:
        count /= MiB
        suffix = "M"
    elif count >= KiB:
        count /= KiB
        suffix = "K"
    else:
        suffix = ""
    count = "%.1f" % count
    return count + " " + suffix + "iB"

class Timer:
    def __init__(self):
        self.start = 0
        self.stop = 0
        self.length = 0

    def begin(self):
        self.start = ticks()
        self.stop = 0
        self.length = 0

    def end(self):
        self.stop = ticks()

    def update(self, length):
        self.length += length

    def diff(self):
        return self.stop - self.start

    def speed(self):
        return self.length / self.diff()

#
# Add the SimpleClient timing information and convenience
# functions for GET, HEAD, and PUT.  Both additions are
# required to implement the transmission tests using the
# HTTP protocol.
# To notify success/failure we employ a couple of optional
# callbacks instead of some boolean variables.  And we do
# that because with the former solution we can use loop(),
# rather than dispatch().  We prefer loop() to dispatch()
# because it is cleaner to do everthying from inside the
# event loop, for an event-based program.
#

class Client(SimpleClient):
    def __init__(self):
        SimpleClient.__init__(self)
        self.notify_success = None
#       self.notify_failure = None
        self.responsebody = None
        self.sending = Timer()
        self.connecting = Timer()
        self.receiving = Timer()

    #
    # Convenience methods for measurements--they all have the
    # same API and this allows to write simpler code (see for
    # example the usage of the method() reference, below, in
    # main()).
    #

    def get(self, uri, infile=None, outfile=None, keepalive=False):
        self.responsebody = outfile
        request = Message()
        compose(request, method="GET", uri=uri, keepalive=keepalive)
        self.send(request)

    def put(self, uri, infile=None, outfile=None, keepalive=False):
        request = Message()
        compose(request, method="PUT", uri=uri,
                body=infile, keepalive=keepalive)
        self.send(request)

    def head(self, uri, infile=None, outfile=None, keepalive=False):
        request = Message()
        compose(request, method="HEAD", uri=uri, keepalive=keepalive)
        self.send(request)

    #
    # *Cough* *cough* we still need to do some work to notify
    # that there has been an error.
    #

#   def connect_error(self):
#       if self.notify_failure:
#           self.notify_failure(self)

#   def protocol_error(self):
#       if self.notify_failure:
#           self.notify_failure(self)

#   def sendrecv_error(self):
#       if self.notify_failure:
#           self.notify_failure(self)

    #
    # Resolv & connect()
    #

    def begin_connect(self):
        self.connecting.begin()

    def end_connect(self):
        self.connecting.end()

    #
    # Send
    #

    def begin_sending(self):
        self.sending.begin()

    def send_progress(self, data):
        self.sending.update(len(data))

    def sent_request(self):
        self.sending.end()

    #
    # Recv
    #

    def begin_receiving(self):
        self.receiving.begin()

    # Override because of self.responsebody
    def got_response_line(self, protocol, code, reason):
        SimpleClient.got_response_line(self, protocol, code, reason)
        if self.responsebody:
            self.response.body = self.responsebody

    def recv_progress(self, data):
        self.receiving.update(len(data))

    def got_response(self, request, response):
        self.receiving.end()
        if self.notify_success:
            self.notify_success(self, request, response)

#
# This class tries to employ two connections to download a
# resource, and this might speed-up the download when the
# round-trip delay is high and the available bandwidth is
# significant.
#

class DownloadManager:
    def __init__(self, uri, filename=None):
        self.uri = uri
        if not filename:
            filename = make_filename(uri, "index.html")
        self.filename = filename
        self.filenames = {}
        self._get_resource_length()

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
        client = Client()
        request = Message()
        compose(request, method="HEAD", uri=self.uri)
        client.notify_success = self._got_resource_length
        client.send(request)

    def _got_resource_length(self, client, request, response):
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
            client.notify_success = self._got_resource
            client.responsebody = afile
            client.send(request)

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
                client = Client()
            client.notify_success = self._got_resource_piece
            client.responsebody = afile
            client.send(request)

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
        afile.seek(lower, SEEK_SET)
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

USAGE = "Usage: %s [-2IsVv] [--help] [-o outfile] [-T infile] uri\n"

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

# response body goes on stdout by default, so use stderr
def print_stats(client, request, response):
    stderr.write("connect-time: %f s\n" % client.connecting.diff())
    stderr.write("send-count: %s\n" % formatbytes(client.sending.length))
    stderr.write("send-time: %f s\n" % client.sending.diff())
    stderr.write("send-speed: %s/s\n" % formatbytes(client.sending.speed()))
    stderr.write("recv-count: %s\n" % formatbytes(client.receiving.length))
    stderr.write("recv-time: %f s\n" % client.receiving.diff())
    stderr.write("recv-speed: %s/s\n" % formatbytes(client.receiving.speed()))
    stderr.write("rr-time: %f s\n"%(client.receiving.stop-client.sending.start))

#
# There is a function named main() because we want to be able to
# run this module from neubot(1).
#

def main(args):
    # defaults
    client = Client()
    client.notify_success = print_stats
    method = client.get
    infile = stdin
    outfile = stdout
    two = False
    # parse command line
    try:
        options, arguments = getopt(args[1:], "2Io:sT:Vv", ["help"])
    except GetoptError:
        stderr.write(USAGE % args[0])
        exit(1)
    for name, value in options:
        if name == "-2":
            two = True
        elif name == "--help":
            stdout.write(HELP % args[0])
            exit(0)
        elif name == "-I":
            method = client.head
        elif name == "-o":
            method = client.get
            if value == "-":
                outfile = stdout
                continue
            try:
                outfile = open(value, "wb")
            except IOError:
                log.exception()
                exit(1)
        elif name == "-s":
            client.notify_success = None
        elif name == "-T":
            method = client.put
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
    if len(arguments) == 0 or len(arguments) > 1:
        stderr.write(USAGE % args[0])
        exit(1)
    # run client
    if two:
        if method == client.head:
            log.error("Can't use -2 together with -I")
            exit(1)
        if method == client.put:
            log.error("Can't use -2 together with -T")
            exit(1)
        uri = arguments[0]
        DownloadManager(uri)
    else:
        method(arguments[0], infile, outfile)
    loop()

if __name__ == "__main__":
    main(argv)
