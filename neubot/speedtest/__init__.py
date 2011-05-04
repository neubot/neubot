# neubot/speedtest/__init__.py

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

import ConfigParser
import StringIO
import sys
import getopt
import collections
import os.path
import uuid

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.arcfour import RandomBody

from neubot.config import CONFIG

from neubot.database import database

from neubot.http.message import Message
from neubot.http.utils import parse_range
from neubot.http.server import ServerHTTP
from neubot.http.client import ClientHTTP

from neubot.log import LOG

from neubot.marshal import unmarshal_object
from neubot.marshal import marshal_object

from neubot.net.poller import POLLER
from neubot.net.measurer import HeadlessMeasurer

from neubot.notify import RENEGOTIATE
from neubot.notify import NOTIFIER
from neubot.notify import TESTDONE

from neubot.state import STATE

from neubot import system

from neubot.utils import timestamp
from neubot.utils import ticks

from neubot.utils import time_formatter
from neubot.utils import file_length
from neubot.utils import speed_formatter


class SpeedtestCollect(object):

    def __init__(self):
        self.client = ""
        self.timestamp = 0
        self.internalAddress = ""
        self.realAddress = ""
        self.remoteAddress = ""
        self.connectTime = 0.0
        self.latency = 0.0
        self.downloadSpeed = 0.0
        self.uploadSpeed = 0.0
        self.privacy_informed = 0
        self.privacy_can_collect = 0
        self.privacy_can_share = 0


class SpeedtestNegotiate_Response(object):

    def __init__(self):
        self.authorization = ""
        self.publicAddress = ""
        self.unchoked = 0
        self.queuePos = 0
        self.queueLen = 0


# NB This is the *old* TestServer
class Tester(object):

    def do_download(self, stream, request, self_config_path):
        response = Message()

        try:
            body = open(self_config_path, "rb")
        except (IOError, OSError):
            LOG.exception()
            response.compose(code="500", reason="Internal Server Error")
            stream.send_response(request, response)
            return

        if request["range"]:
            total = file_length(body)

            try:
                first, last = parse_range(request)
            except ValueError:
                LOG.exception()
                response.compose(code="400", reason="Bad Request")
                stream.send_response(request, response)
                return

            # XXX read() assumes there is enough core
            body.seek(first)
            partial = body.read(last - first + 1)
            response["content-range"] = "bytes %d-%d/%d" % (first, last, total)
            body = StringIO.StringIO(partial)
            code, reason = "206", "Partial Content"

        else:
            code, reason = "200", "Ok"

        response.compose(code=code, reason=reason, body=body,
                mimetype="application/octet-stream")
        stream.send_response(request, response)


class TestServer(ServerHTTP):

    def __init__(self, poller):
        ServerHTTP.__init__(self, poller)
        self.old_server = Tester()

    def process_request(self, stream, request):

        if request.uri in ("/speedtest/latency", "/speedtest/upload"):
            response = Message()
            response.compose(code="200", reason="Ok")
            stream.send_response(request, response)

        elif request.uri == "/speedtest/download":
            fpath = self.conf.get("speedtest.server.path",
              "/var/neubot/large_file.bin")
            if os.path.isfile(fpath):
                self.old_server.do_download(stream, request, fpath)
            else:
                first, last = parse_range(request)
                response = Message()
                response.compose(code="200", reason="Ok",
                  body=RandomBody(last - first + 1),
                  mimetype="application/octet-stream")
                stream.send_response(request, response)

        else:
            response = Message()
            stringio = StringIO.StringIO("500 Internal Server Error")
            response.compose(code="500", reason="Internal Server Error",
                             body=stringio, mimetype="text/plain")
            stream.send_response(request, response)


class SessionState(object):
    def __init__(self):
        self.active = False
        self.timestamp = 0
        self.identifier = None
        self.queuepos = 0
        self.negotiations = 0


class SessionTracker(object):

    def __init__(self):
        self.identifiers = {}
        self.queue = collections.deque()
        self.connections = {}
        self.task = None

    def _sample_queue_length(self):
        LOG.info("speedtest queue length: %d\n" % len(self.queue))
        self.task = POLLER.sched(60, self._sample_queue_length)

    def session_active(self, identifier):
        if identifier in self.identifiers:
            session = self.identifiers[identifier]
            session.timestamp = timestamp()             # XXX
            return session.active
        return False

    def session_prune(self):
        stale = []
        now = timestamp()
        for session in self.queue:
            if now - session.timestamp > 30:
                stale.append(session)
        if not stale:
            return False
        for session in stale:
            self._do_remove(session)
        return True

    def session_delete(self, identifier):
        if identifier in self.identifiers:
            session = self.identifiers[identifier]
            self._do_remove(session)

    def session_negotiate(self, identifier):
        if not identifier in self.identifiers:
            session = SessionState()
            # XXX collision is not impossible but very unlikely
            session.identifier = str(uuid.uuid4())
            session.timestamp = timestamp()
            self._do_add(session)
        else:
            session = self.identifiers[identifier]
        session.negotiations += 1
        return session

    def _do_add(self, session):
        self.identifiers[session.identifier] = session
        session.queuepos = len(self.queue)
        self.queue.append(session)
        self._do_update_queue()

    def _do_remove(self, session):
        del self.identifiers[session.identifier]
        self.queue.remove(session)
        self._do_update_queue()

    def _do_update_queue(self):

        pos = 1
        for session in self.queue:
            if pos <= 3 and not session.active:
                session.active = True
            session.queuepos = pos
            pos = pos + 1

        if not self.task:
            self.task = POLLER.sched(60, self._sample_queue_length)

    def register_connection(self, connection, identifier):
        if not connection in self.connections:
            if identifier in self.identifiers:
                self.connections[connection] = identifier

    def unregister_connection(self, connection):
        if connection in self.connections:
            identifier = self.connections[connection]
            del self.connections[connection]
            if identifier in self.identifiers:
                session = self.identifiers[identifier]
                self._do_remove(session)


TRACKER = SessionTracker()


class SpeedtestServer(ServerHTTP):

    def __init__(self, poller):
        ServerHTTP.__init__(self, poller)
        self.begin_test = 0
        POLLER.sched(3, self._speedtest_check_timeout)
        self.test_server = TestServer(poller)

    def initialize(self, config):
        self.conf["speedtest.server.only_auth"] = config.only_auth
        self.conf["speedtest.server.path"] = config.path

    def got_request_headers(self, stream, request):
        ret = True
        TRACKER.register_connection(stream, request["authorization"])

        only_auth = self.conf.get("speedtest.server.only_auth", False)
        if (only_auth and request.uri != "/speedtest/negotiate" and
          not TRACKER.session_active(request["authorization"])):
            LOG.warning("* Connection %s: Forbidden" % stream.logname)
            ret = False

        return ret

    def process_request(self, stream, request):

        if request.uri == "/speedtest/negotiate":
            self.do_negotiate(stream, request)

        elif request.uri == "/speedtest/collect":
            self.do_collect(stream, request)

        else:
            self.test_server.process_request(stream, request)

    #
    # A client is allowed to access restricted URIs if: (i) either
    # only_auth is False, (ii) or the authorization token is valid.
    # Here we decide how to give clients authorization tokens.
    # We start with a very simple (to implement) rule.  We give the
    # client a token and we remove the token after 30+ seconds, or
    # when the authorized client uploads the results.
    # Wish list:
    # - Avoid client synchronization
    #

    def _do_renegotiate(self, event, atuple):
        stream, request = atuple
        self.do_negotiate(stream, request, True)

    def _speedtest_check_timeout(self):
        POLLER.sched(3, self._speedtest_check_timeout)
        if TRACKER.session_prune():
            NOTIFIER.publish(RENEGOTIATE)

    def _speedtest_complete(self, request):
        TRACKER.session_delete(request["authorization"])
        NOTIFIER.publish(RENEGOTIATE)

    def do_negotiate(self, stream, request, nodelay=False):
        session = TRACKER.session_negotiate(request["authorization"])
        if not request["authorization"]:
            request["authorization"] = session.identifier

        #
        # XXX make sure we track ALSO the first connection of the
        # session (which is assigned an identifier in session_negotiate)
        # or, should this connection fail, we would not be able to
        # propagate quickly this information because unregister_connection
        # would not find an entry in self.connections{}.
        #
        if session.negotiations == 1:
            TRACKER.register_connection(stream, request["authorization"])
            nodelay = True

        if not session.active:
            if not nodelay:
                NOTIFIER.subscribe(RENEGOTIATE, self._do_renegotiate,
                          (stream, request))
                return

        m1 = SpeedtestNegotiate_Response()
        m1.authorization = session.identifier
        m1.unchoked = session.active
        m1.queuePos = session.queuepos
        m1.publicAddress = stream.peername[0]
        s = marshal_object(m1, "text/xml")

        stringio = StringIO.StringIO(s)
        response = Message()
        response.compose(code="200", reason="Ok",
         body=stringio, mimetype="application/xml")
        stream.send_response(request, response)

    def do_collect(self, stream, request):
        self._speedtest_complete(request)

        s = request.body.read()
        m = unmarshal_object(s, "text/xml", SpeedtestCollect)

        if database.dbm and (not m.privacy_informed or
                             m.privacy_can_collect):
            database.dbm.save_result(m)

        response = Message()
        response.compose(code="200", reason="Ok")
        stream.send_response(request, response)

    def connection_lost(self, stream):
        TRACKER.unregister_connection(stream)
        NOTIFIER.publish(RENEGOTIATE)


#
# [speedtest]
# address: 0.0.0.0
# only_auth: False
# path: /nonexistent
# port: 80
#

class SpeedtestConfig(ConfigParser.SafeConfigParser):
    def __init__(self):
        ConfigParser.SafeConfigParser.__init__(self)
        self.address = "0.0.0.0"
        self.only_auth = False
        self.path = ""
        self.port = "80"

#   def check(self):
#       pass

    def readfp(self, fp, filename=None):
        ConfigParser.SafeConfigParser.readfp(self, fp, filename)
        self._do_parse()

    def _do_parse(self):
        if self.has_option("speedtest", "address"):
            self.address = self.get("speedtest", "address")
        if self.has_option("speedtest", "only_auth"):
            self.only_auth = self.getboolean("speedtest", "only_auth")
        if self.has_option("speedtest", "path"):
            self.path = self.get("speedtest", "path")
        if self.has_option("speedtest", "port"):
            self.port = self.get("speedtest", "port")

    def read(self, filenames):
        ConfigParser.SafeConfigParser.read(self, filenames)
        self._do_parse()

class SpeedtestModule:
    def __init__(self):
        self.config = SpeedtestConfig()
        self.server = None

    def configure(self, filenames, fakerc):
        self.config.read(filenames)
        self.config.readfp(fakerc)
        # XXX other modules need to read() it too
        fakerc.seek(0)

    def start(self):
        self.server = SpeedtestServer(POLLER)
        self.server.initialize(self.config)
        self.server.listen((self.config.address, int(self.config.port)))

speedtest = SpeedtestModule()

# Client

from neubot.speedtest.client import ClientSpeedtest

class SpeedtestClient2(object):

    def __init__(self, uri, nclients, flags, debug=False, parent=None):
        conf = {
            "speedtest.client.uri": uri,
            "speedtest.client.nconn": nclients,
        }
        client = ClientSpeedtest(POLLER)
        client.configure(conf)
        client.connect_uri()
        NOTIFIER.subscribe(TESTDONE, self.speedtest_complete, parent)

    def speedtest_complete(self, event, parent):
        if parent:
            parent.speedtest_complete()


class SpeedtestController:
    def start_speedtest_simple(self, uri):
        SpeedtestClient2(uri, 2, 0, False, self)

    def speedtest_complete(self):
        pass


# Test unit

USAGE =									\
"Usage: @PROGNAME@ --help\n"						\
"       @PROGNAME@ -V\n"						\
"       @PROGNAME@ [-svx] [-a test] [-n count] [-O fmt] [base-URI]\n"	\
"       @PROGNAME@ -S [-dv] [-D name=value]\n"

HELP = USAGE +								\
"Tests: all*, download, latency, upload.\n"				\
"Fmts: bits*, bytes, raw.\n"						\
"Options:\n"								\
"  -a test       : Add test to the list of tests.\n"			\
"  -D name=value : Set configuration file property.\n"			\
"  -d            : Debug mode, don't become a daemon.\n"                \
"  --help        : Print this help screen and exit.\n"			\
"  -n count      : Use count HTTP connections.\n"			\
"  -O fmt        : Format output numbers using fmt.\n"			\
"  -S            : Run the program in server mode.\n"			\
"  -s            : Do not print speedtest statistics.\n"		\
"  -V            : Print version number and exit.\n"			\
"  -v            : Run the program in verbose mode.\n"			\
"  -x            : Avoid negotiation and collection.\n"

URI = "http://neubot.blupixel.net/speedtest"

VERSION = "0.3.6"

def main(args):
    fakerc = StringIO.StringIO()
    fakerc.write("[speedtest]\r\n")
    daemonize = True
    servermode = False
    xdebug = False
    flags = 0
    nclients = 2
    # parse
    try:
        options, arguments = getopt.getopt(args[1:], "a:D:dn:O:SsVvx", ["help"])
    except getopt.GetoptError:
        sys.stderr.write(USAGE.replace("@PROGNAME@", args[0]))
        sys.exit(1)
    # options
    for name, value in options:
        if name == "-a":
            # XXX for backward compatibility only
            pass
        elif name == "-D":
            fakerc.write(value + "\n")
        elif name == "-d":
            daemonize = False
        elif name == "--help":
            sys.stdout.write(HELP.replace("@PROGNAME@", args[0]))
            sys.exit(0)
        elif name == "-n":
            try:
                nclients = int(value)
            except ValueError:
                nclients = -1
            if nclients <= 0:
                LOG.error("Invalid argument to -n: %s" % value)
                sys.exit(1)
        elif name == "-O":
            # XXX for backward compatibility only
            pass
        elif name == "-S":
            servermode = True
        elif name == "-s":
            # XXX for backward compatibility only
            pass
        elif name == "-V":
            sys.stdout.write(VERSION + "\n")
            sys.exit(0)
        elif name == "-v":
            LOG.verbose()
        elif name == "-x":
            xdebug = True
    # config
    fakerc.seek(0)
    # server
    if servermode:
        if len(arguments) > 0:
            sys.stderr.write(USAGE.replace("@PROGNAME@", args[0]))
            sys.exit(1)
        database.start()
        speedtest.start()
        if daemonize:
            system.change_dir()
            system.go_background()
            LOG.redirect()
        system.drop_privileges()
        POLLER.loop()
        sys.exit(0)
    # client
    if len(arguments) > 1:
        sys.stderr.write(USAGE.replace("@PROGNAME@", args[0]))
        sys.exit(1)
    elif len(arguments) == 1:
        uri = arguments[0]
    else:
        uri = URI
    # run
    SpeedtestClient2(uri, nclients, flags, xdebug)
    POLLER.loop()

if __name__ == "__main__":
    main(sys.argv)
