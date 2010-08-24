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

from getopt import GetoptError
from getopt import getopt
from neubot import log
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

KiB = 1024
MiB = KiB * 1024
GiB = MiB * 1024

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
            self.notify_success(self)

#
# Rather than inventing random command line arguments for what
# we want to do, let's re-use instead a subset of the switches
# accepted by curl(1).
#

USAGE = "Usage: %s [-IsVv] [--help] [-o outfile] [-T infile] uri\n"

HELP = USAGE +								\
"Options:\n"								\
"  --help     : Print this help screen and exit.\n"			\
"  -I         : Use HEAD to retrieve HTTP headers only.\n"		\
"  -o outfile : GET uri and save response body in outfile.\n"		\
"  -s         : Be silent and do not print stats.\n"			\
"  -T infile  : PUT uri and read request body from infile.\n"		\
"  -V         : Print version number and exit.\n"			\
"  -v         : Run the program in verbose mode.\n"

# response body goes on stdout by default, so use stderr
def print_stats(client):
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
    # parse command line
    try:
        options, arguments = getopt(args[1:], "Io:sT:Vv", ["help"])
    except GetoptError:
        stderr.write(USAGE % args[0])
        exit(1)
    for name, value in options:
        if name == "--help":
            stdout.write(HELP % args[0])
            exit(0)
        elif name == "-I":
            method = client.head
        elif name == "-o":
            method = client.get
            if value == "-":
                # this means 'use stdout'
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
                # this means 'use stdin'
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
    method(arguments[0], infile, outfile)
    loop()

if __name__ == "__main__":
    main(argv)
