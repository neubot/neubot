# neubot/negotiate.py
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
import types
import uuid
import urlparse

import neubot

DIRECTIONS = [ "upload", "download" ]

class parameters:
    def __init__(self, octets=""):
        self.direction = u""
        self.length = -1
        self.uri = u""
        if octets:
            dictionary = json.loads(octets)
            if type(dictionary) != types.DictType:
                raise ValueError("Bad json message")
            if dictionary.has_key(u"direction"):
                direction = dictionary[u"direction"]
                if type(direction) != types.UnicodeType:
                    raise ValueError("Bad json message")
                if direction not in DIRECTIONS:
                    raise ValueError("Bad json message")
                self.direction = direction
            if dictionary.has_key(u"length"):
                length = dictionary[u"length"]
                if type(length) != types.IntType:
                    raise ValueError("Bad json message")
                if length < 0:
                    raise ValueError("Bad json message")
                self.length = length
            if dictionary.has_key(u"uri"):
                uri = dictionary[u"uri"]
                if type(uri) != types.UnicodeType:
                    raise ValueError("Bad json message")
                # Make sure the received uri is well-formed
                urlparse.urlsplit(uri)
                self.uri = uri

    def __str__(self):
        dictionary = {}
        if self.direction:
            dictionary[u"direction"] = self.direction
        if self.length >= 0:
            dictionary[u"length"] = self.length
        if self.uri:
            dictionary[u"uri"] = self.uri
        octets = json.dumps(dictionary, ensure_ascii=True)
        return (octets)

    def set_direction(self, direction):
        if direction not in DIRECTIONS:
            raise ValueError("Bad json message")
        self.direction = unicode(direction)

    def set_length(self, length):
        if type(length) != types.IntType:
            raise ValueError("Bad json message")
        if length < 0:
            raise ValueError("Bad json message")
        self.length = length

    def set_uri(self, uri):
        # Make sure the received uri is well-formed
        urlparse.urlsplit(uri)
        self.uri = unicode(uri)

class servlet:
    def __init__(self, maxlen, uri):
        self.maxlen = maxlen
        self.uri = uri

    def main(self, protocol, response):
        if protocol.message.method == "PUT":
            uri = protocol.message.uri
            if uri[-1] == "/":
                logging.warning("There is not resource identifier")
                response.code, response.reason = "403", "Forbidden"
                return
            index = uri.rfind("/")
            if index == -1:
                logging.warning("Could not find the last slash")
                response.code, response.reason = "403", "Forbidden"
                return
            collection = uri[:index + 1]
            identifier = uri[index + 1:]
            if collection not in ["/http/1.0/", "/latency/1.0"]:
                logging.warning("Unrecognized collection name")
                response.code, response.reason = "403", "Forbidden"
                return
            try:
                uuid.UUID(identifier)
            except ValueError:
                logging.warning("Could not parse resource identifier")
                response.code, response.reason = "403", "Forbidden"
                return
            address = str(protocol).split(":")[0]
            success = neubot.table.create_entry(identifier, address)
            if not success:
                response.code, response.reason = "403", "Forbidden"
                return
        elif protocol.message.method == "POST":
            logging.warning("Accepting old-style POST request")
        else:
            response.code, response.reason = "204", "No Content"
            return
        address, port = str(protocol).split(":")                        # XXX
        neubot.whitelist.register(address)
        protocol.message.body.seek(0)
        octets = protocol.message.body.read()
        params = neubot.negotiate.parameters(octets)
        params.set_uri(self.uri)
        if params.length > self.maxlen:
            params.length = self.maxlen
        response.code, response.reason = "200", "Ok"
        response["content-type"] = "application/json"
        octets = str(params)
        response["content-length"] = str(len(octets))
        response.body = StringIO.StringIO(octets)

class client:
    def __init__(self, poller, uri, family=socket.AF_INET):
        self.done = False
        self.poller = poller
        scheme, address, port, self.path = neubot.http.urlsplit(uri)
        logging.info("Begin negotiation with %s" % address)
        secure =  scheme == "https"
        neubot.http.connector(self, poller, address, port, family, secure)
        self.params = None
        self.identifier = str(uuid.uuid4())

    #
    # FIXME I don't like the fact that we have to validate and
    # set values twice (once in the client and then when building
    # the actual JSON message) -- in the next release cycle I'd
    # like to address this issue, rolling out a more elegant
    # implementation.
    #

    def set_direction(self, direction):
        if not direction in DIRECTIONS:
            raise ValueError("Bad direction")
        self.direction = direction

    def set_length(self, length):
        self.length = length

    def aborted(self, connector):
        logging.error("Connection to '%s' failed" % connector)
        self.done = True

    def connected(self, connector, protocol):
        logging.debug("Connected to '%s'" % connector)
        protocol.attach(self)
        logging.debug("Pretty-printing the request")
        self.request = neubot.http.message(method="PUT",
          uri=self.path + self.identifier, protocol="HTTP/1.1")
        self.request["date"] = neubot.http.date()
        self.request["cache-control"] = "no-cache"
        self.request["connection"] = "close"
        self.request["host"] = str(protocol)
        self.request["pragma"] = "no-cache"
        params = neubot.negotiate.parameters()
        params.set_direction(self.direction)
        params.set_length(self.length)
        octets = str(params)
        self.request["content-type"] = "application/json"
        self.request["content-length"] = str(len(octets))
        self.request.body = StringIO.StringIO(octets)
        neubot.http.prettyprinter(logging.debug, "  ", self.request)
        neubot.utils.prettyprint_json(logging.debug, "  ", octets)
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
        if response.code != "200":
            raise Exception("Unexpected response code")
        if response["content-type"] != "application/json":
            raise Exception("Unexpected content-type")
        if response["transfer-encoding"] == "chunked":
            raise Exception("Unexpected chunked response")

    def is_message_unbounded(self, protocol):
       if neubot.http.response_unbounded(self.request, protocol.message):
            raise Exception("Unexpected unbounded response")

    def got_message(self, protocol):
        response = protocol.message
        response.body.seek(0)
        octets = response.body.read()
        neubot.utils.prettyprint_json(logging.debug, "  ", octets)
        self.params = neubot.negotiate.parameters(octets)
        protocol.close()
        logging.info("Negotiation completed successfully")

    def closing(self, protocol):
        logging.debug("Connection to '%s' closed" % protocol)
        self.done = True

USAGE = 								\
"Usage:\n"								\
"  neubot [options] negotiate --server [options] [[address] port]\n"	\
"  neubot [options] negotiate [options] uri\n"				\
"\n"									\
"Try `neubot negotiate --help' for more help.\n"

LONGOPTS = [
    "direction=",
    "help",
    "length=",
    "server",
    "uri=",
]

HELP = 									\
"Usage:\n"								\
"  neubot [options] negotiate --server [options] [[address] port]\n"	\
"  neubot [options] negotiate [options] uri\n"				\
"\n"									\
"Options:\n"								\
"  --direction download|upload\n"					\
"      Set the transfer type the client whishes to perform.\n"		\
"  --help\n"								\
"      Print this help screen.\n"					\
"  --length N\n"							\
"      In client mode specify the amount of bytes we whish to\n"	\
"      transfer.  In server mode specifies the maximum amount\n"	\
"      we are going to accept.\n"					\
"  --server\n"								\
"      Run in server mode.\n"						\
"  --uri URI\n"								\
"      In server mode, specify the URI to connect to in order to\n"	\
"      perform the negotiated test.\n"

def main(argv):
    try:
        options, arguments = getopt.getopt(argv[1:], "", LONGOPTS)
    except getopt.error:
        sys.stderr.write(USAGE)
        sys.exit(1)
    direction = "download"
    length = 0
    servermode = False
    testuri = ""
    for name, value in options:
        if name == "--direction":
            if value not in DIRECTIONS:
                sys.stderr.write("Bad direction\n")
                sys.exit(1)
            direction = value
        elif name == "--help":
            sys.stdout.write(HELP)
            sys.exit(0)
        elif name == "--length":
            try:
                length = int(value)
            except ValueError:
                length = -1
            if length < 0:
                sys.stderr.write("Bad argument to --length\n")
                sys.exit(1)
        elif name == "--server":
            servermode = True
        elif name == "--uri":
            try:
                urlparse.urlsplit(value)
            except:
                sys.stderr.write("Bad argument to --uri\n")
                sys.exit(1)
            testuri = value
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
        slet = neubot.negotiate.servlet(length, testuri)
        container = neubot.container.container(poller, address=address,
                                               port=port)
        container.register("/latency/1.0/", slet.main)
        container.register("/http/1.0/", slet.main)
    else:
        if len(arguments) >= 2:
            sys.stderr.write(USAGE)
            sys.exit(1)
        elif len(arguments) == 1:
            uri = arguments[0]
        else:
            sys.stderr.write(USAGE)
            sys.exit(1)
        clnt = neubot.negotiate.client(poller, uri)
        clnt.set_direction(direction)
        clnt.set_length(length)
    poller.loop()

if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    main(sys.argv)
