# neubot/rendezvous.py
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
import collections
import getopt
import json
import logging
import socket
import sys
import types

import neubot

class request:
    def __init__(self, octets=""):
        self.accepts = []
        self.provides = {}
        self.version = u""
        if octets:
            dictionary = json.loads(octets)
            if type(dictionary) != types.DictType:
                raise ValueError("Bad json message")
            if dictionary.has_key(u"accepts"):
                for accept in dictionary[u"accepts"]:
                    if type(accept) != types.UnicodeType:
                        raise ValueError("Bad json message")
                    self.accepts.append(accept)
            if dictionary.has_key(u"provides"):
                provides = dictionary[u"provides"]
                if type(provides) != types.DictType:
                    raise ValueError("Bad json message")
                for name, uri in provides.items():
                    if type(name) != types.UnicodeType:
                        raise ValueError("Bad json message")
                    if type(uri) != types.UnicodeType:
                        raise ValueError("Bad json message")
                    self.provides[name] = uri
            if dictionary.has_key(u"version"):
                version = dictionary[u"version"]
                if type(version) != types.UnicodeType:
                    raise ValueError("Bad json message")
                self.version = version

    def __str__(self):
        dictionary = {}
        if len(self.accepts) > 0:
            dictionary[u"accepts"] = self.accepts
        if len(self.provides) > 0:
            dictionary[u"provides"] = self.provides
        if len(self.version) > 0:
            dictionary[u"version"] = self.version
        octets = json.dumps(dictionary, ensure_ascii=True)
        return octets

    def accept_test(self, name):
        self.accepts.append(unicode(name))

    def provide_test(self, name, uri):
        self.provides[unicode(name)] = unicode(uri)

    def set_version(self, version):
        self.version = unicode(version)

class response:
    def __init__(self, octets=""):
        self.versioninfo = {}
        self.available = {}
        self.collecturi = u""
        if octets:
            dictionary = json.loads(octets)
            if type(dictionary) != types.DictType:
                raise ValueError("Bad json message")
            if dictionary.has_key(u"versioninfo"):
                versioninfo = dictionary[u"versioninfo"]
                if type(versioninfo) != types.DictType:
                    raise ValueError("Bad json message")
                for key, value in versioninfo.items():
                    if type(key) != types.UnicodeType:
                        raise ValueError("Bad json message")
                    if type(value) != types.UnicodeType:
                        raise ValueError("Bad json message")
                    self.versioninfo[key] = value
            if dictionary.has_key(u"available"):
                available = dictionary[u"available"]
                if type(available) != types.DictType:
                    raise ValueError("Bad json message")
                for name, uri in available.items():
                    if type(name) != types.UnicodeType:
                        raise ValueError("Bad json message")
                    if type(uri) != types.UnicodeType:
                        raise ValueError("Bad json message")
                    self.available[name] = uri
            if dictionary.has_key(u"collecturi"):
                collecturi = dictionary[u"collecturi"]
                if type(collecturi) != types.UnicodeType:
                    raise ValueError("Bad json message")
                self.collecturi = collecturi

    def __str__(self):
        dictionary = {}
        if len(self.versioninfo) > 0:
            dictionary[u"versioninfo"] = self.versioninfo
        if len(self.available) > 0:
            dictionary[u"available"] = self.available
        if self.collecturi:
            dictionary[u"collecturi"] = self.collecturi
        octets = json.dumps(dictionary, ensure_ascii=True)
        return octets

    def set_versioninfo(self, version, uri):
        self.versioninfo[u"version"] = unicode(version)
        self.versioninfo[u"uri"] = unicode(uri)

    def add_available(self, name, uri):
        self.available[unicode(name)] = unicode(uri)

    def set_collecturi(self, collecturi):
        self.collecturi = unicode(collecturi)

class servlet:
    def __init__(self):
        self.available = {}
        self.version = neubot.version
        self.uri = "http://www.neubot.org:8080/"
        self.collecturi = "http://master.neubot.org:9773/collect/1.0/"

    def add_available(self, name, value):
        self.available[name] = value

    def set_versioninfo(self, version, uri):
        self.version = version
        self.uri = uri

    def set_collecturi(self, collecturi):
        self.collecturi = collecturi

    def main(self, protocol, response):
        if protocol.message.method != "POST":
            response.code, response.reason = "204", "No Content"
            return
        protocol.message.body.seek(0)
        octets = protocol.message.body.read()
        requestbody = neubot.rendezvous.request(octets)
        responsebody = neubot.rendezvous.response()
        if len(requestbody.version) > 0:
            version = requestbody.version
            if neubot.utils.versioncmp(neubot.version, version) > 0:
                responsebody.set_versioninfo(self.version, self.uri)
        for name in requestbody.accepts:
            if name in self.available.keys():
                responsebody.add_available(name, self.available[name])
        responsebody.set_collecturi(self.collecturi)
        response.code, response.reason = "200", "Ok"
        response["content-type"] = "application/json"
        octets = str(responsebody)
        response["content-length"] = str(len(octets))
        response.body = StringIO.StringIO(octets)

class client:
    def __init__(self, poller, family=socket.AF_INET,
      uri="http://master.neubot.org:9773/rendez-vous/1.0/"):
        self.done = False
        self.poller = poller
        scheme, address, port, self.path = neubot.http.urlsplit(uri)
        logging.info("Begin rendez-vous with %s" % address)
        secure =  scheme == "https"
        neubot.http.connector(self, poller, address, port, family, secure)
        self.provides = {}
        self.accepts = set()
        self.version = neubot.version
        self.request = None
        self.responsebody = None

    def accept_test(self, name):
        self.accepts.add(name)

    def provide_test(self, name, uri):
        self.provides[name] = uri

    def set_version(self, version):
        self.version = version

    def aborted(self, connector):
        logging.error("Connection to '%s' failed" % connector)
        self.done = True

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
        requestbody = neubot.rendezvous.request()
        requestbody.set_version(self.version)
        for name, uri in self.provides.items():
            requestbody.provide_test(name, uri)
        for name in self.accepts:
            requestbody.accept_test(name)
        octets = str(requestbody)
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
        self.responsebody = neubot.rendezvous.response(octets)
        protocol.close()
        logging.info("Rendez-vous completed successfully")

    def closing(self, protocol):
        logging.debug("Connection to '%s' closed" % protocol)
        self.done = True

USAGE =									\
"Usage:\n"								\
"  neubot [options] rendezvous --server [options] [[address] port]\n"	\
"  neubot [options] rendezvous [options] [uri]\n"			\
"\n"									\
"Try `neubot rendezvous --help' for more help.\n"

LONGOPTS = [
    "accept-test=",
    "add-available-test=",
    "collecturi=",
    "help",
    "provide-test=",
    "server",
    "set-update-uri=",
    "set-version=",
]

HELP =									\
"Usage:\n"								\
"  neubot [options] rendezvous --server [options] [[address] port]\n"	\
"  neubot [options] rendezvous [options] [uri]\n"			\
"\n"									\
"Options:\n"								\
"  --accept-test NAME\n"						\
"      Add NAME to the list of tests the client will accept.\n"		\
"  --add-available-test NAME,URI\n"					\
"      Add test NAME provided by URI to the list of tests that the\n"	\
"      server is aware of (provided by TestServers or other Neubots.)\n"\
"  --collecturi URI\n"                                                 \
"      Uri to send results to.\n"                                       \
"  --help\n"								\
"      Print this help screen.\n"					\
"  --provide-test NAME,URI\n"						\
"      Add test NAME provided by URI to the list of tests that the\n"	\
"      client provides to other clients (i.e. in peer-to-peer mode.)\n"	\
"  --server\n"								\
"      Run in server mode.\n"						\
"  --set-update-uri URI\n"						\
"      Tell clients they could retrieve updated versions at URI.\n"	\
"  --set-version VERSION\n"						\
"      Override neubot version with VERSION.\n"

def main(argv):
    try:
        options, arguments = getopt.getopt(argv[1:], "", LONGOPTS)
    except getopt.error:
        sys.stderr.write(USAGE)
        sys.exit(1)
    acceptlist = collections.deque()
    availablelist = collections.deque()
    providelist = collections.deque()
    updateuri = "http://www.neubot.org:8080/"
    collecturi = "http://master.neubot.org:9773/collect/1.0/"
    version = neubot.version
    servermode = False
    for name, value in options:
        if name == "--accept-test":
            acceptlist.append(value)
        elif name == "--add-available-test":
            try:
                testname, testuri = value.split(",", 1)
            except ValueError:
                sys.stderr.write("Bad %s parameter %s" % (name, value))
                sys.stderr.write(USAGE)
                sys.exit(1)
            availablelist.append((testname, testuri))
        elif name == "--collecturi":
            collecturi = value
        elif name == "--help":
            sys.stdout.write(HELP)
            sys.exit(0)
        elif name == "--provide-test":
            try:
                testname, testuri = value.split(",", 1)
            except ValueError:
                sys.stderr.write("Bad %s parameter %s" % (name, value))
                sys.stderr.write(USAGE)
                sys.exit(1)
            providelist.append((testname, testuri))
        elif name == "--server":
            servermode = True
        elif name == "--set-update-uri":
            updateuri = value
        elif name == "--set-version":
            version = value
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
        slet = neubot.rendezvous.servlet()
        for name, value in availablelist:
            slet.add_available(name, value)
        slet.set_versioninfo(version, updateuri)
        slet.set_collecturi(collecturi)
        container = neubot.container.container(poller,
          address=address, port=port)
        container.register("/rendez-vous/1.0/", slet.main)
    else:
        if len(arguments) >= 2:
            sys.stderr.write(USAGE)
            sys.exit(1)
        elif len(arguments) == 1:
            uri = arguments[0]
        else:
            uri = "http://master.neubot.org:9773/rendez-vous/1.0/"
        clnt = neubot.rendezvous.client(poller, uri=uri)
        for name in acceptlist:
            clnt.accept_test(name)
        for name, value in providelist:
            clnt.provide_test(name, value)
        clnt.set_version(version)
    poller.loop()

if (__name__ == "__main__"):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    main(sys.argv)
