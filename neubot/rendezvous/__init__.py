# neubot/rendezvous/__init__.py

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
import xml.dom.minidom
import random
import sys
import getopt

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.config import CONFIG

from neubot.speedtest import SpeedtestController
from ConfigParser import SafeConfigParser
from neubot.net.poller import POLLER
from neubot.database import database
from neubot.utils import versioncmp
from neubot.log import LOG
from neubot.state import STATE
from neubot.http.server import ServerHTTP
from neubot.http.message import Message
from neubot.marshal import unmarshal_object
from neubot.marshal import marshal_object
from neubot.http.client import ClientHTTP
from neubot import system

VERSION = "0.3.7"


class RendezvousRequest(object):
    def __init__(self):
        self.accept = []
        self.version = ""


class RendezvousResponse(object):
    def __init__(self):
        self.update = {}
        self.available = {}


#
# Backward-compat ad-hoc stuff.  BLEAH.
#
# <rendezvous_response>
#  <available name="speedtest">
#   <uri>http://speedtest1.neubot.org/speedtest</uri>
#   <uri>http://speedtest2.neubot.org/speedtest</uri>
#  </available>
#  <update uri="http://releases.neubot.org/neubot-0.2.4.exe">0.2.4</update>
# </rendezvous_response>
#

def adhoc_element(document, root, name, value, attributes):
    element = document.createElement(name)
    root.appendChild(element)

    if value:
        text = document.createTextNode(value)
        element.appendChild(text)

    if attributes:
        for name, value in attributes.items():
            element.setAttribute(name, value)

    return element

def adhoc_marshaller(obj):
    document = xml.dom.minidom.parseString("<rendezvous_response/>")

    if obj.update:
        adhoc_element(document, document.documentElement, "update",
          obj.update["version"], {"uri": obj.update["uri"]})

    for name, vector in obj.available.items():
        element = adhoc_element(document, document.documentElement,
          "available", None, {"name": name})

        for uri in vector:
            adhoc_element(document, element, "uri", uri, None)

    return document.documentElement.toxml("utf-8")


class ServerRendezvous(ServerHTTP):

    def process_request(self, stream, request):
        m = unmarshal_object(request.body.read(),
          "application/xml", RendezvousRequest)

        m1 = RendezvousResponse()

        if m.version and versioncmp(VERSION, m.version) > 0:
            m1.update["uri"] = self.conf.get(
              "rendezvous.server.update_uri",
              "http://www.neubot.org/download"
            )
            m1.update["version"] = self.conf.get(
              "rendezvous.server.update_version",
              VERSION
            )

        if "speedtest" in m.accept:
            generator = self.conf.get(
              "rendezvous.server.speedtest_uri_generator",
              lambda: ["http://speedtest1.neubot.org/speedtest"]
            )
            m1.available["speedtest"] = generator()

        if m.version and versioncmp(m.version, "0.3.7") >= 0:
            s = marshal_object(m1, "application/json")
            mimetype = "application/json"
        else:
            s = adhoc_marshaller(m1)
            mimetype = "text/xml"

        stringio = StringIO.StringIO()
        stringio.write(s)
        stringio.seek(0)

        response = Message()
        response.compose(code="200", reason="Ok",
          mimetype=mimetype, body=stringio)
        stream.send_response(request, response)


class RendezvousServer(object):
    def __init__(self, config, port):
        server = ServerRendezvous(POLLER)
        server.conf = {
            "rendezvous.server.update_uri": config.update_uri,
            "rendezvous.server.speedtest_uri_generator": lambda: [
                config.test_uri
            ]
        }
        server.listen((config.address, int(config.altport)))
        server.listen((config.address, int(config.port)))


#
# [rendezvous]
# address: 0.0.0.0
# update_uri: http://releases.neubot.org
# test_uri2:
# test_uri: http://speedtest1.neubot.org/speedtest
# port: 9773
# alt-port: 8080
#

class RendezvousConfig(SafeConfigParser):
    def __init__(self):
        SafeConfigParser.__init__(self)
        self.address = "0.0.0.0"
        self.update_uri = "http://releases.neubot.org"
        self.test_uri = "http://speedtest1.neubot.org/speedtest"
        self.test_uri2 = ""
        self.port = "9773"
        self.altport = "8080"

#   def check(self):
#       pass

    def readfp(self, fp, filename=None):
        SafeConfigParser.readfp(self, fp, filename)
        self._do_parse()

    def _do_parse(self):
        if self.has_option("rendezvous", "address"):
            self.address = self.get("rendezvous", "address")
        if self.has_option("rendezvous", "update_uri"):
            self.update_uri = self.get("rendezvous", "update_uri")
        if self.has_option("rendezvous", "test_uri"):
            self.test_uri = self.get("rendezvous", "test_uri")
        if self.has_option("rendezvous", "test_uri2"):
            self.test_uri2 = self.get("rendezvous", "test_uri2")
        if self.has_option("rendezvous", "port"):
            self.port = self.get("rendezvous", "port")

    def read(self, filenames):
        SafeConfigParser.read(self, filenames)
        self._do_parse()

class RendezvousModule:
    def __init__(self):
        self.config = RendezvousConfig()
        self.server = None
        self.altserver = None

    def configure(self, filenames, fakerc):
        self.config.read(filenames)
        self.config.readfp(fakerc)
        # XXX other modules need to read() it too
        fakerc.seek(0)

    # XXX Migration from 9773 to 8080 because the former might be blocked
    def start(self):
        self.server = RendezvousServer(self.config, self.config.port)

rendezvous = RendezvousModule()


class RendezvousClient(ClientHTTP, SpeedtestController):

    def init(self, server_uri, interval, dontloop, xdebug):
        self.server_uri = server_uri
        self.interval = interval
        self.dontloop = dontloop
        self.xdebug = xdebug
        self.testing = 0
        self.task = None

    def _reschedule(self):

        if self.testing:
            return
        if self.dontloop:
            return
        if self.task:
            LOG.debug("rendezvous: There is already a pending task")
            return

        LOG.info("* Next rendezvous in %d seconds" % self.interval)
        self.task = POLLER.sched(self.interval, self.rendezvous)

        STATE.update("next_rendezvous", self.task.timestamp, publish=False)
        STATE.update("idle")

    def connection_failed(self, connector, exception):
        STATE.update("rendezvous", {"status": "failed"})
        self._reschedule()

    def connection_lost(self, stream):
        self._reschedule()

    def rendezvous(self):
        self.task = None
        STATE.update("rendezvous")

        r = Message()
        r.compose(uri=self.server_uri)
        self.connect((r.address, int(r.port)))

    def connection_ready(self, stream):

        m = RendezvousRequest()
        m.accept.append("speedtest")
        m.version = VERSION

        s = marshal_object(m, "application/xml")

        if self.xdebug:
            sys.stdout.write(s + "\n")

        stringio = StringIO.StringIO()
        stringio.write(s)
        stringio.seek(0)

        request = Message()
        request.compose(method="GET", uri=self.server_uri,
          mimetype="text/xml", body=stringio, keepalive=False)

        stream.send_request(request)

    def got_response(self, stream, request, response):
        if response.code != "200":
            LOG.error("Error: %s %s" % (response.code, response.reason))
            self._reschedule()
            return

        s = response.body.read()
        if self.xdebug:
            sys.stdout.write(s)

        try:
            m1 = unmarshal_object(s, "application/json", RendezvousResponse)
        except ValueError:
            LOG.exception()
            self._reschedule()
            return

        if "version" in m1.update and "uri" in m1.update:
            ver, uri = m1.update["version"], m1.update["uri"]
            LOG.warning("Version %s available at %s" % (ver, uri))
            STATE.update("update", {"version": ver, "uri": uri})

        if self.xdebug:
            self._reschedule()
            return

        if not CONFIG.get("enabled", True):
            self._reschedule()
            return

        if (CONFIG.get("privacy.informed", 0) and
          not CONFIG.get("privacy.can_collect", 0)):
            LOG.warning("refusing to test because you don't give me "
                        "the permission to collect the results")
            self._reschedule()
            return

        if "speedtest" in m1.available:
            uri = m1.available["speedtest"][0]
            self.testing = 1
            self.start_speedtest_simple(uri)

    def speedtest_complete(self):
        self.testing = 0
        self._reschedule()


USAGE = 								\
"Usage: @PROGNAME@ -V\n"						\
"       @PROGNAME@ --help\n"						\
"       @PROGNAME@ [-dnvx] [-T interval] [master-URI]\n"		\
"       @PROGNAME@ -S [-dv] [-D name=value]\n"

HELP = USAGE +								\
"Options:\n"								\
"  -d            : Debug mode, don't become a daemon.\n"		\
"  -D name=value : Set configuration file property.\n"			\
"  --help        : Print this help screen and exit.\n"			\
"  -n            : Don't loop, just rendez-vous once.\n"		\
"  -S            : Run the program in server mode.\n"			\
"  -T interval   : Interval between each rendez-vous.\n"		\
"  -V            : Print version number and exit.\n"			\
"  -v            : Run the program in verbose mode.\n"			\
"  -x            : Debug mode, don't run any test.\n"

URI = "http://master.neubot.org:8080/rendezvous"

def main(args):
    fakerc = StringIO.StringIO()
    fakerc.write("[rendezvous]\n")
    dontloop = False
    servermode = False
    interval = 1380 + random.randrange(0, 240)
    xdebug = False
    daemonize = True

    try:
        options, arguments = getopt.getopt(args[1:], "dD:nST:Vvx", ["help"])
    except getopt.GetoptError:
        sys.stderr.write(USAGE.replace("@PROGNAME@", args[0]))
        sys.exit(1)

    for name, value in options:
        if name == "-d":
            daemonize = False
        elif name == "-D":
            fakerc.write(value + "\n")
        elif name == "--help":
            sys.stdout.write(HELP.replace("@PROGNAME@", args[0]))
            sys.exit(1)
        elif name == "-n":
            dontloop = True
        elif name == "-S":
            servermode = True
        elif name == "-T":
            try:
                interval = int(value)
            except ValueError:
                interval = -1
            if interval <= 0:
                LOG.error("Invalid argument to -T: %s" % value)
                sys.exit(1)
        elif name == "-V":
            sys.stdout.write(VERSION + "\n")
            sys.exit(0)
        elif name == "-v":
            LOG.verbose()
        elif name == "-x":
            xdebug = True

    fakerc.seek(0)

    if servermode:
        if len(arguments) > 0:
            sys.stderr.write(USAGE.replace("@PROGNAME@", args[0]))
            sys.exit(1)
        database.start()
        rendezvous.start()
        if daemonize:
            system.change_dir()
            system.go_background()
            LOG.redirect()
        system.drop_privileges()
        POLLER.loop()
        sys.exit(0)

    if len(arguments) > 1:
        sys.stderr.write(USAGE.replace("@PROGNAME@", args[0]))
        sys.exit(1)
    elif len(arguments) == 1:
        uri = arguments[0]
    else:
        uri = URI
    database.start()
    if daemonize:
        system.change_dir()
        system.go_background()
        LOG.redirect()
    system.drop_privileges()
    client = RendezvousClient(POLLER)
    client.init(uri, interval, dontloop, xdebug)
    client.rendezvous()
    POLLER.loop()

if __name__ == "__main__":
    main(sys.argv)
