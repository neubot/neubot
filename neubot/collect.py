# neubot/collect.py
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
import json
import logging
import socket
import sys
import uuid

import neubot

DIRECTIONS = ["upload", "download"]

class servlet:
    def main(self, protocol, response):
        if protocol.message.method != "POST":
            response.code, response.reason = "204", "No Content"
            return
        protocol.message.body.seek(0)
        octets = protocol.message.body.read()
        try:
            json.loads(octets)                                          # FIXME
        except ValueError:
            response.code, response.reason = "500", "Internal Server Error"
            return
        neubot.database.writes(octets)
        response.code, response.reason = "201", "Created"

class client:
    def __init__(self, poller, uri, octets, family=socket.AF_INET):
        self.poller = poller
        scheme, address, port, self.path = neubot.http.urlsplit(uri)
        secure =  scheme == "https"
        neubot.http.connector(self, poller, address, port, family, secure)
        logging.info("Begin uploading results to %s" % address)
        self.octets = octets
        json.loads(self.octets)                                         # FIXME

    def aborted(self, connector):
        logging.error("Connection to '%s' failed" % connector)

    def connected(self, connector, protocol):
        logging.debug("Connected to '%s'" % connector)
        protocol.attach(self)
        logging.debug("Pretty-printing the request")
        self.request = neubot.http.message(method="POST",
          uri=self.path, protocol="HTTP/1.1")
        self.request["date"] = neubot.http.date()
        self.request["cache-control"] = "no-cache"
        self.request["connection"] = "close"
        self.request["host"] = str(protocol)
        self.request["pragma"] = "no-cache"
        self.request["content-type"] = "application/json"
        self.request["content-length"] = str(len(self.octets))
        self.request.body = StringIO.StringIO(self.octets)
        neubot.http.prettyprinter(logging.debug, "  ", self.request)
        neubot.utils.prettyprint_json(logging.debug, "  ", self.octets)
        logging.debug("Start sending the request")
        protocol.sendmessage(self.request)

    def message_sent(self, protocol):
        logging.debug("Done sending request to '%s'" % protocol)
        logging.debug("Waiting for response from '%s'" % protocol)
        protocol.recvmessage()

    def got_metadata(self, protocol):
        logging.debug("Pretty-printing response")
        response = protocol.message
        neubot.http.prettyprinter(logging.debug, "  ", response)
        response.body = StringIO.StringIO()
        if response.code != "201":
            raise Exception("Unexpected response code")

    def is_message_unbounded(self, protocol):
       if neubot.http.response_unbounded(self.request, protocol.message):
            raise Exception("Unexpected unbounded response")

    def got_message(self, protocol):
        protocol.close()
        logging.info("Results successfully uploaded")

    def closing(self, protocol):
        logging.debug("Connection to '%s' closed" % protocol)

USAGE = 								\
"Usage:\n"								\
"  neubot [options] collect --server [options] [[address] port]\n"	\
"  neubot [options] collect [options] uri\n"				\
"\n"									\
"Try `neubot collect --help' for more help.\n"

LONGOPTS = [
    "concurrency=",
    "direction=",
    "help",
    "identifier=",
    "length=",
    "myname=",
    "peername=",
    "protocol=",
    "server",
    "timespan=",
]

HELP = 									\
"Usage:\n"								\
"  neubot [options] collect --server [options] [[address] port]\n"	\
"  neubot [options] collect [options] uri\n"				\
"\n"									\
"Options:\n"								\
"  --concurrency N\n"							\
"      The average number of concurrent active connections.\n"          \
"  --direction download|upload\n"					\
"      The direction of the transfer.\n"                                \
"  --help\n"								\
"      Print this help screen.\n"					\
"  --identifier UUID\n"                                                 \
"      Specify the measure UUID (if you omit this option, a random\n"   \
"      UUID will be created.)\n"                                        \
"  --length N\n"							\
"      The length of the transfer.\n"                                   \
"  --myname ADDRESS\n"                                                  \
"      The IP address of the report sender.\n"                          \
"  --peername ADDRESS\n"                                                \
"      The IP address of the report sender's peer.\n"                   \
"  --protocol PROTOCOL\n"                                               \
"      The protocol employed for the transfer (e.g. HTTP)\n"            \
"  --server\n"								\
"      Run in server mode.\n"						\
"  --timespan TIME\n"                                                   \
"      The time needed for the transfer to complete.\n"

def main(argv):
    try:
        options, arguments = getopt.getopt(argv[1:], "", LONGOPTS)
    except getopt.error:
        sys.stderr.write(USAGE)
        sys.exit(1)
    concurrency = -1
    direction = ""
    identifier = str(uuid.uuid4())
    length = -1
    myname = ""
    peername = ""
    protocol = ""
    servermode = False
    timespan = -1
    for name, value in options:
        if name == "--concurrency":
            try:
                concurrency = int(value)
            except ValueError:
                concurrency = -1
            if concurrency < 0:
                sys.stderr.write("Bad argument to --concurrency")
                sys.exit(1)
        elif name == "--direction":
            if value not in DIRECTIONS:
                sys.stderr.write("Bad argument to --direction\n")
                sys.exit(1)
            direction = value
        elif name == "--help":
            sys.stdout.write(HELP)
            sys.exit(0)
        elif name == "--identifier":
            identifier = value
        elif name == "--length":
            try:
                length = int(value)
            except ValueError:
                length = -1
            if length < 0:
                sys.stderr.write("Bad argument to --length\n")
                sys.exit(1)
        elif name == "--myname":
            myname = value
        elif name == "--peername":
            peername = value
        elif name == "--protocol":
            protocol = value
        elif name == "--server":
            servermode = True
        elif name == "--timespan":
            timespan = value
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
            port = "9773"
        slet = neubot.collect.servlet()
        container = neubot.container.container(poller, address=address,
                                               port=port)
        container.register("/collect/1.0/", slet.main)
    else:
        if len(arguments) >= 2:
            sys.stderr.write(USAGE)
            sys.exit(1)
        elif len(arguments) == 1:
            uri = arguments[0]
        else:
            sys.stderr.write(USAGE)
            sys.exit(1)
        neubot.table.create_entry(identifier, peername)
        neubot.table.update_entry(identifier, concurrency, direction,
                                  length, myname, protocol, timespan)
        octets = neubot.table.stringify_entry(identifier)
        neubot.table.remove_entry(identifier)
        neubot.collect.client(poller, uri, octets)
    poller.loop()

if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    main(sys.argv)
