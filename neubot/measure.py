# neubot/measure.py
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

import StringIO
import getopt
import logging
import os
import sys
import socket
import time

import neubot

ADDRESS    = "0.0.0.0"
FAMILY     = socket.AF_INET
MAXCONNS   = 7
MAXLENGTH  = (1<<23)
MYFILE     = None
PORT       = "80"

class server:
    def __init__(self, poller, family=FAMILY, address=ADDRESS, port=PORT,
                 maxconns=MAXCONNS, maxlength=MAXLENGTH, myfile=MYFILE):
        self.poller = poller
        self.family = family
        self.address = address
        self.port = port
        self.maxconns = maxconns
        self.maxlength = maxlength
        self.myfile = myfile
        self.conns = 0
        neubot.http.acceptor(self, self.poller, self.address, self.port,
                             self.family, secure=False, certfile=None)

    def aborted(self, acceptor):
        logging.error("Could not listen at '%s'" % acceptor)

    def listening(self, acceptor):
        logging.info("Listening at '%s'" % acceptor)
        self.poller.register_periodic(neubot.whitelist.prune)

    def got_client(self, protocol):
        logging.info("[%s] New client" % protocol)
        # XXX Here we should RST the client to avoid CLOSE_WAIT state
        if self.conns > self.maxconns:
            logging.error("[%s] Too many connections" % protocol)
            protocol.close()
            return
        address, port = str(protocol).split(":")                        # XXX
        if not neubot.whitelist.allowed(address):
            logging.warning("Not in whitelist %s" % address)
            protocol.close()
            return
        neubot.measure.servercontext(protocol, self)
        self.conns = self.conns + 1

    def dead_client(self):
        self.conns = self.conns - 1

class servercontext:
    def __init__(self, protocol, server):
        self.protocol = protocol
        self.protocol.attach(self)
        logging.info("[%s] Ready to serve client" % protocol)
        self.server = server
        self.requestlength = 0
        self.responselength = 0
        self.recv_begin = time.time()
        self.recv_end = 0
        self.send_begin = 0
        self.send_end = 0

    def got_metadata(self, protocol):
        request = protocol.message
        logging.info("[%s] Pretty-printing request" % protocol)
        neubot.http.prettyprinter(logging.info, "[%s]   " % protocol, request)
        # Make sure request-body is not too big
        if request["transfer-encoding"] == "chunked":
            raise Exception("Not accepting chunked request body")
        contentlength = request["content-length"]
        if contentlength:
            self.requestlength = int(contentlength)
            if self.requestlength > self.server.maxlength:
                raise Exception("Request body is too big")

    def is_message_unbounded(self, protocol):
        return False

    def got_message(self, protocol):
        self.recv_end = time.time()
        request = protocol.message
        response = neubot.http.message(protocol="HTTP/1.1")
        response["date"] = neubot.http.date()
        response["cache-control"] = "no-cache"
        # TODO Support keepalive for a certain number of requests
        keepalive = False
        if request.uri == "/":
            if request.method == "POST" or request.method == "PUT":
                response.code, response.reason = "204", "No Content"
            elif request.method == "GET" or request.method == "HEAD":
                if self.server.myfile:
                    try:
                        myfile = open(self.server.myfile, "rb")
                    except:
                        myfile = None
                    if myfile:
                        # TODO Support Content-Range for more flexible testing
                        response.code, response.reason = "200", "Ok"
                        response["content-type"] = "application/octet-stream"
                        myfile.seek(0, os.SEEK_END)
                        mylen = myfile.tell()
                        myfile.seek(0)
                        self.responselength = mylen
                        contentlength = str(self.responselength)
                        response["content-length"] = contentlength
                        if request.method == "GET":
                            response.body = myfile
                    else:
                        response.code, response.reason = "404", "Not Found"
                else:
                    response.code, response.reason = "404", "Not Found"
            else:
                response.code = "405", "Method Not Allowed"
                response["allow"] = "GET, HEAD, POST, PUT"
        else:
            response.code, response.reason = "404", "Not Found"
        if not keepalive:
            response["connection"] = "close"
        logging.info("[%s] Pretty-printing response" % protocol)
        neubot.http.prettyprinter(logging.info, "[%s]   " % protocol, response)
        logging.info("[%s] Start sending response" % protocol)
        protocol.sendmessage(response)
        self.send_begin = time.time()

    def message_sent(self, protocol):
        self.send_end = time.time()
        logging.info("[%s] Response sent" % protocol)
        logging.info("[%s] Waiting for client to close connection" % protocol)

    def closing(self, protocol):
        address, port = str(protocol).split(":")                        # XXX
        neubot.whitelist.unregister(address)
        logging.info("[%s] The connection has been closed" % protocol)
        # TODO Save result into the proper database
        logging.info("[%s] Received %d bytes in %.2f seconds" % (protocol,
                     self.requestlength, self.recv_end - self.recv_begin))
        logging.info("[%s] Sent %d bytes in %.2f seconds" % (protocol,
                     self.responselength, self.send_end - self.send_begin))
        self.server.dead_client()

CONNECTIONS = 1

class client:
    def __init__(self, poller, uri, family=FAMILY, connections=3, myfile=None):
        logging.info("Begin measurement")
        self.poller = poller
        self.uri = uri
        self.family = family
        self.connections = connections
        self.myfile = myfile
        (self.scheme, self.address,
         self.port, self.path) = neubot.http.urlsplit(uri)
        secure =  self.scheme == "https"
        while connections >= 1:
            connections = connections - 1
            neubot.http.connector(self, self.poller, self.address,
                                  self.port, self.family, secure)

    def aborted(self, connector):
        logging.error("Connection to '%s' failed" % connector)

    def connected(self, connector, protocol):
        logging.info("Connected to '%s'" % connector)
        clientcontext(protocol, self)

    def probe_done(self):
        pass

    def __del__(self):
        logging.info("End measurement")

class clientcontext:
    def __init__(self, protocol, client):
        self.protocol = protocol
        self.client = client
        self.request = neubot.http.message(uri=self.client.path,
                                           protocol="HTTP/1.1")
        self.request["date"] = neubot.http.date()
        self.request["cache-control"] = "no-cache"
        self.request["connection"] = "close"
        self.request["host"] = self.client.address + ":" + self.client.port
        self.request["pragma"] = "no-cache"
        if self.client.myfile:
            self.request.method = "PUT"
            try:
                myfile = open(self.client.myfile, "rb")
            except:
                myfile = None
            if myfile:
                myfile.seek(0, os.SEEK_END)
                self.requestlength = myfile.tell()
                self.request["content-length"] = str(self.requestlength)
                self.request["content-type"] = "application/octet-stream"
                self.request.body = myfile
                myfile.seek(0)
        else:
            # FIXME Add support for HEAD (to calculate "latency")
            self.request.method = "GET"
            self.requestlength = 0
        protocol.attach(self)
        logging.info("[%s] Pretty-printing the request" % protocol.sockname)
        neubot.http.prettyprinter(logging.info, "[%s]   " % protocol.sockname,
                                  self.request)
        logging.info("[%s] Start sending the request" % protocol.sockname)
        protocol.sendmessage(self.request)
        self.send_begin = time.time()
        self.send_end = 0
        self.recv_begin = 0
        self.recv_end = 0
        self.responselength = 0

    def message_sent(self, protocol):
        self.send_end = time.time()
        logging.info("[%s] Done sending request" % protocol.sockname)
        logging.info("[%s] Waiting for response" % protocol.sockname)
        self.recv_begin = time.time()

    def got_metadata(self, protocol):
        logging.info("[%s] Pretty-printing response" % protocol.sockname)
        response = protocol.message
        neubot.http.prettyprinter(logging.info, "[%s]   " % protocol.sockname,
                                  response)
        response.body = StringIO.StringIO()
        # FIXME The model does not allow easy handling of responses to HEAD
        if self.request.method == "HEAD":
            if self.request["transfer-encoding"]:
                del self.request["transfer-encoding"]
            if self.request["content-length"]:
                del self.request["content-length"]

    def is_message_unbounded(self, protocol):
        return neubot.http.response_unbounded(self.request, protocol.message)

    def got_message(self, protocol):
        self.recv_end = time.time()
        logging.info("[%s] Done receiving response" % protocol.sockname)
        response = protocol.message
        response.body.seek(0, os.SEEK_END)
        self.responselength = response.body.tell()
        protocol.close()

    def closing(self, protocol):
        logging.info("[%s] Connection closed" % protocol.sockname)
        # TODO Save result into the proper database
        logging.info("[%s] Received %d bytes in %.2f seconds" % (
                     protocol.sockname, self.responselength,
                     self.recv_end - self.recv_begin))
        logging.info("[%s] Sent %d bytes in %.2f seconds" % (
                     protocol.sockname, self.requestlength,
                     self.send_end - self.send_begin))

    def __del__(self):
        self.client.probe_done()

USAGE = 								\
"Usage:\n"								\
"  neubot [options] measure --server [options] [[address] port]\n"	\
"  neubot [options] measure [options] uri\n"				\
"\n"									\
"Try `neubot measure --help' for more help.\n"

LONGOPTS = [
    "connections=",
    "disable-whitelist",
    "disable-whitelist-prune",
    "file=",
    "help",
    "permanent-whitelist",
    "server",
    "whitelist=",
]

HELP = 									\
"Usage:\n"								\
"  neubot [options] measure --server [options] [[address] port]\n"	\
"  neubot [options] measure [options] uri\n"				\
"\n"									\
"Options:\n"								\
"  --connections NCONN\n"						\
"      When running as a client, use NCONN connections to download\n"	\
"      the resource.  When running as a server, do not accept more\n"	\
"      than NCONN incoming connections at a time.\n"			\
"  --disable-whitelist\n"						\
"      Disable the white-list mechanism.\n"				\
"  --disable-whitelist-prune\n"						\
"      Disable the white-list prune mechanism.\n"			\
"  --file FILE\n"							\
"      When running as a client, measure the time required to send\n"	\
"      the specified file (instead of measuring the time required\n"	\
"      to download a file.)  When running as a server, indicates the\n"	\
"      file to be sent to the client.\n"				\
"  --help\n"								\
"      Print this help screen.\n"					\
"  --permanent-whitelist\n"						\
"      Do not remove address from whitelist after a measure.\n"		\
"  --server\n"								\
"      Run in server mode.\n"						\
"  --whitelist ADDRESS\n"						\
"      Add ADDRESS to white-list (address that are not white-listed\n"	\
"      are not allowed to perform measurements.)\n"			\
"\n"

def main(argv):
    try:
        options, arguments = getopt.getopt(argv[1:], "", LONGOPTS)
    except getopt.error:
        sys.stderr.write(USAGE)
        sys.exit(1)
    connections = 1
    myfile = None
    servermode = False
    for name, value in options:
        if name == "--connections":
            try:
                connections = int(value)
            except ValueError:
                connections = -1
            if connections < 0:
                logging.error("Argument to --connections is invalid")
                sys.exit(1)
        elif name == "--disable-whitelist":
            neubot.whitelist.allowed = lambda x: True
        elif name == "--disable-whitelist-prune":
            neubot.whitelist.prune = lambda x: None
        elif name == "--file":
            myfile = value
        elif name == "--help":
            sys.stdout.write(HELP)
            sys.exit(0)
        elif name == "--permanent-whitelist":
            neubot.whitelist.unregister = lambda x: None
        elif name == "--server":
            servermode = True
        elif name == "--whitelist":
            neubot.whitelist.register(value)
    poller = neubot.network.poller()
    if servermode:
        if len(arguments) >= 3:
            sys.stderr.write(USAGE)
            sys.exit(1)
        elif len(arguments) == 2:
            address = arguments[0]
            port = arguments[1]
        elif len(arguments) == 1:
            address = "0.0.0.0"
            port = arguments[0]
        else:
            address = "0.0.0.0"
            port = "80"
        server(poller, address=address, port=port, myfile=myfile)
    else:
        if len(arguments) >= 2:
            sys.stderr.write(USAGE)
            sys.exit(1)
        elif len(arguments) == 1:
            uri = arguments[0]
        else:
            sys.stderr.write(USAGE)
            sys.exit(1)
        client(poller, uri=uri, connections=connections, myfile=myfile)
    poller.loop()

if (__name__ == "__main__"):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    main(sys.argv)
